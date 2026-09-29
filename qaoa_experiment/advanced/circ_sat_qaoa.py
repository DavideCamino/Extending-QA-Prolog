"""
Automate the generation of a circuit-SAT QUBO problem from a Verilog source,
convert it to Ising form, and run a batch of QAOA experiments (5-layer
ansatz, COBYLA optimizer, restarted `RESTARTING` times per run) on a
simulated backend, saving the resulting bitstring distributions to file.

Requires `util.py` (providing `load_qubo`, `convert_to_ising`, `build_paulis`
and `run_experiment`) to be present in the working directory.
"""

import os
import subprocess

from qiskit.quantum_info import SparsePauliOp
from qiskit.circuit.library import QAOAAnsatz
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_aer import AerSimulator

import qubovert

from util import *

RESTARTING = 15
BATCH = 30


def gen_qubo(verilog_source):
    """Run the Verilog-to-QUBO translation pipeline and generate `sat.npz`."""
    try:
        path = os.getcwd()
        subprocess.run(
            ['yosys', verilog_source, 'work/synth.ys', '-b', 'edif', '-o', 'work/circ_sat.edif'],
            capture_output=True,
        )
        subprocess.run(['edif2qmasm', '-o', 'work/circ_sat.qmasm', 'work/circ_sat.edif'])
        os.chdir('work')
        subprocess.run(
            ['qmasm', '--format', 'numpy', '-o', '../sat.npz', '--solver', 'tabu',
             '--pin', 'circ_sat.y := true', 'circ_sat.qmasm']
        )
        os.chdir(path)
        return 0
    except Exception:
        return 1


def gen_ising(qubo_mat):
    """Convert the QUBO matrix to Ising form and compute its ground-state energy."""
    ising_dict, ising_mat = convert_to_ising(qubo_mat)
    ising_solution = qubovert.QUSO(ising_dict).solve_bruteforce()
    ising_energy = qubovert.QUSO(ising_dict).value(ising_solution)
    return ising_mat, ising_energy


def initialize_tsv(file):
    """Write the header row (all 3-bit strings) to the results file."""
    columns = ["000", "001", "010", "011", "100", "101", "110", "111"]
    with open(file, 'w') as out:
        out.write('\t'.join(columns) + '\n')


def write_tsv(res, file):
    """Append one row of frequencies to the results file."""
    with open(file, 'a') as out:
        out.write('\t'.join(str(freq[1]) for freq in res) + '\n')
    return 0


def run_experiments(ansatz, backend, candidate_circuit, cost_hamiltonian, restarting, opt_method, file_tsv):
    """Run `BATCH` independent experiments and append each result to `file_tsv`."""
    for i in range(BATCH):
        energy, n_eval, res, run_time = run_experiment(
            ansatz, backend, candidate_circuit, cost_hamiltonian, restarting, opt_method
        )
        print(opt_method, i, run_time, sep='\t')
        write_tsv(res, file_tsv)


def main():
    error = gen_qubo('circ_sat.v')
    data, qubo_mat, n_qubits = load_qubo('sat.npz')
    ising_mat, ising_energy = gen_ising(qubo_mat)

    cost_hamiltonian = SparsePauliOp.from_sparse_list(build_paulis(ising_mat), n_qubits)
    ansatz = QAOAAnsatz(cost_operator=cost_hamiltonian, reps=5)
    ansatz.measure_all()

    backend = AerSimulator()
    pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
    candidate_circuit = pm.run(ansatz)

    initialize_tsv('raw_data.tsv')
    run_experiments(ansatz, backend, candidate_circuit, cost_hamiltonian, RESTARTING, 'COBYLA', 'raw_data.tsv')
    return 0


if __name__ == "__main__":
    main()