# Análisis de disciplina — diario de trading (marzo 2026)

Fuente: `data/diario.csv`, 9 registros del diario compacto (15–31/03/2026, XAUUSD). Los % son los que el trader declaró, sumados de forma simple (no compuesta) y sin saber en qué cuenta ocurrió cada uno.

> ⚠️ Muestra muy pequeña (9 sesiones). Sirve para ver patrones de conducta, no para sacar conclusiones estadísticas.

## Resumen
- Suma declarada: **+1.1%** en 8 registros con %. El 16/03 no tiene % (“cuenta perdida”), así que la suma real es **peor** que esta cifra.
- Mejor registro: 23/03 (+7.5%). Peor: 18/03 (-6.0%).
- Días limpios (plan sí + entrada, stop, gestión y riesgo ✔): **1 de 9** (24/03). Racha máxima: **1**.
- Días en que ganó rompiendo el plan: 4 (15/03, 23/03, 30/03, 31/03). Según tu propia regla, esas ganancias no validan la operación y reinician la racha.

## Cumplimiento de reglas
| Regla | Días cumplida | % |
|---|---|---|
| Respetó el plan | 2 de 9 | 22% |
| Entrada correcta | 3 de 9 | 33% |
| Stop respetado | 6 de 9 | 67% |
| Gestión correcta | 5 de 9 | 56% |
| Sin aumento de riesgo | 2 de 9 | 22% |
| Respetó la ventana (30 min) | 2 de 9 | 22% |
| Respetó confirmación B | 1 de 9 | 11% |
| Máximo 1 trade | 0 de 9 | 0% |
| No movió el stop | 6 de 9 | 67% |

## Resultado según respeto del plan
| Grupo | Días | Suma % | Promedio % | Trades prom. |
|---|---|---|---|---|
| No respetó plan | 7 | +3.8% | +0.6% | 6.1 |
| Respetó plan | 2 | -2.7% | -1.4% | 4.5 |

## Resultado según número de trades
| Grupo | Días | Suma % | Promedio % | Trades prom. |
|---|---|---|---|---|
| 3–6 trades | 5 | +9.8% | +2.0% | 4.8 |
| 7+ trades | 3 | -10.4% | -5.2% | 8.7 |
| 1–2 trades | 1 | +1.7% | +1.7% | 2.0 |

## Resultado según emoción dominante
| Emoción | Días | Suma % | Promedio % | Trades prom. |
|---|---|---|---|---|
| rabia | 3 | -3.3% | -1.7% | 6.7 |
| urgencia | 2 | -6.5% | -3.2% | 7.5 |
| control | 3 | +10.4% | +3.5% | 4.3 |
| FOMO | 1 | +0.5% | +0.5% | 4.0 |

## Resultado según VIX (clasificación del diario)
| VIX | Días | Suma % | Promedio % | Trades prom. |
|---|---|---|---|---|
| 15–25 | 7 | -0.6% | -0.1% | 6.1 |
| >25 | 2 | +1.7% | +0.8% | 4.5 |

## Exposición real vs. ventana de 30 min
Registros con minutos reales: 23/03: 60 min, 24/03: 30 min, 30/03: 37 min, 31/03: 67 min. Cerró a tiempo en 1 de 9 sesiones. En los demás días no quedó anotado el tiempo exacto.

## Lectura (descriptiva)
1. **Máximo 1 trade no se cumplió ningún día** (0 de 9). Es la regla más rota.
2. **Confirmación B respetada solo 1 de 9 días**; ese día fue el único limpio.
3. Las sesiones con 7 o más trades suman -10.4% (sin contar el 16/03, que fue cuenta perdida con 10 trades). Más operaciones coincidió con peor resultado.
4. Las emociones negativas (rabia, urgencia, FOMO) aparecen en 6 de 9 sesiones y suman -9.3%; con “control” suman +10.4%.
5. **El resultado no mide la disciplina:** los días que rompió el plan sumaron +3.8% y los que lo respetó -2.7%. Ganar con el plan roto refuerza justo el hábito que más riesgo le genera al challenge.
6. Inconsistencia a revisar: el 25–26/03 marcó “respetó plan” y “respetó ventana” pero también “no cerró a tiempo” y “sin aumento de riesgo ✖”.

---
*Análisis del proceso con datos declarados por el trader. No es asesoría financiera ni indica cuándo operar.*
