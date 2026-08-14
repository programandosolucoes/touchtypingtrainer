"""Testa a parte SEM GUI do Modo Lição: mapeamento de teclas e registro.

A tela em si é conferida à mão (`docs/BUILD.md`), mas o mapeamento keysym→
caractere e a montagem do registro são lógica pura — e são justamente onde um
erro passa despercebido, porque a tela continua abrindo bonita.
"""
import json

import licoes
import metricas
import modo_licao


def _resultado_perfeito(texto):
    batidas = [metricas.Batida(c, c, 200.0) for c in texto]
    return {'batidas': batidas, 'duracao_s': 20.0, 'cancelado': False}


def test_letra_solta_vira_o_proprio_caractere():
    assert modo_licao.keysym_para_caractere('a') == 'a'
    assert modo_licao.keysym_para_caractere('A') == 'a'


def test_teclas_com_nome_viram_o_caractere_certo():
    assert modo_licao.keysym_para_caractere('ccedilla') == 'ç'
    assert modo_licao.keysym_para_caractere('semicolon') == ';'
    assert modo_licao.keysym_para_caractere('space') == ' '
    assert modo_licao.keysym_para_caractere('ograve') == 'ò'


def test_modificador_e_navegacao_nao_sao_resposta():
    # Se Shift contasse como resposta, apertar Shift para a maiúscula marcaria
    # tropeço — e o nível 9 seria impossível de passar.
    for keysym in ('Shift_L', 'Control_L', 'Alt_R', 'BackSpace', 'Left', 'Tab'):
        assert modo_licao.keysym_para_caractere(keysym) is None


def test_keysym_desconhecido_e_none():
    assert modo_licao.keysym_para_caractere('F13') is None
    assert modo_licao.keysym_para_caractere('') is None


def test_toda_tecla_dos_tres_layouts_tem_keysym_conhecido():
    # Sem isto, uma tecla do layout seria impossível de digitar no exercício:
    # o programa a cobraria e nunca aceitaria a resposta.
    import layouts
    nomeados = set(modo_licao._KEYSYM_PARA_CARACTERE.values())
    for nome in ('abnt2', 'us', 'it'):
        for tecla in layouts.teclas(nome):
            c = tecla.caractere
            assert len(c) == 1
            # Ou é digitável como letra solta, ou tem nome mapeado.
            assert c.isalnum() or c in nomeados, (nome, c)


def test_descrever_tecla_diz_a_tecla_o_dedo_e_a_mao():
    # A cor sozinha não diz QUAL dedo usar sem decorar a legenda; o texto diz.
    texto = modo_licao.descrever_tecla('j', 'us', 'pt')
    assert 'J' in texto
    assert 'indicador' in texto
    assert 'direita' in texto


def test_descrever_tecla_nomeia_o_espaco_em_vez_de_mostrar_vazio():
    # Sem isto o aluno leria "Próxima tecla:    — ..." e não entenderia nada.
    assert 'ESPAÇO' in modo_licao.descrever_tecla(' ', 'us', 'pt')
    assert 'SPACE' in modo_licao.descrever_tecla(' ', 'us', 'en')


def test_descrever_tecla_traduz_dedo_e_mao():
    assert 'pinky' in modo_licao.descrever_tecla('a', 'us', 'en')
    assert 'mignolo' in modo_licao.descrever_tecla('a', 'it', 'it')


def test_descrever_tecla_fora_do_layout_devolve_so_o_rotulo():
    assert modo_licao.descrever_tecla('€', 'us', 'pt') == '€'


def test_descrever_toda_tecla_dos_tres_layouts_sem_estourar():
    import layouts
    for nome in ('abnt2', 'us', 'it'):
        for tecla in layouts.teclas(nome):
            for idioma in ('pt', 'en', 'it'):
                texto = modo_licao.descrever_tecla(tecla.caractere, nome, idioma)
                assert texto and 'NG' not in texto, (nome, idioma, tecla.caractere)


def test_registro_tem_os_campos_que_o_historico_espera():
    nivel = licoes.curriculo('us')[0]
    texto = licoes.gerar_exercicio('us', 1, semente=5)
    registro = modo_licao.montar_registro(nivel, 'us', 'en', texto, 5,
                                          _resultado_perfeito(texto))
    for campo in ('quando', 'modo', 'nivel', 'wpm_meta', 'idioma', 'layout', 'alvo',
                  'semente', 'duracao_s', 'limite_s', 'wpm_bruto', 'wpm_liquido',
                  'tropecos', 'total_teclas', 'regularidade', 'aprovado', 'teclas'):
        assert campo in registro, campo


def test_registro_de_licao_marca_o_modo_e_o_nivel():
    nivel = licoes.curriculo('us')[0]
    texto = licoes.gerar_exercicio('us', 1, semente=5)
    registro = modo_licao.montar_registro(nivel, 'us', 'en', texto, 5,
                                          _resultado_perfeito(texto))
    assert registro['modo'] == 'licao'
    assert registro['nivel'] == 'base-esquerda'


def test_exercicio_sem_erro_nenhum_nao_tem_tropecos():
    nivel = licoes.curriculo('us')[0]
    texto = licoes.gerar_exercicio('us', 1, semente=5)
    registro = modo_licao.montar_registro(nivel, 'us', 'en', texto, 5,
                                          _resultado_perfeito(texto))
    assert registro['tropecos'] == 0


def test_tecla_errada_aparece_como_tropeco_e_confusao():
    nivel = licoes.curriculo('us')[0]
    batidas = [metricas.Batida('a', 'a', 200.0), metricas.Batida('s', 'd', 200.0)]
    resultado = {'batidas': batidas, 'duracao_s': 5.0, 'cancelado': False}
    registro = modo_licao.montar_registro(nivel, 'us', 'en', 'as', 1, resultado)
    assert registro['tropecos'] == 1
    assert registro['teclas']['s']['confusoes'] == {'d': 1}


def test_wpm_conta_so_os_acertos():
    # A trava impede erro no texto, então o líquido tem de ser igual ao bruto.
    nivel = licoes.curriculo('us')[0]
    batidas = [metricas.Batida('a', 'a', 200.0)] * 25 + [metricas.Batida('s', 'd', 200.0)] * 5
    resultado = {'batidas': batidas, 'duracao_s': 60.0, 'cancelado': False}
    registro = modo_licao.montar_registro(nivel, 'us', 'en', 'a' * 25, 1, resultado)
    assert registro['wpm_bruto'] == registro['wpm_liquido']
    assert registro['wpm_bruto'] == 5.0      # 25 acertos / 5 / 1 minuto


def test_registro_e_serializavel_em_json():
    nivel = licoes.curriculo('abnt2')[0]
    texto = licoes.gerar_exercicio('abnt2', 1, semente=2)
    registro = modo_licao.montar_registro(nivel, 'abnt2', 'pt', texto, 2,
                                          _resultado_perfeito(texto))
    assert json.loads(json.dumps(registro, ensure_ascii=False))['alvo'] == texto


def test_registro_alimenta_a_avaliacao_sem_faltar_campo():
    # O `avaliar` lê o registro direto; um campo com nome trocado só apareceria
    # ao terminar um exercício de verdade.
    nivel = licoes.curriculo('us')[0]
    texto = licoes.gerar_exercicio('us', 1, semente=9)
    registro = modo_licao.montar_registro(nivel, 'us', 'en', texto, 9,
                                          _resultado_perfeito(texto))
    avaliacao = licoes.avaliar(registro, nivel)
    assert isinstance(avaliacao.aprovado, bool)
