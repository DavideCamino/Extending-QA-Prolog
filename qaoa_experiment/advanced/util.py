import subprocess
import os

import numpy as np
import pandas as pd

import matplotlib
import matplotlib.pyplot as plt

from scipy.optimize import minimize
from collections import defaultdict
from typing import Sequence

from qiskit.quantum_info import SparsePauliOp
from qiskit.circuit.library import QAOAAnsatz

from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_ibm_runtime import Session, EstimatorV2 as Estimator
from qiskit_ibm_runtime import SamplerV2 as Sampler

from qiskit_aer import AerSimulator
from qiskit.transpiler import generate_preset_pass_manager

import qubovert

import time

def hello():
    print("asd")

def load_qubo(file):
    data = np.load(file)
    qubo_mat = data['qubo']
    n_qubits = len(data['syms'])

    return data, qubo_mat, n_qubits

def convert_to_ising(qubo_mat):
    qubo = qubovert.utils.matrix_to_qubo(qubo_mat)
    ising = qubovert.utils.qubo_to_quso(qubo)
    ising_dict = dict(ising)
    offset = ising_dict.pop(())
    ising_mat = qubovert.utils.qubo_to_matrix(ising_dict)

    return ising_dict, ising_mat

def build_paulis(matrix):
    pauli_list = []
    for i in range(len(matrix)):
        pauli_list.append(('Z', [i], matrix[i][i]))
        for j in range(i+1, len(matrix)):
            pauli_list.append(('ZZ', [i, j], matrix[i][j]))
    return pauli_list

def cost_func_estimator(params, ansatz, hamiltonian, estimator):
    # transform the observable defined on virtual qubits to
    # an observable defined on all physical qubits
    isa_hamiltonian = hamiltonian.apply_layout(ansatz.layout)
 
    pub = (ansatz, isa_hamiltonian, params)
    job = estimator.run([pub])
 
    results = job.result()[0]
    cost = results.data.evs
  
    return cost

def optimize(ansatz, backend, candidate_circuit, hamiltonian, opt_method):
    """
    Optimization of QAOA parameters with restarting strategy
    """
    init_params = np.random.rand(ansatz.num_parameters) * 2 * np.pi

    with Session(backend=backend) as session:
        estimator = Estimator(mode=session)
        estimator.options.default_shots = 1000
    
        result = minimize(
            cost_func_estimator,
            init_params,
            args=(candidate_circuit, hamiltonian, estimator),
            method=opt_method,
            #tol=1e-5,
        )

    return result

def optimization_cycle(ansatz, backend, candidate_circuit, hamiltonian, opt_method,  n_cycle=15):
    energy = []

    for i in range(n_cycle):
        result = optimize(ansatz, backend, candidate_circuit, hamiltonian, opt_method)
        energy.append((result.fun, result.x, result.nfev))

    best = min(energy)
    min_energy = best[0]
    best_parameters = best[1]
    n_eval = best[2]

    return min_energy, best_parameters, n_eval

def sample(backend, optimized_circuit):
    sampler = Sampler(mode=backend)
    sampler.options.default_shots = 10000
    
    pub = (optimized_circuit,)
    job = sampler.run([pub], shots=int(1e4))
    counts_int = job.result()[0].data.meas.get_int_counts()
    counts_bin = job.result()[0].data.meas.get_counts()
    shots = sum(counts_int.values())
    final_distribution_bin = {key: val / shots for key, val in counts_bin.items()}

    return final_distribution_bin

def select_relevant_bit(distribution_bin):
    first_3 = {}
    for (key, value) in distribution_bin.items():
        first = key[:3]
        if first in first_3.keys():
            first_3[first] += value
        else:
            first_3[first] = value

    lst = list(first_3.items())
    lst.sort()

    return lst


def run_experimet(ansatz, backend, candidate_circuit, hamiltonian, n_restarting, opt_method): 

    start_time = time.time()

    energy, best_parameters, n_eval = optimization_cycle(ansatz, backend, candidate_circuit, hamiltonian, opt_method, n_restarting)
    optimized_circuit = candidate_circuit.assign_parameters(best_parameters)
    final_distribution_bin = sample(backend, optimized_circuit)
    relevant_bit = select_relevant_bit(final_distribution_bin)

    end_time = time.time()

    run_time = end_time - start_time

    return energy, n_eval, relevant_bit, run_time

def plot_experiments(
    experiments,
    titles=None,
    highlight_keys=None,
    nrows=1,
    ncols=None,
    max_color="mediumpurple",
    other_color="lightgrey",
    highlight_color="red",
    figsize=20
):
    if highlight_keys is None:
        highlight_keys = []

    n_exp = len(experiments)

    if ncols is None:
        ncols = int(np.ceil(n_exp / nrows))

    fig, axes = plt.subplots(nrows, ncols, figsize=(10,11))
    axes = np.array(axes).reshape(-1)

    for i, exp in enumerate(experiments):
        ax = axes[i]

        keys = [k for k, _ in exp]
        freqs = [f for _, f in exp]

        max_idx = np.argmax(freqs)

        max_key = keys[max_idx]

        if max_key in highlight_keys:
            ax.set_facecolor("#a2ffa2")   # light green
        else:
            ax.set_facecolor("#ffb7b7")   # light red

        colors = [other_color] * len(freqs)
        colors[np.argmax(freqs)] = max_color

        ax.bar(keys, freqs, color=colors)

        if titles:
            ax.set_title(titles[i])

        # Rotate labels if necessary
        ax.tick_params(axis='x', rotation=45)

        # Highlight keys
        for tick in ax.get_xticklabels():
                if tick.get_text() in highlight_keys:
                    tick.set_color(highlight_color)
                    tick.set_fontweight("bold")

    # Remove unused axes
    for ax in axes[n_exp:]:
        fig.delaxes(ax)

    plt.tight_layout()
    plt.show()