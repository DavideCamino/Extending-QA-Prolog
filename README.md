# Extended QA-Prolog

This repository accompanies the scientific paper "**Extending QA-Prolog for Heterogeneous Quantum Workflows and Ontology Reasoning**" and provides instructions for reproducing the experiments presented in it.

The setup relies on a Python environment managed with `conda` and is organized into four phases:

1. **Basic Utilities**
2. **Quantum Frameworks**
3. **Custom QMASM**
4. **Original QA-Prolog Pipeline**

## Setup

### Environment Creation

Create and activate the conda environment:

```bash
conda create -n Extended_QA-Prolog python=3.10
conda activate Extended_QA-Prolog
```

### 1. Basic Utilities

Install the core dependencies:

```bash
pip install numpy matplotlib scipy jupyter
```

To work with QUBO problems, also install `qubovert`:

```bash
pip install qubovert
```

### 2. Quantum Frameworks

Install the D-Wave Ocean SDK:

```bash
pip install dwave-ocean-sdk
```

Install the IBM Qiskit framework:

```bash
pip install qiskit
```

Install IBM Runtime and Aer, in order to simulate IBM quantum hardware:

```bash
pip install qiskit_ibm_runtime
pip install qiskit-aer
```

Lastly to visualize quantum circuit is required:
```bash
pip install pylatexenc
```

### 3. Custom QMASM

This is an updated version of QMASM, modified in this work to restore compatibility with `scipy` and with the Ocean framework. The updated QMASM is available as a fork of the original project at [https://github.com/DavideCamino/qmasm](https://github.com/DavideCamino/qmasm).

To install it, clone the repository and run the setup script:

```bash
git clone https://github.com/DavideCamino/qmasm
cd qmasm
python setup.py install
```

This adds the `qmasm` executable directly to the `bin` folder of the conda environment.

### 4. Original QA-Prolog Pipeline

With the updated QMASM in place, the remaining pieces of the pipeline can be layered on top of it, each one building on the previous step.

#### `edif2qmasm`

Available at [https://github.com/lanl/edif2qmasm](https://github.com/lanl/edif2qmasm). This tool requires Go to be installed.

Once Go is available, follow the installation guide in [INSTALL.md](https://github.com/lanl/edif2qmasm/blob/master/INSTALL.md). The simplest approach is to create a dedicated folder for Go programs, then, from within that folder, run:

```bash
go install github.com/lanl/edif2qmasm@latest
```

This creates two folders, `bin` and `pkg`. To run Go programs from any location, add the `bin` folder to the environment path.

#### `yosys`

`edif2qmasm` converts an EDIF netlist into a QMASM-compatible symbolic Hamiltonian. To convert a Verilog digital circuit into an EDIF netlist, `yosys` is required.

This software is available from the official website, [https://yosyshq.net/yosys/](https://yosyshq.net/yosys/), and is also commonly available through the package manager of most Linux distributions.

#### `QA-Prolog`

The final component is QA-Prolog itself, available at [https://github.com/lanl/QA-Prolog/tree/master](https://github.com/lanl/QA-Prolog/tree/master).

The installation process described in [INSTALL.md](https://github.com/lanl/QA-Prolog/blob/master/INSTALL.md) is slightly outdated. Instead of using `go get`, QA-Prolog can be installed the same way as `edif2qmasm`:

```bash
go install github.com/lanl/QA-Prolog@latest
```

## Software Versions

The following table summarizes the exact software versions used to build and validate this setup. Matching these versions is recommended for exact reproducibility.

| Software | Version |
|---|---|
| Python | 3.10.20 |
| numpy | 2.2.6 |
| matplotlib | 3.10.9 |
| scipy | 1.15.3 |
| jupyter | 1.1.1 |
| qubovert | 1.2.5 |
| dwave-ocean-sdk | 9.4.0 |
| qiskit | 2.5.0 |
| qiskit-aer | 0.17.2 |
| qiskit-ibm-runtime | 0.48.0 |
|pylatexenc | 2.11 |
| qmasm (fork, commit) | `5cb9268af2ae88c9d2bbec9acd68d98ebbbfe223` |
| Go | 1.26.5 |
| edif2qmasm | v0.0.0-20220923054444-7bb1cdfb1b7b |
| yosys | 0.66 |
| QA-Prolog | v0.0.0-20220125203107-a6ff63ee38b7 |

## Conclusion

Each subfolder of this repository contains the script required to run a specific experiment presented in the paper, along with its own README detailing how to run it.
