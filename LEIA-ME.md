# TouchTypingTrainer

Treinador de digitação (touch typing) com interface em português, inglês e italiano,
correção caractere a caractere em tempo real e exercícios gerados por IA.

## As duas edições

| | **free** | **trial** |
|---|---|---|
| biblioteca de GUI | FreeSimpleGUI 5.1.0 (LGPL) | PySimpleGUI 5.0.10 |
| exige registro do usuário | não | **sim**, na primeira execução |
| funcionalidades | todas | as mesmas |
| binário | `TouchTypingTrainer` | `TouchTypingTrainer-trial` |

O código das duas é **idêntico** — muda só qual biblioteca de interface entra no pacote
(`gui_backend.py`, trocado pelo `build.py`). A limitação da edição trial vem do próprio
PySimpleGUI, que passou a exigir cadastro/licença; é ela que vai para clientes avaliarem,
enquanto a edição free é a completa, sem cadastro.

## O que o programa faz

- **Exercício com correção ao vivo**: cada caractere da frase-alvo muda de cor enquanto
  você digita — cinza (ainda não digitado), verde (certo), vermelho (errado).
- **Duas medidas de erro**: "Erros (texto final)" olha só o resultado; "Total de erros
  cometidos" conta cada posição em que você tropeçou, mesmo tendo corrigido depois.
- **Limite de tempo**: automático a partir do ritmo de aprendizado (1,5 caractere/s),
  ×2, ×3, ou manual em segundos.
- **Classificação de desempenho** comparando com 4 c/s (excelente) e 2,5 c/s (bom) —
  precisão abaixo de 85% tem prioridade sobre velocidade na classificação.
- **Guia de posicionamento das mãos** com desenho ASCII do teclado do idioma escolhido
  (ABNT2, US QWERTY ou QWERTY italiano) e legenda de qual dedo usa qual tecla.
- **Três fontes de frases**: internas, arquivo `.txt` do usuário, ou **geradas por IA**.

## Exercícios gerados por IA

A fonte "Gerado por IA" usa a API pública do **OpenCode Zen** nos modelos com sufixo
`-free`, que respondem **sem nenhuma credencial**:

- não há chave de API embutida no executável — nada a configurar, nada a extrair dele;
- o app já vem com um banco de frases geradas previamente (`sentences_ai.py`), então a
  fonte funciona na primeira execução e **sem internet**;
- o botão "Gerar Exercícios (IA)" acrescenta frases novas, guardadas em
  `~/.touchtypingtrainer/frases_ia.json` para as próximas execuções;
- a chamada roda em thread separada — a janela não congela — e qualquer falha de rede
  apenas mantém o banco offline em uso.

## Rodando a partir do código

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-free.txt      # ou requirements-trial.txt
python TouchTypingTrainer.py
```

Requer Python 3.13+ **com tkinter** (`python3-tk` no Debian/Ubuntu).

## Gerando os binários

```bash
pip install pyinstaller
python build.py            # as duas edições
python build.py free       # só a livre
```

O PyInstaller empacota para o sistema em que roda — não faz compilação cruzada. Para
gerar o `.exe` do Windows a partir do Linux, use um Python de Windows sob Wine:

```bash
wine ~/.wine/drive_c/Python313/python.exe -m pip install FreeSimpleGUI pyinstaller
wine ~/.wine/drive_c/Python313/python.exe build.py free
```

## Atualizando o banco de frases embutido

```bash
python tools/gerar_frases.py      # chama a IA e grava tools/frases_ia.json
python tools/atualizar_banco.py   # converte o JSON em sentences_ai.py
```

O gerador usa a credencial local do OpenCode, se existir, apenas porque faz dezenas de
chamadas seguidas; o aplicativo distribuído continua anônimo.

## Estrutura

| arquivo | papel |
|---|---|
| `TouchTypingTrainer.py` | aplicativo: janelas, sessão de treino, relatório |
| `i18n.py` | todos os textos nos três idiomas + `get_text` |
| `keyboards.py` | desenhos ASCII dos teclados (ABNT2, US, IT) |
| `ai_exercises.py` | cliente da API anônima + cache local |
| `sentences_ai.py` | banco de frases gerado por IA (offline, embutido) |
| `gui_backend.py` | escolhe FreeSimpleGUI ou PySimpleGUI conforme a edição |
| `build.py` | empacota as duas edições |
| `original/` | fonte recuperado do executável, sem alterações (referência) |
| `docs/RECUPERACAO.md` | como o código foi recuperado do `.exe` |
| `docs/LICOES_APRENDIDAS.md` | armadilhas encontradas no caminho |

## Histórico

O código-fonte deste programa foi perdido; só restavam os executáveis. Ele foi
reconstruído a partir do bytecode dos `.exe` (PyInstaller/Python 3.13) e validado
instrução por instrução contra o original — ver `docs/RECUPERACAO.md`. O fonte fiel,
sem nenhuma alteração, está em `original/` para conferência.
