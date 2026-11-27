"""Tabla histórica diaria: contexto del mercado + tus operaciones, para revisar qué días eran viables.

Genera data/dias_revision.xlsx con dos hojas:
  - Dias: un renglón por día (mercado + tus operaciones + columna vacía `tu_veredicto`)
  - Operaciones: el historial limpio

Uso:
    python dias_viables.py                 # mercado (yfinance) + operaciones si existe data/operaciones.csv
    python dias_viables.py --sin-mercado   # solo tus operaciones agrupadas por día (sin internet)
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

OPS = Path("data/operaciones.csv")
SALIDA = Path("data/dias_revision.xlsx")
SIMBOLO = "XAUUSD"


# ---------- tus operaciones ----------
def cargar_operaciones() -> pd.DataFrame:
    d = pd.read_csv(OPS)
    d = d[d["Symbol"] == SIMBOLO].copy()
    d["apertura"] = pd.to_datetime(d["Opening time"], format="%d/%m/%Y %H:%M:%S.%f")
    d["cierre"] = pd.to_datetime(d["Closing time"], format="%d/%m/%Y %H:%M:%S.%f")
    d["fecha"] = d["apertura"].dt.normalize()
    d["neto"] = d["Net $"]
    d["lotes"] = d["Closing Quantity"]
    d["minutos"] = (d["cierre"] - d["apertura"]).dt.total_seconds() / 60
    return d.sort_values("apertura").reset_index(drop=True)


def por_dia(d: pd.DataFrame) -> pd.DataFrame:
    filas = []
    for fecha, g in d.groupby("fecha"):
        dirs = g["Opening direction"].tolist()
        filas.append(
            {
                "fecha": fecha,
                "ops": len(g),
                "compras": dirs.count("Buy"),
                "ventas": dirs.count("Sell"),
                "cambios_direccion": sum(a != b for a, b in zip(dirs, dirs[1:])),
                "lotes_total": round(g["lotes"].sum(), 2),
                "lote_max": g["lotes"].max(),
                "ganadas": int((g["neto"] > 0).sum()),
                "neto_usd": round(g["neto"].sum(), 2),
                "comision_usd": round(g["Commission"].sum(), 2),
                "ops_hasta_2min": int((g["minutos"] <= 2).sum()),
                "primera_op": g["apertura"].min().strftime("%H:%M"),
                "ultima_cierre": g["cierre"].max().strftime("%H:%M"),
                "min_expuesto": round((g["cierre"].max() - g["apertura"].min()).total_seconds() / 60),
            }
        )
    return pd.DataFrame(filas)


# ---------- mercado ----------
def descargar(ticker: str, inicio: str) -> pd.DataFrame:
    import yfinance as yf

    df = yf.download(ticker, start=inicio, interval="1d", auto_adjust=False, progress=False)
    if df.empty:
        raise RuntimeError(f"Sin datos para {ticker}")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
    return df


def clase_vix(v: float) -> str:
    if pd.isna(v):
        return ""
    return "<15 calmado" if v < 15 else "15-25 normal" if v <= 25 else "25-35 fuerte" if v <= 35 else ">35 peligroso"


def mercado(inicio: str) -> pd.DataFrame:
    oro = descargar("GC=F", inicio)
    vix = descargar("^VIX", inicio)["Close"].rename("vix")
    c = oro["Close"]
    tr = pd.concat(
        [oro["High"] - oro["Low"], (oro["High"] - c.shift()).abs(), (oro["Low"] - c.shift()).abs()], axis=1
    ).max(axis=1)
    m = pd.DataFrame(
        {
            "open": oro["Open"],
            "high": oro["High"],
            "low": oro["Low"],
            "close": c,
            "rango": oro["High"] - oro["Low"],
            "atr14": tr.ewm(alpha=1 / 14, adjust=False).mean(),
            "cambio_dia_pct": (c / c.shift() - 1) * 100,
            "gap_apertura": oro["Open"] - c.shift(),
            "sma20": c.rolling(20).mean(),
            "sma50": c.rolling(50).mean(),
            "cambio_5d_pct": (c / c.shift(5) - 1) * 100,
        }
    ).join(vix)
    m["rango_vs_atr"] = m["rango"] / m["atr14"].shift()  # rango del día vs ATR de los días previos
    m["cierre_vs_sma20"] = np.where(m["close"] > m["sma20"], "arriba", "abajo")
    m["cierre_vs_sma50"] = np.where(m["close"] > m["sma50"], "arriba", "abajo")
    m["cuerpo_pct_rango"] = (c - oro["Open"]).abs() / m["rango"] * 100  # 100 = día muy direccional
    m["vix_clase"] = m["vix"].map(clase_vix)
    m.index.name = "fecha"
    return m.reset_index()


# ---------- salida ----------
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sin-mercado", action="store_true")
    ap.add_argument("--inicio", default="2026-03-01")
    args = ap.parse_args()

    ops = cargar_operaciones() if OPS.exists() else None
    dias_ops = por_dia(ops) if ops is not None else None

    if args.sin_mercado:
        if dias_ops is None:
            raise SystemExit("Falta data/operaciones.csv")
        tabla = dias_ops
    else:
        tabla = mercado(args.inicio)
        if dias_ops is not None:
            tabla = tabla.merge(dias_ops, on="fecha", how="outer").sort_values("fecha")
    tabla["operaste"] = tabla["ops"].notna() if "ops" in tabla else False
    tabla["tu_veredicto"] = ""  # tú marcas: viable / no viable

    tabla["fecha"] = pd.to_datetime(tabla["fecha"]).dt.strftime("%Y-%m-%d")
    tabla = tabla.round(2)
    SALIDA.parent.mkdir(exist_ok=True)
    with pd.ExcelWriter(SALIDA) as w:
        tabla.to_excel(w, sheet_name="Dias", index=False)
        if ops is not None:
            ops.drop(columns=["fecha"]).to_excel(w, sheet_name="Operaciones", index=False)
    tabla.to_csv(SALIDA.with_suffix(".csv"), index=False)
    print(f"{len(tabla)} días -> {SALIDA}")


if __name__ == "__main__":
    main()
