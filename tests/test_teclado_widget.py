"""Testes do teclado rasterizado.

Não dependem de janela: o teclado guarda o estado e o `rasterizador` produz PNG
a partir dele. Isso deixa testável o que antes só se via a olho — inclusive se o
antialiasing está mesmo acontecendo.
"""
import io

import pytest
from PIL import Image

import layouts
import rasterizador
import teclado_widget


@pytest.fixture
def teclado():
    t = teclado_widget.Teclado('us', 800, 240, chave='-T-')
    for tecla in layouts.teclas('us'):
        t._estados.setdefault(tecla.caractere, 'repouso')
    return t


def _imagem(teclado):
    dados = rasterizador.desenhar_teclado(
        teclado.nome_layout, teclado.largura_px, teclado.altura_px,
        estados=teclado._estados, marcado=teclado._marcado,
        cores_das_teclas=teclado_widget.CORES_DAS_TECLAS,
        cores_das_bordas=teclado_widget.CORES_DOS_DEDOS,
        cores_dos_estados=teclado_widget.CORES_DOS_ESTADOS,
        cores_das_bordas_dos_estados=teclado_widget.CORES_DAS_BORDAS_DOS_ESTADOS,
        cor_de_fundo=teclado_widget.COR_DE_FUNDO,
        cor_do_marcador=teclado_widget.COR_DO_MARCADOR,
        cor_do_texto=teclado_widget.COR_DO_TEXTO)
    return Image.open(io.BytesIO(dados)).convert('RGB')


def _cor_no_centro(teclado, caractere):
    """A cor do pixel no meio daquela tecla, lida da imagem gerada."""
    rets = layouts.retangulos(teclado.nome_layout, teclado.largura_px, teclado.altura_px)
    x0, y0, x1, y1 = rets[caractere]
    imagem = _imagem(teclado)
    # Fora do centro exato, para não cair sobre a letra desenhada.
    return imagem.getpixel((int((x0 + x1) / 2), int(y0 + (y1 - y0) * 0.22)))


def _hex_para_rgb(cor):
    return tuple(int(cor[i:i + 2], 16) for i in (1, 3, 5))


def _proximo(a, b, tolerancia=24):
    """Compara cores com folga: a redução com LANCZOS mexe alguns tons."""
    return all(abs(x - y) <= tolerancia for x, y in zip(a, b))


def test_toda_tecla_do_layout_tem_estado(teclado):
    assert len(teclado._estados) == len(layouts.teclas('us'))


def test_tecla_em_repouso_usa_a_face_palida_do_dedo(teclado):
    # A face é PÁLIDA e a borda é saturada: pintar a face com a cor forte punha
    # a letra escura em ~3,6:1 de contraste, abaixo do mínimo legível.
    assert _proximo(_cor_no_centro(teclado, 'a'),
                    _hex_para_rgb(teclado_widget.CORES_DAS_TECLAS['minimo']))
    assert _proximo(_cor_no_centro(teclado, 'f'),
                    _hex_para_rgb(teclado_widget.CORES_DAS_TECLAS['indicador']))


def test_teclas_do_mesmo_dedo_nas_duas_maos_tem_a_mesma_cor(teclado):
    # A simetria é o que ensina: mesmo dedo, mesma cor dos dois lados.
    assert _proximo(_cor_no_centro(teclado, 'a'), _cor_no_centro(teclado, ';'))
    assert _proximo(_cor_no_centro(teclado, 'f'), _cor_no_centro(teclado, 'j'))


def test_pintar_muda_a_cor_da_tecla(teclado):
    teclado.pintar('j', 'proxima')
    assert teclado.estado_de('j') == 'proxima'
    assert _proximo(_cor_no_centro(teclado, 'j'),
                    _hex_para_rgb(teclado_widget.CORES_DOS_ESTADOS['proxima']))


def test_a_letra_fica_legivel_sobre_a_tecla_desenhada(teclado):
    """Lê a imagem e confirma que existe pixel escuro DENTRO da tecla.

    É a checagem de ponta: contraste calculado na paleta não prova que o texto
    chegou à tela com aquela cor."""
    imagem = _imagem(teclado)
    rets = layouts.retangulos('us', teclado.largura_px, teclado.altura_px)
    x0, y0, x1, y1 = rets['f']
    recorte = imagem.crop((int(x0), int(y0), int(x1), int(y1)))
    escuros = [p for p in recorte.getdata() if sum(p) / 3 < 90]
    assert escuros, 'nenhum pixel escuro na tecla: a letra sumiu'


def test_pintar_nao_afeta_as_outras_teclas(teclado):
    teclado.pintar('j', 'certa')
    assert teclado.estado_de('k') == 'repouso'


def test_limpar_estados_devolve_a_cor_do_dedo(teclado):
    teclado.pintar('j', 'errada')
    teclado.limpar_estados()
    assert teclado.estado_de('j') == 'repouso'
    assert teclado.marcado is None


def test_pintar_caractere_fora_do_layout_nao_estoura(teclado):
    teclado.pintar('ç', 'proxima')      # não existe no layout US
    teclado.pintar('€', 'errada')


def test_marcar_registra_a_tecla_da_vez(teclado):
    teclado.marcar('j')
    assert teclado.marcado == 'j'
    teclado.marcar(None)
    assert teclado.marcado is None


def test_marcar_tecla_fora_do_layout_nao_marca_nada(teclado):
    teclado.marcar('ç')
    assert teclado.marcado is None


def test_o_anel_aparece_na_imagem(teclado):
    """O anel tem de mudar pixels DENTRO da tecla marcada — e só dela."""
    antes = _imagem(teclado)
    teclado.marcar('j')
    depois = _imagem(teclado)
    rets = layouts.retangulos('us', teclado.largura_px, teclado.altura_px)
    x0, y0, x1, y1 = (int(v) for v in rets['j'])
    recorte_antes = antes.crop((x0, y0, x1, y1))
    recorte_depois = depois.crop((x0, y0, x1, y1))
    assert list(recorte_antes.getdata()) != list(recorte_depois.getdata())


def test_o_anel_e_da_cor_do_marcador(teclado):
    teclado.marcar('j')
    imagem = _imagem(teclado)
    rets = layouts.retangulos('us', teclado.largura_px, teclado.altura_px)
    x0, y0, x1, y1 = rets['j']
    alvo = _hex_para_rgb(teclado_widget.COR_DO_MARCADOR)
    recorte = imagem.crop((int(x0), int(y0), int(x1), int(y1)))
    assert any(_proximo(p, alvo, 40) for p in recorte.getdata())


def test_o_desenho_tem_antialiasing_de_verdade(teclado):
    """A borda arredondada precisa ter tons INTERMEDIÁRIOS.

    É esta a diferença que o Canvas do Tk não entrega no X11: sem antialiasing a
    borda só tem a cor da tecla e a do fundo, e o degrau aparece. Contar cores
    distintas na quina de uma tecla é o jeito objetivo de verificar.
    """
    imagem = _imagem(teclado)
    rets = layouts.retangulos('us', teclado.largura_px, teclado.altura_px)
    x0, y0, x1, y1 = rets['f']
    # Quina superior esquerda da tecla, onde está o canto arredondado.
    quina = imagem.crop((int(x0), int(y0), int(x0) + 12, int(y0) + 12))
    cores = {p for p in quina.getdata()}
    assert len(cores) > 3, f'só {len(cores)} cores na quina: sem antialiasing'


def test_redimensionar_muda_o_tamanho_da_imagem(teclado):
    assert _imagem(teclado).size == (800, 240)
    teclado.redimensionar(1200, 360)
    assert _imagem(teclado).size == (1200, 360)


def test_so_redesenha_quando_algo_muda(teclado):
    # Redesenhar a cada volta do laço de eventos custaria caro à toa.
    teclado._sujo = False
    teclado.pintar('j', 'repouso')      # já está em repouso: nada muda
    assert teclado._sujo is False
    teclado.pintar('j', 'certa')
    assert teclado._sujo is True


@pytest.mark.parametrize('nome', ('abnt2', 'us', 'it'))
def test_desenha_os_tres_layouts_sem_estourar(nome):
    t = teclado_widget.Teclado(nome, 700, 200)
    for tecla in layouts.teclas(nome):
        t._estados.setdefault(tecla.caractere, 'repouso')
    assert _imagem(t).size == (700, 200)
