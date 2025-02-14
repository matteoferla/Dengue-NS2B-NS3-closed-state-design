# Dengue-NS2B-NS3-closed-state-design
Wild type Dengue NS2B-NS3 protease refuses to crystallise in the closed/reaction-ready state: 
AI designs to the rescue!

Zika NS2B+NS3, PDB:8PN6, is in the closed state.

The fusion of Dengue NS2B-GGGGSGGGG-NS3 results in domain swapping.

Andre Schützer visually looked at the model and made a trimmed construct,
this construct was the basis for the design,
but the AA numbering was (mostly) kept to the original.
(I don't know the construct name, so in the files it is called `andre`)

## AlphaFold3 Modelling of constructs

I had envisioned that the AF3 models would refuse to fold in the closed state.
They actually _mostly_ fold in the closed state.

RMSD of replicates vs. state that matches PDB:8PN6

| experiment   |   count |     mean |       std |      min |      25% |      50% |      75% |      max |
|:-------------|--------:|---------:|----------:|---------:|---------:|---------:|---------:|---------:|
| fusion       |       5 | 0.964802 | 0.0316412 | 0.929486 | 0.944555 | 0.965687 | 0.971505 |  1.01278 |
| split_andre  |      25 | 3.30666  | 3.92184   | 0        | 0.752309 | 0.914142 | 8.00751  | 13.0989  |
| split_full   |      25 | 4.0446   | 3.29357   | 1.89563  | 2.19573  | 2.37641  | 2.75445  | 12.6187  |


Full table: [af3_rmsds file](af3_rmsds.csv)

The construct matches very well the Zika model, PDB:8PN6, 
therefore, there is no need to thread the sequence on PDB:8PN6 then!

The [top model of the andre split](models/split_andre_model.cif) is correct 
and the replicates were modelled over half the time in the correct state.
The [top model of split NSP2B-NSP3 full sequence](models/split_full_model.cif) is in wrong state,
and the _mostly_ correct state is visited once or twice only ([example](split_full-seed-666_sample-3.cif)).

Mostly: top constructs in mostly correct state (fusion, trimmed, full):

![constructs](images/constructs.png)

## Design of better linker

The linker construct (NS2B-GGGGSGGGG-NS3) is subpar because the protein itself has floppy ends.

![fusion](images/fusion.png)

However, the linker could be designed to better adhere to the protein.

The design was done in the following stages:

* ~4,000 RFdiffusion designs (5 major series, 3 successful, see below)
* Filtering of RFdiffusion designs: minimum residue pLDDT > 0.90
* No structural filtering were done at this stage
* proteinMPNN designs (507 &times; 5)
* Filtering of proteinMPNN designs: sorted by `global_score` (low is better), cutoff global_score of first polyG sequence
* 1301 AlphaFold3 models (one seed only)
* Filtering of AF3 replicate models: RMSD vs reference closed structure < 1.5Å
* 182 Rosetta FastRelax minimised (5 cycles, ref2015)

Note: pLDDT filtering at the RFdiffusion is a personal choice
as there is a weak correlation (personal results: ask if interested) between
RFdiffusion pLDDT and final Rosetta score.
Likewise proteinMPNN global_score, but better to stack the deck in your favour.

### Symmetry series

> Experiment group: `mirror`

One design idea was to design a linker that aids dimerisation in the crystal form
seen in PDB:8PN6. See [symmetry.md](symmetry.md) for more details.

This is a rabbit hole of madness —TL;DR: C2 symmetry, but no designed loops aimed dimerisation.
Nevertheless, the symmetry provided a useful no-go zone cutoff.

* Contig: `[A1-40/15-40/A41-196/0 A1001-1040/15-40/A1041-1196/0]`
* N designs: 50 per length = 1,800 
* 
(Note: symmetry does not work with ranges, so an iterations were done)

### Alt cut series

A fusion of NS2B and NS3 needs a long linker,
furthermore, NS2B is not ordered in isolation, 
so it seems unproductive expressing the unstable part first...

The NS2B peptide is formed of

* a N-terminal beta-strand that packs with the C-terminal sheet of NS3
* a long linker
* a C-terminal beta-hairpin

Were the linker ignored as it lacks buried hydrophobic (bar for W14),
the N-terminal beta-strand of NS2B could be appended to the C-terminus of NS3
and the C-terminal beta-hairpin of NS2B could be prepended to the N-terminus of NS3.

The former sheet has two strand adjacent residues of note, NSP2B V12 and NSP3 L18 (3 in Andre).
Cutting after NSP2B V12 and before NSP3 L18, gives 18Å gap (/3.5 = 5AA)
Cutting after NSP2B W14 and before NSP3 L18, gives 21Å gap  (/3.5 = 6AA)

The hairpin is more problematic, 
adding after NSP13 K170 the NSP2B 26-41 beta-hairpin, gives a 28Å gap (8AA).

On initial inspection, it is clear a further design refinement is possible:
inserting the C-terminus hairpin of NSP2B between residue 71–79 (:warning: get Unicode numbering).

![alt-cut](images/alt-cut.png)

* Altcut-A Contig: `[A1-12/6-10/B4-155/8-15/A25-41/0]`
* * Altcut-A N designs: 1,000
* Altcut-B Contig: `A1-12/6-10/B4-76/3-6/A25-41/6-10/B79-155/0`
* * Altcut-B N designs: 500

### ProteinMPNN

Difference in global_score of the two groups:
![proteinMPNN-control.png](images/proteinMPNN-groups.png)

The rando outliers are the polyG sequences, which is expected/good:
![proteinMPNN-control.png](images/proteinMPNN-control.png)

### AF3 scoring

On a A100 the rate limiting step for AF3 is the A3M MSA generation
(~15minutes even with databases on the node's local NVMe).

Without template things fail:

|       |   chain_pair_iptm |   chain_pair_pae_min |   chain_ptm |   fraction_disordered |   has_clash |    ptm |   ranking_score |
|:------|------------------:|---------------------:|------------:|----------------------:|------------:|-------:|----------------:|
| count |            582    |               582    |      582    |                582    |         582 | 582    |          582    |
| mean  |              0.18 |                 0.76 |        0.18 |                  0.62 |           0 |   0.18 |            0.49 |
| std   |              0.03 |                 0    |        0.03 |                  0.18 |           0 |   0.03 |            0.07 |
| min   |              0.14 |                 0.76 |        0.14 |                  0    |           0 |   0.14 |            0.24 |
| 25%   |              0.16 |                 0.76 |        0.16 |                  0.51 |           0 |   0.16 |            0.44 |
| 50%   |              0.17 |                 0.76 |        0.17 |                  0.62 |           0 |   0.17 |            0.49 |
| 75%   |              0.19 |                 0.76 |        0.19 |                  0.73 |           0 |   0.19 |            0.54 |
| max   |              0.35 |                 0.76 |        0.35 |                  1    |           0 |   0.35 |            0.66 |

The WT fails too without MSA:

![AF3-wo-MSA](images/AF3-wo-MSA.png)

Oddly, providing a template for the NSP3 also fails.

![AF3-w-template](AF3-w-template.png)

The solution was then to munge the A3M of the NSP3 to be gapped appropriately.
NSP2B was left out to favour true binders.

### Final selection
Of the 5 replicates in AF3 those with an RMSD under 1.5Å were chosen.

These were minimised with Rosetta FastRelax (5 cycles, ref2015)
with a termini 'stretching' restraint, in the offchance that the termini are badly bundled 
(no case failed, but best be safe).

The number of accepted replicates varied (1.8 mean), but had a standard deviation of 7.8 REU.

![design-scores.png](images/design-scores.png)

164 finalists is not great, but it is only a linker
and the filtering was harsh.

Of the 181 designs, only 73 failed the final filtering due to one or more of the following:
* 53 were singletons
* 15 had more than one residue with a potential worse than 6.0 kcal/mol (harsh)
* 17 had a worse potential than the WT (this is low, but I double-checked for bugs in the code)

The top50 final designs are in [linker-designs](models/linker-designs),
Their sequences are in [top_linker_designs.fasta](linker_designs.fasta) and
the look like:

![linker-designs.png](images/linker-designs.png)

In the above image, turquoise is the NS3, coral is the design, and gold is the NS2B,
however, the NS2B annotation was a hack in PyMOL and is not accurate,
see JSON files for the actual details.
Also, note that in the PDB files, 
the temperature factor is Rosetta per residue energy, design residues have an occupancy of 0.5,
for proper analysis see the actual json files, this is just for PyMOL.

## Chimotrypsin

Other serine proteases, like chimotrypsin are not split. What does that look like?

These extra sheets look different, so poor comparison. I could look for closer structures,
but most likely it will require some effort to find a useful match...

![chimotrypsin](images/vs_chimotrypsin.png)