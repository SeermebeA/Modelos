# Modelo 1: Flujo al Costo Minimo
**Metodologia: Algoritmica (NetworkX / NX)**

## Descripcion del Problema

Se busca transportar **500 unidades** desde los nodos origen (1, 2) hacia los nodos
destino (78, 79, 80), **minimizando el costo total** de transporte a traves de la red.

### Restriccion adicional
Al menos el **20% del flujo total** (100 unidades) debe llegar al **nodo 80**.

## Parametros del Modelo

| Parametro | Valor |
|---|---|
| Flujo total requerido | 500 |
| Minimo al nodo 80 (20%) | 100 |
| Nodos origen | [1, 2] |
| Nodos destino | [78, 79, 80] |

## Algoritmo Utilizado

Se utiliza **`nx.min_cost_flow()`** de NetworkX, que implementa el algoritmo de
**caminos mas cortos sucesivos** (Successive Shortest Path Algorithm).

### Modelado de la restriccion del 20%:
1. Se crea un **super-origen** (nodo 0) conectado a los nodos 1 y 2 con costo 0.
2. Se crea un **super-destino** (nodo 81) que recibe flujo de 78, 79 y 80.
3. Para forzar que al menos 100 unidades lleguen al nodo 80, se crea un
   **nodo auxiliar** (nodo 82) con capacidad exacta de 100 entre el nodo 80
   y el nodo 82, y luego del 82 al super-destino.
4. El flujo excedente del nodo 80 va directo al super-destino.

## Funcionamiento del Codigo

```
cargar_datos()          -> Lee CSV con 391 arcos
construir_grafo()       -> Crea DiGraph con capacity, weight, distance
agregar_super_nodos()   -> Agrega nodos 0, 81, 82 y demandas
resolver_flujo()        -> Ejecuta min_cost_flow()
analizar_resultados()   -> Extrae metricas de la solucion
generar_grafica()       -> PNG con layout izquierda(entrada) -> derecha(salida)
generar_readme()        -> Este archivo
```

## Resultados

### Resumen General

| Metrica | Valor |
|---|---|
| **Costo total minimo** | **44321** |
| Restriccion nodo 80 (>= 100) | **SI** |
| Arcos activos | 77 |
| **Tiempo de ejecucion** | **0.0084 segundos** |

### Flujo por Origen

| Nodo Origen | Flujo Enviado |
|---|---|
| Nodo 1 | 219 |
| Nodo 2 | 281 |

### Flujo por Destino

| Nodo Destino | Flujo Recibido | Porcentaje |
|---|---|---|
| Nodo 78 | 131 | 26.2% |
| Nodo 79 | 194 | 38.8% |
| Nodo 80 | 175 | 35.0% |

### Arcos Activos (flujo > 0)

| Origen | Destino | Flujo | Capacidad | Costo Unitario | Costo x Flujo |
|---|---|---|---|---|---|
| 1 | 37 | 43 | 43 | 35 | 1505 |
| 1 | 29 | 28 | 28 | 39 | 1092 |
| 1 | 75 | 47 | 47 | 9 | 423 |
| 1 | 18 | 42 | 42 | 41 | 1722 |
| 1 | 4 | 59 | 59 | 36 | 2124 |
| 37 | 13 | 43 | 89 | 12 | 516 |
| 29 | 61 | 28 | 58 | 13 | 364 |
| 75 | 49 | 41 | 60 | 17 | 697 |
| 75 | 35 | 6 | 66 | 26 | 156 |
| 18 | 8 | 42 | 61 | 17 | 714 |
| 4 | 24 | 25 | 25 | 33 | 825 |
| 4 | 67 | 22 | 22 | 30 | 660 |
| 4 | 12 | 26 | 26 | 17 | 442 |
| 4 | 22 | 25 | 25 | 6 | 150 |
| 4 | 71 | 29 | 52 | 21 | 609 |
| 2 | 31 | 83 | 83 | 42 | 3486 |
| 2 | 42 | 53 | 53 | 37 | 1961 |
| 2 | 68 | 23 | 23 | 19 | 437 |
| 2 | 73 | 54 | 54 | 7 | 378 |
| 2 | 4 | 68 | 100 | 41 | 2788 |
| 31 | 22 | 29 | 86 | 9 | 261 |
| 31 | 12 | 21 | 21 | 12 | 252 |
| 31 | 66 | 33 | 33 | 21 | 693 |
| 42 | 53 | 38 | 48 | 15 | 570 |
| 42 | 5 | 15 | 29 | 13 | 195 |
| 68 | 41 | 23 | 58 | 30 | 690 |
| 73 | 57 | 7 | 93 | 6 | 42 |
| 73 | 35 | 47 | 87 | 17 | 799 |
| 53 | 63 | 38 | 38 | 7 | 266 |
| 49 | 39 | 41 | 86 | 7 | 287 |
| 67 | 10 | 22 | 46 | 6 | 132 |
| 35 | 44 | 45 | 86 | 5 | 225 |
| 35 | 63 | 8 | 47 | 9 | 72 |
| 5 | 25 | 15 | 22 | 9 | 135 |
| 8 | 74 | 8 | 70 | 9 | 72 |
| 8 | 23 | 22 | 95 | 15 | 330 |
| 8 | 10 | 12 | 71 | 8 | 96 |
| 22 | 21 | 41 | 41 | 20 | 820 |
| 22 | 58 | 13 | 27 | 26 | 338 |
| 12 | 39 | 47 | 94 | 13 | 611 |
| 66 | 6 | 22 | 94 | 19 | 418 |
| 66 | 58 | 11 | 65 | 9 | 99 |
| 41 | 25 | 23 | 29 | 7 | 161 |
| 13 | 47 | 43 | 83 | 14 | 602 |
| 24 | 77 | 25 | 36 | 9 | 225 |
| 61 | 23 | 12 | 29 | 7 | 84 |
| 61 | 34 | 16 | 78 | 5 | 80 |
| 71 | 44 | 27 | 27 | 13 | 351 |
| 71 | 15 | 2 | 90 | 25 | 50 |
| 57 | 34 | 7 | 48 | 11 | 77 |
| 25 | 72 | 38 | 69 | 8 | 304 |
| 6 | 11 | 22 | 22 | 5 | 110 |
| 47 | 36 | 43 | 87 | 16 | 688 |
| 44 | 46 | 72 | 83 | 10 | 720 |
| 63 | 38 | 46 | 75 | 10 | 460 |
| 15 | 56 | 2 | 95 | 23 | 46 |
| 23 | 11 | 34 | 46 | 16 | 544 |
| 77 | 11 | 5 | 60 | 19 | 95 |
| 77 | 16 | 20 | 83 | 20 | 400 |
| 39 | 70 | 32 | 32 | 6 | 192 |
| 39 | 56 | 56 | 56 | 24 | 1344 |
| 10 | 50 | 34 | 34 | 5 | 170 |
| 34 | 33 | 23 | 23 | 8 | 184 |
| 21 | 62 | 41 | 82 | 8 | 328 |
| 58 | 16 | 24 | 45 | 19 | 456 |
| 74 | 62 | 8 | 56 | 6 | 48 |
| 11 | 79 | 61 | 61 | 5 | 305 |
| 50 | 80 | 34 | 60 | 34 | 1156 |
| 62 | 78 | 49 | 49 | 14 | 686 |
| 33 | 80 | 23 | 82 | 19 | 437 |
| 38 | 80 | 46 | 46 | 14 | 644 |
| 36 | 79 | 43 | 90 | 20 | 860 |
| 70 | 79 | 32 | 52 | 19 | 608 |
| 16 | 78 | 44 | 47 | 15 | 660 |
| 72 | 78 | 38 | 79 | 23 | 874 |
| 56 | 79 | 58 | 91 | 12 | 696 |
| 46 | 80 | 72 | 72 | 17 | 1224 |

## Grafica

La grafica muestra el grafo con:
- **Izquierda**: Nodos origen (entradas) en verde
- **Derecha**: Nodos destino (salidas) en rojo
- **Centro**: Nodos intermedios en azul claro
- **Naranja**: Arcos con flujo > 0 (con etiquetas de flujo)

![Flujo al Costo Minimo](flujo_costo_minimo.png)
