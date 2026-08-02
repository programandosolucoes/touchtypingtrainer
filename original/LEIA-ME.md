# Material original (referência histórica)

O que está nesta pasta é a versão **anterior** do programa, preservada como está. Nada
aqui é usado pelo build ou pelo aplicativo — serve para conferência e comparação.

## `binarios/`

Os dois executáveis dos quais o código-fonte foi recuperado, exatamente como estavam
em `~/Downloads` (02/08/2026):

| arquivo | md5 | tamanho | GUI |
|---|---|---|---|
| `TouchTypingTrainer.exe` | `ea26b6629a0b7ad80712aea392a65b34` | 12.297.217 B | FreeSimpleGUI 5.1.0 |
| `TouchTypingTrainer-trial.exe` | `770fe0d8e0b93f1ce17feb2e122305ac` | 13.892.824 B | PySimpleGUI 5.0.10 |

Empacotados com PyInstaller (onefile, console) sobre Python 3.13.3. O bytecode dos dois
é **byte a byte idêntico**, exceto uma instrução: o `IMPORT_NAME` da biblioteca de GUI.
Foi essa comparação que confirmou que a única mudança entre as duas versões distribuídas
na época era a troca de PySimpleGUI por FreeSimpleGUI.

Estes binários **não têm** a geração de exercícios por IA nem as 209 frases novas — são o
programa como ele era antes desta rodada de trabalho. Os executáveis atuais estão em
`dist/windows/`.

## `TouchTypingTrainer_recuperado.py`

O fonte reconstruído do bytecode, **sem nenhuma alteração**: mesmos nomes, mesma ordem,
mesmas 507 linhas, cada instrução na mesma linha do original. Compilá-lo com Python 3.13
produz bytecode idêntico ao extraído do `.exe` (3512 de 3512 instruções).

É a referência para conferir qualquer dúvida sobre o comportamento antigo: o código em
produção hoje (na raiz do repositório) foi comentado, dividido em módulos e ganhou a
fonte de frases por IA, então diverge deste arquivo de propósito.

Ver `docs/RECUPERACAO.md` para o método de recuperação e a validação.
