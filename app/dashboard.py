"""Read-only research viewer; does not tune parameters against the holdout."""

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from equity_lab.analytics import drawdown

st.set_page_config(page_title="Brazilian Equity Lab", page_icon="📊", layout="wide")
st.title("Brazilian Equity Lab")
st.caption("Factor investing · Portfolio construction · Risk research")
root = Path(st.sidebar.text_input("Diretório do experimento", "outputs/demo"))
if not (root / "manifest.json").exists():
    st.info("Execute `equity-lab demo` para gerar um experimento reproduzível.")
    st.stop()
manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
st.warning(
    f"Base: {manifest['dataset']}. Dados sintéticos não são evidência de retorno de mercado."
)
returns = pd.read_csv(root / "returns.csv", index_col="date", parse_dates=True)
summary = pd.read_csv(root / "metrics.csv")
selected = st.sidebar.multiselect("Carteiras", list(returns), default=list(returns))
period = st.sidebar.radio("Janela", ["holdout", "development", "full"])
split = pd.Timestamp(manifest["research"]["holdout_start"])
mask = returns.index >= split if period == "holdout" else returns.index < split
view = returns if period == "full" else returns.loc[mask]
if not selected:
    st.info("Selecione pelo menos uma carteira.")
    st.stop()
view = view[selected]
performance, risk, implementation, audit = st.tabs(
    ["Desempenho", "Risco", "Implementação", "Auditoria"]
)
with performance:
    st.plotly_chart(px.line((1 + view).cumprod(), title="Crescimento de R$ 1"), width="stretch")
    st.dataframe(
        summary[(summary.period == period) & summary.strategy.isin(selected)], hide_index=True
    )
    st.caption(
        "Sharpe usa retorno excedente ao caixa. CAGR e volatilidade anualizados por 252 sessões."
    )
with risk:
    st.plotly_chart(px.area(view.apply(drawdown), title="Drawdown"), width="stretch")
    rolling = view.rolling(126).std() * 252**0.5
    st.plotly_chart(px.line(rolling, title="Volatilidade móvel — 126 sessões"), width="stretch")
    st.subheader("Incerteza do retorno ativo — holdout")
    st.dataframe(pd.read_csv(root / "bootstrap_holdout.csv"), hide_index=True)
    st.caption("Bootstrap em blocos; intervalo descritivo, sem correção por múltiplos testes.")
with implementation:
    strategy = st.selectbox("Carteira para inspeção", [s for s in returns if s != "benchmark"])
    weights = pd.read_csv(root / f"{strategy}_weights.csv", index_col="date", parse_dates=True)
    st.plotly_chart(
        px.bar(weights.iloc[-1].sort_values(ascending=False), title="Pesos no último fechamento"),
        width="stretch",
    )
    st.subheader("Sensibilidade a custos — multifatorial inverso da volatilidade")
    st.dataframe(pd.read_csv(root / "cost_sensitivity_holdout.csv"), hide_index=True)
    st.subheader("Regimes ex-post — explicação, não regra de alocação")
    regimes = pd.read_csv(root / "regimes_ex_post.csv")
    st.dataframe(regimes[regimes.strategy == strategy], hide_index=True)
    st.download_button("Baixar retornos", returns.to_csv().encode(), "returns.csv", "text/csv")
with audit:
    st.json(manifest)
    st.markdown(
        "Os pesos podem ultrapassar o limite entre rebalanceamentos por drift. Custos são lineares e não modelam impacto. Não há promessa de capacidade ou recomendação de investimento."
    )
