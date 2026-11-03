"""Long-only portfolio construction with explicit feasibility checks."""

import numpy as np
import pandas as pd


def capped_weights(raw: pd.Series, cap: float) -> pd.Series:
    """Proportional water-filling; fails rather than silently violating the cap."""
    if not 0 < cap <= 1 or raw.empty or not np.isfinite(raw).all() or (raw <= 0).any():
        raise ValueError("Positive finite scores and cap in (0, 1] required")
    if len(raw) * cap < 1 - 1e-10:
        raise ValueError("Infeasible cap: insufficient selected assets")
    result = pd.Series(0.0, index=raw.index)
    free = pd.Series(True, index=raw.index)
    while free.any():
        proposal = raw[free] / raw[free].sum() * (1 - result.sum())
        binding = proposal > cap + 1e-12
        if not binding.any():
            result.loc[proposal.index] = proposal
            break
        fixed = proposal.index[binding]
        result.loc[fixed] = cap
        free.loc[fixed] = False
    return result


def target_weights(
    score: pd.Series,
    volatility: pd.Series,
    strategy: str,
    selection: float = 0.3,
    cap: float = 0.15,
) -> pd.Series:
    valid = score.dropna().sort_values(ascending=False, kind="stable")
    output = pd.Series(0.0, index=score.index)
    if valid.empty:
        return output  # cash until a historical universe is available
    minimum = int(np.ceil(1 / cap))
    if len(valid) < minimum:
        return output  # explicit cash fallback, never relax the risk limit
    n = (
        len(valid)
        if strategy == "equal_universe"
        else max(minimum, int(np.ceil(len(valid) * selection)))
    )
    chosen = valid.index[:n]
    raw = 1 / volatility.loc[chosen] if strategy.endswith("inverse_vol") else pd.Series(1.0, chosen)
    output.loc[chosen] = capped_weights(raw, cap)
    return output
