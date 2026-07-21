"""
Run the QA-Prolog -> QMASM pipeline on a knowledge base with an increasing
number of unfolded recursive calls, and measure how the dimension of the
resulting QUBO problem (number of qubits) scales with the number of
unfolded calls.

Equivalent to: run_experiment.ipynb
"""

import time
import subprocess
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

# Command to build the QUBO problem and retrieve its dimension
COMMAND_QMASM = ('qmasm --format="numpy" -o="out.npz" --pin="Query.Valid := true" '
                  '--solver="tabu" ' + str(Path.cwd()) + '/work/animal_unfold.qmasm')
COMMAND_QAP = 'QA-Prolog --qmasm-args="--stop" --work-dir="' + str(Path.cwd()) + '/work"'

# Query used for every run
QUERY = 'subClass(mammal, animal).'


def read_file(file_name):
    """Read a text file and return its lines."""
    with open(file_name, 'r') as file_in:
        return file_in.readlines()


def write_unfold_calls(file_out, n_unfold):
    """Write the unfolded recursive `subClass` calls to the given file handle."""
    file_out.write('subClass0(C0,C1) :- \n\tsubclass(C0, C1).\n')
    for i in range(1, n_unfold):
        rule = ('subClass' + str(i) + '(C0,C2) :-\n' +
                '\tsubClass' + str(i - 1) + '(C0,C3),\n' +
                '\tsubclass(C3, C2).\n')
        file_out.write(rule)
    for i in range(n_unfold):
        file_out.write('subClass(C0,C1) :- subClass' + str(i) + '(C0, C1).\n')


def write_file(file_name_in, file_name_out, n_unfold):
    """Generate a new knowledge base from `file_name_in`, appending `n_unfold`
    unfolded recursive calls, and save it to `file_name_out`."""
    t_box = read_file(file_name_in)
    with open(file_name_out, 'w') as file_out:
        file_out.writelines(t_box)
        file_out.write('\n\n')
        write_unfold_calls(file_out, n_unfold)


def experiment(file_name_in, file_name_out, n_calls):
    """Generate a new knowledge base with `n_calls` unfolded classes and
    return the resulting QUBO dimension."""
    write_file(file_name_in, file_name_out, n_calls)
    command = COMMAND_QAP + ' --query="' + QUERY + '" ' + file_name_out
    subprocess.run(command, shell=True, capture_output=True, text=True)
    subprocess.run(COMMAND_QMASM, shell=True)
    data = np.load("out.npz")
    return len(data["syms"])


def run_experiments(file_name_in, file_name_out, n_unfold_max):
    """Run the experiment for an increasing number of unfolded calls, from
    2 up to `n_unfold_max`, and return the list of resulting QUBO dimensions."""
    n_qubits = []
    for i in range(2, n_unfold_max + 1):
        print(f"unfolded calls {i}/{n_unfold_max} ...", end="")
        start = time.time()
        n_qubits.append(experiment(file_name_in, file_name_out, i))
        stop = time.time()
        print(f"ok ({int(stop - start)} sec)")
    return n_qubits


def main():
    n_qubits = run_experiments('animal.pl', 'animal_unfold.pl', 20)

    with open('raw_data.tsv', 'w') as out:
        out.write('unfolded_calls\tn_qubits\n')
        for i, qubits in enumerate(n_qubits):
            print(i + 2, qubits)
            out.write(f"{i + 2}\t{qubits}\n")

if __name__ == "__main__":
    main()