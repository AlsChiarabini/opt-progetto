from src.parser import read_instance
from src.solver import MaxFlowConflictSolver
import os

if __name__ == "__main__":
    file_path = "data/Instances/40_30_30_10_15.txt"
    instance = read_instance(file_path)

    solver = MaxFlowConflictSolver(time_limit=30, log=True)
    result = solver.solve(instance)

    print("\n--- RISULTATO ---")
    print("Status:", result["status"])
    print("Opt:", result["objective"])
    print("Tempo:", result["solve_time"], "s")
