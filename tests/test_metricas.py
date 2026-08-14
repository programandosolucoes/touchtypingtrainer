"""Testes das métricas puras — nada aqui importa GUI."""
import metricas


def test_wpm_usa_padrao_de_cinco_caracteres_por_palavra():
    # 60 caracteres = 12 "palavras"; em 60 segundos dá 12 WPM
    assert metricas.wpm(60, 60.0) == 12.0


def test_wpm_com_duracao_zero_nao_divide_por_zero():
    assert metricas.wpm(50, 0.0) == 0.0


def test_wpm_com_texto_vazio_e_zero():
    assert metricas.wpm(0, 30.0) == 0.0


def test_wpm_liquido_desconta_erros_por_minuto():
    # 60 caracteres em 60s = 12 WPM bruto; 2 erros em 1 minuto tira 2
    assert metricas.wpm_liquido(60, 60.0, 2) == 10.0


def test_wpm_liquido_tem_piso_em_zero():
    # erros demais não podem gerar WPM negativo
    assert metricas.wpm_liquido(60, 60.0, 99) == 0.0


def test_regularidade_perfeita_quando_o_ritmo_e_constante():
    # 3 de aquecimento descartadas + 12 intervalos iguais
    assert metricas.regularidade([200.0] * 15) == 1.0


def test_regularidade_ignora_uma_pausa_isolada_longa():
    # Uma pausa de 2s no meio (o telefone tocou) derruba o índice, mas pouco:
    # 1 parada em 12 intervalos contados.
    intervalos = [200.0] * 15
    intervalos[8] = 2000.0
    assert metricas.regularidade(intervalos) == round(1 - 1 / 12, 4)


def test_regularidade_usa_mediana_e_nao_media():
    # Com média, a pausa de 5s puxaria o limiar para cima e nenhuma parada
    # seria detectada. Com mediana, a parada aparece.
    intervalos = [100.0] * 15
    intervalos[7] = 5000.0
    assert metricas.regularidade(intervalos) < 1.0


def test_regularidade_descarta_as_tres_primeiras_teclas():
    # Reação inicial lenta não é hesitação: as 3 primeiras não contam.
    intervalos = [3000.0, 3000.0, 3000.0] + [200.0] * 12
    assert metricas.regularidade(intervalos) == 1.0


def test_regularidade_sem_intervalos_suficientes_e_indefinida():
    # Exercício curto demais não recebe índice — e não reprova ninguém.
    assert metricas.regularidade([200.0] * 12) is None


def test_regularidade_com_mediana_zero_e_indefinida():
    # Caso degenerado (relógio sem resolução): não inventa nota.
    assert metricas.regularidade([0.0] * 20) is None


def test_tropecos_conta_cada_tecla_errada():
    batidas = [
        metricas.Batida('a', 'a', 200.0),
        metricas.Batida('s', 'd', 300.0),
        metricas.Batida('s', 's', 250.0),
    ]
    assert metricas.tropecos(batidas) == 1


def test_resumo_por_tecla_agrupa_pelo_caractere_esperado():
    batidas = [
        metricas.Batida('a', 'a', 200.0),
        metricas.Batida('a', 's', 400.0),
        metricas.Batida('a', 'a', 300.0),
    ]
    resumo = metricas.resumo_por_tecla(batidas)
    assert resumo['a']['acertos'] == 2
    assert resumo['a']['erros'] == 1
    assert resumo['a']['ms_medio'] == 300


def test_resumo_registra_o_que_foi_digitado_no_lugar():
    # É esse par que revela dedo trocado: esperava j, saiu k = médio no lugar
    # do indicador.
    batidas = [
        metricas.Batida('j', 'k', 400.0),
        metricas.Batida('j', 'k', 380.0),
        metricas.Batida('j', 'h', 350.0),
    ]
    resumo = metricas.resumo_por_tecla(batidas)
    assert resumo['j']['confusoes'] == {'k': 2, 'h': 1}


def test_resumo_de_lista_vazia_e_dicionario_vazio():
    assert metricas.resumo_por_tecla([]) == {}
