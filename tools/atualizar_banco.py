"""Converte `frases_ia.json` (saída do gerador) no módulo `sentences_ai.py`.

O aplicativo importa um módulo Python, não um JSON, para que o PyInstaller embuta o
banco no executável sem precisar de arquivo de dados ao lado do binário.
"""
import json
import os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CABECALHO = '''"""Banco de frases de treino gerado por IA (offline).

Gerado uma única vez por `tools/gerar_frases.py` usando os modelos gratuitos do
OpenCode Zen e revisado por comprimento/idioma. Serve para que a fonte "Gerado por IA"
funcione já na primeira execução, sem internet — a geração ao vivo (`ai_exercises.py`)
apenas acrescenta frases a este conjunto.

Não edite à mão: rode `python tools/gerar_frases.py && python tools/atualizar_banco.py`.
Total de frases: {total}
"""

FRASES_IA = {corpo}
'''


def formatar(banco):
    linhas = ['{']
    for lang in ('pt', 'en', 'it'):
        dados = banco.get(lang, {})
        linhas.append(f"    '{lang}': {{")
        for tipo in ('short', 'long'):
            linhas.append(f"        '{tipo}': [")
            for frase in dados.get(tipo, []):
                escapada = frase.replace('\\', '\\\\').replace("'", "\\'")
                linhas.append(f"            '{escapada}',")
            linhas.append('        ],')
        linhas.append('    },')
    linhas.append('}')
    return '\n'.join(linhas)


def main():
    caminho_json = os.path.join(RAIZ, 'tools', 'frases_ia.json')
    with open(caminho_json, encoding='utf-8') as fh:
        banco = json.load(fh)
    total = sum(len(v) for d in banco.values() for v in d.values())
    destino = os.path.join(RAIZ, 'sentences_ai.py')
    with open(destino, 'w', encoding='utf-8') as fh:
        fh.write(CABECALHO.format(total=total, corpo=formatar(banco)))
    print(f'{destino}: {total} frases')
    for lang, d in banco.items():
        print(f'  {lang}: {len(d.get("short", []))} curtas, {len(d.get("long", []))} longas')


if __name__ == '__main__':
    main()
