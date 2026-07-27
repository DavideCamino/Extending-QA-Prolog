"""
Solve a circuit-SAT instance, encoded as a QUBO/Ising problem, with a QAOA
circuit (5 levels) on a simulated backend. The circuit parameters are
optimized with COBYLA, the optimized circuit is then sampled multiple times,
and the resulting bitstring distributions are saved to file.

The circuit represents the logic formula: a AND (NOT (b OR c)).

Requires `sat.npz` (the QUBO problem in matrix form) to be present in the
working directory. See the README for how to generate it.
"""

import numpy as np
from scipy.optimize import minimize

from qiskit.quantum_info import SparsePauliOp
from qiskit.circuit.library import QAOAAnsatz
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_ibm_runtime import Session, EstimatorV2 as Estimator
from qiskit_ibm_runtime import SamplerV2 as Sampler
from qiskit_aer import AerSimulator

import qubovert

N_EXPERIMENTS = 8


def load_ising_matrix(npz_file):
    """Load the QUBO problem in matrix form and convert it to an Ising matrix."""
    data = np.load(npz_file)
    qubo_mat = data['qubo']
    n_qubits = len(data['syms'])

    qubo = qubovert.utils.matrix_to_qubo(qubo_mat)
    ising = qubovert.utils.qubo_to_quso(qubo)
    ising_dict = dict(ising)
    ising_dict.pop(())
    ising_mat = qubovert.utils.qubo_to_matrix(ising_dict)

    return ising_mat, n_qubits


def build_paulis(matrix):
    """Build the list of Pauli terms representing the cost matrix."""
    pauli_list = []
    for i in range(len(matrix)):
        pauli_list.append(('Z', [i], matrix[i][i]))
        for j in range(i + 1, len(matrix)):
            pauli_list.append(('ZZ', [i, j], matrix[i][j]))
    return pauli_list


def cost_func_estimator(params, ansatz, hamiltonian, estimator):
    """Evaluate the expectation value of the cost Hamiltonian for a given set
    of QAOA parameters."""
    # Transform the observable defined on virtual qubits to
    # an observable defined on all physical qubits.
    isa_hamiltonian = hamiltonian.apply_layout(ansatz.layout)

    pub = (ansatz, isa_hamiltonian, params)
    job = estimator.run([pub])

    results = job.result()[0]
    return results.data.evs


def run_experiment(backend, candidate_circuit, cost_hamiltonian):
    """Optimize the QAOA parameters, sample the optimized circuit, and return
    the distribution of the first 3 measured bits, sorted by bitstring."""
    init_params = np.random.rand(candidate_circuit.num_parameters) * 2 * np.pi

    with Session(backend=backend) as session:
        estimator = Estimator(mode=session)
        estimator.options.default_shots = 1000

        result = minimize(
            cost_func_estimator,
            init_params,
            args=(candidate_circuit, cost_hamiltonian, estimator),
            method='COBYLA',
            tol=1e-10,
        )

    optimized_circuit = candidate_circuit.assign_parameters(result.x)

    sampler = Sampler(mode=backend)
    sampler.options.default_shots = 10000

    pub = (optimized_circuit,)
    job = sampler.run([pub], shots=int(1e4))
    counts_bin = job.result()[0].data.meas.get_counts()
    shots = sum(counts_bin.values())
    final_distribution_bin = {key: val / shots for key, val in counts_bin.items()}

    first_3 = {}
    for key, value in final_distribution_bin.items():
        first = key[:3]
        first_3[first] = first_3.get(first, 0) + value

    return sorted(first_3.items())


def main():
    ising_mat, n_qubits = load_ising_matrix('sat.npz')

    sat_paulis = build_paulis(ising_mat)
    cost_hamiltonian = SparsePauliOp.from_sparse_list(sat_paulis, n_qubits)

    ansatz = QAOAAnsatz(cost_operator=cost_hamiltonian, reps=5)
    ansatz.measure_all()

    backend = AerSimulator()
    pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
    candidate_circuit = pm.run(ansatz)

    results = []
    for i in range(N_EXPERIMENTS):
        res = run_experiment(backend, candidate_circuit, cost_hamiltonian)
        print(res)
        results.append(res)

    with open('raw_data.tsv', 'w') as out:
        for val in results[0]:
            out.write(val[0] + '\t')
        out.write('\n')
        for r in results:
            for val in r:
                out.write(str(val[1]) + '\t')
            out.write('\n')


if __name__ == "__main__":
    main()