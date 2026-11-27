"""Análisis del diario de trading (data/diario.csv).

Mide disciplina y resultados con los datos que el trader declaró en su diario compacto.
No evalúa mercado ni da señales; audita el proceso (plan, ventana, confirmación, riesgo).

Uso:
    python analisis_diario.py            # genera reports/analisis_diario.md
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

RUTA = Path("data/diario.csv")
SALIDA = Path("reports/analisis_diario.md")

REGLAS = {
    "plan": "Respetó el plan",
    "entrada": "Entrada correcta",
    "stop": "Stop respetado",
    "gestion": "Gestión correcta",
    "sin_aumento_riesgo": "Sin aumento de riesgo",
    "ventana": "Respetó la ventana (30 min)",
    "conf_b": "Respetó confirmación B",
    "max_1_trade": "Máximo 1 trade",
    "no_movio_stop": "No movió el stop",
}


def cargar() -> pd.DataFrame:
    df = pd.read_csv(RUTA, parse_dates=["fecha"])
    for col in list(REGLAS) + ["cerro_a_tiempo"]:
        df[col] = df[col].str.strip().str.lower().eq("si")
    df["emocion_principal"] = df["emocion"].str.split("/").str[0].str.strip()
    ejecucion = ["entrada", "stop", "gestion", "sin_aumento_riesgo"]
    df["dia_limpio"] = df["plan"] & df[ejecucion].all(axis=1)
    return df


def fmt(v: float | None, signo: bool = True) -> str:
    return "n/d" if v is None or pd.isna(v) else (f"{v:+.1f}%" if signo else f"{v:.1f}%")


def tabla_grupo(df: pd.DataFrame, clave: str, titulo: str) -> list[str]:
    filas = [f"| {titulo} | Días | Suma % | Promedio % | Trades prom. |", "|---|---|---|---|---|"]
    for nombre, g in df.groupby(clave, sort=False):
        r = g["resultado_pct"]
        filas.append(
            f"| {nombre} | {len(g)} | {fmt(r.sum() if r.notna().any() else None)} | "
            f"{fmt(r.mean())} | {g['trades'].mean():.1f} |"
        )
    return filas


def racha_maxima(serie: pd.Series) -> int:
    mejor = actual = 0
    for v in serie:
        actual = actual + 1 if v else 0
        mejor = max(mejor, actual)
    return mejor


def reporte(df: pd.DataFrame) -> str:
    con_pct = df.dropna(subset=["resultado_pct"])
    total = con_pct["resultado_pct"].sum()
    n = len(df)

    cumplimiento = ["| Regla | Días cumplida | % |", "|---|---|---|"]
    for col, nombre in REGLAS.items():
        k = int(df[col].sum())
        cumplimiento.append(f"| {nombre} | {k} de {n} | {k / n * 100:.0f}% |")

    df = df.assign(
        plan_txt=df["plan"].map({True: "Respetó plan", False: "No respetó plan"}),
        trades_grupo=pd.cut(df["trades"], [0, 2, 6, 99], labels=["1–2 trades", "3–6 trades", "7+ trades"]),
        vix_grupo=df["vix"].replace({"15-26": "15–25", "15-25": "15–25", ">25": ">25"}),
    )
    df["trades_grupo"] = df["trades_grupo"].astype(str)

    exp = df.dropna(subset=["exposicion_min"])
    exp_txt = ", ".join(f"{d:%d/%m}: {int(m)} min" for d, m in zip(exp["fecha"], exp["exposicion_min"]))

    peor = con_pct.loc[con_pct["resultado_pct"].idxmin()]
    mejor = con_pct.loc[con_pct["resultado_pct"].idxmax()]
    limpios = df.loc[df["dia_limpio"], "fecha"].dt.strftime("%d/%m").tolist()
    ganó_roto = df[(df["resultado_pct"] > 0) & (~df["plan"])]

    partes = [
        "# Análisis de disciplina — diario de trading (marzo 2026)",
        "",
        f"Fuente: `data/diario.csv`, {n} registros del diario compacto (15–31/03/2026, XAUUSD). "
        "Los % son los que el trader declaró, sumados de forma simple (no compuesta) y sin saber en qué cuenta ocurrió cada uno.",
        "",
        "> ⚠️ Muestra muy pequeña (9 sesiones). Sirve para ver patrones de conducta, no para sacar conclusiones estadísticas.",
        "",
        "## Resumen",
        f"- Suma declarada: **{fmt(total)}** en {len(con_pct)} registros con %. "
        "El 16/03 no tiene % (“cuenta perdida”), así que la suma real es **peor** que esta cifra.",
        f"- Mejor registro: {mejor['fecha']:%d/%m} ({fmt(mejor['resultado_pct'])}). "
        f"Peor: {peor['fecha']:%d/%m} ({fmt(peor['resultado_pct'])}).",
        f"- Días limpios (plan sí + entrada, stop, gestión y riesgo ✔): **{len(limpios)} de {n}** "
        f"({', '.join(limpios) if limpios else 'ninguno'}). Racha máxima: **{racha_maxima(df['dia_limpio'])}**.",
        f"- Días en que ganó rompiendo el plan: {len(ganó_roto)} "
        f"({', '.join(ganó_roto['fecha'].dt.strftime('%d/%m'))}). "
        "Según tu propia regla, esas ganancias no validan la operación y reinician la racha.",
        "",
        "## Cumplimiento de reglas",
        *cumplimiento,
        "",
        "## Resultado según respeto del plan",
        *tabla_grupo(df, "plan_txt", "Grupo"),
        "",
        "## Resultado según número de trades",
        *tabla_grupo(df, "trades_grupo", "Grupo"),
        "",
        "## Resultado según emoción dominante",
        *tabla_grupo(df, "emocion_principal", "Emoción"),
        "",
        "## Resultado según VIX (clasificación del diario)",
        *tabla_grupo(df, "vix_grupo", "VIX"),
        "",
        "## Exposición real vs. ventana de 30 min",
        f"Registros con minutos reales: {exp_txt}. "
        f"Cerró a tiempo en {int(df['cerro_a_tiempo'].sum())} de {n} sesiones. "
        "En los demás días no quedó anotado el tiempo exacto.",
        "",
        "## Lectura (descriptiva)",
        f"1. **Máximo 1 trade no se cumplió ningún día** ({int(df['max_1_trade'].sum())} de {n}). Es la regla más rota.",
        f"2. **Confirmación B respetada solo {int(df['conf_b'].sum())} de {n} días**; ese día fue el único limpio.",
        f"3. Las sesiones con 7 o más trades suman {fmt(df.loc[df['trades'] >= 7, 'resultado_pct'].sum())} "
        "(sin contar el 16/03, que fue cuenta perdida con 10 trades). Más operaciones coincidió con peor resultado.",
        f"4. Las emociones negativas (rabia, urgencia, FOMO) aparecen en "
        f"{int(df['emocion_principal'].isin(['rabia', 'urgencia', 'FOMO']).sum())} de {n} sesiones y "
        f"suman {fmt(df.loc[df['emocion_principal'].isin(['rabia', 'urgencia', 'FOMO']), 'resultado_pct'].sum())}; "
        f"con “control” suman {fmt(df.loc[df['emocion_principal'] == 'control', 'resultado_pct'].sum())}.",
        f"5. **El resultado no mide la disciplina:** los días que rompió el plan sumaron "
        f"{fmt(df.loc[~df['plan'], 'resultado_pct'].sum())} y los que lo respetó "
        f"{fmt(df.loc[df['plan'], 'resultado_pct'].sum())}. Ganar con el plan roto "
        "refuerza justo el hábito que más riesgo le genera al challenge.",
        "6. Inconsistencia a revisar: el 25–26/03 marcó “respetó plan” y “respetó ventana” pero también “no cerró a tiempo” "
        "y “sin aumento de riesgo ✖”.",
        "",
        "---",
        "*Análisis del proceso con datos declarados por el trader. No es asesoría financiera ni indica cuándo operar.*",
        "",
    ]
    return "\n".join(partes)


def main() -> None:
    df = cargar()
    SALIDA.parent.mkdir(exist_ok=True)
    SALIDA.write_text(reporte(df), encoding="utf-8")
    print(f"Análisis guardado en {SALIDA}")


if __name__ == "__main__":
    main()
