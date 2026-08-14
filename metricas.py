"""Métricas do treino, sem nenhuma dependência de interface.

Separado da janela de propósito: é a parte que dá para testar sozinha, e é onde
mora a decisão do que conta como bom desempenho.
"""
import statistics

# Padrão da área: uma "palavra" são 5 caracteres, independente do idioma.
CARACTERES_POR_PALAVRA = 5

# As primeiras teclas de um exercício medem tempo de reação, não hesitação.
TECLAS_DE_AQUECIMENTO = 3
# Abaixo disso a amostra é pequena demais para significar alguma coisa.
MINIMO_DE_INTERVALOS = 10
# Intervalo acima de 3x a mediana é "parada": o olho foi procurar a tecla.
FATOR_DE_PARADA = 3.0


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


def regularidade(intervalos_ms):
    """Proporção de teclas digitadas sem parada para procurar a tecla.

    Devolve de 0 a 1, ou None quando a amostra é pequena demais para dizer
    qualquer coisa — nesse caso o exercício não reprova por ritmo.

    Usa a MEDIANA, não a média: uma única pausa longa (o telefone tocou)
    arrastaria a média e reprovaria alguém que digita bem.
    """
    contados = intervalos_ms[TECLAS_DE_AQUECIMENTO:]
    if len(contados) < MINIMO_DE_INTERVALOS:
        return None
    mediana = statistics.median(contados)
    if mediana <= 0:
        return None
    limite = mediana * FATOR_DE_PARADA
    paradas = sum(1 for i in contados if i > limite)
    return round(1 - paradas / len(contados), 4)
