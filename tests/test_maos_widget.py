"""Testes das mãos desenhadas, consultando o Canvas do Tk de verdade."""
import os

import pytest

pytestmark = pytest.mark.skipif(
    not os.environ.get('DISPLAY') and not os.environ.get('WAYLAND_DISPLAY'),
    reason='sem servidor gráfico para abrir a janela')

DEDOS = ('minimo', 'anelar', 'medio', 'indicador')


@pytest.fixture
def maos():
    import maos_widget
    from gui_backend import sg

    widget = maos_widget.Maos(400, 260, chave='-M-')
    janela = sg.Window('teste', [[widget.elemento()]], finalize=True,
                       alpha_channel=0, location=(-2000, -2000))
    widget.desenhar()
    yield widget
    janela.close()


def _cor(maos, mao, dedo):
    return maos._grafico.tk_canvas.itemcget(maos._figuras[(mao, dedo)], 'fill')


def test_desenha_os_quatro_dedos_das_duas_maos(maos):
    for mao in ('esquerda', 'direita'):
        for dedo in DEDOS:
            assert (mao, dedo) in maos._figuras


def test_em_repouso_todos_os_dedos_tem_cor_de_pele(maos):
    import maos_widget
    for mao in ('esquerda', 'direita'):
        for dedo in DEDOS:
            assert _cor(maos, mao, dedo) == maos_widget.COR_DA_PELE


def test_destacar_usa_a_mesma_cor_do_teclado(maos):
    # A ligação visual é o que ensina: o dedo aceso tem a cor da tecla acesa.
    import teclado_widget
    maos.destacar('direita', 'indicador')
    assert _cor(maos, 'direita', 'indicador') == \
        teclado_widget.CORES_DOS_DEDOS['indicador']


def test_destacar_apaga_o_dedo_anterior(maos):
    import maos_widget
    maos.destacar('esquerda', 'minimo')
    maos.destacar('direita', 'medio')
    assert _cor(maos, 'esquerda', 'minimo') == maos_widget.COR_DA_PELE
    assert _cor(maos, 'direita', 'medio') != maos_widget.COR_DA_PELE


def test_so_um_dedo_fica_aceso_por_vez(maos):
    import maos_widget
    maos.destacar('esquerda', 'anelar')
    acesos = [(m, d) for m in ('esquerda', 'direita') for d in DEDOS
              if _cor(maos, m, d) != maos_widget.COR_DA_PELE]
    assert acesos == [('esquerda', 'anelar')]


def test_limpar_apaga_tudo(maos):
    import maos_widget
    maos.destacar('direita', 'minimo')
    maos.limpar()
    for mao in ('esquerda', 'direita'):
        for dedo in DEDOS:
            assert _cor(maos, mao, dedo) == maos_widget.COR_DA_PELE


def test_destacar_dedo_inexistente_nao_estoura(maos):
    maos.destacar('esquerda', 'polegar')     # o polegar não é destacável
    maos.destacar(None, None)


def test_as_maos_sao_espelhadas(maos):
    # O mínimo esquerdo fica na borda esquerda; o direito, na borda direita.
    canvas = maos._grafico.tk_canvas
    x_min_esq = canvas.coords(maos._figuras[('esquerda', 'minimo')])[0]
    x_min_dir = canvas.coords(maos._figuras[('direita', 'minimo')])[0]
    x_ind_esq = canvas.coords(maos._figuras[('esquerda', 'indicador')])[0]
    x_ind_dir = canvas.coords(maos._figuras[('direita', 'indicador')])[0]
    assert x_min_esq < x_ind_esq          # esquerda: mínimo mais à esquerda
    assert x_ind_dir < x_min_dir          # direita: mínimo mais à direita
