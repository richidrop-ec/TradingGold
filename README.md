# TradingGold
Análisis diario del oro

Genera cada día de semana un reporte descriptivo del oro (futuros `GC=F`) con:
rango y volatilidad (ATR, Bollinger), soporte/resistencia de 60 días, medias móviles
(SMA 20/50/200), RSI(14), MACD y variaciones por periodo.

Los reportes quedan en [`reports/`](reports/); el más reciente es [`reports/ultimo.md`](reports/ultimo.md).

> Es una herramienta de análisis, no da señales de compra/venta ni es asesoría financiera.

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
