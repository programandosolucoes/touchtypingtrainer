"""Testes do diagnóstico — leitura pura do histórico, sem tela e sem disco."""
import progresso


def _reg(data, wpm=20.0, tropecos=0, teclas_total=100, modo='licao', teclas=None):
    return {'quando': f'{data}T10:00:00-03:00', 'modo': modo, 'wpm_bruto': wpm,
            'tropecos': tropecos, 'total_teclas': teclas_total,
            'teclas': teclas or {}}


# --- evolução ----------------------------------------------------------------

def test_sem_historico_nao_ha_evolucao():
    assert progresso.evolucao_por_dia([]) == []


def test_agrupa_exercicios_do_mesmo_dia():
    dias = progresso.evolucao_por_dia([_reg('2026-08-14'), _reg('2026-08-14')])
    assert len(dias) == 1
    assert dias[0]['exercicios'] == 2


def test_os_dias_saem_em_ordem_crescente():
    dias = progresso.evolucao_por_dia(
        [_reg('2026-08-14'), _reg('2026-08-12'), _reg('2026-08-13')])
    assert [d['data'] for d in dias] == ['2026-08-12', '2026-08-13', '2026-08-14']


def test_wpm_medio_e_melhor_do_dia():
    dias = progresso.evolucao_por_dia(
        [_reg('2026-08-14', wpm=10.0), _reg('2026-08-14', wpm=20.0)])
    assert dias[0]['wpm_medio'] == 15.0
    assert dias[0]['melhor_wpm'] == 20.0


def test_precisao_vem_dos_tropecos_e_nao_do_texto_final():
    # No Modo Lição o texto final é sempre perfeito (a trava impede erro), então
    # precisão só significa alguma coisa se vier do tropeço.
    dias = progresso.evolucao_por_dia([_reg('2026-08-14', tropecos=5, teclas_total=100)])
    assert dias[0]['precisao'] == 95.0


def test_dia_sem_tecla_nenhuma_nao_divide_por_zero():
    dias = progresso.evolucao_por_dia([_reg('2026-08-14', teclas_total=0)])
    assert dias[0]['precisao'] == 100.0


def test_registro_sem_data_e_ignorado_em_vez_de_estourar():
    assert progresso.evolucao_por_dia([{'modo': 'licao'}]) == []


def test_filtro_por_modo_separa_licao_de_treino_livre():
    registros = [_reg('2026-08-14', modo='licao'), _reg('2026-08-14', modo='livre')]
    assert progresso.evolucao_por_dia(registros, modo='licao')[0]['exercicios'] == 1


# --- tendência ---------------------------------------------------------------

def test_tendencia_indefinida_com_um_dia_so():
    assert progresso.esta_melhorando(progresso.evolucao_por_dia([_reg('2026-08-14')])) is None


def test_tendencia_positiva_quando_o_wpm_sobe():
    registros = [_reg('2026-08-0%d' % d, wpm=10.0) for d in (1, 2, 3)] + \
                [_reg('2026-08-0%d' % d, wpm=20.0) for d in (4, 5, 6)]
    tendencia = progresso.esta_melhorando(progresso.evolucao_por_dia(registros), dias=3)
    assert tendencia == 10.0


def test_tendencia_negativa_quando_o_wpm_cai():
    registros = [_reg('2026-08-0%d' % d, wpm=25.0) for d in (1, 2, 3)] + \
                [_reg('2026-08-0%d' % d, wpm=15.0) for d in (4, 5, 6)]
    assert progresso.esta_melhorando(progresso.evolucao_por_dia(registros), dias=3) == -10.0


# --- ranking de teclas -------------------------------------------------------

def _com_teclas(**por_tecla):
    """Monta um registro com o resumo por tecla já no formato do histórico."""
    teclas = {}
    for tecla, (acertos, erros, confusoes) in por_tecla.items():
        teclas[tecla] = {'acertos': acertos, 'erros': erros, 'ms_medio': 300,
                         'confusoes': confusoes}
    return _reg('2026-08-14', teclas=teclas)


def test_tecla_com_poucas_cobrancas_fica_de_fora():
    # 1 erro em 2 tentativas daria 50% e lideraria o ranking sem significar nada.
    registros = [_com_teclas(j=(1, 1, {'k': 1}))]
    assert progresso.ranking_de_teclas(registros) == []


def test_a_tecla_mais_errada_vem_primeiro():
    registros = [_com_teclas(j=(10, 10, {'k': 10}), a=(19, 1, {'s': 1}))]
    ranking = progresso.ranking_de_teclas(registros)
    assert ranking[0]['tecla'] == 'j'
    assert ranking[0]['taxa'] == 50.0


def test_o_ranking_soma_varios_exercicios():
    registros = [_com_teclas(j=(5, 5, {'k': 5})), _com_teclas(j=(5, 5, {'k': 5}))]
    assert progresso.ranking_de_teclas(registros)[0]['cobrancas'] == 20


def test_o_ranking_diz_qual_tecla_foi_digitada_no_lugar():
    # É a confusão que revela dedo errado: k no lugar de j é médio no lugar de
    # indicador. O erro sozinho não diz isso.
    registros = [_com_teclas(j=(10, 10, {'k': 8, 'h': 2}))]
    assert progresso.ranking_de_teclas(registros)[0]['confusao'] == ('k', 8)


def test_tecla_sem_erro_nenhum_nao_tem_confusao():
    registros = [_com_teclas(a=(20, 0, {}))]
    assert progresso.ranking_de_teclas(registros)[0]['confusao'] is None


# --- ranking de dedos --------------------------------------------------------

def test_agrupa_os_erros_por_dedo():
    # j e k são da mão direita: indicador e médio.
    registros = [_com_teclas(j=(10, 10, {'k': 10}), k=(18, 2, {'j': 2}))]
    ranking = progresso.ranking_de_dedos(registros, 'us')
    pior = ranking[0]
    assert (pior['mao'], pior['dedo']) == ('direita', 'indicador')
    assert pior['taxa'] == 50.0


def test_o_dedo_junta_todas_as_teclas_dele():
    # No US, `a` é mínimo esquerdo e `q` também.
    registros = [_com_teclas(a=(8, 2, {'s': 2}), q=(8, 2, {'w': 2}))]
    ranking = progresso.ranking_de_dedos(registros, 'us')
    minimo = [d for d in ranking if d['dedo'] == 'minimo'][0]
    assert minimo['cobrancas'] == 20
    assert minimo['erros'] == 4


def test_tecla_fora_do_layout_nao_entra_no_ranking_de_dedos():
    # Histórico gravado noutro idioma não pode contaminar o diagnóstico.
    registros = [_com_teclas(**{'ç': (10, 10, {'l': 10})})]
    assert progresso.ranking_de_dedos(registros, 'us') == []


# --- treino dirigido ---------------------------------------------------------

def test_sugere_as_piores_teclas_para_treinar():
    registros = [_com_teclas(j=(10, 10, {'k': 10}), a=(19, 1, {'s': 1}),
                             f=(20, 0, {}))]
    alvo = progresso.teclas_para_treinar(registros)
    assert alvo[0] == 'j'
    assert 'f' not in alvo          # sem erro não é ponto fraco


def test_limita_a_quantidade_pedida():
    registros = [_com_teclas(**{c: (5, 5, {'x': 5}) for c in 'asdfjkl'})]
    assert len(progresso.teclas_para_treinar(registros, quantas=3)) == 3


def test_sem_erro_nenhum_nao_ha_o_que_treinar():
    assert progresso.teclas_para_treinar([_com_teclas(a=(20, 0, {}))]) == ()


# --- resumo ------------------------------------------------------------------

def test_resumo_traz_tudo_de_uma_vez():
    registros = [_com_teclas(j=(10, 10, {'k': 10}))]
    r = progresso.resumo(registros, 'us')
    assert set(r) == {'exercicios', 'dias', 'evolucao', 'tendencia', 'teclas',
                      'dedos', 'para_treinar'}
    assert r['exercicios'] == 1


def test_resumo_de_historico_vazio_nao_estoura():
    r = progresso.resumo([], 'us')
    assert r['exercicios'] == 0
    assert r['tendencia'] is None
    assert r['teclas'] == [] and r['dedos'] == []
