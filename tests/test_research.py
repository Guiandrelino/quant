import json

import pandas as pd
import pytest

from equity_lab.data import load_csv, synthetic_data
from equity_lab.research import ResearchConfig, run_research


def test_csv_roundtrip_and_provenance(tmp_path):
    data = synthetic_data(sessions=700, assets=12)
    for name, frame in [
        ("prices", data.prices),
        ("volume", data.volume),
        ("membership", data.membership.astype(int)),
    ]:
        frame.to_csv(tmp_path / f"{name}.csv", index_label="date")
    pd.concat([data.benchmark, data.risk_free], axis=1).to_csv(
        tmp_path / "reference.csv", index_label="date"
    )
    metadata = {
        "source": "Synthetic fixture",
        "retrieved_at": "2026-01-01",
        "universe_method": "Synthetic historical entries",
        "limitations": "Not real data",
        "label": data.label,
        "price_convention": "total_return_index",
    }
    (tmp_path / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
    loaded = load_csv(tmp_path)
    pd.testing.assert_frame_equal(loaded.prices, data.prices.rename_axis("date"), check_freq=False)
    metadata["price_convention"] = "close"
    (tmp_path / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
    with pytest.raises(ValueError, match="total-return"):
        load_csv(tmp_path)


def test_end_to_end_artifacts(tmp_path):
    data = synthetic_data(sessions=800, assets=12)
    manifest = run_research(data, tmp_path, ResearchConfig(holdout_start="2020-01-01"))
    assert len(manifest["data_sha256"]) == 64
    assert (tmp_path / "report.html").stat().st_size > 1000
    assert "SYNTHETIC" in (tmp_path / "report.html").read_text(encoding="utf-8")
    summary = pd.read_csv(tmp_path / "metrics.csv")
    assert len(summary) == 18
    assert set(summary.period) == {"development", "holdout", "full"}
    assert summary.cagr.notna().all()
    rets = pd.read_csv(tmp_path / "returns.csv")
    assert rets.shape[1] == 7
    stress = pd.read_csv(tmp_path / "cost_sensitivity_holdout.csv")
    assert stress.cagr.is_monotonic_decreasing


def test_invalid_holdout(tmp_path):
    with pytest.raises(ValueError, match="126"):
        run_research(
            synthetic_data(sessions=650, assets=12),
            tmp_path,
            ResearchConfig(holdout_start="2030-01-01"),
        )
