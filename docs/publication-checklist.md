# Checklist de publicação

## Material pronto no repositório

- `docs/assets/linkedin-cover.png`: capa 1200 × 627, com identificação sintética visível.
- `docs/linkedin.md`: texto revisado para LinkedIn e roteiro de apresentação.
- `scripts/build_publication.py`: gera relatório público e capa.
- `.github/workflows/pages.yml`: publica relatório estático pelo GitHub Pages.
- `README.md`: apresentação, instalação, metodologia e limitações.

## Publicar no GitHub

1. Crie um repositório público vazio chamado `brazilian-equity-lab`, sem README automático.
2. Use a URL fornecida pelo GitHub nos comandos abaixo. Não há remote configurado neste projeto.

```bash
git remote add origin URL_REAL_DO_REPOSITORIO
git push -u origin main
```

O histórico foi reorganizado em commits menores a pedido do autor. Não foi inventada uma cronologia de desenvolvimento; timestamps refletem a reorganização. A tag local `backup/pre-publication-history` preserva o histórico anterior. Não é necessário publicá-la.

3. Em **Settings → Pages → Build and deployment**, selecione **GitHub Actions**.
4. Execute o workflow **Publish research demo** se necessário. Aguarde sucesso; o ambiente `github-pages` informará o endereço real da demonstração.
5. Em **About**, inclua a descrição abaixo e a URL da demo:

> Framework de pesquisa quantitativa: fatores de ações, construção de carteiras, backtest auditável e risco. Demonstração sintética; sem alegação de performance real.

Topics sugeridos: `quantitative-finance`, `portfolio-management`, `factor-investing`, `python`, `backtesting`, `risk-management`.

## Publicar no LinkedIn

1. Abra a demo publicada e confira o aviso sintético.
2. Use `docs/assets/linkedin-cover.png` como imagem da publicação.
3. Copie o texto de `docs/linkedin.md` e substitua o único placeholder pela URL real do repositório.
4. Acrescente a URL da demo gerada pelo Pages.
5. Confira que nenhum retorno sintético é apresentado como performance B3.
6. Adicione o repositório à seção **Destaques** do perfil.

Não há necessidade de atribuir vínculo ao Itaú ou a outra instituição. O projeto demonstra competências; não é trabalho realizado para uma gestora.

## Regeneração local

```powershell
.\.venv\Scripts\python.exe scripts/build_publication.py
```

O relatório fica em `site/index.html` e é autocontido. `site/` é ignorado pelo Git; o CI gera a versão publicada a partir do commit enviado. O manifest da demonstração preserva a proveniência desse build.

## Pendência deliberada

A infraestrutura está pronta para ser apresentada como **projeto de engenharia e pesquisa exploratória**. Uma publicação com conclusões de investimento exige dados reais auditados e um novo relatório. Não substitua essa etapa por números sintéticos.
