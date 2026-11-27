"""Prueba histórica de escenarios de entrada en el oro (futuros GC=F, velas de 1h).

Mide, con reglas fijas, si cada escenario tuvo ventaja en el pasado. Resultados en R
(múltiplos del riesgo de cada trade), con costo fijo por trade. Si una vela toca stop
y objetivo a la vez se cuenta la pérdida. Horas en hora de Bogotá.

Escenarios:
  A  ruptura del máximo/mínimo de ayer (PDH/PDL) a favor de la tendencia diaria
  B  retroceso a un FVG de 1h a favor de la EMA50 de 1h
  y, para comparar: barridas de PDH/PDL y del rango asiático, ruptura contra tendencia
  y entradas al azar.

Uso:
    python escenarios_oro.py            # genera reports/escenarios.md
No es asesoría financiera: una prueba histórica no garantiza resultados futuros.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

SALIDA = Path("reports/escenarios.md")
COSTO = 0.5  # spread + comisión, en $ de precio
TZ = "America/Bogota"


def descargar() -> pd.DataFrame:
    import yfinance as yf

    df = yf.download("GC=F", period="730d", interval="1h", auto_adjust=False, progress=False)
    if df.empty:
        raise RuntimeError("Sin datos de GC=F")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.index = pd.to_datetime(df.index, utc=True).tz_convert(TZ).tz_localize(None)
    df = df[["Open", "High", "Low", "Close"]].dropna()
    df["td"] = (df.index + pd.Timedelta(hours=6)).normalize()  # la sesión empieza a las 18:00
    df["hr"] = df.index.hour
    return df


def diario(h: pd.DataFrame) -> pd.DataFrame:
    d = h.groupby("td").agg(hi=("High", "max"), lo=("Low", "min"), c=("Close", "last"))
    tr = pd.concat([d.hi - d.lo, (d.hi - d.c.shift()).abs(), (d.lo - d.c.shift()).abs()], axis=1).max(axis=1)
    d["atr"] = tr.ewm(alpha=1 / 14, adjust=False).mean().shift(1)
    d["phi"], d["plo"] = d.hi.shift(1), d.lo.shift(1)
    d["tendencia"] = np.where(d.c.shift(1) > d.c.rolling(20).mean().shift(1), 1, -1)
    return d


def simular(b: pd.DataFrame, i: int, dr: int, e: float, stop: float, obj: float, max_velas: int = 12) -> float:
    riesgo = abs(e - stop)
    H, L, C = b.High.values, b.Low.values, b.Close.values
    for j in range(i, min(i + max_velas, len(b))):
        if (L[j] <= stop) if dr == 1 else (H[j] >= stop):
            return (-riesgo - COSTO) / riesgo
        if (H[j] >= obj) if dr == 1 else (L[j] <= obj):
            return (abs(obj - e) - COSTO) / riesgo
    j = min(i + max_velas, len(b)) - 1
    return ((C[j] - e) * dr - COSTO) / riesgo


def pdh_pdl(h, d, modo="ruptura", filtro=1, horas=(2, 11), k_stop=0.5):
    """modo ruptura: cierre fuera del rango de ayer. modo barrida: mecha fuera y cierre dentro."""
    out = []
    for td, g in h.groupby("td"):
        if td not in d.index or np.isnan(d.at[td, "phi"]) or np.isnan(d.at[td, "atr"]):
            continue
        ph, pl, tr, atr = d.at[td, "phi"], d.at[td, "plo"], d.at[td, "tendencia"], d.at[td, "atr"]
        s = g[(g.hr >= horas[0]) & (g.hr < horas[1])]
        for k, (t, b) in zip(h.index.get_indexer(s.index), s.iterrows()):
            if modo == "ruptura":
                dr = 1 if b.Close > ph else -1 if b.Close < pl else 0
                stop = b.Close - dr * k_stop * atr
            else:
                dr = -1 if (b.High > ph and b.Close < ph) else 1 if (b.Low < pl and b.Close > pl) else 0
                stop = b.High + 0.5 if dr == -1 else b.Low - 0.5
            if dr == 0:
                continue
            if (filtro == 1 and dr != tr) or (filtro == -1 and dr == tr):
                break
            e = b.Close
            out.append((t, dr, simular(h, k + 1, dr, e, stop, e + dr * 2 * abs(e - stop))))
            break
    return pd.DataFrame(out, columns=["t", "dr", "R"])


def rango_asiatico(h, d, modo="barrida"):
    out = []
    for td, g in h.groupby("td"):
        a = g[g.index < td + pd.Timedelta(hours=2)]
        if len(a) < 3 or td not in d.index or np.isnan(d.at[td, "atr"]):
            continue
        ah, al = a.High.max(), a.Low.min()
        if ah - al > d.at[td, "atr"]:
            continue
        s = g[(g.index >= td + pd.Timedelta(hours=2)) & (g.index < td + pd.Timedelta(hours=11))]
        for k, (t, b) in zip(h.index.get_indexer(s.index), s.iterrows()):
            if modo == "barrida":
                dr = -1 if (b.High > ah and b.Close < ah) else 1 if (b.Low < al and b.Close > al) else 0
                stop = b.High + 0.5 if dr == -1 else b.Low - 0.5
            else:
                dr = 1 if b.Close > ah else -1 if b.Close < al else 0
                stop = (ah + al) / 2
            if dr == 0:
                continue
            e = b.Close
            out.append((t, dr, simular(h, k + 1, dr, e, stop, e + dr * 2 * abs(e - stop))))
            break
    return pd.DataFrame(out, columns=["t", "dr", "R"])


def fvg(h, filtro=True, horas=(2, 11), rr=2.0, espera=8):
    H, L, C, hr, T = h.High.values, h.Low.values, h.Close.values, h.hr.values, h.index
    ema = h.Close.ewm(span=50).mean().values
    out, i, n = [], 2, len(h)
    while i < n - 1:
        dr = 1 if L[i] - H[i - 2] > 0.3 else -1 if L[i - 2] - H[i] > 0.3 else 0
        if not (horas[0] <= hr[i] < horas[1]) or dr == 0 or (filtro and np.sign(C[i] - ema[i]) != dr):
            i += 1
            continue
        borde = L[i] if dr == 1 else H[i]
        stop = L[i - 2] - 0.5 if dr == 1 else H[i - 2] + 0.5
        j_fin = i + 1
        for j in range(i + 1, min(i + 1 + espera, n)):
            j_fin = j
            if (L[j] <= borde) if dr == 1 else (H[j] >= borde):
                if (L[j] <= stop) if dr == 1 else (H[j] >= stop):
                    r = -1 - COSTO / abs(borde - stop)
                else:
                    r = simular(h, j + 1, dr, borde, stop, borde + dr * rr * abs(borde - stop))
                out.append((T[j], dr, r))
                break
        i = j_fin + 1 if out and out[-1][0] == T[j_fin] else i + 1
    return pd.DataFrame(out, columns=["t", "dr", "R"])


def azar(h, d, seed=1):
    rng, out = np.random.default_rng(seed), []
    for td, g in h.groupby("td"):
        s = g[(g.hr >= 2) & (g.hr < 11)]
        if len(s) == 0 or td not in d.index or np.isnan(d.at[td, "atr"]):
            continue
        k = h.index.get_loc(s.index[rng.integers(len(s))])
        dr, e, atr = rng.choice([1, -1]), h.Close.iloc[k], d.at[td, "atr"]
        out.append((s.index[0], dr, simular(h, k + 1, dr, e, e - dr * 0.5 * atr, e + dr * atr)))
    return pd.DataFrame(out, columns=["t", "dr", "R"])


def fila(nombre: str, r: pd.DataFrame) -> str:
    R = r.R.dropna()
    if R.empty:
        return f"| {nombre} | 0 | | | | |"
    g, p = R[R > 0].sum(), -R[R <= 0].sum()
    eq = R.cumsum()
    return (f"| {nombre} | {len(R)} | {(R > 0).mean() * 100:.0f}% | {R.mean():+.2f}R | "
            f"{g / p if p else float('nan'):.2f} | {(eq - eq.cummax()).min():.1f}R |")


def main() -> None:
    h = descargar()
    d = diario(h)
    escenarios = {
        "A · Ruptura PDH/PDL a favor de tendencia": pdh_pdl(h, d),
        "A · igual, solo Londres (02–07h)": pdh_pdl(h, d, horas=(2, 7)),
        "B · FVG 1h a favor de EMA50": fvg(h),
        "B · igual, solo Londres (02–07h)": fvg(h, horas=(2, 7)),
        "B · igual, objetivo 3R": fvg(h, rr=3),
        "Ruptura PDH/PDL contra tendencia": pdh_pdl(h, d, filtro=-1),
        "Barrida PDH/PDL y vuelta": pdh_pdl(h, d, modo="barrida", filtro=0),
        "Barrida del rango asiático y vuelta": rango_asiatico(h, d),
        "Ruptura del rango asiático": rango_asiatico(h, d, modo="ruptura"),
        "Control: entrada al azar": azar(h, d),
    }
    lineas = [
        f"# Escenarios en el oro (GC=F 1h, {h.index.min():%Y-%m-%d} a {h.index.max():%Y-%m-%d})",
        "",
        f"Horas de Bogotá. Costo ${COSTO} por trade. Stop/objetivo en la misma vela = pérdida. "
        "Tendencia diaria = cierre de ayer vs SMA20. Ventana de señal 02:00–11:00 salvo que se indique.",
        "",
        "| Escenario | Trades | Ganados | Esperanza | PF | Máx. DD |",
        "|---|---|---|---|---|---|",
    ]
    lineas += [fila(k, v) for k, v in escenarios.items()]
    corte = h.index.min() + (h.index.max() - h.index.min()) / 2
    lineas += ["", "## Estabilidad (primera vs segunda mitad del periodo)", "",
               "| Escenario | Trades | Ganados | Esperanza | PF | Máx. DD |", "|---|---|---|---|---|---|"]
    for k in ["A · Ruptura PDH/PDL a favor de tendencia", "B · FVG 1h a favor de EMA50"]:
        r = escenarios[k]
        lineas += [fila(f"{k} — 1ª mitad", r[r.t < corte]), fila(f"{k} — 2ª mitad", r[r.t >= corte])]
    lineas += ["", "> Prueba histórica, no asesoría financiera. Los resultados pasados no garantizan los futuros."]
    SALIDA.parent.mkdir(exist_ok=True)
    SALIDA.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print(f"-> {SALIDA}")


if __name__ == "__main__":
    main()
