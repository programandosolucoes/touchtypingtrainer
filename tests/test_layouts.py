"""Testes dos três layouts e do mapa tecla→dedo."""
import pytest

import layouts

TODOS = ('abnt2', 'us', 'it')


@pytest.mark.parametrize('nome', TODOS)
def test_toda_tecla_tem_mao_e_dedo(nome):
    for tecla in layouts.teclas(nome):
        assert tecla.mao in ('esquerda', 'direita'), tecla
        assert tecla.dedo in ('minimo', 'anelar', 'medio', 'indicador'), tecla


@pytest.mark.parametrize('nome', TODOS)
def test_nao_ha_caractere_repetido_no_layout(nome):
    caracteres = [t.caractere for t in layouts.teclas(nome)]
    assert len(caracteres) == len(set(caracteres))


@pytest.mark.parametrize('nome', TODOS)
def test_linha_base_tem_asdf_na_esquerda(nome):
    esquerda, _ = layouts.teclas_base(nome)
    assert esquerda == ('a', 's', 'd', 'f')


def test_a_quarta_tecla_da_base_direita_muda_por_layout():
    assert layouts.teclas_base('us')[1] == ('j', 'k', 'l', ';')
    assert layouts.teclas_base('abnt2')[1] == ('j', 'k', 'l', 'ç')
    assert layouts.teclas_base('it')[1] == ('j', 'k', 'l', 'ò')


def test_dedo_da_linha_base_segue_o_padrao_do_toque():
    assert layouts.dedo_de('a', 'us') == ('esquerda', 'minimo')
    assert layouts.dedo_de('f', 'us') == ('esquerda', 'indicador')
    assert layouts.dedo_de('g', 'us') == ('esquerda', 'indicador')
    assert layouts.dedo_de('j', 'us') == ('direita', 'indicador')
    assert layouts.dedo_de('k', 'us') == ('direita', 'medio')
    assert layouts.dedo_de(';', 'us') == ('direita', 'minimo')


def test_dedo_de_caractere_desconhecido_e_none():
    assert layouts.dedo_de('€', 'us') is None


def test_ce_cedilha_so_existe_no_abnt2():
    assert layouts.dedo_de('ç', 'abnt2') == ('direita', 'minimo')
    assert layouts.dedo_de('ç', 'us') is None


def test_retangulos_cabem_dentro_da_area_pedida():
    rets = layouts.retangulos('us', 1000.0, 300.0)
    assert rets['a'][0] >= 0 and rets['a'][1] >= 0
    for x0, y0, x1, y1 in rets.values():
        assert 0 <= x0 < x1 <= 1000.0
        assert 0 <= y0 < y1 <= 300.0


def test_linha_de_baixo_comeca_mais_a_direita_que_a_de_cima():
    # O escalonamento das linhas é o que faz o desenho parecer um teclado.
    rets = layouts.retangulos('us', 1000.0, 300.0)
    assert rets['z'][0] > rets['q'][0] > rets['1'][0]


def test_retangulos_acompanham_a_area_pedida():
    # O teclado precisa redesenhar proporcional quando a janela muda de tamanho.
    pequeno = layouts.retangulos('us', 500.0, 150.0)
    grande = layouts.retangulos('us', 1000.0, 300.0)
    assert grande['a'][2] > pequeno['a'][2]


def test_caracteres_da_linha_devolve_a_linha_base():
    assert layouts.caracteres_da_linha('us', 2) == "asdfghjkl;'"
