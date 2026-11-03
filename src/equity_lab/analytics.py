"""Performance, active risk and dependence-aware uncertainty estimates."""

import numpy as np
import pandas as pd


def drawdown(returns: pd.Series) -> pd.Series:
    nav = (1 + returns).cumprod()
    return nav / nav.cummax().clip(lower=1) - 1


def metrics(returns: pd.Series, benchmark: pd.Series, risk_free: pd.Series) -> dict:
    aligned = pd.concat([returns, benchmark, risk_free], axis=1).dropna()
    if len(aligned) < 2:
        raise ValueError("At least two aligned return observations required")
    r, b, rf = (aligned.iloc[:, i] for i in range(3))
    excess, active = r - rf, r - b
    vol = r.std(ddof=1) * np.sqrt(252)
    te = active.std(ddof=1) * np.sqrt(252)
    ex_vol = excess.std(ddof=1) * np.sqrt(252)
    downside = np.sqrt(np.mean(np.minimum(excess, 0) ** 2)) * np.sqrt(252)
    q = r.quantile(0.05)
    dd = drawdown(r)
    underwater = dd < -1e-12
    durations = underwater.groupby((~underwater).cumsum()).cumsum()
    x = b - rf
    beta = excess.cov(x) / x.var() if x.var() > 0 else np.nan
    return {
        "cagr": float(np.expm1(np.log1p(r).sum() * 252 / len(r))),
        "volatility": float(vol),
        "sharpe": float(excess.mean() * 252 / ex_vol) if ex_vol > 1e-12 else np.nan,
        "sortino": float(excess.mean() * 252 / downside) if downside > 1e-12 else np.nan,
        "max_drawdown": float(dd.min()),
        "longest_underwater_sessions": int(durations.max()),
        "daily_var_95_loss": float(-q),
        "daily_es_95_loss": float(-r[r <= q].mean()),
        "tracking_error": float(te),
        "information_ratio": float(active.mean() * 252 / te) if te > 1e-12 else np.nan,
        "beta": float(beta),
        "capm_alpha_arithmetic": float((excess.mean() - beta * x.mean()) * 252),
        "observations": len(r),
    }


def block_bootstrap_active_mean(
    returns: pd.Series, benchmark: pd.Series, seed: int = 42, samples: int = 1000, block: int = 21
) -> dict:
    """Circular moving-block bootstrap of annualized arithmetic active mean.

    Descriptive percentile interval; not corrected for strategy selection/multiple tests.
    """
    active = (returns - benchmark).dropna().to_numpy()
    if len(active) < block or samples < 2:
        raise ValueError("Insufficient observations or bootstrap replications")
    rng = np.random.default_rng(seed)
    starts = rng.integers(0, len(active), (samples, int(np.ceil(len(active) / block))))
    indices = (starts[..., None] + np.arange(block)) % len(active)
    draws = active[indices.reshape(samples, -1)[:, : len(active)]].mean(axis=1) * 252
    low, high = np.quantile(draws, [0.025, 0.975])
    return {
        "active_mean_annualized": float(active.mean() * 252),
        "ci_95_low": float(low),
        "ci_95_high": float(high),
        "bootstrap_samples": samples,
        "block_sessions": block,
    }


def conditional_metrics(
    returns: pd.Series, benchmark: pd.Series, risk_free: pd.Series
) -> pd.DataFrame:
    """Ex-post explanatory regimes, NOT an allocation rule or causal inference."""
    frame = pd.concat({"return": returns, "benchmark": benchmark, "rf": risk_free}, axis=1).dropna()
    monthly = (1 + frame).resample("ME").prod() - 1
    monthly["market_regime"] = np.where(monthly.benchmark >= 0, "market_up", "market_down")
    # Rate changes compare monthly average daily cash rates, not compounded month totals.
    mean_rate = frame.rf.resample("ME").mean()
    change = mean_rate.diff()
    monthly["rate_regime"] = np.where(
        change.abs() < 1e-10, "rate_flat", np.where(change > 0, "rate_rising", "rate_falling")
    )
    monthly.loc[change.isna(), "rate_regime"] = "unknown"
    rows = []
    for kind in ["market_regime", "rate_regime"]:
        for regime, subset in monthly.groupby(kind):
            rows.append(
                {
                    "dimension": kind,
                    "regime": regime,
                    "months": len(subset),
                    "mean_monthly_return": subset["return"].mean(),
                    "mean_monthly_active": (subset["return"] - subset.benchmark).mean(),
                }
            )
    return pd.DataFrame(rows)
