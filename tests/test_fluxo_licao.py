"""Fluxo ponta a ponta do Modo Lição, sem GUI.

Cada módulo tem os seus testes; este cobre a costura entre eles, que é onde o
defeito de integração se esconde: nome de campo trocado entre quem grava e quem
lê, progressão que não avança, nível que reabre no lugar errado.
"""
import historico
import licoes
import metricas
import modo_licao


def _exercicio_perfeito(nivel, nome_layout, semente, duracao_s=20.0):
    """Um exercício em que o aluno acertou tudo, no ritmo constante da meta."""
    texto = licoes.gerar_exercicio(nome_layout, nivel.numero, semente)
    batidas = [metricas.Batida(c, c, 200.0) for c in texto]
    return texto, {'batidas': batidas, 'duracao_s': duracao_s, 'cancelado': False}


def _rodar(nivel, nome_layout, arquivo, semente, duracao_s=20.0):
    """Faz um exercício inteiro e grava, como o aplicativo faz."""
    texto, resultado = _exercicio_perfeito(nivel, nome_layout, semente, duracao_s)
    registro = modo_licao.montar_registro(nivel, nome_layout, 'pt', texto, semente,
                                          resultado)
    avaliacao = licoes.avaliar(registro, nivel)
    registro['aprovado'] = avaliacao.aprovado
    historico.gravar(registro, arquivo)
    return registro, avaliacao


def test_historico_vazio_comeca_no_primeiro_nivel(tmp_path):
    arquivo = tmp_path / 'progresso.jsonl'
    assert licoes.nivel_atual(historico.ler(arquivo), 'abnt2').numero == 1


def test_dois_exercicios_perfeitos_liberam_o_segundo_nivel(tmp_path):
    arquivo = tmp_path / 'progresso.jsonl'
    nivel = licoes.nivel_atual(historico.ler(arquivo), 'abnt2')

    _, avaliacao = _rodar(nivel, 'abnt2', arquivo, semente=1)
    assert avaliacao.aprovado, avaliacao.faltou
    assert licoes.nivel_atual(historico.ler(arquivo), 'abnt2').numero == 1

    _rodar(nivel, 'abnt2', arquivo, semente=2)
    assert licoes.nivel_atual(historico.ler(arquivo), 'abnt2').numero == 2


def test_exercicio_lento_demais_nao_avanca_o_nivel(tmp_path):
    arquivo = tmp_path / 'progresso.jsonl'
    nivel = licoes.nivel_atual(historico.ler(arquivo), 'abnt2')
    for semente in (1, 2):
        # Devagar o bastante para ficar abaixo da meta de WPM do nível.
        _, avaliacao = _rodar(nivel, 'abnt2', arquivo, semente, duracao_s=600.0)
        assert not avaliacao.aprovado
        assert 'wpm' in avaliacao.faltou
    assert licoes.nivel_atual(historico.ler(arquivo), 'abnt2').numero == 1


def test_o_curriculo_inteiro_pode_ser_percorrido(tmp_path):
    # Cada nível liberado tem de gerar exercício válido e aprovável; se algum
    # gerar texto vazio ou impossível, o aluno fica preso ali para sempre.
    arquivo = tmp_path / 'progresso.jsonl'
    for esperado in range(1, 13):
        nivel = licoes.nivel_atual(historico.ler(arquivo), 'abnt2')
        assert nivel.numero == esperado, (esperado, nivel.numero)
        if nivel.numero == 12:
            break            # o 12 usa frases reais, não o gerador
        for semente in (esperado * 10, esperado * 10 + 1):
            texto, _ = _exercicio_perfeito(nivel, 'abnt2', semente)
            assert texto.strip(), nivel.id
            _, avaliacao = _rodar(nivel, 'abnt2', arquivo, semente)
            assert avaliacao.aprovado, (nivel.id, avaliacao.faltou)


def test_contagem_de_aprovacoes_acompanha_o_que_foi_gravado(tmp_path):
    arquivo = tmp_path / 'progresso.jsonl'
    nivel = licoes.curriculo('abnt2')[0]
    assert licoes.aprovacoes_seguidas(historico.ler(arquivo), nivel) == 0
    _rodar(nivel, 'abnt2', arquivo, semente=1)
    assert licoes.aprovacoes_seguidas(historico.ler(arquivo), nivel) == 1


def test_registro_sobrevive_a_ida_e_volta_do_disco(tmp_path):
    arquivo = tmp_path / 'progresso.jsonl'
    nivel = licoes.curriculo('abnt2')[0]
    gravado, _ = _rodar(nivel, 'abnt2', arquivo, semente=7)
    lido = historico.ler(arquivo)[0]
    for campo in ('nivel', 'alvo', 'tropecos', 'total_teclas', 'wpm_bruto', 'aprovado'):
        assert lido[campo] == gravado[campo], campo


def test_exercicio_com_muitos_tropecos_reprova_por_precisao(tmp_path):
    arquivo = tmp_path / 'progresso.jsonl'
    nivel = licoes.curriculo('abnt2')[0]
    texto = licoes.gerar_exercicio('abnt2', 1, semente=3)
    # Erra uma tecla a cada três, bem acima do limite de 3%.
    batidas = [metricas.Batida(c, 'x' if i % 3 == 0 else c, 200.0)
               for i, c in enumerate(texto)]
    resultado = {'batidas': batidas, 'duracao_s': 20.0, 'cancelado': False}
    registro = modo_licao.montar_registro(nivel, 'abnt2', 'pt', texto, 3, resultado)
    avaliacao = licoes.avaliar(registro, nivel)
    assert not avaliacao.aprovado
    assert 'tropecos' in avaliacao.faltou
