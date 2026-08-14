"""Teclado desenhado, com tecla e dedo acendendo ao vivo.

O desenho não é feito com as primitivas do Canvas: elas não fazem antialiasing no
X11, e todo canto arredondado e todo círculo sai serrilhado. Aqui o teclado é
**rasterizado** com supersampling (`rasterizador.py`) e entregue ao Tk como
imagem pronta — ver o cabeçalho daquele módulo para o porquê.

Este módulo cuida do ESTADO (que tecla está em que cor, qual leva o anel) e só
manda redesenhar quando algo muda. Redesenhar a cada tecla digitada custa poucos
milissegundos; redesenhar a cada volta do laço de eventos, não.
"""
import layouts
import rasterizador
import tema
from gui_backend import sg

# Cor saturada de cada dedo. Usada onde ela é o próprio conteúdo: o dedo aceso
# na ilustração das mãos e a borda da tecla.
CORES_DOS_DEDOS = {
    'minimo': '#8e24aa',
    'anelar': '#1565c0',
    'medio': '#2e7d32',
    'indicador': '#a85a00',
    # O polegar só bate o espaço. Cinza de propósito: é a única tecla dele, não
    # há o que confundir, e uma quinta cor forte só poluiria a leitura.
    'polegar': '#5f6368',
}

# Tom PÁLIDO do mesmo dedo, para a FACE da tecla. Pintar a tecla com a cor
# saturada e pôr letra escura em cima dava ~3,6:1 de contraste — abaixo do
# mínimo de 4,5:1 do WCAG AA, e visivelmente ilegível. Com a face pálida a letra
# escura passa dos 10:1 e a informação de dedo continua lá, na borda e no tom.
CORES_DAS_TECLAS = {
    'minimo': '#f7e4fb',
    'anelar': '#dceafb',
    'medio': '#e3f2e5',
    'indicador': '#f9eadb',
    'polegar': '#eceff1',
}

COR_DE_FUNDO = tema.SUPERFICIE
# Estados também em tom claro, pelo mesmo motivo: a letra tem de continuar
# legível *durante* o exercício, que é justamente quando ela mais importa.
CORES_DOS_ESTADOS = {
    'proxima': '#fff0b3',
    'certa': '#cdeccf',
    'errada': '#f9d4d2',
}
CORES_DAS_BORDAS_DOS_ESTADOS = {
    'proxima': '#b58a00',
    'certa': tema.SUCESSO,
    'errada': tema.ERRO,
}
COR_DO_TEXTO = '#1a1a1a'

# O anel que marca a tecla da vez. Cor diferente da do preenchimento de
# propósito: mudar só o tom do amarelo não salta aos olhos de quem está
# tentando não olhar para o teclado físico — o contorno vermelho salta.
COR_DO_MARCADOR = tema.ERRO


class Teclado:
    """Um teclado desenhável. Guarda o estado e redesenha só quando ele muda."""

    def __init__(self, nome_layout, largura_px, altura_px, chave='-TECLADO-'):
        self.nome_layout = nome_layout
        self.largura_px = int(largura_px)
        self.altura_px = int(altura_px)
        self.chave = chave
        self._elemento = None
        self._estados = {}       # caractere -> estado atual
        self._marcado = None     # caractere que está com o anel
        self._sujo = True        # há mudança ainda não desenhada?

    def elemento(self):
        """O elemento a colocar no layout da janela."""
        self._elemento = sg.Image(key=self.chave, background_color=COR_DE_FUNDO,
                                  pad=(0, 0))
        return self._elemento

    def desenhar(self, mostrar_dedos=True):
        """Redesenha o teclado. Chamar depois de `finalize=True`."""
        self._mostrar_dedos = mostrar_dedos
        for tecla in layouts.teclas(self.nome_layout):
            self._estados.setdefault(tecla.caractere, 'repouso')
        self._sujo = True
        self.atualizar()

    def atualizar(self, forcar=False):
        """Rasteriza e manda para a tela, se houver mudança pendente."""
        if not (self._sujo or forcar) or self._elemento is None:
            return
        dados = rasterizador.desenhar_teclado(
            self.nome_layout, self.largura_px, self.altura_px,
            estados=self._estados, marcado=self._marcado,
            cores_das_teclas=CORES_DAS_TECLAS, cores_das_bordas=CORES_DOS_DEDOS,
            cores_dos_estados=CORES_DOS_ESTADOS,
            cores_das_bordas_dos_estados=CORES_DAS_BORDAS_DOS_ESTADOS,
            cor_de_fundo=COR_DE_FUNDO, cor_do_marcador=COR_DO_MARCADOR,
            cor_do_texto=COR_DO_TEXTO)
        self._elemento.update(data=dados)
        self._sujo = False

    def pintar(self, caractere, estado):
        """Muda o estado de UMA tecla. Caractere fora do layout é ignorado."""
        caractere = caractere.lower()
        if caractere not in self._estados or self._estados[caractere] == estado:
            return
        self._estados[caractere] = estado
        self._sujo = True

    def marcar(self, caractere):
        """Põe o anel sobre a tecla da vez. None tira o anel.

        Existe além da cor porque mudar o preenchimento de uma tecla entre tantas
        teclas coloridas não salta aos olhos — e quem está aprendendo a não olhar
        para o teclado físico precisa achar a marca na hora.
        """
        caractere = caractere.lower() if caractere else None
        if caractere is not None and caractere not in self._estados:
            caractere = None
        if self._marcado == caractere:
            return
        self._marcado = caractere
        self._sujo = True

    def limpar_estados(self):
        """Devolve todas as teclas ao repouso (cor do dedo) e tira o anel."""
        for caractere in self._estados:
            if self._estados[caractere] != 'repouso':
                self._estados[caractere] = 'repouso'
                self._sujo = True
        self.marcar(None)

    def redimensionar(self, largura_px, altura_px):
        """Muda o tamanho em pixels; o desenho é refeito na próxima atualização."""
        if (int(largura_px), int(altura_px)) == (self.largura_px, self.altura_px):
            return
        self.largura_px = max(200, int(largura_px))
        self.altura_px = max(80, int(altura_px))
        self._sujo = True

    # --- consulta, usada pelos testes e por quem precisa saber o estado ---

    def estado_de(self, caractere):
        return self._estados.get(caractere.lower())

    @property
    def marcado(self):
        return self._marcado
