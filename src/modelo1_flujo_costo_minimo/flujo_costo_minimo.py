"""
Modelo 1: Flujo al Costo Mínimo
================================
Problema: Enviar 500 unidades desde los nodos origen (1, 2) a los nodos
destino (78, 79, 80), minimizando el costo total de transporte.
Restricción: Al menos 20% (100 unidades) deben llegar al nodo 80.

Algoritmo: min_cost_flow() de NetworkX (implementación basada en el
algoritmo de caminos más cortos sucesivos).

Estructura del script:
    1. cargar_datos()          - Lectura del CSV
    2. construir_grafo()       - Grafo dirigido con capacidades/costos
    3. agregar_super_nodos()   - Super-origen/destino + restricción 20%
    4. resolver_flujo()        - Ejecución del algoritmo
    5. analizar_resultados()   - Extracción de métricas
    6. generar_grafica()       - Visualización con layout izq→der
    7. generar_readme()        - README.md con explicación y resultados
"""

import os
import sys
import time
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# ─── Configuración de rutas ────────────────────────────────────────────────
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATA_PATH = os.path.join(BASE_DIR, 'data', 'matriz_de_datos.csv')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output', 'modelo1')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ─── Parámetros del modelo ─────────────────────────────────────────────────
FLUJO_TOTAL = 500
MIN_FLUJO_NODO_80 = int(FLUJO_TOTAL * 0.20)  # 100 unidades
NODOS_ORIGEN = [1, 2]
NODOS_DESTINO = [78, 79, 80]
SUPER_ORIGEN = 0
SUPER_DESTINO = 81
NODO_80_OBLIGATORIO = 82  # Nodo auxiliar para forzar mínimo al nodo 80


def cargar_datos(ruta_csv):
    """
    Lee el archivo CSV con la matriz de datos del grafo.

    Parámetros:
        ruta_csv (str): Ruta absoluta al archivo CSV.

    Retorna:
        pd.DataFrame: DataFrame con columnas [Origen, Destino, Costo, Distancia, Capacidad].

    El CSV debe tener las siguientes columnas:
        - Origen: nodo de inicio del arco
        - Destino: nodo de fin del arco
        - Costo: costo unitario de transporte por el arco
        - Distancia: distancia física del arco
        - Capacidad: capacidad máxima de flujo del arco
    """
    df = pd.read_csv(ruta_csv)
    print(f"  Arcos leídos del CSV: {len(df)}")
    return df


def construir_grafo(df):
    """
    Construye un grafo dirigido (DiGraph) a partir del DataFrame.

    Parámetros:
        df (pd.DataFrame): DataFrame con las columnas del CSV.

    Retorna:
        nx.DiGraph: Grafo dirigido con atributos:
            - capacity: capacidad máxima del arco
            - weight: costo unitario (usado por min_cost_flow)
            - distance: distancia del arco

    Nota: NetworkX usa el atributo 'weight' como costo en min_cost_flow(),
    por lo que mapeamos la columna 'Costo' a 'weight'.
    """
    G = nx.DiGraph()
    for _, row in df.iterrows():
        G.add_edge(
            int(row['Origen']),
            int(row['Destino']),
            capacity=int(row['Capacidad']),
            weight=int(row['Costo']),
            distance=int(row['Distancia'])
        )
    print(f"  Nodos en el grafo: {G.number_of_nodes()}")
    print(f"  Arcos en el grafo: {G.number_of_edges()}")
    return G


def agregar_super_nodos(G):
    """
    Agrega super-origen, super-destino y nodo auxiliar para modelar
    las restricciones del problema de flujo al costo mínimo.

    Parámetros:
        G (nx.DiGraph): Grafo dirigido original.

    Retorna:
        nx.DiGraph: Grafo modificado con:
            - Nodo 0 (super-origen) conectado a nodos 1 y 2 con costo 0
            - Nodo 81 (super-destino) recibe flujo de 78, 79 y 80
            - Nodo 82 (auxiliar) fuerza que al menos 100 unidades
              lleguen al nodo 80 (restricción del 20%)

    Modelado de la restricción del 20%:
        Se crea un nodo auxiliar (82) al que el nodo 80 envía exactamente
        MIN_FLUJO_NODO_80 unidades. Esto garantiza que al menos esa cantidad
        pase por el nodo 80. El excedente va directo al super-destino.
    """
    # Capacidad de salida desde cada origen (para dimensionar super-arcos)
    cap_salida_1 = sum(d['capacity'] for _, _, d in G.out_edges(1, data=True))
    cap_salida_2 = sum(d['capacity'] for _, _, d in G.out_edges(2, data=True))

    # Super-origen → orígenes (costo 0, capacidad = suma de salidas)
    G.add_edge(SUPER_ORIGEN, 1, capacity=cap_salida_1, weight=0)
    G.add_edge(SUPER_ORIGEN, 2, capacity=cap_salida_2, weight=0)

    # Capacidad de entrada a cada destino (excluyendo super-nodos)
    cap_entrada = {}
    for d_node in NODOS_DESTINO:
        cap_entrada[d_node] = sum(
            data['capacity'] for _, _, data in G.in_edges(d_node, data=True)
            if _ not in [SUPER_ORIGEN, SUPER_DESTINO, NODO_80_OBLIGATORIO]
        )

    # Destinos 78 y 79 → super-destino
    G.add_edge(78, SUPER_DESTINO, capacity=cap_entrada.get(78, FLUJO_TOTAL), weight=0)
    G.add_edge(79, SUPER_DESTINO, capacity=cap_entrada.get(79, FLUJO_TOTAL), weight=0)

    # Nodo 80 → nodo auxiliar 82 (flujo obligatorio) → super-destino
    G.add_edge(80, NODO_80_OBLIGATORIO, capacity=MIN_FLUJO_NODO_80, weight=0)
    G.add_edge(NODO_80_OBLIGATORIO, SUPER_DESTINO, capacity=MIN_FLUJO_NODO_80, weight=0)

    # Nodo 80 → super-destino (flujo adicional más allá del mínimo)
    G.add_edge(80, SUPER_DESTINO,
               capacity=cap_entrada.get(80, FLUJO_TOTAL) - MIN_FLUJO_NODO_80, weight=0)

    # Asignar demandas: oferta en super-origen, demanda en super-destino
    for node in G.nodes():
        G.nodes[node]['demand'] = 0
    G.nodes[SUPER_ORIGEN]['demand'] = -FLUJO_TOTAL   # fuente: ofrece 500
    G.nodes[SUPER_DESTINO]['demand'] = FLUJO_TOTAL    # sumidero: recibe 500

    print(f"  Super-nodos agregados (0=fuente, 81=sumidero, 82=auxiliar)")
    return G


def resolver_flujo(G):
    """
    Ejecuta el algoritmo de flujo al costo mínimo sobre el grafo.

    Parámetros:
        G (nx.DiGraph): Grafo con demandas, capacidades y costos.

    Retorna:
        tuple: (flow_dict, costo_total)
            - flow_dict (dict): Diccionario {u: {v: flujo}} con el flujo
              óptimo en cada arco.
            - costo_total (int): Suma de (costo × flujo) de todos los arcos.

    Excepciones:
        Termina el programa si el problema no es factible (capacidades
        insuficientes para transportar la demanda requerida).
    """
    try:
        flow_dict = nx.min_cost_flow(G)
        costo_total = nx.cost_of_flow(G, flow_dict)
        print(f"  Solucion encontrada - Costo total minimo: {costo_total}")
        return flow_dict, costo_total
    except nx.NetworkXUnfeasible:
        print("  ERROR: El problema no tiene solucion factible.")
        print("  Verifique las capacidades y la demanda total.")
        sys.exit(1)


def analizar_resultados(G, flow_dict, costo_total):
    """
    Extrae métricas detalladas de la solución óptima.

    Parámetros:
        G (nx.DiGraph): Grafo con atributos de arcos.
        flow_dict (dict): Solución del flujo al costo mínimo.
        costo_total (int): Costo total de la solución.

    Retorna:
        dict: Diccionario con las métricas:
            - 'costo_total': costo total mínimo
            - 'flujo_origenes': {nodo: flujo} para cada origen
            - 'flujo_destinos': {nodo: flujo} para cada destino
            - 'arcos_activos': lista de (u, v, flujo, capacidad, costo_unitario)
            - 'restriccion_cumple': bool indicando si nodo 80 >= 100
    """
    resultados = {
        'costo_total': costo_total,
        'flujo_origenes': {},
        'flujo_destinos': {},
        'arcos_activos': [],
        'restriccion_cumple': False
    }

    # Flujo desde cada origen
    for origen in NODOS_ORIGEN:
        resultados['flujo_origenes'][origen] = flow_dict[SUPER_ORIGEN].get(origen, 0)

    # Flujo hacia cada destino (excluyendo super-nodos del conteo)
    for destino in NODOS_DESTINO:
        flujo_total = sum(
            flow_dict[u].get(destino, 0) for u in G.predecessors(destino)
            if u not in [SUPER_ORIGEN, SUPER_DESTINO, NODO_80_OBLIGATORIO]
        )
        resultados['flujo_destinos'][destino] = flujo_total

    # Verificar restricción del 20% en nodo 80
    resultados['restriccion_cumple'] = resultados['flujo_destinos'].get(80, 0) >= MIN_FLUJO_NODO_80

    # Arcos con flujo > 0 (excluyendo super-nodos)
    for u in flow_dict:
        for v, flujo in flow_dict[u].items():
            if (flujo > 0
                    and u not in [SUPER_ORIGEN, NODO_80_OBLIGATORIO]
                    and v not in [SUPER_DESTINO, NODO_80_OBLIGATORIO]):
                costo_arco = G[u][v].get('weight', 0)
                cap_arco = G[u][v].get('capacity', 0)
                resultados['arcos_activos'].append((u, v, flujo, cap_arco, costo_arco))

    return resultados


def calcular_layout(G_vis):
    """
    Calcula posiciones de nodos con un layout jerárquico de izquierda a derecha:
    - IZQUIERDA: Nodos origen (1, 2) — entradas al sistema
    - DERECHA: Nodos destino (78, 79, 80) — salidas del sistema
    - CENTRO: Nodos intermedios distribuidos por capas según su distancia
      topológica a los orígenes.

    Parámetros:
        G_vis (nx.DiGraph): Grafo de visualización (sin super-nodos).

    Retorna:
        dict: {nodo: (x, y)} posiciones para matplotlib.

    Algoritmo:
        1. Calcula la distancia mínima (en saltos) de cada nodo a cualquier
           nodo origen usando BFS.
        2. Agrupa los nodos por profundidad (capas).
        3. Asigna X de izquierda a derecha (profundidad 0 = izquierda).
        4. Distribuye Y uniformemente dentro de cada capa.
        5. Añade una capa fija en el extremo derecho para los destinos.
    """
    pos = {}

    # --- Calcular profundidad BFS desde los orígenes ---
    profundidad = {}
    for origen in NODOS_ORIGEN:
        if origen in G_vis:
            distancias = nx.single_source_shortest_path_length(G_vis, origen)
            for nodo, dist in distancias.items():
                if nodo not in profundidad or dist < profundidad[nodo]:
                    profundidad[nodo] = dist

    # Asignar profundidad máxima a nodos no alcanzados desde los orígenes
    max_prof = max(profundidad.values()) if profundidad else 0
    for nodo in G_vis.nodes():
        if nodo not in profundidad:
            profundidad[nodo] = max_prof

    # --- Agrupar nodos por capa ---
    capas = {}
    for nodo, prof in profundidad.items():
        if nodo in NODOS_DESTINO:
            continue  # los destinos van en su propia capa
        if prof not in capas:
            capas[prof] = []
        capas[prof].append(nodo)

    # Número total de capas (intermedios + 1 capa de destinos)
    num_capas = max(capas.keys()) + 2 if capas else 2

    # --- Asignar posiciones X (izquierda → derecha) ---
    # Orígenes a la izquierda (x = 0), destinos a la derecha (x alto)
    for prof, nodos in capas.items():
        x = prof  # profundidad 0 → x = 0 (izquierda, orígenes)
        nodos_sorted = sorted(nodos)
        n = len(nodos_sorted)
        for i, nodo in enumerate(nodos_sorted):
            # Distribuir verticalmente con espaciado uniforme
            y = (i - (n - 1) / 2) * 1.2
            pos[nodo] = (x, y)

    # Destinos en el extremo derecho (x = num_capas)
    destinos_en_grafo = [d for d in NODOS_DESTINO if d in G_vis]
    n_dest = len(destinos_en_grafo)
    for i, nodo in enumerate(sorted(destinos_en_grafo)):
        y = (i - (n_dest - 1) / 2) * 2.5
        pos[nodo] = (num_capas, y)

    return pos


def generar_grafica(G_vis, resultados, output_dir):
    """
    Genera la visualización del grafo con el flujo óptimo.

    Parámetros:
        G_vis (nx.DiGraph): Grafo original (sin super-nodos) para visualizar.
        resultados (dict): Métricas del modelo (arcos activos, costos, etc.).
        output_dir (str): Directorio donde guardar el PNG.

    Características de la gráfica:
        - Layout jerárquico: orígenes a la IZQUIERDA, destinos a la DERECHA
        - Arcos inactivos en gris tenue
        - Arcos con flujo > 0 resaltados en naranja con etiquetas de flujo
        - Nodos coloreados: verde=origen, rojo=destino, azul=intermedio
        - Fondo oscuro estilo dark mode
    """
    pos = calcular_layout(G_vis)

    # Colores de nodos según su rol
    node_colors = []
    for node in G_vis.nodes():
        if node in NODOS_ORIGEN:
            node_colors.append('#2ecc71')   # verde - origen (entrada)
        elif node in NODOS_DESTINO:
            node_colors.append('#e74c3c')   # rojo - destino (salida)
        else:
            node_colors.append('#85c1e9')   # azul claro - intermedio

    fig, ax = plt.subplots(1, 1, figsize=(24, 16))
    fig.patch.set_facecolor('#1a1a2e')
    ax.set_facecolor('#1a1a2e')

    # 1. Dibujar todos los arcos (gris tenue, fondo)
    nx.draw_networkx_edges(G_vis, pos, edge_color='#333333', alpha=0.3,
                           arrows=True, arrowsize=8, ax=ax, width=0.5,
                           connectionstyle='arc3,rad=0.05')

    # 2. Dibujar arcos activos (naranja, resaltados)
    active_edges = [(u, v) for u, v, _, _, _ in resultados['arcos_activos']
                    if G_vis.has_edge(u, v)]
    if active_edges:
        nx.draw_networkx_edges(G_vis, pos, edgelist=active_edges,
                               edge_color='#f39c12', alpha=0.9,
                               arrows=True, arrowsize=12, ax=ax, width=2.5,
                               connectionstyle='arc3,rad=0.05')

    # 3. Dibujar nodos
    nx.draw_networkx_nodes(G_vis, pos, node_color=node_colors, node_size=400,
                           edgecolors='white', linewidths=1.0, ax=ax)
    nx.draw_networkx_labels(G_vis, pos, font_size=7, font_color='white',
                            font_weight='bold', ax=ax)

    # 4. Etiquetas de flujo en arcos activos
    edge_labels = {(u, v): f"{f}"
                   for u, v, f, _, _ in resultados['arcos_activos']
                   if G_vis.has_edge(u, v)}
    nx.draw_networkx_edge_labels(G_vis, pos, edge_labels=edge_labels,
                                 font_size=6, font_color='#f1c40f',
                                 bbox=dict(boxstyle='round,pad=0.15',
                                           facecolor='#2c3e50', alpha=0.8),
                                 ax=ax)

    # 5. Indicadores de dirección del flujo
    ax.annotate('ENTRADAS\n(Origenes)', xy=(0.05, 0.95), xycoords='axes fraction',
                fontsize=12, fontweight='bold', color='#2ecc71',
                ha='center', va='top',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='#2c3e50', alpha=0.9))
    ax.annotate('SALIDAS\n(Destinos)', xy=(0.95, 0.95), xycoords='axes fraction',
                fontsize=12, fontweight='bold', color='#e74c3c',
                ha='center', va='top',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='#2c3e50', alpha=0.9))
    # Flecha de dirección del flujo
    ax.annotate('', xy=(0.85, 0.02), xytext=(0.15, 0.02),
                xycoords='axes fraction',
                arrowprops=dict(arrowstyle='->', color='white', lw=2))
    ax.text(0.5, 0.02, 'Direccion del flujo', transform=ax.transAxes,
            fontsize=10, color='white', ha='center', va='bottom')

    # 6. Leyenda
    costo = resultados['costo_total']
    legend_patches = [
        mpatches.Patch(color='#2ecc71', label='Nodos Origen (1, 2)'),
        mpatches.Patch(color='#e74c3c', label='Nodos Destino (78, 79, 80)'),
        mpatches.Patch(color='#85c1e9', label='Nodos Intermedios'),
        mpatches.Patch(color='#f39c12', label=f'Arcos con flujo (costo total: {costo})'),
    ]
    ax.legend(handles=legend_patches, loc='lower left', fontsize=10,
              facecolor='#2c3e50', edgecolor='white', labelcolor='white')

    # 7. Título
    fd = resultados['flujo_destinos']
    ax.set_title(
        f'Modelo 1: Flujo al Costo Minimo\n'
        f'Flujo Total: {FLUJO_TOTAL} | Costo Minimo: {costo} | '
        f'Nodo 80 recibe: {fd.get(80, 0)} (>={MIN_FLUJO_NODO_80})',
        fontsize=14, fontweight='bold', color='white', pad=20)

    plt.tight_layout()
    output_path = os.path.join(output_dir, 'flujo_costo_minimo.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='#1a1a2e')
    plt.close()
    print(f"  Grafica guardada en: {output_path}")
    return output_path


def generar_readme(resultados, output_dir):
    """
    Genera un archivo README.md con la explicación completa del modelo,
    el código, el funcionamiento y los resultados obtenidos.

    Parámetros:
        resultados (dict): Métricas del modelo.
        output_dir (str): Directorio donde guardar el README.

    El README incluye:
        - Descripción del problema
        - Parámetros del modelo
        - Explicación del algoritmo
        - Resultados numéricos detallados
        - Tabla de arcos activos
    """
    fd = resultados['flujo_destinos']
    fo = resultados['flujo_origenes']
    costo = resultados['costo_total']
    cumple = "SI" if resultados['restriccion_cumple'] else "NO"

    contenido = f"""# Modelo 1: Flujo al Costo Minimo

## Descripcion del Problema

Se busca transportar **{FLUJO_TOTAL} unidades** desde los nodos origen (1, 2) hacia los nodos
destino (78, 79, 80), **minimizando el costo total** de transporte a traves de la red.

### Restriccion adicional
Al menos el **20% del flujo total** ({MIN_FLUJO_NODO_80} unidades) debe llegar al **nodo 80**.

## Parametros del Modelo

| Parametro | Valor |
|---|---|
| Flujo total requerido | {FLUJO_TOTAL} |
| Minimo al nodo 80 (20%) | {MIN_FLUJO_NODO_80} |
| Nodos origen | {NODOS_ORIGEN} |
| Nodos destino | {NODOS_DESTINO} |

## Algoritmo Utilizado

Se utiliza **`nx.min_cost_flow()`** de NetworkX, que implementa el algoritmo de
**caminos mas cortos sucesivos** (Successive Shortest Path Algorithm).

### Modelado de la restriccion del 20%:
1. Se crea un **super-origen** (nodo 0) conectado a los nodos 1 y 2 con costo 0.
2. Se crea un **super-destino** (nodo 81) que recibe flujo de 78, 79 y 80.
3. Para forzar que al menos {MIN_FLUJO_NODO_80} unidades lleguen al nodo 80, se crea un
   **nodo auxiliar** (nodo 82) con capacidad exacta de {MIN_FLUJO_NODO_80} entre el nodo 80
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
| **Costo total minimo** | **{costo}** |
| Restriccion nodo 80 (>= {MIN_FLUJO_NODO_80}) | **{cumple}** |
| Arcos activos | {len(resultados['arcos_activos'])} |
| **Tiempo de ejecucion** | **{resultados['tiempo_ejecucion']:.4f} segundos** |

### Flujo por Origen

| Nodo Origen | Flujo Enviado |
|---|---|
"""
    for origen, flujo in fo.items():
        contenido += f"| Nodo {origen} | {flujo} |\n"

    contenido += f"""
### Flujo por Destino

| Nodo Destino | Flujo Recibido | Porcentaje |
|---|---|---|
"""
    for destino, flujo in fd.items():
        pct = (flujo / FLUJO_TOTAL * 100) if FLUJO_TOTAL > 0 else 0
        contenido += f"| Nodo {destino} | {flujo} | {pct:.1f}% |\n"

    contenido += f"""
### Arcos Activos (flujo > 0)

| Origen | Destino | Flujo | Capacidad | Costo Unitario | Costo x Flujo |
|---|---|---|---|---|---|
"""
    for u, v, flujo, cap, costo_u in resultados['arcos_activos']:
        contenido += f"| {u} | {v} | {flujo} | {cap} | {costo_u} | {costo_u * flujo} |\n"

    contenido += f"""
## Grafica

La grafica muestra el grafo con:
- **Izquierda**: Nodos origen (entradas) en verde
- **Derecha**: Nodos destino (salidas) en rojo
- **Centro**: Nodos intermedios en azul claro
- **Naranja**: Arcos con flujo > 0 (con etiquetas de flujo)

![Flujo al Costo Minimo](flujo_costo_minimo.png)
"""

    readme_path = os.path.join(output_dir, 'README.md')
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(contenido)
    print(f"  README.md guardado en: {readme_path}")
    return readme_path


# ═══════════════════════════════════════════════════════════════════════════
#  EJECUCION PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    print("=" * 70)
    print("  MODELO 1: FLUJO AL COSTO MINIMO")
    print("=" * 70)

    # Paso 1: Cargar datos del CSV
    print("\n[1/7] Cargando datos...")
    df = cargar_datos(DATA_PATH)

    # Paso 2: Construir el grafo dirigido
    print("\n[2/7] Construyendo grafo dirigido...")
    G = construir_grafo(df)

    # Paso 3: Agregar super-nodos y restricciones
    print("\n[3/7] Agregando super-nodos y restricciones...")
    G = agregar_super_nodos(G)

    # Paso 4: Resolver el flujo al costo mínimo (con medición de tiempo)
    print("\n[4/7] Resolviendo flujo al costo minimo...")
    t_inicio = time.time()
    flow_dict, costo_total = resolver_flujo(G)
    t_fin = time.time()
    tiempo_ejecucion = t_fin - t_inicio
    print(f"  Tiempo de ejecucion del modelo: {tiempo_ejecucion:.4f} segundos")

    # Paso 5: Analizar los resultados
    print("\n[5/7] Analizando resultados...")
    resultados = analizar_resultados(G, flow_dict, costo_total)
    resultados['tiempo_ejecucion'] = tiempo_ejecucion

    # Imprimir resumen en consola
    print(f"\n  Costo total minimo: {costo_total}")
    for destino, flujo in resultados['flujo_destinos'].items():
        pct = flujo / FLUJO_TOTAL * 100
        print(f"  Nodo {destino}: {flujo} ({pct:.1f}%)")
    print(f"  Restriccion nodo 80 (>={MIN_FLUJO_NODO_80}): "
          f"{'CUMPLE' if resultados['restriccion_cumple'] else 'NO CUMPLE'}")

    # Paso 6: Generar gráfica del grafo
    print("\n[6/7] Generando grafica...")
    G_vis = nx.DiGraph()
    for _, row in df.iterrows():
        G_vis.add_edge(int(row['Origen']), int(row['Destino']))
    generar_grafica(G_vis, resultados, OUTPUT_DIR)

    # Paso 7: Generar README.md
    print("\n[7/7] Generando README.md...")
    generar_readme(resultados, OUTPUT_DIR)

    print("\n" + "=" * 70)
    print("  Modelo 1 completado exitosamente!")
    print("=" * 70)
