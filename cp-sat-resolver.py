# Importa la libreria CP-SAT
from ortools.sat.python import cp_model
from collections import defaultdict

# --- Dati di Input (Istanza Figura 1 del paper) ---
# Nodi: s=0, a=1, b=2, c=3, d=4, e=5, t=6
N = 7  
s = 0  # Sorgente
t = 6  # Pozzo

arc_ids = ['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9']

arc_map = {
    'A1': (0, 1), 'A2': (0, 2), 'A3': (1, 4), 'A4': (1, 3), 
    'A5': (4, 6), 'A6': (3, 6), 'A7': (2, 3), 'A8': (2, 5), 'A9': (5, 6)
}

capacity_map = {
    'A1': 3, 'A2': 6, 'A3': 2, 'A4': 1, 
    'A5': 5, 'A6': 3, 'A7': 4, 'A8': 3, 'A9': 7
}

# Coppie di archi in conflitto (stesso colore, non nero, nella Figura 1)
conflict_pairs = [
    ('A6', 'A7'), ('A6', 'A9'), ('A7', 'A9'),  # Rosso
    ('A3', 'A4'),                             # Blu
    ('A2', 'A8')                              # Verde
]

# ----------------------------------------------------
# 1. Funzione per l'Inizializzazione del Modello e delle Variabili (Fase 1)
# ----------------------------------------------------
def setup_mfpc_model_phase1(N, s, t, arc_ids, arc_map, capacity_map):
    model = cp_model.CpModel()
    
    # Variabile z: Flusso Totale
    max_capacity = sum(capacity_map[a_id] for a_id in arc_ids if arc_map[a_id][0] == s)
    z = model.NewIntVar(0, max_capacity, 'total_flow')
    
    # Variabili f_ij: Flusso sugli archi
    f = {a_id: model.NewIntVar(0, capacity_map[a_id], f'f_{a_id}') for a_id in arc_ids}
        
    # Variabili x_ij: Attivazione degli archi (Binaria)
    x = {a_id: model.NewBoolVar(f'x_{a_id}') for a_id in arc_ids}

    return model, z, f, x

# ----------------------------------------------------
# 2. Funzione per l'Aggiunta dei Vincoli (Fase 2)
# ----------------------------------------------------
def add_mfpc_constraints_phase2(model, z, f, x, N, s, t, arc_ids, arc_map, capacity_map, conflict_pairs):
    
    arcs_out = defaultdict(list)
    arcs_in = defaultdict(list)
    for a_id in arc_ids:
        tail, head = arc_map[a_id]
        arcs_out[tail].append(a_id)
        arcs_in[head].append(a_id)
        
    # Vincoli di Conservazione del Flusso (Equazione 2)
    for i in range(N):
        flow_in = sum(f[a_id] for a_id in arcs_in[i])
        flow_out = sum(f[a_id] for a_id in arcs_out[i])
        
        if i == s:
            model.Add(flow_in - flow_out == -z)
        elif i == t:
            model.Add(flow_in - flow_out == z)
        else:
            model.Add(flow_in - flow_out == 0)

    # Vincoli di Capacità e Attivazione Binaria (Equazione 3)
    for a_id in arc_ids:
        # f_ij <= u_ij * x_ij
        model.Add(f[a_id] <= capacity_map[a_id] * x[a_id])
        # Nota: Un vincolo implicito utile per l'attivazione:
        # Se f_ij > 0, x_ij deve essere 1.
        # Questo è già gestito implicitamente dalla disuguaglianza precedente se f_ij è positivo,
        # ma è spesso utile aggiungere una disuguaglianza che forzi x=1 se f > 0 per robustezza, 
        # ad esempio: model.Add(f[a_id] > 0).OnlyEnforceIf(x[a_id])
        # Per CP-SAT, Add(f <= u*x) è sufficiente per MILP.

    # Vincoli di Conflitto (Equazione 4)
    for a_id_1, a_id_2 in conflict_pairs:
        # x_ij + x_kl <= 1
        model.Add(x[a_id_1] + x[a_id_2] <= 1)


# ----------------------------------------------------
# 3. Funzione di Risoluzione e Output (Fase 3)
# ----------------------------------------------------
def solve_mfpc_model_phase3(model, z, f, x, arc_ids, arc_map, capacity_map):
    
    # 1. Funzione Obiettivo: Massimizzazione del Flusso Totale
    model.Maximize(z)
    
    # 2. Risoluzione
    solver = cp_model.CpSolver()
    
    # Aggiungiamo un limite di tempo opzionale per la risoluzione (es. 60 secondi)
    # solver.parameters.max_time_in_seconds = 60.0 
    
    status = solver.Solve(model)
    
    # 3. Interpretazione dei Risultati
    print("\n" + "="*50)
    print("RISULTATI FINALI")
    print("="*50)
    
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        
        # Flusso Totale
        optimal_flow = solver.ObjectiveValue()
        print(f"Stato Soluzione: {'OTTIMALE' if status == cp_model.OPTIMAL else 'AMMISSIBILE'}")
        print(f"Massimo Flusso (z): **{int(optimal_flow)}**")
        print(f"Tempo di Calcolo: {solver.WallTime():.4f} secondi")
        print("-" * 50)
        
        # Dettagli del Flusso per Arco
        print("Dettaglio del Flusso per Arco (f_ij) e Attivazione (x_ij):")
        
        results = []
        for a_id in arc_ids:
            flow_value = solver.Value(f[a_id])
            is_active = solver.Value(x[a_id])
            tail, head = arc_map[a_id]
            capacity = capacity_map[a_id]
            
            # Se l'arco è attivo o ha flusso, lo stampiamo
            if flow_value > 0 or is_active == 1:
                results.append({
                    'ID': a_id,
                    'Arco': f"({tail}->{head})",
                    'Capacità': capacity,
                    'Flusso': int(flow_value),
                    'Attivo (x)': is_active
                })

        # Stampa i risultati in una tabella (solo archi attivi o con flusso)
        print("| ID | Arco | Cap. | Flusso | Attivo (x) |")
        print("|:---|:-----|:-----|:-------|:----------|")
        for res in results:
            print(f"| {res['ID']} | {res['Arco']} | {res['Capacità']} | **{res['Flusso']}** | {res['Attivo (x)']} |")
            
        print("\nVerifica Conflitti (Attivazione):")
        conflict_violated = False
        for a_id_1, a_id_2 in conflict_pairs:
            x_val_1 = solver.Value(x[a_id_1])
            x_val_2 = solver.Value(x[a_id_2])
            if x_val_1 + x_val_2 > 1:
                print(f"❌ CONFLITTO VIOLATO tra {a_id_1} e {a_id_2}")
                conflict_violated = True
        
        if not conflict_violated:
             print("✅ Nessun vincolo di conflitto violato.")

        # L'output atteso per l'esempio della Figura 1 è z=5.
        print("\nNota: Il risultato atteso per l'istanza d'esempio (Figura 1) è z=5.")

    else:
        print(f"Stato Soluzione: {solver.StatusName(status)}")
        print("Impossibile trovare una soluzione ammissibile o ottimale.")


# Esecuzione del Modello Completo
model, z, f, x = setup_mfpc_model_phase1(N, s, t, arc_ids, arc_map, capacity_map)
add_mfpc_constraints_phase2(model, z, f, x, N, s, t, arc_ids, arc_map, capacity_map, conflict_pairs)
solve_mfpc_model_phase3(model, z, f, x, arc_ids, arc_map, capacity_map)