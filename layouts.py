"""Os três layouts físicos e a quem cada tecla pertence.

Substitui os desenhos ASCII do `keyboards.py`. A diferença que importa não é
estética: aqui a relação tecla→dedo é DADO consultável, e era só prosa antes.

O truque que mantém isto curto: o padrão de dedos por posição é o mesmo nos três
layouts — o que muda é o caractere que sai em cada posição. Por isso cada linha
é descrita por três strings do mesmo comprimento: os caracteres, a mão e o dedo.
"""
from dataclasses import dataclass

LAYOUT_POR_IDIOMA = {'pt': 'abnt2', 'en': 'us', 'it': 'it'}

_MAO = {'E': 'esquerda', 'D': 'direita'}
_DEDO = {'P': 'minimo', 'R': 'anelar', 'M': 'medio', 'I': 'indicador'}

# Deslocamento de cada linha, em larguras de tecla. É o escalonamento que faz o
# desenho parecer um teclado de verdade.
_DESLOCAMENTOS = (0.0, 1.5, 1.75, 2.25)

# (caracteres, mãos, dedos) por linha: números, cima, base, baixo.
_LINHAS = {
    'abnt2': (
        ("'1234567890-=", 'EEEEEEDDDDDDD', 'PPRMIIIIMRPPP'),
        ('qwertyuiop´[', 'EEEEEDDDDDDD', 'PRMIIIIMRPPP'),
        ('asdfghjklç~]', 'EEEEEDDDDDDD', 'PRMIIIIMRPPP'),
        ('zxcvbnm,.;/', 'EEEEEDDDDDD', 'PRMIIIIMRPP'),
    ),
    'us': (
        ('`1234567890-=', 'EEEEEEDDDDDDD', 'PPRMIIIIMRPPP'),
        ('qwertyuiop[]', 'EEEEEDDDDDDD', 'PRMIIIIMRPPP'),
        ("asdfghjkl;'", 'EEEEEDDDDDD', 'PRMIIIIMRPP'),
        ('zxcvbnm,./', 'EEEEEDDDDD', 'PRMIIIIMRP'),
    ),
    'it': (
        ("\\1234567890'ì", 'EEEEEEDDDDDDD', 'PPRMIIIIMRPPP'),
        ('qwertyuiopè+', 'EEEEEDDDDDDD', 'PRMIIIIMRPPP'),
        ('asdfghjklòàù', 'EEEEEDDDDDDD', 'PRMIIIIMRPPP'),
        ('zxcvbnm,.-', 'EEEEEDDDDD', 'PRMIIIIMRP'),
    ),
}


@dataclass(frozen=True)
class TeclaFisica:
    caractere: str
    linha: int          # 0 = números, 1 = cima, 2 = base, 3 = baixo
    x: float            # posição em larguras de tecla, a partir da esquerda
    largura: float      # em larguras de tecla
    mao: str            # 'esquerda' | 'direita'
    dedo: str           # 'minimo' | 'anelar' | 'medio' | 'indicador'


def teclas(nome_layout):
    """Todas as teclas de caractere do layout, já com mão e dedo atribuídos."""
    resultado = []
    for numero_da_linha, (caracteres, maos, dedos) in enumerate(_LINHAS[nome_layout]):
        assert len(caracteres) == len(maos) == len(dedos), \
            f'{nome_layout} linha {numero_da_linha}: as três strings têm de ter o mesmo tamanho'
        deslocamento = _DESLOCAMENTOS[numero_da_linha]
        for coluna, caractere in enumerate(caracteres):
            resultado.append(TeclaFisica(
                caractere=caractere, linha=numero_da_linha,
                x=deslocamento + coluna, largura=1.0,
                mao=_MAO[maos[coluna]], dedo=_DEDO[dedos[coluna]]))
    return tuple(resultado)


def dedo_de(caractere, nome_layout):
    """(mão, dedo) da tecla, ou None se o caractere não existe nesse layout.

    Maiúscula é resolvida pela minúscula correspondente: o dedo é o mesmo, o
    que muda é o Shift do mínimo oposto.
    """
    procurado = caractere.lower()
    for tecla in teclas(nome_layout):
        if tecla.caractere == procurado:
            return tecla.mao, tecla.dedo
    return None


def caracteres_da_linha(nome_layout, numero):
    """Os caracteres de uma linha física: 0 números, 1 cima, 2 base, 3 baixo.

    Existe para o `licoes.py` montar os níveis sem espiar a estrutura interna
    daqui — quem define o que é uma linha é este módulo.
    """
    return _LINHAS[nome_layout][numero][0]


def teclas_base(nome_layout):
    """As oito teclas da linha-base: (esquerda, direita).

    A quarta da direita muda por layout — `;` no US, `ç` no ABNT2, `ò` no
    italiano — e é justamente ela que o teste de mãos precisa cobrar certo.

    Os índices 4 e 5 (`g` e `h`) ficam de fora de propósito: são alcance
    estendido dos indicadores, não posição de repouso. Quem pousa a mão em
    `ghjk` está com a mão inteira deslocada uma tecla para a esquerda.
    """
    caracteres = caracteres_da_linha(nome_layout, 2)
    return tuple(caracteres[0:4]), tuple(caracteres[6:10])


def retangulos(nome_layout, largura_px, altura_px):
    """Onde desenhar cada tecla, em pixels, dentro da área dada.

    Devolve {caractere: (x0, y0, x1, y1)} com a origem no canto superior
    esquerdo. Quem desenha não precisa saber nada de layout — só consumir isto.
    """
    todas = teclas(nome_layout)
    colunas = max(t.x + t.largura for t in todas)
    unidade = min(largura_px / colunas, altura_px / len(_LINHAS[nome_layout]))
    return {
        t.caractere: (t.x * unidade, t.linha * unidade,
                      (t.x + t.largura) * unidade, (t.linha + 1) * unidade)
        for t in todas
    }
