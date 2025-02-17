#!/usr/bin/env python

import pandas as pd
from pathlib import Path
import json, os, random, time, traceback
from pebble import ProcessPool, ProcessFuture
import pyrosetta
import pyrosetta_help as ph
from types import ModuleType
from typing import Union, Any, List, Dict
# Better than star imports:
prc: ModuleType = pyrosetta.rosetta.core
prp: ModuleType = pyrosetta.rosetta.protocols
pru: ModuleType = pyrosetta.rosetta.utility
prn: ModuleType = pyrosetta.rosetta.numeric
prs: ModuleType = pyrosetta.rosetta.std
pr_conf: ModuleType = pyrosetta.rosetta.core.conformation
pr_scoring: ModuleType = pyrosetta.rosetta.core.scoring
pr_res: ModuleType = pyrosetta.rosetta.core.select.residue_selector
pr_options: ModuleType = pyrosetta.rosetta.basic.options

logger = ph.configure_logger()
pyrosetta.distributed.maybe_init(extra_options=ph.make_option_string(no_optH=False,
                                                                     ex1=None,
                                                                     ex2=None,
                                                                     ignore_unrecognized_res=False,
                                                                     load_PDB_components=True,
                                                                     ignore_waters=True,
                                                                    )
                                 )

def read_jsonl(filename: Union[str, Path]) -> List[Any]:
    """
    Read a jsonl file skipping errors

    :param filename:
    :return:
    """
    data = []
    for line in Path(filename).read_text().split('\n'):
        with contextlib.suppress(json.JSONDecodeError):
            data.append(json.loads(line))
    return data

def write_jsonl(filename: Union[str, Path], data: Any):
    """
    Write a jsonl file
    I have not checked if I need to escape newlines

    :param filename:
    :param data:
    :return:
    """
    hold_path = Path(str(filename) + '.hold')
    while hold_path.exists():
        time.sleep(1)
    hold_path.write_text()    
    with Path(filename).open('a') as f:
        f.write(json.dumps(data) + '\n')
    os.remove(hold_path)

def path2pose(path:Path, ranking_score=0.) -> pyrosetta.Pose:
    path = Path(path)
    if path.suffix == '.pdb':
        return pyrosetta.pose_from_file(path.as_posix())
    elif path.suffix == '.cif':
        if '_database_PDB_remark.text' not in path.read_text():
            with path.open('a') as fh:
                fh.write(f'\n_database_PDB_remark.text  "AlphaFold3 rank={path.name} ranking_score={ranking_score}"\n')
        
        pose = pyrosetta.Pose()
        prc.import_pose.pose_from_file(pose, path.as_posix(), False, pyrosetta.rosetta.core.import_pose.FileType.CIF_file)
        return pose
    else:
        raise Exception

from Bio.Align import PairwiseAligner, Alignment, substitution_matrices
from typing import TypeAlias, Dict
FTypeIdx: TypeAlias = int  # one-based index
CTypeIdx: TypeAlias = int  # zero-based index

def minimize(model_path):
    name = model_path.stem.replace('_model', '')
    out_path = Path(f'rf_output/af3_minimized/{name}.pdb')
    taken_path = Path(f'rf_output/af3_minimized/{name}.pdb.hold')
    log_path = Path(f'rf_output/af3_minimized/scores.jsonl')
    if out_path.exists() or taken_path.exists():
        return True
    taken_path.write_text('working on it!')
    scorefxn = pyrosetta.get_fa_scorefxn()
    scorefxn.set_weight(pr_scoring.ScoreType.atom_pair_constraint, 1)
    relax = pyrosetta.rosetta.protocols.relax.FastRelax(scorefxn, 5)
    pose = path2pose(model_path)
    last_polymer_idx1 = pose.total_residue() - int(pose.sequence()[-1] == 'Z') 
    ph.add_stretch_constraint(pose, weight=1, residue_index_B=last_polymer_idx1)
    relax.apply(pose)
    pose.dump_pdb(out_path.as_posix())
    os.remove(taken_path)
    write_jsonl(log_path, {'name': name, 'score': scorefxn(pose)})
    return True

def get_max_cores():
    """
    the number of cores to use.
    Called by main
    """
    if os.environ['SLURM_JOB_CPUS_PER_NODE']:
        return int(os.environ['SLURM_JOB_CPUS_PER_NODE'])
    else:
        return os.cpu_count()

def main(timeout=60*60*5):
    futuredex = {}
    with ProcessPool(max_workers=get_max_cores() - 1, max_tasks=0) as pool:
        # queue jobs
        model_paths = list(Path('rf_output/af3_selected').glob('*.pdb'))
        random.shuffle(model_paths)
        for model_path in model_paths:
            future: ProcessFuture = pool.schedule(minimize, kwargs=dict(model_path=model_path, ), timeout=timeout)
            futuredex[model_path.stem] = future
        print(f'Submitted {len(futuredex)} processes')
        # ## Get results
        for name, future in futuredex.items():
            try:
                print(name)
                future.result()  # blocks until results are ready
            except Exception as error:
                error_msg = str(error)
                if isinstance(error, TimeoutError):
                    print(f'Processing {name} took longer than {timeout} seconds {error}')
                else:
                    print(f"Processing {name} raised {error}")
                    traceback.print_tb(error.__traceback__)  # traceback of the function
        print('Complete', flush=True)

if __name__ == '__main__':
    main()