import os
import csv
import time
# Importiamo CpSolverStatus per la correzione dell'errore
from ortools.sat.python import cp_model, cp_solver_pb2 

# ==========================================================
# 1) PARSER DELLE ISTANZE (identico al primo codice)
# ==========================================================
def parse_mfpc_instance(path):
    with open(path, "r") as f:
        lines = [line.strip() for line in f if line.strip()]

    if not lines:
        raise ValueError(f"File vuoto o non formattato correttamente: {path}")
        
    n_nodes, n_arcs, n_conflicts = map(int, lines[0].split())
    source = int(lines[1])
    sink = int(lines[2])

    arcs = {}
    index_to_arc = {}
    conflict_index_pairs = []

    for row in lines[3:]:
        parts = list(map(int, row.split()))
        tail = parts[0]
        head = parts[1]
        cap = parts[2]
        idx = parts[3]

        arcs[(tail, head)] = cap
        index_to_arc[idx] = (tail, head)

        for conflict_idx in parts[4:]:
            conflict_index_pairs.append((idx, conflict_idx))

    conflicts = []
    seen = set()

    for a, b in conflict_index_pairs:
        # Evitiamo doppioni (a, b) e (b, a)
        if (b, a) in seen:
            continue
        if a in index_to_arc and b in index_to_arc:
            conflicts.append((index_to_arc[a], index_to_arc[b]))
            seen.add((a, b))

    nodes = list(range(n_nodes))

    return nodes, arcs, conflicts, source, sink


# ==========================================================
# 2) RISOLUTORE CP-SAT PER MFPC (modello corretto)
# ==========================================================
def solve_mfpc(nodes, arcs, conflicts, source, sink, time_limit=3600):
    model = cp_model.CpModel()

    f = {} # Variabile di flusso (IntVar)
    x = {} # Variabile di selezione (BoolVar)
    
    for (i, j), u in arcs.items():
        f[i, j] = model.NewIntVar(0, u, f"f_{i}_{j}")
        x[i, j] = model.NewBoolVar(f"x_{i}_{j}")
        
        # 1. Implicazione: Se x=0, allora f=0. (f <= u * x)
        model.Add(f[i, j] <= u * x[i, j])
        
        # 2. Implicazione: Se f>0 (f>=1), allora x=1. (f >= 1 * x)
        model.Add(f[i, j] >= x[i, j]) 
        # Risultato: x = 1 SE E SOLO SE f > 0

    z = model.NewIntVar(0, sum(arcs.values()), "z")

    # Conservazione del flusso
    for i in nodes:
        inflow = sum(f[j, i] for (j, k) in arcs if k == i)
        outflow = sum(f[i, j] for (k, j) in arcs if k == i)

        if i == source:
            model.Add(outflow - inflow == z)
        elif i == sink:
            model.Add(inflow - outflow == z)
        else:
            model.Add(inflow == outflow)

    # Vincoli di conflitto: al massimo uno tra x_a e x_b può essere 1
    for (a1, a2) in conflicts:
        i, j = a1
        k, l = a2
        model.Add(x[i, j] + x[k, l] <= 1)

    # Obiettivo
    model.Maximize(z)

    # Solver
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit

    start = time.time()
    status = solver.Solve(model)
    t_elapsed = time.time() - start

    # Gestione output
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        max_flow_z = solver.Value(z)
        
        print(f"\nFlusso massimo: {max_flow_z}")
        print("Archi attivi e flussi:")
        for (i, j) in arcs:
             flow_val = solver.Value(f[i, j])
             if flow_val > 0:
                 print(f"  {i} -> {j}: {flow_val}")

        return max_flow_z, status, t_elapsed

    return None, status, t_elapsed


# ==========================================================
# 3) ESECUZIONE SU SINGOLA ISTANZA
# ==========================================================
if __name__ == "__main__":
    
    # ⚠️ IMPOSTA QUI IL PATH DEL TUO FILE DI TEST
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_name = "40_30_40_15_20.txt"
    folder_path = "Instances" 
    full_path = os.path.join(script_dir, folder_path, file_name) 

    print(f"--- AVVIO RISOLUZIONE ISTANZA: {file_name} ---")
    
    try:
        nodes, arcs, conflicts, source, sink = parse_mfpc_instance(full_path)
        
        print(f"Dati istanza: Nodi={len(nodes)}, Archi={len(arcs)}, Conflitti={len(conflicts)}")
        print(f"Sorgente={source}, Pozzo={sink}")
        
        z_opt, status, t_elapsed = solve_mfpc(nodes, arcs, conflicts, source, sink, time_limit=60)
        
        # ⛔️ CORREZIONE ERRORE: Usiamo cp_model.CpSolverStatus (o solver.StatusName)
        stato_nome = cp_model.CpSolverStatus.Name(status)

        print("\n--- RISULTATO FINALE ---")
        print(f"Stato: **{stato_nome}**")
        print(f"Flusso Massimo (Z): **{z_opt}**")
        print(f"Tempo di risoluzione: {round(t_elapsed, 4)} sec")
        print("------------------------")

    except FileNotFoundError:
        print(f"\nERRORE: File non trovato al percorso: {full_path}")
        print("Controlla che il nome del file e il percorso della cartella siano corretti.")
    except Exception as e:
        # Stampa l'errore per il debug
        print(f"\nERRORE generale durante l'esecuzione: {e}")