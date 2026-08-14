"""Onde o progresso mora e como ele é lido e gravado.

O aplicativo é portátil: o padrão é gravar ao lado do executável, para o
progresso viajar junto quando a pasta for copiada para um pendrive. Só quando
esse lugar é somente-leitura — programa instalado em Arquivos de Programas, por
exemplo — o histórico cai para a pasta do usuário.

O formato é JSON Lines, uma linha por exercício, sempre acrescentando. Foi
escolhido sobre SQLite porque, com um usuário e sem escrita concorrente, o banco
cobraria migração de esquema a cada campo novo sem entregar nada perceptível.
"""
import json
import os
import sys
from pathlib import Path

NOME_DO_ARQUIVO = 'progresso.jsonl'

# Sobe quando o significado de um campo mudar. Campo novo NÃO exige subir:
# versão antiga simplesmente ignora o que não conhece.
VERSAO_DO_FORMATO = 1


def resolver_caminho(pasta_executavel, pasta_usuario):
    """Decide onde gravar. Devolve (caminho, caiu_para_a_pasta_do_usuario)."""
    destino = Path(pasta_executavel) / 'dados'
    try:
        destino.mkdir(parents=True, exist_ok=True)
        # mkdir passar não garante escrita: a pasta pode já existir sem permissão.
        if not os.access(destino, os.W_OK):
            raise PermissionError(destino)
        return destino / NOME_DO_ARQUIVO, False
    except (OSError, PermissionError):
        alternativo = Path(pasta_usuario)
        alternativo.mkdir(parents=True, exist_ok=True)
        return alternativo / NOME_DO_ARQUIVO, True


def pasta_do_executavel():
    """Onde o programa está: ao lado do .exe empacotado, ou do fonte."""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent


def pasta_do_usuario():
    """~/.touchtypingtrainer no Linux, %APPDATA%\\TouchTypingTrainer no Windows."""
    if os.name == 'nt':
        base = os.environ.get('APPDATA') or os.path.expanduser('~')
        return Path(base) / 'TouchTypingTrainer'
    return Path(os.path.expanduser('~')) / '.touchtypingtrainer'


def gravar(registro, caminho):
    """Acrescenta um exercício ao histórico. Nunca reescreve o que já está lá."""
    linha = dict(registro)
    linha['v'] = VERSAO_DO_FORMATO
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, 'a', encoding='utf-8') as f:
        f.write(json.dumps(linha, ensure_ascii=False) + '\n')


def ler(caminho):
    """Lê o histórico inteiro, pulando linha ilegível em vez de estourar.

    Arquivo truncado por queda de energia ou editado à mão não pode invalidar
    todo o progresso — a linha ruim é descartada e o resto continua valendo.
    """
    caminho = Path(caminho)
    if not caminho.exists():
        return []
    registros = []
    with open(caminho, 'r', encoding='utf-8') as f:
        for numero, linha in enumerate(f, start=1):
            linha = linha.strip()
            if not linha:
                continue
            try:
                registros.append(json.loads(linha))
            except json.JSONDecodeError:
                print(f'historico: linha {numero} ilegivel, pulada', file=sys.stderr)
    return registros


def _caminho_das_preferencias(caminho_do_progresso):
    return Path(caminho_do_progresso).parent / 'preferencias.json'


def ler_preferencias(caminho_do_progresso):
    """Preferências que não são exercício — hoje só o limite do teclado.

    Arquivo ausente ou ilegível vira dicionário vazio: preferência é conforto,
    nunca motivo para o programa não abrir.
    """
    arquivo = _caminho_das_preferencias(caminho_do_progresso)
    if not arquivo.exists():
        return {}
    try:
        with open(arquivo, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def gravar_preferencia(caminho_do_progresso, chave, valor):
    """Grava uma preferência preservando as outras."""
    arquivo = _caminho_das_preferencias(caminho_do_progresso)
    atuais = ler_preferencias(caminho_do_progresso)
    atuais[chave] = valor
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    with open(arquivo, 'w', encoding='utf-8') as f:
        json.dump(atuais, f, ensure_ascii=False, indent=2)
