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
