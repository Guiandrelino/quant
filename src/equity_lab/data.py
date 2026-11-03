"""Strict input contracts and a deterministic, explicitly synthetic dataset."""

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class MarketData:
    prices: pd.DataFrame
    volume: pd.DataFrame
    membership: pd.DataFrame
    benchmark: pd.Series
    risk_free: pd.Series
    label: str

    def validate(self) -> None:
        p = self.prices
        if len(p) < 280 or p.shape[1] < 2:
            raise ValueError("At least 280 sessions and two assets are required")
        if not isinstance(p.index, pd.DatetimeIndex):
            raise ValueError("Dates must be a DatetimeIndex")
        if p.index.has_duplicates or not p.index.is_monotonic_increasing:
            raise ValueError("Dates must be unique and increasing")
        if p.columns.has_duplicates or p.isin([np.inf, -np.inf]).any().any():
            raise ValueError("Duplicate assets or infinite prices")
        if (p <= 0).any().any():
            raise ValueError("Observed prices must be positive")
        for name, frame in [("volume", self.volume), ("membership", self.membership)]:
            if not frame.index.equals(p.index) or not frame.columns.equals(p.columns):
                raise ValueError(f"{name}: axes must exactly match prices")
        if (
            self.volume.isna().any().any()
            or not np.isfinite(self.volume).all().all()
            or (self.volume < 0).any().any()
        ):
            raise ValueError("Volume must be finite, nonnegative traded BRL notional")
        if self.membership.isna().any().any() or not self.membership.isin([0, 1]).all().all():
            raise ValueError("Membership must contain only 0/1 without gaps")
        for name, series in [("benchmark", self.benchmark), ("risk_free", self.risk_free)]:
            if (
                not series.index.equals(p.index)
                or not np.isfinite(series).all()
                or (series <= -1).any()
            ):
                raise ValueError(f"{name}: aligned finite daily simple returns > -1 required")


def synthetic_data(seed: int = 42, sessions: int = 1800, assets: int = 40) -> MarketData:
    """Stylized correlated returns, NOT calibrated to Brazilian market performance."""
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2018-01-02", periods=sessions)
    market = rng.normal(0.00025, 0.012, sessions)
    sectors = rng.normal(0, 0.006, (sessions, 5))
    beta = rng.uniform(0.6, 1.4, assets)
    shocks = rng.normal(0, rng.uniform(0.008, 0.023, assets), (sessions, assets))
    returns = market[:, None] * beta + sectors[:, np.arange(assets) % 5] + shocks
    returns = np.clip(returns, -0.6, 0.6)
    columns = [f"SYN{i:03d}" for i in range(assets)]
    prices = pd.DataFrame(100 * np.cumprod(1 + returns, axis=0), dates, columns)
    volume = pd.DataFrame(rng.lognormal(17, 0.5, (sessions, assets)), dates, columns)
    membership = pd.DataFrame(True, dates, columns)
    # Historical entrants: unavailable prices before admission, no backward fill.
    for j in range(assets // 5):
        entry = 100 + 20 * j
        membership.iloc[:entry, j] = False
        prices.iloc[:entry, j] = np.nan
    return MarketData(
        prices,
        volume,
        membership,
        pd.Series(market, dates, name="benchmark"),
        pd.Series(0.0003, dates, name="risk_free"),
        "SYNTHETIC — NOT REAL MARKET DATA",
    )


def load_csv(directory: str | Path) -> MarketData:
    """Load wide CSVs; require provenance and an explicit return convention."""
    import json

    root = Path(directory)
    metadata = json.loads((root / "metadata.json").read_text(encoding="utf-8"))
    for key in ["source", "retrieved_at", "universe_method", "limitations", "label"]:
        if not metadata.get(key):
            raise ValueError(f"metadata.json requires nonempty {key}")
    if metadata.get("price_convention") != "total_return_index":
        raise ValueError("Prices must be total-return indices, including distributions")

    def frame(name: str) -> pd.DataFrame:
        return pd.read_csv(root / f"{name}.csv", index_col="date", parse_dates=True)

    reference = frame("reference")
    data = MarketData(
        frame("prices"),
        frame("volume"),
        frame("membership"),
        reference["benchmark"],
        reference["risk_free"],
        metadata["label"],
    )
    data.validate()
    return data
