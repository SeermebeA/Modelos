"""
Modelo 2: Flujo Maximo
=======================
Problema: Determinar el flujo maximo que puede transportarse desde los
nodos origen (1, 2) hacia los nodos destino (78, 79, 80).

Algoritmo: maximum_flow() de NetworkX (implementacion del algoritmo
de Edmonds-Karp, basado en BFS para encontrar caminos aumentantes).

Estructura del script:
    1. cargar_datos()          - Lectura del CSV
    2. construir_grafo()       - Grafo dirigido con capacidades
    3. agregar_super_nodos()   - Super-origen y super-destino
    4. resolver_flujo_maximo() - Ejecucion del algoritmo
    5. analizar_resultados()   - Extraccion de metricas y cuellos de botella
    6. generar_grafica()       - Visualizacion con layout izq->der
    7. generar_readme()        - README.md con explicacion y resultados
"""

import os
import time
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# ─── Configuracion de rutas ────────────────────────────────────────────────
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATA_PATH = os.path.join(BASE_DIR, 'data', 'matriz_de_datos.csv')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output', 'modelo2')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ─── Parametros del modelo ─────────────────────────────────────────────────
NODOS_ORIGEN = [1, 2]
NODOS_DESTINO = [78, 79, 80]
SUPER_ORIGEN = 0
SUPER_DESTINO = 81
CAP_INF = 10_000  # Capacidad "infinita" para arcos de super-nodos


def cargar_datos(ruta_csv):
    """
    Lee el archivo CSV con la matriz de datos del grafo.

    Parametros:
        ruta_csv (str): Ruta absoluta al archivo CSV.

    Retorna:
        pd.DataFrame: DataFrame con columnas [Origen, Destino, Costo, Distancia, Capacidad].
    """
    df = pd.read_csv(ruta_csv)
    print(f"  Arcos leidos del CSV: {len(df)}")
    return df


def construir_grafo(df):
    """
    Construye un grafo dirigido (DiGraph) con atributo 'capacity'.

    Parametros:
        df (pd.DataFrame): DataFrame con las columnas del CSV.

    Retorna:
        nx.DiGraph: Grafo dirigido donde cada arco tiene:
            - capacity: capacidad maxima de flujo
            - cost: costo unitario de transporte
            - distance: distancia del arco

    Para flujo maximo, el atributo clave es 'capacity'. Los otros
    atributos se mantienen para referencia y analisis.
    """
    G = nx.DiGraph()
    for _, row in df.iterrows():
        G.add_edge(
            int(row['Origen']),
            int(row['Destino']),
            capacity=int(row['Capacidad']),
            cost=int(row['Costo']),
            distance=int(row['Distancia'])
        )
    print(f"  Nodos en el grafo: {G.number_of_nodes()}")
    print(f"  Arcos en el grafo: {G.number_of_edges()}")
    return G


def agregar_super_nodos(G):
    """
    Agrega un super-origen y un super-destino para unificar multiples
    fuentes y sumideros en un unico problema de flujo maximo.

    Parametros:
        G (nx.DiGraph): Grafo dirigido original.

    Retorna:
        nx.DiGraph: Grafo modificado con:
            - Nodo 0 (super-origen) -> nodos 1, 2 con capacidad infinita
            - Nodos 78, 79, 80 -> nodo 81 (super-destino) con capacidad infinita

    Razon de la capacidad infinita:
        Los arcos de super-nodos no deben ser cuellos de botella.
        El flujo maximo esta limitado solo por las capacidades de la red original.
    """
    for origen in NODOS_ORIGEN:
        G.add_edge(SUPER_ORIGEN, origen, capacity=CAP_INF)

    for destino in NODOS_DESTINO:
        G.add_edge(destino, SUPER_DESTINO, capacity=CAP_INF)

    print(f"  Super-nodos agregados (0=super-origen, 81=super-destino)")
    return G


def resolver_flujo_maximo(G):
    """
    Ejecuta el algoritmo de flujo maximo (Edmonds-Karp).

    Parametros:
        G (nx.DiGraph): Grafo con super-origen (0) y super-destino (81).

    Retorna:
        tuple: (flow_value, flow_dict)
            - flow_value (int): Valor del flujo maximo total.
            - flow_dict (dict): Diccionario {u: {v: flujo}} con el flujo
              en cada arco de la solucion.

    El algoritmo busca iterativamente caminos aumentantes (de super-origen
    a super-destino) usando BFS, y envia flujo por ellos hasta que no
    existan mas caminos con capacidad residual.
    """
    flow_value, flow_dict = nx.maximum_flow(G, SUPER_ORIGEN, SUPER_DESTINO)
    print(f"  Flujo maximo encontrado: {flow_value}")
    return flow_value, flow_dict


def analizar_resultados(G, flow_value, flow_dict):
    """
    Extrae metricas detalladas de la solucion de flujo maximo,
    incluyendo analisis de cuellos de botella.

    Parametros:
        G (nx.DiGraph): Grafo con atributos de arcos.
        flow_value (int): Valor del flujo maximo.
        flow_dict (dict): Solucion del flujo maximo.

    Retorna:
        dict: Diccionario con:
            - 'flujo_maximo': valor total del flujo maximo
            - 'flujo_origenes': {nodo: flujo} para cada origen
            - 'flujo_destinos': {nodo: flujo} para cada destino
            - 'arcos_activos': lista de (u, v, flujo, capacidad, pct_uso)
            - 'arcos_saturados': lista de arcos donde flujo == capacidad
            - 'total_saturados': conteo de arcos saturados
    """
    resultados = {
        'flujo_maximo': flow_value,
        'flujo_origenes': {},
        'flujo_destinos': {},
        'arcos_activos': [],
        'arcos_saturados': [],
        'total_saturados': 0
    }

    # Flujo por cada origen
    for origen in NODOS_ORIGEN:
        resultados['flujo_origenes'][origen] = flow_dict[SUPER_ORIGEN].get(origen, 0)

    # Flujo por cada destino
    for destino in NODOS_DESTINO:
        resultados['flujo_destinos'][destino] = flow_dict[destino].get(SUPER_DESTINO, 0)

    # Arcos activos y saturados (excluyendo super-nodos)
    for u in flow_dict:
        for v, flujo in flow_dict[u].items():
            if flujo > 0 and u != SUPER_ORIGEN and v != SUPER_DESTINO:
                cap = G[u][v].get('capacity', 0)
                pct_uso = (flujo / cap * 100) if cap > 0 else 0
                resultados['arcos_activos'].append((u, v, flujo, cap, pct_uso))
                if flujo == cap:
                    resultados['arcos_saturados'].append((u, v, flujo, cap))

    resultados['total_saturados'] = len(resultados['arcos_saturados'])
    return resultados


def calcular_layout(G_vis):
    """
    Calcula posiciones de nodos con layout jerarquico izquierda -> derecha:
    - IZQUIERDA: Nodos origen (entradas)
    - DERECHA: Nodos destino (salidas)
    - CENTRO: Nodos intermedios por capas (profundidad BFS)

    Parametros:
        G_vis (nx.DiGraph): Grafo de visualizacion.

    Retorna:
        dict: {nodo: (x, y)} posiciones para matplotlib.

    El algoritmo BFS agrupa nodos por distancia a los origenes
    y los distribuye en capas de izquierda (entradas) a derecha (salidas).
    """
    pos = {}

    # Calcular profundidad desde origenes usando BFS
    profundidad = {}
    for origen in NODOS_ORIGEN:
        if origen in G_vis:
            distancias = nx.single_source_shortest_path_length(G_vis, origen)
            for nodo, dist in distancias.items():
                if nodo not in profundidad or dist < profundidad[nodo]:
                    profundidad[nodo] = dist

    max_prof = max(profundidad.values()) if profundidad else 0
    for nodo in G_vis.nodes():
        if nodo not in profundidad:
            profundidad[nodo] = max_prof

    # Agrupar nodos por capa (excluyendo destinos)
    capas = {}
    for nodo, prof in profundidad.items():
        if nodo in NODOS_DESTINO:
            continue
        if prof not in capas:
            capas[prof] = []
        capas[prof].append(nodo)

    num_capas = max(capas.keys()) + 2 if capas else 2

    # Posiciones X: izquierda (origenes) -> derecha (destinos)
    for prof, nodos in capas.items():
        x = prof
        nodos_sorted = sorted(nodos)
        n = len(nodos_sorted)
        for i, nodo in enumerate(nodos_sorted):
            y = (i - (n - 1) / 2) * 1.2
            pos[nodo] = (x, y)

    # Destinos fijos en el extremo derecho
    destinos_en_grafo = [d for d in NODOS_DESTINO if d in G_vis]
    n_dest = len(destinos_en_grafo)
    for i, nodo in enumerate(sorted(destinos_en_grafo)):
        y = (i - (n_dest - 1) / 2) * 2.5
        pos[nodo] = (num_capas, y)

    return pos


def generar_grafica(G_vis, resultados, output_dir):
    """
    Genera la visualizacion del grafo con el flujo maximo.

    Parametros:
        G_vis (nx.DiGraph): Grafo original para visualizar.
        resultados (dict): Metricas del modelo.
        output_dir (str): Directorio donde guardar el PNG.

    Caracteristicas:
        - Layout jerarquico: origenes (IZQUIERDA) -> destinos (DERECHA)
        - Grosor de arcos proporcional al flujo transportado
        - Arcos saturados mas visibles (indican cuellos de botella)
        - Anotaciones de direccion del flujo
    """
    pos = calcular_layout(G_vis)

    # Colores de nodos
    node_colors = []
    for node in G_vis.nodes():
        if node in NODOS_ORIGEN:
            node_colors.append('#2ecc71')
        elif node in NODOS_DESTINO:
            node_colors.append('#e74c3c')
        else:
            node_colors.append('#85c1e9')

    fig, ax = plt.subplots(1, 1, figsize=(24, 16))
    fig.patch.set_facecolor('#1a1a2e')
    ax.set_facecolor('#1a1a2e')

    # 1. Arcos inactivos (fondo gris)
    nx.draw_networkx_edges(G_vis, pos, edge_color='#333333', alpha=0.3,
                           arrows=True, arrowsize=8, ax=ax, width=0.5,
                           connectionstyle='arc3,rad=0.05')

    # 2. Arcos activos con grosor proporcional al flujo
    if resultados['arcos_activos']:
        max_flujo = max(f for _, _, f, _, _ in resultados['arcos_activos'])
        for u, v, flujo, _, _ in resultados['arcos_activos']:
            if G_vis.has_edge(u, v):
                width = 1 + (flujo / max_flujo) * 4
                nx.draw_networkx_edges(G_vis, pos, edgelist=[(u, v)],
                                       edge_color='#e67e22', alpha=0.85,
                                       arrows=True, arrowsize=12, ax=ax,
                                       width=width,
                                       connectionstyle='arc3,rad=0.05')

    # 3. Nodos
    nx.draw_networkx_nodes(G_vis, pos, node_color=node_colors, node_size=400,
                           edgecolors='white', linewidths=1.0, ax=ax)
    nx.draw_networkx_labels(G_vis, pos, font_size=7, font_color='white',
                            font_weight='bold', ax=ax)

    # 4. Etiquetas de flujo
    edge_labels = {(u, v): f"{f}"
                   for u, v, f, _, _ in resultados['arcos_activos']
                   if G_vis.has_edge(u, v)}
    nx.draw_networkx_edge_labels(G_vis, pos, edge_labels=edge_labels,
                                 font_size=6, font_color='#f1c40f',
                                 bbox=dict(boxstyle='round,pad=0.15',
                                           facecolor='#2c3e50', alpha=0.8),
                                 ax=ax)

    # 5. Indicadores de direccion
    ax.annotate('ENTRADAS\n(Origenes)', xy=(0.05, 0.95), xycoords='axes fraction',
                fontsize=12, fontweight='bold', color='#2ecc71',
                ha='center', va='top',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='#2c3e50', alpha=0.9))
    ax.annotate('SALIDAS\n(Destinos)', xy=(0.95, 0.95), xycoords='axes fraction',
                fontsize=12, fontweight='bold', color='#e74c3c',
                ha='center', va='top',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='#2c3e50', alpha=0.9))
    ax.annotate('', xy=(0.85, 0.02), xytext=(0.15, 0.02),
                xycoords='axes fraction',
                arrowprops=dict(arrowstyle='->', color='white', lw=2))
    ax.text(0.5, 0.02, 'Direccion del flujo', transform=ax.transAxes,
            fontsize=10, color='white', ha='center', va='bottom')

    # 6. Leyenda
    flow_max = resultados['flujo_maximo']
    legend_patches = [
        mpatches.Patch(color='#2ecc71', label='Nodos Origen (1, 2)'),
        mpatches.Patch(color='#e74c3c', label='Nodos Destino (78, 79, 80)'),
        mpatches.Patch(color='#85c1e9', label='Nodos Intermedios'),
        mpatches.Patch(color='#e67e22', label=f'Arcos con flujo (maximo: {flow_max})'),
    ]
    ax.legend(handles=legend_patches, loc='lower left', fontsize=10,
              facecolor='#2c3e50', edgecolor='white', labelcolor='white')

    # 7. Titulo
    fd = resultados['flujo_destinos']
    ax.set_title(
        f'Modelo 2: Flujo Maximo\n'
        f'Flujo Maximo: {flow_max} | '
        f'Nodo 78: {fd.get(78, 0)} | '
        f'Nodo 79: {fd.get(79, 0)} | '
        f'Nodo 80: {fd.get(80, 0)}',
        fontsize=14, fontweight='bold', color='white', pad=20)

    plt.tight_layout()
    output_path = os.path.join(output_dir, 'flujo_maximo.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='#1a1a2e')
    plt.close()
    print(f"  Grafica guardada en: {output_path}")
    return output_path


def generar_readme(resultados, output_dir):
    """
    Genera un archivo README.md con la explicacion completa del modelo
    de flujo maximo, incluyendo analisis de cuellos de botella.

    Parametros:
        resultados (dict): Metricas del modelo.
        output_dir (str): Directorio donde guardar el README.

    El README incluye:
        - Descripcion del problema
        - Explicacion del algoritmo
        - Resultados generales y por nodo
        - Analisis de arcos saturados (cuellos de botella)
        - Tabla completa de arcos activos
    """
    fd = resultados['flujo_destinos']
    fo = resultados['flujo_origenes']
    flow_max = resultados['flujo_maximo']

    contenido = f"""# Modelo 2: Flujo Maximo

## Descripcion del Problema

Se busca determinar el **flujo maximo** que puede transportarse desde los nodos
origen (1, 2) hacia los nodos destino (78, 79, 80) a traves de la red, respetando
las **capacidades** de cada arco.

## Parametros del Modelo

| Parametro | Valor |
|---|---|
| Nodos origen | {NODOS_ORIGEN} |
| Nodos destino | {NODOS_DESTINO} |
| Capacidad "infinita" (super-arcos) | {CAP_INF} |

## Algoritmo Utilizado

Se utiliza **`nx.maximum_flow()`** de NetworkX, que implementa el algoritmo de
**Edmonds-Karp** (variante de Ford-Fulkerson con BFS).

### Modelado con super-nodos:
1. Se crea un **super-origen** (nodo 0) conectado a los nodos 1 y 2 con capacidad
   infinita ({CAP_INF}).
2. Se crea un **super-destino** (nodo 81) al que se conectan los nodos 78, 79 y 80
   con capacidad infinita.
3. El flujo maximo se calcula entre el super-origen y el super-destino.
4. Las capacidades infinitas aseguran que los super-arcos no limiten el flujo;
   los cuellos de botella reales estan en la red original.

## Funcionamiento del Codigo

```
cargar_datos()           -> Lee CSV con 391 arcos
construir_grafo()        -> Crea DiGraph con capacity, cost, distance
agregar_super_nodos()    -> Agrega nodos 0 y 81 con capacidad infinita
resolver_flujo_maximo()  -> Ejecuta maximum_flow() (Edmonds-Karp)
analizar_resultados()    -> Extrae metricas y cuellos de botella
generar_grafica()        -> PNG con layout izquierda(entrada) -> derecha(salida)
generar_readme()         -> Este archivo
```

## Resultados

### Resumen General

| Metrica | Valor |
|---|---|
| **Flujo maximo total** | **{flow_max}** |
| Arcos activos | {len(resultados['arcos_activos'])} |
| Arcos saturados (cuello de botella) | {resultados['total_saturados']} |
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
        pct = (flujo / flow_max * 100) if flow_max > 0 else 0
        contenido += f"| Nodo {destino} | {flujo} | {pct:.1f}% |\n"

    contenido += f"""
### Arcos Saturados (Cuellos de Botella)

Estos arcos operan al 100% de su capacidad y limitan el flujo total de la red:

| Origen | Destino | Flujo | Capacidad |
|---|---|---|---|
"""
    for u, v, flujo, cap in resultados['arcos_saturados']:
        contenido += f"| {u} | {v} | {flujo} | {cap} |\n"

    contenido += f"""
### Todos los Arcos Activos

| Origen | Destino | Flujo | Capacidad | % Uso |
|---|---|---|---|---|
"""
    for u, v, flujo, cap, pct in resultados['arcos_activos']:
        contenido += f"| {u} | {v} | {flujo} | {cap} | {pct:.1f}% |\n"

    contenido += f"""
## Grafica

La grafica muestra el grafo con:
- **Izquierda**: Nodos origen (entradas) en verde
- **Derecha**: Nodos destino (salidas) en rojo
- **Centro**: Nodos intermedios en azul claro
- **Naranja**: Arcos con flujo > 0 (grosor proporcional al flujo)

![Flujo Maximo](flujo_maximo.png)
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
    print("  MODELO 2: FLUJO MAXIMO")
    print("=" * 70)

    # Paso 1: Cargar datos del CSV
    print("\n[1/7] Cargando datos...")
    df = cargar_datos(DATA_PATH)

    # Paso 2: Construir el grafo dirigido
    print("\n[2/7] Construyendo grafo dirigido...")
    G = construir_grafo(df)

    # Paso 3: Agregar super-nodos
    print("\n[3/7] Agregando super-nodos...")
    G = agregar_super_nodos(G)

    # Paso 4: Resolver flujo maximo (con medicion de tiempo)
    print("\n[4/7] Resolviendo flujo maximo...")
    t_inicio = time.time()
    flow_value, flow_dict = resolver_flujo_maximo(G)
    t_fin = time.time()
    tiempo_ejecucion = t_fin - t_inicio
    print(f"  Tiempo de ejecucion del modelo: {tiempo_ejecucion:.4f} segundos")

    # Paso 5: Analizar resultados
    print("\n[5/7] Analizando resultados...")
    resultados = analizar_resultados(G, flow_value, flow_dict)
    resultados['tiempo_ejecucion'] = tiempo_ejecucion

    # Imprimir resumen en consola
    print(f"\n  Flujo maximo total: {flow_value}")
    for destino, flujo in resultados['flujo_destinos'].items():
        pct = flujo / flow_value * 100 if flow_value > 0 else 0
        print(f"  Nodo {destino}: {flujo} ({pct:.1f}%)")
    print(f"  Arcos saturados: {resultados['total_saturados']} / {len(resultados['arcos_activos'])}")

    # Paso 6: Generar grafica
    print("\n[6/7] Generando grafica...")
    G_vis = nx.DiGraph()
    for _, row in df.iterrows():
        G_vis.add_edge(int(row['Origen']), int(row['Destino']))
    generar_grafica(G_vis, resultados, OUTPUT_DIR)

    # Paso 7: Generar README.md
    print("\n[7/7] Generando README.md...")
    generar_readme(resultados, OUTPUT_DIR)

    print("\n" + "=" * 70)
    print("  Modelo 2 completado exitosamente!")
    print("=" * 70)
