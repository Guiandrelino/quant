"""Gera a imagem do post. Dependência opcional: python -m pip install Pillow."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
WIDTH, HEIGHT = 1600, 1400
NAVY = "#172D46"
INK = "#26394C"
MUTED = "#5E6D7A"
GOLD = "#A58A55"
LINE = "#D5DCE2"
image = Image.new("RGB", (WIDTH, HEIGHT), "#F5F6F7")
draw = ImageDraw.Draw(image)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    names = ["arialbd.ttf", "DejaVuSans-Bold.ttf"] if bold else ["arial.ttf", "DejaVuSans.ttf"]
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    raise RuntimeError("Instale Arial ou DejaVu Sans para gerar a imagem.")


def text(x: int, y: int, value: str, size: int, color: str, bold: bool = False) -> None:
    draw.text((x, y), value, font=font(size, bold), fill=color)


def arrow(points: list[tuple[int, int]]) -> None:
    draw.line(points, fill="#8A98A5", width=3)
    x, y = points[-1]
    px, py = points[-2]
    if x > px:
        head = [(x, y), (x - 10, y - 6), (x - 10, y + 6)]
    elif x < px:
        head = [(x, y), (x + 10, y - 6), (x + 10, y + 6)]
    else:
        head = [(x, y), (x - 6, y - 10), (x + 6, y - 10)]
    draw.polygon(head, fill="#8A98A5")


def card(x: int, y: int, number: str, title: str, subtitle: str, lines: list[str]) -> None:
    draw.rectangle((x, y, x + 460, y + 255), fill="white", outline=LINE, width=2)
    draw.rectangle((x, y, x + 460, y + 4), fill=NAVY)
    text(x + 24, y + 24, number, 24, GOLD, True)
    text(x + 72, y + 21, title, 29, NAVY, True)
    text(x + 24, y + 72, subtitle, 21, MUTED)
    draw.line((x + 24, y + 110, x + 436, y + 110), fill=LINE, width=1)
    for i, line in enumerate(lines):
        text(x + 24, y + 132 + i * 34, line, 23, INK)


# Cabeçalho editorial: marca, assunto e escopo, sem detalhes de implementação.
draw.rectangle((0, 0, WIDTH, 12), fill=NAVY)
text(60, 49, "BRAZILIAN EQUITY LAB", 23, NAVY, True)
text(60, 104, "Arquitetura de pesquisa quantitativa", 49, NAVY, True)
text(
    60,
    174,
    "Estratégias fatoriais em ações brasileiras | Processo de análise e avaliação",
    26,
    MUTED,
)
draw.line((60, 232, 1540, 232), fill=LINE, width=2)
draw.line((60, 232, 185, 232), fill=GOLD, width=4)

# O protocolo coordena todas as etapas; o diagrama representa o fluxo da pesquisa.
draw.rectangle((60, 274, 1540, 369), fill=NAVY)
text(84, 289, "PROTOCOLO DE PESQUISA", 23, "#FFFFFF", True)
text(
    84,
    329,
    "Hipótese de investimento • Parâmetros definidos • Separação cronológica das amostras",
    25,
    "#E0E6EC",
)

card(
    60,
    419,
    "01",
    "Base de dados",
    "Universo de investimento",
    [
        "Preços, liquidez e universo histórico",
        "Referência de mercado e taxa de caixa",
        "Validação e origem dos dados",
    ],
)
card(
    570,
    419,
    "02",
    "Fatores de seleção",
    "Sinais quantitativos",
    [
        "Momentum 12–1 e baixa volatilidade",
        "Classificação relativa dos ativos",
        "Filtros de elegibilidade e liquidez",
    ],
)
card(
    1080,
    419,
    "03",
    "Construção de carteira",
    "Seleção e ponderação",
    [
        "Pesos iguais ou inverso da volatilidade",
        "Limite de concentração por ativo",
        "Posições compradas, sem alavancagem",
    ],
)
card(
    1080,
    744,
    "04",
    "Simulação histórica",
    "Implementação e fricções",
    [
        "Rebalanceamento mensal defasado",
        "Evolução dos pesos e saldo em caixa",
        "Custos sobre compras e vendas",
    ],
)
card(
    570,
    744,
    "05",
    "Risco e desempenho",
    "Avaliação das estratégias",
    [
        "Desenvolvimento e amostra reservada",
        "Retorno, volatilidade e perdas máximas",
        "Sensibilidade a custos e incerteza",
    ],
)
card(
    60,
    744,
    "06",
    "Relatórios e evidências",
    "Comunicação dos resultados",
    [
        "Comparação com referência de mercado",
        "Painel de desempenho e risco",
        "Histórico de pesos, custos e operações",
    ],
)
arrow([(522, 547), (565, 547)])
arrow([(1032, 547), (1075, 547)])
arrow([(1310, 676), (1310, 739)])
arrow([(1078, 872), (1037, 872)])
arrow([(568, 872), (527, 872)])

# Controles descritos como capacidades de pesquisa, não como certificação institucional.
draw.rectangle((60, 1054, 1540, 1204), fill="#E9EDF0")
draw.rectangle((60, 1054, 65, 1204), fill=GOLD)
text(86, 1076, "CONTROLES E RASTREABILIDADE", 23, NAVY, True)
text(
    86,
    1120,
    "Testes de causalidade temporal e consistência contábil • Verificações automatizadas",
    26,
    INK,
)
text(86, 1161, "Registro dos dados, parâmetros e versões utilizados em cada experimento", 25, MUTED)

draw.line((60, 1253, 1540, 1253), fill=LINE, width=2)
text(60, 1280, "ESCOPO E LIMITAÇÕES", 19, NAVY, True)
text(
    60,
    1314,
    "Demonstração com dados sintéticos, sem evidência empírica de desempenho no mercado brasileiro.",
    23,
    MUTED,
)
text(
    60,
    1350,
    "Material de pesquisa exploratória. Não constitui recomendação de investimento.",
    23,
    MUTED,
)

if __name__ == "__main__":
    output = ROOT / "project-architecture.png"
    image.save(output, optimize=True)
    print(output)
