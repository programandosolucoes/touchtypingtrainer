"""Desenha teclado e mãos como IMAGEM com antialiasing, não como forma no Canvas.

## Por que não usar as primitivas do Canvas

O Canvas do Tk **não faz antialiasing no X11**. Retângulo alinhado ao eixo até
passa, mas todo círculo, oval e canto arredondado sai serrilhado. No macOS o Tk
desenha via Cocoa, que antialiasa — é por isso que a mesma tela parece boa lá e
ruim aqui. Não é ajuste de configuração: é o backend gráfico.

A saída é rasterizar por conta própria e entregar ao Tk uma imagem pronta. Aqui
o desenho é feito num tamanho maior (`SUPERAMOSTRAGEM`) e reduzido com
reamostragem LANCZOS — as bordas ganham os tons intermediários que o Canvas não
produz. É o mesmo princípio do antialiasing por supersampling.

Custa uma dependência (Pillow) e alguns milissegundos por quadro. Como o teclado
só é redesenhado quando alguma tecla muda de estado, e não a 60 quadros por
segundo, o custo não aparece.

O resultado sai como PNG em memória (`bytes`), que é o formato que o
`sg.Image.update(data=...)` aceita — sem arquivo temporário no disco.
"""
import io

from PIL import Image, ImageDraw, ImageFont

import layouts
import tema

# Fator de ampliação antes de reduzir. 3 já satura o ganho visual; acima disso
# só se paga memória.
SUPERAMOSTRAGEM = 3
RAIO_DO_CANTO = 0.18        # em fração da menor dimensão da tecla

_cache_de_fontes = {}


def _fonte(tamanho_px, negrito=False):
    """Carrega a fonte do tema no tamanho pedido, com cache.

    O Pillow precisa do ARQUIVO da fonte, não do nome — então a família
    escolhida pelo `tema` é resolvida em caminho pelo fontconfig.
    """
    chave = (tamanho_px, negrito)
    if chave in _cache_de_fontes:
        return _cache_de_fontes[chave]
    caminho = _caminho_da_fonte(tema.texto()[0], negrito)
    try:
        fonte = ImageFont.truetype(caminho, tamanho_px) if caminho \
            else ImageFont.load_default(tamanho_px)
    except (OSError, ValueError):
        fonte = ImageFont.load_default(tamanho_px)
    _cache_de_fontes[chave] = fonte
    return fonte


def _caminho_da_fonte(familia, negrito):
    """Pergunta ao fontconfig onde está o arquivo daquela família."""
    import shutil
    import subprocess
    if not shutil.which('fc-match'):
        return None
    estilo = 'bold' if negrito else 'regular'
    try:
        saida = subprocess.run(['fc-match', '-f', '%{file}', f'{familia}:style={estilo}'],
                               capture_output=True, text=True, timeout=5)
        return saida.stdout.strip() or None
    except (subprocess.SubprocessError, OSError):
        return None


def _png(imagem):
    buffer = io.BytesIO()
    imagem.save(buffer, format='PNG')
    return buffer.getvalue()


def desenhar_teclado(nome_layout, largura_px, altura_px, estados, marcado,
                     cores_das_teclas, cores_das_bordas, cores_dos_estados,
                     cores_das_bordas_dos_estados, cor_de_fundo,
                     cor_do_marcador, cor_do_texto):
    """Devolve o PNG do teclado inteiro no estado atual.

    `estados` é {caractere: 'repouso'|'proxima'|'certa'|'errada'} e `marcado` é o
    caractere que leva o anel — ou None.

    A face da tecla é PÁLIDA e a borda é saturada: assim a letra fica legível
    (contraste alto sobre fundo claro) e a informação de qual dedo usar continua
    visível no contorno e no tom da face.
    """
    escala = SUPERAMOSTRAGEM
    largura, altura = int(largura_px * escala), int(altura_px * escala)
    imagem = Image.new('RGB', (largura, altura), cor_de_fundo)
    pincel = ImageDraw.Draw(imagem)
    retangulos = layouts.retangulos(nome_layout, largura, altura)

    tamanho_da_fonte = max(8, int(altura / 4 * 0.40))
    fonte = _fonte(tamanho_da_fonte, negrito=True)
    espessura = max(1, int(1.6 * escala))

    for tecla in layouts.teclas(nome_layout):
        x0, y0, x1, y1 = retangulos[tecla.caractere]
        estado = estados.get(tecla.caractere, 'repouso')
        face = cores_dos_estados.get(estado) or cores_das_teclas[tecla.dedo]
        borda = (cores_das_bordas_dos_estados.get(estado)
                 or cores_das_bordas[tecla.dedo])
        raio = min(x1 - x0, y1 - y0) * RAIO_DO_CANTO
        margem = max(1.0, escala)
        # Canto arredondado é o que dá o ar de interface moderna — e é justamente
        # o que o Canvas não conseguiria desenhar sem serrilhar.
        pincel.rounded_rectangle(
            (x0 + margem, y0 + margem, x1 - margem, y1 - margem),
            radius=raio, fill=face, outline=borda, width=espessura)
        rotulo = tecla.caractere.upper()
        caixa = pincel.textbbox((0, 0), rotulo, font=fonte)
        pincel.text(((x0 + x1) / 2 - (caixa[2] - caixa[0]) / 2 - caixa[0],
                     (y0 + y1) / 2 - (caixa[3] - caixa[1]) / 2 - caixa[1]),
                    rotulo, font=fonte, fill=cor_do_texto)

    if marcado and marcado in retangulos:
        x0, y0, x1, y1 = retangulos[marcado]
        largura_da_tecla, altura_da_tecla = x1 - x0, y1 - y0
        traco = int(3 * escala)
        if largura_da_tecla > altura_da_tecla * 1.6:
            # Tecla larga (a barra de espaço): um círculo no meio dela ficaria
            # solto. O contorno acompanha a forma e continua saltando aos olhos.
            folga = 3 * escala
            pincel.rounded_rectangle(
                (x0 + folga, y0 + folga, x1 - folga, y1 - folga),
                radius=altura_da_tecla * RAIO_DO_CANTO,
                outline=cor_do_marcador, width=traco)
        else:
            raio = min(largura_da_tecla, altura_da_tecla) / 2 - 2 * escala
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            pincel.ellipse((cx - raio, cy - raio, cx + raio, cy + raio),
                           outline=cor_do_marcador, width=traco)

    return _png(imagem.resize((int(largura_px), int(altura_px)), Image.LANCZOS))


# --- Mãos ---------------------------------------------------------------------

LARGURA_LOGICA = 200.0
ALTURA_LOGICA = 132.0
_LARGURA_DO_DEDO = 17.0
_BASE_DO_DEDO = 80.0
_DEDOS = (
    ('minimo', 8.0, 34.0),
    ('anelar', 27.0, 18.0),
    ('medio', 46.0, 10.0),
    ('indicador', 65.0, 24.0),
)


def _espelhar(x0):
    return LARGURA_LOGICA - (x0 + _LARGURA_DO_DEDO)


def desenhar_maos(largura_px, altura_px, destacado, cores_dos_dedos,
                  cor_da_pele, cor_do_contorno, cor_de_fundo, cor_do_rotulo):
    """Devolve o PNG das duas mãos, com no máximo um dedo destacado.

    `destacado` é (mão, dedo) ou None.
    """
    escala = SUPERAMOSTRAGEM
    largura, altura = int(largura_px * escala), int(altura_px * escala)
    unidade = min(largura / LARGURA_LOGICA, altura / ALTURA_LOGICA)
    imagem = Image.new('RGB', (largura, altura), cor_de_fundo)
    pincel = ImageDraw.Draw(imagem)
    espessura = max(1, int(2 * unidade))

    def caixa(x0, y0, x1, y1):
        return (x0 * unidade, y0 * unidade, x1 * unidade, y1 * unidade)

    for mao in ('esquerda', 'direita'):
        espelhada = (mao == 'direita')
        x_palma = _espelhar(65.0) if espelhada else 8.0
        pincel.rounded_rectangle(caixa(x_palma, 70.0, x_palma + 74.0, 118.0),
                                 radius=10 * unidade, fill=cor_da_pele,
                                 outline=cor_do_contorno, width=espessura)
        x_polegar = 96.0 if espelhada else 78.0
        pincel.ellipse(caixa(x_polegar, 88.0, x_polegar + 26.0, 108.0),
                       fill=cor_da_pele, outline=cor_do_contorno, width=espessura)
        for dedo, x_esquerda, topo in _DEDOS:
            x0 = _espelhar(x_esquerda) if espelhada else x_esquerda
            aceso = destacado == (mao, dedo)
            pincel.rounded_rectangle(
                caixa(x0, topo, x0 + _LARGURA_DO_DEDO, _BASE_DO_DEDO),
                radius=_LARGURA_DO_DEDO / 2 * unidade,
                fill=cores_dos_dedos[dedo] if aceso else cor_da_pele,
                outline=cor_do_contorno, width=espessura)
        rotulo = 'E' if mao == 'esquerda' else 'D'
        fonte = _fonte(max(8, int(12 * unidade)), negrito=True)
        centro = ((x_palma + 37.0) * unidade, 94.0 * unidade)
        limites = pincel.textbbox((0, 0), rotulo, font=fonte)
        pincel.text((centro[0] - (limites[2] - limites[0]) / 2 - limites[0],
                     centro[1] - (limites[3] - limites[1]) / 2 - limites[1]),
                    rotulo, font=fonte, fill=cor_do_rotulo)

    return _png(imagem.resize((int(largura_px), int(altura_px)), Image.LANCZOS))
