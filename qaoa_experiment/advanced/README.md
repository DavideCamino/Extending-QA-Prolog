# QAOA Batch Experiment on an Automatically Generated SAT QUBO Problem

This experiment automates the generation of the circuit-SAT QUBO problem directly from its Verilog source, converts it to Ising form, and runs a batch of 30 QAOA experiments (5-layer ansatz, COBYLA optimizer, 15 restarts per run) on a simulated backend, saving the resulting bitstring distributions to file.

## Requirements

Activate the conda environment created in the main [README](../README.md):

```bash
conda activate Extended_QA-Prolog
```

> **Important:** do not delete the `stdcell.qmasm` and `synth.ys` files. They are required by the translation pipeline.

Unlike the previous QAOA experiment, the QUBO problem generation is automated by the script itself (via the `gen_qubo` function), so the Verilog-to-QUBO pipeline commands do not need to be run manually beforehand. It is sufficient to have the Verilog source `circ_sat.v` present in the working directory.

## Files

- `run_experiment.py` — script version of the experiment.
- `run_experiment.ipynb` — notebook version of the experiment, functionally equivalent to the script. It additionally allows visualizing the results as an errorplot.
- `util.py` — helper module providing `load_qubo`, `convert_to_ising`, `build_paulis` and `run_experiment`, required by the script.

## Running the experiment

```bash
python run_experiment.py
```

Results are saved to `raw_data.tsv`: the header row lists the eight possible 3-bit outcomes, and each subsequent row reports their frequencies for one of the 30 batch runs.