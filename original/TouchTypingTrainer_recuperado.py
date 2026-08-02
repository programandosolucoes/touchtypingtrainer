import FreeSimpleGUI as sg
import random
import time
import os

# Velocidades de referência em caracteres por segundo
CPS_FAST = 4.0
CPS_FASTER = 2.5
CPS_LEARNING = 1.5

# Layouts de teclado em ASCII
abnt2_full_keyboard_ascii = """
+-----------------------------------------------------------------------------------+
| `~ | 1!| 2@| 3#| 4$| 5%| 6^| 7&| 8*| 9(| 0)| -_| =+| Backspace               |
| Tab |  Q|  W|  E|  R|  T|  Y|  U|  I|  O|  P|  ´`|  [{|          Enter        |
|CapsL|  A|  S|  D|  F|  G|  H|  J|  K|  L|  Ç|  ~^|  ]} |          |        |
|LShft|  Z|  X|  C|  V|  B|  N|  M|  ,<|  .>|  ;:| /?°|         RShift          |
|LCtrl|LWin|LAlt|                    Spacebar                     |RAltGr|Menu|RCtrl|
+-----------------------------------------------------------------------------------+
"""
us_qwerty_full_keyboard_ascii = """
+-----------------------------------------------------------------------------------+
| `~ | 1!| 2@| 3#| 4$| 5%| 6^| 7&| 8*| 9(| 0)| -_| =+| Backspace               |
| Tab |  Q|  W|  E|  R|  T|  Y|  U|  I|  O|  P|  [{|  ]}|         \\ |           |
|CapsL|  A|  S|  D|  F|  G|  H|  J|  K|  L|  ;:|  '"|          Enter            |
|LShft|  Z|  X|  C|  V|  B|  N|  M|  ,<|  .>|  /?|           RShift          |
|LCtrl|LWin|LAlt|                    Spacebar                     |RAlt|Menu|RCtrl|
+-----------------------------------------------------------------------------------+
"""
it_qwerty_full_keyboard_ascii = """
+-----------------------------------------------------------------------------------+
| \\| | 1!| 2"| 3£| 4$| 5%| 6&| 7/| 8(| 9)| 0=| ?'| ì^| Backspace               |
| Tab |  Q|  W|  E|  R|  T|  Y|  U|  I|  O|  P|  è*[|  é+]|         Invio         |
|CapsL|  A|  S|  D|  F|  G|  H|  J|  K|  L|  ò@|  à#|  ù§|                     |
|LShft|> <|  Z|  X|  C|  V|  B|  N|  M|  ;%|  :_|  -|           RShift          |
|LCtrl|LWin|LAlt|                    Spacebar                     |RAltGr|Menu|RCtrl|
+-----------------------------------------------------------------------------------+
"""

focused_keys_ascii_template = """
{line1}
      {left_hand_label}                           {right_hand_label}
      -------------------                     -----------------------
      | Q | W | E | R | T |         | Y | U | I | O | P | {key_right_of_p} |
      --- --- --- --- ---         --- --- --- --- --- -----
      |{L_P_key}|{L_R_key}|{L_M_key}|{L_I_key}|{L_I_key}|         |{R_I_key}|{R_I_key}|{R_M_key}|{R_R_key}|{R_P_key}| {R_P_Alt_key} |
      --- --- --- --- ---         --- --- --- --- --- -----
{line2}
{legend_title}
  {L_P_key_legend} = {pinky_label} ({left_label_short})        {R_P_key_legend} = {pinky_label} ({right_label_short})
  {L_R_key_legend} = {ring_label} ({left_label_short})       {R_R_key_legend} = {ring_label} ({right_label_short})
  {L_M_key_legend} = {middle_label} ({left_label_short})     {R_M_key_legend} = {middle_label} ({right_label_short})
  {L_I_key_legend} = {index_label} ({left_label_short})      {R_I_key_legend} = {index_label} ({right_label_short})

{thumbs_rest_label}
"""


translations = {
    'en': {
        'app_title': 'Touch Typing Trainer',
        'welcome_message': 'Welcome to the Touch Typing Trainer!',
        'select_language': 'Select Language:', 'italian': 'Italian', 'english': 'English', 'portuguese': 'Portuguese',
        'hand_guide_button': 'Hand Positioning Guide', 'start_training_button': 'Start Training', 'exit_button': 'Exit',
        'sentence_length_label': 'Sentence Length:', 'length_short': 'Short', 'length_long': 'Long', 'length_mixed': 'Mixed',
        'sentence_source_label': 'Sentence Source:', 'source_builtin': 'Built-in', 'source_custom': 'From File',
        'time_limit_settings_label': 'Time Limit Settings:',
        'time_auto_1x_label': 'Automatic (Learning Pace)', 'time_auto_2x_label': 'Automatic x2 Time',
        'time_auto_3x_label': 'Automatic x3 Time', 'time_manual_label': 'Manual',
        'manual_time_seconds_label': 'Seconds:', 'invalid_manual_time_popup': 'Invalid manual time. Using default.',
        'load_custom_file_button': 'Load Sentences (.txt)', 'download_example_button': 'Download Example .txt',
        'file_loaded_popup': 'Sentences loaded from: {}', 'file_load_error_popup': 'Error loading file: {}',
        'example_file_saved_popup': 'Example file saved to: {}', 'example_file_save_error_popup': 'Error saving example file.',
        'hand_guide_title': 'US QWERTY Hand Positioning Guide', 'key_right_of_p_char_en': ';',
        'focused_ascii_line1': 'Focus: QWERTY Row & Semicolon Key', 'left_hand_label': 'Left Hand', 'right_hand_label': 'Right Hand',
        'focused_ascii_line2': '(LP=Left Pinky, LR=Left Ring, etc.)', 'legend_title_ascii': 'Finger Legend:',
        'pinky_label_ascii': 'Pinky', 'ring_label_ascii': 'Ring', 'middle_label_ascii': 'Middle', 'index_label_ascii': 'Index',
        'left_label_short_ascii': 'L', 'right_label_short_ascii': 'R',
        'L_P_key_label_ascii': 'LP', 'L_R_key_label_ascii': 'LR', 'L_M_key_label_ascii': 'LM', 'L_I_key_label_ascii': 'LI',
        'R_P_key_label_ascii': 'RP', 'R_R_key_label_ascii': 'RR', 'R_M_key_label_ascii': 'RM', 'R_I_key_label_ascii': 'RI',
        'R_P_Alt_key_label_ascii': 'RP', 'thumbs_rest_label_ascii': 'Thumbs rest on SPACEBAR.',
        'general_keyboard_layout_label': '\nGeneral US QWERTY Keyboard Layout Context:', 'full_keyboard_ascii_art': us_qwerty_full_keyboard_ascii,
        'hand_guide_text_intro': "Proper hand positioning is key for efficient typing.\n\nHOME ROW (US QWERTY):\n  - Left Hand: Place fingers on A (Pinky), S (Ring), D (Middle), F (Index).\n  - Right Hand: Place fingers on J (Index), K (Middle), L (Ring), ; (Semicolon - Pinky).\n  - Thumbs: Rest lightly on the Spacebar.\n\nEXERCISE FOCUS (QWERTY Row & Semicolon Key):\n  Practice reaching these keys from the home row.\n  Left Hand:\n    - Pinky (LP): 'Q'\n    - Ring (LR): 'W'\n    - Middle (LM): 'E'\n    - Index (LI): 'R', 'T'\n\n  Right Hand:\n    - Index (RI): 'Y', 'U'\n    - Middle (RM): 'I'\n    - Ring (RR): 'O'\n    - Pinky (RP): 'P', ';' (Semicolon key)\n\n",
        'hand_guide_text_tips': '\nGENERAL TIPS:\n  - Keep wrists straight.\n  - Use light, quick strokes.\n  - Return fingers to home row.\n  - Accuracy first, then speed.\n',
        'training_prompt_title': 'Training Mode', 'sentence_to_type_label': 'Type this sentence:',
        'your_input_label': 'Your input:', 'timer_label': 'Time:',
        'submit_button': 'Submit', 'cancel_button': 'Cancel', 'ok_button': 'OK', 'report_title': 'Typing Report',
        'report_target_sentence': 'Target:', 'report_your_sentence': 'You typed:', 'report_target_length': 'Target length:',
        'report_typed_length': 'Your length:', 'report_errors': 'Errors (final text):', 'report_accuracy': 'Accuracy:',
        'report_total_mistakes_made': 'Total Mistakes Made:',
        'report_time_taken': 'Time taken:', 'report_performance_label': 'Performance:',
        'perf_excellent_speed': 'Excellent Speed! (Fast)', 'perf_good_speed': 'Good Speed! (Faster)',
        'perf_learning_pace': 'Keep Practicing! (Learning Pace)', 'perf_focus_accuracy': 'Focus on Accuracy!',
        'perf_time_limit_exceeded': 'Time Limit Exceeded. Practice more!',
        'error_no_sentences': 'No example sentences found.',
        'pending_char_color': 'grey60', 'correct_char_color': 'green', 'incorrect_char_color': 'red',
        'short_sentences': ['The cat sat on the mat.', 'Hello world example.', 'Test 123 go fast.'],
        'long_sentences': ['The quick brown fox jumps over the lazy dog with zeal.', 'Pack my box with five dozen large liquor jugs for the party.'],
    },
    'it': {
        'app_title': 'Trainer di Dattilografia',
        'welcome_message': 'Benvenuto/a al Trainer di Dattilografia!',
        'select_language': 'Seleziona Lingua:', 'italian': 'Italiano', 'english': 'Inglese', 'portuguese': 'Portoghese',
        'hand_guide_button': 'Guida Posizionamento Mani', 'start_training_button': 'Inizia Allenamento', 'exit_button': 'Esci',
        'sentence_length_label': 'Lunghezza Frase:', 'length_short': 'Corta', 'length_long': 'Lunga', 'length_mixed': 'Mista',
        'sentence_source_label': 'Sorgente Frasi:', 'source_builtin': 'Integrate', 'source_custom': 'Da File',
        'time_limit_settings_label': 'Impostazioni Limite Tempo:',
        'time_auto_1x_label': 'Automatico (Apprendimento)', 'time_auto_2x_label': 'Automatico x2 Tempo',
        'time_auto_3x_label': 'Automatico x3 Tempo', 'time_manual_label': 'Manuale',
        'manual_time_seconds_label': 'Secondi:', 'invalid_manual_time_popup': 'Tempo manuale non valido. Uso predefinito.',
        'load_custom_file_button': 'Carica Frasi (.txt)', 'download_example_button': 'Scarica Esempio .txt',
        'file_loaded_popup': 'Frasi caricate con successo da: {}', 'file_load_error_popup': 'Errore caricamento file: {}',
        'example_file_saved_popup': 'File di esempio salvato in: {}', 'example_file_save_error_popup': 'Errore salvataggio file di esempio.',
        'hand_guide_title': 'Guida Posizionamento Mani (QWERTY Italiana)', 'key_right_of_p_char_it': 'ù',
        'focused_ascii_line1': "Focus: Riga QWERTY & Tasto 'ù'", 'left_hand_label': 'Mano Sinistra', 'right_hand_label': 'Mano Destra',
        'focused_ascii_line2': '(MgS=Mignolo Sinistro, ecc.)', 'legend_title_ascii': 'Legenda Dita:',
        'pinky_label_ascii': 'Mignolo', 'ring_label_ascii': 'Anulare', 'middle_label_ascii': 'Medio', 'index_label_ascii': 'Indice',
        'left_label_short_ascii': 'S', 'right_label_short_ascii': 'D',
        'L_P_key_label_ascii': 'MgS', 'L_R_key_label_ascii': 'AnS', 'L_M_key_label_ascii': 'MdS', 'L_I_key_label_ascii': 'InS',
        'R_P_key_label_ascii': 'MgD', 'R_R_key_label_ascii': 'AnD', 'R_M_key_label_ascii': 'MdD', 'R_I_key_label_ascii': 'InD',
        'R_P_Alt_key_label_ascii': 'MgD', 'thumbs_rest_label_ascii': 'I pollici riposano sulla BARRA SPAZIATRICE.',
        'general_keyboard_layout_label': '\nLayout Tastiera QWERTY Italiana:', 'full_keyboard_ascii_art': it_qwerty_full_keyboard_ascii,
        'hand_guide_text_intro': "Posizionamento corretto delle mani è fondamentale.\n\nRIGA BASE (QWERTY Italiana):\n  - Sinistra: A(Mignolo), S(Anulare), D(Medio), F(Indice).\n  - Destra: J(Indice), K(Medio), L(Anulare), ò(Mignolo).\n  - Pollici: Sulla Barra Spaziatrice.\n\nFOCUS ESERCIZIO (Riga QWERTY & 'ù'):\n  Sinistra:\n    - Mignolo(MgS):'Q'\n    - Anulare(AnS):'W'\n    - Medio(MdS):'E'\n    - Indice(InS):'R','T'\n\n  Destra:\n    - Indice(InD):'Y','U'\n    - Medio(MdD):'I'\n    - Anulare(AnD):'O'\n    - Mignolo(MgD):'P','ù'\n    (Nota: Per ';' usa Shift + ,)\n\n",
        'hand_guide_text_tips': '\nCONSIGLI GENERALI:\n  - Polsi dritti.\n  - Tocchi leggeri.\n  - Dita sulla riga base.\n  - Precisione prima, velocità poi.',
        'training_prompt_title': 'Modalità Allenamento', 'sentence_to_type_label': 'Digita questa frase:',
        'your_input_label': 'La tua digitazione:', 'timer_label': 'Tempo:',
        'submit_button': 'Invia', 'cancel_button': 'Annulla', 'ok_button': 'OK', 'report_title': 'Report Dattilografia',
        'report_target_sentence': 'Frase Target:', 'report_your_sentence': 'Hai digitato:', 'report_target_length': 'Lunghezza target:',
        'report_typed_length': 'Tua lunghezza:', 'report_errors': 'Errori (testo finale):', 'report_accuracy': 'Accuratezza:',
        'report_total_mistakes_made': 'Errori totali commessi:',
        'report_time_taken': 'Tempo impiegato:', 'report_performance_label': 'Prestazione:',
        'perf_excellent_speed': 'Velocità Eccellente!', 'perf_good_speed': 'Buona Velocità!',
        'perf_learning_pace': 'Continua ad Allenarti!', 'perf_focus_accuracy': "Concentrati sull'Accuratezza!",
        'perf_time_limit_exceeded': 'Tempo Limite Superato!',
        'error_no_sentences': 'Nessuna frase di esempio.',
        'short_sentences': ['Ciao mondo.', 'Come stai oggi?', 'Prova questo testo semplice.'],
        'long_sentences': ['La volpe veloce salta agilmente sopra il cane pigro e poi si riposa.', 'Oggi il sole splende alto nel cielo azzurro e sereno.'],
    },
    'pt': {
        'app_title': 'Treinador de Digitação',
        'welcome_message': 'Bem-vindo ao Treinador de Digitação!',
        'select_language': 'Selecione o Idioma:', 'italian': 'Italiano', 'english': 'Inglês', 'portuguese': 'Português',
        'hand_guide_button': 'Guia de Posicionamento', 'start_training_button': 'Iniciar Treinamento', 'exit_button': 'Sair',
        'sentence_length_label': 'Comprimento da Frase:', 'length_short': 'Curta', 'length_long': 'Longa', 'length_mixed': 'Mista',
        'sentence_source_label': 'Fonte das Frases:', 'source_builtin': 'Internas', 'source_custom': 'De Arquivo',
        'time_limit_settings_label': 'Config. Tempo Limite:',
        'time_auto_1x_label': 'Automático (Aprendizagem)', 'time_auto_2x_label': 'Automático x2',
        'time_auto_3x_label': 'Automático x3', 'time_manual_label': 'Manual', 'manual_time_seconds_label': 'Seg:',
        'invalid_manual_time_popup': 'Tempo inválido.', 'load_custom_file_button': 'Carregar Frases (.txt)', 'download_example_button': 'Baixar Exemplo .txt',
        'file_loaded_popup': 'Frases carregadas: {}', 'file_load_error_popup': 'Erro ao carregar: {}',
        'example_file_saved_popup': 'Exemplo salvo: {}', 'example_file_save_error_popup': 'Erro ao salvar.',
        'hand_guide_title': 'Guia de Posicionamento (ABNT2)', 'key_right_of_p_char_pt': ';',
        'focused_ascii_line1': "Foco: Linha QWERTY & Tecla ';'", 'left_hand_label': 'Mão Esquerda', 'right_hand_label': 'Mão Direita',
        'focused_ascii_line2': '(MnE=Mínimo Esq.)', 'legend_title_ascii': 'Legenda:',
        'pinky_label_ascii': 'Mínimo', 'ring_label_ascii': 'Anelar', 'middle_label_ascii': 'Médio', 'index_label_ascii': 'Indicador',
        'left_label_short_ascii': 'E', 'right_label_short_ascii': 'D',
        'L_P_key_label_ascii': 'MnE', 'L_R_key_label_ascii': 'AnE', 'L_M_key_label_ascii': 'MdE', 'L_I_key_label_ascii': 'InE',
        'R_P_key_label_ascii': 'MnD', 'R_R_key_label_ascii': 'AnD', 'R_M_key_label_ascii': 'MdD', 'R_I_key_label_ascii': 'InD',
        'R_P_Alt_key_label_ascii': 'MnD', 'thumbs_rest_label_ascii': 'Polegares no ESPAÇO.',
        'general_keyboard_layout_label': '\nTeclado ABNT2:', 'full_keyboard_ascii_art': abnt2_full_keyboard_ascii,
        'hand_guide_text_intro': "Posicionamento correto é crucial para ABNT2.\n\nLINHA BASE (ABNT2):\n  - Esquerda: A(Mínimo), S(Anelar), D(Médio), F(Indicador).\n  - Direita: J(Indicador), K(Médio), L(Anelar), Ç(Mínimo).\n  - Polegares: Espaço.\n\nFOCO (Linha QWERTY & ';'):\n  Esquerda:\n    - Mínimo(MnE):'Q'\n    - Anelar(AnE):'W'\n    - Médio(MdE):'E'\n    - Indicador(InE):'R','T'\n\n  Direita:\n    - Indicador(InD):'Y','U'\n    - Médio(MdD):'I'\n    - Anelar(AnD):'O'\n    - Mínimo(MnD):'P',';'\n\n",
        'hand_guide_text_tips': '\nDICAS: Pulsos retos. Toques leves. Dedos na base.\n',
        'training_prompt_title': 'Treinamento', 'sentence_to_type_label': 'Digite:',
        'your_input_label': 'Sua digitação:', 'timer_label': 'Tempo:',
        'submit_button': 'Enviar', 'cancel_button': 'Cancelar', 'ok_button': 'OK', 'report_title': 'Relatório',
        'report_target_sentence': 'Alvo:', 'report_your_sentence': 'Digitado:', 'report_target_length': 'Comp. Alvo:',
        'report_typed_length': 'Seu Comp.:', 'report_errors': 'Erros (texto final):', 'report_accuracy': 'Precisão:',
        'report_total_mistakes_made': 'Total de erros cometidos:',
        'report_time_taken': 'Tempo:', 'report_performance_label': 'Desempenho:',
        'perf_excellent_speed': 'Excelente!', 'perf_good_speed': 'Boa Veloci.!', 'perf_learning_pace': 'Continue!',
        'perf_focus_accuracy': 'Foco Precisão!', 'perf_time_limit_exceeded': 'Esgotado!',
        'error_no_sentences': 'Nenhuma frase.',
        'short_sentences': ['O gato sentou.', 'Olá mundo.', 'Teste 123 rápido.'],
        'long_sentences': ['A raposa veloz pula sobre o cão.', 'O meu amigo foi à praia.'],
    },
}
# Estado global da aplicação
global current_lang, custom_sentences_all, custom_sentences_short, custom_sentences_long
current_lang = 'en'
current_length_pref = 'mixed'
current_source_pref = 'builtin'
current_time_limit_mode = 'auto_1x'
current_manual_time_setting = 60

custom_sentences_all, custom_sentences_short, custom_sentences_long = [], [], []

def get_text(key, lang_code):
    # Busca o texto traduzido, caindo para o inglês quando não houver tradução
    effective_lang_code = lang_code
    if effective_lang_code not in translations:
        # Idioma desconhecido: usa inglês
        effective_lang_code = 'en'
    lang_dict = translations[effective_lang_code]
    value = lang_dict.get(key)
    if value is None and effective_lang_code != 'en':
        value = translations['en'].get(key, f'<{key} NG EN>')
    elif value is None and effective_lang_code == 'en':
        value = f'<{key} NG>'
    return value

def get_formatted_focused_ascii(lang_code):
    key_right_p_char = get_text(f'key_right_of_p_char_{lang_code}', lang_code) if lang_code in ('en', 'it', 'pt') else ';'
    return focused_keys_ascii_template.format(
        line1=get_text('focused_ascii_line1', lang_code),
        left_hand_label=get_text('left_hand_label', lang_code), right_hand_label=get_text('right_hand_label', lang_code),
        row_sep_left=get_text('row_sep_left_short', lang_code), row_sep_right=get_text('row_sep_right_short', lang_code),
        row_sep_left_short=get_text('row_sep_left_short', lang_code), row_sep_right_short=get_text('row_sep_right_short', lang_code),
        key_right_of_p=key_right_p_char,
        L_P_key=get_text('L_P_key_label_ascii', lang_code), L_R_key=get_text('L_R_key_label_ascii', lang_code),
        L_M_key=get_text('L_M_key_label_ascii', lang_code), L_I_key=get_text('L_I_key_label_ascii', lang_code),
        R_P_key=get_text('R_P_key_label_ascii', lang_code), R_R_key=get_text('R_R_key_label_ascii', lang_code),
        R_M_key=get_text('R_M_key_label_ascii', lang_code), R_I_key=get_text('R_I_key_label_ascii', lang_code),
        R_P_Alt_key=get_text('R_P_Alt_key_label_ascii', lang_code),
        line2=get_text('focused_ascii_line2', lang_code), legend_title=get_text('legend_title_ascii', lang_code),
        L_P_key_legend=get_text('L_P_key_label_ascii', lang_code), L_R_key_legend=get_text('L_R_key_label_ascii', lang_code),
        L_M_key_legend=get_text('L_M_key_label_ascii', lang_code), L_I_key_legend=get_text('L_I_key_label_ascii', lang_code),
        R_P_key_legend=get_text('R_P_key_label_ascii', lang_code), R_R_key_legend=get_text('R_R_key_label_ascii', lang_code),
        R_M_key_legend=get_text('R_M_key_label_ascii', lang_code), R_I_key_legend=get_text('R_I_key_label_ascii', lang_code),
        pinky_label=get_text('pinky_label_ascii', lang_code), ring_label=get_text('ring_label_ascii', lang_code),
        middle_label=get_text('middle_label_ascii', lang_code), index_label=get_text('index_label_ascii', lang_code),
        left_label_short=get_text('left_label_short_ascii', lang_code), right_label_short=get_text('right_label_short_ascii', lang_code),
        thumbs_rest_label=get_text('thumbs_rest_label_ascii', lang_code))


def create_main_window(lang_for_window, length_pref_for_window, source_pref_for_window, time_mode_for_window, manual_time_for_window):
    sg.theme('SystemDefault'); font_settings = ('Helvetica', 10)
    app_window_title = get_text('app_title', lang_for_window)
    lang_options_map = {'-ENGLISH-': 'en', '-ITALIAN-': 'it', '-PORTUGUESE-': 'pt'}
    lang_display_name_keys = {'en': 'english', 'it': 'italian', 'pt': 'portuguese'}
    lang_radios = []
    for event_key_suffix, short_code in lang_options_map.items():
        display_name_key = lang_display_name_keys[short_code]
        lang_radios.append(sg.Radio(get_text(display_name_key, lang_for_window), 'LANG',
                                    key=event_key_suffix,
                                    default=(lang_for_window == short_code),
                                    enable_events=True, font=font_settings))
    lang_frame = sg.Frame(get_text('select_language', lang_for_window), [lang_radios], font=font_settings)
    source_radios = [sg.Radio(get_text(f'source_{src_key.lower()}', lang_for_window), 'SOURCE', key=f'-SOURCE_{src_key.upper()}-', default=(source_pref_for_window == src_key.lower()), enable_events=True, font=font_settings) for src_key in ('BUILTIN', 'CUSTOM')]
    source_frame = sg.Frame(get_text('sentence_source_label', lang_for_window), [source_radios], font=font_settings, expand_x=True)
    length_radios = [sg.Radio(get_text(f'length_{len_key.lower()}', lang_for_window), 'LENGTH', key=f'-LENGTH_{len_key.upper()}-', default=(length_pref_for_window == len_key.lower()), enable_events=True, font=font_settings) for len_key in ('SHORT', 'LONG', 'MIXED')]
    length_frame = sg.Frame(get_text('sentence_length_label', lang_for_window), [length_radios], key='-LENGTH_FRAME-', visible=(source_pref_for_window == 'builtin'), font=font_settings, expand_x=True)
    file_ops_column = sg.Column([[sg.Button(get_text('load_custom_file_button', lang_for_window), key='-LOAD_CUSTOM_FILE-', font=font_settings, expand_x=True), sg.Button(get_text('download_example_button', lang_for_window), key='-DOWNLOAD_EXAMPLE-', font=font_settings, expand_x=True)]], justification='center', key='-FILE_OPS_COLUMN-', visible=(source_pref_for_window == 'custom'), expand_x=True)
    time_limit_radios_data = [('auto_1x', 'time_auto_1x_label'), ('auto_2x', 'time_auto_2x_label'), ('auto_3x', 'time_auto_3x_label'), ('manual', 'time_manual_label')]
    time_limit_radios = [sg.Radio(get_text(label_key, lang_for_window), 'TIMEMODE', key=f'-TIME_{mode_key.upper()}-', default=(time_mode_for_window == mode_key), enable_events=True, font=font_settings) for mode_key, label_key in time_limit_radios_data]
    manual_time_input_row = [sg.Text(get_text('manual_time_seconds_label', lang_for_window), font=font_settings), sg.InputText(str(manual_time_for_window), key='-MANUAL_TIME_INPUT-', size=(5, 1), font=font_settings, enable_events=True)]
    manual_time_container = sg.Column([manual_time_input_row], key='-MANUAL_TIME_ROW-', visible=(time_mode_for_window == 'manual'))
    time_settings_frame = sg.Frame(get_text('time_limit_settings_label', lang_for_window), [time_limit_radios, [manual_time_container]], font=font_settings, expand_x=True)
    layout = [
        [sg.Text(app_window_title, font=('Helvetica', 20), justification='center', expand_x=True, key='-APP_TITLE_DISPLAY-')],
        [sg.Text(get_text('welcome_message', lang_for_window), font=('Helvetica', 12), justification='center', expand_x=True)],
        [sg.VPush()], [lang_frame], [source_frame], [length_frame], [file_ops_column], [time_settings_frame], [sg.VPush()],
        [sg.Button(get_text('hand_guide_button', lang_for_window), key='-HAND_GUIDE-', expand_x=True, font=('Helvetica', 12))],
        [sg.Button(get_text('start_training_button', lang_for_window), key='-START_TRAINING-', expand_x=True, font=('Helvetica', 12))],
        [sg.VPush()], [sg.Button(get_text('exit_button', lang_for_window), key='-EXIT-', expand_x=True, font=('Helvetica', 10), button_color=('white', 'firebrick'))]
    ]
    return sg.Window(app_window_title, layout, finalize=True, element_justification='center', size=(600, 720))

def show_hand_positioning_guide():
    # Monta o texto do guia juntando introdução, desenho ASCII e dicas
    guide_content = get_text('hand_guide_text_intro', current_lang) + \
        get_formatted_focused_ascii(current_lang) + \
        get_text('general_keyboard_layout_label', current_lang) + '\n' + \
        get_text('full_keyboard_ascii_art', current_lang) + \
        get_text('hand_guide_text_tips', current_lang)
    layout = [
        [sg.Text(get_text('hand_guide_title', current_lang), font=('Helvetica', 16))],
        [sg.Multiline(guide_content, size=(90, 40), font=('Courier New', 9),
                      disabled=True, expand_x=True, expand_y=True)],
        [sg.Button(get_text('ok_button', current_lang), key='-OK-', font=('Helvetica', 10))]
    ]
    popup_window = sg.Window(get_text('hand_guide_title', current_lang), layout, modal=True, keep_on_top=True, resizable=True, size=(800, 700))
    while True:
        event, _ = popup_window.read()
        if event == sg.WIN_CLOSED or event == '-OK-':
            break
    popup_window.close()

def calculate_accuracy_report(target, typed):
    errors = 0; target_len = len(target); typed_len = len(typed)
    for i in range(max(target_len, typed_len)):
        if i < target_len and i < typed_len:
            if target[i] != typed[i]: errors += 1
        elif i < target_len or i < typed_len: errors += 1
    accuracy = max(0, (target_len - errors) / target_len) * 100 if target_len > 0 else (100 if typed_len == 0 else 0)
    return {'target_sentence': target, 'typed_sentence': typed, 'target_length': target_len,
            'typed_length': typed_len, 'errors': errors, 'accuracy': round(accuracy, 2)}

def load_custom_sentences_from_file(filepath, lang_code):
    global custom_sentences_all, custom_sentences_short, custom_sentences_long
    custom_sentences_all, custom_sentences_short, custom_sentences_long = [], [], []
    try:
        with open(filepath, 'r', encoding='utf-8') as f: lines = f.readlines()
        for line in lines:
            sentence = line.strip()
            if not sentence: continue
            custom_sentences_all.append(sentence)
            if len(sentence) < 60: custom_sentences_short.append(sentence)
            else: custom_sentences_long.append(sentence)
        if custom_sentences_all: sg.popup(get_text('file_loaded_popup', lang_code).format(os.path.basename(filepath)), keep_on_top=True); return True
        else: sg.popup_error(get_text('error_no_sentences', lang_code) + f' (in {os.path.basename(filepath)})', keep_on_top=True); return False
    except Exception as e: sg.popup_error(get_text('file_load_error_popup', lang_code).format(str(e)), keep_on_top=True); return False

def download_example_txt_file(lang_code):
    example_content = get_text('short_sentences', lang_code)[0] + '\n' + get_text('long_sentences', lang_code)[0] + """
Questa è una frase di esempio per file personalizzati.
Esta é uma frase de exemplo para arquivos personalizados."""
    try:
        save_path = sg.popup_get_file(get_text('download_example_button', lang_code), save_as=True, default_extension='.txt',
                                      file_types=(('Text Files', '*.txt'),), no_window=True, keep_on_top=True)
        if save_path:
            with open(save_path, 'w', encoding='utf-8') as f: f.write(example_content)
            sg.popup(get_text('example_file_saved_popup', lang_code).format(save_path), keep_on_top=True)
    except Exception as e: sg.popup_error(get_text('example_file_save_error_popup', lang_code) + f'\n{str(e)}', keep_on_top=True)

def start_training_session(length_preference, source_preference, time_mode, manual_time_val, lang_code):
    # Marca, por posição, se o usuário já errou aquele caractere alguma vez

    error_committed_at_position = []

    chosen_sentences = []
    if source_preference == 'custom':
        if not custom_sentences_all: sg.popup_error(get_text('error_no_sentences', lang_code) + ' (Custom file empty).', keep_on_top=True); return
        chosen_sentences = custom_sentences_all
    else:
        active_short = get_text('short_sentences', lang_code); active_long = get_text('long_sentences', lang_code)
        if length_preference == 'short': chosen_sentences = active_short
        elif length_preference == 'long': chosen_sentences = active_long
        else: chosen_sentences = active_short + active_long
    if not chosen_sentences: sg.popup_error(get_text('error_no_sentences', lang_code), keep_on_top=True); return

    target_sentence = random.choice(chosen_sentences)
    target_len = len(target_sentence)
    error_committed_at_position = [False] * target_len

    base_time = target_len / CPS_LEARNING if CPS_LEARNING > 0 and target_len > 0 else 600.0
    if base_time == 0 and target_len > 0: base_time = 600.0
    max_exercise_time = base_time
    if time_mode == 'auto_2x': max_exercise_time = base_time * 2
    elif time_mode == 'auto_3x': max_exercise_time = base_time * 3
    elif time_mode == 'manual':
        try:
            current_manual_val = float(manual_time_val)
            if current_manual_val <= 0: raise ValueError("Time must be positive.")
            max_exercise_time = current_manual_val
        except ValueError: sg.popup(get_text('invalid_manual_time_popup', lang_code), keep_on_top=True); max_exercise_time = base_time

    time_limit_fast = target_len / CPS_FAST if CPS_FAST > 0 else float('inf')
    time_limit_faster = target_len / CPS_FASTER if CPS_FASTER > 0 else float('inf')
    target_char_elements = [sg.Text(c, key=f'-TARGET_CHAR_{i}-', font=('Courier New', 14, 'bold'), pad=(0, 0), text_color=get_text('pending_char_color', lang_code)) for i, c in enumerate(target_sentence)]
    target_display_container = sg.Column([[*target_char_elements]], scrollable=True, expand_x=True, background_color='lightgrey', pad=(5, 10), key='-TARGET_DISPLAY_CONTAINER-')
    timer_display = sg.Text(f"{get_text('timer_label', lang_code)} 0.0s / {max_exercise_time:.1f}s", key='-TIMER_DISPLAY-', font=('Helvetica', 10))
    training_layout = [[sg.Text(get_text('sentence_to_type_label', lang_code)), sg.Push(), timer_display], [target_display_container], [sg.Text(get_text('your_input_label', lang_code))], [sg.InputText(key='-USER_INPUT-', font=('Courier New', 14), expand_x=True, focus=True, enable_events=True)], [sg.Button(get_text('submit_button', lang_code), key='-SUBMIT-', bind_return_key=True), sg.Button(get_text('cancel_button', lang_code), key='-CANCEL-')]]
    training_window = sg.Window(get_text('training_prompt_title', lang_code), training_layout, modal=True, keep_on_top=True, finalize=True, resizable=True, size=(800, 220))
    start_time = time.time(); user_typed_sentence_final = ""; timed_out = False
    training_window['-USER_INPUT-'].set_focus()

    while True:
        event, values = training_window.read(timeout=100)
        elapsed_time = time.time() - start_time; display_elapsed = min(elapsed_time, max_exercise_time)
        training_window['-TIMER_DISPLAY-'].update(f"{get_text('timer_label', lang_code)} {display_elapsed:.1f}s / {max_exercise_time:.1f}s")
        if not timed_out and elapsed_time >= max_exercise_time: timed_out = True; user_typed_sentence_final = values['-USER_INPUT-']; break
        if event == sg.WIN_CLOSED or event == '-CANCEL-': user_typed_sentence_final = values['-USER_INPUT-']; break
        if event == '-USER_INPUT-':
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
        if event == '-SUBMIT-': user_typed_sentence_final = values['-USER_INPUT-']; break
    training_window.close(); final_elapsed_time = min(elapsed_time, max_exercise_time)

    final_persistent_errors = sum(error_committed_at_position)

    if timed_out: sg.popup_auto_close(get_text('perf_time_limit_exceeded', lang_code), title="Timeout", auto_close_duration=3, grab_anywhere=True, keep_on_top=True)

    if user_typed_sentence_final is not None:
        report_data = calculate_accuracy_report(target_sentence, user_typed_sentence_final); perf_txt = ""; acc_thresh = 85
        if timed_out: perf_txt = get_text('perf_time_limit_exceeded', lang_code)
        elif report_data['accuracy'] < acc_thresh: perf_txt = get_text('perf_focus_accuracy', lang_code)
        elif final_elapsed_time <= time_limit_fast: perf_txt = get_text('perf_excellent_speed', lang_code)
        elif final_elapsed_time <= time_limit_faster: perf_txt = get_text('perf_good_speed', lang_code)
        else: perf_txt = get_text('perf_learning_pace', lang_code)
        perf_color = 'black'
        if get_text('perf_excellent_speed', lang_code) in perf_txt: perf_color = 'darkgreen'
        elif get_text('perf_good_speed', lang_code) in perf_txt: perf_color = 'green'
        elif get_text('perf_focus_accuracy', lang_code) in perf_txt: perf_color = 'darkorange'
        elif get_text('perf_time_limit_exceeded', lang_code) in perf_txt: perf_color = 'red'

        report_layout = [
            [sg.Text(get_text('report_title', lang_code), font=('Helvetica', 16))],
            [sg.Text(f"{get_text('report_target_sentence', lang_code)} {report_data['target_sentence']}", font=('Courier New', 10), size=(70, 2))],
            [sg.Text(f"{get_text('report_your_sentence', lang_code)} {report_data['typed_sentence']}", font=('Courier New', 10), size=(70, 2))],
            [sg.HSeparator()],
            [sg.Text(f"{get_text('report_target_length', lang_code)} {report_data['target_length']}")],
            [sg.Text(f"{get_text('report_typed_length', lang_code)} {report_data['typed_length']}")],
            [sg.Text(f"{get_text('report_errors', lang_code)} {report_data['errors']}", text_color='red' if report_data['errors'] > 0 else 'green')],
            [sg.Text(f"{get_text('report_total_mistakes_made', lang_code)} {final_persistent_errors}", text_color='red' if final_persistent_errors > 0 else 'green')],
            [sg.Text(f"{get_text('report_accuracy', lang_code)} {report_data['accuracy']}%", text_color='green' if report_data['accuracy'] >= 95 else ('darkorange' if report_data['accuracy'] >= acc_thresh else 'red'))],
            [sg.Text(f"{get_text('report_time_taken', lang_code)} {final_elapsed_time:.2f}s")],
            [sg.Text(f"{get_text('report_performance_label', lang_code)} {perf_txt}", font=('Helvetica', 11, 'bold'), text_color=perf_color)],
            [sg.Button(get_text('ok_button', lang_code), key='-OK-')]
        ]
        report_win = sg.Window(get_text('report_title', lang_code), report_layout, modal=True, keep_on_top=True, resizable=True, element_justification='center')
        while True:
            ev, _ = report_win.read()
            if ev == sg.WIN_CLOSED or ev == '-OK-': break
        report_win.close()


if __name__ == '__main__':
    window = create_main_window(current_lang, current_length_pref, current_source_pref, current_time_limit_mode, current_manual_time_setting)

    while True:
        event, values = window.read()

        # Fechamento da janela ou botão Sair
        if event == sg.WIN_CLOSED or event == '-EXIT-':

            break

        lang_to_recreate_for = None
        # Troca de idioma: recria a janela inteira
        if event == '-ENGLISH-': lang_to_recreate_for = 'en'
        elif event == '-ITALIAN-': lang_to_recreate_for = 'it'
        elif event == '-PORTUGUESE-': lang_to_recreate_for = 'pt'

        if lang_to_recreate_for and current_lang != lang_to_recreate_for:

            current_lang = lang_to_recreate_for
            window.close()

            window = create_main_window(current_lang, current_length_pref, current_source_pref, current_time_limit_mode, current_manual_time_setting)

            continue

        # Fonte das frases: internas ou arquivo do usuário


        source_ui_update_needed = False
        if event == '-SOURCE_BUILTIN-' and current_source_pref != 'builtin':
            current_source_pref = 'builtin'; source_ui_update_needed = True
        elif event == '-SOURCE_CUSTOM-' and current_source_pref != 'custom':
            current_source_pref = 'custom'; source_ui_update_needed = True

        if source_ui_update_needed:
            window['-FILE_OPS_COLUMN-'].update(visible=(current_source_pref == 'custom'))
            window['-LENGTH_FRAME-'].update(visible=(current_source_pref == 'builtin'))

        if event == '-LENGTH_SHORT-' and current_length_pref != 'short': current_length_pref = 'short'
        elif event == '-LENGTH_LONG-' and current_length_pref != 'long': current_length_pref = 'long'
        elif event == '-LENGTH_MIXED-' and current_length_pref != 'mixed': current_length_pref = 'mixed'

        time_mode_ui_update_needed = False
        newly_selected_time_mode = current_time_limit_mode
        if event == '-TIME_AUTO_1X-': newly_selected_time_mode = 'auto_1x'
        elif event == '-TIME_AUTO_2X-': newly_selected_time_mode = 'auto_2x'
        elif event == '-TIME_AUTO_3X-': newly_selected_time_mode = 'auto_3x'
        elif event == '-TIME_MANUAL-': newly_selected_time_mode = 'manual'

        if current_time_limit_mode != newly_selected_time_mode:
            current_time_limit_mode = newly_selected_time_mode
            time_mode_ui_update_needed = True

        if event == '-MANUAL_TIME_INPUT-':
            try:
                val = int(values['-MANUAL_TIME_INPUT-'])
                if val > 0: current_manual_time_setting = val
                else: window['-MANUAL_TIME_INPUT-'].update(str(current_manual_time_setting))
            except ValueError:
                if values['-MANUAL_TIME_INPUT-'] == '': pass
                else: window['-MANUAL_TIME_INPUT-'].update(str(current_manual_time_setting))

        if time_mode_ui_update_needed:
            window['-MANUAL_TIME_ROW-'].update(visible=(current_time_limit_mode == 'manual'))
            if current_time_limit_mode == 'manual':
                window['-MANUAL_TIME_INPUT-'].update(str(current_manual_time_setting))
                window['-MANUAL_TIME_INPUT-'].set_focus()

        if event == '-LOAD_CUSTOM_FILE-':
            filepath = sg.popup_get_file(get_text('load_custom_file_button', current_lang), title='Select Text File', file_types=(('Text Files', '*.txt'),), keep_on_top=True)
            if filepath and load_custom_sentences_from_file(filepath, current_lang):
                if current_source_pref != 'custom':
                    current_source_pref = 'custom'; window['-SOURCE_CUSTOM-'].update(value=True)
                    window['-FILE_OPS_COLUMN-'].update(visible=True); window['-LENGTH_FRAME-'].update(visible=False)
        elif event == '-DOWNLOAD_EXAMPLE-': download_example_txt_file(current_lang)
        elif event == '-HAND_GUIDE-': show_hand_positioning_guide()
        elif event == '-START_TRAINING-':
            manual_time_to_pass = current_manual_time_setting
            if current_time_limit_mode == 'manual':
                try:
                    manual_input_val = values['-MANUAL_TIME_INPUT-']
                    if not manual_input_val.strip(): manual_time_to_pass = current_manual_time_setting
                    else: manual_time_to_pass = int(manual_input_val)
                    if manual_time_to_pass <= 0: sg.popup_error(get_text('invalid_manual_time_popup', current_lang), keep_on_top=True); continue
                    current_manual_time_setting = manual_time_to_pass
                except ValueError: sg.popup_error(get_text('invalid_manual_time_popup', current_lang), keep_on_top=True); continue

            start_training_session(current_length_pref, current_source_pref, current_time_limit_mode, manual_time_to_pass, current_lang)

    window.close()
