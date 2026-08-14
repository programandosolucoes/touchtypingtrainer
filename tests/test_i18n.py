"""Testes do dicionário de traduções.

O defeito clássico deste arquivo é a chave que existe num idioma e não nos
outros: o programa só quebra quando alguém troca de idioma na tela certa.
"""
import pytest

import i18n

IDIOMAS = ('en', 'it', 'pt')


def _todas_as_chaves():
    chaves = set()
    for idioma in IDIOMAS:
        chaves.update(i18n.translations[idioma])
    # `key_right_of_p_char_<idioma>` existe por idioma de propósito.
    return {c for c in chaves if not c.startswith('key_right_of_p_char_')}


@pytest.mark.parametrize('idioma', IDIOMAS)
def test_nenhuma_chave_cai_no_marcador_de_traducao_faltando(idioma):
    # O contrato do get_text é cair para o inglês; o que não pode acontecer é
    # sobrar `<chave NG>` na tela. Cor de caractere, por exemplo, só existe em
    # inglês de propósito — cor não se traduz — e chega aos outros por herança.
    for chave in _todas_as_chaves():
        valor = i18n.get_text(chave, idioma)
        assert not (isinstance(valor, str) and valor.startswith('<') and 'NG' in valor), \
            (idioma, chave, valor)


@pytest.mark.parametrize('idioma', IDIOMAS)
def test_todo_texto_do_modo_licao_e_traduzido_de_verdade(idioma):
    # Aqui, ao contrário das cores, herdar do inglês seria defeito: são frases
    # que o aluno lê. Cada idioma precisa da sua.
    do_modo_licao = [c for c in i18n.translations['pt']
                     if c.startswith(('licao_', 'menu_', 'historico_'))]
    assert do_modo_licao
    for chave in do_modo_licao:
        assert chave in i18n.translations[idioma], (idioma, chave)


@pytest.mark.parametrize('idioma', IDIOMAS)
def test_todas_as_chaves_do_modo_licao_existem(idioma):
    for chave in ('menu_modo_licao', 'licao_titulo', 'licao_teste_esquerda',
                  'licao_teste_direita', 'licao_teste_sequencial',
                  'licao_layout_diferente', 'licao_comecar', 'licao_digite',
                  'licao_relatorio_titulo', 'licao_faltou_regularidade',
                  'licao_para_avancar', 'historico_caiu_para_usuario'):
        assert i18n.get_text(chave, idioma), (idioma, chave)


@pytest.mark.parametrize('idioma', IDIOMAS)
def test_os_marcadores_de_formato_batem_entre_idiomas(idioma):
    # Um texto com {} a menos estoura no `.format()` só quando aquela tela abre.
    for chave, esperados in (('licao_titulo', 2), ('licao_criterio', 2),
                             ('licao_progresso', 2), ('licao_tempo', 2),
                             ('licao_wpm', 2), ('licao_tropecos_de', 2),
                             ('licao_layout_diferente', 2),
                             ('licao_para_avancar', 2),
                             ('licao_relatorio_titulo', 1),
                             ('licao_regularidade', 1), ('licao_reprovado', 1),
                             ('historico_caiu_para_usuario', 1)):
        texto = i18n.get_text(chave, idioma)
        assert texto.count('{') == esperados, (idioma, chave, texto)
