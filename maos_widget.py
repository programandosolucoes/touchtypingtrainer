"""As duas mãos desenhadas, com o dedo da vez destacado.

Rasterizadas com antialiasing pelo `rasterizador.py` e não desenhadas no Canvas:
mão é feita de curva, e curva no Canvas do Tk sob X11 sai serrilhada. Ver o
cabeçalho do `rasterizador` para o motivo completo.

As cores dos dedos são as mesmas do `teclado_widget`, de propósito: é a ligação
visual que ensina qual dedo vai em qual tecla.
"""
import rasterizador
import teclado_widget
import tema
from gui_backend import sg

COR_DA_PELE = '#f0d6c0'
COR_DO_CONTORNO = '#b99a86'
COR_DO_ROTULO = '#5a4a40'

DEDOS = ('minimo', 'anelar', 'medio', 'indicador')


class Maos:
    """As duas mãos numa imagem só. `destacar` acende um dedo por vez."""

    def __init__(self, largura_px, altura_px, chave='-MAOS-'):
        self.largura_px = int(largura_px)
        self.altura_px = int(altura_px)
        self.chave = chave
        self._elemento = None
        self._destacado = None   # (mão, dedo) atualmente aceso
        self._sujo = True

    def elemento(self):
        self._elemento = sg.Image(key=self.chave,
                                  background_color=teclado_widget.COR_DE_FUNDO,
                                  pad=(0, 0))
        return self._elemento

    def desenhar(self):
        """Desenha as duas mãos em repouso. Chamar depois de `finalize=True`."""
        self._sujo = True
        self.atualizar()

    def atualizar(self, forcar=False):
        if not (self._sujo or forcar) or self._elemento is None:
            return
        dados = rasterizador.desenhar_maos(
            self.largura_px, self.altura_px, destacado=self._destacado,
            cores_dos_dedos=teclado_widget.CORES_DOS_DEDOS,
            cor_da_pele=COR_DA_PELE, cor_do_contorno=COR_DO_CONTORNO,
            cor_de_fundo=tema.SUPERFICIE, cor_do_rotulo=COR_DO_ROTULO)
        self._elemento.update(data=dados)
        self._sujo = False

    def destacar(self, mao, dedo):
        """Acende um dedo e apaga o anterior. (None, None) deixa tudo em repouso."""
        alvo = (mao, dedo) if (mao and dedo in DEDOS) else None
        if self._destacado == alvo:
            return
        self._destacado = alvo
        self._sujo = True

    def limpar(self):
        self.destacar(None, None)

    def redimensionar(self, largura_px, altura_px):
        if (int(largura_px), int(altura_px)) == (self.largura_px, self.altura_px):
            return
        self.largura_px = max(120, int(largura_px))
        self.altura_px = max(80, int(altura_px))
        self._sujo = True

    @property
    def destacado(self):
        return self._destacado
