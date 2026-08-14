# Empacotamento: Linux, Windows e Windows a partir do Linux

Registro do que é necessário para gerar os quatro binários, com as armadilhas que
apareceram em cada plataforma.

## Resumo

```bash
python build.py            # as duas edições, para o sistema onde está rodando
python build.py free       # só a livre (FreeSimpleGUI)
python build.py trial      # só a de demonstração (PySimpleGUI)
```

Saída em `dist/`. O `build.py` troca a constante `EDICAO` em `gui_backend.py`, chama o
PyInstaller com `--onefile` e devolve o arquivo ao estado original no `finally`.

Cada edição precisa da sua biblioteca instalada no ambiente que está empacotando — por
isso há dois ambientes virtuais aqui: `.venv` (FreeSimpleGUI) e `.venv-trial`
(PySimpleGUI).

## Requisito que não é óbvio: tkinter

(Free)SimpleGUI é uma camada sobre o tkinter. Sem ele, nem o programa roda nem o
empacotamento serve para nada:

- Debian/Ubuntu: `sudo apt install python3-tk`
- **o Python 3.14 do sistema desta máquina não tem tkinter**; o ambiente usado é o Python
  3.13 do `uv` (`uv python install 3.13`), que já vem com ele — e, por coincidência útil,
  é a mesma série do Python do build original (3.13.3).

## Armadilha do Linux: as bibliotecas Tcl/Tk não são encontradas

Distribuições "standalone" do Python (as do `uv`, por exemplo) guardam `libtcl9.0.so` e
`libtcl9tk9.0.so` em `<prefixo>/lib`, fora dos caminhos que o PyInstaller inspeciona. O
binário é gerado sem erro e quebra na primeira execução:

```
ImportError: libtcl9.0.so: cannot open shared object file: No such file or directory
```

A função `libs_tcl_tk()` no `build.py` resolve isso: localiza as bibliotecas em
`sys.base_prefix/lib` e as adiciona com `--add-binary`. Só roda no Linux; no Windows as
DLLs já vêm junto.

Isso também vale como alerta: **binário que compila não é binário que roda.** Todos os
quatro foram executados depois de gerados; o teste é rodar com um tempo limite e verificar
que o processo continua vivo e sem traceback (um app de janela que "termina sozinho" em
segundos morreu).

## Gerando o `.exe` a partir do Linux (Wine)

O PyInstaller **não faz compilação cruzada** — ele empacota para o sistema em que está
rodando. Para gerar `.exe` no Linux é preciso um Python de Windows sob Wine.

```bash
# 1. instalador oficial do Python para Windows
curl -LO https://www.python.org/ftp/python/3.13.7/python-3.13.7-amd64.exe

# 2. instalação silenciosa no prefixo do Wine (com tcl/tk e pip)
WINEDEBUG=-all wine python-3.13.7-amd64.exe /quiet InstallAllUsers=1 \
    TargetDir=C:\\Python313 Include_tcltk=1 Include_pip=1 PrependPath=1 \
    Shortcuts=0 Include_test=0

# 3. conferir que subiu com tkinter
WINEDEBUG=-all wine ~/.wine/drive_c/Python313/python.exe -c "import tkinter; print('ok')"

# 4. dependências e build
WINEDEBUG=-all wine ~/.wine/drive_c/Python313/python.exe -m pip install \
    FreeSimpleGUI PySimpleGUI pyinstaller
WINEDEBUG=-all wine ~/.wine/drive_c/Python313/python.exe build.py free
WINEDEBUG=-all wine ~/.wine/drive_c/Python313/python.exe build.py trial
```

Testado com Wine 10.0. O `WINEDEBUG=-all` só reduz o ruído no terminal.

**O que isso prova e o que não prova:** os `.exe` gerados abrem sob Wine sem traceback.
Isso não substitui testar num Windows de verdade antes de mandar para um cliente — Wine
reproduz a API do Windows, não o Windows.

## Tamanhos e formato

| binário | tamanho | observação |
|---|---|---|
| `dist/windows/TouchTypingTrainer.exe` | ~12,4 MB | mesma ordem do `.exe` original (12,3 MB) |
| `dist/windows/TouchTypingTrainer-trial.exe` | ~12,2 MB | |
| `dist/linux/TouchTypingTrainer` | ~17,3 MB | maior por causa das Tcl/Tk embutidas |
| `dist/linux/TouchTypingTrainer-trial` | ~17,1 MB | |

Os `.exe` são **console** (sem `--noconsole`), igual ao original: uma janela de terminal
aparece junto com a interface. Para escondê-la, acrescente `--noconsole` ao comando no
`build.py` — mas saiba que isso também engole qualquer mensagem de erro no arranque.

## Nota sobre as versões da GUI

O `.exe` trial original usava PySimpleGUI 5.0.10. A série 5 foi retirada do PyPI; hoje o
`pip` instala a 6.x, que mantém a mesma API dos elementos usados aqui (testado com a 6.2:
`Radio`, `Frame`, `Column`, `Multiline`, `Push`, `VPush`, `HSeparator`, `Window`). Por isso
`requirements-trial.txt` pede `PySimpleGUI>=6.0` em vez da versão exata do original.

A edição free continua exatamente na mesma versão do binário original: FreeSimpleGUI 5.1.0.

## Verificação antes de empacotar

A lógica é coberta por `pytest`; o comportamento das telas com o usuário digitando,
não. Antes de gerar binário:

```bash
.venv/bin/python -m pytest tests/ -v          # 148 testes, tudo verde
.venv/bin/python tools/ver_teclado.py         # os três layouts, a olho
```

E o roteiro que só o humano faz, porque depende de mão em teclado:

1. `.venv/bin/python tools/sonda_teclas.py` — mede quantas teclas simultâneas o
   teclado reporta. **Rodar num teclado de membrana barato, não só no bom**: é onde
   o limite de rollover aparece.
2. `.venv/bin/python TouchTypingTrainer.py` → **Modo Lição**:
   - o botão "Começar" nasce desabilitado;
   - segurar `asdf` e depois `jkl`+quarta tecla habilita;
   - segurar uma tecla por 3 segundos **não** faz o passo voltar (auto-repeat);
   - no exercício: tecla errada não avança o texto, `Ctrl+V` não cola, Backspace não
     apaga;
   - o teclado desenhado acende a próxima tecla e o dedo certo na mão.
3. Conferir que `dados/progresso.jsonl` ganhou uma linha por exercício, nos dois
   modos (lição e treino livre).

Há ainda um teste de fumaça que só prova que nenhuma janela estoura ao montar — não
clica nem digita nada:

```bash
for j in menu guia previa exercicio relatorio; do
  timeout -s KILL 6 .venv/bin/python tools/fumaca_janelas.py $j 2>&1 | grep -q Traceback \
    && echo "FALHOU $j" || echo "ok $j"
done
```


## Requisitos do ambiente de empacotamento

Duas coisas que o binário herda de quem o gerou, e que por isso precisam estar
certas **na máquina do build**, não só na do usuário:

1. **Tk com Xft.** O PyInstaller embute o Tcl/Tk do Python que rodou o build. Um
   Python "standalone" (o do `uv`, por exemplo) traz Tk sem Xft, e o executável
   sai com fonte bitmap para todo mundo. Use um venv sobre o Python do sistema
   com `python3-tk` instalado. Confira antes de empacotar:

   ```bash
   .venv/bin/python -c "import tema, tkinter; tkinter.Tk().withdraw(); print(tema.diagnostico())"
   ```

   `{'xft': True, ...}` é o que se espera. Com `False`, pare e conserte o
   interpretador — nenhuma mudança de código melhora a fonte.

2. **Pillow.** Entra no pacote e é dependência de execução: é ela que rasteriza o
   teclado e as mãos com antialiasing.


## Empacotando para Windows sob Wine

Funciona e é o caminho usado hoje. O `build.py` detecta `os.name == 'nt'` sozinho
e joga o resultado em `dist/windows`.

```bash
export WINEDEBUG=-all      # sem isto o log vira uma parede de mensagens do Wine
wine ~/.wine/drive_c/Python313/python.exe -m pip install FreeSimpleGUI Pillow pyinstaller
wine ~/.wine/drive_c/Python313/python.exe build.py free
wine ~/.wine/drive_c/Python313/python.exe build.py trial   # precisa de PySimpleGUI
```

⚠️ **Feche o `.exe` antes de reempacotar.** Um processo Wine ainda vivo segura o
arquivo e o PyInstaller falha com `PermissionError: [WinError 5] Acesso negado`.
Note que `pkill -f TouchTypingTrainer.exe` **não** pega
`TouchTypingTrainer-trial.exe` — o nome não contém aquela string:

```bash
pkill -9 -f TouchTypingTrainer ; wineserver -k
```

### O que não dá para verificar sob Wine

A pasta `C:\Windows\Fonts` do prefixo Wine é **vazia** — ele mapeia as fontes do
Linux por fontconfig. Então o caminho de código que acha o arquivo da fonte no
Windows (`rasterizador._caminho_da_fonte`) não é exercitado aqui: sob Wine ele
devolve `None` e o desenho cai na fonte embutida do Pillow.

Num Windows de verdade `segoeui.ttf` existe e o caminho funciona. **Isto precisa
ser conferido num Windows real** antes de mandar binário para cliente — é o
mesmo item que já estava pendente para os `.exe`.
