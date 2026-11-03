# Protocolo de pesquisa e limitações

## Hipótese e escopo

Estratégia long-only de ações brasileiras: testar se momentum e baixa volatilidade, isolados e combinados, melhoram o perfil de retorno e risco após custos. O software não presume que os fatores funcionam. Não é um sistema de execução nem recomendação de investimento.

O dataset padrão é **inteiramente sintético**, com calendário de dias úteis genérico (não calendário B3), choques correlacionados e entradas históricas. Não foi calibrado para gerar alpha. Não há evidência sobre o mercado brasileiro sem uma execução com dados reais adequados.

## Contrato dos dados

Leia [data-contract.md](data-contract.md). A matriz de membership representa elegibilidade histórica conhecida no fechamento, não a composição atual retroagida. Preços devem representar índices de retorno total em moeda local. Volume é notional negociado em BRL, não quantidade de ações multiplicada por um preço ajustado retrospectivamente.

A validação estrutural não comprova ausência de viés de sobrevivência, disponibilidade point-in-time ou direitos de redistribuição. Essas propriedades devem ser auditadas na fonte. Falta de retorno em um ativo mantido gera erro, nunca retorno zero ou preenchimento silencioso. Saídas devem incluir evento terminal e retorno econômico correto; se a fonte não os fornece, interrompa a pesquisa. Uma variação extrema não é automaticamente erro: não removemos crashes por winsorization.

## Sinais e universo

- Momentum: `P[t-21] / P[t-252] - 1`, convenção 12–1 por sessões.
- Volatilidade: desvio padrão amostral de 126 retornos diários completos, anualizado por sqrt(252).
- Liquidez: média de 63 sessões de notional negociado, mínimo padrão R$ 5 milhões/dia.
- Elegibilidade: membership histórico, preço observado e ambos os sinais válidos. Universo comum permite comparação controlada entre fatores, embora imponha o histórico de momentum também à baixa volatilidade.
- Scores: ranks percentuais cross-section; multifator = média dos ranks de momentum e volatilidade negativa. Empates finais usam ordem estável das colunas.

## Construção de carteiras

Seleção dos 30% melhores scores, arredondados para cima, com pelo menos ceil(1/cap) ativos para viabilidade. Limite padrão de 15% por ação no rebalanceamento. Pesos iguais ou inverso da volatilidade com water-filling proporcional. Inverso da volatilidade **não é equal risk contribution**: correlações não entram nessa regra.

Com universo insuficiente para o limite, o alvo é caixa. Não relaxamos o cap silenciosamente. O limite pode ser excedido entre rebalanceamentos por valorização relativa. Não há limite setorial nem alegação de neutralidade setorial. Para produção, adicionar classificação histórica, exposição a fatores, capacidade e restrições específicas do mandato.

## Linha do tempo e contabilidade

1. Sinal observado no fechamento da última sessão de cada mês.
2. Execução no fechamento da sessão seguinte; o retorno desse dia ainda é da carteira anterior.
3. Nova exposição começa a render na sessão posterior à execução.
4. Pesos derivam diariamente com os retornos; caixa rende a taxa livre de risco fornecida.
5. Notional negociado = soma dos valores absolutos de alvo menos peso pré-negociação, em fração do patrimônio. Compra e venda contam separadamente; não usamos metade desse valor.
6. Custo = notional negociado × (comissão + slippage)/10.000. Uma troca completa da carteira custa sobre 200% do patrimônio; aporte inicial sobre 100%.
7. Retorno líquido = `(1 + retorno bruto) * (1 - custo) - 1`.

**Aproximação explícita:** alvos são proporções do patrimônio pós-custo, enquanto o cálculo do notional usa patrimônio pré-custo. A diferença é de ordem pequena para custos baixos; não há solução implícita exata dos fluxos de caixa. O modelo não contempla impostos, aluguel, emolumentos específicos, leilões, lotes, impacto não linear ou impossibilidade de negociar um ativo suspenso. Membership afeta o próximo sinal mensal, não força venda intramês.

## Avaliação

Janela comum começa após a primeira execução elegível, excluindo warm-up. Desenvolvimento e holdout cronológicos exigem pelo menos 126 sessões cada; padrão de holdout: 2023-01-01. O primeiro custo de entrada pode anteceder a janela comum; os diários completos preservam esse custo para auditoria.

O holdout só é genuinamente fora da amostra se não tiver sido usado em decisões posteriores. Repetir análises e ajustar parâmetros com base nele o transforma em desenvolvimento. A comparação entre cinco estratégias é pesquisa exploratória, não validação de um vencedor selecionado. Não há otimização automática, teste de superioridade ou correção por múltiplos testes.

- CAGR geométrico; volatilidade amostral anualizada.
- Sharpe com excesso diário ao caixa e desvio padrão desse excesso.
- Sortino com raiz da média de quadrados dos excessos negativos (MAR = caixa).
- Drawdown inclui patrimônio inicial igual a 1; duração reporta maior sequência submersa em sessões, incluindo episódio ainda aberto.
- VaR/ES históricos diários a 95%, reportados em convenção de perda; podem ser negativos em amostras de ganhos.
- Tracking error e information ratio usam retorno ativo aritmético.
- Beta/alpha CAPM são descritivos; alpha aritmético, sem teste de significância ou erros HAC.
- Bootstrap circular em blocos de 21 sessões, 1.000 amostras, seed fixa, intervalo percentil de 95% da média ativa aritmética anualizada no holdout. Sensível à escolha do bloco; não prova causalidade nem persistência.
- Sensibilidade de custos: 0/10/25/50 bps por lado para multifatorial inverso da volatilidade. É stress, não calibração.

Regimes usam sinal do retorno mensal do benchmark e mudança da média mensal da taxa diária de caixa. São **ex-post**, podem incluir mês parcial e não são datas oficiais de ciclos do Copom. Caixa constante da demo não permite estudar ciclos reais de juros.

## Reprodutibilidade e extensões

Manifest inclui fingerprint dos dados, parâmetros, versões de dependências, Python, commit e estado dirty. Não confundir hash de dados com checksum dos arquivos originais. CSVs preservam trilhas diárias, pesos e decisões.

Antes de afirmar evidência investível: dados reais PIT e deslistadas; calendário B3; auditoria de eventos corporativos; execução com restrições; classificação setorial histórica; benchmark adequado ao mandato; testes de subperíodos e estabilidade de parâmetros em desenvolvimento; avaliação final congelada; análise de capacidade. O projeto implementa a infraestrutura e os experimentos descritos, não essas garantias institucionais.
