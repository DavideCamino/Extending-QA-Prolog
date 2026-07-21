"""
Run the QA-Prolog -> QMASM pipeline for a set of realistic queries and
measure the number of qubits (dimension of the QUBO problem) required
to represent each one.

Equivalent to: run_experiment.ipynb
"""

import time
import subprocess
from pathlib import Path

import numpy as np

# Path to the QA-Prolog compatible ontology
FILE = '../knowledge_bases/Animal_QA_Prolog_compatible.pl'

# Queries to evaluate
QUERY_LIST = [
    "class(animal).",
    "class(X).",
    "subClass(seal, X).",
    "isA(reiny, X).",
    "isA(sardy, X).",
    "isA(Y, X).",
    "error(X, Y, Z).",
    "hasProperty(I1, ancestor, reiny_c).",
]

# Commands to run the pipeline and generate a matrix representation of the QUBO problem
COMMAND_QAP = 'QA-Prolog --qmasm-args="--stop" --work-dir="' + str(Path.cwd()) + '/work"'
COMMAND_QMASM = ('qmasm --format="numpy" -o="out.npz" --pin="Query.Valid := true" '
                  '--solver="tabu" ' + str(Path.cwd()) + '/work/Animal_QA_Prolog_compatible.qmasm')


def experiment(query):
    """Run the pipeline for a single query and return the number of qubits
    used to represent the resulting QUBO problem."""
    command = COMMAND_QAP + ' --query="' + query + '" ' + FILE
    subprocess.run(command, shell=True, capture_output=True, text=True)
    subprocess.run(COMMAND_QMASM, shell=True)
    data = np.load("out.npz")
    return len(data["syms"])


def main():
    n_qubits = []
    for i, query in enumerate(QUERY_LIST):
        print(f"query {i + 1}/{len(QUERY_LIST)}: {query} ...", end="")
        start = time.time()
        n_qubits.append(experiment(query))
        stop = time.time()
        print(f"ok ({int(stop - start)} sec)")

    with open('raw_data.tsv', 'w') as out:
        out.write('query\tn_qubits\n')
        for i, query in enumerate(QUERY_LIST):
            print(query, n_qubits[i])
            out.write(f"{query}\t{n_qubits[i]}\n")


if __name__ == "__main__":
    main()