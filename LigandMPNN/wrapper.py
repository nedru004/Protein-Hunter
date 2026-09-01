import os
import json
import glob
import re
import tempfile
import subprocess
import torch

STANDARD_AA = set("ACDEFGHIKLMNPQRSTVWY")
_POSITION_TOKEN = re.compile(
    r"^(?:(?P<chain>[A-Za-z]+))?(?P<start>\d+)(?:-(?:(?P<end_chain>[A-Za-z]+))?(?P<end>\d+))?$"
)


def parse_fixed_positions(spec, default_chain="A"):
    """
    Parse a binder residue spec into 1-indexed positions and LigandMPNN tokens.

    Accepts comma/space-separated positions or ranges, with an optional chain
    prefix: ``10-16,20``, ``A10 A11 A12``, or ``A10-A16``.
    """
    if not spec or not str(spec).strip():
        return [], ""

    chain_default = str(default_chain).upper()
    positions = []
    for tok in re.split(r"[,\s]+", str(spec).strip()):
        if not tok:
            continue
        match = _POSITION_TOKEN.match(tok)
        if not match:
            raise ValueError(
                f"Invalid fixed position '{tok}'. Use 1-indexed positions or ranges, "
                "e.g. '10-16,20' or 'A10 A11 A12'."
            )
        chain = (match.group("chain") or chain_default).upper()
        end_chain = match.group("end_chain")
        if chain != chain_default:
            raise ValueError(
                f"Fixed position '{tok}' is on chain {chain}, but the designed "
                f"binder chain is {chain_default}."
            )
        if end_chain and end_chain.upper() != chain:
            raise ValueError(
                f"Range '{tok}' spans multiple chains; specify one chain at a time."
            )
        start = int(match.group("start"))
        end = int(match.group("end") or start)
        if start < 1 or end < 1:
            raise ValueError("Residue positions are 1-indexed and must be >= 1.")
        if end < start:
            raise ValueError(f"Invalid range '{tok}': end is less than start.")
        positions.extend(range(start, end + 1))

    seen = set()
    unique_positions = []
    for pos in positions:
        if pos not in seen:
            seen.add(pos)
            unique_positions.append(pos)
    tokens = " ".join(f"{chain_default}{pos}" for pos in unique_positions)
    return unique_positions, tokens


def apply_fixed_motif(sequence, positions, motif):
    """Write motif amino acids into ``sequence`` at 1-indexed ``positions``."""
    if not positions:
        return sequence
    if len(motif) != len(positions):
        raise ValueError(
            f"Motif length ({len(motif)}) must match the number of fixed "
            f"positions ({len(positions)})."
        )
    seq = list(sequence)
    for pos, aa in zip(positions, motif):
        if pos < 1 or pos > len(seq):
            raise ValueError(
                f"Fixed position {pos} is outside sequence length {len(seq)}."
            )
        if aa not in STANDARD_AA:
            raise ValueError(
                f"Motif residue '{aa}' at position {pos} is not a standard amino acid."
            )
        seq[pos - 1] = aa
    return "".join(seq)


def resolve_mpnn_fixed_residues(
    fixed_positions_spec,
    motif="",
    sequence="",
    chain="A",
    min_length=None,
):
    """
    Resolve motif amino acids and LigandMPNN ``--fixed_residues`` tokens.

    ``motif`` (if given) is written onto the binder at ``fixed_positions``.
    Otherwise amino acids are taken from ``sequence`` at those positions.
    """
    positions, token_str = parse_fixed_positions(
        fixed_positions_spec, default_chain=chain
    )
    motif = re.sub(r"\s+", "", motif or "").upper()
    sequence = sequence or ""

    if not positions:
        if motif:
            raise ValueError(
                "--motif requires --fixed_positions so MPNN knows which residues to keep."
            )
        return [], "", None

    if motif:
        if len(motif) != len(positions):
            raise ValueError(
                f"--motif length ({len(motif)}) must match the number of "
                f"--fixed_positions ({len(positions)})."
            )
        motif_aas = motif
    elif sequence:
        too_long = [p for p in positions if p > len(sequence)]
        if too_long:
            raise ValueError(
                f"--fixed_positions {too_long} exceed --seq length {len(sequence)}."
            )
        motif_aas = "".join(sequence[p - 1] for p in positions)
        if any(aa not in STANDARD_AA for aa in motif_aas):
            raise ValueError(
                "Fixed positions include undefined residues (e.g. X). "
                "Pass --motif with standard amino acids or a --seq that already "
                "contains the motif."
            )
    else:
        raise ValueError(
            "--fixed_positions requires --motif or --seq so those sites have "
            "defined amino acids before MPNN."
        )

    if sequence and max(positions) > len(sequence):
        raise ValueError(
            f"--fixed_positions go up to {max(positions)} but --seq length is {len(sequence)}."
        )
    if not sequence and min_length is not None and max(positions) > min_length:
        raise ValueError(
            f"--fixed_positions go up to {max(positions)} but min_protein_length "
            f"is {min_length}. Increase min_protein_length or lower the motif positions."
        )

    return positions, token_str, motif_aas


class LigandMPNNWrapper:
    def __init__(self, run_py="LigandMPNN/run.py", python="python"):
        self.run_py = run_py
        self.python = python

    def run(
        self,
        pdb_path,
        seed=111,
        model_type="protein_mpnn",
        temperature=0.1,
        temperature_per_residue=None,
        chains_to_design=None,
        bias_AA="",
        omit_AA="C",
        extra_args=None,
        fix_unk=True,
        return_logits=False,
        fixed_residues=None,
    ):
        """
        Unified Ligand/ProteinMPNN runner.

        Args:
            pdb_path (str): Path to PDB or CIF file.
            seed (int): Random seed.
            model_type (str): 'protein_mpnn', 'ligand_mpnn', 'soluble_mpnn', etc.
            temperature (float): Global temperature (sampling).
            temperature_per_residue (dict): Optional per-residue temp override.
            chains_to_design (str or list): e.g. 'A' or ['A','B'].
            bias_AA (str): Bias residues, e.g. "DE".
            omit_AA (str): Omit residues, e.g. "C".
            extra_args (dict): Additional command-line args.
            fix_unk (bool): Replace 'UNK' with 'GLY'.
            return_logits (bool): If True, return (S, logits) tensors.
            fixed_residues (str or list): LigandMPNN residues to keep, e.g. 'A12 A13 A14'.

        Returns:
            list[str] or (list[str], logits): Generated sequences or model outputs.
        """
        extra_args = dict(extra_args or {})

        with tempfile.TemporaryDirectory() as tmpdir:
            out_folder = tmpdir

            # --- Preprocess PDB ---
            pdb_copy = os.path.join(tmpdir, os.path.basename(pdb_path))
            with open(pdb_path, "r") as fin, open(pdb_copy, "w") as fout:
                for line in fin:
                    fout.write(line.replace("UNK", "GLY") if fix_unk else line)

            # --- Handle per-residue temperature ---
            temp_json_path = None
            if temperature_per_residue:
                temp_json_path = os.path.join(tmpdir, "temperature_per_residue.json")
                with open(temp_json_path, "w") as f:
                    json.dump(temperature_per_residue, f)

            # --- Build base command ---
            cmd = [
                self.python, self.run_py,
                "--seed", str(seed),
                "--pdb_path", pdb_copy,
                "--out_folder", out_folder,
                "--model_type", model_type,
                "--temperature", str(temperature)
            ]

            # --- Model checkpoint handling ---
            run_py_path = os.path.abspath(self.run_py)
            BASE_DIR = os.path.dirname(run_py_path)
            MODEL_DIR = os.path.join(BASE_DIR, "model_params")

            if model_type == "protein_mpnn":
                cmd += ["--checkpoint_protein_mpnn", os.path.join(MODEL_DIR, "proteinmpnn_v_48_020.pt")]
            elif model_type == "ligand_mpnn":
                cmd += ["--checkpoint_ligand_mpnn", os.path.join(MODEL_DIR, "ligandmpnn_v_32_010_25.pt")]
            elif model_type == "soluble_mpnn":
                cmd += ["--checkpoint_soluble_mpnn", os.path.join(MODEL_DIR, "solublempnn_v_48_020.pt")]

            # --- Add AA control options ---
            if omit_AA:
                cmd += ["--omit_AA", omit_AA]
            if bias_AA:
                cmd += ["--bias_AA", bias_AA]
            if return_logits:
                cmd += ["--return_logits"]
            if chains_to_design:
                if isinstance(chains_to_design, (list, tuple)):
                    chains_to_design = "".join(chains_to_design)
                cmd += ["--chains_to_design", chains_to_design]
            if temp_json_path:
                cmd += ["--temperature_per_residue", temp_json_path]
            if fixed_residues:
                if isinstance(fixed_residues, (list, tuple)):
                    fixed_residues = " ".join(str(item) for item in fixed_residues)
                cmd += ["--fixed_residues", str(fixed_residues)]

            # --- Add any extra CLI arguments ---
            for k, v in extra_args.items():
                cmd += [k, str(v)]

            # --- Run subprocess safely ---
            result = subprocess.run(cmd, capture_output=True, text=True)

            # --- Handle logits output ---
            if return_logits:
                stdout_lines = result.stdout.strip().split("\n")
                json_str = None
                for line in reversed(stdout_lines):
                    if line.strip().startswith("{"):
                        json_str = line.strip()
                        break
                if json_str is None:
                    raise RuntimeError("Could not find JSON output in stdout")

                try:
                    output = json.loads(json_str)
                    S = torch.tensor(output["S"][0])
                    log_probs = torch.tensor(output["log_probs"][0])
                    logits = torch.softmax(log_probs, dim=-1)
                    return S, logits
                except Exception as e:
                    raise RuntimeError(f"Failed to parse logits JSON: {e}")

            # --- Handle normal sequence generation ---
            if result.returncode != 0:
                raise RuntimeError(
                    f"LigandMPNN failed with code {result.returncode}\nSTDERR:\n{result.stderr}"
                )

            fasta_files = glob.glob(os.path.join(out_folder, "seqs", "*.fa"))
            if not fasta_files:
                raise RuntimeError("No FASTA found in output folder.")
            fasta = fasta_files[0]

            seqs = []
            with open(fasta) as f:
                for line in f:
                    if not line.startswith(">"):
                        seqs.append(line.strip())

            return seqs[1:], None
