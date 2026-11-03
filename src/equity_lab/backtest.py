"""Close-to-close self-financing accounting with drift and delayed execution."""

from dataclasses import dataclass

import pandas as pd

from equity_lab.data import MarketData
from equity_lab.portfolio import target_weights
from equity_lab.signals import SignalSet, factor_score

STRATEGIES = (
    "equal_universe",
    "momentum",
    "low_volatility",
    "multifactor",
    "multifactor_inverse_vol",
)


@dataclass(frozen=True)
class BacktestConfig:
    selection: float = 0.3
    cap: float = 0.15
    commission_bps: float = 5.0
    slippage_bps: float = 5.0

    def __post_init__(self) -> None:
        if not 0 < self.selection <= 1 or not 0 < self.cap <= 1:
            raise ValueError("selection and cap must be in (0, 1]")
        if not 0 <= self.commission_bps + self.slippage_bps < 1000:
            raise ValueError("Combined transaction cost must be in [0, 1000) bps")
        if min(self.commission_bps, self.slippage_bps) < 0:
            raise ValueError("Negative costs are not allowed")


@dataclass
class BacktestResult:
    daily: pd.DataFrame
    weights: pd.DataFrame
    trades: pd.DataFrame
    strategy: str


def run_backtest(
    data: MarketData, signals: SignalSet, strategy: str, config: BacktestConfig | None = None
) -> BacktestResult:
    """Signal at month-end t, trade at t+1 close, earn new exposure from t+2.

    Costs are charged per BRL bought OR sold, based on pre-cost NAV. Post-trade
    allocation is scaled by remaining NAV (small-cost approximation, documented).
    Cash earns the supplied daily risk-free return. Missing held returns fail closed.
    """
    config = config or BacktestConfig()
    data.validate()
    score = factor_score(signals, strategy)
    prices = data.prices
    returns = prices.pct_change(fill_method=None)
    dates = prices.index
    # Last observation is not a signal unless a following session exists.
    month = dates.to_period("M")
    execution = {i + 1: i for i in range(len(dates) - 1) if month[i] != month[i + 1]}
    w = pd.Series(0.0, index=prices.columns)
    rows, history, trades = [], [], []
    cost_rate = (config.commission_bps + config.slippage_bps) / 10_000
    for i, date in enumerate(dates):
        r = returns.iloc[i]
        if (w.gt(1e-12) & r.isna()).any():
            missing = list(w.index[w.gt(1e-12) & r.isna()])
            raise ValueError(
                f"Missing return on held assets at {date}: {missing}; supply delisting/terminal returns"
            )
        cash = max(0.0, 1 - w.sum())
        gross = float(w @ r.fillna(0) + cash * data.risk_free.iloc[i])
        growth = 1 + gross
        if growth <= 0:
            raise ValueError("Portfolio insolvency")
        drifted = w * (1 + r.fillna(0)) / growth
        turnover = cost = 0.0
        w = drifted
        if i in execution:
            signal_i = execution[i]
            target = target_weights(
                score.iloc[signal_i],
                signals.volatility.iloc[signal_i],
                strategy,
                config.selection,
                config.cap,
            )
            delta = target - drifted
            turnover = float(delta.abs().sum())
            cost = turnover * cost_rate
            for ticker in delta.index[delta.abs() > 1e-10]:
                trades.append(
                    {
                        "date": date,
                        "signal_date": dates[signal_i],
                        "ticker": ticker,
                        "weight_change": delta[ticker],
                        "target_weight": target[ticker],
                    }
                )
            w = target
        net = growth * (1 - cost) - 1
        rows.append(
            {
                "date": date,
                "return": net,
                "gross_return": gross,
                "traded_notional": turnover,
                "cost_fraction": cost,
                "cash_weight": max(0.0, 1 - w.sum()),
                "concentration_hhi": float(w @ w),
            }
        )
        history.append(w.to_numpy().copy())
    return BacktestResult(
        pd.DataFrame(rows).set_index("date"),
        pd.DataFrame(history, index=dates, columns=prices.columns),
        pd.DataFrame(
            trades, columns=["date", "signal_date", "ticker", "weight_change", "target_weight"]
        ),
        strategy,
    )
