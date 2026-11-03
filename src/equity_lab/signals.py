"""Signals use information through the observation date, never future prices."""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from equity_lab.data import MarketData


@dataclass(frozen=True)
class SignalSet:
    momentum: pd.DataFrame
    low_volatility: pd.DataFrame
    volatility: pd.DataFrame
    eligible: pd.DataFrame


def compute_signals(data: MarketData, min_volume: float = 5_000_000) -> SignalSet:
    prices = data.prices
    returns = prices.pct_change(fill_method=None)
    # 12-1 momentum: cumulative performance from t-252 through t-21.
    momentum = prices.shift(21) / prices.shift(252) - 1
    volatility = returns.rolling(126, min_periods=126).std(ddof=1) * np.sqrt(252)
    liquidity = data.volume.rolling(63, min_periods=63).mean()
    eligible = (
        data.membership.astype(bool)
        & prices.notna()
        & momentum.notna()
        & volatility.gt(0)
        & liquidity.ge(min_volume)
    )
    momentum = momentum.where(eligible)
    low_vol = (-volatility).where(eligible)
    return SignalSet(momentum, low_vol, volatility, eligible)


def factor_score(signals: SignalSet, strategy: str) -> pd.DataFrame:
    if strategy == "equal_universe":
        return signals.eligible.astype(float).where(signals.eligible)
    mom = signals.momentum.rank(axis=1, pct=True)
    low = signals.low_volatility.rank(axis=1, pct=True)
    if strategy == "momentum":
        return mom
    if strategy == "low_volatility":
        return low
    if strategy in {"multifactor", "multifactor_inverse_vol"}:
        return (mom + low) / 2
    raise ValueError(f"Unknown strategy: {strategy}")
