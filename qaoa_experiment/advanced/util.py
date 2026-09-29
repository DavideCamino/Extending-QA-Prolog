"""
qaoa_utils.py
=============
Utilities for solving QUBO problems with QAOA on Qiskit / IBM Runtime.

Typical workflow
----------------
    data, qubo_mat, n_qubits = load_qubo("problem.npz")
    ising_dict, ising_mat    = convert_to_ising(qubo_mat)
    pauli_list               = build_paulis(ising_mat)
    hamiltonian              = SparsePauliOp.from_sparse_list(pauli_list, num_qubits=n_qubits)
    # ... build ansatz + transpile -> candidate_circuit ...
    energy, n_eval, relevant, runtime = run_experiment(
        ansatz, backend, candidate_circuit, hamiltonian,
        n_restarting=15, opt_method="COBYLA",
    )
    plot_experiments([relevant], titles=["run 1"], highlight_keys=["010"])
"""

import time

import numpy as np
import matplotlib.pyplot as plt
import qubovert
from scipy.optimize import minimize
from qiskit_ibm_runtime import Session, EstimatorV2 as Estimator, SamplerV2 as Sampler


# ---------------------------------------------------------------------------
# Problem loading / conversion
# ---------------------------------------------------------------------------

def load_qubo(file):
    """Load a QUBO problem from an .npz file.

    The file must contain a 'qubo' matrix and a 'syms' array (variable names).

    Returns
    -------
    data : NpzFile   -- the raw loaded archive
    qubo_mat : ndarray -- the QUBO matrix
    n_qubits : int   -- number of variables (= qubits)
    """
    data = np.load(file)
    qubo_mat = data["qubo"]
    n_qubits = len(data["syms"])
    return data, qubo_mat, n_qubits


def convert_to_ising(qubo_mat):
    """Convert a QUBO matrix to its Ising (spin) formulation.

    Returns
    -------
    ising_dict : dict   -- Ising coefficients, constant offset removed
    ising_mat  : ndarray -- the same coefficients as a matrix
    """
    qubo = qubovert.utils.matrix_to_qubo(qubo_mat)
    ising = qubovert.utils.qubo_to_quso(qubo)

    ising_dict = dict(ising)
    # The constant term () only shifts the energy; it doesn't affect the
    # optimum, so we drop it (pop it here if you need it: offset = ...).
    ising_dict.pop((), None)

    ising_mat = qubovert.utils.qubo_to_matrix(ising_dict)
    return ising_dict, ising_mat


def build_paulis(matrix):
    """Build a sparse Pauli list from an Ising matrix.

    Diagonal entries become single-qubit Z terms, upper-triangular entries
    become two-qubit ZZ terms. The result can be passed to
    ``SparsePauliOp.from_sparse_list(pauli_list, num_qubits=n)``.

    Returns
    -------
    list of (label, [qubit indices], coefficient)
    """
    n = len(matrix)
    pauli_list = []
    for i in range(n):
        pauli_list.append(("Z", [i], matrix[i][i]))
        for j in range(i + 1, n):
            pauli_list.append(("ZZ", [i, j], matrix[i][j]))
    return pauli_list


# ---------------------------------------------------------------------------
# QAOA optimization
# ---------------------------------------------------------------------------

def cost_func_estimator(params, ansatz, hamiltonian, estimator):
    """Cost function for the classical optimizer: <psi(params)|H|psi(params)>.

    `ansatz` must be an already-transpiled circuit (it carries `.layout`).
    """
    # Map the observable from virtual qubits onto the physical qubits.
    isa_hamiltonian = hamiltonian.apply_layout(ansatz.layout)

    job = estimator.run([(ansatz, isa_hamiltonian, params)])
    return job.result()[0].data.evs


def optimize(ansatz, backend, candidate_circuit, hamiltonian, opt_method, shots=1000):
    """Run one optimization of the QAOA parameters from a random start.

    Parameters
    ----------
    ansatz : the untranspiled ansatz (used only for the parameter count)
    candidate_circuit : the transpiled ansatz that is actually executed
    shots : Estimator shots per evaluation

    Returns
    -------
    scipy.optimize.OptimizeResult
    """
    init_params = np.random.rand(ansatz.num_parameters) * 2 * np.pi

    with Session(backend=backend) as session:
        estimator = Estimator(mode=session)
        estimator.options.default_shots = shots

        return minimize(
            cost_func_estimator,
            init_params,
            args=(candidate_circuit, hamiltonian, estimator),
            method=opt_method,
        )


def optimization_cycle(ansatz, backend, candidate_circuit, hamiltonian,
                       opt_method, n_cycle=15):
    """Repeat `optimize` from random starts and keep the lowest-energy result.

    Returns
    -------
    min_energy : float
    best_parameters : ndarray
    n_eval : int -- function evaluations used by the best run
    """
    results = [
        optimize(ansatz, backend, candidate_circuit, hamiltonian, opt_method)
        for _ in range(n_cycle)
    ]
    # Compare on energy only (comparing tuples would break on ties, since
    # numpy arrays have no unambiguous ordering).
    best = min(results, key=lambda r: r.fun)
    return best.fun, best.x, best.nfev


# ---------------------------------------------------------------------------
# Sampling / post-processing
# ---------------------------------------------------------------------------

def sample(backend, optimized_circuit, shots=10_000):
    """Sample the optimized circuit and return normalized bitstring frequencies.

    Returns
    -------
    dict {bitstring: probability}
    """
    sampler = Sampler(mode=backend)

    job = sampler.run([(optimized_circuit,)], shots=shots)
    counts = job.result()[0].data.meas.get_counts()

    total = sum(counts.values())
    return {bits: n / total for bits, n in counts.items()}


def select_relevant_bit(distribution_bin, n_bits=3):
    """Marginalize a distribution onto the first `n_bits` characters of each key.

    Note: Qiskit bitstrings are little-endian (qubit 0 is the rightmost
    character), so the leading characters are the highest-index qubits.

    Returns
    -------
    list of (prefix, probability), sorted by prefix
    """
    marginal = {}
    for key, prob in distribution_bin.items():
        prefix = key[:n_bits]
        marginal[prefix] = marginal.get(prefix, 0.0) + prob

    return sorted(marginal.items())


def run_experiment(ansatz, backend, candidate_circuit, hamiltonian,
                   n_restarting, opt_method, n_bits=3):
    """Full pipeline: optimize -> bind best params -> sample -> marginalize.

    Returns
    -------
    energy : float
    n_eval : int
    relevant_bit : list of (prefix, probability)
    run_time : float -- wall-clock seconds
    """
    start = time.time()

    energy, best_parameters, n_eval = optimization_cycle(
        ansatz, backend, candidate_circuit, hamiltonian, opt_method, n_restarting
    )
    optimized_circuit = candidate_circuit.assign_parameters(best_parameters)
    distribution = sample(backend, optimized_circuit)
    relevant_bit = select_relevant_bit(distribution, n_bits)

    return energy, n_eval, relevant_bit, time.time() - start


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------

def plot_experiments(
    experiments,
    titles=None,
    highlight_keys=None,
    nrows=1,
    ncols=None,
    max_color="mediumpurple",
    other_color="lightgrey",
    highlight_color="red",
    good_bg="#a2ffa2",   # light green: most frequent key is a target
    bad_bg="#ffb7b7",    # light red: it is not
    figsize=(10, 11),
):
    """Plot one bar chart per experiment on a grid.

    Parameters
    ----------
    experiments : list of [(key, frequency), ...] (as from `select_relevant_bit`)
    titles : optional list of subplot titles
    highlight_keys : keys considered "correct"; their tick labels are drawn
        in `highlight_color`, and a subplot is green if its tallest bar is
        one of them, red otherwise
    nrows, ncols : grid shape (ncols is inferred if None)
    figsize : (width, height) tuple
    """
    highlight_keys = highlight_keys or []
    n_exp = len(experiments)
    ncols = ncols or int(np.ceil(n_exp / nrows))

    fig, axes = plt.subplots(nrows, ncols, figsize=figsize)
    axes = np.array(axes).reshape(-1)

    for i, exp in enumerate(experiments):
        ax = axes[i]
        keys = [k for k, _ in exp]
        freqs = [f for _, f in exp]

        max_idx = int(np.argmax(freqs))
        ax.set_facecolor(good_bg if keys[max_idx] in highlight_keys else bad_bg)

        # Grey bars, with the most frequent one emphasized.
        colors = [other_color] * len(freqs)
        colors[max_idx] = max_color
        ax.bar(keys, freqs, color=colors)

        if titles:
            ax.set_title(titles[i])

        ax.tick_params(axis="x", rotation=45)

        # Emphasize the target keys on the x axis.
        for tick in ax.get_xticklabels():
            if tick.get_text() in highlight_keys:
                tick.set_color(highlight_color)
                tick.set_fontweight("bold")

    # Remove unused subplots.
    for ax in axes[n_exp:]:
        fig.delaxes(ax)

    plt.tight_layout()
    plt.show()