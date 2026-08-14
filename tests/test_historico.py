"""Testes do histórico — usa tmp_path, nunca escreve no histórico de verdade."""
import os

import pytest

import historico


def test_grava_ao_lado_do_executavel_quando_da(tmp_path):
    pasta_exe = tmp_path / 'app'
    pasta_exe.mkdir()
    pasta_usuario = tmp_path / 'home'
    caminho, caiu = historico.resolver_caminho(pasta_exe, pasta_usuario)
    assert caminho == pasta_exe / 'dados' / 'progresso.jsonl'
    assert caiu is False


@pytest.mark.skipif(os.geteuid() == 0, reason='root ignora permissão de escrita')
def test_cai_para_a_pasta_do_usuario_quando_e_somente_leitura(tmp_path):
    pasta_exe = tmp_path / 'app'
    pasta_exe.mkdir()
    pasta_exe.chmod(0o555)
    pasta_usuario = tmp_path / 'home'
    try:
        caminho, caiu = historico.resolver_caminho(pasta_exe, pasta_usuario)
    finally:
        pasta_exe.chmod(0o755)
    assert caminho == pasta_usuario / 'progresso.jsonl'
    assert caiu is True


def test_cria_a_pasta_de_destino(tmp_path):
    pasta_exe = tmp_path / 'app'
    pasta_exe.mkdir()
    caminho, _ = historico.resolver_caminho(pasta_exe, tmp_path / 'home')
    assert caminho.parent.is_dir()


def test_gravar_acrescenta_sem_reescrever(tmp_path):
    arquivo = tmp_path / 'progresso.jsonl'
    historico.gravar({'modo': 'licao', 'nivel': 'base-esquerda'}, arquivo)
    historico.gravar({'modo': 'livre', 'nivel': None}, arquivo)
    registros = historico.ler(arquivo)
    assert [r['modo'] for r in registros] == ['licao', 'livre']


def test_gravar_carimba_a_versao_do_formato(tmp_path):
    arquivo = tmp_path / 'progresso.jsonl'
    historico.gravar({'modo': 'livre'}, arquivo)
    assert historico.ler(arquivo)[0]['v'] == historico.VERSAO_DO_FORMATO


def test_linha_corrompida_e_pulada_sem_derrubar_o_resto(tmp_path):
    arquivo = tmp_path / 'progresso.jsonl'
    historico.gravar({'modo': 'licao'}, arquivo)
    with open(arquivo, 'a', encoding='utf-8') as f:
        f.write('{isto nao e json\n')
    historico.gravar({'modo': 'livre'}, arquivo)
    registros = historico.ler(arquivo)
    assert [r['modo'] for r in registros] == ['licao', 'livre']


def test_ler_arquivo_inexistente_devolve_lista_vazia(tmp_path):
    assert historico.ler(tmp_path / 'nao-existe.jsonl') == []


def test_acentos_sobrevivem_a_ida_e_volta(tmp_path):
    arquivo = tmp_path / 'progresso.jsonl'
    historico.gravar({'alvo': 'ação coração ç'}, arquivo)
    assert historico.ler(arquivo)[0]['alvo'] == 'ação coração ç'


def test_preferencias_inexistentes_sao_dicionario_vazio(tmp_path):
    assert historico.ler_preferencias(tmp_path / 'progresso.jsonl') == {}


def test_preferencia_gravada_sobrevive(tmp_path):
    arquivo = tmp_path / 'progresso.jsonl'
    historico.gravar_preferencia(arquivo, 'teclado_sem_rollover', True)
    assert historico.ler_preferencias(arquivo)['teclado_sem_rollover'] is True


def test_preferencia_corrompida_nao_derruba(tmp_path):
    arquivo = tmp_path / 'progresso.jsonl'
    (tmp_path / 'preferencias.json').write_text('{quebrado', encoding='utf-8')
    assert historico.ler_preferencias(arquivo) == {}
