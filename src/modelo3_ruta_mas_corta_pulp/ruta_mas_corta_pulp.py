"""
Modelo 3 (PuLP): Ruta Mas Corta
=================================
Variante usando PuLP (LP) para resolver ruta mas corta.
Formulacion: Minimizar SUM(distancia_ij * x_ij) donde x_ij in {0,1}
sujeto a conservacion de flujo unitario.
"""
import os, sys, time
import pandas as pd
import pulp
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATA_PATH = os.path.join(BASE_DIR, 'data', 'matriz_de_datos.csv')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output', 'modelo3_pulp')
os.makedirs(OUTPUT_DIR, exist_ok=True)
NODOS_ORIGEN = [1, 2]
NODOS_DESTINO = [78, 79, 80]

def cargar_datos(ruta):
    df = pd.read_csv(ruta)
    print(f"  Arcos: {len(df)}")
    return df

def resolver_ruta_pulp(df, origen, destino):
    """
    Resuelve ruta mas corta entre origen y destino usando LP.
    Formula: min SUM(dist_ij * x_ij) con flujo unitario.
    x_ij binarias (0 o 1), conservacion de flujo en intermedios.
    """
    prob = pulp.LpProblem(f"Ruta_{origen}_{destino}", pulp.LpMinimize)
    arcos, nodos = {}, set()
    for _, r in df.iterrows():
        i, j = int(r['Origen']), int(r['Destino'])
        arcos[(i,j)] = {'dist': int(r['Distancia']), 'costo': int(r['Costo']), 'cap': int(r['Capacidad'])}
        nodos.update([i, j])
    vs = {(i,j): pulp.LpVariable(f"x_{i}_{j}", 0, 1, cat='Binary') for (i,j) in arcos}
    prob += pulp.lpSum(arcos[(i,j)]['dist'] * vs[(i,j)] for (i,j) in arcos)
    for n in nodos:
        fi = pulp.lpSum(vs[(i,j)] for (i,j) in arcos if j == n)
        fo = pulp.lpSum(vs[(i,j)] for (i,j) in arcos if i == n)
        if n == origen:
            prob += fo - fi == 1, f"Origen_{n}"
        elif n == destino:
            prob += fi - fo == 1, f"Destino_{n}"
        else:
            prob += fi == fo, f"Cons_{n}"
    prob.solve(pulp.PULP_CBC_CMD(msg=0))
    if pulp.LpStatus[prob.status] != 'Optimal':
        return None
    # Reconstruir ruta
    arcos_usados = [(i,j) for (i,j), v in vs.items() if v.varValue and v.varValue > 0.5]
    dist_total = pulp.value(prob.objective)
    # Ordenar ruta
    ruta = [origen]
    actual = origen
    while actual != destino:
        siguiente = [j for (i,j) in arcos_usados if i == actual]
        if not siguiente: break
        actual = siguiente[0]
        ruta.append(actual)
    return {'origen': origen, 'destino': destino, 'distancia': dist_total,
            'ruta': ruta, 'num_arcos': len(ruta)-1, 'encontrada': True,
            'arcos_detalle': [(i,j, arcos[(i,j)]['dist'], arcos[(i,j)]['costo'], arcos[(i,j)]['cap']) for (i,j) in arcos_usados]}

def calcular_layout(G):
    pos, prof = {}, {}
    for o in NODOS_ORIGEN:
        if o in G:
            for n, d in nx.single_source_shortest_path_length(G, o).items():
                if n not in prof or d < prof[n]: prof[n] = d
    mx = max(prof.values()) if prof else 0
    for n in G.nodes():
        if n not in prof: prof[n] = mx
    capas = {}
    for n, p in prof.items():
        if n not in NODOS_DESTINO: capas.setdefault(p, []).append(n)
    nc = max(capas.keys()) + 2 if capas else 2
    for p, ns in capas.items():
        ns = sorted(ns)
        for i, n in enumerate(ns): pos[n] = (p, (i-(len(ns)-1)/2)*1.2)
    ds = sorted([d for d in NODOS_DESTINO if d in G])
    for i, n in enumerate(ds): pos[n] = (nc, (i-(len(ds)-1)/2)*2.5)
    return pos

def main():
    print("="*70); print("  MODELO 3 (PuLP): RUTA MAS CORTA"); print("="*70)
    df = cargar_datos(DATA_PATH)
    G = nx.DiGraph()
    for _, r in df.iterrows():
        G.add_edge(int(r['Origen']), int(r['Destino']), weight=int(r['Distancia']))

    # Resolver todas las combinaciones
    print("\n  Resolviendo 6 combinaciones con PuLP...")
    t0 = time.time()
    resultados = []
    for o in NODOS_ORIGEN:
        for d in NODOS_DESTINO:
            res = resolver_ruta_pulp(df, o, d)
            if res:
                resultados.append(res)
                print(f"  {o} -> {d}: dist={res['distancia']:.0f}, arcos={res['num_arcos']}")
            else:
                resultados.append({'origen':o,'destino':d,'distancia':None,'ruta':None,'num_arcos':0,'encontrada':False})
                print(f"  {o} -> {d}: NO EXISTE")
    tiempo = time.time() - t0
    print(f"  Tiempo total: {tiempo:.4f}s")

    # Mejor ruta
    validas = [r for r in resultados if r['encontrada']]
    mejor = min(validas, key=lambda r: r['distancia']) if validas else None
    if mejor:
        print(f"\n  MEJOR: {mejor['origen']} -> {mejor['destino']}, dist={mejor['distancia']:.0f}")

    # Grafica todas las rutas
    pos = calcular_layout(G)
    colores = ['#e74c3c','#f39c12','#2ecc71','#3498db','#9b59b6','#1abc9c']
    fig, ax = plt.subplots(1,1,figsize=(24,16)); fig.patch.set_facecolor('#1a1a2e'); ax.set_facecolor('#1a1a2e')
    nx.draw_networkx_edges(G, pos, edge_color='#333', alpha=0.3, arrows=True, arrowsize=8, ax=ax, width=0.5, connectionstyle='arc3,rad=0.05')
    sorted_r = sorted(validas, key=lambda r: r['distancia'], reverse=True)
    legends = []
    for idx, r in enumerate(sorted_r):
        edges = list(zip(r['ruta'][:-1], r['ruta'][1:]))
        c = colores[idx % len(colores)]
        es_mejor = mejor and r['origen']==mejor['origen'] and r['destino']==mejor['destino']
        w, a, s = (4, 1.0, 'solid') if es_mejor else (2, 0.7, 'dashed')
        nx.draw_networkx_edges(G, pos, edgelist=edges, edge_color=c, alpha=a, arrows=True, arrowsize=14, ax=ax, width=w, style=s, connectionstyle='arc3,rad=0.05')
        lb = f"{r['origen']}->{r['destino']} (dist={r['distancia']:.0f})"
        if es_mejor: lb += " << MEJOR"
        legends.append(Line2D([0],[0], color=c, linewidth=w, linestyle='-' if es_mejor else '--', label=lb))
    ncolors = ['#2ecc71' if n in NODOS_ORIGEN else '#e74c3c' if n in NODOS_DESTINO else '#85c1e9' for n in G.nodes()]
    nx.draw_networkx_nodes(G, pos, node_color=ncolors, node_size=400, edgecolors='white', linewidths=1.0, ax=ax)
    nx.draw_networkx_labels(G, pos, font_size=7, font_color='white', font_weight='bold', ax=ax)
    ax.annotate('ENTRADAS\n(Origenes)', xy=(0.05,0.95), xycoords='axes fraction', fontsize=12, fontweight='bold', color='#2ecc71', ha='center', va='top', bbox=dict(boxstyle='round,pad=0.5', facecolor='#2c3e50', alpha=0.9))
    ax.annotate('SALIDAS\n(Destinos)', xy=(0.95,0.95), xycoords='axes fraction', fontsize=12, fontweight='bold', color='#e74c3c', ha='center', va='top', bbox=dict(boxstyle='round,pad=0.5', facecolor='#2c3e50', alpha=0.9))
    ax.annotate('', xy=(0.85,0.02), xytext=(0.15,0.02), xycoords='axes fraction', arrowprops=dict(arrowstyle='->', color='white', lw=2))
    ax.text(0.5,0.02,'Direccion del flujo',transform=ax.transAxes, fontsize=10, color='white', ha='center', va='bottom')
    ax.set_title(f'Modelo 3 (PuLP): Rutas Mas Cortas\nMejor: {mejor["origen"]}->{mejor["destino"]} (dist={mejor["distancia"]:.0f})', fontsize=14, fontweight='bold', color='white', pad=20)
    base_lg = [mpatches.Patch(color='#2ecc71',label='Origen'), mpatches.Patch(color='#e74c3c',label='Destino'), mpatches.Patch(color='#85c1e9',label='Intermedios')]
    ax.legend(handles=base_lg+legends, loc='lower left', fontsize=9, facecolor='#2c3e50', edgecolor='white', labelcolor='white')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'todas_las_rutas_pulp.png'), dpi=150, bbox_inches='tight', facecolor='#1a1a2e'); plt.close()

    # Grafica mejor ruta
    fig, ax = plt.subplots(1,1,figsize=(24,16)); fig.patch.set_facecolor('#1a1a2e'); ax.set_facecolor('#1a1a2e')
    nx.draw_networkx_edges(G, pos, edge_color='#333', alpha=0.3, arrows=True, arrowsize=8, ax=ax, width=0.5, connectionstyle='arc3,rad=0.05')
    if mejor:
        be = list(zip(mejor['ruta'][:-1], mejor['ruta'][1:]))
        nx.draw_networkx_edges(G, pos, edgelist=be, edge_color='#f1c40f', alpha=1.0, arrows=True, arrowsize=16, ax=ax, width=4, connectionstyle='arc3,rad=0.05')
        el = {}
        for i in range(len(mejor['ruta'])-1):
            u, v = mejor['ruta'][i], mejor['ruta'][i+1]
            el[(u,v)] = f"d={G[u][v]['weight']}"
        nx.draw_networkx_edge_labels(G, pos, edge_labels=el, font_size=7, font_color='#f1c40f', bbox=dict(boxstyle='round,pad=0.2', facecolor='#2c3e50', alpha=0.9), ax=ax)
    nc2, ns2 = [], []
    for n in G.nodes():
        if mejor and n in mejor['ruta']:
            nc2.append('#2ecc71' if n in NODOS_ORIGEN else '#e74c3c' if n in NODOS_DESTINO else '#f1c40f')
            ns2.append(550)
        else: nc2.append('#555'); ns2.append(200)
    nx.draw_networkx_nodes(G, pos, node_color=nc2, node_size=ns2, edgecolors='white', linewidths=1.0, ax=ax)
    nx.draw_networkx_labels(G, pos, font_size=7, font_color='white', font_weight='bold', ax=ax)
    ax.annotate('ENTRADAS\n(Origenes)', xy=(0.05,0.95), xycoords='axes fraction', fontsize=12, fontweight='bold', color='#2ecc71', ha='center', va='top', bbox=dict(boxstyle='round,pad=0.5', facecolor='#2c3e50', alpha=0.9))
    ax.annotate('SALIDAS\n(Destinos)', xy=(0.95,0.95), xycoords='axes fraction', fontsize=12, fontweight='bold', color='#e74c3c', ha='center', va='top', bbox=dict(boxstyle='round,pad=0.5', facecolor='#2c3e50', alpha=0.9))
    ax.annotate('', xy=(0.85,0.02), xytext=(0.15,0.02), xycoords='axes fraction', arrowprops=dict(arrowstyle='->', color='white', lw=2))
    ax.text(0.5,0.02,'Direccion del flujo',transform=ax.transAxes, fontsize=10, color='white', ha='center', va='bottom')
    ax.set_title(f'Modelo 3 (PuLP): Mejor Ruta\n{mejor["origen"]}->{mejor["destino"]} | Dist:{mejor["distancia"]:.0f} | Arcos:{mejor["num_arcos"]}', fontsize=14, fontweight='bold', color='white', pad=20)
    ax.legend(handles=[mpatches.Patch(color='#2ecc71',label=f'Origen ({mejor["origen"]})'), mpatches.Patch(color='#e74c3c',label=f'Destino ({mejor["destino"]})'), mpatches.Patch(color='#f1c40f',label='Nodos en ruta'), mpatches.Patch(color='#555',label='No utilizados')], loc='lower left', fontsize=10, facecolor='#2c3e50', edgecolor='white', labelcolor='white')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'ruta_mas_corta_pulp.png'), dpi=150, bbox_inches='tight', facecolor='#1a1a2e'); plt.close()

    # README
    c = "# Modelo 3 (PuLP): Ruta Mas Corta\n\n## Descripcion\nVariante usando **PuLP** (LP con variables binarias). Formula cada ruta como:\n"
    c += "**min SUM(dist_ij * x_ij)** con flujo unitario y x_ij binarias.\n\n"
    c += f"## Resultados\n\n| # | Origen | Destino | Distancia | Arcos |\n|---|---|---|---|---|\n"
    for idx, r in enumerate(sorted(validas, key=lambda x: x['distancia']), 1):
        marca = " **MEJOR**" if mejor and r['origen']==mejor['origen'] and r['destino']==mejor['destino'] else ""
        c += f"| {idx} | {r['origen']} | {r['destino']} | {r['distancia']:.0f} | {r['num_arcos']}{marca} |\n"
    c += f"\n| Metrica | Valor |\n|---|---|\n| **Mejor ruta** | **{mejor['origen']} -> {mejor['destino']}** |\n"
    c += f"| **Distancia** | **{mejor['distancia']:.0f}** |\n| **Ruta** | **{' -> '.join(map(str, mejor['ruta']))}** |\n"
    c += f"| **Tiempo total** | **{tiempo:.4f} seg** |\n| Solver | CBC (PuLP) |\n\n"
    c += "## Graficas\n\n![Todas las Rutas](todas_las_rutas_pulp.png)\n\n![Mejor Ruta](ruta_mas_corta_pulp.png)\n"
    with open(os.path.join(OUTPUT_DIR, 'README.md'), 'w', encoding='utf-8') as f: f.write(c)
    print("  Completado!")

if __name__ == '__main__': main()
