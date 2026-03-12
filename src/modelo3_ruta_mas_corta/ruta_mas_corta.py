"""
Modelo 3: Ruta Mas Corta
=========================
Problema: Encontrar la ruta mas corta entre los nodos origen (1, 2)
y los nodos destino (78, 79, 80), usando la distancia como peso.

Se evaluan las 6 combinaciones posibles y se identifica la ruta global
mas corta. Se utiliza el algoritmo de Dijkstra de NetworkX.

Estructura del script:
    1. cargar_datos()            - Lectura del CSV
    2. construir_grafo()         - Grafo dirigido con pesos = distancia
    3. calcular_todas_rutas()    - Dijkstra para cada par (origen, destino)
    4. identificar_mejor_ruta()  - Seleccion de la ruta global mas corta
    5. generar_grafica_todas()   - Visualizacion de todas las rutas
    6. generar_grafica_mejor()   - Visualizacion de la mejor ruta
    7. generar_readme()          - README.md con explicacion y resultados
"""

import os
import time
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D

# ─── Configuracion de rutas ────────────────────────────────────────────────
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATA_PATH = os.path.join(BASE_DIR, 'data', 'matriz_de_datos.csv')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output', 'modelo3')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ─── Parametros del modelo ─────────────────────────────────────────────────
NODOS_ORIGEN = [1, 2]
NODOS_DESTINO = [78, 79, 80]


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
    Construye un grafo dirigido (DiGraph) con peso = Distancia.

    Parametros:
        df (pd.DataFrame): DataFrame con las columnas del CSV.

    Retorna:
        nx.DiGraph: Grafo dirigido donde cada arco tiene:
            - weight: distancia del arco (usado por Dijkstra)
            - cost: costo unitario de transporte
            - capacity: capacidad maxima de flujo

    Nota: Para el algoritmo de ruta mas corta, el atributo 'weight'
    se asigna a la Distancia (no al Costo). Dijkstra minimiza la suma
    de pesos en el camino.
    """
    G = nx.DiGraph()
    for _, row in df.iterrows():
        G.add_edge(
            int(row['Origen']),
            int(row['Destino']),
            weight=int(row['Distancia']),
            cost=int(row['Costo']),
            capacity=int(row['Capacidad'])
        )
    print(f"  Nodos en el grafo: {G.number_of_nodes()}")
    print(f"  Arcos en el grafo: {G.number_of_edges()}")
    return G


def calcular_todas_rutas(G):
    """
    Calcula la ruta mas corta para cada combinacion (origen, destino)
    usando el algoritmo de Dijkstra.

    Parametros:
        G (nx.DiGraph): Grafo dirigido con atributo 'weight' = distancia.

    Retorna:
        list[dict]: Lista de resultados, donde cada elemento es:
            {
                'origen': int,        # nodo de inicio
                'destino': int,       # nodo de fin
                'distancia': int,     # distancia total de la ruta
                'ruta': list[int],    # secuencia de nodos
                'num_arcos': int,     # numero de arcos en la ruta
                'encontrada': bool    # True si existe camino
            }

    Se evaluan 6 combinaciones: {1,2} x {78,79,80}.
    Si no existe un camino entre un par, se marca como no encontrada.
    """
    resultados = []

    for origen in NODOS_ORIGEN:
        for destino in NODOS_DESTINO:
            try:
                # Dijkstra: minimiza la suma de 'weight' en el camino
                distancia = nx.shortest_path_length(
                    G, source=origen, target=destino, weight='weight'
                )
                ruta = nx.shortest_path(
                    G, source=origen, target=destino, weight='weight'
                )
                resultados.append({
                    'origen': origen,
                    'destino': destino,
                    'distancia': distancia,
                    'ruta': ruta,
                    'num_arcos': len(ruta) - 1,
                    'encontrada': True
                })
                print(f"  {origen} -> {destino}: distancia={distancia}, arcos={len(ruta)-1}")

            except nx.NetworkXNoPath:
                # No existe camino dirigido entre este par
                resultados.append({
                    'origen': origen,
                    'destino': destino,
                    'distancia': None,
                    'ruta': None,
                    'num_arcos': 0,
                    'encontrada': False
                })
                print(f"  {origen} -> {destino}: NO EXISTE RUTA")

    return resultados


def identificar_mejor_ruta(resultados):
    """
    Identifica la ruta con la menor distancia total entre todas
    las combinaciones evaluadas.

    Parametros:
        resultados (list[dict]): Lista de resultados de calcular_todas_rutas().

    Retorna:
        dict o None: Diccionario con la mejor ruta (misma estructura que
        los elementos de resultados), o None si no se encontro ninguna ruta.
    """
    rutas_validas = [r for r in resultados if r['encontrada']]

    if not rutas_validas:
        print("  No se encontraron rutas validas.")
        return None

    mejor = min(rutas_validas, key=lambda r: r['distancia'])
    print(f"  Mejor ruta: {mejor['origen']} -> {mejor['destino']}, "
          f"distancia={mejor['distancia']}")
    return mejor


def obtener_detalle_arcos(G, ruta):
    """
    Obtiene los atributos de cada arco en una ruta dada.

    Parametros:
        G (nx.DiGraph): Grafo con atributos de arcos.
        ruta (list[int]): Secuencia de nodos de la ruta.

    Retorna:
        list[dict]: Lista con un diccionario por arco:
            {
                'origen': int,
                'destino': int,
                'distancia': int,
                'costo': int,
                'capacidad': int
            }
    """
    detalle = []
    for i in range(len(ruta) - 1):
        u, v = ruta[i], ruta[i + 1]
        detalle.append({
            'origen': u,
            'destino': v,
            'distancia': G[u][v]['weight'],
            'costo': G[u][v].get('cost', 0),
            'capacidad': G[u][v].get('capacity', 0)
        })
    return detalle


def calcular_layout(G):
    """
    Calcula posiciones de nodos con layout jerarquico izquierda -> derecha:
    - IZQUIERDA: Nodos origen (entradas)
    - DERECHA: Nodos destino (salidas)
    - CENTRO: Nodos intermedios distribuidos por profundidad BFS

    Parametros:
        G (nx.DiGraph): Grafo de visualizacion.

    Retorna:
        dict: {nodo: (x, y)} posiciones para matplotlib.
    """
    pos = {}

    # Calcular profundidad BFS desde origenes
    profundidad = {}
    for origen in NODOS_ORIGEN:
        if origen in G:
            distancias = nx.single_source_shortest_path_length(G, origen)
            for nodo, dist in distancias.items():
                if nodo not in profundidad or dist < profundidad[nodo]:
                    profundidad[nodo] = dist

    max_prof = max(profundidad.values()) if profundidad else 0
    for nodo in G.nodes():
        if nodo not in profundidad:
            profundidad[nodo] = max_prof

    # Agrupar por capa (sin destinos)
    capas = {}
    for nodo, prof in profundidad.items():
        if nodo in NODOS_DESTINO:
            continue
        if prof not in capas:
            capas[prof] = []
        capas[prof].append(nodo)

    num_capas = max(capas.keys()) + 2 if capas else 2

    # X de izquierda a derecha
    for prof, nodos in capas.items():
        x = prof
        nodos_sorted = sorted(nodos)
        n = len(nodos_sorted)
        for i, nodo in enumerate(nodos_sorted):
            y = (i - (n - 1) / 2) * 1.2
            pos[nodo] = (x, y)

    # Destinos en extremo derecho
    destinos_en_grafo = [d for d in NODOS_DESTINO if d in G]
    n_dest = len(destinos_en_grafo)
    for i, nodo in enumerate(sorted(destinos_en_grafo)):
        y = (i - (n_dest - 1) / 2) * 2.5
        pos[nodo] = (num_capas, y)

    return pos


def generar_grafica_todas(G, resultados, mejor_ruta, output_dir):
    """
    Genera una grafica que muestra TODAS las rutas mas cortas encontradas,
    cada una en un color diferente. La mejor ruta aparece con trazo continuo
    y mas grueso, las demas con trazo discontinuo.

    Parametros:
        G (nx.DiGraph): Grafo para visualizar.
        resultados (list[dict]): Todas las rutas calculadas.
        mejor_ruta (dict): La ruta con menor distancia.
        output_dir (str): Directorio donde guardar el PNG.

    Retorna:
        str: Ruta al archivo PNG generado.
    """
    pos = calcular_layout(G)

    # Colores de nodos
    node_colors = []
    for node in G.nodes():
        if node in NODOS_ORIGEN:
            node_colors.append('#2ecc71')
        elif node in NODOS_DESTINO:
            node_colors.append('#e74c3c')
        else:
            node_colors.append('#85c1e9')

    fig, ax = plt.subplots(1, 1, figsize=(24, 16))
    fig.patch.set_facecolor('#1a1a2e')
    ax.set_facecolor('#1a1a2e')

    # 1. Arcos base (gris tenue)
    nx.draw_networkx_edges(G, pos, edge_color='#333333', alpha=0.3,
                           arrows=True, arrowsize=8, ax=ax, width=0.5,
                           connectionstyle='arc3,rad=0.05')

    # 2. Dibujar cada ruta con un color diferente
    colores_rutas = ['#e74c3c', '#f39c12', '#2ecc71', '#3498db', '#9b59b6', '#1abc9c']
    rutas_encontradas = [r for r in resultados if r['encontrada']]
    # Ordenar: mejor ruta al final para que se dibuje encima
    rutas_encontradas.sort(key=lambda r: r['distancia'], reverse=True)

    legend_items = []
    for idx, r in enumerate(rutas_encontradas):
        edges = list(zip(r['ruta'][:-1], r['ruta'][1:]))
        color = colores_rutas[idx % len(colores_rutas)]

        # La mejor ruta: trazo grueso y continuo
        es_mejor = (mejor_ruta and r['origen'] == mejor_ruta['origen']
                    and r['destino'] == mejor_ruta['destino'])
        width = 4 if es_mejor else 2
        alpha = 1.0 if es_mejor else 0.7
        style = 'solid' if es_mejor else 'dashed'

        nx.draw_networkx_edges(G, pos, edgelist=edges, edge_color=color,
                               alpha=alpha, arrows=True, arrowsize=14, ax=ax,
                               width=width, style=style,
                               connectionstyle='arc3,rad=0.05')

        label = f"{r['origen']}->{r['destino']} (dist={r['distancia']})"
        if es_mejor:
            label += " << MEJOR"
        legend_items.append(Line2D([0], [0], color=color, linewidth=width,
                                   linestyle='-' if es_mejor else '--', label=label))

    # 3. Nodos
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=400,
                           edgecolors='white', linewidths=1.0, ax=ax)
    nx.draw_networkx_labels(G, pos, font_size=7, font_color='white',
                            font_weight='bold', ax=ax)

    # 4. Indicadores de direccion
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

    # 5. Leyenda
    base_legend = [
        mpatches.Patch(color='#2ecc71', label='Nodos Origen (1, 2)'),
        mpatches.Patch(color='#e74c3c', label='Nodos Destino (78, 79, 80)'),
        mpatches.Patch(color='#85c1e9', label='Nodos Intermedios'),
    ]
    all_legend = base_legend + legend_items
    ax.legend(handles=all_legend, loc='lower left', fontsize=9,
              facecolor='#2c3e50', edgecolor='white', labelcolor='white')

    # 6. Titulo
    ax.set_title(
        f'Modelo 3: Rutas Mas Cortas (Todas las Combinaciones)\n'
        f'Mejor: Nodo {mejor_ruta["origen"]} -> Nodo {mejor_ruta["destino"]} '
        f'(Distancia: {mejor_ruta["distancia"]})',
        fontsize=14, fontweight='bold', color='white', pad=20)

    plt.tight_layout()
    output_path = os.path.join(output_dir, 'todas_las_rutas.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='#1a1a2e')
    plt.close()
    print(f"  Grafica (todas las rutas) guardada en: {output_path}")
    return output_path


def generar_grafica_mejor(G, mejor_ruta, output_dir):
    """
    Genera una grafica enfocada en la mejor ruta, resaltando
    los nodos que la componen y mostrando etiquetas de distancia.

    Parametros:
        G (nx.DiGraph): Grafo para visualizar.
        mejor_ruta (dict): La ruta con menor distancia.
        output_dir (str): Directorio donde guardar el PNG.

    Caracteristicas:
        - Nodos de la ruta resaltados (tamano mayor, color amarillo)
        - Nodos fuera de la ruta en gris oscuro
        - Etiquetas de distancia en cada arco de la ruta
        - Layout jerarquico: origenes IZQUIERDA, destinos DERECHA
    """
    pos = calcular_layout(G)

    fig, ax = plt.subplots(1, 1, figsize=(24, 16))
    fig.patch.set_facecolor('#1a1a2e')
    ax.set_facecolor('#1a1a2e')

    # 1. Arcos base
    nx.draw_networkx_edges(G, pos, edge_color='#333333', alpha=0.3,
                           arrows=True, arrowsize=8, ax=ax, width=0.5,
                           connectionstyle='arc3,rad=0.05')

    # 2. Mejor ruta resaltada
    if mejor_ruta:
        best_edges = list(zip(mejor_ruta['ruta'][:-1], mejor_ruta['ruta'][1:]))
        nx.draw_networkx_edges(G, pos, edgelist=best_edges, edge_color='#f1c40f',
                               alpha=1.0, arrows=True, arrowsize=16, ax=ax, width=4,
                               connectionstyle='arc3,rad=0.05')

        # Etiquetas de distancia en cada arco
        edge_labels_best = {}
        for i in range(len(mejor_ruta['ruta']) - 1):
            u = mejor_ruta['ruta'][i]
            v = mejor_ruta['ruta'][i + 1]
            edge_labels_best[(u, v)] = f"d={G[u][v]['weight']}"

        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels_best,
                                     font_size=7, font_color='#f1c40f',
                                     bbox=dict(boxstyle='round,pad=0.2',
                                               facecolor='#2c3e50', alpha=0.9),
                                     ax=ax)

    # 3. Nodos con colores diferenciados
    node_colors = []
    node_sizes = []
    for node in G.nodes():
        if mejor_ruta and node in mejor_ruta['ruta']:
            if node in NODOS_ORIGEN:
                node_colors.append('#2ecc71')   # verde - origen en ruta
            elif node in NODOS_DESTINO:
                node_colors.append('#e74c3c')   # rojo - destino en ruta
            else:
                node_colors.append('#f1c40f')   # amarillo - intermedio en ruta
            node_sizes.append(550)
        else:
            node_colors.append('#555555')       # gris - no en ruta
            node_sizes.append(200)

    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes,
                           edgecolors='white', linewidths=1.0, ax=ax)
    nx.draw_networkx_labels(G, pos, font_size=7, font_color='white',
                            font_weight='bold', ax=ax)

    # 4. Indicadores de direccion
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

    # 5. Leyenda
    legend_best = [
        mpatches.Patch(color='#2ecc71', label=f'Origen (Nodo {mejor_ruta["origen"]})'),
        mpatches.Patch(color='#e74c3c', label=f'Destino (Nodo {mejor_ruta["destino"]})'),
        mpatches.Patch(color='#f1c40f', label='Nodos en la ruta mas corta'),
        mpatches.Patch(color='#555555', label='Nodos no utilizados'),
    ]
    ax.legend(handles=legend_best, loc='lower left', fontsize=10,
              facecolor='#2c3e50', edgecolor='white', labelcolor='white')

    # 6. Titulo
    ax.set_title(
        f'Modelo 3: Ruta Mas Corta Global\n'
        f'Nodo {mejor_ruta["origen"]} -> Nodo {mejor_ruta["destino"]} | '
        f'Distancia Total: {mejor_ruta["distancia"]} | '
        f'Arcos: {mejor_ruta["num_arcos"]}',
        fontsize=14, fontweight='bold', color='white', pad=20)

    plt.tight_layout()
    output_path = os.path.join(output_dir, 'ruta_mas_corta.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='#1a1a2e')
    plt.close()
    print(f"  Grafica (mejor ruta) guardada en: {output_path}")
    return output_path


def generar_readme(G, resultados, mejor_ruta, output_dir, tiempo_ejecucion):
    """
    Genera un archivo README.md con la explicacion completa del modelo
    de ruta mas corta, incluyendo todas las combinaciones y el detalle
    arco por arco de la mejor ruta.

    Parametros:
        G (nx.DiGraph): Grafo con atributos de arcos.
        resultados (list[dict]): Todas las rutas calculadas.
        mejor_ruta (dict): La ruta con menor distancia.
        output_dir (str): Directorio donde guardar el README.

    El README incluye:
        - Descripcion del problema
        - Explicacion del algoritmo de Dijkstra
        - Tabla con todas las combinaciones
        - Detalle arco por arco de la mejor ruta
        - Referencias a las graficas
    """
    contenido = f"""# Modelo 3: Ruta Mas Corta

## Descripcion del Problema

Se busca encontrar la **ruta mas corta** (en terminos de distancia) entre los
nodos origen (1, 2) y los nodos destino (78, 79, 80).

Se evaluan las **6 combinaciones** posibles: {{1,2}} x {{78,79,80}}.

## Parametros del Modelo

| Parametro | Valor |
|---|---|
| Nodos origen | {NODOS_ORIGEN} |
| Nodos destino | {NODOS_DESTINO} |
| Peso de arcos | Distancia |
| Algoritmo | Dijkstra |

## Algoritmo Utilizado

Se utiliza **`nx.shortest_path()`** y **`nx.shortest_path_length()`** de NetworkX,
que implementan el **algoritmo de Dijkstra** para grafos con pesos no negativos.

### Funcionamiento de Dijkstra:
1. Comienza en el nodo origen con distancia = 0.
2. Explora los vecinos actualizando la distancia minima conocida.
3. Siempre expande el nodo no visitado con menor distancia acumulada.
4. Termina cuando llega al nodo destino o explora todos los nodos alcanzables.
5. Complejidad: O((V + E) log V) con cola de prioridad.

## Funcionamiento del Codigo

```
cargar_datos()            -> Lee CSV con 391 arcos
construir_grafo()         -> Crea DiGraph con weight=Distancia
calcular_todas_rutas()    -> Dijkstra para cada par (origen, destino)
identificar_mejor_ruta()  -> Selecciona la ruta con menor distancia
generar_grafica_todas()   -> PNG con las 6 rutas en colores diferentes
generar_grafica_mejor()   -> PNG enfocado en la mejor ruta
generar_readme()          -> Este archivo
```

## Resultados

### Todas las Combinaciones (ordenadas por distancia)

| # | Origen | Destino | Distancia | N Arcos | Ruta |
|---|---|---|---|---|---|
"""
    rutas_ordenadas = sorted(
        [r for r in resultados if r['encontrada']],
        key=lambda r: r['distancia']
    )
    for idx, r in enumerate(rutas_ordenadas, 1):
        ruta_str = ' -> '.join(map(str, r['ruta']))
        marca = " **<< MEJOR**" if (mejor_ruta and r['origen'] == mejor_ruta['origen']
                                     and r['destino'] == mejor_ruta['destino']) else ""
        contenido += f"| {idx} | {r['origen']} | {r['destino']} | {r['distancia']} | {r['num_arcos']} | {ruta_str}{marca} |\n"

    # Detalle de la mejor ruta
    if mejor_ruta:
        detalle = obtener_detalle_arcos(G, mejor_ruta['ruta'])
        contenido += f"""
### Mejor Ruta Global

| Metrica | Valor |
|---|---|
| **Origen** | **Nodo {mejor_ruta['origen']}** |
| **Destino** | **Nodo {mejor_ruta['destino']}** |
| **Distancia total** | **{mejor_ruta['distancia']}** |
| **Numero de arcos** | **{mejor_ruta['num_arcos']}** |
| **Ruta** | **{' -> '.join(map(str, mejor_ruta['ruta']))}** |
| **Tiempo de ejecucion** | **{tiempo_ejecucion:.4f} segundos** |

### Detalle Arco por Arco de la Mejor Ruta

| Arco | Distancia | Costo | Capacidad | Dist. Acumulada |
|---|---|---|---|---|
"""
        dist_acum = 0
        for arco in detalle:
            dist_acum += arco['distancia']
            contenido += (f"| {arco['origen']} -> {arco['destino']} | "
                          f"{arco['distancia']} | {arco['costo']} | "
                          f"{arco['capacidad']} | {dist_acum} |\n")

    contenido += f"""
## Graficas

### Todas las Rutas
Muestra las 6 rutas en colores diferentes. La mejor ruta aparece con
trazo continuo y grueso. Las demas con trazo discontinuo y fino.

![Todas las Rutas](todas_las_rutas.png)

### Mejor Ruta
Enfoca la mejor ruta con etiquetas de distancia en cada arco.
Los nodos de la ruta aparecen resaltados en amarillo.

![Ruta Mas Corta](ruta_mas_corta.png)

---

**Disposicion del grafo:**
- **Izquierda**: Nodos origen (entradas) en verde
- **Derecha**: Nodos destino (salidas) en rojo
- **Centro**: Nodos intermedios en azul claro (o amarillo si estan en la ruta)
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
    print("  MODELO 3: RUTA MAS CORTA")
    print("=" * 70)

    # Paso 1: Cargar datos del CSV
    print("\n[1/7] Cargando datos...")
    df = cargar_datos(DATA_PATH)

    # Paso 2: Construir el grafo dirigido
    print("\n[2/7] Construyendo grafo dirigido...")
    G = construir_grafo(df)

    # Paso 3: Calcular todas las rutas mas cortas (con medicion de tiempo)
    print("\n[3/7] Calculando rutas mas cortas (Dijkstra)...")
    t_inicio = time.time()
    resultados = calcular_todas_rutas(G)
    t_fin = time.time()
    tiempo_ejecucion = t_fin - t_inicio
    print(f"  Tiempo de ejecucion del modelo: {tiempo_ejecucion:.4f} segundos")

    # Paso 4: Identificar la mejor ruta
    print("\n[4/7] Identificando mejor ruta global...")
    mejor_ruta = identificar_mejor_ruta(resultados)

    # Imprimir resumen en consola
    if mejor_ruta:
        print(f"\n  MEJOR RUTA: {mejor_ruta['origen']} -> {mejor_ruta['destino']}")
        print(f"  Distancia: {mejor_ruta['distancia']}")
        print(f"  Ruta: {' -> '.join(map(str, mejor_ruta['ruta']))}")

    # Paso 5: Generar grafica con todas las rutas
    print("\n[5/7] Generando grafica (todas las rutas)...")
    generar_grafica_todas(G, resultados, mejor_ruta, OUTPUT_DIR)

    # Paso 6: Generar grafica de la mejor ruta
    print("\n[6/7] Generando grafica (mejor ruta)...")
    generar_grafica_mejor(G, mejor_ruta, OUTPUT_DIR)

    # Paso 7: Generar README.md
    print("\n[7/7] Generando README.md...")
    generar_readme(G, resultados, mejor_ruta, OUTPUT_DIR, tiempo_ejecucion)

    print("\n" + "=" * 70)
    print("  Modelo 3 completado exitosamente!")
    print("=" * 70)
