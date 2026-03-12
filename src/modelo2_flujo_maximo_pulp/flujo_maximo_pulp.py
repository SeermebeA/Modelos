"""
Modelo 2 (PuLP): Flujo Maximo
===============================
Variante usando PuLP (LP) para resolver flujo maximo.
Maximiza F sujeto a conservacion de flujo y capacidades.
"""
import os, sys, time
import pandas as pd
import pulp
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATA_PATH = os.path.join(BASE_DIR, 'data', 'matriz_de_datos.csv')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output', 'modelo2_pulp')
os.makedirs(OUTPUT_DIR, exist_ok=True)
NODOS_ORIGEN = [1, 2]
NODOS_DESTINO = [78, 79, 80]

def cargar_datos(ruta):
    """Lee CSV del grafo."""
    df = pd.read_csv(ruta)
    print(f"  Arcos: {len(df)}")
    return df

def construir_modelo(df):
    """Formula LP: Maximizar F sujeto a conservacion y capacidades."""
    prob = pulp.LpProblem("Flujo_Maximo", pulp.LpMaximize)
    arcos, nodos = {}, set()
    for _, r in df.iterrows():
        i, j = int(r['Origen']), int(r['Destino'])
        arcos[(i,j)] = {'cap': int(r['Capacidad']), 'costo': int(r['Costo']), 'dist': int(r['Distancia'])}
        nodos.update([i, j])
    vs = {(i,j): pulp.LpVariable(f"x_{i}_{j}", 0, d['cap']) for (i,j), d in arcos.items()}
    F = pulp.LpVariable("F", 0)
    prob += F
    for n in nodos:
        fi = pulp.lpSum(vs[(i,j)] for (i,j) in arcos if j == n)
        fo = pulp.lpSum(vs[(i,j)] for (i,j) in arcos if i == n)
        if n not in NODOS_ORIGEN and n not in NODOS_DESTINO:
            prob += fi == fo, f"Cons_{n}"
    prob += pulp.lpSum(vs[(i,j)] for (i,j) in arcos if i in NODOS_ORIGEN) - pulp.lpSum(vs[(i,j)] for (i,j) in arcos if j in NODOS_ORIGEN) == F
    prob += pulp.lpSum(vs[(i,j)] for (i,j) in arcos if j in NODOS_DESTINO) - pulp.lpSum(vs[(i,j)] for (i,j) in arcos if i in NODOS_DESTINO) == F
    return prob, vs, F, arcos, nodos

def calcular_layout(G):
    """Layout jerarquico izquierda->derecha."""
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
    print("="*70); print("  MODELO 2 (PuLP): FLUJO MAXIMO"); print("="*70)
    df = cargar_datos(DATA_PATH)
    prob, vs, F, arcos, nodos = construir_modelo(df)
    t0 = time.time()
    prob.solve(pulp.PULP_CBC_CMD(msg=0))
    tiempo = time.time() - t0
    estado = pulp.LpStatus[prob.status]
    print(f"  Estado: {estado}, Tiempo: {tiempo:.4f}s")
    if estado != 'Optimal': sys.exit(1)
    fm = F.varValue
    # Resultados
    res = {'flujo_maximo': fm, 'flujo_origenes': {}, 'flujo_destinos': {},
           'arcos_activos': [], 'arcos_saturados': [], 'total_saturados': 0, 'tiempo_ejecucion': tiempo}
    for o in NODOS_ORIGEN:
        res['flujo_origenes'][o] = sum(vs[(i,j)].varValue for (i,j) in arcos if i==o) - sum(vs[(i,j)].varValue for (i,j) in arcos if j==o)
    for d in NODOS_DESTINO:
        res['flujo_destinos'][d] = sum(vs[(i,j)].varValue for (i,j) in arcos if j==d) - sum(vs[(i,j)].varValue for (i,j) in arcos if i==d)
    for (i,j), v in vs.items():
        f = v.varValue
        if f and f > 0.001:
            c = arcos[(i,j)]['cap']
            res['arcos_activos'].append((i,j,f,c,f/c*100 if c else 0))
            if abs(f-c) < 0.001: res['arcos_saturados'].append((i,j,f,c))
    res['total_saturados'] = len(res['arcos_saturados'])
    print(f"  Flujo maximo: {fm:.0f}")
    for d, f in res['flujo_destinos'].items(): print(f"  Nodo {d}: {f:.0f}")
    # Grafica
    G_vis = nx.DiGraph()
    for _, r in df.iterrows(): G_vis.add_edge(int(r['Origen']), int(r['Destino']))
    pos = calcular_layout(G_vis)
    nc = ['#2ecc71' if n in NODOS_ORIGEN else '#e74c3c' if n in NODOS_DESTINO else '#85c1e9' for n in G_vis.nodes()]
    fig, ax = plt.subplots(1,1,figsize=(24,16)); fig.patch.set_facecolor('#1a1a2e'); ax.set_facecolor('#1a1a2e')
    nx.draw_networkx_edges(G_vis, pos, edge_color='#333', alpha=0.3, arrows=True, arrowsize=8, ax=ax, width=0.5, connectionstyle='arc3,rad=0.05')
    if res['arcos_activos']:
        mxf = max(f for _,_,f,_,_ in res['arcos_activos'])
        for u,v,f,_,_ in res['arcos_activos']:
            if G_vis.has_edge(u,v):
                nx.draw_networkx_edges(G_vis, pos, edgelist=[(u,v)], edge_color='#9b59b6', alpha=0.85, arrows=True, arrowsize=12, ax=ax, width=1+(f/mxf)*4, connectionstyle='arc3,rad=0.05')
    nx.draw_networkx_nodes(G_vis, pos, node_color=nc, node_size=400, edgecolors='white', linewidths=1.0, ax=ax)
    nx.draw_networkx_labels(G_vis, pos, font_size=7, font_color='white', font_weight='bold', ax=ax)
    el = {(u,v): f"{f:.0f}" for u,v,f,_,_ in res['arcos_activos'] if G_vis.has_edge(u,v)}
    nx.draw_networkx_edge_labels(G_vis, pos, edge_labels=el, font_size=6, font_color='#d7bde2', bbox=dict(boxstyle='round,pad=0.15', facecolor='#2c3e50', alpha=0.8), ax=ax)
    ax.annotate('ENTRADAS\n(Origenes)', xy=(0.05,0.95), xycoords='axes fraction', fontsize=12, fontweight='bold', color='#2ecc71', ha='center', va='top', bbox=dict(boxstyle='round,pad=0.5', facecolor='#2c3e50', alpha=0.9))
    ax.annotate('SALIDAS\n(Destinos)', xy=(0.95,0.95), xycoords='axes fraction', fontsize=12, fontweight='bold', color='#e74c3c', ha='center', va='top', bbox=dict(boxstyle='round,pad=0.5', facecolor='#2c3e50', alpha=0.9))
    ax.annotate('', xy=(0.85,0.02), xytext=(0.15,0.02), xycoords='axes fraction', arrowprops=dict(arrowstyle='->', color='white', lw=2))
    ax.text(0.5, 0.02, 'Direccion del flujo', transform=ax.transAxes, fontsize=10, color='white', ha='center', va='bottom')
    fd = res['flujo_destinos']
    ax.set_title(f'Modelo 2 (PuLP): Flujo Maximo\nFlujo: {fm:.0f} | N78:{fd.get(78,0):.0f} | N79:{fd.get(79,0):.0f} | N80:{fd.get(80,0):.0f}', fontsize=14, fontweight='bold', color='white', pad=20)
    ax.legend(handles=[mpatches.Patch(color='#2ecc71',label='Origen'), mpatches.Patch(color='#e74c3c',label='Destino'), mpatches.Patch(color='#85c1e9',label='Intermedios'), mpatches.Patch(color='#9b59b6',label=f'Flujo PuLP (max:{fm:.0f})')], loc='lower left', fontsize=10, facecolor='#2c3e50', edgecolor='white', labelcolor='white')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'flujo_maximo_pulp.png'), dpi=150, bbox_inches='tight', facecolor='#1a1a2e'); plt.close()
    # README
    c = f"# Modelo 2 (PuLP): Flujo Maximo\n\n## Descripcion\nVariante usando **PuLP** (LP). Maximiza F sujeto a conservacion de flujo.\n\n"
    c += f"## Resultados\n\n| Metrica | Valor |\n|---|---|\n| **Flujo maximo** | **{fm:.0f}** |\n| Arcos activos | {len(res['arcos_activos'])} |\n| Saturados | {res['total_saturados']} |\n| **Tiempo** | **{tiempo:.4f} seg** |\n| Solver | CBC |\n\n"
    c += "### Flujo por Destino\n\n| Nodo | Flujo | % |\n|---|---|---|\n"
    for d, f in fd.items(): c += f"| {d} | {f:.0f} | {f/fm*100:.1f}% |\n"
    c += f"\n### Saturados\n\n| Origen | Destino | Flujo | Cap |\n|---|---|---|---|\n"
    for u,v,f,cap in res['arcos_saturados']: c += f"| {u} | {v} | {f:.0f} | {cap} |\n"
    c += f"\n## Grafica\n\n![Flujo Maximo PuLP](flujo_maximo_pulp.png)\n"
    with open(os.path.join(OUTPUT_DIR, 'README.md'), 'w', encoding='utf-8') as f: f.write(c)
    print("  Completado!")

if __name__ == '__main__': main()
