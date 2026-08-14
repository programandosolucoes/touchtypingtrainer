"""As duas mãos desenhadas, com o dedo da vez destacado.

Desenhadas no mesmo Canvas do teclado, e não como imagem PNG, por três motivos
práticos:

1. **Escala de graça.** O Graph trabalha em coordenadas lógicas: mudar o tamanho
   em pixels reescala o desenho inteiro. PNG teria de ser pré-gerado num tamanho
   e ficaria serrilhado em qualquer outro.
2. **Um destaque, não dez imagens.** Destacar um dedo é trocar o preenchimento
   de uma figura. Com PNG seriam 10 arquivos (2 mãos × neutra + 4 dedos), todos
   regerados a cada ajuste de cor.
3. **Nenhuma dependência de empacotamento.** Converter SVG exigiria
   `rsvg-convert` ou `inkscape` instalado em toda máquina que gera binário,
   inclusive a de Windows — num programa cujo requisito é ser portátil.

As cores dos dedos são as mesmas do `teclado_widget`, de propósito: é a ligação
visual que ensina qual dedo vai em qual tecla.
"""
import teclado_widget
from gui_backend import sg

COR_DA_PELE = '#f0d6c0'
COR_DO_CONTORNO = '#b99a86'
COR_DO_ROTULO = '#5a4a40'

# Área lógica do desenho das duas mãos. Os pixels são independentes disto: o
# Graph reescala sozinho, que é o motivo de desenhar em vez de usar imagem.
LARGURA_LOGICA = 200.0
ALTURA_LOGICA = 132.0

_LARGURA_DO_DEDO = 17.0
_BASE_DO_DEDO = 80.0

# (dedo, x da borda esquerda na mão ESQUERDA, topo). O comprimento diferente
# entre os dedos é o que faz o desenho ser lido como mão.
_DEDOS = (
    ('minimo', 8.0, 34.0),
    ('anelar', 27.0, 18.0),
    ('medio', 46.0, 10.0),
    ('indicador', 65.0, 24.0),
)


def _espelhar(x0):
    """Posição equivalente na mão direita: o desenho é simétrico."""
    return LARGURA_LOGICA - (x0 + _LARGURA_DO_DEDO)


class Maos:
    """As duas mãos num Graph só. `destacar` acende um dedo por vez."""

    def __init__(self, largura_px, altura_px, chave='-MAOS-'):
        self.largura_px = int(largura_px)
        self.altura_px = int(altura_px)
        self.chave = chave
        self._grafico = None
        self._figuras = {}       # (mao, dedo) -> id da figura
        self._destacado = None   # (mao, dedo) atualmente aceso

    def elemento(self):
        self._grafico = sg.Graph(
            canvas_size=(self.largura_px, self.altura_px),
            graph_bottom_left=(0, ALTURA_LOGICA),
            graph_top_right=(LARGURA_LOGICA, 0),
            key=self.chave, background_color=teclado_widget.COR_DE_FUNDO,
            pad=(0, 0))
        return self._grafico

    def desenhar(self):
        """Desenha as duas mãos em repouso. Chamar depois de `finalize=True`."""
        self._grafico.erase()
        self._figuras.clear()
        self._destacado = None
        for mao in ('esquerda', 'direita'):
            self._desenhar_mao(mao)

    def _desenhar_mao(self, mao):
        espelhada = (mao == 'direita')
        # Palma primeiro: os dedos nascem por cima dela.
        x_palma = _espelhar(65.0) if espelhada else 8.0
        self._grafico.draw_rectangle(
            (x_palma, 70.0), (x_palma + 74.0, 118.0),
            fill_color=COR_DA_PELE, line_color=COR_DO_CONTORNO, line_width=2)
        # Polegar: fica do lado de dentro, apontando para a barra de espaço.
        x_polegar = 96.0 if espelhada else 78.0
        self._grafico.draw_oval(
            (x_polegar, 88.0), (x_polegar + 26.0, 108.0),
            fill_color=COR_DA_PELE, line_color=COR_DO_CONTORNO, line_width=2)
        for dedo, x_esquerda, topo in _DEDOS:
            x0 = _espelhar(x_esquerda) if espelhada else x_esquerda
            self._figuras[(mao, dedo)] = self._grafico.draw_oval(
                (x0, topo), (x0 + _LARGURA_DO_DEDO, _BASE_DO_DEDO),
                fill_color=COR_DA_PELE, line_color=COR_DO_CONTORNO, line_width=2)
        rotulo = 'E' if mao == 'esquerda' else 'D'
        self._grafico.draw_text(rotulo, (x_palma + 37.0, 94.0),
                                color=COR_DO_ROTULO, font=('Helvetica', 14, 'bold'))

    def destacar(self, mao, dedo):
        """Acende um dedo e apaga o anterior. (None, None) deixa tudo em repouso."""
        if self._destacado == (mao, dedo):
            return
        if self._destacado in self._figuras:
            self._grafico.tk_canvas.itemconfig(
                self._figuras[self._destacado], fill=COR_DA_PELE)
        self._destacado = None
        figura = self._figuras.get((mao, dedo))
        if figura is not None:
            self._grafico.tk_canvas.itemconfig(
                figura, fill=teclado_widget.CORES_DOS_DEDOS[dedo])
            self._destacado = (mao, dedo)

    def limpar(self):
        self.destacar(None, None)

    def redimensionar(self, largura_px, altura_px):
        """Só o tamanho em pixels muda — as coordenadas lógicas são fixas.

        É por isso que o desenho não precisa ser refeito: quem reescala é o
        próprio Canvas.
        """
        self.largura_px = max(120, int(largura_px))
        self.altura_px = max(80, int(altura_px))
        self._grafico.set_size((self.largura_px, self.altura_px))
