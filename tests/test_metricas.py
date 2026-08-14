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
