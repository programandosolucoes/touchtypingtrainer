"""Fonte, cores e tamanhos — um lugar só, decidido uma vez por execução.

## Por que este módulo existe

O programa pedia `('Helvetica', 12)` em dezenas de lugares. No Linux, `Helvetica`
não é uma fonte: é um apelido do X11 que cai em **Nimbus Sans L**, um clone
PostScript dos anos 90 sem hinting decente. Pior: `TkDefaultFont` cai em `fixed`,
que é **bitmap** — não tem antialiasing nenhum. É por isso que a letra fica ruim.

A correção tem duas metades, e a primeira não é código:

1. **O Tk precisa ter Xft.** Sem Xft o Tk nem enxerga o fontconfig: pedir
   "DejaVu Sans" devolve `fixed`. O Python standalone do `uv` empacota um Tk sem
   Xft — e o binário do PyInstaller herda esse Tk, então o problema viajava para
   o cliente junto com o executável. Usar um Python cujo Tk tenha Xft
   (`python3-tk` do sistema) é o que resolve de verdade. `diagnostico()` abaixo
   diz em que situação a máquina está.
2. **Pedir uma fonte que exista.** `escolher_familia` percorre uma lista de
   preferência e devolve a primeira instalada, em vez de cravar um nome e torcer.

## A paleta

Segue o Material Design 3 do Google: uma cor primária, uma superfície clara, e
texto em dois níveis de ênfase. A escolha não é estética — é contraste: os pares
usados aqui ficam acima de 4.5:1, o mínimo do WCAG AA para texto normal.
"""
from tkinter import font as tkfont

# Ordem de preferência. **DejaVu Sans vem primeiro de propósito**: Roboto e Noto
# Sans são bonitas, mas têm haste mais leve e ficam finas demais em tela comum no
# tamanho de interface. Legibilidade ganha de elegância aqui — quem usa o
# programa está justamente tentando NÃO forçar a vista para achar a letra.
FAMILIAS_DE_TEXTO = (
    'DejaVu Sans', 'Noto Sans', 'Roboto', 'Inter', 'Lato', 'Carlito',
    'Ubuntu', 'Cantarell', 'Liberation Sans', 'FreeSans', 'Arial', 'Helvetica',
)
# Monoespaçada, para a frase do exercício: alinhamento coluna a coluna importa
# porque cada caractere é pintado individualmente.
FAMILIAS_MONO = (
    'Roboto Mono', 'Noto Sans Mono', 'JetBrains Mono', 'Ubuntu Mono',
    'DejaVu Sans Mono', 'Liberation Mono', 'FreeMono', 'Courier New', 'Courier',
)

# --- Material Design 3, tema claro -------------------------------------------
PRIMARIA = '#1a73e8'          # azul do Google
PRIMARIA_ESCURA = '#0b57d0'
SOBRE_PRIMARIA = '#ffffff'
SUPERFICIE = '#ffffff'
SUPERFICIE_VARIANTE = '#f1f3f4'
CONTORNO = '#c4c7c5'
TEXTO = '#1f1f1f'             # 15.9:1 sobre a superfície
TEXTO_SECUNDARIO = '#5f6368'  # 5.9:1 — ainda AA para texto normal
SUCESSO = '#188038'
ATENCAO = '#b06000'           # 4.6:1; o laranja claro comum reprova em contraste
ERRO = '#c5221f'

# Escala tipográfica, no espírito da do Material: poucos degraus, com papel claro.
# Os valores são generosos de propósito — a queixa que originou esta escala foi
# "está fino demais", e texto de interface pequeno é a primeira coisa que cansa
# quem passa meia hora treinando digitação.
TAMANHO_TITULO = 26
TAMANHO_SUBTITULO = 17
TAMANHO_CORPO = 13
TAMANHO_APOIO = 11
TAMANHO_EXERCICIO = 26        # a frase a digitar: o maior elemento da tela
TAMANHO_DESTAQUE = 19

NOME_DO_TEMA = 'TouchTypingClaro'

_familia_texto = None
_familia_mono = None
_tema_registrado = False


def aplicar(sg):
    """Registra e ativa a paleta no (Free)SimpleGUI.

    **Sem isto nada adianta.** O tema padrão do FreeSimpleGUI pinta o fundo de
    cinza-ardósia; o texto secundário desta paleta é cinza médio, e cinza sobre
    cinza é ilegível. Pior: os desenhos do teclado e das mãos têm fundo branco e
    viram retângulos recortados sobre o cinza.

    Definir cor elemento por elemento não resolveria — todo `sg.Text` novo que
    alguém acrescentasse voltaria a nascer cinza. O tema é o lugar certo.
    """
    global _tema_registrado
    if not _tema_registrado:
        sg.theme_add_new(NOME_DO_TEMA, {
            'BACKGROUND': SUPERFICIE,
            'TEXT': TEXTO,
            'INPUT': SUPERFICIE_VARIANTE,
            'TEXT_INPUT': TEXTO,
            'SCROLL': SUPERFICIE_VARIANTE,
            'BUTTON': (SOBRE_PRIMARIA, PRIMARIA),
            'PROGRESS': (PRIMARIA, SUPERFICIE_VARIANTE),
            'BORDER': 1,
            'SLIDER_DEPTH': 0,
            'PROGRESS_DEPTH': 0,
        })
        _tema_registrado = True
    sg.theme(NOME_DO_TEMA)
    iniciar()


def escolher_familia(preferidas, padrao='TkDefaultFont'):
    """Primeira família da lista que estiver instalada nesta máquina.

    Compara sem espaços nem caixa porque o Tk devolve os nomes normalizados de
    formas diferentes conforme a plataforma.
    """
    try:
        instaladas = {f.lower().replace(' ', ''): f for f in tkfont.families()}
    except RuntimeError:
        return padrao        # sem janela ainda; quem chamar de novo depois acerta
    for nome in preferidas:
        achada = instaladas.get(nome.lower().replace(' ', ''))
        if achada:
            return achada
    return padrao


def iniciar():
    """Resolve as famílias uma vez. Chamar depois que existir uma janela Tk."""
    global _familia_texto, _familia_mono
    _familia_texto = escolher_familia(FAMILIAS_DE_TEXTO)
    _familia_mono = escolher_familia(FAMILIAS_MONO)
    return _familia_texto, _familia_mono


def texto(tamanho=TAMANHO_CORPO, negrito=False):
    """Fonte de interface, no formato que o (Free)SimpleGUI espera."""
    familia = _familia_texto or escolher_familia(FAMILIAS_DE_TEXTO)
    return (familia, tamanho, 'bold') if negrito else (familia, tamanho)


def mono(tamanho=TAMANHO_CORPO, negrito=False):
    """Fonte monoespaçada, para a frase do exercício e o teclado desenhado."""
    familia = _familia_mono or escolher_familia(FAMILIAS_MONO)
    return (familia, tamanho, 'bold') if negrito else (familia, tamanho)


def diagnostico():
    """O que esta máquina consegue renderizar. Usado pelo `tools/diagnostico.py`.

    `xft` False significa que nenhum ajuste de código deixará a letra bonita:
    o Tk desta instalação não fala com o fontconfig.
    """
    try:
        familias = tkfont.families()
    except RuntimeError:
        return {'xft': False, 'familias': 0, 'texto': None, 'mono': None,
                'motivo': 'nenhuma janela Tk ativa'}
    # Um Tk sem Xft só enxerga as fontes do X11 antigo — algumas dezenas, e
    # nenhuma das modernas. Com Xft passam de duas centenas.
    escolhida = escolher_familia(('DejaVu Sans',), padrao='')
    return {
        'xft': bool(escolhida),
        'familias': len(familias),
        'texto': escolher_familia(FAMILIAS_DE_TEXTO),
        'mono': escolher_familia(FAMILIAS_MONO),
        'motivo': '' if escolhida else
                  'Tk sem Xft: nao enxerga o fontconfig e cai em fonte bitmap',
    }
