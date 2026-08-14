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
- **Guia de posicionamento das mãos** com o teclado do idioma escolhido (ABNT2, US
  QWERTY ou QWERTY italiano) desenhado e colorido por dedo, ao lado das duas mãos.
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

## Modo Lição

Doze níveis, do `asdf` isolado ao texto corrido, feitos para construir memória
muscular em vez de medir quem já sabe digitar.

**Nenhum software sabe qual dedo você usou** — não existe teclado comum que reporte
isso. O que o programa faz é cercar o erro por quatro vias:

- **Teste de mãos antes de começar.** O botão só habilita depois de você pousar cada
  mão na linha-base e pressionar **as quatro teclas ao mesmo tempo**. Quatro teclas
  simultâneas provam que a mão está na posição — não dá para simular digitando uma de
  cada vez. É de uma mão por vez porque teclado de membrana comum não reporta oito.
- **Tecla errada não entra.** O texto não avança, não há backspace e não há como colar.
  Você repete até acertar.
- **Teclado desenhado** mostra a próxima tecla acesa e o dedo correspondente na mão,
  na mesma cor — é o que dispensa olhar para o teclado físico.
- **Ritmo picotado reprova**, mesmo com 100% de acerto: pausa longa antes de uma tecla
  é o sinal de quem procurou a tecla com o olho.

Só passa de nível com no máximo 3% de tropeços, o WPM da meta e ritmo regular, **em
dois exercícios seguidos** — um acerto isolado pode ser sorte. Reprovar não pune: o
relatório diz qual dos quatro critérios faltou e você repete o nível.

| # | nível | teclas novas | meta |
|---|---|---|---|
| 1-3 | linha-base | `asdf`, `jkl`+`;`/`ç`/`ò`, espaço | 10-12 WPM |
| 4-8 | resto das letras | `gh`, linha de cima, linha de baixo | 14-22 WPM |
| 9-11 | maiúsculas, números, símbolos | Shift, `1`-`0`, acentuação do layout | 25-30 WPM |
| 12 | texto corrido | banco interno, arquivo do usuário e IA | 35 WPM |

### Séries e escolha de nível

No menu você define **quantos exercícios seguidos** quer fazer (1, 3, 5 ou 10) e **em
que nível treinar**. O seletor lista só os níveis já liberados: revisar o que passou
sim, pular adiante não — senão o portão de progressão deixa de existir.

No fim de cada exercício o relatório oferece **Repetir** (o mesmo texto, mesma semente
— para consertar exatamente a sequência que saiu errada) ou **Próximo**.

### Tudo numa janela só

O programa inteiro — menu, guia de mãos, tela prévia, exercício, relatório, treino
livre e progresso — vive numa **única** janela de tamanho fixo, trocando o conteúdo
da mesma área. Nada de janela nova a cada etapa: cada uma roubaria o foco do teclado
e obrigaria a tirar as mãos da linha-base, que é justamente o hábito que o programa
existe para desfazer.

A única exceção é trocar de idioma, que reconstrói a janela — os rótulos mudam de
largura e frame do Tk não se redimensiona depois de criado.

### Meu progresso

Tela nova, lendo o mesmo `dados/progresso.jsonl`:

- **evolução por dia** — exercícios, WPM médio e precisão, e se você está subindo
  ou caindo em relação aos dias anteriores;
- **teclas que você mais erra**, com a troca mais frequente: `J → K (4x)` significa
  que você usou o dedo médio no lugar do indicador;
- **dedos que mais erram**, somando todas as teclas de cada um.

O progresso fica em `dados/progresso.jsonl`, **ao lado do executável** — copiou a
pasta para o pendrive, levou o histórico junto. Se essa pasta for somente-leitura, cai
para a pasta do usuário e o programa avisa.

## Rodando os testes

```bash
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pytest tests/ -v
```

São 252 testes cobrindo os módulos sem GUI e, quando há servidor gráfico, também o
teclado e as mãos desenhados. Alguns leem a **cor real dos widgets na janela montada**
para provar que o texto ficou legível — paleta correta não garante tela legível. Sem
`DISPLAY`, os testes de tela são pulados em vez de falhar.

## Rodando a partir do código

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-free.txt      # ou requirements-trial.txt
python TouchTypingTrainer.py
```

Requer Python 3.13+ **com tkinter compilado com Xft** — no Debian/Ubuntu,
`sudo apt install python3-tk` sobre o Python do sistema.

⚠️ O Python "standalone" (o que o `uv` instala, por exemplo) empacota um Tk **sem
Xft**: ele não enxerga o fontconfig, cai numa fonte bitmap e a letra fica feia — no
seu computador e dentro do executável que você distribuir. Para conferir:

```bash
python -c "from tkinter import font as f; import tkinter; tkinter.Tk().withdraw(); print(len(f.families()))"
```

Menos de ~50 famílias significa Tk sem Xft. Com Xft passam de 200.

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
| `TouchTypingTrainer.py` | frases, sorteio do treino livre e gravação — sem desenhar nada |
| `i18n.py` | todos os textos nos três idiomas + `get_text` |
| `tema.py` | fonte, paleta e escala tipográfica — um lugar só (sem GUI) |
| `aplicativo.py` | a janela única e o laço que troca de tela |
| `telas.py` | as telas do Modo Lição, como colunas da mesma janela |
| `sessao.py` | a série de exercícios e o nível em treino (sem GUI) |
| `rasterizador.py` | desenha teclado e mãos com antialiasing (sem GUI) |
| `metricas.py` | WPM, tropeços e regularidade do ritmo (sem GUI) |
| `historico.py` | onde o progresso mora e como é lido/gravado (sem GUI) |
| `layouts.py` | os três teclados e o **mapa tecla→dedo** (sem GUI) |
| `licoes.py` | currículo de 12 níveis, gerador e critério (sem GUI) |
| `teclas_pressionadas.py` | quais teclas estão seguradas, apesar do auto-repeat |
| `teclado_widget.py` | teclado desenhado no Canvas, com cor por dedo |
| `maos_widget.py` | as duas mãos desenhadas, dedo da vez aceso |
| `modo_licao.py` | tela prévia com teste de mãos e exercício travado |
| `progresso.py` | evolução por dia e diagnóstico de tecla/dedo (sem GUI) |
| `tests/` | suíte pytest — 252 testes |
| `ai_exercises.py` | cliente da API anônima + cache local |
| `sentences_ai.py` | banco de frases gerado por IA (offline, embutido) |
| `gui_backend.py` | escolhe FreeSimpleGUI ou PySimpleGUI conforme a edição |
| `build.py` | empacota as duas edições |
| `tools/` | gerador do banco de frases e verificador de bytecode |
| `original/` | fonte e binários originais, sem alterações (referência) |
| `docs/` | documentação completa — comece por `docs/README.md` |

## Documentação

Todo o conhecimento do projeto está em [docs/](docs/README.md):

- **[docs/ARQUITETURA.md](docs/ARQUITETURA.md)** — o desenho do programa e o porquê de
  cada decisão (erro permanente, um elemento por caractere, recriar a janela na troca de
  idioma…).
- **[docs/API_IA.md](docs/API_IA.md)** — a API anônima usada, as três armadilhas que
  custaram tempo (403 por User-Agent, raciocínio vazando na resposta, thread) e as
  alternativas caso o serviço mude.
- **[docs/BUILD.md](docs/BUILD.md)** — empacotamento nas duas plataformas, inclusive o
  passo a passo do `.exe` sob Wine.
- **[docs/RECUPERACAO.md](docs/RECUPERACAO.md)** — como o fonte foi recuperado do `.exe`,
  com o comando para refazer a verificação hoje.
- **[docs/LICOES_APRENDIDAS.md](docs/LICOES_APRENDIDAS.md)** — índice das armadilhas.

## Histórico

O código-fonte deste programa foi perdido; só restavam os executáveis. Ele foi
reconstruído a partir do bytecode dos `.exe` (PyInstaller/Python 3.13) e validado
instrução por instrução contra o original — ver `docs/RECUPERACAO.md`. O fonte fiel,
sem nenhuma alteração, está em `original/` para conferência.
