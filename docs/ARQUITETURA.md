# Arquitetura e decisões de projeto

O programa é pequeno, mas várias escolhas dele parecem estranhas até se entender o motivo.
Este documento explica o desenho e o porquê — inclusive das partes herdadas do código
original, que foram mantidas de propósito.

## Módulos

| arquivo | responsabilidade |
|---|---|
| `TouchTypingTrainer.py` | janelas, laço de eventos, sessão de treino, relatório |
| `i18n.py` | dicionário `translations` (3 idiomas) + `get_text` + desenho do teclado |
| `keyboards.py` | os três layouts em ASCII e o gabarito da linha QWERTY |
| `ai_exercises.py` | cliente da API de IA, validação das frases e cache em disco |
| `sentences_ai.py` | banco de frases gerado previamente (dado, não código) |
| `gui_backend.py` | escolhe FreeSimpleGUI ou PySimpleGUI conforme a edição |

O original era um arquivo único de 507 linhas. A divisão foi feita na hora de comentar:
metade do arquivo era o dicionário de traduções, o que obrigava a rolar centenas de linhas
de dados para achar a lógica. Não houve mudança de comportamento na separação — a prova é
que a cópia fiel continua em `original/` para comparação.

## Fluxo da aplicação

```
main()
 ├── carregar_frases_ia(idioma)          banco embutido + cache do usuário
 ├── create_main_window(...)             janela de preferências
 └── laço de eventos
      ├── troca de idioma  → fecha a janela e recria (ver abaixo)
      ├── troca de fonte   → mostra/esconde as colunas de arquivo e de IA
      ├── '-AI_GENERATE-'  → dispara thread; resultado volta como '-AI_DONE-'
      └── '-START_TRAINING-' → start_training_session(...)
                                ├── escolher_frases(...)   qual conjunto sortear
                                ├── janela modal do exercício (read com timeout=100)
                                └── janela modal do relatório
```

## Por que a troca de idioma recria a janela inteira

Atualizar rótulo por rótulo seria mais rápido, mas os textos mudam de largura entre
idiomas ("Sentence Length:" vs "Comprimento da Frase:") e os frames não se redimensionam
sozinhos depois de criados — o resultado é texto cortado. Fechar e recriar custa alguns
milissegundos e sempre dá o layout certo.

Isso explica por que as preferências (`current_lang`, `current_source_pref`, …) são
variáveis de módulo e são passadas por parâmetro para `create_main_window`: o estado
precisa sobreviver à destruição da janela, e quem chama decide qual estado desenhar.

## Por que cada caractere é um elemento próprio

Durante o exercício, a frase-alvo é montada como uma lista de `sg.Text`, um por caractere,
com chave `-TARGET_CHAR_<i>-`. Parece exagero, e é o que viabiliza o recurso principal:
pintar letra a letra (cinza = não digitada, verde = certa, vermelha = errada) sem
redesenhar a janela. Um único `Multiline` não permite colorir intervalos com esse controle
em (Free)SimpleGUI.

A cada tecla, o laço repinta a frase inteira em vez de só a posição alterada. É barato no
tamanho de frase usado e evita rastrear qual índice mudou — colar um texto altera várias
posições de uma vez.

## Por que o erro é permanente

`error_committed_at_position` é uma lista de booleanos, uma por caractere. Quando o usuário
erra a posição *i*, ela vira `True` e **não** volta a `False` quando ele apaga e corrige.

Isso separa duas métricas que o relatório mostra lado a lado:

- **Erros (texto final)** — compara o resultado com o alvo. Mede o produto.
- **Total de erros cometidos** — soma dessas marcas. Mede o caminho.

Quem digita errado e corrige tudo tem 100% de precisão e um total de erros alto: exatamente
o diagnóstico que interessa a quem está aprendendo a digitar sem olhar.

## Como o tempo do exercício é calculado

`CPS_LEARNING = 1.5` caractere por segundo é o ritmo de referência de quem está aprendendo.
O tempo-base do exercício é `comprimento_da_frase / 1.5`, e os modos automáticos ×2 e ×3
multiplicam isso. O modo manual usa o valor em segundos digitado pelo usuário.

`CPS_FAST = 4.0` e `CPS_FASTER = 2.5` não limitam nada — servem só para classificar o
desempenho no fim. A ordem de avaliação é deliberada: tempo estourado e precisão abaixo de
85% vêm **antes** de qualquer elogio à velocidade, porque digitar rápido e errado não é
progresso.

O `600.0` que aparece como tempo-base alternativo é rede de segurança: frase vazia ou
constante zerada dariam divisão por zero ou limite de tempo instantâneo.

## Por que o laço do exercício usa `read(timeout=100)`

Com `read()` bloqueante, nada acontece enquanto o usuário não digita — e o cronômetro
precisa andar e o tempo precisa poder estourar sozinho. Com timeout de 100 ms, o laço
acorda dez vezes por segundo, atualiza o relógio e verifica o limite mesmo com o teclado
parado.

## Fontes de frases

`escolher_frases()` centraliza a decisão de qual conjunto sortear e devolve o erro já
traduzido, porque cada fonte falha por um motivo diferente:

| fonte | conjunto | erro possível |
|---|---|---|
| `builtin` | frases do `i18n.py`, filtradas por tamanho | idioma sem frases |
| `custom` | `.txt` do usuário, uma frase por linha | arquivo vazio ou não carregado |
| `ai` | `sentences_ai.py` + cache do usuário | banco vazio (nunca gerou e sem internet) |

O corte entre curta e longa é 60 caracteres, em todas as fontes (`LIMITE_FRASE_CURTA`).
O seletor de tamanho só aparece na fonte "internas", onde os dois conjuntos são curados;
nas outras, o usuário treina com o que tem.

## As duas edições

`gui_backend.py` tem uma constante literal:

```python
EDICAO = 'free'   # 'free' (FreeSimpleGUI) ou 'trial' (PySimpleGUI)
```

O `build.py` reescreve essa linha antes de empacotar e restaura depois, inclusive se o
empacotamento falhar (`try/finally`). A constante é uma string literal, e não algo lido de
variável de ambiente, porque o PyInstaller precisa enxergar o `import` de forma estática
para incluir a biblioteca certa no pacote.

A edição trial não tem nenhuma funcionalidade a menos: a limitação vem do próprio
PySimpleGUI, que exige registro do usuário na primeira execução. É essa a que vai para
clientes avaliarem; a free é a completa.

## Dependências

O aplicativo usa **apenas a biblioteca padrão** além da GUI: `urllib` para a chamada de
IA, `json`, `threading`, `ssl`, `random`, `time`, `os`, `re`. Nada de `requests`. Isso
mantém o executável pequeno e evita arrastar `certifi` e derivados para dentro do pacote.

---

# Modo Lição

## O limite físico, declarado

**Nenhum teclado comum reporta qual dedo pressionou a tecla.** Não existe API para
isso. O programa cerca o comportamento errado por vias indiretas: restringir o
conjunto de teclas do nível, ler o padrão do erro (alvo `j`, digitado `k` = dedo
médio no lugar do indicador) e ler o ritmo. A única verificação direta é o teste de
mãos, que exige quatro teclas pressionadas ao mesmo tempo.

## Por que JSON Lines e não SQLite

Com um usuário, sem escrita concorrente e com histórico na casa dos poucos megabytes,
o SQLite cobraria migração de esquema a cada campo novo sem entregar nada
perceptível. O JSONL acrescenta linha — queda de energia não corrompe o que já estava
gravado —, aceita campo novo sem migração e abre no editor de texto.

O que se perde, e é aceito: consulta indexada. Quem quiser progresso agregado lê o
arquivo inteiro. Se um dia incomodar, o caminho é gerar um resumo, não trocar de banco.

## Por que a regularidade usa mediana e não média

O índice conta quantos intervalos entre teclas passam de 3× o intervalo típico — o
sinal de quem parou para procurar a tecla com o olho. Se o "típico" fosse a média, uma
única pausa longa (o telefone tocou) arrastaria o limiar para cima e mascararia todas
as outras paradas. Com a mediana, a pausa isolada é um ponto fora da curva e o resto
do ritmo continua sendo medido.

As três primeiras teclas são descartadas — reação inicial não é hesitação — e com
menos de 10 intervalos válidos o índice fica indefinido em vez de chutar.

## Por que o teste de mãos é de quatro teclas e não de oito

Pedir `asdf`+`jkl;` de uma vez seria prova mais forte. Só que teclado de membrana
comum reporta no máximo ~6 teclas simultâneas: o programa culparia o usuário por um
limite do equipamento. Uma mão por vez passa em praticamente qualquer teclado e
continua impossível de simular digitando uma tecla de cada vez.

## Por que a lição não usa campo de texto

A entrada é dirigida por evento de tecla (`return_keyboard_events` + `bind`), não por
`sg.InputText`. Isso elimina de graça o colar — que no treino livre daria 100% de
precisão — e o backspace, já que caractere errado nunca entra.

Consequência: na lição "erros no texto final" é sempre zero, por construção. Por isso
a nota da lição é **tropeço por tecla**, e o relatório da lição não exibe a métrica de
texto final — anunciar 100% ali não significaria nada.

## Por que o teclado é desenhado e não é imagem

Cada tecla muda de cor individualmente durante a digitação; imagem estática exigiria
uma por estado. O `sg.Graph` também reescala com a janela. As mãos seguem o mesmo
princípio: em coordenadas lógicas fixas, o Canvas reescala sozinho, e destacar um dedo
é trocar um preenchimento em vez de trocar de arquivo.
