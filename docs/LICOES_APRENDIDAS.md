# Lições aprendidas

Armadilhas encontradas durante a recuperação do código e a implementação da geração por
IA. Cada item é algo que custou tempo e que teria sido invisível na leitura do código.

## Recuperação do executável

**`pycdc` não descompila bytecode do Python 3.13.** A tabela de opcodes dele para 3.13
está correta, mas o alinhamento das entradas `CACHE` não — ele desanda no primeiro
dicionário grande e produziu 15 linhas de um arquivo de 507. Perder tempo tentando
consertar o descompilador seria pior do que o caminho que funcionou: extrair com
`pyinstxtractor-ng`, instalar o Python 3.13 real (`uv python install 3.13`) e reescrever
o fonte a partir do `dis` nativo, que é fiel por definição.

**Números de linha são um mapa de formatação.** O bytecode guarda a linha de cada
instrução. Isso permitiu reconstruir não só o código, mas o *layout* original — inclusive
descobrir quais pares chave/valor de um dicionário estavam na mesma linha. Foi assim que
a reconstrução fechou em 507 linhas, exatamente como o original.

**Um `if` e um `elif` produzem bytecode diferente.** A única divergência da primeira
tentativa foi um `elif` que eu havia escrito como `if`: o compilador duplica o `return`
no fim do primeiro ramo quando é `elif`, e essa instrução extra denunciou a diferença.

## API de IA anônima (OpenCode Zen)

**HTTP 403 não era limite de uso: era o User-Agent.** O `urllib` manda
`Python-urllib/3.x` por padrão e a API recusa com 403. Qualquer User-Agent identificável
passa — `curl/8.5.0`, `Mozilla/5.0` ou o do próprio app. Chegamos a interpretar 71 erros
403 como rate limit e a espaçar chamadas em 25 segundos à toa; o problema era um
cabeçalho. **Sempre defina User-Agent em cliente HTTP próprio.**

**Modelos com cadeia de pensamento vazam o raciocínio no corpo da resposta.** O
`deepseek-v4-flash-free` tem campo `reasoning_content` separado, mas em parte das
respostas escreveu *"We need 3 short sentences (25-55 chars). Let's craft."* dentro do
`content`, uma linha por vez — e o parser linha-a-linha aceitou tudo como "frase de
treino". A correção foi pedir um array JSON e extraí-lo do meio do texto, com o modo
linha-a-linha como reserva e um filtro que descarta ruído de raciocínio e resposta no
idioma errado. **Nunca confie no formato da resposta de um LLM: valide o conteúdo.**

**Geração ao vivo não pode rodar na thread da interface.** (Free)SimpleGUI é
single-thread; uma chamada de rede de 30 segundos congela a janela inteira. A geração
roda em `threading.Thread` e devolve o resultado por `window.write_event_value`, que o
laço de eventos trata como qualquer outro evento.

## Empacotamento

**Python 3.14 do sistema não tem tkinter aqui.** O ambiente que reproduz o original é o
Python 3.13 do `uv`, que já traz tkinter — e, por coincidência útil, é a mesma série do
Python usado no build original (3.13.3).

**PyInstaller não faz compilação cruzada.** Gerar `.exe` a partir do Linux exige um
Python de Windows rodando sob Wine; não existe flag de "target platform".
