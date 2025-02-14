# Active site visualization with PyMOL

Getting the neighbourhood residues:
```python
pose = pyrosetta.pose_from_file('andre.min.pdb')
triad = pr_res.ResidueIndexSelector()
offset = len(pose.chain_sequence(1))
for resi, resn in [(36, 'HIS'), (60, 'ASP'), (120, 'SER')]:
    assert pose.residue(resi+offset).name3() == resn, (pose.residue(resi+offset).name3(), resn)
    triad.append_index(resi+offset)
neigh = pr_res.CloseContactResidueSelector()
neigh.central_residue_group_selector(triad)
neigh.threshold(6)

no_go_residue_idx0s = pr_res.ResidueVector(neigh.apply(pose))

print(no_go_residue_idx0s)
print('+'.join(map(str, [r - offset for r in no_go_residue_idx0s])))
```

Gives:

    select cata, chain B and resi 36+120+60
    select neigh6, (resi 34+35+37 and chain A) or (resi 10+20+21+22+23+24+33+34+35+36+37+38+39+56+57+58+59+60+61+62+68+85+87+115+116+117+118+119+120+121+122+134+135+136+137+146+149+151 and chain B)
    select neigh4, (resi 35 and chain A) or (resi 22+23+33+34+35+36+37+38+39+56+57+58+59+60+61+117+118+119+120+121+122+135+136+137+151 and chain B)
    color white, element C    
    color gold, chain A and element C
    color black, cata and element C
    color teal, neigh4 and element C
    color turquoise, neigh6 and not neigh4 and element C
    color atomic, not element C
    hide sticks
    show sticks, (cata or neigh6) and not element H