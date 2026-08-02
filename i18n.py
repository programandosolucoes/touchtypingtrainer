"""Todo o texto visível do aplicativo, nos três idiomas, e o acesso a ele.

O dicionário `translations` é a única fonte de texto da interface: rótulos, botões,
mensagens de erro, cores dos caracteres durante o exercício e até as frases de treino
embutidas. Trocar de idioma em tempo de execução é só recriar a janela lendo outra
chave deste dicionário — por isso nenhum texto fica escrito direto na tela.

Chaves terminadas em `_ascii` alimentam o desenho do teclado; `short_sentences` e
`long_sentences` são as frases de treino que acompanham o programa (a IA acrescenta
outras em tempo de execução, ver `ai_exercises.py`).
"""
from keyboards import (abnt2_full_keyboard_ascii, focused_keys_ascii_template,
                       it_qwerty_full_keyboard_ascii, us_qwerty_full_keyboard_ascii)

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
        'source_ai': 'AI Generated', 'ai_generate_button': 'Generate Exercises (AI)',
        'ai_generating_popup': 'Generating exercises with AI...', 'ai_generated_popup': '{} new sentences generated!',
        'ai_error_popup': 'Could not reach the AI: {}', 'ai_status_available': 'AI sentences ready: {}',
        'ai_no_sentences': 'No AI sentences yet - click Generate.',
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
        'source_ai': 'Generate con IA', 'ai_generate_button': 'Genera Esercizi (IA)',
        'ai_generating_popup': 'Generazione esercizi con IA...', 'ai_generated_popup': '{} nuove frasi generate!',
        'ai_error_popup': 'IA non raggiungibile: {}', 'ai_status_available': 'Frasi IA pronte: {}',
        'ai_no_sentences': 'Nessuna frase IA - premi Genera.',
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
        'source_ai': 'Gerado por IA', 'ai_generate_button': 'Gerar Exercícios (IA)',
        'ai_generating_popup': 'Gerando exercícios com IA...', 'ai_generated_popup': '{} novas frases geradas!',
        'ai_error_popup': 'Não foi possível falar com a IA: {}', 'ai_status_available': 'Frases da IA prontas: {}',
        'ai_no_sentences': 'Nenhuma frase da IA - clique em Gerar.',
        'short_sentences': ['O gato sentou.', 'Olá mundo.', 'Teste 123 rápido.'],
        'long_sentences': ['A raposa veloz pula sobre o cão.', 'O meu amigo foi à praia.'],
    },
}


def get_text(key, lang_code):
    """Devolve o texto da chave no idioma pedido, com dois níveis de proteção.

    1. Idioma desconhecido cai para inglês;
    2. chave faltando naquele idioma cai para o inglês, e se faltar também em inglês
       devolve um marcador visível (`<chave NG>`) em vez de quebrar a janela.

    Esse marcador é proposital: uma tradução esquecida aparece na tela durante o teste
    em vez de derrubar o aplicativo na frente do cliente.
    """
    effective_lang_code = lang_code
    if effective_lang_code not in translations:
        effective_lang_code = 'en'
    lang_dict = translations[effective_lang_code]
    value = lang_dict.get(key)
    if value is None and effective_lang_code != 'en':
        value = translations['en'].get(key, f'<{key} NG EN>')
    elif value is None and effective_lang_code == 'en':
        value = f'<{key} NG>'
    return value


def get_formatted_focused_ascii(lang_code):
    """Monta o desenho reduzido do teclado com os nomes dos dedos no idioma ativo.

    A tecla à direita do P muda por layout (';' no US e no ABNT2, 'ù' no italiano),
    então ela vem do dicionário e não do desenho.
    """
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
