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

from util import *


opt_methods = ['Nelder-Mead', 'Powell', 'CG', 'BFGS', 'L-BFGS-B', 'TNC', 'COBYLA', 'COBYQA', 'SLSQP', 'trust-constr']
opt_methods = ['COBYLA', 'COBYQA', 'CG', 'BFGS', 'L-BFGS-B', 'TNC', 'trust-constr', 'Powell']
restarting = 15
batch = 30
tsv_name = 'df.tsv'
df_name = 'df_2.pkl'



def gen_qubo(verilog_source):
    try:
        path = os.getcwd()
        subprocess.run(['yosys', verilog_source, 'work/synth.ys', '-b', 'edif', '-o', 'work/circ_sat.edif'], capture_output=True)
        subprocess.run(['edif2qmasm', '-o', 'work/circ_sat.qmasm', 'work/circ_sat.edif'])
        os.chdir('work')
        subprocess.run(['qmasm', '--format', 'numpy', '-o', '../sat.npz', '--solver', 'tabu', '--pin', 'circ_sat.y := true', 'circ_sat.qmasm'])
        os.chdir(path)
        return 0
    except:
        return 1

def gen_ising(qubo_mat):
    ising_dict, ising_mat = convert_to_ising(qubo_mat)
    ising_solution = qubovert.QUSO(ising_dict).solve_bruteforce()
    ising_energy = qubovert.QUSO(ising_dict).value(ising_solution)
    return ising_mat, ising_energy

def gen_index(batch, methods):
    id_m = []
    id_b = []
    id = []
    for m in methods:
        for i in range(batch):
            id_m.append(m)
            id_b.append(i)
    id.append(id_m)
    id.append(id_b)
    return pd.MultiIndex.from_arrays(id, names=["opt_method", "rep"])

def gen_df():
    index = gen_index(batch, opt_methods)
    column = ["energy", "n_eval", "runtime"]
    column.extend(["000", "001", "010", "011", "100", "101", "110", "111"])
    df = pd.DataFrame(np.zeros((batch*len(opt_methods), len(column))), index=index, columns=column)
    return df

def initialize_tsv(file):
    column = ["method", "rep", "energy", "n_eval", "runtime", "000", "001", "010", "011", "100", "101", "110", "111"]
    with open(file, 'w') as out:
        for col in column:
            out.write(col + "\t")
        out.write('\n')

def save_results(df, method, rep, energy, n_eval, result, run_time):
    data = [energy, n_eval, run_time]
    for res in result:
        data.append(res[1])

    df.loc[method, rep] = data
    return 0

def write_tsv(method, i, energy, n_eval, res, run_time, file):
    with open(file, 'a') as out:
        out.write(method + '\t' + str(i) + '\t' + str(energy) + '\t' + str(n_eval) + '\t' + str(run_time))
        for freq in res:
            out.write('\t' + str(freq[1]))
        out.write('\n')
    return 0

def run_experiments(ansatz, backend, candidate_circuit, cost_hamiltonian, restarting, opt_methods, df, file_tsv):
    for method in opt_methods:
        for i in range(batch):
            energy, n_eval, res, run_time = run_experimet(ansatz, backend, candidate_circuit, cost_hamiltonian, restarting, method)
            print(method, i, run_time, sep='\t')
            save_results(df, method, i, energy, n_eval, res, run_time)
            write_tsv(method, i, energy, n_eval, res, run_time, file_tsv)

def __main__():
    error = gen_qubo('circ_sat.v')
    data, qubo_mat, n_qubits = load_qubo('sat.npz')
    ising_mat, ising_energy = gen_ising(qubo_mat)
    cost_hamiltonian = SparsePauliOp.from_sparse_list(build_paulis(ising_mat), n_qubits)
    ansatz = QAOAAnsatz(cost_operator=cost_hamiltonian, reps=5)
    ansatz.measure_all()
    backend = AerSimulator()
    pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
    candidate_circuit = pm.run(ansatz)

    df = gen_df()
    initialize_tsv(tsv_name)
    run_experiments(ansatz, backend, candidate_circuit, cost_hamiltonian, restarting, opt_methods, df, tsv_name)
    df.to_pickle(df_name)
    return 0

__main__()