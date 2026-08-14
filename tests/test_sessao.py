"""Testes da sessão: série de exercícios, escolha de nível e gravação."""
import licoes
import metricas
import sessao as mod_sessao


def _perfeito(texto):
    return {'batidas': [metricas.Batida(c, c, 200.0) for c in texto],
            'duracao_s': 20.0, 'cancelado': False}


def _nova(tmp_path, idioma='pt'):
    return mod_sessao.Sessao(idioma, tmp_path / 'progresso.jsonl')


def test_comeca_no_primeiro_nivel(tmp_path):
    assert _nova(tmp_path).nivel.numero == 1


def test_serie_tem_tamanho_padrao(tmp_path):
    s = _nova(tmp_path)
    assert s.tamanho_da_serie == mod_sessao.PADRAO_DE_SERIE
    assert s.tamanho_da_serie in mod_sessao.EXERCICIOS_POR_SERIE


def test_iniciar_serie_troca_o_tamanho_e_zera_o_indice(tmp_path):
    s = _nova(tmp_path)
    s.indice_na_serie = 2
    s.iniciar_serie(5)
    assert (s.tamanho_da_serie, s.indice_na_serie) == (5, 0)


def test_tem_proximo_ate_o_fim_da_serie(tmp_path):
    s = _nova(tmp_path)
    s.iniciar_serie(3)
    assert s.tem_proximo()
    s.avancar()
    assert s.tem_proximo()
    s.avancar()
    assert not s.tem_proximo()      # 3 de 3


def test_serie_de_um_nao_tem_proximo(tmp_path):
    s = _nova(tmp_path)
    s.iniciar_serie(1)
    assert not s.tem_proximo()


def test_o_texto_e_estavel_dentro_do_mesmo_exercicio(tmp_path):
    s = _nova(tmp_path)
    assert s.texto_do_exercicio() == s.texto_do_exercicio()


def test_avancar_gera_texto_novo(tmp_path):
    s = _nova(tmp_path)
    s.iniciar_serie(5)
    primeiro = s.texto_do_exercicio()
    s.avancar()
    # Semente nova a cada exercício; repetir o mesmo texto seria decorar, não treinar.
    assert s.semente is None
    assert s.texto_do_exercicio() is not None
    assert primeiro is not None


def test_concluir_grava_e_devolve_a_avaliacao(tmp_path):
    s = _nova(tmp_path)
    texto = s.texto_do_exercicio()
    registro, avaliacao = s.concluir_exercicio(texto, _perfeito(texto))
    assert registro['modo'] == 'licao'
    assert avaliacao.aprovado
    assert s.ultimo_resultado == (registro, avaliacao)


def test_o_registro_guarda_a_posicao_na_serie(tmp_path):
    s = _nova(tmp_path)
    s.iniciar_serie(5)
    s.avancar()
    texto = s.texto_do_exercicio()
    registro, _ = s.concluir_exercicio(texto, _perfeito(texto))
    assert registro['serie'] == [2, 5]


def test_duas_aprovacoes_avancam_o_nivel(tmp_path):
    s = _nova(tmp_path)
    s.iniciar_serie(5)
    for _ in range(2):
        texto = s.texto_do_exercicio()
        s.concluir_exercicio(texto, _perfeito(texto))
        s.avancar()
    assert s.nivel.numero == 2


def test_so_da_para_escolher_nivel_ja_liberado(tmp_path):
    s = _nova(tmp_path)
    assert [n.numero for n in s.niveis_disponiveis()] == [1]
    assert s.escolher_nivel(5) is False       # pular adiante não pode
    assert s.nivel.numero == 1


def test_niveis_disponiveis_crescem_conforme_a_progressao(tmp_path):
    s = _nova(tmp_path)
    s.iniciar_serie(5)
    for _ in range(2):
        texto = s.texto_do_exercicio()
        s.concluir_exercicio(texto, _perfeito(texto))
        s.avancar()
    assert [n.numero for n in s.niveis_disponiveis()] == [1, 2]


def test_da_para_voltar_a_um_nivel_ja_passado(tmp_path):
    s = _nova(tmp_path)
    s.iniciar_serie(5)
    for _ in range(2):
        texto = s.texto_do_exercicio()
        s.concluir_exercicio(texto, _perfeito(texto))
        s.avancar()
    assert s.escolher_nivel(1) is True
    assert s.nivel.numero == 1


def test_treinar_nivel_antigo_nao_rebaixa_o_progresso(tmp_path):
    # Revisar o nível 1 não pode fazer o aluno "voltar" — o currículo já liberou
    # o 2 e ele continua liberado.
    s = _nova(tmp_path)
    s.iniciar_serie(5)
    for _ in range(2):
        texto = s.texto_do_exercicio()
        s.concluir_exercicio(texto, _perfeito(texto))
        s.avancar()
    s.escolher_nivel(1)
    texto = s.texto_do_exercicio()
    s.concluir_exercicio(texto, _perfeito(texto))
    assert s.nivel.numero == 1                       # continua onde escolheu
    assert max(n.numero for n in s.niveis_disponiveis()) == 2


def test_registrar_sem_rollover_persiste(tmp_path):
    s = _nova(tmp_path)
    assert s.teclado_sem_rollover is False
    s.registrar_sem_rollover()
    assert s.teclado_sem_rollover is True
    assert _nova(tmp_path).teclado_sem_rollover is True


def test_rotulo_da_serie_conta_a_partir_de_um(tmp_path):
    s = _nova(tmp_path)
    s.iniciar_serie(5)
    assert '1' in s.rotulo_da_serie('pt') and '5' in s.rotulo_da_serie('pt')
