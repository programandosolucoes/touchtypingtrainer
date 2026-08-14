# Modo Lição — memória muscular com dedo correto

Design validado em 2026-08-14. Cobre as três frentes que formam uma entrega só:
**F1** (captura, métricas e histórico), **F2** (teclado e mãos desenhados) e
**F3** (o Modo Lição em si).

Fica de fora, para um spec próprio depois: **F4** — tela de evolução ao longo dos
dias, ranking das teclas/dedos mais errados e treino dirigido neles. O formato de
dados definido aqui já é o que o F4 vai consumir.

## O problema

O programa hoje sorteia uma frase e mede o resultado. Isso avalia quem já sabe
digitar; não *ensina* ninguém a digitar sem olhar. Faltam as três coisas que
constroem memória muscular: saber qual dedo vai em qual tecla sem procurar,
não poder seguir em frente errando, e progredir por critério em vez de vontade.

## O limite físico, declarado

**Nenhum teclado comum reporta qual dedo pressionou a tecla.** Não existe API
para isso, e qualquer promessa de "detecta o dedo errado" seria mentira. O que
o programa faz é cercar o comportamento errado por três vias indiretas:

1. **Restringir o conjunto de teclas** do nível, de modo que usar outro dedo
   seja desconfortável e não compense.
2. **Ler o padrão do erro**: alvo `j` e digitado `k` significa dedo médio no
   lugar do indicador. O mapa tecla→dedo classifica isso.
3. **Ler o ritmo**: quem procura a tecla com o olho tem intervalos irregulares;
   quem tem memória muscular tem intervalo regular.

E uma via direta, essa sim verificável: o **teste de mãos** antes do exercício
confirma que as duas mãos estão pousadas na linha-base, porque exige quatro
teclas pressionadas *ao mesmo tempo* — o que não dá para simular digitando uma
de cada vez.

## Decisões de produto

| decisão | escolha | por quê |
|---|---|---|
| usuários | um perfil por instalação | app portátil de uso pessoal; perfis podem entrar depois sem descartar dado |
| onde grava | ao lado do executável, com queda para a pasta do usuário | progresso viaja junto no pendrive |
| GUI | FreeSimpleGUI (mantida) | grátis, já é a base, e a edição trial usa a mesma API |
| dependência nova em execução | nenhuma | portabilidade do executável é requisito |
| treino livre atual | continua, intocado | quem já usa não perde nada |

## Arquitetura

O `TouchTypingTrainer.py` tem 672 linhas misturando janela, métrica e sessão.
A lógica sai para módulos sem GUI — que é o que os torna testáveis, e o projeto
hoje não tem nenhum teste.

| módulo | papel | GUI |
|---|---|---|
| `metricas.py` | WPM bruto/líquido, precisão, tropeços, regularidade do ritmo | não |
| `historico.py` | resolução do caminho portátil, gravação e leitura do JSONL | não |
| `layouts.py` | geometria das teclas e mapa tecla→dedo dos 3 layouts | não |
| `licoes.py` | currículo, gerador de exercício por conjunto de teclas, critério de aprovação | não |
| `teclado_widget.py` | desenha o teclado no `sg.Graph` e acende tecla/dedo | sim |
| `modo_licao.py` | tela prévia com teste de mãos e exercício travado | sim |
| `TouchTypingTrainer.py` | menu, preferências e roteamento | sim |

`keyboards.py` (ASCII) e o guia de mãos em texto são aposentados pelo
`teclado_widget.py`: o botão **Guia de Mãos** do menu passa a abrir o teclado
desenhado, com as teclas coloridas por dedo e a ilustração das mãos, no lugar do
`sg.Multiline` em fonte monoespaçada. O `i18n.py` perde as chaves do desenho
ASCII e ganha as do Modo Lição. A cópia fiel do código original em `original/`
não é tocada.

## F1 — Captura, métricas e histórico

### Onde os dados moram

Ordem de resolução, decidida uma vez na abertura e exibida na tela de progresso:

1. `<pasta do executável>/dados/progresso.jsonl`, se a pasta for gravável.
2. `~/.touchtypingtrainer/progresso.jsonl` (Linux) ou
   `%APPDATA%\TouchTypingTrainer\progresso.jsonl` (Windows).

A queda para a pasta do usuário acontece quando o programa está instalado em
local somente-leitura. É avisada uma vez, não a cada abertura.

### Formato: JSON Lines, uma linha por exercício

Escolhido sobre SQLite porque, com um usuário, sem escrita concorrente e nesse
volume, o SQLite cobraria migração de esquema a cada campo novo sem entregar
nada perceptível. JSONL acrescenta linha (queda de energia não corrompe o que já
estava gravado), aceita campo novo sem migração e abre no editor.

```json
{
  "v": 1,
  "quando": "2026-08-14T10:32:11-03:00",
  "modo": "licao",
  "nivel": "base-esquerda",
  "idioma": "pt",
  "layout": "abnt2",
  "alvo": "asdf jkl asdf",
  "duracao_s": 12.4,
  "wpm_bruto": 34.2,
  "wpm_liquido": 31.0,
  "tropecos": 3,
  "total_teclas": 52,
  "regularidade": 0.94,
  "aprovado": true,
  "teclas": {
    "a": {"acertos": 12, "erros": 1, "ms_medio": 280, "confusoes": {"s": 1}}
  }
}
```

Em `teclas`, a chave é o caractere **esperado** e `confusoes` diz o que foi
digitado no lugar dele e quantas vezes — no exemplo, o `a` foi cobrado 13 vezes,
saiu errado 1, e nessa vez o usuário digitou `s`. É esse par que revela dedo
trocado: `j` cobrado e `k` digitado é dedo médio no lugar do indicador.

Guarda **resumo por tecla**, não cada tecla individual: um exercício de 200
caracteres vira ~30 entradas em vez de 200, e 1000 exercícios ficam em torno de
3 MB. A contrapartida, assumida: não dá para reanalisar o ritmo bruto de uma
sessão antiga — a regularidade é calculada na hora e gravada como número.

Uma linha ilegível (arquivo truncado, edição manual) é pulada com aviso no log;
não derruba o programa nem invalida o resto do histórico.

### Métricas

**WPM** no padrão da área — uma "palavra" são 5 caracteres:

- bruto = `(caracteres_digitados / 5) / minutos`
- líquido = `bruto − (erros_nao_corrigidos / minutos)`, com piso em zero

No Modo Lição o líquido é igual ao bruto, porque a trava impede que erro entre
no texto. É de propósito: na lição quem mede a qualidade é o tropeço.

**Precisão / tropeços.** No treino livre continuam as duas medidas de hoje
(erros no texto final e total de tropeços). Na lição, "erros no texto final" é
zero por construção — a trava não deixa caractere errado entrar. Por isso a nota
da lição é `tropeços / total_de_teclas`, e o relatório da lição não mostra a
métrica de texto final, para não anunciar um 100% que não significa nada.

**Regularidade do ritmo** — o índice que reprova quem caça a tecla com o olho:

1. Coleta o intervalo entre teclas consecutivas.
2. Descarta as 3 primeiras (tempo de reação inicial não é hesitação).
3. Calcula a **mediana** dos intervalos.
4. Conta como *parada* todo intervalo maior que 3× a mediana.
5. Índice = `1 − paradas / intervalos_contados`.

Mediana e não média porque uma única pausa longa — o telefone tocou — arrastaria
a média e reprovaria quem digita bem. Exercício com menos de 10 intervalos
válidos não recebe índice (fica `null` e não reprova).

## F2 — Teclado e mãos desenhados

### Teclado

Desenhado em `sg.Graph` (Canvas do Tk), não em imagem: cada tecla precisa mudar
de cor individualmente durante a digitação, e imagem estática exigiria uma
imagem por estado. O Graph também redesenha proporcional quando a janela muda de
tamanho.

`layouts.py` descreve cada tecla como `(linha, x, largura, rótulo, dedo, mão)`,
para ABNT2, US QWERTY e QWERTY italiano. **Essa tabela é o mapa tecla→dedo que
hoje não existe** — atualmente essa informação só está como prosa no
`i18n.py` e como gabarito da linha QWERTY no `keyboards.py`, nenhum dos dois
consultável por código.

Estados de tecla: repouso, **próxima** (destacada), certa, errada, e a marca
tátil de `F` e `J`. Cada dedo tem cor própria, usada tanto no teclado quanto na
ilustração da mão.

### Mãos

SVG autoral com um grupo por dedo, convertido para PNG **no `build.py`**:
5 variações por mão (neutra + 4 dedos em destaque), 10 imagens pré-geradas.
Nenhum conversor de SVG entra no executável — `cairosvg` arrastaria a biblioteca
nativa do Cairo e quebraria a portabilidade. Os SVGs são gerados no Open Design.

### Janelas

- menu: 800×860 (hoje 600×760)
- lição: 1100×780, redimensionável — frase no topo, mãos ao lado, teclado na
  faixa inferior

## F3 — Modo Lição

### Tela prévia: o portão

Mostra o nível, quais teclas são novas, o objetivo e o critério de aprovação.
Abaixo, o teste de mãos em dois passos:

1. **Mão esquerda** — pousar em `a s d f` e pressionar as quatro juntas.
2. **Mão direita** — pousar em `j k l` + a quarta tecla do layout
   (`;` no US, `ç` no ABNT2, `ò` no italiano) e pressionar as quatro juntas.

Cada tecla fica verde enquanto pressionada; o passo conclui com as quatro verdes
simultâneas por 400 ms. O botão **Começar** só habilita com os dois passos
verdes.

Duas armadilhas tratadas explicitamente:

- **Auto-repeat do X11.** Segurar a tecla no Linux gera `KeyRelease`+`KeyPress`
  repetidos, que ingenuamente parecem "soltou". Um `KeyRelease` seguido de
  `KeyPress` da mesma tecla em menos de 50 ms não conta como soltar. Sem isso o
  teste pisca e nunca fecha.
- **Rollover do teclado.** Teclado de membrana costuma reportar no máximo ~6
  teclas simultâneas e alguns travam em combinações específicas — por isso o
  teste é de 4 teclas (uma mão), não 8. Se mesmo assim não fechar em 15 s, o
  programa assume limite do equipamento, oferece o teste sequencial (uma tecla
  por vez, na ordem) e **diz que o limite é do teclado**, não do usuário. Essa
  condição fica gravada para não reoferecer o teste simultâneo toda vez.

### O exercício travado

- Entrada dirigida por evento de tecla (`return_keyboard_events`), não
  `sg.InputText` livre. **Colar deixa de existir** — hoje colar a frase dá 100%
  de precisão, e com histórico gravado isso viraria dado sujo permanente.
- Tecla errada **não entra no texto**: pisca a tecla certa no teclado desenhado,
  conta um tropeço e o exercício continua exigindo a tecla certa.
- Backspace desabilitado na lição — não há o que apagar.
- O teclado desenhado acende a **próxima** tecla e destaca o dedo na mão.
- Cronômetro e intervalo entre teclas medidos ao longo de todo o exercício.

### Aprovação de nível

Todos os quatro critérios, em **dois exercícios seguidos** (um acerto isolado
pode ser sorte):

| critério | valor |
|---|---|
| tropeços | ≤ 3% das teclas |
| WPM | ≥ a meta do nível (coluna da tabela do currículo) |
| regularidade | ≥ 0,90 |
| tempo | dentro do limite do exercício |

O **limite de tempo do exercício** deriva da própria meta de WPM, para não haver
dois números soltos dizendo a mesma coisa: é o dobro do tempo que o exercício
levaria digitado exatamente na meta do nível. Assim quem alcança a meta tem
sempre 100% de folga, e o limite acompanha o nível sem ajuste manual.

Reprovar não pune: repete o mesmo nível, e o relatório diz **qual** dos quatro
critérios faltou.

### Currículo

Doze níveis. Até o 8, o exercício é *gerado* a partir do conjunto de teclas já
liberado, em grupos de 3 a 5 caracteres. Do 9 em diante, usa frases reais
filtradas para caber no alfabeto já aprendido; o 12 libera o banco inteiro.

| # | nível | teclas novas | meta de WPM |
|---|---|---|---|
| 1 | base esquerda | `a s d f` | 10 |
| 2 | base direita | `j k l` + `;`/`ç`/`ò` | 10 |
| 3 | base completa | as oito + espaço | 12 |
| 4 | índices estendidos | `g` `h` | 14 |
| 5 | linha de cima esquerda | `q w e r t` | 16 |
| 6 | linha de cima direita | `y u i o p` | 18 |
| 7 | linha de baixo esquerda | `z x c v b` | 20 |
| 8 | linha de baixo direita | `n m , .` | 22 |
| 9 | maiúsculas | Shift com o mínimo oposto | 25 |
| 10 | números | `1`–`0` | 28 |
| 11 | símbolos e acentuação | próprios do layout (`ç ~ ´` / `ò à ù` / `' - =`) | 30 |
| 12 | texto corrido | banco interno, arquivo do usuário e IA | 35 |

As metas são baixas de propósito nos primeiros níveis: nessa altura o que se
está construindo é o caminho do dedo, não velocidade — e uma meta agressiva cedo
empurra a pessoa de volta a olhar para o teclado, que é exatamente o hábito a
matar.

O gerador é determinístico a partir de uma semente gravada na linha do
histórico, então um exercício pode ser repetido igual.

### O que não muda

O treino livre de hoje continua como está, acessível pelo menu. Ele passa a
gravar no histórico (`modo: "livre"`) e a mostrar WPM no relatório, e mantém as
duas métricas de erro atuais.

## Casos de borda

| situação | comportamento |
|---|---|
| pasta do executável somente-leitura | grava na pasta do usuário, avisa uma vez |
| linha do JSONL ilegível | pula a linha, segue lendo o resto |
| teclado sem rollover para 4 teclas | teste sequencial, com a causa explicada |
| auto-repeat do X11 | filtro de 50 ms entre soltar e apertar |
| layout do sistema diferente do idioma escolhido | o teste de mãos detecta (a tecla física não produz o caractere esperado) e avisa qual layout o sistema parece estar usando |
| exercício curto demais para medir ritmo | regularidade fica `null` e não reprova |
| janela redimensionada durante o exercício | teclado redesenha proporcional, sem perder o estado |
| histórico inexistente na primeira execução | começa no nível 1, sem erro |

## Testes

`pytest`, sobre os módulos sem GUI — hoje o projeto não tem nenhum teste.

- `metricas`: WPM com texto vazio e com duração zero; líquido com piso em zero;
  regularidade com uma pausa isolada (não pode reprovar); regularidade com
  poucos intervalos (`null`); tropeço não zera quando o usuário corrige.
- `licoes`: gerador só produz teclas do conjunto liberado; mesma semente produz
  o mesmo exercício; aprovação exige os quatro critérios e dois seguidos;
  reprovação identifica qual critério faltou.
- `historico`: caminho cai para a pasta do usuário quando a de destino é
  somente-leitura; linha corrompida é pulada; gravação acrescenta sem reescrever.
- `layouts`: os três layouts cobrem todas as teclas com dedo atribuído; nenhuma
  tecla sem dedo; a quarta tecla da base direita difere por layout.

A parte com GUI (`teclado_widget`, `modo_licao`) é verificada à mão, com um
roteiro no `docs/BUILD.md` — inclusive o teste de mãos num teclado de membrana
real, que é onde o rollover aparece.

## Riscos

| risco | mitigação |
|---|---|
| rollover pior que o previsto em teclados comuns | modo sequencial já desenhado; testar cedo, num teclado de membrana barato |
| auto-repeat com comportamento diferente entre X11, Wayland e Windows | tratar por filtro de tempo, que independe da plataforma; validar nos três |
| `sg.Graph` lento para repintar o teclado a cada tecla | repintar só as teclas que mudaram de estado, não o teclado inteiro |
| frase do banco fora do alfabeto do nível | filtro no `licoes.py`, com teste que garante o conjunto |
