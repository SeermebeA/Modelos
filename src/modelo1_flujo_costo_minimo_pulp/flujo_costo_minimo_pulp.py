"""
Modelo 1 (PuLP): Flujo al Costo Minimo
========================================
Variante del Modelo 1 usando PuLP (programacion lineal) en lugar de
NetworkX para resolver el problema de flujo al costo minimo.

Formulacion LP:
    Minimizar: SUM(costo_ij * x_ij) para todo arco (i,j)
    Sujeto a:
        - 0 <= x_ij <= capacidad_ij  (limites de flujo)
        - Conservacion de flujo en nodos intermedios
        - Oferta total = 500 en origenes
        - Demanda total = 500 en destinos
        - Al menos 100 unidades llegan al nodo 80

Estructura del script:
    1. cargar_datos()          - Lectura del CSV
    2. construir_modelo()      - Formulacion del problema LP con PuLP
    3. resolver_modelo()       - Ejecucion del solver
    4. analizar_resultados()   - Extraccion de metricas
    5. calcular_layout()       - Layout jerarquico para graficacion
    6. generar_grafica()       - Visualizacion con NetworkX/Matplotlib
    7. generar_readme()        - README.md con resultados
"""

import os
import sys
import time
import pandas as pd
import pulp
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# ─── Configuracion de rutas ────────────────────────────────────────────────
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATA_PATH = os.path.join(BASE_DIR, 'data', 'matriz_de_datos.csv')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output', 'modelo1_pulp')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ─── Parametros del modelo ─────────────────────────────────────────────────
FLUJO_TOTAL = 500
MIN_FLUJO_NODO_80 = int(FLUJO_TOTAL * 0.20)  # 100 unidades
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


def construir_modelo(df):
    """
    Formula el problema de flujo al costo minimo como un programa lineal (LP)
    usando la libreria PuLP.

    Parametros:
        df (pd.DataFrame): DataFrame con los arcos del grafo.

    Retorna:
        tuple: (prob, variables, arcos_data, nodos)
            - prob: objeto LpProblem de PuLP
            - variables: dict {(i,j): LpVariable} para cada arco
            - arcos_data: dict {(i,j): {costo, capacidad, distancia}}
            - nodos: set de todos los nodos del grafo

    Formulacion:
        MIN SUM(costo_ij * x_ij)
        s.a.
            x_ij >= 0, x_ij <= cap_ij   (para todo arco)
            SUM(x_ij out) - SUM(x_ji in) = oferta_i  (nodos origen)
            SUM(x_ji in) - SUM(x_ij out) = demanda_j  (nodos destino)
            SUM(x_ji in) - SUM(x_ij out) = 0  (nodos intermedios)
            flujo al nodo 80 >= 100
    """
    # Crear el problema de minimizacion
    prob = pulp.LpProblem("Flujo_Costo_Minimo", pulp.LpMinimize)

    # Recopilar datos de arcos y nodos
    arcos_data = {}
    nodos = set()
    for _, row in df.iterrows():
        i, j = int(row['Origen']), int(row['Destino'])
        arcos_data[(i, j)] = {
            'costo': int(row['Costo']),
            'capacidad': int(row['Capacidad']),
            'distancia': int(row['Distancia'])
        }
        nodos.add(i)
        nodos.add(j)

    # Variables de decision: flujo en cada arco
    variables = {}
    for (i, j), data in arcos_data.items():
        variables[(i, j)] = pulp.LpVariable(
            f"x_{i}_{j}",
            lowBound=0,
            upBound=data['capacidad'],
            cat='Continuous'
        )

    # Funcion objetivo: minimizar costo total
    prob += pulp.lpSum(
        arcos_data[(i, j)]['costo'] * variables[(i, j)]
        for (i, j) in arcos_data
    ), "Costo_Total"

    # Restricciones de conservacion de flujo
    # Para cada nodo: flujo_entrante - flujo_saliente = demanda
    for nodo in nodos:
        flujo_entrante = pulp.lpSum(
            variables[(i, j)] for (i, j) in arcos_data if j == nodo
        )
        flujo_saliente = pulp.lpSum(
            variables[(i, j)] for (i, j) in arcos_data if i == nodo
        )

        if nodo in NODOS_ORIGEN:
            # Nodos origen: flujo_saliente - flujo_entrante = oferta
            # Repartir 500 equitativamente (o dejar libre para optimizar)
            pass  # Se maneja con la restriccion global
        elif nodo in NODOS_DESTINO:
            # Nodos destino: flujo_entrante - flujo_saliente = demanda
            pass  # Se maneja con la restriccion global
        else:
            # Nodos intermedios: conservacion de flujo
            prob += (flujo_entrante == flujo_saliente,
                     f"Conservacion_nodo_{nodo}")

    # Restriccion: flujo total saliente desde origenes = 500
    flujo_total_origenes = pulp.lpSum(
        variables[(i, j)] for (i, j) in arcos_data if i in NODOS_ORIGEN
    )
    flujo_total_entrante_origenes = pulp.lpSum(
        variables[(i, j)] for (i, j) in arcos_data if j in NODOS_ORIGEN
    )
    prob += (flujo_total_origenes - flujo_total_entrante_origenes == FLUJO_TOTAL,
             "Flujo_total_500")

    # Restriccion: al menos 100 unidades llegan al nodo 80
    flujo_nodo_80 = pulp.lpSum(
        variables[(i, j)] for (i, j) in arcos_data if j == 80
    )
    flujo_saliente_80 = pulp.lpSum(
        variables[(i, j)] for (i, j) in arcos_data if i == 80
    )
    prob += (flujo_nodo_80 - flujo_saliente_80 >= MIN_FLUJO_NODO_80,
             "Minimo_nodo_80")

    # Restriccion: flujo total entrante a destinos = 500
    flujo_total_destinos = pulp.lpSum(
        variables[(i, j)] for (i, j) in arcos_data if j in NODOS_DESTINO
    )
    flujo_total_saliente_destinos = pulp.lpSum(
        variables[(i, j)] for (i, j) in arcos_data if i in NODOS_DESTINO
    )
    prob += (flujo_total_destinos - flujo_total_saliente_destinos == FLUJO_TOTAL,
             "Flujo_total_destinos_500")

    print(f"  Variables de decision: {len(variables)}")
    print(f"  Nodos en el modelo: {len(nodos)}")
    print(f"  Restricciones: {len(prob.constraints)}")
    return prob, variables, arcos_data, nodos


def resolver_modelo(prob):
    """
    Ejecuta el solver de PuLP para resolver el problema LP.

    Parametros:
        prob (LpProblem): Problema de programacion lineal formulado.

    Retorna:
        str: Estado de la solucion ('Optimal', 'Infeasible', etc.)

    PuLP usa por defecto el solver CBC (Coin-or Branch and Cut),
    un solver open-source de programacion lineal y entera mixta.
    """
    prob.solve(pulp.PULP_CBC_CMD(msg=0))  # msg=0 suprime output del solver
    estado = pulp.LpStatus[prob.status]
    print(f"  Estado del solver: {estado}")
    return estado


def analizar_resultados(prob, variables, arcos_data):
    """
    Extrae metricas detalladas de la solucion optima del LP.

    Parametros:
        prob (LpProblem): Problema resuelto.
        variables (dict): Variables de decision con valores optimos.
        arcos_data (dict): Datos de los arcos.

    Retorna:
        dict: Metricas del modelo incluyendo costo total, flujos
              por origen/destino, y arcos activos.
    """
    costo_total = pulp.value(prob.objective)

    resultados = {
        'costo_total': costo_total,
        'flujo_origenes': {},
        'flujo_destinos': {},
        'arcos_activos': [],
        'restriccion_cumple': False
    }

    # Flujo por origen (saliente - entrante)
    for origen in NODOS_ORIGEN:
        saliente = sum(variables[(i, j)].varValue for (i, j) in arcos_data if i == origen)
        entrante = sum(variables[(i, j)].varValue for (i, j) in arcos_data if j == origen)
        resultados['flujo_origenes'][origen] = saliente - entrante

    # Flujo por destino (entrante - saliente)
    for destino in NODOS_DESTINO:
        entrante = sum(variables[(i, j)].varValue for (i, j) in arcos_data if j == destino)
        saliente = sum(variables[(i, j)].varValue for (i, j) in arcos_data if i == destino)
        resultados['flujo_destinos'][destino] = entrante - saliente

    # Verificar restriccion del 20%
    resultados['restriccion_cumple'] = resultados['flujo_destinos'].get(80, 0) >= MIN_FLUJO_NODO_80

    # Arcos activos (flujo > 0)
    for (i, j), var in variables.items():
        flujo = var.varValue
        if flujo is not None and flujo > 0.001:
            cap = arcos_data[(i, j)]['capacidad']
            costo = arcos_data[(i, j)]['costo']
            resultados['arcos_activos'].append((i, j, flujo, cap, costo))

    return resultados


def calcular_layout(G):
    """
    Layout jerarquico: origenes IZQUIERDA, destinos DERECHA.
    Usa BFS para agrupar nodos intermedios en capas.
    """
    pos = {}
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

    capas = {}
    for nodo, prof in profundidad.items():
        if nodo in NODOS_DESTINO:
            continue
        if prof not in capas:
            capas[prof] = []
        capas[prof].append(nodo)

    num_capas = max(capas.keys()) + 2 if capas else 2

    for prof, nodos in capas.items():
        x = prof
        nodos_sorted = sorted(nodos)
        n = len(nodos_sorted)
        for i, nodo in enumerate(nodos_sorted):
            y = (i - (n - 1) / 2) * 1.2
            pos[nodo] = (x, y)

    destinos_en_grafo = [d for d in NODOS_DESTINO if d in G]
    n_dest = len(destinos_en_grafo)
    for i, nodo in enumerate(sorted(destinos_en_grafo)):
        y = (i - (n_dest - 1) / 2) * 2.5
        pos[nodo] = (num_capas, y)

    return pos


def generar_grafica(G_vis, resultados, output_dir):
    """
    Genera la visualizacion del grafo con el flujo optimo.
    Layout: origenes IZQUIERDA -> destinos DERECHA.
    """
    pos = calcular_layout(G_vis)

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

    nx.draw_networkx_edges(G_vis, pos, edge_color='#333333', alpha=0.3,
                           arrows=True, arrowsize=8, ax=ax, width=0.5,
                           connectionstyle='arc3,rad=0.05')

    active_edges = [(u, v) for u, v, _, _, _ in resultados['arcos_activos']
                    if G_vis.has_edge(u, v)]
    if active_edges:
        nx.draw_networkx_edges(G_vis, pos, edgelist=active_edges,
                               edge_color='#9b59b6', alpha=0.9,
                               arrows=True, arrowsize=12, ax=ax, width=2.5,
                               connectionstyle='arc3,rad=0.05')

    nx.draw_networkx_nodes(G_vis, pos, node_color=node_colors, node_size=400,
                           edgecolors='white', linewidths=1.0, ax=ax)
    nx.draw_networkx_labels(G_vis, pos, font_size=7, font_color='white',
                            font_weight='bold', ax=ax)

    edge_labels = {(u, v): f"{f:.0f}"
                   for u, v, f, _, _ in resultados['arcos_activos']
                   if G_vis.has_edge(u, v)}
    nx.draw_networkx_edge_labels(G_vis, pos, edge_labels=edge_labels,
                                 font_size=6, font_color='#d7bde2',
                                 bbox=dict(boxstyle='round,pad=0.15',
                                           facecolor='#2c3e50', alpha=0.8),
                                 ax=ax)

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

    costo = resultados['costo_total']
    legend_patches = [
        mpatches.Patch(color='#2ecc71', label='Nodos Origen (1, 2)'),
        mpatches.Patch(color='#e74c3c', label='Nodos Destino (78, 79, 80)'),
        mpatches.Patch(color='#85c1e9', label='Nodos Intermedios'),
        mpatches.Patch(color='#9b59b6', label=f'Arcos con flujo - PuLP (costo: {costo:.0f})'),
    ]
    ax.legend(handles=legend_patches, loc='lower left', fontsize=10,
              facecolor='#2c3e50', edgecolor='white', labelcolor='white')

    fd = resultados['flujo_destinos']
    ax.set_title(
        f'Modelo 1 (PuLP): Flujo al Costo Minimo\n'
        f'Flujo Total: {FLUJO_TOTAL} | Costo Minimo: {costo:.0f} | '
        f'Nodo 80 recibe: {fd.get(80, 0):.0f} (>={MIN_FLUJO_NODO_80})',
        fontsize=14, fontweight='bold', color='white', pad=20)

    plt.tight_layout()
    output_path = os.path.join(output_dir, 'flujo_costo_minimo_pulp.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='#1a1a2e')
    plt.close()
    print(f"  Grafica guardada en: {output_path}")


def generar_readme(resultados, output_dir):
    """Genera README.md con resultados detallados del modelo PuLP."""
    fd = resultados['flujo_destinos']
    fo = resultados['flujo_origenes']
    costo = resultados['costo_total']
    cumple = "SI" if resultados['restriccion_cumple'] else "NO"
    tiempo = resultados['tiempo_ejecucion']

    contenido = f"""# Modelo 1 (PuLP): Flujo al Costo Minimo

## Descripcion

Variante del Modelo 1 usando **PuLP** (programacion lineal) en lugar de NetworkX.
Se formula como un **problema de programacion lineal (LP)** y se resuelve con el
solver **CBC** (Coin-or Branch and Cut).

## Formulacion LP

```
Minimizar: SUM(costo_ij * x_ij)  para todo arco (i,j)

Sujeto a:
  0 <= x_ij <= capacidad_ij         (limites de flujo)
  SUM(x_out) - SUM(x_in) = 0       (conservacion en nodos intermedios)
  Flujo total desde origenes = {FLUJO_TOTAL}
  Flujo al nodo 80 >= {MIN_FLUJO_NODO_80}
```

## Resultados

| Metrica | Valor |
|---|---|
| **Costo total minimo** | **{costo:.0f}** |
| Restriccion nodo 80 (>= {MIN_FLUJO_NODO_80}) | **{cumple}** |
| Arcos activos | {len(resultados['arcos_activos'])} |
| **Tiempo de ejecucion** | **{tiempo:.4f} segundos** |
| Solver | CBC (PuLP) |

### Flujo por Origen

| Nodo Origen | Flujo Enviado |
|---|---|
"""
    for origen, flujo in fo.items():
        contenido += f"| Nodo {origen} | {flujo:.0f} |\n"

    contenido += f"""
### Flujo por Destino

| Nodo Destino | Flujo Recibido | Porcentaje |
|---|---|---|
"""
    for destino, flujo in fd.items():
        pct = (flujo / FLUJO_TOTAL * 100) if FLUJO_TOTAL > 0 else 0
        contenido += f"| Nodo {destino} | {flujo:.0f} | {pct:.1f}% |\n"

    contenido += f"""
### Arcos Activos

| Origen | Destino | Flujo | Capacidad | Costo Unitario | Costo x Flujo |
|---|---|---|---|---|---|
"""
    for u, v, flujo, cap, costo_u in resultados['arcos_activos']:
        contenido += f"| {u} | {v} | {flujo:.0f} | {cap} | {costo_u} | {costo_u * flujo:.0f} |\n"

    contenido += f"""
## Grafica

![Flujo al Costo Minimo PuLP](flujo_costo_minimo_pulp.png)
"""

    readme_path = os.path.join(output_dir, 'README.md')
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(contenido)
    print(f"  README.md guardado en: {readme_path}")


# ═══════════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    print("=" * 70)
    print("  MODELO 1 (PuLP): FLUJO AL COSTO MINIMO")
    print("=" * 70)

    print("\n[1/7] Cargando datos...")
    df = cargar_datos(DATA_PATH)

    print("\n[2/7] Construyendo modelo LP...")
    prob, variables, arcos_data, nodos = construir_modelo(df)

    print("\n[3/7] Resolviendo con PuLP (CBC)...")
    t_inicio = time.time()
    estado = resolver_modelo(prob)
    t_fin = time.time()
    tiempo_ejecucion = t_fin - t_inicio
    print(f"  Tiempo de ejecucion: {tiempo_ejecucion:.4f} segundos")

    if estado != 'Optimal':
        print(f"  ERROR: Solucion no optima ({estado})")
        sys.exit(1)

    print("\n[4/7] Analizando resultados...")
    resultados = analizar_resultados(prob, variables, arcos_data)
    resultados['tiempo_ejecucion'] = tiempo_ejecucion

    print(f"\n  Costo total minimo: {resultados['costo_total']:.0f}")
    for destino, flujo in resultados['flujo_destinos'].items():
        pct = flujo / FLUJO_TOTAL * 100
        print(f"  Nodo {destino}: {flujo:.0f} ({pct:.1f}%)")

    print("\n[5/7] Generando grafica...")
    G_vis = nx.DiGraph()
    for _, row in df.iterrows():
        G_vis.add_edge(int(row['Origen']), int(row['Destino']))
    generar_grafica(G_vis, resultados, OUTPUT_DIR)

    print("\n[6/7] Generando README.md...")
    generar_readme(resultados, OUTPUT_DIR)

    print("\n" + "=" * 70)
    print("  Modelo 1 (PuLP) completado exitosamente!")
    print("=" * 70)
