# Integração de dados reais

O modo real é deliberadamente independente de fornecedor. Não baixamos os constituintes atuais e fingimos que formavam o universo de 2018. Sem fonte histórica adequada, use a demo apenas para engenharia.

## Arquivos em um diretório local

Todas as datas em ISO `YYYY-MM-DD`, sem timezone; ordenadas, únicas e com os mesmos eixos. Não inclua colunas extras nos painéis. Decimais usam ponto.

`prices.csv` — índices de retorno total positivos; vazio permitido antes da listagem. Deve incorporar distribuições e eventos corporativos, incluindo retorno econômico terminal de saída. Não use preço de fechamento simples.

```csv
date,ATIVO_A,ATIVO_B
2020-01-02,100.0,100.0
2020-01-03,101.0,99.0
```

`volume.csv` — mesmas colunas/datas, notional em BRL não negativo e sem ausências. Zero para sessões sem negociação; use fonte de volume original, não preços total-return para converter quantidade.

`membership.csv` — mesmas colunas/datas; 0 ou 1, conhecido historicamente na data. Inclua empresas que deixaram o mercado. Não remova um ativo do painel quando deixa o universo.

`reference.csv` — duas colunas: `benchmark` e `risk_free`, **retornos simples diários**, não níveis ou taxa anual. Primeira linha pode usar zero se documentado. Benchmark deve ser de retorno total e compatível com o mandato; não use uma série de preço como retorno. CDI diário ou outra referência apropriada para caixa; não converta Selic meta em CDI histórico sem ressalva.

```csv
date,benchmark,risk_free
2020-01-02,0.003,0.0002
2020-01-03,-0.002,0.0002
```

`metadata.json`:

```json
{
  "label": "Pesquisa exploratória B3 — fornecedor e período",
  "source": "Nome do fornecedor, identificador da extração e licença",
  "retrieved_at": "2026-01-01T12:00:00Z",
  "price_convention": "total_return_index",
  "universe_method": "Regra histórica de inclusão e data efetiva de disponibilidade",
  "limitations": "Descrever ausências, cobertura de deslistadas, revisões e viés residual"
}
```

Os fragmentos ilustram schema, não constituem dataset executável: são necessárias pelo menos 280 sessões para validação e janelas de avaliação suficientes dos dois lados do holdout.

## Execução

```bash
equity-lab run --data data/raw/meu_dataset --holdout-start 2023-01-01 --output outputs/real
```

Nunca publique dados de terceiros sem licença. Os arquivos brutos são ignorados pelo Git. A responsabilidade de certificar o caráter point-in-time continua sendo da pesquisa: metadados preenchidos não o garantem.
