"""A parte sem interface do Modo Lição: teclas, descrição e registro.

O teste de mãos é o único jeito honesto de verificar posição de mão por
software: exige quatro teclas pressionadas AO MESMO TEMPO, o que não dá para
simular digitando uma de cada vez. Não diz qual dedo foi usado — nada diz — mas
prova que a mão está pousada na linha-base antes de o exercício começar.

O exercício, por sua vez, não usa campo de texto: a entrada é dirigida por
evento de tecla. É isso que elimina o colar (que no treino livre daria 100% de
precisão de graça) e o backspace (não há o que apagar, porque caractere errado
nunca entra).
"""
from datetime import datetime

import layouts
import licoes
import metricas
from i18n import get_text

# Nomes que o tkinter dá às teclas que não são uma letra solta.
_KEYSYM_PARA_CARACTERE = {
    'ccedilla': 'ç', 'Ccedilla': 'ç', 'semicolon': ';', 'colon': ';',
    'space': ' ', 'ograve': 'ò', 'Ograve': 'ò', 'agrave': 'à', 'Agrave': 'à',
    'ugrave': 'ù', 'Ugrave': 'ù', 'egrave': 'è', 'Egrave': 'è',
    'igrave': 'ì', 'Igrave': 'ì', 'apostrophe': "'", 'quotedbl': "'",
    'comma': ',', 'less': ',', 'period': '.', 'greater': '.',
    'minus': '-', 'underscore': '-', 'equal': '=', 'plus': '+',
    'bracketleft': '[', 'braceleft': '[', 'bracketright': ']', 'braceright': ']',
    'slash': '/', 'question': '/', 'backslash': '\\', 'bar': '\\',
    'grave': '`', 'asciitilde': '~', 'dead_tilde': '~', 'dead_acute': '´',
    'acute': '´', 'dead_grave': '`',
}

# Teclas que são modificador ou navegação: não são resposta do aluno.
_TECLAS_IGNORADAS = {
    'Shift_L', 'Shift_R', 'Control_L', 'Control_R', 'Alt_L', 'Alt_R',
    'ISO_Level3_Shift', 'Caps_Lock', 'Num_Lock', 'Super_L', 'Super_R', 'Menu',
    'Left', 'Right', 'Up', 'Down', 'Home', 'End', 'Prior', 'Next', 'Insert',
    'Tab', 'Escape', 'Delete', 'BackSpace', 'Return', 'KP_Enter',
}


def keysym_para_caractere(keysym):
    """Converte o keysym do tkinter no caractere que ele produz.

    Devolve None para modificador, navegação e qualquer tecla que não seja uma
    resposta possível — quem chama simplesmente ignora.
    """
    if not keysym or keysym in _TECLAS_IGNORADAS:
        return None
    if len(keysym) == 1:
        return keysym.lower()
    return _KEYSYM_PARA_CARACTERE.get(keysym)


def descrever_tecla(caractere, nome_layout, idioma):
    """"Próxima tecla: J — indicador mão direita".

    A cor sozinha não basta: num teclado inteiro colorido por dedo, saber que a
    tecla da vez ficou amarela não diz QUAL dedo usar sem o aluno decorar a
    legenda de cores. O texto diz.
    """
    rotulo = get_text('licao_espaco', idioma) if caractere == ' ' else caractere.upper()
    par = layouts.dedo_de(caractere, nome_layout)
    if not par:
        return rotulo
    mao, dedo = par
    return get_text('licao_proxima_tecla', idioma).format(
        rotulo, get_text(f'dedo_{dedo}', idioma), get_text(f'mao_{mao}', idioma))


def montar_registro(nivel, nome_layout, idioma, texto, semente, resultado):
    """Monta a linha do histórico a partir do que o exercício produziu.

    Puro de propósito: recebe o resultado bruto e devolve o dicionário pronto,
    sem tocar em disco nem em janela — é o que permite testá-lo.
    """
    batidas = resultado['batidas']
    duracao = resultado['duracao_s']
    acertos = sum(1 for b in batidas if b.esperado == b.digitado)
    intervalos = [b.ms for b in batidas]
    velocidade = round(metricas.wpm(acertos, duracao), 2)
    return {
        'quando': datetime.now().astimezone().isoformat(timespec='seconds'),
        'modo': 'licao',
        'nivel': nivel.id,
        'wpm_meta': nivel.wpm_meta,
        'idioma': idioma,
        'layout': nome_layout,
        'alvo': texto,
        'semente': semente,
        'duracao_s': round(duracao, 2),
        'limite_s': round(licoes.limite_de_tempo(len(texto), nivel.wpm_meta), 2),
        'wpm_bruto': velocidade,
        # Na lição o líquido é igual ao bruto: a trava impede erro no texto.
        'wpm_liquido': velocidade,
        'tropecos': metricas.tropecos(batidas),
        'total_teclas': len(batidas),
        'regularidade': metricas.regularidade(intervalos),
        'aprovado': False,     # preenchido por quem avalia
        'teclas': metricas.resumo_por_tecla(batidas),
    }
