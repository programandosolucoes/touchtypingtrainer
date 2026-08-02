# Lições aprendidas

Índice das armadilhas que custaram tempo neste projeto, com o essencial de cada uma e o
documento onde ela está detalhada. Se você voltar aqui daqui a um ano, comece por esta
lista.

## Bytecode e recuperação de código

**`pycdc` não descompila Python 3.13.** A tabela de opcodes dele está certa, mas o
alinhamento das entradas `CACHE` não — para no primeiro dicionário grande e entrega 15
linhas de um arquivo de 507. `uncompyle6` e `decompyle3` param no 3.8. O caminho que
funciona é `dis` do Python real + reescrita + verificação automatizada.
→ `RECUPERACAO.md`

**O bytecode guarda o número da linha de cada instrução.** Isso reconstrói a *formatação*
do arquivo, não só o código — e serve como verificação independente de que a estrutura foi
entendida. Foi o que permitiu fechar em 507 linhas idênticas.
→ `RECUPERACAO.md`

**`if` e `elif` geram bytecode diferente.** Com `elif`, o compilador duplica o `return` no
fim do primeiro ramo. Foi a única divergência da primeira tentativa de reconstrução, e só
apareceu porque havia comparação instrução a instrução.
→ `RECUPERACAO.md`

**Comparação automatizada > leitura atenta.** `tools/comparar_bytecode.py` transforma "o
código parece certo" em "3316 instruções conferidas, IGUAL". Sem essa ferramenta, o `elif`
teria passado despercebido.
→ `tools/comparar_bytecode.py`

## Clientes HTTP e APIs de IA

**HTTP 403 pode ser o User-Agent, não permissão nem rate limit.** O `urllib` manda
`Python-urllib/3.x` por padrão, e a API do OpenCode Zen recusa. Interpretamos 71 erros 403
como limite por IP e reescrevemos o gerador com espera de 25 s e backoff — tudo à toa. O
que denunciou foi `curl` respondendo 200 no mesmo instante. **Sempre defina User-Agent.**
→ `API_IA.md`

**Modelos com cadeia de pensamento vazam o raciocínio no corpo da resposta.** Mesmo tendo
campo `reasoning_content` separado. Sem validação, o usuário digitaria *"We'll count
manually."* como exercício. Peça JSON, extraia o array do meio do texto e **valide cada
item** — comprimento, idioma, ausência de vocabulário de raciocínio.
→ `API_IA.md`

**`max_tokens` baixo com modelo de raciocínio devolve `content` vazio.** O orçamento é
consumido pensando. Abaixo de ~300 tokens, a resposta vem vazia sem erro nenhum.
→ `API_IA.md`

**Chave de API em binário distribuído é chave vazada.** Este projeto é a prova: o código
inteiro foi extraído de um `.exe`. Por isso a escolha foi um serviço que responde
anonimamente, e não "esconder" uma credencial no pacote.
→ `API_IA.md`

**Chamada de rede na thread da interface congela a janela.** (Free)SimpleGUI é
single-thread; use `threading.Thread` + `window.write_event_value` para devolver o
resultado ao laço de eventos.
→ `ARQUITETURA.md`

## Empacotamento

**Binário que compila não é binário que roda.** Os primeiros binários Linux foram gerados
sem erro e quebravam na primeira execução, com `libtcl9.0.so: cannot open shared object
file` — as bibliotecas Tcl/Tk de Pythons "standalone" ficam fora dos caminhos que o
PyInstaller inspeciona. Sempre execute o binário depois de gerar.
→ `BUILD.md`

**PyInstaller não faz compilação cruzada.** `.exe` a partir do Linux exige um Python de
Windows sob Wine. Funciona, e não substitui um teste em Windows real.
→ `BUILD.md`

**Nem todo Python tem tkinter.** O 3.14 do sistema desta máquina não tem; o 3.13 do `uv`
tem. Sem tkinter, (Free)SimpleGUI não importa.
→ `BUILD.md`

**Dependência pode sumir do PyPI.** PySimpleGUI 5.0.10 (a do `.exe` trial original) não é
mais instalável; hoje só a série 6. Fixar a versão exata do original teria quebrado o
build — por isso `requirements-trial.txt` usa `>=6.0`, com a diferença registrada.
→ `BUILD.md`

## Processo

**Preserve o artefato original antes de melhorar qualquer coisa.** Os dois `.exe` de onde
o código saiu estão versionados em `original/binarios/`, com md5. É o que permite refazer
a verificação a qualquer momento — e foi comparando os dois que se provou que eles eram o
mesmo programa com outra biblioteca de GUI.
→ `original/LEIA-ME.md`
