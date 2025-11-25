import os
import csv
import time
from ortools.sat.python import cp_model


# ==========================================================
# 1) PARSER DELLE ISTANZE (formato dei tuoi file)
# ==========================================================
def parse_mfpc_instance(path):
    with open(path, "r") as f:
        lines = [line.strip() for line in f if line.strip()]

    # Riga 1: n_nodes, n_arcs, n_conflicts
    n_nodes, n_arcs, n_conflicts = map(int, lines[0].split())

    # Riga 2: sorgente
    source = int(lines[1])

    # Riga 3: sink
    sink = int(lines[2])

    arcs = {}
    index_to_arc = {}
    conflict_index_pairs = []

    # Dalla quarta riga in poi: archi
    for row in lines[3:]:
        parts = list(map(int, row.split()))

        tail = parts[0]
        head = parts[1]
        cap = parts[2]
        idx = parts[3]

        arcs[(tail, head)] = cap
        index_to_arc[idx] = (tail, head)

        # eventuali conflitti
        for conflict_idx in parts[4:]:
            conflict_index_pairs.append((idx, conflict_idx))

    # convertiamo indici → coppie di archi reali
    conflicts = []
    seen = set()

    for a, b in conflict_index_pairs:
        if (b, a) in seen:
            continue
        if a in index_to_arc and b in index_to_arc:
            conflicts.append((index_to_arc[a], index_to_arc[b]))
            seen.add((a, b))

    nodes = list(range(n_nodes))

    return nodes, arcs, conflicts, source, sink



# ==========================================================
# 2) RISOLUTORE CP-SAT PER MFPC (modello del paper)
# ==========================================================
def solve_mfpc(nodes, arcs, conflicts, source, sink, time_limit=3600):
    model = cp_model.CpModel()

    # variabili
    f = {}
    x = {}
    for (i, j), u in arcs.items():
        f[i, j] = model.NewIntVar(0, u, f"f_{i}_{j}")
        x[i, j] = model.NewBoolVar(f"x_{i}_{j}")
        model.Add(f[i, j] <= u * x[i, j])   # vincolo (3)

    # flusso totale
    z = model.NewIntVar(0, sum(arcs.values()), "z")

    # conservazione del flusso
    for i in nodes:
        inflow = sum(f[j, i] for (j, k) in arcs if k == i)
        outflow = sum(f[i, j] for (k, j) in arcs if k == i)

        if i == source:
            model.Add(inflow - outflow == -z)
        elif i == sink:
            model.Add(inflow - outflow == z)
        else:
            model.Add(inflow - outflow == 0)

    # conflitti
    for (a1, a2) in conflicts:
        i, j = a1
        k, l = a2
        model.Add(x[i, j] + x[k, l] <= 1)

    # obiettivo
    model.Maximize(z)

    # solver
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit

    start = time.time()
    status = solver.Solve(model)
    t_elapsed = time.time() - start

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        flows = {(i, j): solver.Value(f[i, j]) for (i, j) in arcs}
        active = {(i, j): solver.Value(x[i, j]) for (i, j) in arcs}
        return solver.Value(z), flows, active, status, t_elapsed

    return None, None, None, status, t_elapsed



# ==========================================================
# 3) LANCIARE TUTTE LE ISTANZE E SALVARE CSV
# ==========================================================
def solve_all_instances(folder_path="Istances", csv_output="risultati_miei.csv"):
    header = [
        "filename",
        "num_nodes",
        "num_arcs",
        "num_conflicts",
        "source",
        "sink",
        "max_flow_z",
        "status",
        "solve_time_sec"
    ]

    rows = []

    print("\n============================================")
    print(" AVVIO RISOLUZIONE DI TUTTE LE ISTANZE")
    print("============================================\n")

    for fname in sorted(os.listdir(folder_path)):
        if not fname.endswith(".txt"):
            continue

        full_path = os.path.join(folder_path, fname)
        print(f" → Risolvo: {fname}")

        nodes, arcs, conflicts, source, sink = parse_mfpc_instance(full_path)
        z, flows, active, status, t = solve_mfpc(nodes, arcs, conflicts, source, sink)

        stato = {
            cp_model.OPTIMAL: "OTTIMALE",
            cp_model.FEASIBLE: "FATTIBILE",
            cp_model.INFEASIBLE: "NON FATTIBILE",
            cp_model.UNKNOWN: "SCONOSCIUTO"
        }.get(status, "SCONOSCIUTO")

        rows.append([
            fname,
            len(nodes),
            len(arcs),
            len(conflicts),
            source,
            sink,
            z,
            stato,
            round(t, 4)
        ])

    # salva CSV
    with open(csv_output, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)

    print(f"\n============================================")
    print(f" FINE! Risultati salvati in: {csv_output}")
    print("============================================\n")



# ==========================================================
# 4) ESECUZIONE (puoi lasciarla così)
# ==========================================================
if __name__ == "__main__":
    solve_all_instances("Instances", "risultati_miei.csv")
