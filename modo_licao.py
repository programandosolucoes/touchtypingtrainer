"""O Modo Lição: tela prévia com teste de mãos e exercício travado.

O teste de mãos é o único jeito honesto de verificar posição de mão por
software: exige quatro teclas pressionadas AO MESMO TEMPO, o que não dá para
simular digitando uma de cada vez. Não diz qual dedo foi usado — nada diz — mas
prova que a mão está pousada na linha-base antes de o exercício começar.

O exercício, por sua vez, não usa campo de texto: a entrada é dirigida por
evento de tecla. É isso que elimina o colar (que no treino livre daria 100% de
precisão de graça) e o backspace (não há o que apagar, porque caractere errado
nunca entra).
"""
import time
from datetime import datetime

import layouts
import licoes
import maos_widget
import metricas
import teclado_widget
import teclas_pressionadas
from gui_backend import sg
from i18n import get_text

# Tempo que as quatro teclas precisam ficar juntas para o passo valer.
MS_PARA_CONFIRMAR = 400.0
# Depois disso sem conseguir, assume-se limite de rollover do teclado.
SEGUNDOS_ATE_OFERECER_SEQUENCIAL = 15.0

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


def _agora_ms():
    return time.monotonic() * 1000.0


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


def _caractere_do_evento(janela):
    return keysym_para_caractere(getattr(janela.user_bind_event, 'keysym', ''))


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


def tela_previa(nivel, nome_layout, idioma, sem_rollover=False, aprovacoes=0):
    """Mostra o nível e cobra o teste de mãos.

    Devolve (comecar, sem_rollover). O segundo valor vira True quando se
    descobre que o teclado não reporta quatro teclas juntas — quem chama grava
    isso para não fazer o aluno esperar 15 segundos toda vez.
    """
    esquerda, direita = layouts.teclas_base(nome_layout)
    passos = [('licao_teste_esquerda', esquerda, 'esquerda'),
              ('licao_teste_direita', direita, 'direita')]
    passo_atual = 0
    confirmando_desde = None
    sequencial = sem_rollover      # já se sabia: entra direto no modo alternativo
    proxima_sequencial = 0
    inicio = _agora_ms()

    rastreador = teclas_pressionadas.Rastreador()
    teclado = teclado_widget.Teclado(nome_layout, 860, 250, chave='-TECLADO_PREVIA-')
    maos = maos_widget.Maos(320, 210, chave='-MAOS_PREVIA-')

    percentual = int(licoes.MAXIMO_DE_TROPECOS * 100)
    titulo = get_text('licao_titulo', idioma).format(nivel.numero, nivel.id)
    layout = [
        [sg.Text(titulo, font=('Helvetica', 20))],
        [sg.Text(get_text('licao_teclas_novas', idioma), font=('Helvetica', 11)),
         sg.Text(' '.join(nivel.teclas_novas) or '—', font=('Courier New', 16, 'bold'))],
        [sg.Text(get_text('licao_criterio', idioma).format(percentual, nivel.wpm_meta),
                 font=('Helvetica', 10))],
        [sg.Text(get_text('licao_para_avancar', idioma).format(
            licoes.APROVACOES_SEGUIDAS, aprovacoes), font=('Helvetica', 10))],
        [sg.HSeparator()],
        [sg.Text('', key='-INSTRUCAO-', font=('Helvetica', 15, 'bold'),
                 expand_x=True, justification='center')],
        [sg.Text('', key='-DETALHE-', font=('Helvetica', 13),
                 text_color='#d81b3a', expand_x=True, justification='center')],
        [maos.elemento()],
        [teclado.elemento()],
        [sg.Text('', key='-AVISO-', font=('Helvetica', 10), text_color='darkorange',
                 expand_x=True, justification='center', size=(100, 2))],
        [sg.Button(get_text('licao_comecar', idioma), key='-COMECAR-', disabled=True,
                   font=('Helvetica', 14), button_color=('white', 'darkgreen')),
         sg.Button(get_text('licao_voltar', idioma), key='-VOLTAR-', font=('Helvetica', 11))],
    ]
    janela = sg.Window(titulo, layout, modal=True, finalize=True, size=(1100, 820),
                       element_justification='center', return_keyboard_events=True)
    janela.bind('<KeyPress>', '-DOWN-')
    janela.bind('<KeyRelease>', '-UP-')
    teclado.desenhar()
    maos.desenhar()
    if sequencial:
        janela['-AVISO-'].update(get_text('licao_teste_sequencial', idioma))

    comecar = False
    while True:
        evento, _ = janela.read(timeout=50)
        agora = _agora_ms()

        if evento in (sg.WIN_CLOSED, '-VOLTAR-'):
            break
        if evento == '-COMECAR-':
            comecar = True
            break

        if evento in ('-DOWN-', '-UP-'):
            caractere = _caractere_do_evento(janela)
            if caractere:
                if evento == '-DOWN-':
                    rastreador.pressionou(caractere, agora)
                    # Se a tecla produziu um caractere que este layout não tem,
                    # o teclado do sistema está noutro layout. Sem avisar, o
                    # aluno tentaria a vida inteira sem entender o que falta.
                    if (passo_atual < len(passos)
                            and layouts.dedo_de(caractere, nome_layout) is None):
                        janela['-AVISO-'].update(
                            get_text('licao_layout_diferente', idioma).format(
                                caractere, ' '.join(passos[passo_atual][1])))
                else:
                    rastreador.soltou(caractere, agora)

        if passo_atual >= len(passos):
            continue

        _, esperadas, mao_da_vez = passos[passo_atual]
        ativas = rastreador.ativas(agora)

        # Verde o que está pressionado, amarelo o que ainda falta.
        for caractere in esperadas:
            teclado.pintar(caractere, 'certa' if caractere in ativas else 'proxima')

        if sequencial:
            # Modo alternativo: uma tecla por vez, na ordem, para teclado sem rollover.
            alvo = esperadas[proxima_sequencial]
            maos.destacar(mao_da_vez, layouts.dedo_de(alvo, nome_layout)[1])
            # Uma tecla por vez: dá para marcar com o anel e dizer qual dedo é.
            teclado.marcar(alvo)
            janela['-DETALHE-'].update(descrever_tecla(alvo, nome_layout, idioma))
            if alvo in ativas:
                proxima_sequencial += 1
                if proxima_sequencial >= len(esperadas):
                    proxima_sequencial = 0
                    passo_atual += 1
                    teclado.limpar_estados()
        else:
            maos.destacar(mao_da_vez, 'indicador')
            # Aqui são quatro teclas de uma vez: não há "a" tecla para marcar,
            # então o detalhe lista as quatro em vez de nomear um dedo só.
            janela['-DETALHE-'].update('   '.join(
                get_text('licao_espaco', idioma) if c == ' ' else c.upper()
                for c in esperadas))
            completo = set(esperadas) <= ativas
            if completo:
                confirmando_desde = confirmando_desde or agora
                if agora - confirmando_desde >= MS_PARA_CONFIRMAR:
                    confirmando_desde = None
                    passo_atual += 1
                    teclado.limpar_estados()
            else:
                confirmando_desde = None
            if (not completo and passo_atual == 0
                    and agora - inicio > SEGUNDOS_ATE_OFERECER_SEQUENCIAL * 1000):
                sequencial = True
                janela['-AVISO-'].update(get_text('licao_teste_sequencial', idioma))

        if passo_atual < len(passos):
            janela['-INSTRUCAO-'].update(get_text(passos[passo_atual][0], idioma))
        else:
            janela['-INSTRUCAO-'].update(get_text('licao_teste_ok', idioma))
            janela['-DETALHE-'].update('')
            janela['-COMECAR-'].update(disabled=False)
            teclado.limpar_estados()
            maos.limpar()

    janela.close()
    return comecar, sequencial


def executar_exercicio(texto, nome_layout, idioma, limite_s):
    """Roda o exercício travado: tecla errada não entra e o texto não avança.

    Devolve {'batidas', 'duracao_s', 'cancelado'}.
    """
    teclado = teclado_widget.Teclado(nome_layout, 860, 250, chave='-TECLADO_EXERCICIO-')
    maos = maos_widget.Maos(320, 210, chave='-MAOS_EXERCICIO-')
    elementos_do_alvo = [
        sg.Text(c, key=f'-ALVO_{i}-', font=('Courier New', 16, 'bold'), pad=(0, 0),
                text_color='grey')
        for i, c in enumerate(texto)]

    layout = [
        [sg.Text(get_text('licao_digite', idioma), font=('Helvetica', 12)), sg.Push(),
         sg.Text('', key='-TEMPO-', font=('Helvetica', 11)), sg.Text('   '),
         sg.Text('', key='-PROGRESSO-', font=('Helvetica', 11))],
        [sg.Column([[*elementos_do_alvo]], scrollable=True, expand_x=True,
                   background_color='#eeeeee', pad=(5, 10))],
        [sg.Text('', key='-PROXIMA-', font=('Helvetica', 17, 'bold'),
                 text_color='#d81b3a', expand_x=True, justification='center')],
        [maos.elemento()],
        [teclado.elemento()],
        [sg.Button(get_text('licao_cancelar', idioma), key='-CANCELAR-')],
    ]
    janela = sg.Window(get_text('licao_digite', idioma), layout, modal=True, finalize=True,
                       size=(1100, 820), element_justification='center',
                       return_keyboard_events=True)
    janela.bind('<KeyPress>', '-DOWN-')
    teclado.desenhar()
    maos.desenhar()

    posicao = 0
    batidas = []
    inicio = _agora_ms()
    ultima_batida = inicio
    cancelado = False

    def destacar_proxima():
        """Acende a tecla que vem, o anel sobre ela, o dedo na mão e o texto."""
        teclado.limpar_estados()
        if posicao >= len(texto):
            maos.limpar()
            janela['-PROXIMA-'].update('')
            return
        alvo = texto[posicao]
        teclado.pintar(alvo, 'proxima')
        # O anel é o que se acha sem procurar; a cor sozinha se perde no meio
        # de um teclado inteiro colorido.
        teclado.marcar(alvo)
        janela['-PROXIMA-'].update(descrever_tecla(alvo, nome_layout, idioma))
        par = layouts.dedo_de(alvo, nome_layout)
        if par:
            maos.destacar(par[0], par[1])
        else:
            maos.limpar()

    destacar_proxima()

    while posicao < len(texto):
        evento, _ = janela.read(timeout=100)
        agora = _agora_ms()
        decorrido = (agora - inicio) / 1000.0
        janela['-TEMPO-'].update(get_text('licao_tempo', idioma).format(decorrido, limite_s))
        janela['-PROGRESSO-'].update(
            get_text('licao_progresso', idioma).format(posicao, len(texto)))

        if evento in (sg.WIN_CLOSED, '-CANCELAR-'):
            cancelado = True
            break
        if decorrido >= limite_s:
            break
        if evento != '-DOWN-':
            continue

        caractere = _caractere_do_evento(janela)
        if caractere is None:
            continue      # Shift, Ctrl, setas: são modificador, não resposta

        esperado = texto[posicao]
        batidas.append(metricas.Batida(esperado=esperado, digitado=caractere,
                                       ms=agora - ultima_batida))
        ultima_batida = agora

        if caractere == esperado.lower():
            janela[f'-ALVO_{posicao}-'].update(text_color='green')
            posicao += 1
            destacar_proxima()
        else:
            # A tecla errada NÃO entra: o alvo não avança e a certa continua acesa.
            janela[f'-ALVO_{posicao}-'].update(text_color='red')
            teclado.pintar(caractere, 'errada')

    duracao = (_agora_ms() - inicio) / 1000.0
    janela.close()
    return {'batidas': batidas, 'duracao_s': duracao, 'cancelado': cancelado}


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


def mostrar_relatorio(registro, avaliacao, idioma):
    """Mostra o resultado e, quando reprova, diz exatamente o que faltou."""
    motivos = ', '.join(
        get_text(f'licao_faltou_{f}', idioma) for f in avaliacao.faltou)
    veredito = (get_text('licao_aprovado', idioma) if avaliacao.aprovado
                else get_text('licao_reprovado', idioma).format(motivos))
    regularidade = registro['regularidade']
    titulo = get_text('licao_relatorio_titulo', idioma).format(registro['nivel'])
    layout = [
        [sg.Text(titulo, font=('Helvetica', 16))],
        [sg.Text(veredito, font=('Helvetica', 13, 'bold'),
                 text_color='darkgreen' if avaliacao.aprovado else 'darkorange')],
        [sg.HSeparator()],
        [sg.Text(get_text('licao_wpm', idioma).format(
            registro['wpm_bruto'], registro['wpm_meta']))],
        [sg.Text(get_text('licao_tropecos_de', idioma).format(
            registro['tropecos'], registro['total_teclas']))],
        [sg.Text(get_text('licao_regularidade', idioma).format(
            '—' if regularidade is None else f'{regularidade:.0%}'))],
        [sg.Button(get_text('licao_repetir', idioma), key='-REPETIR-'),
         sg.Button(get_text('licao_proximo', idioma), key='-PROXIMO-')],
    ]
    janela = sg.Window(titulo, layout, modal=True, element_justification='center')
    while True:
        evento, _ = janela.read()
        if evento in (sg.WIN_CLOSED, '-REPETIR-', '-PROXIMO-'):
            break
    janela.close()
