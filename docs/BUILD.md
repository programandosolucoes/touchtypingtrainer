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
