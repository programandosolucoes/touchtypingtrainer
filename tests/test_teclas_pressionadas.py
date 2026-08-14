"""Testes do filtro de auto-repeat, sem abrir janela nenhuma."""
import teclas_pressionadas


def test_tecla_pressionada_fica_ativa():
    r = teclas_pressionadas.Rastreador()
    r.pressionou('a', 0.0)
    assert r.ativas(10.0) == {'a'}


def test_quatro_teclas_simultaneas():
    r = teclas_pressionadas.Rastreador()
    for i, k in enumerate('asdf'):
        r.pressionou(k, i * 5.0)
    assert r.ativas(30.0) == {'a', 's', 'd', 'f'}


def test_soltar_de_verdade_desativa_a_tecla():
    r = teclas_pressionadas.Rastreador()
    r.pressionou('a', 0.0)
    r.soltou('a', 100.0)
    assert r.ativas(200.0) == set()


def test_auto_repeat_nao_desativa_a_tecla():
    # X11 segurando a tecla: release e press colados. Ingenuamente pareceria
    # que o usuário soltou, e o teste de mãos piscaria sem nunca fechar.
    r = teclas_pressionadas.Rastreador()
    r.pressionou('f', 0.0)
    r.soltou('f', 500.0)
    r.pressionou('f', 510.0)      # 10 ms depois: é auto-repeat
    assert r.ativas(600.0) == {'f'}


def test_soltar_so_vale_depois_da_janela_de_auto_repeat():
    r = teclas_pressionadas.Rastreador()
    r.pressionou('f', 0.0)
    r.soltou('f', 500.0)
    assert r.ativas(520.0) == {'f'}     # ainda na dúvida, mantém
    assert r.ativas(560.0) == set()     # passou dos 50 ms, soltou mesmo


def test_pressionar_de_novo_nao_reinicia_o_instante():
    r = teclas_pressionadas.Rastreador()
    r.pressionou('a', 0.0)
    r.pressionou('a', 100.0)
    assert r.desde('a') == 0.0


def test_soltar_tecla_que_nunca_foi_pressionada_e_ignorado():
    r = teclas_pressionadas.Rastreador()
    r.soltou('z', 10.0)
    assert r.ativas(100.0) == set()
