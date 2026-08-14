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
    import TouchTypingTrainer as app
    app.current_lang = 'pt'
    app.show_hand_positioning_guide()


def _previa():
    import modo_licao
    nivel = licoes.curriculo('abnt2')[0]
    modo_licao.tela_previa(nivel, 'abnt2', 'pt', sem_rollover=False, aprovacoes=1)


def _exercicio():
    import modo_licao
    texto = licoes.gerar_exercicio('abnt2', 3, semente=1, grupos=6)
    modo_licao.executar_exercicio(texto, 'abnt2', 'pt', 120.0)


def _relatorio():
    import metricas
    import modo_licao
    nivel = licoes.curriculo('abnt2')[0]
    texto = licoes.gerar_exercicio('abnt2', 1, semente=1)
    resultado = {'batidas': [metricas.Batida(c, c, 200.0) for c in texto],
                 'duracao_s': 20.0, 'cancelado': False}
    registro = modo_licao.montar_registro(nivel, 'abnt2', 'pt', texto, 1, resultado)
    avaliacao = licoes.avaliar(registro, nivel)
    modo_licao.mostrar_relatorio(registro, avaliacao, 'pt')


JANELAS = {'menu': _menu, 'guia': _guia, 'previa': _previa,
           'exercicio': _exercicio, 'relatorio': _relatorio}

if __name__ == '__main__':
    qual = sys.argv[1] if len(sys.argv) > 1 else 'menu'
    JANELAS[qual]()
