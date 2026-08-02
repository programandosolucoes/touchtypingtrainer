"""Geração de exercícios novos por IA, em tempo de execução.

Usa a API pública do OpenCode Zen nos modelos com sufixo `-free`, que respondem
**sem nenhuma credencial** — não há chave embutida no binário, nada para o cliente
configurar e nada que possa ser extraído do executável. Se a máquina estiver sem
internet (ou a API fora do ar), o aplicativo simplesmente continua com o banco de
frases offline; a geração por IA é um extra, nunca um requisito.

Só usa a biblioteca padrão do Python (urllib), de propósito: assim o PyInstaller não
precisa empacotar `requests`/`certifi` e o executável não engorda.
"""
import json
import os
import re
import ssl
import threading
import urllib.error
import urllib.request

ENDPOINT = 'https://opencode.ai/zen/v1/chat/completions'

# Modelos gratuitos e anônimos, tentados nesta ordem. Se um estiver indisponível
# ou lento, o próximo assume — por isso a lista, e não um modelo único.
MODELOS = [
    'deepseek-v4-flash-free',
    'nemotron-3-ultra-free',
    'ling-3.0-flash-free',
    'mimo-v2.5-free',
    'laguna-s-2.1-free',
]

# Nome do idioma como ele deve aparecer no pedido feito ao modelo
NOMES_IDIOMA = {'pt': 'português do Brasil', 'en': 'inglês', 'it': 'italiano'}

# Corte de comprimento que o aplicativo usa para separar frase curta de longa
LIMITE_CURTA = 60
COMPRIMENTO_MINIMO = 20
COMPRIMENTO_MAXIMO = 110

TEMAS = [
    'cotidiano e trabalho', 'natureza e viagem', 'tecnologia', 'comida', 'esporte',
    'estudo e leitura', 'música', 'cidade e transporte', 'família', 'clima',
]


def _caminho_cache():
    """Arquivo onde as frases geradas ficam guardadas entre execuções.

    Fica na pasta do usuário (não ao lado do .exe) porque o executável pode estar
    em local somente-leitura, como Arquivos de Programas ou um pendrive.
    """
    base = os.path.join(os.path.expanduser('~'), '.touchtypingtrainer')
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, 'frases_ia.json')


def carregar_cache():
    """Devolve {idioma: [frases]} do cache em disco, ou {} se não houver/estiver corrompido."""
    try:
        with open(_caminho_cache(), 'r', encoding='utf-8') as fh:
            dados = json.load(fh)
        return dados if isinstance(dados, dict) else {}
    except (OSError, ValueError):
        return {}


def salvar_cache(cache):
    """Grava o cache de frases. Falha de escrita é ignorada de propósito: perder o
    cache não pode impedir o usuário de treinar."""
    try:
        with open(_caminho_cache(), 'w', encoding='utf-8') as fh:
            json.dump(cache, fh, ensure_ascii=False, indent=2)
    except OSError:
        pass


# Palavras que denunciam raciocínio do modelo vazando na resposta ("We need 3 short
# sentences (25-55 chars)..."). Modelos com cadeia de pensamento às vezes escrevem isso
# no corpo da resposta, e não no campo separado de reasoning.
_RUIDO = re.compile(r'\b(chars?|characters?|sentences?|count|let\'s|we need|we\'ll|i\'ll|'
                    r'within range|now long|now short|frasi? \d|frases? \d|prompt|json)\b', re.I)
# Palavras funcionais do inglês, usadas para descartar raciocínio em respostas que
# deveriam estar em português ou italiano.
_INGLES = re.compile(r'\b(the|we|need|each|within|should|must|here are|following)\b', re.I)


def _validar(frase, idioma):
    """Diz se uma linha é uma frase de exercício aceitável."""
    if not COMPRIMENTO_MINIMO <= len(frase) <= COMPRIMENTO_MAXIMO:
        return False
    if any(c in frase for c in '{}<>[]|#*_`'):     # sobra de markdown ou código
        return False
    if _RUIDO.search(frase):                        # raciocínio do modelo
        return False
    if idioma == 'en':
        if re.search(r'[àáâãäçèéêëìíîïòóôõöùúûü]', frase, re.I):
            return False                            # inglês não deve vir acentuado
    elif _INGLES.search(frase):
        return False                                # resposta saiu no idioma errado
    # Uma frase de treino tem espaço e termina em pontuação ou letra, nunca em ':'
    if ' ' not in frase or frase.rstrip().endswith(':'):
        return False
    return True


def _limpar_resposta(texto, idioma):
    """Transforma a resposta bruta do modelo em uma lista de frases utilizáveis.

    Primeiro tenta ler um array JSON (é o formato pedido no prompt, e o mais confiável).
    Se o modelo ignorar o formato, cai para leitura linha a linha com filtros — nunca se
    confia no que voltou, porque frase inválida vira exercício quebrado na cara do usuário.
    """
    texto = texto or ''
    inicio, fim = texto.find('['), texto.rfind(']')
    if 0 <= inicio < fim:
        try:
            itens = json.loads(texto[inicio:fim + 1])
            frases = [str(i).strip() for i in itens if isinstance(i, str)]
            validas = [f for f in frases if _validar(f, idioma)]
            if validas:
                return validas
        except ValueError:
            pass        # JSON malformado: segue para o modo linha a linha

    frases = []
    for linha in texto.splitlines():
        f = linha.strip()
        f = re.sub(r'^[\-\*•]\s*', '', f)        # marcador de lista
        f = re.sub(r'^\d+[\.\)]\s*', '', f)      # "1." / "1)"
        f = f.strip().strip('"').strip("'").strip().rstrip(',')
        if _validar(f, idioma):
            frases.append(f)
    return frases


def montar_prompt(nome_idioma, assunto, quantidade):
    """Texto do pedido enviado ao modelo.

    Pede JSON porque é o formato que sobrevive melhor a modelos que gostam de comentar
    o próprio trabalho: mesmo que venha texto em volta, o array continua extraível.
    """
    return (f'Gere {quantidade} frases em {nome_idioma} para treino de digitação, sobre '
            f'"{assunto}". Metade com 25 a 55 caracteres e metade com 62 a 110 caracteres. '
            f'Cada frase deve ser uma oração completa, com pontuação e acentuação corretas '
            f'do idioma, sem aspas internas. Não repita frases. '
            f'Responda APENAS com um array JSON de strings, sem nenhum texto antes ou depois.')


def _requisitar(modelo, prompt, timeout):
    """Uma chamada HTTP à API. Devolve o texto da resposta ou levanta a exceção de rede."""
    corpo = json.dumps({
        'model': modelo,
        'messages': [
            {'role': 'system', 'content': 'Você gera frases para treino de digitação. '
                                          'Responda SOMENTE com as frases, uma por linha, '
                                          'sem numeração, sem marcadores e sem aspas.'},
            {'role': 'user', 'content': prompt},
        ],
        'max_tokens': 1200,
    }).encode('utf-8')
    req = urllib.request.Request(ENDPOINT, data=corpo,
                                 headers={'Content-Type': 'application/json',
                                          'User-Agent': 'TouchTypingTrainer/2.0'})
    # Alguns Windows sem certificados atualizados quebram na validação TLS; nesse caso
    # a chamada falha e o app cai no banco offline, que é o comportamento desejado.
    contexto = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=timeout, context=contexto) as resp:
        dados = json.load(resp)
    return dados['choices'][0]['message'].get('content') or ''


def gerar_frases(idioma, quantidade=12, tema=None, timeout=60):
    """Pede frases novas à IA no idioma indicado.

    Devolve (frases, erro): em caso de sucesso `erro` é None; se todos os modelos
    falharem, devolve ([], mensagem) para a interface mostrar o motivo.
    """
    nome = NOMES_IDIOMA.get(idioma, NOMES_IDIOMA['en'])
    assunto = tema or TEMAS[hash(idioma) % len(TEMAS)]
    prompt = montar_prompt(nome, assunto, quantidade)
    ultimo_erro = 'sem resposta'
    for modelo in MODELOS:
        try:
            frases = _limpar_resposta(_requisitar(modelo, prompt, timeout), idioma)
            if frases:
                return frases, None
            ultimo_erro = f'{modelo}: resposta vazia'
        except (urllib.error.URLError, TimeoutError, OSError, ValueError, KeyError) as e:
            ultimo_erro = f'{modelo}: {e}'
    return [], ultimo_erro


def gerar_em_thread(idioma, ao_terminar, quantidade=12):
    """Roda `gerar_frases` fora da thread da interface.

    A GUI do (Free)SimpleGUI é single-thread: uma chamada de rede síncrona congela a
    janela por dezenas de segundos. Por isso a geração roda em thread e o resultado
    volta pelo callback `ao_terminar(frases, erro)`, que a janela transforma em evento.
    """
    def alvo():
        frases, erro = gerar_frases(idioma, quantidade)
        ao_terminar(frases, erro)

    t = threading.Thread(target=alvo, daemon=True)
    t.start()
    return t


def separar_por_tamanho(frases):
    """Divide as frases entre curtas e longas usando o mesmo corte do resto do app."""
    curtas = [f for f in frases if len(f) < LIMITE_CURTA]
    longas = [f for f in frases if len(f) >= LIMITE_CURTA]
    return curtas, longas
