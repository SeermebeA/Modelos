"""
Visualización del Grafo Completo
=================================
Este script genera una visualización de la topología completa 
de la red, mostrando los 80 nodos y los 391 arcos sin ejecutar 
ningún modelo de optimización.
"""

import os
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# --- Configuración ---
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_PATH = os.path.join(BASE_DIR, 'data', 'matriz_de_datos.csv')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output', 'grafo_completo')
os.makedirs(OUTPUT_DIR, exist_ok=True)

NODOS_ORIGEN = [1, 2]
NODOS_DESTINO = [78, 79, 80]

def cargar_datos():
    df = pd.read_csv(DATA_PATH)
    print(f"Total de arcos leídos: {len(df)}")
    return df

def construir_grafo(df):
    G = nx.DiGraph()
    for _, row in df.iterrows():
        i, j = int(row['Origen']), int(row['Destino'])
        cap = int(row['Capacidad'])
        G.add_edge(i, j, capacity=cap)
    print(f"Total de nodos en el grafo: {G.number_of_nodes()}")
    return G

def calcular_layout(G):
    pos = {}
    profundidad = {}
    
    # Calcular distancia desde orígenes usando BFS
    for origen in NODOS_ORIGEN:
        if origen in G:
            for n, d in nx.single_source_shortest_path_length(G, origen).items():
                if n not in profundidad or d < profundidad[n]:
                    profundidad[n] = d
                    
    mx = max(profundidad.values()) if profundidad else 0
    for n in G.nodes():
        if n not in profundidad:
            profundidad[n] = mx
            
    capas = {}
    for n, p in profundidad.items():
        if n not in NODOS_DESTINO:
            capas.setdefault(p, []).append(n)
            
    nc = max(capas.keys()) + 2 if capas else 2
    
    # Distribuir nodos en capas verticales
    for p, ns in capas.items():
        ns = sorted(ns)
        for i, n in enumerate(ns):
            pos[n] = (p, (i - (len(ns) - 1) / 2) * 1.5)
            
    # Posicionar destinos al final
    ds = sorted([d for d in NODOS_DESTINO if d in G])
    for i, n in enumerate(ds):
        pos[n] = (nc, (i - (len(ds) - 1) / 2) * 4.0)
        
    return pos

def visualizar_grafo(G):
    print("Calculando layout...")
    pos = calcular_layout(G)
    
    node_colors = []
    for node in G.nodes():
        if node in NODOS_ORIGEN:
            node_colors.append('#2ecc71')  # Verde (Orígenes)
        elif node in NODOS_DESTINO:
            node_colors.append('#e74c3c')  # Rojo (Destinos)
        else:
            node_colors.append('#85c1e9')  # Azul (Intermedios)
            
    fig, ax = plt.subplots(1, 1, figsize=(30, 20))
    fig.patch.set_facecolor('#1a1a2e')
    ax.set_facecolor('#1a1a2e')
    
    print("Dibujando arcos (esto puede tardar unos segundos)...")
    nx.draw_networkx_edges(G, pos, edge_color='#f39c12', alpha=0.4, 
                           arrows=True, arrowsize=10, ax=ax, width=1.0, 
                           connectionstyle='arc3,rad=0.1')
                           
    print("Dibujando nodos y etiquetas...")
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=500, 
                           edgecolors='white', linewidths=1.5, ax=ax)
    nx.draw_networkx_labels(G, pos, font_size=8, font_color='white', 
                            font_weight='bold', ax=ax)
                            
    # Leyendas
    legend_patches = [
        mpatches.Patch(color='#2ecc71', label='Orígenes (1, 2)'),
        mpatches.Patch(color='#e74c3c', label='Destinos (78, 79, 80)'),
        mpatches.Patch(color='#85c1e9', label='Nodos Intermedios'),
        mpatches.Patch(color='#f39c12', label=f'Arcos ({G.number_of_edges()})')
    ]
    ax.legend(handles=legend_patches, loc='lower left', fontsize=12, 
              facecolor='#2c3e50', edgecolor='white', labelcolor='white')
              
    ax.set_title(f"Topología Completa de la Red\nNodos: {G.number_of_nodes()} | Arcos: {G.number_of_edges()}", 
                 fontsize=18, fontweight='bold', color='white', pad=20)
                 
    plt.tight_layout()
    output_path = os.path.join(OUTPUT_DIR, 'grafo_completo.png')
    plt.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='#1a1a2e')
    plt.close()
    print(f"Gráfica guardada en: {output_path}")

def generar_reporte(G):
    # Genera un listado en texto de los arcos
    reporte_path = os.path.join(OUTPUT_DIR, 'lista_de_arcos.txt')
    with open(reporte_path, 'w', encoding='utf-8') as f:
        f.write(f"REPORTE DE TOPOLOGÍA DE RED\n")
        f.write(f"===========================\n")
        f.write(f"Total Nodos: {G.number_of_nodes()}\n")
        f.write(f"Total Arcos: {G.number_of_edges()}\n\n")
        
        f.write("LISTADO COMPLETO DE ARCOS:\n")
        f.write("--------------------------\n")
        f.write("FORMATO: Origen -> Destino (Capacidad)\n\n")
        
        for u, v, data in sorted(G.edges(data=True), key=lambda x: (x[0], x[1])):
            f.write(f"Nodo {u:02d} -> Nodo {v:02d}  (Capacidad: {data.get('capacity', 'N/A')})\n")
            
    print(f"Reporte en texto guardado en: {reporte_path}")

if __name__ == '__main__':
    df = cargar_datos()
    G = construir_grafo(df)
    visualizar_grafo(G)
    generar_reporte(G)
    print("\nProceso exitoso. Revise la carpeta 'output/grafo_completo'.")
