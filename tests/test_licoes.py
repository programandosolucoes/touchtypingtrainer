"""Testes do currículo, do gerador de exercício e do critério de aprovação."""
import pytest

import layouts
import licoes

TODOS = ('abnt2', 'us', 'it')


@pytest.mark.parametrize('nome', TODOS)
def test_curriculo_tem_doze_niveis_numerados_em_ordem(nome):
    niveis = licoes.curriculo(nome)
    assert len(niveis) == 12
    assert [n.numero for n in niveis] == list(range(1, 13))


@pytest.mark.parametrize('nome', TODOS)
def test_meta_de_wpm_nunca_cai_de_um_nivel_para_o_seguinte(nome):
    metas = [n.wpm_meta for n in licoes.curriculo(nome)]
    assert metas == sorted(metas)


def test_primeiro_nivel_e_so_a_base_esquerda():
    assert licoes.curriculo('us')[0].teclas_novas == ('a', 's', 'd', 'f')


def test_segundo_nivel_usa_a_quarta_tecla_do_layout():
    assert licoes.curriculo('us')[1].teclas_novas == ('j', 'k', 'l', ';')
    assert licoes.curriculo('abnt2')[1].teclas_novas == ('j', 'k', 'l', 'ç')


def test_teclas_liberadas_acumulam_dos_niveis_anteriores():
    liberadas = licoes.teclas_liberadas('us', 2)
    assert liberadas == frozenset('asdfjkl;')


def test_nivel_tres_libera_o_espaco():
    assert ' ' in licoes.teclas_liberadas('us', 3)


@pytest.mark.parametrize('nome', TODOS)
def test_toda_tecla_nova_existe_no_layout(nome):
    for nivel in licoes.curriculo(nome):
        for tecla in nivel.teclas_novas:
            if tecla in (' ',) or tecla.isupper() or tecla.isdigit():
                continue
            assert layouts.dedo_de(tecla, nome) is not None, (nome, nivel.id, tecla)


@pytest.mark.parametrize('nome', TODOS)
def test_nenhuma_tecla_e_apresentada_como_nova_duas_vezes(nome):
    # `ç` (nível 2) reaparecia como "símbolo novo" no nível 11, e `,`/`.` do
    # nível 8 também. Ensinar a mesma tecla duas vezes desperdiça o nível.
    vistas = set()
    for nivel in licoes.curriculo(nome):
        for tecla in nivel.teclas_novas:
            assert tecla not in vistas, (nome, nivel.id, tecla)
            vistas.add(tecla)


@pytest.mark.parametrize('nome', TODOS)
def test_nivel_de_maiusculas_so_traz_letras(nome):
    # `;` em maiúscula continua `;`: entraria repetindo o nível 2 sem ensinar
    # Shift nenhum.
    maiusculas = licoes.curriculo(nome)[8].teclas_novas
    assert maiusculas, nome
    assert all(c.isalpha() and c.isupper() for c in maiusculas), maiusculas


@pytest.mark.parametrize('nome', TODOS)
def test_simbolos_nao_repetem_letra_asc_ii_nem_digito(nome):
    # Letra acentuada PODE aparecer aqui: `à ù è ì` são teclas próprias do
    # teclado italiano e nunca foram ensinadas antes. O que não pode voltar é
    # letra ASCII ou dígito, ensinados nos níveis 1 a 10.
    simbolos = licoes.curriculo(nome)[10].teclas_novas
    ja_ensinadas = set('abcdefghijklmnopqrstuvwxyz0123456789')
    assert all(c not in ja_ensinadas for c in simbolos), (nome, simbolos)


def test_limite_de_tempo_da_o_dobro_do_tempo_da_meta():
    # 60 caracteres = 12 palavras; a 10 WPM levaria 72s; o limite é o dobro.
    assert licoes.limite_de_tempo(60, 10) == pytest.approx(144.0)


def test_exercicio_so_usa_teclas_ja_liberadas():
    permitidas = licoes.teclas_liberadas('us', 5)
    texto = licoes.gerar_exercicio('us', 5, semente=42)
    assert set(texto) <= permitidas | {' '}


def test_mesma_semente_gera_o_mesmo_exercicio():
    a = licoes.gerar_exercicio('us', 4, semente=7)
    b = licoes.gerar_exercicio('us', 4, semente=7)
    assert a == b


def test_sementes_diferentes_geram_exercicios_diferentes():
    a = licoes.gerar_exercicio('us', 4, semente=7)
    b = licoes.gerar_exercicio('us', 4, semente=8)
    assert a != b


def test_primeiro_nivel_nao_usa_teclas_da_mao_direita():
    texto = licoes.gerar_exercicio('us', 1, semente=1)
    assert set(texto) <= set('asdf ')


def test_nivel_de_maiusculas_produz_maiusculas():
    texto = licoes.gerar_exercicio('us', 9, semente=3)
    assert any(c.isupper() for c in texto)


def test_nivel_de_numeros_produz_digitos():
    texto = licoes.gerar_exercicio('us', 10, semente=3)
    assert any(c.isdigit() for c in texto)


def test_exercicio_nao_e_vazio_em_nenhum_nivel():
    for numero in range(1, 12):
        assert licoes.gerar_exercicio('abnt2', numero, semente=numero).strip()


def test_filtrar_frases_descarta_as_que_usam_tecla_nao_liberada():
    frases = ['dad fads', 'quick brown fox']
    permitidas = licoes.teclas_liberadas('us', 3)
    assert licoes.filtrar_frases(frases, permitidas) == ['dad fads']


def test_filtrar_frases_ignora_diferenca_de_caixa():
    permitidas = licoes.teclas_liberadas('us', 3)
    assert licoes.filtrar_frases(['DAD'], permitidas) == ['DAD']


def _resultado(**mudancas):
    """Um resultado que passa em tudo; os testes pioram um critério de cada vez."""
    base = {'tropecos': 0, 'total_teclas': 100, 'wpm_bruto': 20.0,
            'regularidade': 0.99, 'duracao_s': 30.0, 'limite_s': 60.0}
    base.update(mudancas)
    return base


NIVEL_1 = licoes.curriculo('us')[0] if hasattr(licoes, 'curriculo') else None


def test_aprova_quando_os_quatro_criterios_passam():
    assert licoes.avaliar(_resultado(), NIVEL_1).aprovado is True


def test_reprova_por_tropecos_e_diz_qual_criterio_faltou():
    a = licoes.avaliar(_resultado(tropecos=10), NIVEL_1)
    assert a.aprovado is False
    assert a.faltou == ('tropecos',)


def test_reprova_por_wpm_abaixo_da_meta():
    a = licoes.avaliar(_resultado(wpm_bruto=5.0), NIVEL_1)
    assert a.faltou == ('wpm',)


def test_reprova_por_ritmo_irregular_mesmo_sem_errar_nada():
    # 100% de acerto lento e picotado NÃO passa: é o caso de quem caça a tecla.
    a = licoes.avaliar(_resultado(regularidade=0.50), NIVEL_1)
    assert a.faltou == ('regularidade',)


def test_reprova_por_estourar_o_tempo():
    a = licoes.avaliar(_resultado(duracao_s=90.0), NIVEL_1)
    assert a.faltou == ('tempo',)


def test_regularidade_indefinida_nao_reprova():
    # Exercício curto demais para medir ritmo não pode punir ninguém.
    assert licoes.avaliar(_resultado(regularidade=None), NIVEL_1).aprovado is True


def test_lista_todos_os_criterios_que_faltaram():
    a = licoes.avaliar(_resultado(tropecos=10, wpm_bruto=1.0), NIVEL_1)
    assert set(a.faltou) == {'tropecos', 'wpm'}


def test_comeca_no_nivel_um_sem_historico():
    assert licoes.nivel_atual([], 'us').numero == 1


def test_uma_aprovacao_isolada_nao_libera_o_proximo_nivel():
    registros = [{'modo': 'licao', 'nivel': 'base-esquerda', 'aprovado': True}]
    assert licoes.nivel_atual(registros, 'us').numero == 1


def test_duas_aprovacoes_seguidas_liberam_o_proximo():
    registros = [{'modo': 'licao', 'nivel': 'base-esquerda', 'aprovado': True}] * 2
    assert licoes.nivel_atual(registros, 'us').numero == 2


def test_reprovar_no_meio_zera_a_contagem():
    registros = [
        {'modo': 'licao', 'nivel': 'base-esquerda', 'aprovado': True},
        {'modo': 'licao', 'nivel': 'base-esquerda', 'aprovado': False},
        {'modo': 'licao', 'nivel': 'base-esquerda', 'aprovado': True},
    ]
    assert licoes.nivel_atual(registros, 'us').numero == 1


def test_exercicio_do_modo_livre_nao_conta_para_a_progressao():
    registros = [{'modo': 'livre', 'nivel': None, 'aprovado': True}] * 5
    assert licoes.nivel_atual(registros, 'us').numero == 1


def test_aprovacoes_seguidas_comeca_em_zero():
    assert licoes.aprovacoes_seguidas([], NIVEL_1) == 0


def test_aprovacoes_seguidas_conta_uma():
    registros = [{'modo': 'licao', 'nivel': 'base-esquerda', 'aprovado': True}]
    assert licoes.aprovacoes_seguidas(registros, NIVEL_1) == 1


def test_aprovacoes_seguidas_zera_ao_reprovar():
    registros = [
        {'modo': 'licao', 'nivel': 'base-esquerda', 'aprovado': True},
        {'modo': 'licao', 'nivel': 'base-esquerda', 'aprovado': False},
    ]
    assert licoes.aprovacoes_seguidas(registros, NIVEL_1) == 0


def test_aprovacoes_seguidas_zera_ao_completar_a_dupla():
    # Duas seguidas liberam o próximo nível; a contagem deste recomeça do zero.
    registros = [{'modo': 'licao', 'nivel': 'base-esquerda', 'aprovado': True}] * 2
    assert licoes.aprovacoes_seguidas(registros, NIVEL_1) == 0


def test_aprovacoes_seguidas_ignora_o_treino_livre():
    registros = [{'modo': 'livre', 'nivel': None, 'aprovado': True}] * 3
    assert licoes.aprovacoes_seguidas(registros, NIVEL_1) == 0


def test_nao_passa_do_ultimo_nivel():
    registros = [{'modo': 'licao', 'nivel': n.id, 'aprovado': True}
                 for n in licoes.curriculo('us') for _ in range(2)]
    assert licoes.nivel_atual(registros, 'us').numero == 12
