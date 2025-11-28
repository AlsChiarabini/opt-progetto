from ortools.sat.python import cp_model
import os

def read_instance(file_path):

    with open(file_path, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]

    # Prime tre righe
    num_nodes, num_arcs, num_conflicts = map(int, lines[0].split())
    s = int(lines[1])
    d = int(lines[2])

    edges = []
    conflicts = []

    # Righe degli archi
    for line in lines[3:]:
        parts = list(map(int, line.split()))
        tail = parts[0]
        head = parts[1]
        capacity = parts[2]
        arc_index = parts[3]

        edges.append((tail, head, capacity, arc_index))

        # Se ci sono conflitti
        if len(parts) > 4:
            for conflict_index in parts[4:]:
                conflicts.append((arc_index, conflict_index))

        #debug (stampo info primo arco)   (lines[3] --> primo arco)
        debug = True
        if debug:
            if True:   # line == lines[3]
                print(f"Arco: {tail} --> {head} , cap: {capacity} , arc_index {arc_index}")
                print(f"Conflitti con: {parts[4:]}")
                print("\n")

    n = 1
    for _, _, _, idx in edges: 
        if idx == n:
            n+=1
        else:
            print("ERRORE")
    print("TUTTO OK")

    return num_nodes, s, d, edges, conflicts

def max_flow_with_conflicts_instance(num_nodes, s, d, edges, conflicts):
    """
    num_nodes: numero di nodi
    s: sorgente
    d: pozzo
    edges: lista di tuple (tail, head, capacity, arc_index)
    conflicts: lista di coppie di arc_index in conflitto  (i,j) ==> i conflitto con j
    """
    model = cp_model.CpModel()

    # Variabili di flusso per ogni arco, indicizzate per arc_index
    flow = {}
    active = {}
    for tail, head, capacity, arc_index in edges:
        flow[arc_index] = model.NewIntVar(0, capacity, f'flow_{arc_index}')
        active[arc_index] = model.NewBoolVar(f'active_{arc_index}')
        # Se flusso > 0 allora attivo
        model.Add(flow[arc_index] > 0).OnlyEnforceIf(active[arc_index])     #fij > 0 (if attivo)
        model.Add(flow[arc_index] == 0).OnlyEnforceIf(active[arc_index].Not())  #duale

    # Conflitti tra archi
    for arc1, arc2 in conflicts:
        model.AddBoolOr([active[arc1].Not(), active[arc2].Not()])       #almeno uno non attivo

    # Conservazione del flusso
    for node in range(num_nodes):
        if node == s or node == d:
            continue
        inflow = sum(flow[arc_index] for tail, head, _, arc_index in edges if head == node)
        outflow = sum(flow[arc_index] for tail, head, _, arc_index in edges if tail == node)
        model.Add(inflow == outflow)

    # Obiettivo: massimizzare il flusso uscente dalla sorgente
    total_out = sum(flow[arc_index] for tail, head, _, arc_index in edges if tail == s)
    model.Maximize(total_out)

    # Risoluzione
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        print(f"Flusso massimo: {solver.ObjectiveValue()}")
        for tail, head, _, arc_index in edges:
            if solver.Value(flow[arc_index]) > 0:
                print(f"{tail} -> {head} (arco {arc_index}): {solver.Value(flow[arc_index])}")
    else:
        print("Nessuna soluzione trovata.")



script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, "Instances", "40_50_30_10_15.txt")  #"40_30_30_10_15.txt"
num_nodes, s, d, edges, conflicts = read_instance(file_path)


max_flow_with_conflicts_instance(num_nodes, s, d, edges, conflicts)