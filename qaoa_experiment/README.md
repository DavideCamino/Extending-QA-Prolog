# QAOA Solving of a Circuit-SAT QUBO Problem

This experiment runs a QAOA circuit (5 layers) on the Ising form of a circuit-SAT QUBO problem, optimizes its parameters on a simulated backend, and samples the resulting distribution over repeated runs.


The circuit represents the logic formula: $$a \land (\neg (b \lor c)).$$


## Requirements

Activate the conda environment created in the main [README](../README.md):

```bash
conda activate Extended_QA-Prolog
```

**Important:** do not delete the `stdcell.qmasm` and `synth.ys` files. They are required by the translation pipeline below.

## Generating the QUBO problem

Before running the script, the QUBO problem must be obtained in matrix form (`sat.npz`). This is done by running part of the Verilog-to-QUBO translation pipeline:

```bash
yosys circ_sat.v work/synth.ys -b edif -o work/circ_sat.edif
edif2qmasm -o work/circ_sat.qmasm work/circ_sat.edif
cd work
qmasm --format numpy -o ../sat.npz --solver=tabu --pin "circ_sat.y := true" circ_sat.qmasm
```

## Files

- `run_experiment.py` — script version of the experiment.
- `run_experiment.ipynb` — notebook version of the experiment, functionally equivalent to the script. It additionally allows visualizing the QAOA circuit inline, and reports the results as bar charts.

## Running the experiment

```bash
python run_experiment.py
```

Results are saved to `raw_data.tsv`, one column per bitstring (first 3 measured bits) and one row per experiment, reporting the corresponding probability.