# dataset_builder.py

import csv
import os
from collections import defaultdict, deque
from solver import MaxFlowConflictSolver
from parser import read_instance
from ortools.sat.python import cp_model


def compute_node_degrees(edges, num_nodes):
    out_deg = [0] * num_nodes
    in_deg = [0] * num_nodes

    for tail, head, _, _ in edges:
        out_deg[tail] += 1
        in_deg[head] += 1

    return out_deg, in_deg


def bfs_distances(num_nodes, adjacency, start):
    """Generic BFS distance calculator."""
    dist = [-1] * num_nodes
    dist[start] = 0
    queue = deque([start])

    while queue:
        u = queue.popleft()
        for v in adjacency[u]:
            if dist[v] == -1:
                dist[v] = dist[u] + 1
                queue.append(v)
    return dist


def compute_distances(num_nodes, edges, s, d):
    """Compute dist_from_source and dist_to_sink correctly."""

    # Forward adjacency for S → nodes
    adj_fwd = defaultdict(list)
    # Reverse adjacency for nodes → D
    adj_rev = defaultdict(list)

    for tail, head, _, _ in edges:
        adj_fwd[tail].append(head)
        adj_rev[head].append(tail)

    dist_from_s = bfs_distances(num_nodes, adj_fwd, s)
    dist_to_d = bfs_distances(num_nodes, adj_rev, d)

    return dist_from_s, dist_to_d


def build_dataset_for_instance(instance_path, solver_time_limit=10):
    inst = read_instance(instance_path)

    num_nodes = inst["num_nodes"]
    s_orig = inst["s"]
    d_orig = inst["d"]
    edges_orig = inst["edges"]
    conflicts = inst["conflicts"]

    # === CORREZIONE: CONVERSIONE NODI A 0-BASED ===
    # I nodi (tail, head, s, d) sono usati come indici per liste di lunghezza num_nodes.
    s = s_orig - 1
    d = d_orig - 1
    
    edges = []
    for tail, head, capacity, arc_index in edges_orig:
        edges.append((tail - 1, head - 1, capacity, arc_index))
    # ============================================

    # === 1) Features strutturali ===
    # Le funzioni usano ora i nodi (0-based) come indici validi [0, num_nodes-1]
    out_deg, in_deg = compute_node_degrees(edges, num_nodes)
    dist_from_s, dist_to_d = compute_distances(num_nodes, edges, s, d)

    # === 2) Risolvi l’istanza ===
    # NOTA: Il solver e il parser devono essere compatibili.
    # Assicurati che MaxFlowConflictSolver e il parser gestiscano l'indicizzazione 
    # dei nodi in modo coerente (o li trasformino internamente).
    solver = MaxFlowConflictSolver(time_limit=solver_time_limit, log=False)
    # Se il solver richiede dati 1-based, dovrai passargli gli originali. 
    # Ma se i dati passati al solver sono usati per indici 0-based (come faresti con OR-Tools),
    # allora devi trasformare anche 'inst' in modo coerente prima di passarlo al solver.
    # Poiché non vediamo il codice del solver, assumiamo per ora che gli archi originali
    # non siano usati come indici di liste in MaxFlowConflictSolver.
    result = solver.solve(inst) 

    if result["status"] not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return []

    flow = result["flow"]

    # Conta conflitti per arco
    conflict_count = defaultdict(int)
    for a, b in conflicts:
        conflict_count[a] += 1
        conflict_count[b] += 1

    rows = []

    # === 3) Crea riga per ogni arco ===
    for tail_0based, head_0based, capacity, arc_index in edges:
        rows.append({
            "arc_index": arc_index,
            # Salviamo i nodi nel dataset come 1-based (per coerenza con l'istanza)
            "tail": tail_0based + 1, 
            "head": head_0based + 1,
            "capacity": capacity,
            # Usiamo gli indici 0-based per accedere alle liste
            "out_deg_tail": out_deg[tail_0based],
            "in_deg_head": in_deg[head_0based],
            "dist_from_source": dist_from_s[tail_0based],
            "dist_to_sink": dist_to_d[head_0based],
            "num_conflicts": conflict_count[arc_index],

            # Label supervisata
            "label": 1 if flow[arc_index] > 0 else 0
        })

    return rows


def build_dataset(instance_folder, output_csv, solver_time_limit=10):
    all_rows = []

    for fname in sorted(os.listdir(instance_folder)):
        if not fname.endswith(".txt"):
            continue

        full = os.path.join(instance_folder, fname)
        print("Processo", fname)
        rows = build_dataset_for_instance(full, solver_time_limit=solver_time_limit)
        all_rows.extend(rows)

    if not all_rows:
        print("Nessun dato generato.")
        return

    keys = list(all_rows[0].keys())
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)

    with open(output_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(all_rows)

    print("Dataset generato in:", output_csv)

if __name__ == "__main__":
    base = os.path.dirname(os.path.abspath(__file__))
    instances_folder = os.path.join(base, "..", "data", "Instances")

    output_csv = os.path.join(base, "dataset", "dataset.csv")

    build_dataset(instances_folder, output_csv, solver_time_limit=10)
