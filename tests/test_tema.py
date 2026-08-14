"""Testes do tema: escolha de fonte e contraste da paleta."""
import math
import os

import pytest

import tema

pytestmark = pytest.mark.skipif(
    not os.environ.get('DISPLAY') and not os.environ.get('WAYLAND_DISPLAY'),
    reason='sem servidor gráfico para consultar as fontes')


@pytest.fixture(autouse=True)
def _janela():
    """As funções de fonte do Tk exigem um interpretador Tcl vivo."""
    import tkinter
    raiz = tkinter.Tk()
    raiz.withdraw()
    yield
    raiz.destroy()


def _luminancia(cor):
    """Luminância relativa do WCAG, para calcular contraste de verdade."""
    canais = []
    for i in (1, 3, 5):
        c = int(cor[i:i + 2], 16) / 255
        canais.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    r, g, b = canais
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contraste(frente, fundo):
    a, b = _luminancia(frente), _luminancia(fundo)
    claro, escuro = max(a, b), min(a, b)
    return (claro + 0.05) / (escuro + 0.05)


def test_escolhe_a_primeira_familia_instalada():
    familia = tema.escolher_familia(('Fonte Que Nao Existe', 'DejaVu Sans'))
    assert familia.lower().replace(' ', '') != 'fontequenaoexiste'


def test_cai_no_padrao_quando_nenhuma_existe():
    assert tema.escolher_familia(('Nao Existe A', 'Nao Existe B'),
                                 padrao='TkDefaultFont') == 'TkDefaultFont'


def test_nunca_devolve_o_apelido_helvetica_se_houver_coisa_melhor():
    # `Helvetica` no Linux é apelido do X11 e cai numa fonte sem hinting bom.
    # Ele é o último da lista de propósito.
    assert tema.FAMILIAS_DE_TEXTO[-1] == 'Helvetica'


def test_texto_e_mono_devolvem_tupla_que_o_simplegui_aceita():
    assert len(tema.texto()) == 2
    assert len(tema.texto(negrito=True)) == 3
    assert tema.texto(negrito=True)[2] == 'bold'
    assert len(tema.mono(14)) == 2
    assert tema.mono(14)[1] == 14


def test_iniciar_resolve_as_duas_familias():
    familia_texto, familia_mono = tema.iniciar()
    assert familia_texto and familia_mono


def test_a_mono_escolhida_e_realmente_monoespacada():
    from tkinter import font as tkfont
    _, familia_mono = tema.iniciar()
    f = tkfont.Font(family=familia_mono, size=12)
    # Numa fonte monoespaçada, `i` e `W` ocupam a mesma largura. Se não ocupam,
    # a frase do exercício desalinha conforme o aluno digita.
    assert f.measure('i') == f.measure('W'), familia_mono


def test_o_texto_principal_passa_no_contraste_AA():
    assert contraste(tema.TEXTO, tema.SUPERFICIE) >= 4.5


def test_o_texto_secundario_passa_no_contraste_AA():
    assert contraste(tema.TEXTO_SECUNDARIO, tema.SUPERFICIE) >= 4.5


@pytest.mark.parametrize('nome', ('PRIMARIA', 'SUCESSO', 'ATENCAO', 'ERRO'))
def test_as_cores_de_estado_passam_no_contraste_AA(nome):
    # Laranja e verde claros são o erro clássico aqui: bonitos e ilegíveis.
    assert contraste(getattr(tema, nome), tema.SUPERFICIE) >= 4.5, nome


def test_texto_sobre_a_cor_primaria_passa_no_contraste():
    assert contraste(tema.SOBRE_PRIMARIA, tema.PRIMARIA) >= 4.5


def test_diagnostico_diz_se_o_tk_tem_xft():
    d = tema.diagnostico()
    assert set(d) >= {'xft', 'familias', 'texto', 'mono', 'motivo'}
    assert isinstance(d['xft'], bool)
    if not d['xft']:
        assert d['motivo']       # sem Xft, tem de explicar o porquê


# --- Contraste das teclas do teclado -----------------------------------------
# Esta seção existe por causa de um defeito real: a face da tecla era pintada com
# a cor SATURADA do dedo e a letra por cima era escura, dando ~3,6:1 — abaixo do
# mínimo do WCAG AA e visivelmente ilegível. Sem teste, isso volta.

def test_a_letra_e_legivel_sobre_qualquer_tecla_em_repouso():
    import teclado_widget
    for dedo, face in teclado_widget.CORES_DAS_TECLAS.items():
        razao = contraste(teclado_widget.COR_DO_TEXTO, face)
        assert razao >= 4.5, f'{dedo}: {razao:.1f}:1 sobre {face}'


def test_a_letra_e_legivel_sobre_qualquer_estado():
    import teclado_widget
    for estado, face in teclado_widget.CORES_DOS_ESTADOS.items():
        razao = contraste(teclado_widget.COR_DO_TEXTO, face)
        assert razao >= 4.5, f'{estado}: {razao:.1f}:1 sobre {face}'


def test_a_borda_se_distingue_da_face_da_tecla():
    # É a borda que carrega a informação de dedo agora que a face é pálida.
    import teclado_widget
    for dedo in teclado_widget.CORES_DAS_TECLAS:
        razao = contraste(teclado_widget.CORES_DOS_DEDOS[dedo],
                          teclado_widget.CORES_DAS_TECLAS[dedo])
        assert razao >= 3.0, f'{dedo}: borda com {razao:.1f}:1 sobre a face'


def _lab(cor):
    """sRGB -> CIE Lab, para medir distância PERCEPTUAL entre duas cores."""
    canais = []
    for i in (1, 3, 5):
        v = int(cor[i:i + 2], 16) / 255
        canais.append(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4)
    r, g, b = canais
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883
    def f(t):
        return t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116
    fx, fy, fz = f(x), f(y), f(z)
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))


def distancia(a, b):
    """ΔE76. Abaixo de ~2 ninguém distingue; acima de 25 são cores diferentes."""
    return math.dist(_lab(a), _lab(b))


def test_as_quatro_cores_de_dedo_sao_distinguiveis_entre_si():
    """Distância perceptual, e não razão de contraste.

    Contraste mede só luminância: roxo e azul podem dar 1,0:1 e ainda assim
    serem obviamente cores diferentes. O que importa aqui é o olho separar as
    quatro — e a cor já é redundante (o dedo também é dito por escrito, aceso na
    mão e marcado pelo anel), então ela não precisa carregar a informação
    sozinha.
    """
    import teclado_widget
    # O polegar fica de fora: é cinza de propósito, não compete com as outras.
    cores = [c for d, c in teclado_widget.CORES_DOS_DEDOS.items() if d != 'polegar']
    for i, a in enumerate(cores):
        for b in cores[i + 1:]:
            assert distancia(a, b) >= 25, f'{a} e {b}: dE={distancia(a, b):.0f}'


def test_as_faces_palidas_tambem_se_distinguem():
    # É a face que ocupa a maior área; se duas virarem o mesmo cinza-claro, o
    # teclado deixa de agrupar os dedos visualmente.
    import teclado_widget
    faces = [c for d, c in teclado_widget.CORES_DAS_TECLAS.items() if d != 'polegar']
    for i, a in enumerate(faces):
        for b in faces[i + 1:]:
            assert distancia(a, b) >= 9, f'{a} e {b}: dE={distancia(a, b):.1f}'


def test_o_anel_se_destaca_da_tecla_que_ele_marca():
    import teclado_widget
    razao = contraste(teclado_widget.COR_DO_MARCADOR,
                      teclado_widget.CORES_DOS_ESTADOS['proxima'])
    assert razao >= 3.0, f'anel com só {razao:.1f}:1 sobre a tecla da vez'
