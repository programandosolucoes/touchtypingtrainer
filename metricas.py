"""Métricas do treino, sem nenhuma dependência de interface.

Separado da janela de propósito: é a parte que dá para testar sozinha, e é onde
mora a decisão do que conta como bom desempenho.
"""

# Padrão da área: uma "palavra" são 5 caracteres, independente do idioma.
CARACTERES_POR_PALAVRA = 5


def wpm(caracteres, segundos):
    """Palavras por minuto brutas. Duração zero devolve zero em vez de estourar."""
    if segundos <= 0 or caracteres <= 0:
        return 0.0
    palavras = caracteres / CARACTERES_POR_PALAVRA
    return palavras / (segundos / 60.0)


def wpm_liquido(caracteres, segundos, erros):
    """WPM descontando um erro por minuto para cada erro não corrigido.

    Piso em zero: errar muito significa desempenho nulo, não negativo. No Modo
    Lição o líquido é sempre igual ao bruto, porque a trava impede que caractere
    errado entre no texto — lá quem mede qualidade é o tropeço.
    """
    if segundos <= 0:
        return 0.0
    return max(0.0, wpm(caracteres, segundos) - erros / (segundos / 60.0))
