"""Testes do teclado desenhado, consultando o Canvas do Tk de verdade.

O plano previa "conferir a olho". Perguntar ao Canvas quais figuras existem e de
que cor elas são cobre a parte mecânica melhor do que o olho cobriria — sobra
para o humano só a estética.

Precisa de servidor gráfico: sem DISPLAY os testes são pulados em vez de falhar.
"""
import os

import pytest

import layouts

pytestmark = pytest.mark.skipif(
    not os.environ.get('DISPLAY') and not os.environ.get('WAYLAND_DISPLAY'),
    reason='sem servidor gráfico para abrir a janela')


@pytest.fixture
def teclado():
    """Um teclado desenhado numa janela real, fechada ao fim do teste."""
    import teclado_widget
    from gui_backend import sg

    widget = teclado_widget.Teclado('us', 800, 240, chave='-T-')
    janela = sg.Window('teste', [[widget.elemento()]], finalize=True,
                       alpha_channel=0, location=(-2000, -2000))
    widget.desenhar()
    yield widget
    janela.close()


def _cor_da_tecla(teclado, caractere):
    """Pergunta ao Canvas de que cor está o retângulo daquela tecla."""
    id_retangulo, _ = teclado._figuras[caractere]
    return teclado._grafico.tk_canvas.itemcget(id_retangulo, 'fill')


def test_desenha_uma_figura_por_tecla_do_layout(teclado):
    assert len(teclado._figuras) == len(layouts.teclas('us'))


def test_tecla_em_repouso_usa_a_cor_do_dedo(teclado):
    import teclado_widget
    # `a` é mínimo esquerdo; `f` é indicador esquerdo. Cores diferentes.
    assert _cor_da_tecla(teclado, 'a') == teclado_widget.CORES_DOS_DEDOS['minimo']
    assert _cor_da_tecla(teclado, 'f') == teclado_widget.CORES_DOS_DEDOS['indicador']


def test_teclas_do_mesmo_dedo_nas_duas_maos_tem_a_mesma_cor(teclado):
    # A simetria é o que ensina: mesmo dedo, mesma cor dos dois lados.
    assert _cor_da_tecla(teclado, 'a') == _cor_da_tecla(teclado, ';')
    assert _cor_da_tecla(teclado, 'f') == _cor_da_tecla(teclado, 'j')


def test_pintar_muda_a_cor_da_tecla(teclado):
    import teclado_widget
    teclado.pintar('j', 'proxima')
    assert _cor_da_tecla(teclado, 'j') == teclado_widget.CORES_DOS_ESTADOS['proxima']
    teclado.pintar('j', 'errada')
    assert _cor_da_tecla(teclado, 'j') == teclado_widget.CORES_DOS_ESTADOS['errada']


def test_pintar_nao_afeta_as_outras_teclas(teclado):
    import teclado_widget
    teclado.pintar('j', 'certa')
    assert _cor_da_tecla(teclado, 'k') == teclado_widget.CORES_DOS_DEDOS['medio']


def test_limpar_estados_devolve_a_cor_do_dedo(teclado):
    import teclado_widget
    teclado.pintar('j', 'errada')
    teclado.limpar_estados()
    assert _cor_da_tecla(teclado, 'j') == teclado_widget.CORES_DOS_DEDOS['indicador']


def test_letra_continua_visivel_depois_de_repintar(teclado):
    # Repintar apaga e redesenha o retângulo, que nasce POR CIMA do texto.
    # Sem tag_raise a letra some — defeito que só aparece depois de digitar.
    _, id_texto = teclado._figuras['j']
    teclado.pintar('j', 'certa')
    ordem = teclado._grafico.tk_canvas.find_all()
    id_retangulo, _ = teclado._figuras['j']
    assert ordem.index(id_texto) > ordem.index(id_retangulo)


def test_pintar_caractere_fora_do_layout_nao_estoura(teclado):
    teclado.pintar('ç', 'proxima')      # não existe no layout US
    teclado.pintar('€', 'errada')


def test_marcar_desenha_um_anel_sobre_a_tecla(teclado):
    import teclado_widget
    teclado.marcar('j')
    canvas = teclado._grafico.tk_canvas
    assert canvas.type(teclado._marcador) == 'oval'
    assert canvas.itemcget(teclado._marcador, 'outline') == teclado_widget.COR_DO_MARCADOR
    # Sem preenchimento: o anel marca sem esconder a letra por baixo.
    assert canvas.itemcget(teclado._marcador, 'fill') == ''


def test_o_anel_fica_dentro_da_tecla_marcada(teclado):
    x0, y0, x1, y1 = teclado._retangulos['j']
    teclado.marcar('j')
    ax0, ay0, ax1, ay1 = teclado._grafico.tk_canvas.coords(teclado._marcador)
    assert x0 <= ax0 and ax1 <= x1
    assert y0 <= ay0 and ay1 <= y1


def test_marcar_outra_tecla_tira_o_anel_da_anterior(teclado):
    teclado.marcar('j')
    primeiro = teclado._marcador
    teclado.marcar('k')
    assert teclado._marcado == 'k'
    assert primeiro not in teclado._grafico.tk_canvas.find_all()


def test_marcar_none_tira_o_anel(teclado):
    teclado.marcar('j')
    teclado.marcar(None)
    assert teclado._marcador is None


def test_o_anel_continua_visivel_depois_de_repintar_a_tecla(teclado):
    # `pintar` apaga e redesenha o retângulo, que nasce por cima de tudo. Sem
    # devolver o anel ao topo ele some justamente quando o aluno erra a tecla.
    teclado.marcar('j')
    teclado.pintar('j', 'errada')
    ordem = teclado._grafico.tk_canvas.find_all()
    id_retangulo, _ = teclado._figuras['j']
    assert teclado._marcador in ordem
    assert ordem.index(teclado._marcador) > ordem.index(id_retangulo)


def test_limpar_estados_tira_o_anel_junto(teclado):
    teclado.marcar('j')
    teclado.limpar_estados()
    assert teclado._marcador is None


def test_redimensionar_preserva_o_anel(teclado):
    teclado.marcar('j')
    teclado.redimensionar(1200, 360)
    assert teclado._marcado == 'j'
    assert teclado._marcador in teclado._grafico.tk_canvas.find_all()


def test_marcar_tecla_fora_do_layout_nao_estoura(teclado):
    teclado.marcar('ç')       # não existe no layout US
    assert teclado._marcador is None


def test_redimensionar_aumenta_as_teclas_e_preserva_o_estado(teclado):
    import teclado_widget
    teclado.pintar('j', 'proxima')
    largura_antes = teclado._retangulos['j'][2] - teclado._retangulos['j'][0]
    teclado.redimensionar(1200, 360)
    largura_depois = teclado._retangulos['j'][2] - teclado._retangulos['j'][0]
    assert largura_depois > largura_antes
    assert _cor_da_tecla(teclado, 'j') == teclado_widget.CORES_DOS_ESTADOS['proxima']
