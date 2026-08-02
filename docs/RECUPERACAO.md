# TouchTypingTrainer — código-fonte recuperado

Fonte reconstruído a partir dos executáveis PyInstaller em `~/Downloads`
(`TouchTypingTrainer.exe` e `TouchTypingTrainer-trial.exe`), em 02/08/2026.

## Fidelidade da recuperação

O arquivo `TouchTypingTrainer.py` foi validado assim: ele é compilado com
Python 3.13 e o bytecode resultante é comparado, instrução por instrução, com o
bytecode extraído do `.exe`.

- **3512 de 3512 instruções idênticas** (todos os 9 blocos de código: módulo + 8 funções)
- **507 linhas**, com cada instrução caindo exatamente na mesma linha do original
- Testado em execução: `get_text`, `calculate_accuracy_report` e
  `get_formatted_focused_ascii` rodam e devolvem os valores esperados

O que **não** sobrevive à compilação e portanto não pôde ser recuperado:

- **comentários** — os que existem no arquivo foram escritos agora, como marcação
  de leitura; os originais se perderam
- **nomes de variáveis locais dentro de list comprehensions** já vêm no bytecode,
  então esses estão corretos; nada foi inventado em nomes

## Ambiente original

| item | valor |
|------|-------|
| Python | 3.13.3 |
| GUI (versão final) | FreeSimpleGUI 5.1.0 |
| GUI (versão trial) | PySimpleGUI 5.0.10 |
| empacotador | PyInstaller (onefile, modo console) |

As duas versões do `.exe` têm **exatamente o mesmo código** — a única diferença é
a linha 1: `import PySimpleGUI as sg` no `-trial.exe` e
`import FreeSimpleGUI as sg` no definitivo. Ou seja, a migração de PySimpleGUI
(que passou a exigir licença) para o fork livre FreeSimpleGUI foi a única
alteração entre os dois binários.

## Como rodar

```bash
pip install -r requirements.txt
python TouchTypingTrainer.py
```

Para voltar ao PySimpleGUI, basta trocar a linha 1 por `import PySimpleGUI as sg`.

## Como reempacotar

```bash
pyinstaller --onefile TouchTypingTrainer.py
```

O binário original é console (sem `--windowed`), então uma janela de terminal
aparece junto com a GUI. Para escondê-la, use `--noconsole`.

## O que o programa faz

Treinador de digitação (touch typing) com interface em três idiomas — inglês,
italiano e português — selecionáveis em tempo real (a janela é recriada na troca).

- **Frases**: internas (curtas/longas/mistas) ou carregadas de um `.txt` do usuário;
  há botão para baixar um `.txt` de exemplo
- **Limite de tempo**: automático pelo ritmo de aprendizado (1,5 caractere/s), ×2, ×3,
  ou manual em segundos
- **Durante o exercício**: cada caractere da frase-alvo é um elemento próprio na tela
  e muda de cor conforme você digita — cinza (pendente), verde (certo), vermelho (errado)
- **Erro é permanente**: uma vez errada, a posição fica marcada mesmo se corrigida
  depois (`error_committed_at_position`), e isso vira o "Total de erros cometidos"
- **Relatório final**: precisão %, erros no texto final, erros totais cometidos,
  tempo gasto e classificação de desempenho comparando com 4 e 2,5 caracteres/s
- **Guia de posicionamento das mãos**: desenho ASCII do teclado (ABNT2, US QWERTY
  ou QWERTY italiano, conforme o idioma) com a legenda de qual dedo usa qual tecla
