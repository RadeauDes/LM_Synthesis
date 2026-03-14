import pandas as pd
from rdkit import Chem
from rdkit.Chem import Draw, Descriptors
import argparse
import sys

def get_reactive_n_idx(amine_mol):
    """Finds the most nucleophilic N. Includes fallback for indoline/aniline nitrogens."""
    # 1. Primary or secondary aliphatic amines (preferred)
    match = amine_mol.GetSubstructMatch(Chem.MolFromSmarts("[NX3;H1,H2;!$(N-C=O);!$(N-S(=O)=O);!$(N-a)]"))
    if match:
        return match[0]
    # 2. Fallback to aromatic amines/indolines/tetra-hydroquinoline
    match = amine_mol.GetSubstructMatch(Chem.MolFromSmarts("[NX3;H1,H2;!$(N-C=O)]"))
    return match[0] if match else None

def get_qz_c4_cl_idx(core_mol):
    """Identifies the C4-Chlorine on a quinazoline (C with 1 aromatic N neighbor)."""
    for atom in core_mol.GetAtoms():
        if atom.GetAtomicNum() == 17:  # Chlorine
            carbon = atom.GetNeighbors()[0]
            if carbon.GetIsAromatic():
                # Count aromatic Nitrogen neighbors of the carbon
                n_count = sum(1 for nb in carbon.GetNeighbors() if nb.GetAtomicNum() == 7 and nb.GetIsAromatic())
                if n_count == 1: # C4 has only 1 N neighbor
                    return atom.GetIdx()
    return None

def get_generic_aryl_cl_idx(core_mol):
    """Returns the index of the first available aryl chloride."""
    for atom in core_mol.GetAtoms():
        if atom.GetAtomicNum() == 17:
            carbon = atom.GetNeighbors()[0]
            if carbon.GetIsAromatic():
                return atom.GetIdx()
    return None

def run_mono_snar(core_smi, amine_smi):
    # Strip whitespace to handle formatting issues in CSV
    core = Chem.MolFromSmiles(core_smi.strip())
    amine = Chem.MolFromSmiles(amine_smi.strip())
    if not core or not amine: return None

    cl_idx = get_qz_c4_cl_idx(core) or get_generic_aryl_cl_idx(core)
    n_idx_rel = get_reactive_n_idx(amine)

    if cl_idx is None or n_idx_rel is None: return None

    c_idx_pre = core.GetAtomWithIdx(cl_idx).GetNeighbors()[0].GetIdx()
    rw = Chem.RWMol(core)
    rw.RemoveAtom(cl_idx)
    host = rw.GetMol()
    
    c_idx = c_idx_pre - (1 if cl_idx < c_idx_pre else 0)
    
    combined = Chem.CombineMols(host, amine)
    rw_combined = Chem.RWMol(combined)
    n_idx_final = host.GetNumAtoms() + n_idx_rel
    rw_combined.AddBond(c_idx, n_idx_final, Chem.rdchem.BondType.SINGLE)
    
    product = rw_combined.GetMol()
    try:
        Chem.SanitizeMol(product)
        return product
    except:
        return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--amines", required=True)
    parser.add_argument("--cores", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    try:
        df_amines = pd.read_csv(args.amines).head(8) # Change number of amines here
        df_cores = pd.read_csv(args.cores).head(8) # Change number of electrohiles here
    except Exception as e:
        print(f"Error reading CSV files: {e}")
        return

    rows = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
    results, mols_for_grid, legends = [], [], []

    for c_idx, c_row in df_cores.iterrows():
        col_num = c_idx + 1
        for r_idx, a_row in df_amines.iterrows():
            well = f"{rows[r_idx]}{col_num}"
            prod_mol = run_mono_snar(c_row['SMILES'], a_row['SMILES'])
            
            if prod_mol:
                smi = Chem.MolToSmiles(prod_mol, isomericSmiles=True)
                m_plus_h = Descriptors.ExactMolWt(prod_mol) + 1.0078
                
                results.append({
                    "Well": well,
                    "Amine_ID": a_row['amine'],
                    "Core_ID": c_row['core'],
                    "SMILES": smi,
                    "M+H": round(m_plus_h, 4)
                })
                mols_for_grid.append(prod_mol)
                # Clean label: Well ID on top, Mass below
                legends.append(f"{well}\nMW: {m_plus_h:.2f}")

    if results:
        pd.DataFrame(results).to_csv(args.output, index=False)
        
        # --- CLEAN UP DRAWING OPTIONS ---
        dopts = Draw.MolDrawOptions()
        dopts.addStereoAnnotation = True
        dopts.legendFontSize = 25  # Larger, clearer text
        dopts.minFontSize = 12
        
        img_path = args.output.replace(".csv", ".png")
        img = Draw.MolsToGridImage(
            mols_for_grid, 
            molsPerRow=8, 
            subImgSize=(350, 350),
            legends=legends,
            drawOptions=dopts
        )
        img.save(img_path)
        print(f"Success! Created {args.output} and {img_path}")

if __name__ == "__main__":
    main()