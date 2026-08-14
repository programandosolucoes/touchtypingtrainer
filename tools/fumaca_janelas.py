"""Abre cada janela do programa e sai, para provar que nenhuma estoura ao montar.

NÃO é teste de comportamento: nada é clicado nem digitado. O que isto pega é a
classe de defeito que mais aparece ao mexer em tela — chave de tradução que não
existe, elemento com chave repetida, `.format()` com marcador a menos — e que só
apareceria quando o usuário abrisse aquela tela específica.

Cada janela é aberta num processo com tempo limitado, e o processo é MORTO no
fim; por isso não há "resultado", só ausência de erro.

Rode com:  .venv/bin/python tools/fumaca_janelas.py <qual>
onde <qual> é: menu | guia | previa | exercicio | relatorio
"""
import pathlib
import sys
from pathlib import Path

# Os módulos do aplicativo ficam na raiz do projeto, e este script está em
# tools/ — sem isto, nenhum `import` daqui encontra nada.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import licoes  # noqa: E402  (precisa vir depois do sys.path)


def _menu():
    import TouchTypingTrainer as app
    janela = app.create_main_window('pt', 'mixed', 'ai', 'manual', 60)
    janela.read(timeout=200)
    janela.close()


def _guia():
    import aplicativo
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        aplicativo.abrir_guia('pt', pathlib.Path(d) / 'p.jsonl')


def _previa():
    import aplicativo
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        aplicativo.abrir_licao('pt', pathlib.Path(d) / 'p.jsonl', 3, None)


def _exercicio():
    _previa()      # o exercicio vive na mesma janela agora


def _relatorio():
    """O relatório vive na mesma janela do exercício; abrir a lição já o cobre."""
    _previa()



JANELAS = {'menu': _menu, 'guia': _guia, 'previa': _previa,
           'exercicio': _exercicio, 'relatorio': _relatorio}

if __name__ == '__main__':
    qual = sys.argv[1] if len(sys.argv) > 1 else 'menu'
    JANELAS[qual]()
