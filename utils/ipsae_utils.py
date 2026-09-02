"""ipSAE scoring for binder ranking (Dunbrack ipSAE via the `ipsae` package)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Union

import numpy as np

# AF3 / Boltz / Chai defaults from the ipsae package
DEFAULT_PAE_CUTOFF = 10.0
DEFAULT_DIST_CUTOFF = 10.0


def _ips_calculator():
    try:
        from ipsae import IpsaeCalculator
    except ImportError as exc:
        raise ImportError(
            "The `ipsae` package is required for binder ranking. "
            "Install it with: pip install ipsae"
        ) from exc
    return IpsaeCalculator


def _to_numpy_pae(pae: Any) -> np.ndarray:
    if pae is None:
        raise ValueError("PAE matrix is missing; cannot compute ipSAE.")
    if hasattr(pae, "detach"):
        pae = pae.detach().cpu().numpy()
    pae = np.asarray(pae, dtype=np.float64)
    while pae.ndim > 2:
        pae = pae[0]
    if pae.ndim != 2 or pae.shape[0] != pae.shape[1]:
        raise ValueError(f"Expected square PAE matrix, got shape {pae.shape}")
    return pae


def _align_pae(pae: np.ndarray, n_res: int) -> np.ndarray:
    if pae.shape[0] == n_res:
        return pae
    if pae.shape[0] > n_res:
        # Extra tokens (ligands) are typically appended after polymer residues.
        return pae[:n_res, :n_res]
    raise ValueError(
        f"PAE size {pae.shape[0]} is smaller than residue count {n_res}"
    )


def _structure_file_type(structure_path: Union[str, Path]) -> str:
    suffix = Path(structure_path).suffix.lower()
    if suffix == ".pdb":
        return "af2"
    if suffix in {".cif", ".mmcif"}:
        return "af3"
    raise ValueError(f"Unsupported structure format: {structure_path}")


def _chain_ipsae_values(ipsae_max: Dict[str, Dict[str, float]], binder_chain: str):
    if binder_chain in ipsae_max:
        others = [v for c, v in ipsae_max[binder_chain].items() if c != binder_chain]
        if others:
            return others
    values = []
    for chain1, inner in ipsae_max.items():
        for chain2, value in inner.items():
            if chain1 < chain2:
                values.append(value)
    return values


def compute_binder_ipsae(
    structure_path: Union[str, Path],
    pae: Any,
    binder_chain: str = "A",
    pae_cutoff: float = DEFAULT_PAE_CUTOFF,
    dist_cutoff: float = DEFAULT_DIST_CUTOFF,
) -> Optional[float]:
    """
    Mean max-ipSAE between the binder chain and every other polymer chain.

    Uses the official `ipsae` calculator (d0-res / Type=max), which is the
    recommended score for ranking predicted binders.
    """
    structure_path = Path(structure_path)
    if not structure_path.exists():
        print(f"WARNING: Structure not found for ipSAE: {structure_path}")
        return None

    try:
        pae_matrix = _to_numpy_pae(pae)
        calc = _ips_calculator()(pae_cutoff, dist_cutoff)
        file_type = _structure_file_type(structure_path)
        residues, cb_residues, chains, _token_mask = calc._load_structure(
            structure_path, file_type
        )
        if len(residues) < 2 or len(np.unique(chains)) < 2:
            return 0.0

        if len(cb_residues) != len(residues):
            cb_residues = residues

        pae_matrix = _align_pae(pae_matrix, len(residues))
        plddt = np.zeros(len(residues), dtype=np.float64)
        results = calc._calculate_scores(
            residues,
            cb_residues,
            chains,
            pae_matrix,
            plddt,
            plddt,
            file_type,
            {},
        )
        values = _chain_ipsae_values(
            results["ipsae_scores"]["ipsae_d0res_max"], binder_chain
        )
        return float(np.mean(values) if values else 0.0)
    except Exception as exc:
        print(f"WARNING: ipSAE calculation failed for {structure_path}: {exc}")
        return None


def compute_binder_iptm(pair_chains, binder_chain_idx: int) -> float:
    """Mean max pairwise ipTM between the binder and every other chain."""
    if not pair_chains or len(pair_chains) <= 1:
        return 0.0

    def _to_float(value):
        if hasattr(value, "detach"):
            value = value.detach().cpu().numpy()
        return float(np.asarray(value).reshape(-1)[0])

    values = []
    for i in range(len(pair_chains)):
        if i == binder_chain_idx:
            continue
        values.append(
            max(
                _to_float(pair_chains[binder_chain_idx][i]),
                _to_float(pair_chains[i][binder_chain_idx]),
            )
        )
    return float(np.mean(values) if values else 0.0)


def compute_ipsae_from_files(
    pae_file: Union[str, Path],
    structure_file: Union[str, Path],
    binder_chain: str = "A",
    pae_cutoff: float = DEFAULT_PAE_CUTOFF,
    dist_cutoff: float = DEFAULT_DIST_CUTOFF,
) -> Optional[float]:
    """ipSAE from PAE + structure files (AF2 JSON, AF3 JSON, or Boltz NPZ)."""
    try:
        calc = _ips_calculator()(pae_cutoff, dist_cutoff)
        calc._save_outputs = lambda *args, **kwargs: None
        results = calc.calculate(pae_file, structure_file)
        values = _chain_ipsae_values(
            results["ipsae_scores"]["ipsae_d0res_max"], binder_chain
        )
        return float(np.mean(values) if values else 0.0)
    except Exception as exc:
        print(f"WARNING: ipSAE file scoring failed: {exc}")
        return None


def resolve_ipsae_threshold(high_ipsae_threshold=None, high_iptm_threshold=None, default=0.8):
    """Prefer --high_ipsae_threshold; fall back to the deprecated iptm alias."""
    if high_ipsae_threshold is not None:
        return float(high_ipsae_threshold)
    if high_iptm_threshold is not None:
        return float(high_iptm_threshold)
    return float(default)
