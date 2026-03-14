# Language-Model-Enabled Automated Multi-Step Synthesis

Opentrons Flex protocols and RDKit enumeration scripts for high-throughput reaction design, execution, and post-reaction processing in support of the accompanying paper, *Language Model Enabled Automated Multi-Step Synthesis*. The experimental platform in the ESI is explicitly described as an **Opentrons Flex** automation workflow spanning **96-well amide coupling**, **SNAr chemistry**, and **multi-step synthesis**, which matches the code included here. 

## What this repository contains

This repo is organized around two complementary layers of the workflow:

### 1. Reaction planning and product enumeration
The RDKit scripts generate expected product sets from reagent libraries before or alongside automated execution.

- **`amide_coupling_enumerator.py`**  
  Enumerates amide products from amine and acid CSV inputs, optionally performs Boc deprotection, writes a product table, and saves a grid image of enumerated structures.
- **`snar_enumerator.py`**  
  Enumerates mono-SNAr products from amine and electrophile/core CSV inputs, writes a product table, and saves a grid image for visual review.

### 2. Opentrons Flex execution protocols
The Opentrons scripts implement plate-based liquid handling workflows on **Flex / API 2.25**. 

- **`OpentronsAI_AmideCouple_20260217_0148.py`**  
  Adds activating agent to acid-containing wells, waits 5 minutes, then adds amines and mixes. The code uses Flex 50 µL pipettes and an Axygen 96-well format.
- **`OpentronsAI__SNAr_20260224.py`**  
  Transfers amines into electrophile plates in repeated 5 µL additions separated by 10-minute delays, followed by final mixing, matching the staged SNAr workflow described in the ESI. 
- **`OpentronsAI_Multistep_Amine_Electrophile_20260305 (1).py`**  
  Performs column-wise amine-to-electrophile transfer with in-well mixing for multistep plate preparation. 
- **`OpentronsAI_Workup_20260306 (1).py`**  
  Implements a three-plate workup sequence with two 400 µL transfer stages and a 2-minute incubation between them. 

## Why this repo matters

This codebase connects **reaction enumeration** with **robot-ready execution**:

- build virtual product libraries from reagent CSVs,
- map those libraries onto 96-well plate layouts,
- execute liquid-handling workflows on Opentrons Flex,
- and perform downstream transfer/workup steps that support multistep synthesis campaigns. 

The ESI sections on **96-well amide coupling**, **SNAr data**, and **multi-step synthesis data** align directly with the code here.

## Repository layout

```text
.
├── OpentronsAI_AmideCouple_20260217_0148.py
├── OpentronsAI__SNAr_20260224.py
├── OpentronsAI_Multistep_Amine_Electrophile_20260305 (1).py
├── OpentronsAI_Workup_20260306 (1).py
├── amide_coupling_enumerator.py
├── snar_enumerator.py
```

## Quick start

### Python environment for enumerators

The enumeration scripts import `pandas`, `rdkit`, `argparse`, and standard RDKit drawing/utilities. 

A practical environment is:

```bash
python -m venv .venv
source .venv/bin/activate
pip install pandas rdkit pillow
```

`pillow` is included because the scripts save rendered grid images produced through RDKit image output. That dependency is inferred from the image save calls in the scripts.

### Run the amide enumerator

```bash
python amide_coupling_enumerator.py \
  --amines data/amines.csv \
  --acids data/acids.csv \
  --output results/amide_products.csv
```

Optional: disable Boc deprotection.

```bash
python amide_coupling_enumerator.py \
  --amines data/amines.csv \
  --acids data/acids.csv \
  --output results/amide_products.csv \
  --no-deprotect
```

This script writes a CSV plus a matching PNG grid image. fileciteturn1file13L85-L120

### Run the SNAr enumerator

```bash
python snar_enumerator.py \
  --amines data/amines.csv \
  --cores data/cores.csv \
  --output results/snar_products.csv
```

This script also writes a CSV plus a PNG grid image.

## Input formats

### Amide enumeration inputs

`amide_coupling_enumerator.py` expects:
- an amine CSV with a `SMILES` column and an amine identifier such as `amine` or `Amine_ID`
- an acid CSV with a `SMILES` column and an acid identifier such as `acid` or `Acid_ID` 
Example:

```csv
amine,SMILES
Amine_1,NCC1CCCCC1
Amine_2,CN1CCNCC1
```

```csv
acid,SMILES
Acid_A,O=C(O)C1CCCN1C(=O)OC(C)(C)C
Acid_B,O=C(O)C1CCNCC1
```

### SNAr enumeration inputs

`snar_enumerator.py` expects:
- an amine CSV with at least `amine` and `SMILES`
- a core/electrophile CSV with at least `core` and `SMILES` fileciteturn1file6L40-L90

Example:

```csv
amine,SMILES
Amine_A,CN1CCCCC1
Amine_B,NCC1CCCCC1
```

```csv
core,SMILES
Core_1,Clc1ncnc(Cl)n1
Core_2,FC(F)(F)c1cc(Cl)nc(Cl)n1
```

## Running the Opentrons protocols

All uploaded automation scripts declare **`robotType: Flex`** and **`apiLevel: 2.25`**, so they should be run in a compatible Opentrons Flex environment.

General workflow:

1. Open the Opentrons App.
2. Import the relevant protocol `.py` file.
3. Confirm Flex compatibility and API 2.25 support.
4. Load the labware referenced in the script.
5. Simulate the run before hardware execution.
6. Execute on the robot once deck setup and liquid assignments are verified.

## Protocol highlights

### Amide coupling
The amide protocol transfers **24.8 µL** of activating agent into each destination column, waits **5 minutes**, and then transfers **100 µL** of amine with mixing.This matches the 96-well amide coupling workflow described in the ESI, where activated acid stocks are combined with amine stocks before overnight incubation. 

### SNAr
The ESI describes repeated **5 µL additions** from amine wells to electrophile plates with **10-minute waits** between additions and final mixing after the fifth addition. The uploaded SNAr automation script is consistent with that staged addition design.

### Multistep transfer
The multistep transfer protocol performs column-wise transfer from an amine plate into a matched electrophile plate using the Flex 8-channel 50 µL pipette and includes in-well mixing after dispense. fileciteturn1file19L11-L37

### Workup
The workup protocol performs two consecutive **400 µL** plate-to-plate transfers using repeated 50 µL aspiration/dispense cycles, with a **2-minute delay** between stages.

## Example use cases

- **Virtual reaction design**  
  Enumerate expected amide or SNAr products from curated reagent libraries before running a plate.
- **Plate campaign planning**  
  Use the generated CSV and structure image outputs to define well-level targets and analytical expectations.
- **Automated execution on Flex**  
  Run plate-based amide, SNAr, multistep transfer, and workup workflows using the supplied protocol files.
- **Paper support / reproducibility**  
  Pair the code with the ESI to document how enumerated reaction space and robotic execution were connected experimentally. fileciteturn1file10L1-L18

## Notes

- The repo currently contains standalone scripts rather than a packaged Python module.
- Labware definitions are referenced directly in protocol code, so local Opentrons compatibility should be checked before execution.
- Dependency versions are not pinned in the uploaded materials, so installation guidance here is intentionally conservative and code-driven.

## Citation

If you use or adapt this work, cite the associated manuscript:

**Language Model Enabled Automated Multi-Step Synthesis**  
Patrick M. Doerner Barbour, Gregory D. Thiabaud, and James T. Brewster II.
