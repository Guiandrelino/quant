"""Frozen experiment protocol, artifacts, provenance and portable HTML reporting."""

import hashlib
import json
import platform
import subprocess
from dataclasses import asdict, dataclass
from importlib.metadata import version
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px

from equity_lab.analytics import (
    block_bootstrap_active_mean,
    conditional_metrics,
    drawdown,
    metrics,
)
from equity_lab.backtest import STRATEGIES, BacktestConfig, run_backtest
from equity_lab.data import MarketData
from equity_lab.signals import compute_signals


@dataclass(frozen=True)
class ResearchConfig:
    holdout_start: str = "2023-01-01"
    evaluation_start: str | None = None
    min_volume: float = 5_000_000
    seed: int = 42


def _fingerprint(data: MarketData) -> str:
    digest = hashlib.sha256()
    for frame in [data.prices, data.volume, data.membership, data.benchmark, data.risk_free]:
        digest.update(pd.util.hash_pandas_object(frame, index=True).values.tobytes())
        if isinstance(frame, pd.DataFrame):
            digest.update("|".join(map(str, frame.columns)).encode())
    return digest.hexdigest()


def run_research(
    data: MarketData,
    output: str | Path,
    config: ResearchConfig | None = None,
    trading: BacktestConfig | None = None,
) -> dict:
    config = config or ResearchConfig()
    trading = trading or BacktestConfig()
    data.validate()
    if config.min_volume < 0:
        raise ValueError("min_volume must be nonnegative")
    signals = compute_signals(data, config.min_volume)
    results = {s: run_backtest(data, signals, s, trading) for s in STRATEGIES}
    # Common evaluation window avoids crediting a benchmark with a different history.
    eligible = signals.eligible.sum(axis=1).ge(int(np.ceil(1 / trading.cap)))
    first_signal = next(
        (
            i
            for i in range(len(eligible) - 2)
            if eligible.iloc[i] and eligible.index[i].month != eligible.index[i + 1].month
        ),
        None,
    )
    if first_signal is None:
        raise ValueError("No executable eligible universe")
    start = data.prices.index[first_signal + 2]
    if config.evaluation_start:
        start = max(start, pd.Timestamp(config.evaluation_start))
    rets = pd.DataFrame({s: r.daily["return"] for s, r in results.items()}).loc[start:]
    rets["benchmark"] = data.benchmark.loc[rets.index]
    split = pd.Timestamp(config.holdout_start)
    if (rets.index < split).sum() < 126 or (rets.index >= split).sum() < 126:
        raise ValueError("Require >=126 evaluation sessions on each side of holdout_start")
    root = Path(output)
    root.mkdir(parents=True, exist_ok=True)
    rets.to_csv(root / "returns.csv", index_label="date")
    summary = []
    intervals, regimes = [], []
    for name in rets:
        for period, mask in [
            ("development", rets.index < split),
            ("holdout", rets.index >= split),
            ("full", rets.index == rets.index),
        ]:
            r = rets.loc[mask, name]
            row = {
                "strategy": name,
                "period": period,
                **metrics(r, data.benchmark.loc[r.index], data.risk_free.loc[r.index]),
            }
            if name in results:
                daily = results[name].daily.loc[r.index]
                row["annualized_traded_notional"] = daily.traded_notional.mean() * 252
                row["mean_cash_weight"] = daily.cash_weight.mean()
            summary.append(row)
        intervals.append(
            {
                "strategy": name,
                **block_bootstrap_active_mean(
                    rets.loc[rets.index >= split, name],
                    data.benchmark.loc[rets.index[rets.index >= split]],
                    config.seed,
                ),
            }
        )
        regime = conditional_metrics(rets[name], data.benchmark, data.risk_free)
        regime["strategy"] = name
        regimes.append(regime)
    table = pd.DataFrame(summary)
    table.to_csv(root / "metrics.csv", index=False)
    pd.DataFrame(intervals).to_csv(root / "bootstrap_holdout.csv", index=False)
    pd.concat(regimes).to_csv(root / "regimes_ex_post.csv", index=False)
    for name, result in results.items():
        result.daily.to_csv(root / f"{name}_daily.csv", index_label="date")
        result.weights.to_csv(root / f"{name}_weights.csv", index_label="date")
        result.trades.to_csv(root / f"{name}_trades.csv", index=False)
    sensitivity = []
    for cost in [0, 10, 25, 50]:
        result = run_backtest(
            data,
            signals,
            "multifactor_inverse_vol",
            BacktestConfig(trading.selection, trading.cap, cost, 0),
        )
        r = result.daily["return"].loc[rets.index[rets.index >= split]]
        sensitivity.append(
            {
                "total_cost_bps_per_side": cost,
                **metrics(r, data.benchmark.loc[r.index], data.risk_free.loc[r.index]),
            }
        )
    pd.DataFrame(sensitivity).to_csv(root / "cost_sensitivity_holdout.csv", index=False)
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL, text=True
        ).strip()
        dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], text=True).strip())
    except (OSError, subprocess.CalledProcessError):
        commit, dirty = "unavailable", None
    manifest = {
        "dataset": data.label,
        "data_sha256": _fingerprint(data),
        "research": asdict(config),
        "trading": asdict(trading),
        "git_commit": commit,
        "git_dirty": dirty,
        "python": platform.python_version(),
        "packages": {p: version(p) for p in ["numpy", "pandas", "scipy", "plotly"]},
        "evaluation_start": str(start.date()),
        "evaluation_end": str(rets.index[-1].date()),
        "warning": "Synthetic data proves software behavior, not investment performance. Holdout is only genuinely out-of-sample if untouched by subsequent selection.",
    }
    (root / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    _report(rets, table, manifest, root)
    return manifest


def _report(returns: pd.DataFrame, table: pd.DataFrame, manifest: dict, root: Path) -> None:
    from html import escape

    charts = []
    for title, frame in [
        ("Crescimento de R$ 1 — janela comum", (1 + returns).cumprod()),
        ("Drawdown", returns.apply(drawdown)),
    ]:
        fig = px.line(frame, title=title, template="plotly_dark")
        charts.append(fig.to_html(full_html=False, include_plotlyjs=True if not charts else False))
    html = """<!doctype html><html lang='pt-BR'><meta charset='utf-8'>
    <title>Brazilian Equity Lab — Research</title><style>
    body{background:#101827;color:#e2e8f0;font:16px system-ui;max-width:1200px;margin:40px auto;padding:20px}
    h1{color:#38bdf8}table{border-collapse:collapse;font-size:13px}td,th{padding:8px;border:1px solid #334155}
    .warning{padding:18px;background:#713f12;border-radius:8px}a{color:#38bdf8}</style>
    <h1>Brazilian Equity Lab</h1><p>Factor investing · portfolio construction · risk research</p>"""
    html += (
        f"<div class='warning'>{escape(manifest['dataset'])}<br>{escape(manifest['warning'])}</div>"
    )
    html += "<h2>Hipótese</h2><p>A combinação de momentum 12–1 e baixa volatilidade melhora a relação risco-retorno após custos? Não presumimos superioridade.</p>"
    html += "".join(charts)
    html += "<h2>Avaliação holdout — parâmetros não escolhidos por este resultado</h2>"
    html += table[table.period == "holdout"].to_html(index=False, float_format=lambda x: f"{x:.4f}")
    html += "<h2>Interpretação e limites</h2><p>Compare seleção e ponderação com equal_universe. Avalie retorno ativo junto de tracking error, drawdown e turnover. Alpha é descritivo, sem inferência HAC. Custos lineares não capturam impacto ou capacidade. Regimes são ex-post. Leia docs/methodology.md antes de interpretar.</p>"
    html += f"<p>Fingerprint: <code>{escape(manifest['data_sha256'])}</code></p></html>"
    (root / "report.html").write_text(html, encoding="utf-8")
