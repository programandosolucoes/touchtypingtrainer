# Geração de exercícios por IA — como funciona e o que descobrimos

O aplicativo gera frases de treino novas chamando um modelo de linguagem. Este documento
registra qual serviço é usado, por que ele foi escolhido, as armadilhas que custaram tempo
e o que fazer se o serviço sair do ar.

## O serviço: OpenCode Zen, sem credencial

```
POST https://opencode.ai/zen/v1/chat/completions
Content-Type: application/json
User-Agent: TouchTypingTrainer/2.0        <- obrigatório, ver armadilha nº 1
```

Formato compatível com a API da OpenAI (`model`, `messages`, `max_tokens`;
resposta em `choices[0].message.content`).

Os modelos com sufixo `-free` respondem **sem nenhum cabeçalho de autorização**. Isso é o
que torna a funcionalidade viável num programa distribuído a clientes:

- não há chave de API dentro do executável — nada para configurar e nada para extrair dele
  (e este projeto é a prova de que dá para extrair: veja `docs/RECUPERACAO.md`);
- o uso do cliente não consome cota de ninguém;
- a resposta traz `"cost": "0"`.

Modelos verificados funcionando anonimamente (a lista em `ai_exercises.MODELOS` é tentada
em ordem, caindo para o próximo quando um falha):

| modelo | observação |
|---|---|
| `deepseek-v4-flash-free` | primeira escolha; melhor qualidade em pt/it |
| `nemotron-3-ultra-free` | reserva |
| `ling-3.0-flash-free` | reserva |
| `mimo-v2.5-free` | reserva |
| `laguna-s-2.1-free` | reserva |

A lista completa de modelos está em `GET https://opencode.ai/zen/v1/models` (60 modelos no
momento da escrita; os sem sufixo `-free` exigem credencial e são cobrados — **não use**).

## Armadilha nº 1: HTTP 403 é o User-Agent, não limite de uso

O `urllib` da biblioteca padrão manda `User-Agent: Python-urllib/3.x`, e a API recusa esse
cabeçalho com **403 Forbidden**. Qualquer User-Agent identificável passa:

| User-Agent | resposta |
|---|---|
| `Python-urllib/3.14` (padrão) | HTTP 403 |
| `TouchTypingTrainer/2.0` | 200 OK |
| `curl/8.5.0` | 200 OK |
| `Mozilla/5.0` | 200 OK |

Isso custou tempo real: 71 erros 403 seguidos foram interpretados como limite por IP, e o
gerador chegou a ser reescrito com 25 segundos de espera entre chamadas e backoff
progressivo — tudo desnecessário. O sintoma que denunciou o engano foi `curl` respondendo
200 no mesmo instante em que o script Python tomava 403.

**Regra geral: em cliente HTTP próprio, sempre defina User-Agent.** Um 403 que não
distingue "sem permissão" de "cliente recusado" é indistinguível de rate limit sem esse
teste cruzado.

## Armadilha nº 2: o modelo escreve o raciocínio dentro da resposta

Modelos com cadeia de pensamento têm campo `reasoning_content` separado, mas nem sempre o
usam. Em parte das respostas, o `content` veio assim:

```
We need 3 short sentences (25-55 chars) and 3 long sentences (62-110 chars). Let's craft.
First, short sentences (25-55 chars). Count characters.
We'll count manually.
Sentence 5: "Quando os avós contam lendas antigas, os netos aprendem valores."
```

Um parser linha a linha aceita tudo isso como "frase de treino", e o usuário acabaria
digitando *"We'll count manually."* como exercício. A correção tem três camadas em
`ai_exercises.py`:

1. **pedir JSON** — o prompt exige um array de strings, e o parser recorta do primeiro `[`
   ao último `]`, o que sobrevive a texto solto em volta;
2. **modo linha a linha como reserva**, para quando o modelo ignora o formato;
3. **validação de cada frase** (`_validar`): faixa de comprimento, ausência de caracteres
   de markdown, ausência de vocabulário de raciocínio (`chars`, `sentences`, `count`,
   `let's`…), coerência de idioma (frase em português não pode conter `the`/`we`/`need`;
   frase em inglês não pode ter acento) e formato mínimo de oração (tem espaço, não termina
   em `:`).

**Nunca confie no formato da resposta de um LLM.** Valide o conteúdo, não só o envelope.

## Armadilha nº 3: chamada de rede na thread da interface congela a janela

(Free)SimpleGUI é single-thread. Uma chamada que leva 10 a 40 segundos trava a janela
inteira — sem repintar, sem responder ao mouse, com o sistema marcando "não está
respondendo". A geração roda em `threading.Thread` e devolve o resultado por
`window.write_event_value('-AI_DONE-', ...)`, que o laço de eventos trata como qualquer
outro evento. O botão fica desabilitado enquanto a geração corre, para não empilhar
requisições.

## Onde as frases ficam

| origem | arquivo | quando é usada |
|---|---|---|
| banco embutido | `sentences_ai.py` (209 frases) | sempre; funciona sem internet e já na 1ª execução |
| geradas nesta máquina | `~/.touchtypingtrainer/frases_ia.json` | acumuladas a cada clique em "Gerar" |

O cache fica na pasta do usuário, e não ao lado do `.exe`, porque o executável pode estar
em local somente-leitura (Arquivos de Programas, pendrive). Falha ao gravar o cache é
ignorada de propósito: perder o cache não pode impedir alguém de treinar.

## Regenerando o banco embutido

```bash
python tools/gerar_frases.py       # chama a IA por tema e idioma, grava tools/frases_ia.json
python tools/atualizar_banco.py    # converte o JSON em sentences_ai.py
```

O gerador usa a credencial local do OpenCode (`~/.local/share/opencode/auth.json`) **se
existir** — apenas porque faz dezenas de chamadas seguidas, e os modelos `-free` custam
zero também nesse modo. O aplicativo distribuído continua anônimo; nenhuma chave entra no
repositório ou no binário.

Banco atual: 209 frases (pt 71, en 69, it 69), curtas (25–55 caracteres) e longas
(62–110), geradas sobre 14 temas para variar vocabulário.

## Alternativas pesquisadas (caso o Zen mude)

| serviço | situação em 02/08/2026 |
|---|---|
| **Pollinations** (`text.pollinations.ai`) | responde anonimamente só com `?referrer=<app>`; sem ele, HTTP 402. Ficou instável nos testes |
| **LLM7** (`api.llm7.io`) | anônimo, mas os modelos testados voltaram `model_unavailable` |
| **OVHcloud AI Endpoints** | anônimo documentado, ~2 requisições/minuto por IP, compatível com OpenAI |
| **Groq / OpenRouter / Gemini** | têm camada gratuita, mas **exigem chave** — descartados: chave em binário distribuído é chave vazada |

Se for preciso trocar, o ponto de mudança é pequeno: `ENDPOINT` e `MODELOS` no topo de
`ai_exercises.py`, mais o formato de leitura em `_requisitar` se o serviço não for
compatível com a API da OpenAI. O parser e a validação continuam valendo.

## Testando a API rapidamente

```bash
curl -s https://opencode.ai/zen/v1/chat/completions \
  -H "Content-Type: application/json" -H "User-Agent: teste/1.0" \
  -d '{"model":"deepseek-v4-flash-free","messages":[{"role":"user","content":"Responda apenas: OK"}],"max_tokens":300}'
```

`max_tokens` baixo demais faz o modelo gastar a cota toda no raciocínio e devolver
`content` vazio — use pelo menos 300 para um teste, 1200 para geração de verdade.
