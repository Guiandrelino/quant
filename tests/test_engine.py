from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

from equity_lab.analytics import block_bootstrap_active_mean, drawdown, metrics
from equity_lab.backtest import BacktestConfig, run_backtest
from equity_lab.data import synthetic_data
from equity_lab.portfolio import capped_weights
from equity_lab.signals import compute_signals


@pytest.fixture(scope="module")
def market():
    return synthetic_data(sessions=650, assets=15)


def test_synthetic_reproducible(market):
    pd.testing.assert_frame_equal(market.prices, synthetic_data(sessions=650, assets=15).prices)
    market.validate()


def test_contract_rejects_unsorted(market):
    with pytest.raises(ValueError, match="increasing"):
        replace(market, prices=market.prices.iloc[::-1]).validate()


def test_contract_rejects_bad_membership(market):
    member = market.membership.astype(float)
    member.iloc[0, 0] = 0.5
    with pytest.raises(ValueError, match="Membership"):
        replace(market, membership=member).validate()


def test_momentum_exact(market):
    s = compute_signals(market, 0)
    i, j = 400, 10
    assert s.momentum.iloc[i, j] == pytest.approx(
        market.prices.iloc[i - 21, j] / market.prices.iloc[i - 252, j] - 1
    )


def test_no_future_dependency(market):
    altered = market.prices.copy()
    altered.iloc[450:] *= np.linspace(1, 3, len(altered) - 450)[:, None]
    original = compute_signals(market)
    future = compute_signals(replace(market, prices=altered))
    pd.testing.assert_frame_equal(original.momentum.iloc[:450], future.momentum.iloc[:450])
    a = run_backtest(market, original, "multifactor")
    b = run_backtest(replace(market, prices=altered), future, "multifactor")
    pd.testing.assert_frame_equal(a.daily.iloc[:450], b.daily.iloc[:450])
    pd.testing.assert_frame_equal(a.weights.iloc[:450], b.weights.iloc[:450])


def test_capped_weights():
    raw = pd.Series([100.0, 3, 2, 1, 1, 1, 1, 1])
    weights = capped_weights(raw, 0.15)
    assert weights.sum() == pytest.approx(1)
    assert weights.max() <= 0.15 + 1e-12
    assert weights.min() > 0
    with pytest.raises(ValueError, match="Infeasible"):
        capped_weights(raw.iloc[:2], 0.15)


def test_execution_and_drift(market):
    result = run_backtest(market, compute_signals(market), "multifactor")
    assert (result.weights.sum(axis=1) <= 1 + 1e-12).all()
    assert (result.weights >= -1e-12).all().all()
    for date, group in result.trades.groupby("date"):
        signal = pd.Timestamp(group.signal_date.iloc[0])
        assert market.prices.index.get_loc(date) == market.prices.index.get_loc(signal) + 1
        assert date.month != signal.month
        assert result.weights.loc[date].max() <= 0.15 + 1e-12
    first = result.trades.date.min()
    # Execution-day return still comes from prior cash, less transaction cost.
    gross = result.daily.loc[first, "gross_return"]
    assert gross == pytest.approx(market.risk_free.loc[first])
    assert result.daily.loc[first, "traded_notional"] == pytest.approx(1)
    following = market.prices.index[market.prices.index.get_loc(first) + 1]
    r = market.prices.pct_change(fill_method=None).loc[following].fillna(0)
    assert result.daily.loc[following, "gross_return"] == pytest.approx(
        result.weights.loc[first] @ r
    )


def test_costs_reduce_wealth(market):
    signals = compute_signals(market)
    free = run_backtest(
        market, signals, "multifactor", BacktestConfig(commission_bps=0, slippage_bps=0)
    )
    paid = run_backtest(
        market, signals, "multifactor", BacktestConfig(commission_bps=30, slippage_bps=0)
    )
    assert (1 + paid.daily["return"]).prod() < (1 + free.daily["return"]).prod()
    pd.testing.assert_frame_equal(paid.weights, free.weights)


def test_missing_held_return_fails_closed(market):
    signals = compute_signals(market)
    result = run_backtest(market, signals, "multifactor")
    first = result.trades.date.min()
    ticker = result.weights.loc[first].idxmax()
    i = market.prices.index.get_loc(first) + 1
    prices = market.prices.copy()
    prices.loc[prices.index[i], ticker] = np.nan
    with pytest.raises(ValueError, match="Missing return"):
        run_backtest(replace(market, prices=prices), signals, "multifactor")


def test_accounting_identity(market):
    result = run_backtest(market, compute_signals(market), "momentum")
    expected = (1 + result.daily.gross_return) * (1 - result.daily.cost_fraction) - 1
    np.testing.assert_allclose(result.daily["return"], expected)


def test_drawdown_includes_initial_nav():
    r = pd.Series([-0.1, 0.1, -0.2])
    np.testing.assert_allclose(drawdown(r), [-0.1, -0.01, -0.208])


def test_metrics_and_bootstrap():
    rng = np.random.default_rng(1)
    r = pd.Series(rng.normal(0.001, 0.01, 252))
    b = r * 0.8
    result = metrics(r, b, r * 0)
    assert result["cagr"] == pytest.approx((1 + r).prod() - 1)
    assert result["max_drawdown"] <= 0
    a = block_bootstrap_active_mean(r, b)
    assert a == block_bootstrap_active_mean(r, b)
    assert a["ci_95_low"] <= a["ci_95_high"]


@pytest.mark.parametrize("kwargs", [{"cap": 0}, {"selection": 2}, {"commission_bps": -1}])
def test_bad_config(kwargs):
    with pytest.raises(ValueError):
        BacktestConfig(**kwargs)
