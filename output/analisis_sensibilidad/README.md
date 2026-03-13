# Informe de Análisis de Sensibilidad

Este informe detalla los impactos marginales y cuellos de botella del sistema de transporte.

## 1. Modelo de Costo Mínimo (M1)
### Precios Sombra (Shadow Prices) Clave
| Restricción | Precio Sombra | Significado |
|---|---|---|
| Node_3 | 15.00 | Costo marginal por unidad extra |
| Node_4 | -42.00 | Costo marginal por unidad extra |
| Node_5 | -1.00 | Costo marginal por unidad extra |
| Node_6 | 15.00 | Costo marginal por unidad extra |
| Node_7 | -1.00 | Costo marginal por unidad extra |
| Node_8 | -8.00 | Costo marginal por unidad extra |
| Node_9 | 5.00 | Costo marginal por unidad extra |
| Node_11 | 23.00 | Costo marginal por unidad extra |
| Node_12 | -10.00 | Costo marginal por unidad extra |
| Node_13 | -11.00 | Costo marginal por unidad extra |
| Node_15 | 4.00 | Costo marginal por unidad extra |
| Node_16 | 24.00 | Costo marginal por unidad extra |
| Node_17 | 22.00 | Costo marginal por unidad extra |
| Node_18 | -25.00 | Costo marginal por unidad extra |
| Node_19 | 1.00 | Costo marginal por unidad extra |
| Node_21 | -1.00 | Costo marginal por unidad extra |
| Node_22 | -21.00 | Costo marginal por unidad extra |
| Node_23 | 7.00 | Costo marginal por unidad extra |
| Node_24 | -5.00 | Costo marginal por unidad extra |
| Node_25 | 8.00 | Costo marginal por unidad extra |
| Node_28 | 3.00 | Costo marginal por unidad extra |
| Node_29 | -13.00 | Costo marginal por unidad extra |
| Node_30 | 9.00 | Costo marginal por unidad extra |
| Node_31 | -30.00 | Costo marginal por unidad extra |
| Node_32 | -7.00 | Costo marginal por unidad extra |
| Node_33 | 20.00 | Costo marginal por unidad extra |
| Node_34 | 5.00 | Costo marginal por unidad extra |
| Node_35 | 5.00 | Costo marginal por unidad extra |
| Node_36 | 19.00 | Costo marginal por unidad extra |
| Node_37 | -23.00 | Costo marginal por unidad extra |
| Node_38 | 24.00 | Costo marginal por unidad extra |
| Node_39 | 3.00 | Costo marginal por unidad extra |
| Node_41 | 1.00 | Costo marginal por unidad extra |
| Node_42 | -14.00 | Costo marginal por unidad extra |
| Node_43 | -3.00 | Costo marginal por unidad extra |
| Node_44 | 10.00 | Costo marginal por unidad extra |
| Node_46 | 20.00 | Costo marginal por unidad extra |
| Node_47 | 3.00 | Costo marginal por unidad extra |
| Node_49 | -4.00 | Costo marginal por unidad extra |
| Node_50 | 5.00 | Costo marginal por unidad extra |
| Node_53 | 1.00 | Costo marginal por unidad extra |
| Node_55 | 8.00 | Costo marginal por unidad extra |
| Node_56 | 27.00 | Costo marginal por unidad extra |
| Node_57 | -6.00 | Costo marginal por unidad extra |
| Node_58 | 5.00 | Costo marginal por unidad extra |
| Node_59 | 20.00 | Costo marginal por unidad extra |
| Node_60 | 10.00 | Costo marginal por unidad extra |
| Node_62 | 7.00 | Costo marginal por unidad extra |
| Node_63 | 14.00 | Costo marginal por unidad extra |
| Node_65 | 5.00 | Costo marginal por unidad extra |
| Node_66 | -4.00 | Costo marginal por unidad extra |
| Node_67 | -6.00 | Costo marginal por unidad extra |
| Node_68 | -29.00 | Costo marginal por unidad extra |
| Node_70 | 20.00 | Costo marginal por unidad extra |
| Node_71 | -21.00 | Costo marginal por unidad extra |
| Node_72 | 16.00 | Costo marginal por unidad extra |
| Node_73 | -12.00 | Costo marginal por unidad extra |
| Node_74 | 1.00 | Costo marginal por unidad extra |
| Node_75 | -21.00 | Costo marginal por unidad extra |
| Node_77 | 4.00 | Costo marginal por unidad extra |
| Global_Supply | 83.00 | Costo de la última unidad enviada |
| Global_Demand | 39.00 | Costo de la última unidad enviada |

### Costos Reducidos (Oportunidades de Mejora)
Muestra cuánto debería bajar el costo de un arco para ser utilizado.

| Arco | Costo Actual | Costo Reducido | Nuevo Costo Objetivo |
|---|---|---|---|
| 27->22 | 40 | 61.00 | -21.00 |
| 65->8 | 48 | 61.00 | -13.00 |
| 63->52 | 45 | 59.00 | -14.00 |
| 65->22 | 31 | 57.00 | -26.00 |
| 54->71 | 34 | 55.00 | -21.00 |
| 45->49 | 50 | 54.00 | -4.00 |
| 53->43 | 50 | 54.00 | -4.00 |
| 40->8 | 45 | 53.00 | -8.00 |
| 69->22 | 31 | 52.00 | -21.00 |
| 54->22 | 31 | 52.00 | -21.00 |

---

## 2. Modelo de Flujo Máximo (M2)
**Flujo Máximo Total:** 532 unidades.

### Cuellos de Botella Críticos
Arcos cuya capacidad limita el flujo de toda la red. Aumentar una unidad de capacidad en estos arcos aumenta el flujo total en el valor indicado.

| Arco | Capacidad Actual | Impacto Marginal en Flujo |
|---|---|---|
| 1->37 | 43 | 1.00 |
| 1->29 | 28 | 1.00 |
| 1->75 | 47 | 1.00 |
| 1->18 | 42 | 1.00 |
| 1->4 | 59 | 1.00 |
| 2->31 | 83 | 1.00 |
| 2->42 | 53 | 1.00 |
| 2->68 | 23 | 1.00 |
| 2->73 | 54 | 1.00 |
| 2->4 | 100 | 1.00 |
