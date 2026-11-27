"""Análisis diario del oro (XAU/USD).

Descarga precios, calcula indicadores técnicos y genera un reporte en
reports/AAAA-MM-DD.md. El reporte es descriptivo: NO da señales de compra o venta.

Uso:
    python analisis_oro.py                 # datos reales (yfinance, futuros GC=F)
    python analisis_oro.py --demo          # datos sintéticos para probar el código
    python analisis_oro.py --ticker XAUUSD=X
"""
from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd


# ---------- datos ----------
def descargar(ticker: str, periodo: str = "2y") -> pd.DataFrame:
    import yfinance as yf

    df = yf.download(ticker, period=periodo, interval="1d", auto_adjust=False, progress=False)
    if df.empty:
        raise RuntimeError(f"No se obtuvieron datos para {ticker}")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df[["Open", "High", "Low", "Close"]].dropna()


def datos_demo(n: int = 400) -> pd.DataFrame:
    rng = np.random.default_rng(7)
    cierre = 2000 * np.exp(np.cumsum(rng.normal(0.0004, 0.009, n)))
    abre = cierre * (1 + rng.normal(0, 0.002, n))
    alto = np.maximum(abre, cierre) * (1 + np.abs(rng.normal(0, 0.003, n)))
    bajo = np.minimum(abre, cierre) * (1 - np.abs(rng.normal(0, 0.003, n)))
    idx = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=n)
    return pd.DataFrame({"Open": abre, "High": alto, "Low": bajo, "Close": cierre}, index=idx)


# ---------- indicadores ----------
def rsi(cierre: pd.Series, n: int = 14) -> pd.Series:
    d = cierre.diff()
    ganancia = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    perdida = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    rs = ganancia / perdida.replace(0, np.nan)
    return 100 - 100 / (1 + rs)


def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    cierre_prev = df["Close"].shift()
    tr = pd.concat(
        [df["High"] - df["Low"], (df["High"] - cierre_prev).abs(), (df["Low"] - cierre_prev).abs()],
        axis=1,
    ).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False).mean()


def calcular(df: pd.DataFrame) -> pd.DataFrame:
    c = df["Close"]
    out = df.copy()
    for n in (20, 50, 200):
        out[f"SMA{n}"] = c.rolling(n).mean()
    out["RSI14"] = rsi(c)
    ema12, ema26 = c.ewm(span=12, adjust=False).mean(), c.ewm(span=26, adjust=False).mean()
    out["MACD"] = ema12 - ema26
    out["MACD_senal"] = out["MACD"].ewm(span=9, adjust=False).mean()
    media, desv = c.rolling(20).mean(), c.rolling(20).std()
    out["BB_sup"], out["BB_inf"] = media + 2 * desv, media - 2 * desv
    out["ATR14"] = atr(df)
    return out


def soporte_resistencia(df: pd.DataFrame, ventana: int = 60) -> tuple[float, float]:
    reciente = df.tail(ventana)
    return float(reciente["Low"].min()), float(reciente["High"].max())


# ---------- reporte ----------
def pct(a: float, b: float) -> float:
    return (a / b - 1) * 100


def lectura_rsi(v: float) -> str:
    if v >= 70:
        return "zona de sobrecompra (≥70)"
    if v <= 30:
        return "zona de sobreventa (≤30)"
    return "zona neutral (30–70)"


def generar_reporte(df: pd.DataFrame, ticker: str, demo: bool) -> str:
    x = calcular(df)
    u, p = x.iloc[-1], x.iloc[-2]
    sop, res = soporte_resistencia(df)
    cierre = u["Close"]

    def rel(media: float) -> str:
        return "por encima" if cierre > media else "por debajo"

    cruce = "MACD sobre su señal" if u["MACD"] > u["MACD_senal"] else "MACD bajo su señal"
    ancho_bb = (u["BB_sup"] - u["BB_inf"]) / cierre * 100
    aviso_demo = "\n> ⚠️ **DATOS DE EJEMPLO (modo demo), no son precios reales.**\n" if demo else ""

    return f"""# Análisis diario del oro — {x.index[-1]:%Y-%m-%d}
{aviso_demo}
Instrumento: `{ticker}` · Cierre: **{cierre:,.2f}** ({pct(cierre, p['Close']):+.2f}% vs. sesión anterior)

## Rango y volatilidad
| Métrica | Valor |
|---|---|
| Máximo / mínimo del día | {u['High']:,.2f} / {u['Low']:,.2f} |
| ATR(14) | {u['ATR14']:,.2f} ({u['ATR14'] / cierre * 100:.2f}% del precio) |
| Ancho Bandas de Bollinger | {ancho_bb:.2f}% |
| Soporte (mín. 60 días) | {sop:,.2f} ({pct(cierre, sop):+.1f}% desde el cierre) |
| Resistencia (máx. 60 días) | {res:,.2f} ({pct(res, cierre):+.1f}% hasta ella) |

## Tendencia (medias móviles)
| Media | Valor | Precio está |
|---|---|---|
| SMA 20 | {u['SMA20']:,.2f} | {rel(u['SMA20'])} |
| SMA 50 | {u['SMA50']:,.2f} | {rel(u['SMA50'])} |
| SMA 200 | {u['SMA200']:,.2f} | {rel(u['SMA200'])} |

## Momentum
- **RSI(14):** {u['RSI14']:.1f} — {lectura_rsi(u['RSI14'])}
- **MACD:** {u['MACD']:.2f} (señal {u['MACD_senal']:.2f}) — {cruce}

## Variación
| 1 semana | 1 mes | 3 meses | 1 año |
|---|---|---|---|
| {pct(cierre, df['Close'].iloc[-6]):+.1f}% | {pct(cierre, df['Close'].iloc[-22]):+.1f}% | {pct(cierre, df['Close'].iloc[-64]):+.1f}% | {pct(cierre, df['Close'].iloc[-253]):+.1f}% |

---
*Reporte descriptivo generado automáticamente a partir de datos históricos. No es asesoría financiera ni una señal de compra o venta.*
"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticker", default="GC=F", help="GC=F (futuros oro) o XAUUSD=X (spot)")
    ap.add_argument("--demo", action="store_true", help="usa datos sintéticos")
    args = ap.parse_args()

    df = datos_demo() if args.demo else descargar(args.ticker)
    texto = generar_reporte(df, args.ticker if not args.demo else "DEMO", args.demo)

    carpeta = Path("reports")
    carpeta.mkdir(exist_ok=True)
    destino = carpeta / f"{df.index[-1]:%Y-%m-%d}.md"
    destino.write_text(texto, encoding="utf-8")
    (carpeta / "ultimo.md").write_text(texto, encoding="utf-8")
    print(f"Reporte guardado en {destino}")


if __name__ == "__main__":
    main()
