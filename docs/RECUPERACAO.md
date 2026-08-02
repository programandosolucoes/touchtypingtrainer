# Como o código-fonte foi recuperado do executável

O fonte deste programa foi perdido; restavam apenas os dois `.exe` empacotados com
PyInstaller (preservados em `original/binarios/`). Este documento registra o método que
funcionou, o que não funcionou, e como reproduzir a verificação — inclusive daqui a anos,
para qualquer outro executável Python.

## Resultado

| medida | valor |
|---|---|
| instruções comparadas (semânticas) | 3316, todas idênticas |
| instruções na mesma linha do original | 3512 de 3512 |
| linhas do arquivo | 507, igual ao original |
| arquivo recuperado | `original/TouchTypingTrainer_recuperado.py` |

Os dois números de instrução medem coisas diferentes: 3316 é o total comparado
semanticamente (a ferramenta ignora `EXTENDED_ARG`, `CACHE`, `RESUME` e `NOP`, que não
mudam comportamento), e 3512 é o total de instruções cujo número de linha foi conferido.

Comentários e docstrings **não** sobrevivem à compilação — não existem no bytecode e
portanto não foram recuperados. Tudo o mais (nomes, ordem, strings, estrutura e até a
distribuição do código em linhas) foi.

## Etapa 1 — identificar o executável

```bash
file TouchTypingTrainer.exe                       # PE32+ console, x86-64
strings -a TouchTypingTrainer.exe | grep -i "python3[0-9]\|pyinstaller"
```

Isso revelou `python313.dll` e as strings do bootloader do PyInstaller. A versão exata
(3.13.3) veio de `strings -a python313.dll | grep -E "^3\.13\."` depois da extração.

Saber a versão do Python é o passo mais importante de todos: o formato do bytecode muda a
cada versão menor, e todas as ferramentas seguintes dependem disso.

## Etapa 2 — extrair o pacote

```bash
pip install pyinstxtractor-ng
pyinstxtractor-ng original/binarios/TouchTypingTrainer.exe
```

Sai uma pasta `TouchTypingTrainer.exe_extracted/` com 960 arquivos: o `.pyc` do programa
(`TouchTypingTrainer.pyc`, 41 KB), os módulos da biblioteca padrão, a GUI e as DLLs. Só o
primeiro interessa — o resto é dependência empacotada.

## Etapa 3 — o descompilador NÃO funcionou

`pycdc` (Decompyle++) é a escolha natural, e foi um beco sem saída para Python 3.13:

```
Unsupported opcode: MAP_ADD (188)
# WARNING: Decompyle incomplete
```

Saíram **15 linhas** de um arquivo de 507 — ele parou no primeiro dicionário grande.
Investigando: a tabela de opcodes do pycdc para 3.13 está correta (conferida contra
`dis.opmap` do CPython 3.13 real, divergindo só em pseudo-opcodes ≥ 256, que nunca
aparecem em bytecode compilado). O problema é o alinhamento das entradas `CACHE`, que o
interpretador 3.11+ intercala no fluxo de instruções: quando o pycdc perde o alinhamento,
passa a ler um byte de argumento como se fosse opcode.

`uncompyle6` e `decompyle3` não são alternativa — param no Python 3.8.

**A lição não é "conserte o descompilador".** É que o disassembler oficial do próprio
Python é exato por definição, e reescrever 500 linhas a partir dele saiu mais rápido e
mais confiável do que depurar um descompilador de terceiros.

## Etapa 4 — instalar o Python exato e desmontar

```bash
pip install uv
uv python install 3.13          # o Python do sistema aqui é 3.14: bytecode incompatível
```

Confirme que o `.pyc` casa com o interpretador antes de qualquer outra coisa:

```python
import importlib.util
data = open('TouchTypingTrainer.pyc', 'rb').read()
print(data[:4].hex(), importlib.util.MAGIC_NUMBER.hex())   # f30d0d0a == f30d0d0a
```

Magic igual significa que o `marshal` local lê o objeto de código sem tradução nenhuma:

```python
import marshal, dis
co = marshal.loads(open('TouchTypingTrainer.pyc', 'rb').read()[16:])   # 16 = cabeçalho
dis.dis(co, depth=0, show_caches=False)
```

## Etapa 5 — o truque que muda tudo: números de linha

O objeto de código guarda a linha de origem de **cada instrução** (`ins.line_number`).
Isso transforma a reconstrução: em vez de adivinhar a formatação, dá para saber que
`get_text` começa na linha 187, que o dicionário `translations` vai da 59 à 176 e que
quatro pares chave/valor estavam **na mesma linha** do arquivo original.

Foi assim que a reconstrução fechou em exatamente 507 linhas, com cada instrução na linha
certa — e isso não é vaidade: número de linha batendo é evidência independente de que a
estrutura do código foi entendida corretamente.

## Etapa 6 — reconstruir dados grandes por simulação de pilha

O dicionário `translations` tem centenas de pares em três idiomas. Transcrever isso à mão
do disassembly seria lento e sujeito a erro. Em vez disso, um interpretador mínimo
percorreu as instruções mantendo uma pilha e tratando só o necessário — `BUILD_MAP`,
`MAP_ADD`, `DICT_UPDATE`, `BUILD_LIST`, `LIST_EXTEND`, `BUILD_CONST_KEY_MAP` — e imprimiu
o dicionário já com a linha de origem de cada chave, pronto para colar no arquivo.

Detalhes que apareceram nesse caminho e valem para qualquer reconstrução:

- dicionário literal com mais de ~30 itens não vira um `BUILD_MAP n`; o compilador emite
  `BUILD_MAP 0` e vai empilhando com `MAP_ADD`, em blocos costurados por `DICT_UPDATE`;
- lista literal só de constantes vira `BUILD_LIST 0` + `LOAD_CONST (tupla)` + `LIST_EXTEND`;
- `a, b, c = [], [], []` compila como três `BUILD_LIST 0` seguidos de `SWAP 3` e três
  stores — não há `BUILD_TUPLE`/`UNPACK_SEQUENCE`;
- `STORE_GLOBAL` no nível do módulo (em vez de `STORE_NAME`) denuncia uma declaração
  `global` escrita no próprio módulo — foi assim que `current_lang` foi identificada;
- `f(**{...})` e uma chamada com dezenas de argumentos nomeados geram o mesmo
  `CALL_FUNCTION_EX`; o que distingue os dois é o número de linha das chaves (num
  dicionário literal cada chave tem a linha em que está escrita; em argumentos nomeados
  todas herdam a linha da chamada).

## Etapa 7 — validar, corrigir, repetir

`tools/comparar_bytecode.py` compila o arquivo reconstruído e compara instrução a
instrução com o original:

```bash
python tools/comparar_bytecode.py TouchTypingTrainer.pyc original/TouchTypingTrainer_recuperado.py
```

A primeira execução acusou **uma** divergência, em `get_text`:

```
>> original:     ('RETURN_VALUE', 'None')
>> reconstruído: ('POP_JUMP_IF_NOT_NONE', 'None')
```

Ou seja: onde eu havia escrito `if`, o original tinha `elif`. Com `elif`, o compilador
duplica o `return` no fim do primeiro ramo em vez de deixar o fluxo cair no segundo teste —
e essa instrução extra denuncia a diferença. Trocado o `if` por `elif`, o resultado virou
`IGUAL`.

Depois disso sobrou o alinhamento de linhas, resolvido inserindo e removendo linhas em
branco até `instruções em linha diferente` chegar a zero. Três pontos exigiram juntar
corpo e cabeçalho numa linha só (`except ValueError: sg.popup(...); ...`), porque era
assim no original.

## Reproduzindo a verificação hoje

```bash
pip install pyinstxtractor-ng
uv python install 3.13
pyinstxtractor-ng original/binarios/TouchTypingTrainer.exe
~/.local/share/uv/python/cpython-3.13*/bin/python3.13 \
    tools/comparar_bytecode.py \
    TouchTypingTrainer.exe_extracted/TouchTypingTrainer.pyc \
    original/TouchTypingTrainer_recuperado.py
```

Saída esperada: `instruções conferidas: 3316`, `instruções em linha diferente: 0`, `IGUAL`.

Rodar contra `original/binarios/TouchTypingTrainer-trial.exe` dá **uma** divergência, a
esperada: `IMPORT_NAME 'PySimpleGUI'` no lugar de `IMPORT_NAME 'FreeSimpleGUI'`. Foi essa
comparação que provou que as duas versões distribuídas na época eram o mesmo programa.

## Além do bytecode: a verificação de comportamento

Bytecode idêntico já é prova forte, mas o arquivo também foi executado com um substituto
mínimo da biblioteca de GUI, confirmando que `get_text` faz o fallback de idioma correto,
que `calculate_accuracy_report` devolve 83,33% para um erro em seis caracteres e que o
desenho ASCII do teclado é montado sem erro. Prova de bytecode diz "é o mesmo código";
execução diz "e o código faz o que se espera".

## Por que o código em produção não é esse arquivo

`original/TouchTypingTrainer_recuperado.py` é a cópia fiel e serve de referência. O código
na raiz do repositório partiu dele e divergiu de propósito: ganhou comentários, foi
dividido em módulos e recebeu a geração de exercícios por IA. Para entender o que o
programa *fazia* antes, leia o arquivo em `original/`; para mexer no que ele faz *hoje*,
mexa na raiz.
