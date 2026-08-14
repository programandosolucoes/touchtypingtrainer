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

## Auto-repeat do X11 desfaz o teste de teclas simultâneas

Segurar uma tecla no Linux gera `KeyRelease` + `KeyPress` repetidos e colados.
Quem acreditar no `KeyRelease` conclui que o usuário soltou, e o teste de mãos
pisca sem nunca fechar. A solução é não acreditar num soltar imediatamente: ele
fica em dúvida por 50 ms, e um novo pressionar da mesma tecla o cancela
(`teclas_pressionadas.py`).

## Rollover: teclado de membrana não reporta oito teclas

O teste de mãos foi desenhado com **quatro** teclas (uma mão por vez) porque
teclado comum reporta no máximo ~6 simultâneas e alguns travam antes disso.
Pedir as oito de uma vez faria o programa culpar o usuário por um limite do
equipamento dele. `tools/sonda_teclas.py` mede o limite do teclado à mão.

## Retângulo novo no Graph nasce por cima do texto

Repintar uma tecla apagando e redesenhando o retângulo esconde a letra que estava
por cima. É preciso `tk_canvas.tag_raise(id_do_texto)` depois de redesenhar
(`teclado_widget.pintar`). Sem isso o teclado vai perdendo as letras conforme se
digita — defeito que só aparece depois do primeiro acerto.

## `teclas_base` pegava a fatia errada da linha

A linha-base do ABNT2 é `asdfghjklç~]`. Cortar `[5:9]` devolve `h j k l`, e o `h`
é alcance estendido do indicador, não posição de repouso: o teste de mãos ia
cobrar a mão inteira deslocada uma tecla para a esquerda. O corte certo é
`[6:10]`. Nenhum teste de "existe e tem quatro teclas" pegaria isso — só a
asserção do conteúdo exato.

## Currículo verde não é currículo correto

Os 12 níveis passavam em todos os testes enquanto o nível 9 ("maiúsculas")
oferecia `;` — que em maiúscula continua `;` — e o nível 11 ("símbolos")
reapresentava o `ç` do nível 2 e a vírgula do nível 8. Só apareceu ao **imprimir
o currículo gerado** e ler. Teste de estrutura não substitui olhar o conteúdo.

Cuidado no mesmo lugar: `à è ì ù` do teclado italiano **são** letras e **devem**
entrar no nível de símbolos — são teclas próprias, nunca ensinadas antes. A
asserção correta é sobre letra ASCII, não sobre `isalpha()`.

## Chave de tradução montada por f-string escapa de qualquer busca

`get_text(f'licao_faltou_{f}', idioma)` deixa `licao_faltou_tropecos` e as irmãs
invisíveis para `grep` — elas parecem órfãs numa varredura de código morto. Antes
de apagar chave "não usada", procure também pelo prefixo.

## pytest não acha os módulos da raiz sem `pythonpath`

Com os testes em `tests/` e os módulos na raiz, o pytest põe só `tests/` no
`sys.path`. Sem `pythonpath = .` no `pytest.ini`, nenhum `import metricas`
funciona. O mesmo vale para os scripts de `tools/`, que precisam inserir a raiz no
`sys.path` à mão.
