"""TouchTypingTrainer — treinador de digitação com correção caractere a caractere.

Este módulo é hoje a **camada de dados e regras** do programa: de onde vêm as
frases (internas, arquivo do usuário, IA), como o exercício livre é sorteado e
como o resultado dele é gravado. Ele não desenha mais nada.

Quem desenha é o `aplicativo.py`: uma janela só, de tamanho fixo, com as telas
trocando dentro da mesma área (`telas.py`). Janela nova a cada etapa obrigava o
aluno a tirar as mãos da linha-base para achar o botão — o hábito que o programa
existe para desfazer.

O único momento em que a janela é reconstruída é a troca de idioma: os rótulos
mudam de largura e frame do Tk não se redimensiona depois de criado.

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

def preparar_treino_livre(length_preference, source_preference, time_mode,
                          manual_time_val, lang_code):
    """Sorteia a frase e calcula o limite de tempo. Devolve (frase, limite) ou None.

    O exercício em si virou tela (`telas.TelaLivre`): esta função só decide o
    QUE treinar, e quem mostra é a janela única.
    """
    frases, erro = escolher_frases(length_preference, source_preference, lang_code)
    if erro:
        sg.popup_error(erro, keep_on_top=True)
        return None

    frase = random.choice(frases)
    comprimento = len(frase)
    # Tempo-base: quanto levaria digitando no ritmo de aprendizado. O 600.0 é a
    # rede de segurança para frase vazia, para não dividir por zero nem dar um
    # limite instantâneo.
    base = comprimento / CPS_LEARNING if CPS_LEARNING > 0 and comprimento > 0 else 600.0
    limite = base
    if time_mode == 'auto_2x':
        limite = base * 2
    elif time_mode == 'auto_3x':
        limite = base * 3
    elif time_mode == 'manual':
        try:
            valor = float(manual_time_val)
            if valor <= 0:
                raise ValueError
            limite = valor
        except (TypeError, ValueError):
            # Valor inválido não cancela o treino: avisa e cai no tempo automático.
            sg.popup(get_text('invalid_manual_time_popup', lang_code), keep_on_top=True)
    return frase, limite


def gravar_treino_livre(alvo, duracao, relatorio, tropecos, lang_code, arquivo=None):
    """Põe o exercício livre no histórico, com modo 'livre'.

    Não conta para a progressão do currículo, mas conta para a evolução ao longo
    do tempo — é o mesmo arquivo que a tela de progresso lê.

    `arquivo` é obrigatório na prática: quem chama tem o caminho da sessão. O
    padrão existe só para uso solto e **não deve** ser usado pela interface —
    sem ele, um teste gravaria no histórico de verdade do usuário.
    """
    historico.gravar({
        'quando': datetime.now().astimezone().isoformat(timespec='seconds'),
        'modo': 'livre',
        'nivel': None,
        'idioma': lang_code,
        'layout': layouts.LAYOUT_POR_IDIOMA[lang_code],
        'alvo': alvo,
        'duracao_s': round(duracao, 2),
        'wpm_bruto': round(metricas.wpm(relatorio['typed_length'], duracao), 2),
        'wpm_liquido': round(metricas.wpm_liquido(
            relatorio['typed_length'], duracao, relatorio['errors']), 2),
        'tropecos': tropecos,
        'total_teclas': relatorio['target_length'],
        # O treino livre lê o campo inteiro a cada tecla, não batida por batida:
        # não há intervalo por tecla para medir ritmo.
        'regularidade': None,
        'aprovado': None,
        'teclas': {},
    }, arquivo or caminho_do_historico())


# ---------------------------------------------------------------------------
# Laço principal da janela de preferências
# ---------------------------------------------------------------------------

def main():
    """Abre o programa e o mantém aberto até o usuário sair.

    O laço existe por um motivo só: trocar de idioma reconstrói a janela, porque
    os rótulos mudam de largura e frame do Tk não se redimensiona depois de
    criado. Fora isso, tudo acontece dentro da mesma janela.
    """
    global current_lang
    carregar_frases_ia(current_lang)
    while True:
        idioma_pedido = aplicativo.rodar_aplicativo(current_lang, caminho_do_historico())
        if not idioma_pedido:
            break
        current_lang = idioma_pedido


if __name__ == '__main__':
    main()
