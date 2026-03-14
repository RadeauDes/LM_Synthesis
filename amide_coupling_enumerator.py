import pandas as pd
from rdkit import Chem
from rdkit.Chem import Draw, Descriptors, AllChem
import argparse
import sys

def get_reactive_n_idx(amine_mol):
    """Finds the most nucleophilic N for amide coupling."""
    # 1. Primary or secondary aliphatic amines (preferred)
    match = amine_mol.GetSubstructMatch(Chem.MolFromSmarts("[NX3;H1,H2;!$(N-C=O);!$(N-S(=O)=O);!$(N-a)]"))
    if match:
        return match[0]
    # 2. Fallback to aromatic amines/indolines
    match = amine_mol.GetSubstructMatch(Chem.MolFromSmarts("[NX3;H1,H2;!$(N-C=O)]"))
    return match[0] if match else None

def get_carboxylic_acid_idx(acid_mol):
    """Identifies the carboxylic acid carbon for amide coupling."""
    # Match carboxylic acid: C(=O)O[H] or C(=O)[O-]
    pattern = Chem.MolFromSmarts("[CX3](=O)[OX2H1,OX1-]")
    match = acid_mol.GetSubstructMatch(pattern)
    if match:
        return match[0]  # Return the carbonyl carbon index
    return None

def get_acid_oh_idx(acid_mol):
    """Get the index of the OH (or O-) of the carboxylic acid to remove."""
    pattern = Chem.MolFromSmarts("[CX3](=O)[OX2H1,OX1-]")
    match = acid_mol.GetSubstructMatch(pattern)
    if match:
        return match[2]  # The third atom in the match is the OH oxygen
    return None

def remove_boc_group(mol):
    """Remove Boc protecting group from the molecule."""
    # Boc pattern: tert-butoxycarbonyl attached to nitrogen
    # CC(C)(C)OC(=O)N
    boc_pattern = Chem.MolFromSmarts("[CH3][C]([CH3])([CH3])OC(=O)[NX3]")
    
    if mol is None:
        return None
    
    match = mol.GetSubstructMatch(boc_pattern)
    if not match:
        return mol  # No Boc group found, return as-is
    
    # The nitrogen is the last atom in the match
    n_idx = match[6]
    # The carbonyl carbon of the Boc is match[5]
    carbonyl_c = match[5]
    
    rw = Chem.RWMol(mol)
    
    # Find atoms to remove (the entire Boc group except N)
    # Boc = C(CH3)3-O-C(=O)- 
    # We need to remove: 3 methyls, tertiary C, O, carbonyl C, and carbonyl O
    
    # Get the carbonyl oxygen (=O)
    carbonyl_o = None
    for neighbor in rw.GetAtomWithIdx(carbonyl_c).GetNeighbors():
        if neighbor.GetAtomicNum() == 8 and neighbor.GetIdx() != match[4]:
            carbonyl_o = neighbor.GetIdx()
            break
    
    # Atoms to remove (in descending order to preserve indices)
    atoms_to_remove = sorted([match[0], match[1], match[2], match[3], match[4], match[5]], reverse=True)
    if carbonyl_o is not None:
        atoms_to_remove = sorted(atoms_to_remove + [carbonyl_o], reverse=True)
    
    for idx in atoms_to_remove:
        rw.RemoveAtom(idx)
    
    try:
        product = rw.GetMol()
        Chem.SanitizeMol(product)
        return product
    except:
        return None

def remove_boc_rxn(mol):
    """Remove Boc group using reaction SMARTS (more robust)."""
    if mol is None:
        return None
    
    # Reaction: Boc-N -> H-N (deprotection)
    rxn_smarts = "[C:1](=O)[O:2][C:3]([CH3])([CH3])[CH3].[N:4]>>[N:4]"
    
    # Alternative approach: use ReplaceSubstructs
    boc_pattern = Chem.MolFromSmarts("C(=O)OC(C)(C)C")
    
    if not mol.HasSubstructMatch(boc_pattern):
        return mol
    
    # Use AllChem.ReplaceSidechains or manual removal
    # Let's do a cleaner reaction-based approach
    
    rxn = AllChem.ReactionFromSmarts("[CH3:1][C:2]([CH3:3])([CH3:4])[O:5][C:6](=[O:7])[N:8]>>[N:8]")
    
    try:
        products = rxn.RunReactants((mol,))
        if products and len(products) > 0:
            product = products[0][0]
            Chem.SanitizeMol(product)
            return product
    except:
        pass
    
    return mol

def run_amide_coupling(acid_smi, amine_smi, deprotect_boc=True):
    """
    Perform amide coupling between a carboxylic acid and an amine.
    Optionally remove Boc protecting group afterward.
    """
    # Strip whitespace
    acid = Chem.MolFromSmiles(acid_smi.strip())
    amine = Chem.MolFromSmiles(amine_smi.strip())
    
    if not acid or not amine:
        return None
    
    # Get reactive atoms
    acid_c_idx = get_carboxylic_acid_idx(acid)
    acid_oh_idx = get_acid_oh_idx(acid)
    amine_n_idx = get_reactive_n_idx(amine)
    
    if acid_c_idx is None or acid_oh_idx is None or amine_n_idx is None:
        return None
    
    # Remove the OH from the acid
    rw_acid = Chem.RWMol(acid)
    rw_acid.RemoveAtom(acid_oh_idx)
    acid_fragment = rw_acid.GetMol()
    
    # Adjust carbonyl carbon index if needed
    c_idx = acid_c_idx - (1 if acid_oh_idx < acid_c_idx else 0)
    
    # Combine acid fragment with amine
    combined = Chem.CombineMols(acid_fragment, amine)
    rw_combined = Chem.RWMol(combined)
    
    # Calculate new nitrogen index in combined molecule
    n_idx_final = acid_fragment.GetNumAtoms() + amine_n_idx
    
    # Add bond between carbonyl carbon and nitrogen
    rw_combined.AddBond(c_idx, n_idx_final, Chem.rdchem.BondType.SINGLE)
    
    product = rw_combined.GetMol()
    
    try:
        Chem.SanitizeMol(product)
    except:
        return None
    
    # Optionally remove Boc group
    if deprotect_boc:
        product = remove_boc_rxn(product)
    
    return product

def main():
    parser = argparse.ArgumentParser(description="Amide coupling enumeration with Boc deprotection")
    parser.add_argument("--amines", required=True, help="CSV file with amines (columns 1-7)")
    parser.add_argument("--acids", required=True, help="CSV file with Boc-amino acids (rows A-H)")
    parser.add_argument("--output", required=True, help="Output CSV file")
    parser.add_argument("--no-deprotect", action="store_true", help="Skip Boc deprotection")
    args = parser.parse_args()

    try:
        df_amines = pd.read_csv(args.amines)
        df_acids = pd.read_csv(args.acids)
    except Exception as e:
        print(f"Error reading CSV files: {e}")
        return

    # Limit to 7 amines (columns) and 8 acids (rows A-H)
    df_amines = df_amines.head(7)
    df_acids = df_acids.head(8)
    
    rows = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
    results, mols_for_grid, legends = [], [], []
    
    deprotect = not args.no_deprotect

    # Acids go down rows (A-H), Amines go across columns (1-7)
    for a_idx, acid_row in df_acids.iterrows():
        row_letter = rows[a_idx] if a_idx < len(rows) else f"R{a_idx}"
        
        for am_idx, amine_row in df_amines.iterrows():
            col_num = am_idx + 1
            well = f"{row_letter}{col_num}"
            
            prod_mol = run_amide_coupling(
                acid_row['SMILES'], 
                amine_row['SMILES'],
                deprotect_boc=deprotect
            )
            
            if prod_mol:
                smi = Chem.MolToSmiles(prod_mol, isomericSmiles=True)
                m_plus_h = Descriptors.ExactMolWt(prod_mol) + 1.0078
                
                results.append({
                    "Well": well,
                    "Amine_ID": amine_row.get('amine', amine_row.get('Amine_ID', f"Amine_{am_idx+1}")),
                    "Acid_ID": acid_row.get('acid', acid_row.get('Acid_ID', f"Acid_{a_idx+1}")),
                    "SMILES": smi,
                    "M+H": round(m_plus_h, 4)
                })
                mols_for_grid.append(prod_mol)
                legends.append(f"{well}\nMW: {m_plus_h:.2f}")
            else:
                print(f"Warning: Failed to couple at well {well}")

    if results:
        pd.DataFrame(results).to_csv(args.output, index=False)
        
        # Drawing options
        dopts = Draw.MolDrawOptions()
        dopts.addStereoAnnotation = True
        dopts.legendFontSize = 25
        dopts.minFontSize = 12
        
        img_path = args.output.replace(".csv", ".png")
        
        # Determine grid dimensions (7 columns for amines)
        mols_per_row = min(7, len(df_amines))
        
        img = Draw.MolsToGridImage(
            mols_for_grid, 
            molsPerRow=mols_per_row, 
            subImgSize=(350, 350),
            legends=legends,
            drawOptions=dopts
        )
        img.save(img_path)
        print(f"Success! Created {args.output} and {img_path}")
        print(f"Total products: {len(results)}")
    else:
        print("No products were generated. Check your input SMILES.")

if __name__ == "__main__":
    main()
