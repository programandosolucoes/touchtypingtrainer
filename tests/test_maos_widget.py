"""Testes das mãos rasterizadas — sem janela, lendo a imagem gerada."""
import io

import pytest
from PIL import Image

import maos_widget
import rasterizador
import teclado_widget

DEDOS = ('minimo', 'anelar', 'medio', 'indicador')


@pytest.fixture
def maos():
    return maos_widget.Maos(400, 264, chave='-M-')


def _imagem(maos):
    dados = rasterizador.desenhar_maos(
        maos.largura_px, maos.altura_px, destacado=maos.destacado,
        cores_dos_dedos=teclado_widget.CORES_DOS_DEDOS,
        cor_da_pele=maos_widget.COR_DA_PELE,
        cor_do_contorno=maos_widget.COR_DO_CONTORNO,
        cor_de_fundo='#ffffff', cor_do_rotulo=maos_widget.COR_DO_ROTULO)
    return Image.open(io.BytesIO(dados)).convert('RGB')


def _hex_para_rgb(cor):
    return tuple(int(cor[i:i + 2], 16) for i in (1, 3, 5))


def _pixels(imagem):
    return list(imagem.convert('RGB').tobytes())


def test_em_repouso_nenhum_dedo_esta_aceso(maos):
    assert maos.destacado is None


def test_destacar_registra_a_mao_e_o_dedo(maos):
    maos.destacar('direita', 'indicador')
    assert maos.destacado == ('direita', 'indicador')


def test_destacar_troca_o_dedo_anterior(maos):
    maos.destacar('esquerda', 'minimo')
    maos.destacar('direita', 'medio')
    assert maos.destacado == ('direita', 'medio')


def test_limpar_apaga_tudo(maos):
    maos.destacar('direita', 'minimo')
    maos.limpar()
    assert maos.destacado is None


def test_destacar_dedo_inexistente_nao_acende_nada(maos):
    maos.destacar('esquerda', 'polegar')     # o polegar não é destacável
    assert maos.destacado is None


def test_o_dedo_aceso_aparece_na_imagem_com_a_cor_do_teclado(maos):
    # A ligação visual é o que ensina: o dedo aceso tem a cor da tecla acesa.
    antes = _imagem(maos)
    maos.destacar('direita', 'indicador')
    depois = _imagem(maos)
    assert _pixels(antes) != _pixels(depois)
    alvo = _hex_para_rgb(teclado_widget.CORES_DOS_DEDOS['indicador'])
    achou = any(all(abs(p[i] - alvo[i]) <= 24 for i in range(3))
                for p in depois.getdata())
    assert achou, 'a cor do indicador não apareceu no desenho'


def test_cada_dedo_das_duas_maos_muda_a_imagem(maos):
    # Se dois destaques produzissem a mesma imagem, um deles não estaria sendo
    # desenhado — e o aluno veria o dedo errado aceso.
    vistas = {}
    for mao in ('esquerda', 'direita'):
        for dedo in DEDOS:
            maos.destacar(mao, dedo)
            vistas[(mao, dedo)] = bytes(_pixels(_imagem(maos)))
    assert len(set(vistas.values())) == 8


def test_o_desenho_tem_antialiasing(maos):
    """A borda curva do dedo precisa de tons intermediários.

    Curva no Canvas do Tk sob X11 sai serrilhada — é a razão de as mãos serem
    rasterizadas aqui em vez de desenhadas lá.
    """
    imagem = _imagem(maos)
    cores = {p for p in imagem.getdata()}
    # Só pele, contorno, fundo e rótulo dariam ~4 cores. Com antialiasing, muitas.
    assert len(cores) > 20, f'só {len(cores)} cores: sem antialiasing'


def test_so_redesenha_quando_o_destaque_muda(maos):
    maos.destacar('esquerda', 'medio')
    maos._sujo = False
    maos.destacar('esquerda', 'medio')      # mesmo dedo: nada a fazer
    assert maos._sujo is False
    maos.destacar('direita', 'medio')
    assert maos._sujo is True


def test_redimensionar_muda_o_tamanho_da_imagem(maos):
    assert _imagem(maos).size == (400, 264)
    maos.redimensionar(600, 396)
    assert _imagem(maos).size == (600, 396)
