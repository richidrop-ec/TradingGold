# TradingGold
Análisis diario del oro

Genera cada día de semana un reporte descriptivo del oro (futuros `GC=F`) con:
rango y volatilidad (ATR, Bollinger), soporte/resistencia de 60 días, medias móviles
(SMA 20/50/200), RSI(14), MACD y variaciones por periodo.

Los reportes quedan en [`reports/`](reports/); el más reciente es [`reports/ultimo.md`](reports/ultimo.md).

> Es una herramienta de análisis, no da señales de compra/venta ni es asesoría financiera.

## Análisis del diario de trading
`data/diario.csv` guarda el diario compacto (marzo 2026, XAUUSD) y `analisis_diario.py`
genera [`reports/analisis_diario.md`](reports/analisis_diario.md): cumplimiento de reglas,
resultado según plan, número de trades, emoción y VIX, y rachas de días limpios.
Para añadir sesiones nuevas, agrega filas al CSV y ejecuta `python analisis_diario.py`.

## Uso local
```bash
pip install -r requirements.txt
python analisis_oro.py                 # datos reales
python analisis_oro.py --demo          # datos de ejemplo (sin internet)
python analisis_oro.py --ticker XAUUSD=X   # oro spot
```

## Automático
El workflow `.github/workflows/reporte-diario.yml` corre de lunes a viernes
(5:30 p.m. hora de Bogotá), genera el reporte y lo guarda en el repositorio.
También puede lanzarse a mano desde la pestaña **Actions → Run workflow**.

## Escenarios de entrada
`escenarios_oro.py` prueba con reglas fijas, sobre velas de 1h de GC=F (unos 2 años), si cada
escenario tuvo ventaja: ruptura del máximo/mínimo de ayer a favor de la tendencia, retroceso a
un FVG de 1h a favor de la EMA50, barridas, rango asiático y un control al azar. El resultado
queda en [`reports/escenarios.md`](reports/escenarios.md), en R (múltiplos del riesgo).
```bash
python escenarios_oro.py
```
