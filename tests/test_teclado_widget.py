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


def test_redimensionar_aumenta_as_teclas_e_preserva_o_estado(teclado):
    import teclado_widget
    teclado.pintar('j', 'proxima')
    largura_antes = teclado._retangulos['j'][2] - teclado._retangulos['j'][0]
    teclado.redimensionar(1200, 360)
    largura_depois = teclado._retangulos['j'][2] - teclado._retangulos['j'][0]
    assert largura_depois > largura_antes
    assert _cor_da_tecla(teclado, 'j') == teclado_widget.CORES_DOS_ESTADOS['proxima']
