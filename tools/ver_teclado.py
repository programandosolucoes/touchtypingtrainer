"""Abre os três teclados desenhados para conferência a olho.

A parte mecânica (geometria, cores, repintura) tem teste automatizado em
`tests/test_teclado_widget.py`. Isto aqui existe para a estética, que teste
nenhum julga.

Rode com:  .venv/bin/python tools/ver_teclado.py
"""
import sys
from pathlib import Path

# Os módulos do aplicativo ficam na raiz do projeto, e este script está em
# tools/ — sem isto, nenhum `import` daqui encontra nada.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import layouts  # noqa: E402
import tema  # noqa: E402  (precisa vir depois do sys.path)
import teclado_widget  # noqa: E402
from gui_backend import sg  # noqa: E402

for nome in ('abnt2', 'us', 'it'):
    teclado = teclado_widget.Teclado(nome, 900, 260)
    layout = [
        [sg.Text(f'Layout: {nome}', font=tema.texto(tema.TAMANHO_SUBTITULO))],
        [teclado.elemento()],
        [sg.Button('Acender a linha-base', key='-BASE-'),
         sg.Button('Limpar', key='-LIMPAR-'),
         sg.Button('Próximo layout', key='-FIM-')],
    ]
    janela = sg.Window(f'Teclado {nome}', layout, finalize=True)
    teclado.desenhar()
    while True:
        evento, _ = janela.read()
        if evento in (sg.WIN_CLOSED, '-FIM-'):
            break
        if evento == '-BASE-':
            esquerda, direita = layouts.teclas_base(nome)
            for c in esquerda + direita:
                teclado.pintar(c, 'proxima')
        if evento == '-LIMPAR-':
            teclado.limpar_estados()
    janela.close()
