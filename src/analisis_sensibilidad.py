"""
Script de Análisis de Sensibilidad para Modelos de Optimización de Redes
========================================================================
Este script resuelve las versiones PuLP de los modelos M1 (Costo Mínimo) 
y M2 (Flujo Máximo) para extraer información dual:
1. Shadow Prices (Precios Sombra) de las restricciones.
2. Reduced Costs (Costos Reducidos) de los arcos.
"""

import os
import pandas as pd
import pulp
import time

# --- Configuración ---
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_PATH = os.path.join(BASE_DIR, 'data', 'matriz_de_datos.csv')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output', 'analisis_sensibilidad')
os.makedirs(OUTPUT_DIR, exist_ok=True)

NODOS_ORIGEN = [1, 2]
NODOS_DESTINO = [78, 79, 80]
FLUJO_TOTAL_M1 = 500
MIN_FLUJO_NODO_80 = 100

def cargar_datos():
    return pd.read_csv(DATA_PATH)

def analisis_m1_costo_minimo(df):
    """Resuelve M1 y extrae sensibilidad."""
    print("\n--- Analizando Sensibilidad: Modelo 1 (Costo Mínimo) ---")
    prob = pulp.LpProblem("M1_Sensibilidad", pulp.LpMinimize)
    
    arcos = {}
    nodos = set()
    for _, row in df.iterrows():
        i, j = int(row['Origen']), int(row['Destino'])
        arcos[(i, j)] = {'costo': int(row['Costo']), 'cap': int(row['Capacidad'])}
        nodos.update([i, j])
        
    vars_x = {(i, j): pulp.LpVariable(f"x_{i}_{j}", 0, d['cap']) for (i, j), d in arcos.items()}
    
    # Objetivo
    prob += pulp.lpSum(arcos[k]['costo'] * vars_x[k] for k in arcos)
    
    # Restricciones con nombres para identificar el dual
    constraints = {}
    for n in nodos:
        in_f = pulp.lpSum(vars_x[k] for k in arcos if k[1] == n)
        out_f = pulp.lpSum(vars_x[k] for k in arcos if k[0] == n)
        if n not in NODOS_ORIGEN and n not in NODOS_DESTINO:
            constraints[f"Node_{n}"] = (in_f == out_f)
            prob += (in_f == out_f, f"Node_{n}")
            
    # Orígenes y Destinos globales
    prob += (pulp.lpSum(vars_x[k] for k in arcos if k[0] in NODOS_ORIGEN) - 
             pulp.lpSum(vars_x[k] for k in arcos if k[1] in NODOS_ORIGEN) == FLUJO_TOTAL_M1, "Global_Supply")
             
    prob += (pulp.lpSum(vars_x[k] for k in arcos if k[1] in NODOS_DESTINO) - 
             pulp.lpSum(vars_x[k] for k in arcos if k[0] in NODOS_DESTINO) == FLUJO_TOTAL_M1, "Global_Demand")
             
    prob += (pulp.lpSum(vars_x[k] for k in arcos if k[1] == 80) - 
             pulp.lpSum(vars_x[k] for k in arcos if k[0] == 80) >= MIN_FLUJO_NODO_80, "Min_Node_80")

    prob.solve(pulp.PULP_CBC_CMD(msg=0))
    
    # Extraer Precios Sombra (Shadow Prices)
    shadow_prices = []
    for name, c in prob.constraints.items():
        shadow_prices.append({'Restricción': name, 'Shadow_Price': c.pi})
        
    # Extraer Costos Reducidos (Reduced Costs)
    reduced_costs = []
    for k, v in vars_x.items():
        if v.varValue < 0.001: # Solo arcos no usados o en su límite
            reduced_costs.append({'Arco': f"{k[0]}->{k[1]}", 'Flujo': v.varValue, 'Cost_Unit': arcos[k]['costo'], 'Reduced_Cost': v.dj})

    return shadow_prices, reduced_costs

def analisis_m2_flujo_maximo(df):
    """Resuelve M2 y identifica arcos críticos (cuellos de botella)."""
    print("\n--- Analizando Sensibilidad: Modelo 2 (Flujo Máximo) ---")
    prob = pulp.LpProblem("M2_Sensibilidad", pulp.LpMaximize)
    
    arcos = {}
    nodos = set()
    for _, r in df.iterrows():
        i, j = int(r['Origen']), int(r['Destino'])
        arcos[(i,j)] = {'cap': int(r['Capacidad'])}
        nodos.update([i, j])
        
    vs = {(i,j): pulp.LpVariable(f"x_{i}_{j}", 0, d['cap']) for (i,j), d in arcos.items()}
    F = pulp.LpVariable("F", 0)
    prob += F
    
    for n in nodos:
        fi = pulp.lpSum(vs[k] for k in arcos if k[1] == n)
        fo = pulp.lpSum(vs[k] for k in arcos if k[0] == n)
        if n not in NODOS_ORIGEN and n not in NODOS_DESTINO:
            prob += fi == fo, f"Cons_{n}"
            
    prob += pulp.lpSum(vs[k] for k in arcos if k[0] in NODOS_ORIGEN) - pulp.lpSum(vs[k] for k in arcos if k[1] in NODOS_ORIGEN) == F, "Supply_F"
    prob += pulp.lpSum(vs[k] for k in arcos if k[1] in NODOS_DESTINO) - pulp.lpSum(vs[k] for k in arcos if k[0] in NODOS_DESTINO) == F, "Demand_F"
    
    prob.solve(pulp.PULP_CBC_CMD(msg=0))
    
    # En flujo máximo, los arcos saturados con Reduced Cost != 0 son los cuellos de botella
    bottlenecks = []
    for k, v in vs.items():
        f = v.varValue
        cap = arcos[k]['cap']
        if abs(f - cap) < 0.001:
            # En maximización, el Reduced Cost indica cuánto aumentaría F por unidad de capacidad
            if v.dj != 0:
                bottlenecks.append({'Arco': f"{k[0]}->{k[1]}", 'Capacidad': cap, 'Impacto_F': v.dj})
                
    return F.varValue, bottlenecks

def generar_reporte(m1_data, m2_data):
    sp_m1, rc_m1 = m1_data
    fm_m2, bn_m2 = m2_data
    
    path = os.path.join(OUTPUT_DIR, 'README.md')
    with open(path, 'w', encoding='utf-8') as f:
        f.write("# Informe de Análisis de Sensibilidad\n\n")
        f.write("Este informe detalla los impactos marginales y cuellos de botella del sistema de transporte.\n\n")
        
        f.write("## 1. Modelo de Costo Mínimo (M1)\n")
        f.write("### Precios Sombra (Shadow Prices) Clave\n")
        f.write("| Restricción | Precio Sombra | Significado |\n")
        f.write("|---|---|---|\n")
        for sp in sp_m1:
            if abs(sp['Shadow_Price']) > 0:
                desc = "Costo marginal por unidad extra"
                if "Global" in sp['Restricción']: desc = "Costo de la última unidad enviada"
                if "Node_80" in sp['Restricción']: desc = "Sobrecosto por obligar flujo al Nodo 80"
                f.write(f"| {sp['Restricción']} | {sp['Shadow_Price']:.2f} | {desc} |\n")
        
        f.write("\n### Costos Reducidos (Oportunidades de Mejora)\n")
        f.write("Muestra cuánto debería bajar el costo de un arco para ser utilizado.\n\n")
        f.write("| Arco | Costo Actual | Costo Reducido | Nuevo Costo Objetivo |\n")
        f.write("|---|---|---|---|\n")
        rc_sorted = sorted(rc_m1, key=lambda x: x['Reduced_Cost'], reverse=True)[:10]
        for rc in rc_sorted:
            f.write(f"| {rc['Arco']} | {rc['Cost_Unit']} | {rc['Reduced_Cost']:.2f} | {rc['Cost_Unit'] - rc['Reduced_Cost']:.2f} |\n")
            
        f.write("\n---\n\n")
        
        f.write("## 2. Modelo de Flujo Máximo (M2)\n")
        f.write(f"**Flujo Máximo Total:** {fm_m2:.0f} unidades.\n\n")
        f.write("### Cuellos de Botella Críticos\n")
        f.write("Arcos cuya capacidad limita el flujo de toda la red. Aumentar una unidad de capacidad en estos arcos aumenta el flujo total en el valor indicado.\n\n")
        f.write("| Arco | Capacidad Actual | Impacto Marginal en Flujo |\n")
        f.write("|---|---|---|\n")
        for bn in sorted(bn_m2, key=lambda x: x['Impacto_F'], reverse=True):
            f.write(f"| {bn['Arco']} | {bn['Capacidad']} | {bn['Impacto_F']:.2f} |\n")

    print(f"\nReporte generado en: {path}")

if __name__ == "__main__":
    df = cargar_datos()
    m1_res = analisis_m1_costo_minimo(df)
    m2_res = analisis_m2_flujo_maximo(df)
    generar_reporte(m1_res, m2_res)
