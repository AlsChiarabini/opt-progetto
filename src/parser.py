# parser.py

def read_instance(file_path):
    """
    Legge un'istanza del problema MFMC.
    Formato:
        num_nodes num_arcs num_conflicts
        s
        d
        tail head capacity arc_index [conflicts...]
    """
    edges = []
    conflicts = []

    with open(file_path, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]

    num_nodes, num_arcs, num_conflicts = map(int, lines[0].split())
    s = int(lines[1])
    d = int(lines[2])

    for line in lines[3:]:
        parts = list(map(int, line.split()))
        tail, head, capacity, arc_index = parts[:4]
        conflict_list = parts[4:]

        edges.append((tail, head, capacity, arc_index))

        for c in conflict_list:
            conflicts.append((arc_index, c))

    return {
        "num_nodes": num_nodes,
        "s": s,
        "d": d,
        "edges": edges,
        "conflicts": conflicts
    }

