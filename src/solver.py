# solver.py

from ortools.sat.python import cp_model


class MaxFlowConflictSolver:
    def __init__(self, time_limit=None, max_seconds=None, log=False):
        """
        time_limit: alias OR-Tools per limite di tempo in secondi
        log: se True stampa log dettagliati
        """
        self.time_limit = time_limit or max_seconds
        self.log = log

    def solve(self, instance, warm_start=None):
        """
        instance è un dict con:
            num_nodes, s, d, edges, conflicts
        warm_start (opzionale): dict {arc_index: flow_value}
        """
        num_nodes = instance["num_nodes"]
        s = instance["s"]
        d = instance["d"]
        edges = instance["edges"]
        conflicts = instance["conflicts"]

        model = cp_model.CpModel()

        # ---------------------
        # Variabili
        # ---------------------
        flow = {}
        active = {}

        for tail, head, capacity, arc_index in edges:
            flow[arc_index] = model.NewIntVar(0, capacity, f"flow_{arc_index}")
            active[arc_index] = model.NewBoolVar(f"active_{arc_index}")

            # collegamento tra flow e active
            model.Add(flow[arc_index] > 0).OnlyEnforceIf(active[arc_index])
            model.Add(flow[arc_index] == 0).OnlyEnforceIf(active[arc_index].Not())

        # ---------------------
        # Vincoli di conflitto
        # ---------------------
        for arc1, arc2 in conflicts:
            model.AddBoolOr([active[arc1].Not(), active[arc2].Not()])

        # ---------------------
        # Conservazione del flusso
        # ---------------------
        for node in range(num_nodes):
            if node == s or node == d:
                continue

            inflow = sum(flow[i] for (tail, head, _, i) in edges if head == node)
            outflow = sum(flow[i] for (tail, head, _, i) in edges if tail == node)

            model.Add(inflow == outflow)

        # ---------------------
        # Obiettivo
        # ---------------------
        total_outflow = sum(flow[i] for (tail, head, _, i) in edges if tail == s)
        model.Maximize(total_outflow)

        # ---------------------
        # Solver
        # ---------------------
        solver = cp_model.CpSolver()
        if self.time_limit:
            solver.parameters.max_time_in_seconds = self.time_limit
        if not self.log:
            solver.parameters.log_search_progress = False

        # Warm start (solo placeholder – ML verrà aggiunto nel modulo 4)
        if warm_start:
            var_list, val_list = [], []
            for arc_index, value in warm_start.items():
                if arc_index in flow:
                    var_list.append(flow[arc_index])
                    val_list.append(value)
            if var_list:
                solver.SetHint(var_list, val_list)

        # Risoluzione
        status = solver.Solve(model)

        # ---------------------
        # Output strutturato
        # ---------------------

        STATUS_LABELS = {
            cp_model.OPTIMAL: "OPTIMAL",
            cp_model.FEASIBLE: "FEASIBLE",
            cp_model.INFEASIBLE: "INFEASIBLE",
            cp_model.UNKNOWN: "UNKNOWN",
        }

        result = {
            "status": STATUS_LABELS[status],
            "objective": solver.ObjectiveValue() if status in (cp_model.OPTIMAL, cp_model.FEASIBLE) else None,
            "flow": {i: solver.Value(flow[i]) for i in flow} if status in (cp_model.OPTIMAL, cp_model.FEASIBLE) else None,
            "active": {i: solver.Value(active[i]) for i in active} if status in (cp_model.OPTIMAL, cp_model.FEASIBLE) else None,
            "solve_time": solver.WallTime(),
            "gap": solver.BestObjectiveBound(),
        }

        return result

