# QUBO Problem Dimension vs. Unfolded Recursive Calls

This experiment measures how the dimension of the QUBO problem (number of qubits) scales with the number of unfolded recursive calls in the knowledge base, for a fixed query.

## Requirements

Activate the conda environment created in the main [README](../README.md):

```bash
conda activate Extended_QA-Prolog
```

**Important:** do not delete the `stdcell.qmasm` file. It is required by the pipeline to generate the QUBO problem correctly.

## Files

- `run_experiment.py` — script version of the experiment.
- `run_experiment.ipynb` — notebook version of the experiment, functionally equivalent to the script.

## Running the experiment

```bash
python run_experiment.py
```


Results are saved to `raw_data.tsv`, with one row per number of unfolded calls reporting the corresponding number of qubits. A plot of the data is available in the notebook.