# Publicação e apresentação

## Texto sugerido — versão honesta para a demo atual

Desenvolvi o Brazilian Equity Lab, um framework de pesquisa quantitativa voltado à seleção de ações e construção de carteiras.

A pergunta de investimento é simples: combinar momentum e baixa volatilidade melhora a relação risco-retorno após custos? A implementação foi pensada para tornar essa pergunta auditável — não para fabricar um backtest atraente.

O projeto inclui:
• estratégias fatoriais isoladas e combinadas;
• execução posterior ao sinal e pesos com drift;
• limites de concentração, custos e turnover;
• avaliação cronológica, métricas de risco e bootstrap em blocos;
• dashboard, relatório HTML, testes automatizados e rastreabilidade dos experimentos.

Uma escolha importante: a demonstração pública utiliza dados sintéticos, identificados explicitamente. Ela valida a engenharia, não comprova retorno no mercado brasileiro. A integração com dados reais exige universo histórico e tratamento adequado de eventos corporativos e deslistagens.

Busco oportunidades em gestão e análise de investimentos, unindo Python, pesquisa quantitativa e comunicação de risco.

Código: [inserir URL real do repositório]

#QuantitativeFinance #AssetManagement #Python #Investimentos #GestaoDeRisco

## Carrossel sugerido

1. Problema de investimento e hipótese econômica.
2. Linha do tempo: sinal → execução → retorno.
3. Comparação de estratégias e controles de risco.
4. Dashboard com marca **DEMONSTRAÇÃO SINTÉTICA** visível.
5. Limitações e o que falta para uma conclusão investível.
6. Repositório e contato.

Não publique Sharpe/retorno da simulação como resultado B3. Não anuncie auditoria externa, validação institucional, alpha consistente ou execução em produção. Depois de integrar dados reais, apresente a origem, limitações e resultado — mesmo se negativo.

## Roteiro de entrevista

- Por que começar com fatores interpretáveis em vez de deep learning?
- Como a carteira é financiada, quando negocia e quando começa a ganhar retorno?
- Como distinguir desempenho da seleção e da ponderação?
- Por que não usar a composição atual do índice no passado?
- Por que inverso da volatilidade não é paridade de risco?
- O que seu bootstrap permite concluir, e o que não permite?
- Como custos, concentração e capacidade mudariam uma recomendação?
- Qual evidência faria você abandonar a hipótese?
