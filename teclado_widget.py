"""Teclado desenhado no Canvas do Tk, com tecla e dedo acendendo ao vivo.

Desenhado em `sg.Graph`, não em imagem: cada tecla precisa mudar de cor
individualmente durante a digitação, e imagem estática exigiria uma imagem por
estado. O Graph ainda redesenha proporcional quando a janela muda de tamanho.

Só repinta a tecla que mudou de estado — repintar o teclado inteiro a cada
tecla é o caminho conhecido para a janela engasgar.
"""
import layouts
from gui_backend import sg

# Cada dedo tem cor própria, usada tanto aqui quanto na ilustração das mãos.
CORES_DOS_DEDOS = {
    'minimo': '#8e6bbf',
    'anelar': '#3f7fbf',
    'medio': '#3fa86b',
    'indicador': '#d99a2b',
}
COR_DE_FUNDO = '#f3f3f3'
CORES_DOS_ESTADOS = {
    'proxima': '#ffd21f',
    'certa': '#57b85c',
    'errada': '#d9534f',
}
COR_DA_BORDA = '#9a9a9a'
COR_DO_TEXTO = '#222222'

# O anel que marca a tecla da vez. Cor diferente da do preenchimento de
# propósito: mudar só o tom do amarelo não salta aos olhos de quem está
# tentando não olhar para o teclado físico — o contorno vermelho salta.
COR_DO_MARCADOR = '#d81b3a'
ESPESSURA_DO_MARCADOR = 4


class Teclado:
    """Um teclado desenhável. Mantém o id de cada retângulo para repintar só ele."""

    def __init__(self, nome_layout, largura_px, altura_px, chave='-TECLADO-'):
        self.nome_layout = nome_layout
        self.largura_px = float(largura_px)
        self.altura_px = float(altura_px)
        self.chave = chave
        self._grafico = None
        self._figuras = {}       # caractere -> (id_retangulo, id_texto)
        self._estados = {}       # caractere -> estado atual
        self._retangulos = {}    # cache da geometria no tamanho corrente
        self._marcador = None    # id do anel sobre a tecla da vez
        self._marcado = None     # caractere que está com o anel

    def elemento(self):
        """O elemento a colocar no layout da janela."""
        self._grafico = sg.Graph(
            canvas_size=(int(self.largura_px), int(self.altura_px)),
            graph_bottom_left=(0, self.altura_px),
            graph_top_right=(self.largura_px, 0),
            key=self.chave, background_color=COR_DE_FUNDO, pad=(0, 0))
        return self._grafico

    def desenhar(self, mostrar_dedos=True):
        """Desenha o teclado do zero. Chamar depois de `finalize=True`."""
        self._grafico.erase()
        self._figuras.clear()
        self._estados.clear()
        self._marcador = None
        self._marcado = None
        self._retangulos = layouts.retangulos(
            self.nome_layout, self.largura_px, self.altura_px)
        tamanho_da_fonte = max(7, int(self.altura_px / 22))
        for tecla in layouts.teclas(self.nome_layout):
            x0, y0, x1, y1 = self._retangulos[tecla.caractere]
            cor = CORES_DOS_DEDOS[tecla.dedo] if mostrar_dedos else COR_DE_FUNDO
            id_retangulo = self._grafico.draw_rectangle(
                (x0 + 1, y0 + 1), (x1 - 1, y1 - 1), fill_color=cor, line_color=COR_DA_BORDA)
            id_texto = self._grafico.draw_text(
                tecla.caractere.upper(), ((x0 + x1) / 2, (y0 + y1) / 2),
                color=COR_DO_TEXTO, font=('Helvetica', tamanho_da_fonte, 'bold'))
            self._figuras[tecla.caractere] = (id_retangulo, id_texto)
            self._estados[tecla.caractere] = 'repouso'

    def pintar(self, caractere, estado):
        """Muda o estado de UMA tecla. Caractere fora do layout é ignorado."""
        caractere = caractere.lower()
        if caractere not in self._figuras or self._estados.get(caractere) == estado:
            return
        id_retangulo, id_texto = self._figuras[caractere]
        x0, y0, x1, y1 = self._retangulos[caractere]
        dedo = layouts.dedo_de(caractere, self.nome_layout)[1]
        cor = CORES_DOS_ESTADOS.get(estado, CORES_DOS_DEDOS[dedo])
        self._grafico.delete_figure(id_retangulo)
        novo = self._grafico.draw_rectangle(
            (x0 + 1, y0 + 1), (x1 - 1, y1 - 1), fill_color=cor, line_color=COR_DA_BORDA)
        # O retângulo novo nasce por cima de tudo; devolver texto e anel ao topo.
        self._grafico.tk_canvas.tag_raise(id_texto)
        if self._marcador is not None:
            self._grafico.tk_canvas.tag_raise(self._marcador)
        self._figuras[caractere] = (novo, id_texto)
        self._estados[caractere] = estado

    def marcar(self, caractere):
        """Põe um anel bem visível sobre a tecla da vez. None tira o anel.

        Existe além da cor porque mudar o preenchimento de uma tecla entre
        tantas teclas coloridas não salta aos olhos — e quem está aprendendo a
        não olhar para o teclado físico precisa achar a marca na hora.
        """
        caractere = caractere.lower() if caractere else None
        if self._marcado == caractere:
            return
        if self._marcador is not None:
            self._grafico.delete_figure(self._marcador)
            self._marcador = None
        self._marcado = None
        if caractere is None or caractere not in self._retangulos:
            return
        x0, y0, x1, y1 = self._retangulos[caractere]
        # Círculo inscrito na tecla, sem preenchimento: marca sem esconder a letra.
        raio = min(x1 - x0, y1 - y0) / 2 - 2
        centro_x, centro_y = (x0 + x1) / 2, (y0 + y1) / 2
        self._marcador = self._grafico.draw_oval(
            (centro_x - raio, centro_y - raio), (centro_x + raio, centro_y + raio),
            fill_color='', line_color=COR_DO_MARCADOR, line_width=ESPESSURA_DO_MARCADOR)
        self._marcado = caractere

    def limpar_estados(self):
        """Devolve todas as teclas ao repouso (cor do dedo) e tira o anel."""
        self.marcar(None)
        for caractere in list(self._estados):
            self.pintar(caractere, 'repouso')

    def redimensionar(self, largura_px, altura_px):
        """Redesenha o teclado noutro tamanho, preservando os estados.

        Chamado quando a janela muda de tamanho: o Graph tem tamanho fixo em
        pixels, então quem redesenha proporcional é este método.
        """
        if (int(largura_px), int(altura_px)) == (int(self.largura_px), int(self.altura_px)):
            return
        estados = dict(self._estados)
        marcado = self._marcado
        self.largura_px = max(200.0, float(largura_px))
        self.altura_px = max(80.0, float(altura_px))
        self._grafico.set_size((int(self.largura_px), int(self.altura_px)))
        self._grafico.change_coordinates((0, self.altura_px), (self.largura_px, 0))
        self.desenhar()
        for caractere, estado in estados.items():
            if estado != 'repouso':
                self.pintar(caractere, estado)
        self.marcar(marcado)
