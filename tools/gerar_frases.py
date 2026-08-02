"""Gera o banco de frases embutido (`sentences_ai.py`) chamando a mesma API do aplicativo.

Roda uma vez, fora do aplicativo: grava `frases_ia.json`, que depois vira módulo Python
pelo `atualizar_banco.py`. O aplicativo não depende deste script.

Reusa o cliente e o filtro de `ai_exercises.py` de propósito: se o parser de resposta
mudar lá, o banco passa a ser gerado com o mesmo critério, sem duas regras divergentes.

Diferença em relação ao aplicativo: aqui usamos a credencial do OpenCode instalada nesta
máquina, se houver. São dezenas de chamadas seguidas — mais do que o acesso anônimo
tolera. Os modelos `-free` custam zero nos dois modos. O binário distribuído continua
sem chave nenhuma.
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ai_exercises  # noqa: E402  (precisa do sys.path ajustado acima)

IDIOMAS = {'pt': 'português do Brasil', 'en': 'inglês', 'it': 'italiano'}
TEMAS = [
    'cotidiano e rotina de trabalho', 'natureza e viagens', 'tecnologia e computadores',
    'comida e culinária', 'esporte e saúde', 'estudo e leitura', 'música e arte',
    'cidade e transporte', 'família e amigos', 'clima e estações do ano',
    'história e curiosidades', 'animais', 'casa e organização', 'compras e dinheiro',
]
META_POR_IDIOMA = 60      # frases por idioma (curtas + longas)
INTERVALO = 3             # segundos entre chamadas, para não bater no limite da API


def credencial_local():
    """Chave do OpenCode instalada nesta máquina, se existir (só para este script)."""
    caminho = os.path.expanduser('~/.local/share/opencode/auth.json')
    try:
        with open(caminho, encoding='utf-8') as fh:
            return json.load(fh)['opencode']['key']
    except (OSError, KeyError, ValueError):
        return None


def main():
    chave = credencial_local()
    print('credencial local:', 'encontrada' if chave else 'ausente (usando acesso anônimo)')
    if chave:
        # injeta o cabeçalho de autorização no cliente compartilhado
        original = ai_exercises._requisitar

        def com_chave(modelo, prompt, timeout):
            import urllib.request
            corpo = json.dumps({
                'model': modelo,
                'messages': [
                    {'role': 'system', 'content': 'Você gera frases para treino de digitação.'},
                    {'role': 'user', 'content': prompt},
                ],
                'max_tokens': 1500,
            }).encode('utf-8')
            req = urllib.request.Request(
                ai_exercises.ENDPOINT, data=corpo,
                headers={'Content-Type': 'application/json',
                         'User-Agent': 'TouchTypingTrainer-gerador/1.0',
                         'Authorization': f'Bearer {chave}'})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                dados = json.load(resp)
            return dados['choices'][0]['message'].get('content') or ''

        ai_exercises._requisitar = com_chave

    banco = {lang: {'short': [], 'long': []} for lang in IDIOMAS}
    destino = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frases_ia.json')
    for lang in IDIOMAS:
        vistas = set()
        for tema in TEMAS:
            total = len(banco[lang]['short']) + len(banco[lang]['long'])
            if total >= META_POR_IDIOMA:
                break
            frases, erro = ai_exercises.gerar_frases(lang, quantidade=14, tema=tema, timeout=120)
            if erro:
                print(f'{lang} [{tema}]: falhou -> {erro}', flush=True)
                time.sleep(10)
                continue
            novas = [f for f in frases if f.lower() not in vistas]
            for f in novas:
                vistas.add(f.lower())
            curtas, longas = ai_exercises.separar_por_tamanho(novas)
            banco[lang]['short'].extend(curtas)
            banco[lang]['long'].extend(longas)
            print(f'{lang} [{tema}]: +{len(curtas)} curtas, +{len(longas)} longas '
                  f'(total {len(banco[lang]["short"]) + len(banco[lang]["long"])})', flush=True)
            # grava a cada rodada: se a API cortar no meio, o que já veio fica salvo
            with open(destino, 'w', encoding='utf-8') as fh:
                json.dump(banco, fh, ensure_ascii=False, indent=2)
            time.sleep(INTERVALO)
    print('\nresumo:', {l: {t: len(v) for t, v in d.items()} for l, d in banco.items()})


if __name__ == '__main__':
    main()
