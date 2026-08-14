"""TouchTypingTrainer — treinador de digitação com correção caractere a caractere.

Como o programa funciona, em uma passada:

1. A janela principal só escolhe *preferências* (idioma, tamanho da frase, fonte das
   frases, limite de tempo). Ela não treina nada — ao clicar em "Iniciar Treinamento"
   essas preferências são passadas para `start_training_session`, que abre a janela do
   exercício em modo modal.
2. Durante o exercício, cada caractere da frase-alvo é um elemento `sg.Text` separado
   na tela. É isso que permite pintar letra por letra (cinza = ainda não digitada,
   verde = certa, vermelha = errada) enquanto o usuário digita, sem redesenhar a janela.
3. O erro é *permanente*: quando o usuário erra a posição i, `error_committed_at_position[i]`
   vira True e não volta atrás nem se ele apagar e corrigir. Isso separa duas métricas
   no relatório — "Erros (texto final)", que olha só o resultado, e "Total de erros
   cometidos", que mede quantas vezes ele tropeçou no caminho.
4. A troca de idioma recria a janela inteira (`create_main_window`) em vez de atualizar
   rótulo por rótulo, porque frames e larguras mudam de tamanho junto com o texto.

Edições: este mesmo código roda como edição **free** (FreeSimpleGUI, completa) ou
**trial** (PySimpleGUI, que exige registro) — ver `gui_backend.py` e `build.py`.
"""
import os
import random
import time
from datetime import datetime

import ai_exercises
import aplicativo
import historico
import layouts
import licoes
import metricas
import sessao as mod_sessao
import tema
from gui_backend import sg
from i18n import get_text, translations
from sentences_ai import FRASES_IA

# Velocidade de digitação usada como régua, em caracteres por segundo. Não são
# "metas": servem para calcular o tempo do exercício e classificar o desempenho.
# 1,5 c/s é o ritmo de quem está aprendendo — é ele que define o tempo-base.
CPS_FAST = 4.0
CPS_FASTER = 2.5
CPS_LEARNING = 1.5

# Frase com menos de 60 caracteres conta como curta; a partir daí, longa.
LIMITE_FRASE_CURTA = 60

# Preferências correntes. Ficam em variáveis de módulo porque a janela é destruída e
# recriada a cada troca de idioma — o estado precisa sobreviver à janela.
current_lang = 'en'
current_length_pref = 'mixed'
current_source_pref = 'builtin'
current_time_limit_mode = 'auto_1x'
current_manual_time_setting = 60

# Frases carregadas de um .txt escolhido pelo usuário (fonte "De Arquivo")
custom_sentences_all, custom_sentences_short, custom_sentences_long = [], [], []

# Frases da fonte "Gerado por IA": banco que acompanha o programa + o que a IA gerar
# nesta máquina. Recarregadas a cada troca de idioma por `carregar_frases_ia`.
ai_sentences_all, ai_sentences_short, ai_sentences_long = [], [], []

# Onde o progresso é gravado. Resolvido uma vez por execução; o aviso de que
# caiu para a pasta do usuário só aparece na primeira vez.
_caminho_do_historico = None
_ja_avisou_da_queda = False


def caminho_do_historico():
    """Resolve (uma vez) onde o progresso mora e avisa se caiu para a home."""
    global _caminho_do_historico, _ja_avisou_da_queda
    if _caminho_do_historico is None:
        _caminho_do_historico, caiu = historico.resolver_caminho(
            historico.pasta_do_executavel(), historico.pasta_do_usuario())
        if caiu and not _ja_avisou_da_queda:
            _ja_avisou_da_queda = True
            sg.popup(get_text('historico_caiu_para_usuario', current_lang).format(
                _caminho_do_historico), keep_on_top=True)
    return _caminho_do_historico


# ---------------------------------------------------------------------------
# Fonte de frases gerada por IA
# ---------------------------------------------------------------------------

def carregar_frases_ia(lang_code):
    """Monta o conjunto de frases da IA para o idioma: banco embutido + cache local.

    O banco embutido (`sentences_ai.py`) foi gerado uma vez com a mesma API e viaja
    dentro do executável, então a fonte "Gerado por IA" já funciona na primeira
    execução e sem internet. O cache é o que a IA gerou nesta máquina em execuções
    anteriores (`~/.touchtypingtrainer/frases_ia.json`).
    """
    global ai_sentences_all, ai_sentences_short, ai_sentences_long
    embutidas = FRASES_IA.get(lang_code, {})
    frases = list(embutidas.get('short', [])) + list(embutidas.get('long', []))
    frases += ai_exercises.carregar_cache().get(lang_code, [])
    # dedup preservando a ordem, para não sortear a mesma frase com peso dobrado
    vistas, unicas = set(), []
    for f in frases:
        if f.lower() not in vistas:
            vistas.add(f.lower())
            unicas.append(f)
    ai_sentences_all = unicas
    ai_sentences_short = [f for f in unicas if len(f) < LIMITE_FRASE_CURTA]
    ai_sentences_long = [f for f in unicas if len(f) >= LIMITE_FRASE_CURTA]
    return len(ai_sentences_all)


def registrar_frases_ia(lang_code, frases):
    """Guarda no cache as frases recém-geradas e recarrega o conjunto em memória."""
    cache = ai_exercises.carregar_cache()
    atuais = cache.get(lang_code, [])
    vistas = {f.lower() for f in atuais}
    novas = [f for f in frases if f.lower() not in vistas]
    cache[lang_code] = atuais + novas
    ai_exercises.salvar_cache(cache)
    carregar_frases_ia(lang_code)
    return len(novas)


# ---------------------------------------------------------------------------
# Janela principal
# ---------------------------------------------------------------------------

def create_main_window(lang_for_window, length_pref_for_window, source_pref_for_window,
                       time_mode_for_window, manual_time_for_window):
    """Cria a janela de preferências já refletindo o estado atual.

    Recebe o estado por parâmetro (em vez de ler as globais) justamente porque é
    chamada de novo a cada troca de idioma: quem chama decide qual estado desenhar.
    """
    tema.aplicar(sg)
    font_settings = tema.texto(tema.TAMANHO_APOIO)
    app_window_title = get_text('app_title', lang_for_window)

    # Idioma: o valor do rádio é a chave de evento, o dicionário mapeia para o código
    lang_options_map = {'-ENGLISH-': 'en', '-ITALIAN-': 'it', '-PORTUGUESE-': 'pt'}
    lang_display_name_keys = {'en': 'english', 'it': 'italian', 'pt': 'portuguese'}
    lang_radios = []
    for event_key_suffix, short_code in lang_options_map.items():
        display_name_key = lang_display_name_keys[short_code]
        lang_radios.append(sg.Radio(get_text(display_name_key, lang_for_window), 'LANG',
                                    key=event_key_suffix,
                                    default=(lang_for_window == short_code),
                                    enable_events=True, font=font_settings))
    lang_frame = sg.Frame(get_text('select_language', lang_for_window), [lang_radios],
                          font=font_settings)

    # Fonte das frases: internas, arquivo .txt do usuário, ou geradas por IA
    fontes = [('BUILTIN', 'source_builtin', 'builtin'),
              ('CUSTOM', 'source_custom', 'custom'),
              ('AI', 'source_ai', 'ai')]
    source_radios = [sg.Radio(get_text(rotulo, lang_for_window), 'SOURCE',
                              key=f'-SOURCE_{chave}-', default=(source_pref_for_window == valor),
                              enable_events=True, font=font_settings)
                     for chave, rotulo, valor in fontes]
    source_frame = sg.Frame(get_text('sentence_source_label', lang_for_window),
                            [source_radios], font=font_settings, expand_x=True)

    # Tamanho da frase: só faz sentido para as frases internas, por isso o frame some
    # quando a fonte é arquivo ou IA (lá o usuário treina com o que tiver).
    length_radios = [sg.Radio(get_text(f'length_{len_key.lower()}', lang_for_window), 'LENGTH',
                              key=f'-LENGTH_{len_key.upper()}-',
                              default=(length_pref_for_window == len_key.lower()),
                              enable_events=True, font=font_settings)
                     for len_key in ('SHORT', 'LONG', 'MIXED')]
    length_frame = sg.Frame(get_text('sentence_length_label', lang_for_window), [length_radios],
                            key='-LENGTH_FRAME-', visible=(source_pref_for_window == 'builtin'),
                            font=font_settings, expand_x=True)

    # Botões de arquivo (carregar .txt / baixar exemplo), visíveis só na fonte "De Arquivo"
    file_ops_column = sg.Column(
        [[sg.Button(get_text('load_custom_file_button', lang_for_window), key='-LOAD_CUSTOM_FILE-',
                    font=font_settings, expand_x=True),
          sg.Button(get_text('download_example_button', lang_for_window), key='-DOWNLOAD_EXAMPLE-',
                    font=font_settings, expand_x=True)]],
        justification='center', key='-FILE_OPS_COLUMN-',
        visible=(source_pref_for_window == 'custom'), expand_x=True)

    # Botão de geração por IA + contador de frases disponíveis, visíveis na fonte "IA"
    total_ia = len(ai_sentences_all)
    status_ia = (get_text('ai_status_available', lang_for_window).format(total_ia) if total_ia
                 else get_text('ai_no_sentences', lang_for_window))
    ai_ops_column = sg.Column(
        [[sg.Button(get_text('ai_generate_button', lang_for_window), key='-AI_GENERATE-',
                    font=font_settings, expand_x=True)],
         [sg.Text(status_ia, key='-AI_STATUS-', font=tema.texto(tema.TAMANHO_APOIO), justification='center',
                  expand_x=True)]],
        justification='center', key='-AI_OPS_COLUMN-',
        visible=(source_pref_for_window == 'ai'), expand_x=True)

    # Limite de tempo: automático (1x/2x/3x do tempo-base) ou manual em segundos
    time_limit_radios_data = [('auto_1x', 'time_auto_1x_label'), ('auto_2x', 'time_auto_2x_label'),
                              ('auto_3x', 'time_auto_3x_label'), ('manual', 'time_manual_label')]
    time_limit_radios = [sg.Radio(get_text(label_key, lang_for_window), 'TIMEMODE',
                                  key=f'-TIME_{mode_key.upper()}-',
                                  default=(time_mode_for_window == mode_key),
                                  enable_events=True, font=font_settings)
                         for mode_key, label_key in time_limit_radios_data]
    manual_time_input_row = [
        sg.Text(get_text('manual_time_seconds_label', lang_for_window), font=font_settings),
        sg.InputText(str(manual_time_for_window), key='-MANUAL_TIME_INPUT-', size=(5, 1),
                     font=font_settings, enable_events=True)]
    # A linha dos segundos fica dentro de uma Column própria só para poder ser escondida
    # inteira quando o modo não é manual.
    manual_time_container = sg.Column([manual_time_input_row], key='-MANUAL_TIME_ROW-',
                                      visible=(time_mode_for_window == 'manual'))
    time_settings_frame = sg.Frame(get_text('time_limit_settings_label', lang_for_window),
                                   [time_limit_radios, [manual_time_container]],
                                   font=font_settings, expand_x=True)

    # Configuração da lição: quantos exercícios na série e em que nível treinar.
    # O seletor lista SÓ os níveis já liberados — revisar o passado é permitido,
    # pular adiante não, senão o portão de progressão deixa de existir.
    sessao_atual = mod_sessao.Sessao(lang_for_window, caminho_do_historico())
    niveis = sessao_atual.niveis_disponiveis()
    rotulos = [aplicativo.rotulo_do_nivel(n, sessao_atual, lang_for_window)
               for n in niveis]
    licao_frame = sg.Frame(get_text('menu_modo_licao', lang_for_window), [
        [sg.Text(get_text('menu_serie_label', lang_for_window),
                 font=tema.texto(tema.TAMANHO_APOIO)),
         sg.Combo([str(n) for n in mod_sessao.EXERCICIOS_POR_SERIE],
                  default_value=str(mod_sessao.PADRAO_DE_SERIE), key='-SERIE-',
                  readonly=True, size=(5, 1), font=tema.texto(tema.TAMANHO_APOIO))],
        [sg.Text(get_text('menu_nivel_label', lang_for_window),
                 font=tema.texto(tema.TAMANHO_APOIO)),
         sg.Combo(rotulos, default_value=rotulos[-1], key='-NIVEL-', readonly=True,
                  size=(38, 1), font=tema.texto(tema.TAMANHO_APOIO))],
    ], font=tema.texto(tema.TAMANHO_APOIO), expand_x=True)

    layout = [
        [sg.Text(app_window_title, font=tema.texto(tema.TAMANHO_TITULO, True),
                 justification='center', expand_x=True, key='-APP_TITLE_DISPLAY-')],
        [sg.Text(get_text('welcome_message', lang_for_window), font=tema.texto(tema.TAMANHO_CORPO),
                 justification='center', expand_x=True)],
        [sg.VPush()], [lang_frame], [source_frame], [length_frame],
        [file_ops_column], [ai_ops_column], [time_settings_frame], [sg.VPush()],
        [sg.Button(get_text('hand_guide_button', lang_for_window), key='-HAND_GUIDE-',
                   expand_x=True, font=tema.texto(tema.TAMANHO_CORPO))],
        [licao_frame],
        [sg.Button(get_text('menu_modo_licao', lang_for_window), key='-MODO_LICAO-',
                   expand_x=True, font=tema.texto(tema.TAMANHO_SUBTITULO, True),
                   button_color=(tema.SOBRE_PRIMARIA, tema.PRIMARIA))],
        [sg.Button(get_text('menu_treino_livre', lang_for_window), key='-START_TRAINING-',
                   expand_x=True, font=tema.texto(tema.TAMANHO_CORPO))],
        [sg.VPush()],
        [sg.Button(get_text('exit_button', lang_for_window), key='-EXIT-', expand_x=True,
                   font=tema.texto(tema.TAMANHO_APOIO), button_color=('white', 'firebrick'))],
    ]
    return sg.Window(app_window_title, layout, finalize=True,
                     element_justification='center', size=(800, 860))


def show_hand_positioning_guide():
    """Guia de mãos: o teclado desenhado, colorido por dedo.

    Substitui o desenho ASCII em fonte monoespaçada. A informação é a mesma, mas
    aqui ela é dado consultável (`layouts.py`) em vez de texto — e a mesma cor
    liga cada tecla ao dedo na ilustração das mãos.
    """
    aplicativo.abrir_guia(current_lang, caminho_do_historico())


def rodar_licao(idioma, tamanho_da_serie=None, nivel=None):
    """Abre o Modo Lição: série inteira numa janela só, sem modal por etapa."""
    aplicativo.abrir_licao(idioma, caminho_do_historico(), tamanho_da_serie, nivel)


# ---------------------------------------------------------------------------
# Métricas e fontes de frases
# ---------------------------------------------------------------------------

def calculate_accuracy_report(target, typed):
    """Compara o texto digitado com o alvo, posição a posição.

    Conta como erro tanto o caractere trocado quanto o que falta ou sobra — por isso o
    laço vai até o maior dos dois comprimentos. A precisão é calculada sobre o tamanho
    do alvo; digitar menos não "melhora" a nota.
    """
    errors = 0
    target_len = len(target)
    typed_len = len(typed)
    for i in range(max(target_len, typed_len)):
        if i < target_len and i < typed_len:
            if target[i] != typed[i]:
                errors += 1
        elif i < target_len or i < typed_len:
            errors += 1          # caractere faltando (ou sobrando) também é erro
    accuracy = max(0, (target_len - errors) / target_len) * 100 if target_len > 0 \
        else (100 if typed_len == 0 else 0)
    return {'target_sentence': target, 'typed_sentence': typed, 'target_length': target_len,
            'typed_length': typed_len, 'errors': errors, 'accuracy': round(accuracy, 2)}


def load_custom_sentences_from_file(filepath, lang_code):
    """Lê um .txt do usuário: uma frase por linha, linhas em branco ignoradas.

    Devolve True se pelo menos uma frase foi lida. As frases já entram separadas em
    curtas e longas para o seletor de tamanho continuar funcionando com arquivo.
    """
    global custom_sentences_all, custom_sentences_short, custom_sentences_long
    custom_sentences_all, custom_sentences_short, custom_sentences_long = [], [], []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        for line in lines:
            sentence = line.strip()
            if not sentence:
                continue
            custom_sentences_all.append(sentence)
            if len(sentence) < LIMITE_FRASE_CURTA:
                custom_sentences_short.append(sentence)
            else:
                custom_sentences_long.append(sentence)
        if custom_sentences_all:
            sg.popup(get_text('file_loaded_popup', lang_code).format(os.path.basename(filepath)),
                     keep_on_top=True)
            return True
        sg.popup_error(get_text('error_no_sentences', lang_code) +
                       f' (in {os.path.basename(filepath)})', keep_on_top=True)
        return False
    except Exception as e:
        sg.popup_error(get_text('file_load_error_popup', lang_code).format(str(e)),
                       keep_on_top=True)
        return False


def download_example_txt_file(lang_code):
    """Salva um .txt de exemplo para o usuário ver o formato esperado do arquivo."""
    example_content = get_text('short_sentences', lang_code)[0] + '\n' + \
        get_text('long_sentences', lang_code)[0] + """
Questa è una frase di esempio per file personalizzati.
Esta é uma frase de exemplo para arquivos personalizados."""
    try:
        save_path = sg.popup_get_file(get_text('download_example_button', lang_code),
                                      save_as=True, default_extension='.txt',
                                      file_types=(('Text Files', '*.txt'),), no_window=True,
                                      keep_on_top=True)
        if save_path:
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(example_content)
            sg.popup(get_text('example_file_saved_popup', lang_code).format(save_path),
                     keep_on_top=True)
    except Exception as e:
        sg.popup_error(get_text('example_file_save_error_popup', lang_code) + f'\n{str(e)}',
                       keep_on_top=True)


def escolher_frases(length_preference, source_preference, lang_code):
    """Decide de qual conjunto sortear a frase do exercício.

    Devolve (frases, erro_traduzido). O erro vem pronto para exibição porque cada fonte
    vazia falha por um motivo diferente: arquivo sem frases, IA ainda não gerada, ou
    idioma sem frases internas.
    """
    if source_preference == 'custom':
        if not custom_sentences_all:
            return [], get_text('error_no_sentences', lang_code) + ' (Custom file empty).'
        return custom_sentences_all, None
    if source_preference == 'ai':
        if not ai_sentences_all:
            return [], get_text('ai_no_sentences', lang_code)
        if length_preference == 'short' and ai_sentences_short:
            return ai_sentences_short, None
        if length_preference == 'long' and ai_sentences_long:
            return ai_sentences_long, None
        return ai_sentences_all, None
    active_short = get_text('short_sentences', lang_code)
    active_long = get_text('long_sentences', lang_code)
    if length_preference == 'short':
        escolhidas = active_short
    elif length_preference == 'long':
        escolhidas = active_long
    else:
        escolhidas = active_short + active_long
    if not escolhidas:
        return [], get_text('error_no_sentences', lang_code)
    return escolhidas, None


# ---------------------------------------------------------------------------
# Sessão de treino
# ---------------------------------------------------------------------------

def start_training_session(length_preference, source_preference, time_mode, manual_time_val,
                           lang_code):
    """Roda um exercício completo: sorteia a frase, cronometra, corrige e mostra o relatório."""
    chosen_sentences, erro = escolher_frases(length_preference, source_preference, lang_code)
    if erro:
        sg.popup_error(erro, keep_on_top=True)
        return

    target_sentence = random.choice(chosen_sentences)
    target_len = len(target_sentence)
    # Uma marca por caractere da frase: True = o usuário já errou aqui alguma vez.
    # Não é zerada quando ele corrige — é justamente o histórico de tropeços.
    error_committed_at_position = [False] * target_len

    # Tempo-base: quanto levaria digitando no ritmo de aprendizado. O 600.0 é a rede de
    # segurança para frase vazia ou constante zerada, para não dividir por zero nem dar
    # um limite de tempo instantâneo.
    base_time = target_len / CPS_LEARNING if CPS_LEARNING > 0 and target_len > 0 else 600.0
    if base_time == 0 and target_len > 0:
        base_time = 600.0
    max_exercise_time = base_time
    if time_mode == 'auto_2x':
        max_exercise_time = base_time * 2
    elif time_mode == 'auto_3x':
        max_exercise_time = base_time * 3
    elif time_mode == 'manual':
        try:
            current_manual_val = float(manual_time_val)
            if current_manual_val <= 0:
                raise ValueError('Time must be positive.')
            max_exercise_time = current_manual_val
        except ValueError:
            # Valor inválido não cancela o treino: avisa e cai no tempo automático
            sg.popup(get_text('invalid_manual_time_popup', lang_code), keep_on_top=True)
            max_exercise_time = base_time

    # Marcos de velocidade para classificar o desempenho no fim
    time_limit_fast = target_len / CPS_FAST if CPS_FAST > 0 else float('inf')
    time_limit_faster = target_len / CPS_FASTER if CPS_FASTER > 0 else float('inf')

    # Um sg.Text por caractere: é o que permite colorir letra a letra durante a digitação
    target_char_elements = [
        sg.Text(c, key=f'-TARGET_CHAR_{i}-', font=tema.mono(tema.TAMANHO_DESTAQUE, True), pad=(0, 0),
                text_color=get_text('pending_char_color', lang_code))
        for i, c in enumerate(target_sentence)]
    target_display_container = sg.Column([[*target_char_elements]], scrollable=True,
                                         expand_x=True, background_color='lightgrey',
                                         pad=(5, 10), key='-TARGET_DISPLAY_CONTAINER-')
    timer_display = sg.Text(f"{get_text('timer_label', lang_code)} 0.0s / {max_exercise_time:.1f}s",
                            key='-TIMER_DISPLAY-', font=tema.texto(tema.TAMANHO_APOIO))
    training_layout = [
        [sg.Text(get_text('sentence_to_type_label', lang_code)), sg.Push(), timer_display],
        [target_display_container],
        [sg.Text(get_text('your_input_label', lang_code))],
        [sg.InputText(key='-USER_INPUT-', font=tema.mono(tema.TAMANHO_DESTAQUE), expand_x=True, focus=True,
                      enable_events=True)],
        [sg.Button(get_text('submit_button', lang_code), key='-SUBMIT-', bind_return_key=True),
         sg.Button(get_text('cancel_button', lang_code), key='-CANCEL-')],
    ]
    training_window = sg.Window(get_text('training_prompt_title', lang_code), training_layout,
                                modal=True, keep_on_top=True, finalize=True, resizable=True,
                                size=(800, 220))
    start_time = time.time()
    user_typed_sentence_final = ''
    timed_out = False
    training_window['-USER_INPUT-'].set_focus()

    while True:
        # timeout=100 faz o read() voltar 10x por segundo mesmo sem o usuário digitar:
        # é o que mantém o cronômetro andando e permite estourar o tempo sozinho.
        event, values = training_window.read(timeout=100)
        elapsed_time = time.time() - start_time
        display_elapsed = min(elapsed_time, max_exercise_time)
        training_window['-TIMER_DISPLAY-'].update(
            f"{get_text('timer_label', lang_code)} {display_elapsed:.1f}s / {max_exercise_time:.1f}s")

        if not timed_out and elapsed_time >= max_exercise_time:
            timed_out = True
            user_typed_sentence_final = values['-USER_INPUT-']
            break
        if event == sg.WIN_CLOSED or event == '-CANCEL-':
            user_typed_sentence_final = values['-USER_INPUT-']
            break
        if event == '-USER_INPUT-':
            # A cada tecla, repinta a frase inteira: barato o suficiente nesse tamanho e
            # evita ter de rastrear qual posição mudou (colar texto muda várias de uma vez).
            typed_text = values['-USER_INPUT-']
            for i, target_char in enumerate(target_sentence):
                char_elem = training_window[f'-TARGET_CHAR_{i}-']
                if i < len(typed_text):
                    if typed_text[i] != target_char:
                        if not error_committed_at_position[i]:
                            error_committed_at_position[i] = True
                        char_elem.update(text_color=get_text('incorrect_char_color', lang_code))
                    else:
                        char_elem.update(text_color=get_text('correct_char_color', lang_code))
                else:
                    char_elem.update(text_color=get_text('pending_char_color', lang_code))
        if event == '-SUBMIT-':
            user_typed_sentence_final = values['-USER_INPUT-']
            break

    training_window.close()
    final_elapsed_time = min(elapsed_time, max_exercise_time)
    final_persistent_errors = sum(error_committed_at_position)

    if timed_out:
        sg.popup_auto_close(get_text('perf_time_limit_exceeded', lang_code), title='Timeout',
                            auto_close_duration=3, grab_anywhere=True, keep_on_top=True)

    if user_typed_sentence_final is None:
        return

    report_data = calculate_accuracy_report(target_sentence, user_typed_sentence_final)
    acc_thresh = 85          # abaixo disso, precisão vira o problema principal
    # A ordem importa: tempo estourado e precisão baixa vêm antes da velocidade, porque
    # não adianta elogiar quem digitou rápido e errado.
    if timed_out:
        perf_txt = get_text('perf_time_limit_exceeded', lang_code)
    elif report_data['accuracy'] < acc_thresh:
        perf_txt = get_text('perf_focus_accuracy', lang_code)
    elif final_elapsed_time <= time_limit_fast:
        perf_txt = get_text('perf_excellent_speed', lang_code)
    elif final_elapsed_time <= time_limit_faster:
        perf_txt = get_text('perf_good_speed', lang_code)
    else:
        perf_txt = get_text('perf_learning_pace', lang_code)

    perf_color = 'black'
    if get_text('perf_excellent_speed', lang_code) in perf_txt:
        perf_color = 'darkgreen'
    elif get_text('perf_good_speed', lang_code) in perf_txt:
        perf_color = 'green'
    elif get_text('perf_focus_accuracy', lang_code) in perf_txt:
        perf_color = 'darkorange'
    elif get_text('perf_time_limit_exceeded', lang_code) in perf_txt:
        perf_color = 'red'

    # O treino livre também entra no histórico, com modo 'livre'. Ele não conta
    # para a progressão do currículo, mas conta para a evolução ao longo do tempo.
    historico.gravar({
        'quando': datetime.now().astimezone().isoformat(timespec='seconds'),
        'modo': 'livre',
        'nivel': None,
        'idioma': lang_code,
        'layout': layouts.LAYOUT_POR_IDIOMA[lang_code],
        'alvo': target_sentence,
        'duracao_s': round(final_elapsed_time, 2),
        'wpm_bruto': round(metricas.wpm(report_data['typed_length'],
                                        final_elapsed_time), 2),
        'wpm_liquido': round(metricas.wpm_liquido(report_data['typed_length'],
                                                  final_elapsed_time,
                                                  report_data['errors']), 2),
        'tropecos': final_persistent_errors,
        'total_teclas': target_len,
        # O treino livre lê o campo de texto inteiro a cada tecla, não batida por
        # batida: não há intervalo por tecla para medir ritmo.
        'regularidade': None,
        'aprovado': None,
        'teclas': {},
    }, caminho_do_historico())

    report_layout = [
        [sg.Text(get_text('report_title', lang_code), font=tema.texto(tema.TAMANHO_SUBTITULO, True))],
        [sg.Text(f"{get_text('report_target_sentence', lang_code)} {report_data['target_sentence']}",
                 font=tema.mono(tema.TAMANHO_APOIO), size=(70, 2))],
        [sg.Text(f"{get_text('report_your_sentence', lang_code)} {report_data['typed_sentence']}",
                 font=tema.mono(tema.TAMANHO_APOIO), size=(70, 2))],
        [sg.HSeparator()],
        [sg.Text(f"{get_text('report_target_length', lang_code)} {report_data['target_length']}")],
        [sg.Text(f"{get_text('report_typed_length', lang_code)} {report_data['typed_length']}")],
        [sg.Text(f"{get_text('report_errors', lang_code)} {report_data['errors']}",
                 text_color='red' if report_data['errors'] > 0 else 'green')],
        [sg.Text(f"{get_text('report_total_mistakes_made', lang_code)} {final_persistent_errors}",
                 text_color='red' if final_persistent_errors > 0 else 'green')],
        [sg.Text(f"{get_text('report_accuracy', lang_code)} {report_data['accuracy']}%",
                 text_color='green' if report_data['accuracy'] >= 95
                 else ('darkorange' if report_data['accuracy'] >= acc_thresh else 'red'))],
        [sg.Text(f"{get_text('report_time_taken', lang_code)} {final_elapsed_time:.2f}s")],
        [sg.Text('WPM: {:.1f} / {:.1f}'.format(
            metricas.wpm(report_data['typed_length'], final_elapsed_time),
            metricas.wpm_liquido(report_data['typed_length'], final_elapsed_time,
                                 report_data['errors'])))],
        [sg.Text(f"{get_text('report_performance_label', lang_code)} {perf_txt}",
                 font=tema.texto(tema.TAMANHO_CORPO, True), text_color=perf_color)],
        [sg.Button(get_text('ok_button', lang_code), key='-OK-')],
    ]
    report_win = sg.Window(get_text('report_title', lang_code), report_layout, modal=True,
                           keep_on_top=True, resizable=True, element_justification='center')
    while True:
        ev, _ = report_win.read()
        if ev == sg.WIN_CLOSED or ev == '-OK-':
            break
    report_win.close()


# ---------------------------------------------------------------------------
# Laço principal da janela de preferências
# ---------------------------------------------------------------------------

def main():
    global current_lang, current_length_pref, current_source_pref
    global current_time_limit_mode, current_manual_time_setting

    carregar_frases_ia(current_lang)
    window = create_main_window(current_lang, current_length_pref, current_source_pref,
                                current_time_limit_mode, current_manual_time_setting)
    gerando_ia = False       # trava para não disparar duas gerações ao mesmo tempo

    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED or event == '-EXIT-':
            break

        # --- troca de idioma: recria a janela inteira ---
        lang_to_recreate_for = None
        if event == '-ENGLISH-':
            lang_to_recreate_for = 'en'
        elif event == '-ITALIAN-':
            lang_to_recreate_for = 'it'
        elif event == '-PORTUGUESE-':
            lang_to_recreate_for = 'pt'
        if lang_to_recreate_for and current_lang != lang_to_recreate_for:
            current_lang = lang_to_recreate_for
            carregar_frases_ia(current_lang)   # o banco da IA é por idioma
            window.close()
            window = create_main_window(current_lang, current_length_pref, current_source_pref,
                                        current_time_limit_mode, current_manual_time_setting)
            continue

        # --- fonte das frases: mostra/esconde os controles de cada modo ---
        source_ui_update_needed = False
        for chave, valor in (('-SOURCE_BUILTIN-', 'builtin'), ('-SOURCE_CUSTOM-', 'custom'),
                             ('-SOURCE_AI-', 'ai')):
            if event == chave and current_source_pref != valor:
                current_source_pref = valor
                source_ui_update_needed = True
        if source_ui_update_needed:
            window['-FILE_OPS_COLUMN-'].update(visible=(current_source_pref == 'custom'))
            window['-AI_OPS_COLUMN-'].update(visible=(current_source_pref == 'ai'))
            window['-LENGTH_FRAME-'].update(visible=(current_source_pref == 'builtin'))

        # --- tamanho da frase ---
        if event == '-LENGTH_SHORT-' and current_length_pref != 'short':
            current_length_pref = 'short'
        elif event == '-LENGTH_LONG-' and current_length_pref != 'long':
            current_length_pref = 'long'
        elif event == '-LENGTH_MIXED-' and current_length_pref != 'mixed':
            current_length_pref = 'mixed'

        # --- modo de limite de tempo ---
        time_mode_ui_update_needed = False
        newly_selected_time_mode = current_time_limit_mode
        for chave, modo in (('-TIME_AUTO_1X-', 'auto_1x'), ('-TIME_AUTO_2X-', 'auto_2x'),
                            ('-TIME_AUTO_3X-', 'auto_3x'), ('-TIME_MANUAL-', 'manual')):
            if event == chave:
                newly_selected_time_mode = modo
        if current_time_limit_mode != newly_selected_time_mode:
            current_time_limit_mode = newly_selected_time_mode
            time_mode_ui_update_needed = True

        # Valida o campo de segundos enquanto o usuário digita. Campo vazio é tolerado
        # (ele ainda está digitando); qualquer outra coisa inválida volta ao último valor.
        if event == '-MANUAL_TIME_INPUT-':
            try:
                val = int(values['-MANUAL_TIME_INPUT-'])
                if val > 0:
                    current_manual_time_setting = val
                else:
                    window['-MANUAL_TIME_INPUT-'].update(str(current_manual_time_setting))
            except ValueError:
                if values['-MANUAL_TIME_INPUT-'] != '':
                    window['-MANUAL_TIME_INPUT-'].update(str(current_manual_time_setting))

        if time_mode_ui_update_needed:
            window['-MANUAL_TIME_ROW-'].update(visible=(current_time_limit_mode == 'manual'))
            if current_time_limit_mode == 'manual':
                window['-MANUAL_TIME_INPUT-'].update(str(current_manual_time_setting))
                window['-MANUAL_TIME_INPUT-'].set_focus()

        # --- geração de exercícios por IA ---
        if event == '-AI_GENERATE-' and not gerando_ia:
            gerando_ia = True
            window['-AI_GENERATE-'].update(disabled=True)
            window['-AI_STATUS-'].update(get_text('ai_generating_popup', current_lang))
            # A chamada de rede roda em thread; o resultado volta como evento '-AI_DONE-'
            # para ser tratado aqui no laço, com a janela respondendo o tempo todo.
            ai_exercises.gerar_em_thread(
                current_lang,
                lambda frases, erro: window.write_event_value('-AI_DONE-', (frases, erro)))
        elif event == '-AI_DONE-':
            gerando_ia = False
            frases, erro = values['-AI_DONE-']
            window['-AI_GENERATE-'].update(disabled=False)
            if frases:
                novas = registrar_frases_ia(current_lang, frases)
                window['-AI_STATUS-'].update(
                    get_text('ai_status_available', current_lang).format(len(ai_sentences_all)))
                sg.popup(get_text('ai_generated_popup', current_lang).format(novas),
                         keep_on_top=True)
            else:
                total = len(ai_sentences_all)
                window['-AI_STATUS-'].update(
                    get_text('ai_status_available', current_lang).format(total) if total
                    else get_text('ai_no_sentences', current_lang))
                sg.popup_error(get_text('ai_error_popup', current_lang).format(erro),
                               keep_on_top=True)

        # --- botões de ação ---
        if event == '-LOAD_CUSTOM_FILE-':
            filepath = sg.popup_get_file(get_text('load_custom_file_button', current_lang),
                                         title='Select Text File',
                                         file_types=(('Text Files', '*.txt'),), keep_on_top=True)
            if filepath and load_custom_sentences_from_file(filepath, current_lang):
                if current_source_pref != 'custom':
                    current_source_pref = 'custom'
                    window['-SOURCE_CUSTOM-'].update(value=True)
                    window['-FILE_OPS_COLUMN-'].update(visible=True)
                    window['-AI_OPS_COLUMN-'].update(visible=False)
                    window['-LENGTH_FRAME-'].update(visible=False)
        elif event == '-DOWNLOAD_EXAMPLE-':
            download_example_txt_file(current_lang)
        elif event == '-HAND_GUIDE-':
            show_hand_positioning_guide()
        elif event == '-MODO_LICAO-':
            try:
                tamanho = int(values.get('-SERIE-') or mod_sessao.PADRAO_DE_SERIE)
            except (TypeError, ValueError):
                tamanho = mod_sessao.PADRAO_DE_SERIE
            # O rótulo do nível começa com "Nível N —"; o número é o que interessa.
            escolhido = None
            rotulo = values.get('-NIVEL-') or ''
            for pedaco in rotulo.replace('—', ' ').split():
                if pedaco.isdigit():
                    escolhido = int(pedaco)
                    break
            window.close()
            rodar_licao(current_lang, tamanho, escolhido)
            window = create_main_window(current_lang, current_length_pref,
                                        current_source_pref, current_time_limit_mode,
                                        current_manual_time_setting)
        elif event == '-START_TRAINING-':
            manual_time_to_pass = current_manual_time_setting
            if current_time_limit_mode == 'manual':
                try:
                    manual_input_val = values['-MANUAL_TIME_INPUT-']
                    if not manual_input_val.strip():
                        manual_time_to_pass = current_manual_time_setting
                    else:
                        manual_time_to_pass = int(manual_input_val)
                    if manual_time_to_pass <= 0:
                        sg.popup_error(get_text('invalid_manual_time_popup', current_lang),
                                       keep_on_top=True)
                        continue
                    current_manual_time_setting = manual_time_to_pass
                except ValueError:
                    sg.popup_error(get_text('invalid_manual_time_popup', current_lang),
                                   keep_on_top=True)
                    continue
            start_training_session(current_length_pref, current_source_pref,
                                   current_time_limit_mode, manual_time_to_pass, current_lang)

    window.close()


if __name__ == '__main__':
    main()
