"""Currículo do Modo Lição: o que se aprende, em que ordem e quando libera.

As metas de WPM são baixas de propósito nos primeiros níveis. Nessa altura o que
está sendo construído é o caminho do dedo, não velocidade — e meta agressiva
cedo empurra a pessoa de volta a olhar para o teclado, que é o hábito a matar.
"""
import random
from dataclasses import dataclass

import layouts

CARACTERES_POR_PALAVRA = 5
# Folga sobre o tempo que o exercício levaria digitado exatamente na meta.
FOLGA_DO_LIMITE = 2.0

# Tamanho dos "grupos" (pseudopalavras) dos níveis de treino puro.
MENOR_GRUPO = 3
MAIOR_GRUPO = 5

# Um tropeço a cada 33 teclas ainda é aprendizado; mais que isso é chute.
MAXIMO_DE_TROPECOS = 0.03
REGULARIDADE_MINIMA = 0.90
# Um acerto isolado pode ser sorte; dois seguidos, não.
APROVACOES_SEGUIDAS = 2


@dataclass(frozen=True)
class Nivel:
    numero: int
    id: str
    teclas_novas: tuple
    wpm_meta: int


@dataclass(frozen=True)
class Avaliacao:
    aprovado: bool
    faltou: tuple


# (id, wpm_meta, de onde saem as teclas novas)
_NIVEIS = (
    ('base-esquerda', 10, 'base_esquerda'),
    ('base-direita', 10, 'base_direita'),
    ('base-completa', 12, 'espaco'),
    ('indices-estendidos', 14, 'linha:2:4,6'),
    ('cima-esquerda', 16, 'linha:1:0,5'),
    ('cima-direita', 18, 'linha:1:5,10'),
    ('baixo-esquerda', 20, 'linha:3:0,5'),
    ('baixo-direita', 22, 'linha:3:5,9'),
    ('maiusculas', 25, 'maiusculas'),
    ('numeros', 28, 'linha:0:1,11'),
    ('simbolos', 30, 'simbolos'),
    ('texto-corrido', 35, 'nada'),
)


def _teclas_novas(nome_layout, origem, ja_liberadas):
    """As teclas que ESTE nível acrescenta.

    Recebe o que os níveis anteriores já ensinaram porque dois níveis dependem
    disso: o de símbolos é definido por exclusão (o que sobrou do layout), e sem
    essa informação ele repetiria o `ç` do nível 2 e a vírgula do nível 8.
    """
    esquerda, direita = layouts.teclas_base(nome_layout)
    if origem == 'base_esquerda':
        return esquerda
    if origem == 'base_direita':
        return direita
    if origem == 'espaco':
        return (' ',)
    if origem == 'maiusculas':
        # Só letra tem maiúscula. `;` em maiúscula continua `;` e repetiria o
        # nível 2 sem ensinar Shift nenhum.
        return tuple(c.upper() for c in esquerda + direita if c.isalpha())
    if origem == 'nada':
        return ()
    if origem == 'simbolos':
        return tuple(t.caractere for t in layouts.teclas(nome_layout)
                     if t.caractere not in ja_liberadas)
    if origem.startswith('linha:'):
        _, numero, faixa = origem.split(':')
        inicio, fim = (int(p) for p in faixa.split(','))
        caracteres = layouts.caracteres_da_linha(nome_layout, int(numero))
        return tuple(caracteres[inicio:fim])
    raise ValueError(f'origem desconhecida: {origem}')


def curriculo(nome_layout):
    """Os 12 níveis desse layout, do `asdf` isolado ao texto corrido.

    Montado em sequência, e não por compreensão, porque cada nível precisa saber
    o que os anteriores já ensinaram — é o que impede uma tecla de ser
    apresentada como novidade duas vezes.
    """
    niveis = []
    ja_liberadas = set()
    for numero, (identificador, meta, origem) in enumerate(_NIVEIS, start=1):
        novas = _teclas_novas(nome_layout, origem, ja_liberadas)
        ja_liberadas.update(novas)
        # A maiúscula usa a mesma tecla da minúscula: liberar `A` implica que a
        # tecla `a` já está vista, para o nível de símbolos não a reoferecer.
        ja_liberadas.update(c.lower() for c in novas)
        niveis.append(Nivel(numero=numero, id=identificador, wpm_meta=meta,
                            teclas_novas=novas))
    return tuple(niveis)


def teclas_liberadas(nome_layout, ate_numero):
    """Tudo que o aluno já pode ver num exercício até esse nível, acumulado."""
    liberadas = set()
    for nivel in curriculo(nome_layout):
        if nivel.numero > ate_numero:
            break
        liberadas.update(nivel.teclas_novas)
    return frozenset(liberadas)


def limite_de_tempo(n_caracteres, wpm_meta):
    """Segundos disponíveis: o dobro do tempo que levaria digitando na meta.

    Deriva da própria meta para não existirem dois números soltos dizendo a
    mesma coisa — quem alcança a meta tem sempre 100% de folga.
    """
    if wpm_meta <= 0 or n_caracteres <= 0:
        return 0.0
    minutos_na_meta = (n_caracteres / CARACTERES_POR_PALAVRA) / wpm_meta
    return minutos_na_meta * 60.0 * FOLGA_DO_LIMITE


def gerar_exercicio(nome_layout, numero_do_nivel, semente, grupos=12):
    """Monta o texto do exercício a partir das teclas já liberadas.

    Determinístico: a mesma semente devolve o mesmo texto, e a semente vai
    gravada no histórico — então um exercício pode ser repetido igual.

    Do nível 12 em diante o texto não é gerado: vem das frases reais, por
    `filtrar_frases`.
    """
    permitidas = teclas_liberadas(nome_layout, numero_do_nivel) - {' '}
    if not permitidas:
        return ''
    sorteio = random.Random(semente)
    alfabeto = sorted(permitidas)
    palavras = []
    for _ in range(grupos):
        tamanho = sorteio.randint(MENOR_GRUPO, MAIOR_GRUPO)
        palavras.append(''.join(sorteio.choice(alfabeto) for _ in range(tamanho)))
    return ' '.join(palavras)


def filtrar_frases(frases, teclas_permitidas):
    """Só as frases que cabem inteiras no alfabeto já aprendido.

    Compara em minúsculas porque a maiúscula usa a mesma tecla — o que muda é
    o Shift, liberado no nível 9.
    """
    permitidas = {c.lower() for c in teclas_permitidas} | {' '}
    return [f for f in frases if set(f.lower()) <= permitidas]


def avaliar(resultado, nivel):
    """Diz se o exercício aprova o nível e, se não, exatamente o que faltou.

    Reprovar não pune: o aluno repete o mesmo nível, e o relatório aponta qual
    dos quatro critérios ficou para trás.
    """
    faltou = []
    total = resultado['total_teclas'] or 1
    if resultado['tropecos'] / total > MAXIMO_DE_TROPECOS:
        faltou.append('tropecos')
    if resultado['wpm_bruto'] < nivel.wpm_meta:
        faltou.append('wpm')
    regularidade = resultado.get('regularidade')
    # None = exercício curto demais para medir ritmo. Não mede, não reprova.
    if regularidade is not None and regularidade < REGULARIDADE_MINIMA:
        faltou.append('regularidade')
    if resultado['duracao_s'] > resultado['limite_s']:
        faltou.append('tempo')
    return Avaliacao(aprovado=not faltou, faltou=tuple(faltou))


def nivel_atual(registros, nome_layout):
    """Em que nível o aluno está, lido do histórico.

    Avança quando encontra `APROVACOES_SEGUIDAS` aprovações consecutivas no
    nível corrente. Exercício do modo livre é ignorado — ele não faz parte do
    currículo.
    """
    niveis = curriculo(nome_layout)
    indice = 0
    seguidas = 0
    for registro in registros:
        if registro.get('modo') != 'licao':
            continue
        if registro.get('nivel') != niveis[indice].id:
            continue
        if registro.get('aprovado'):
            seguidas += 1
            if seguidas >= APROVACOES_SEGUIDAS and indice < len(niveis) - 1:
                indice += 1
                seguidas = 0
        else:
            seguidas = 0
    return niveis[indice]
