# Modo Lição — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transformar o TouchTypingTrainer de avaliador de digitação em treinador de memória muscular, com teste de mãos obrigatório, teclado desenhado que acende tecla e dedo, exercício que recusa tecla errada e currículo de 12 níveis liberados por critério.

**Architecture:** Toda a lógica sai para módulos sem GUI (`metricas`, `historico`, `layouts`, `licoes`, `teclas_pressionadas`), que é o que os torna testáveis — o projeto hoje não tem nenhum teste. A GUI (`teclado_widget`, `modo_licao`) consome esses módulos e fica reduzida a desenhar e reagir. O `TouchTypingTrainer.py` encolhe para menu e roteamento.

**Tech Stack:** Python 3.13, FreeSimpleGUI 5.1.0 (Tk 9.0), pytest, apenas biblioteca padrão além da GUI.

**Spec:** `docs/superpowers/specs/2026-08-14-modo-licao-design.md`

## Global Constraints

- **Interpretador:** sempre `.venv/bin/python` a partir da raiz do projeto. O `python3` do sistema é 3.14 e **não tem tkinter** — comando que use `python3` vai falhar.
- **Zero dependência nova em tempo de execução.** O executável precisa continuar portátil. `pytest` é só de desenvolvimento (`requirements-dev.txt`), nunca importado por código de aplicação.
- **Nada de `cairosvg`, `Pillow` ou conversor de SVG no runtime.** SVG vira PNG no `build.py`, em tempo de empacotamento.
- **Idioma do código:** nomes e comentários em português do Brasil, como todo o resto do projeto.
- **`original/` não é tocado.** É a cópia fiel recuperada do executável, referência de conferência.
- **Layouts suportados:** `abnt2` (idioma `pt`), `us` (idioma `en`), `it` (idioma `it`).
- **Commits:** um por tarefa, mensagem em português, sem `Co-Authored-By`.

---

### Task 1: Sonda de teclas simultâneas (risco nº 1, medido antes de tudo)

O spec aposta que dá para detectar 4 teclas pressionadas ao mesmo tempo e filtrar o auto-repeat do X11. Se o teclado do usuário não entregar isso, o teste de mãos inteiro muda de forma. Essa tarefa mede antes de qualquer código depender da resposta.

**Files:**
- Create: `tools/sonda_teclas.py`
- Create: `docs/superpowers/plans/sonda-teclas-resultado.md`

**Interfaces:**
- Consumes: nada
- Produces: um relatório em `docs/superpowers/plans/sonda-teclas-resultado.md` dizendo quantas teclas simultâneas o teclado reporta e se o auto-repeat gera `KeyRelease` espúrio. As Tasks 5 e 14 leem esse relatório.

- [ ] **Step 1: Escrever a sonda**

```python
"""Sonda: descobre o que o teclado real reporta ao segurar várias teclas.

Não faz parte do aplicativo. Serve para responder duas perguntas antes de o
Modo Lição depender das respostas:

1. Quantas teclas simultâneas este teclado consegue reportar? (rollover)
2. Segurar uma tecla gera KeyRelease espúrio? (auto-repeat do X11)

Rode com:  .venv/bin/python tools/sonda_teclas.py
"""
import time

from gui_backend import sg

eventos = []          # (instante_ms, 'press'|'release', keysym)
pressionadas = {}     # keysym -> instante do press
maximo_simultaneo = 0


def agora_ms():
    return time.monotonic() * 1000.0


layout = [
    [sg.Text('Segure ASDF juntas. Depois segure JKL e a quarta tecla.', font=('Helvetica', 12))],
    [sg.Text('Pressionadas agora:', font=('Helvetica', 11)), sg.Text('—', key='-ATIVAS-', font=('Courier New', 14))],
    [sg.Text('Máximo simultâneo:', font=('Helvetica', 11)), sg.Text('0', key='-MAX-', font=('Courier New', 14))],
    [sg.Text('Eventos (últimos 12):', font=('Helvetica', 11))],
    [sg.Multiline('', key='-LOG-', size=(60, 14), font=('Courier New', 9), disabled=True)],
    [sg.Button('Encerrar e gravar relatório', key='-FIM-')],
]
janela = sg.Window('Sonda de teclas', layout, finalize=True, return_keyboard_events=True)
janela.bind('<KeyPress>', '-DOWN-')
janela.bind('<KeyRelease>', '-UP-')

while True:
    evento, _ = janela.read(timeout=50)
    if evento in (sg.WIN_CLOSED, '-FIM-'):
        break
    if evento in ('-DOWN-', '-UP-'):
        tk_evento = janela.user_bind_event
        keysym = getattr(tk_evento, 'keysym', '?')
        instante = agora_ms()
        if evento == '-DOWN-':
            pressionadas.setdefault(keysym, instante)
            eventos.append((instante, 'press', keysym))
        else:
            pressionadas.pop(keysym, None)
            eventos.append((instante, 'release', keysym))
        maximo_simultaneo = max(maximo_simultaneo, len(pressionadas))
        janela['-ATIVAS-'].update(' '.join(sorted(pressionadas)) or '—')
        janela['-MAX-'].update(str(maximo_simultaneo))
        janela['-LOG-'].update('\n'.join(
            f'{t:10.1f}ms  {tipo:7s}  {k}' for t, tipo, k in eventos[-12:]))

janela.close()

# Auto-repeat: um release seguido de press da MESMA tecla em menos de 50 ms.
repeticoes = 0
for i in range(len(eventos) - 1):
    t1, tipo1, k1 = eventos[i]
    t2, tipo2, k2 = eventos[i + 1]
    if tipo1 == 'release' and tipo2 == 'press' and k1 == k2 and (t2 - t1) < 50:
        repeticoes += 1

with open('docs/superpowers/plans/sonda-teclas-resultado.md', 'w', encoding='utf-8') as f:
    f.write('# Resultado da sonda de teclas\n\n')
    f.write(f'- Máximo de teclas simultâneas reportadas: **{maximo_simultaneo}**\n')
    f.write(f'- Pares release+press da mesma tecla em <50 ms (auto-repeat): **{repeticoes}**\n')
    f.write(f'- Total de eventos capturados: {len(eventos)}\n\n')
    f.write('Se o máximo simultâneo for **4 ou mais**, o teste de mãos de 4 teclas funciona\n')
    f.write('neste teclado. Se for menor, a Task 14 precisa entrar já com o modo sequencial\n')
    f.write('como caminho principal, não como alternativa.\n\n')
    f.write('Se houver repetições de auto-repeat, o filtro de 50 ms da Task 5 é obrigatório.\n')
print(f'máximo simultâneo: {maximo_simultaneo} | auto-repeat detectado: {repeticoes}')
```

- [ ] **Step 2: Rodar a sonda no teclado real**

Run: `.venv/bin/python tools/sonda_teclas.py`

Segure `a s d f` juntas por 2 segundos. Solte. Segure `j k l` mais a quarta tecla da base (`;` no US, `ç` no ABNT2). Solte. Segure `f` sozinha por 3 segundos (para provocar auto-repeat). Clique em **Encerrar e gravar relatório**.

Expected: a janela mostra as teclas acendendo em "Pressionadas agora" e o contador de máximo simultâneo chegando a 4.

- [ ] **Step 3: Ler o relatório e decidir**

Run: `cat docs/superpowers/plans/sonda-teclas-resultado.md`

Expected: `Máximo de teclas simultâneas reportadas: 4` (ou mais).

Se vier **menor que 4**, pare e avise: a Task 14 muda de desenho (sequencial vira o caminho principal). Se vier 4 ou mais, siga.

- [ ] **Step 4: Commit**

```bash
git add tools/sonda_teclas.py docs/superpowers/plans/sonda-teclas-resultado.md
git commit -m "sonda: mede rollover e auto-repeat do teclado real antes do teste de maos"
```

---

### Task 2: Infra de testes e WPM

**Files:**
- Create: `requirements-dev.txt`
- Create: `pytest.ini`
- Create: `metricas.py`
- Create: `tests/test_metricas.py`

**Interfaces:**
- Consumes: nada
- Produces:
  - `metricas.wpm(caracteres: int, segundos: float) -> float`
  - `metricas.wpm_liquido(caracteres: int, segundos: float, erros: int) -> float`

- [ ] **Step 1: Criar a infraestrutura de teste**

`requirements-dev.txt`:

```
pytest==9.0.3
```

`pytest.ini`:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
```

Run: `.venv/bin/python -m pip install -r requirements-dev.txt`
Expected: `Successfully installed pytest-9.0.3`

- [ ] **Step 2: Escrever o teste que falha**

`tests/test_metricas.py`:

```python
"""Testes das métricas puras — nada aqui importa GUI."""
import metricas


def test_wpm_usa_padrao_de_cinco_caracteres_por_palavra():
    # 60 caracteres = 12 "palavras"; em 60 segundos dá 12 WPM
    assert metricas.wpm(60, 60.0) == 12.0


def test_wpm_com_duracao_zero_nao_divide_por_zero():
    assert metricas.wpm(50, 0.0) == 0.0


def test_wpm_com_texto_vazio_e_zero():
    assert metricas.wpm(0, 30.0) == 0.0


def test_wpm_liquido_desconta_erros_por_minuto():
    # 60 caracteres em 60s = 12 WPM bruto; 2 erros em 1 minuto tira 2
    assert metricas.wpm_liquido(60, 60.0, 2) == 10.0


def test_wpm_liquido_tem_piso_em_zero():
    # erros demais não podem gerar WPM negativo
    assert metricas.wpm_liquido(60, 60.0, 99) == 0.0
```

- [ ] **Step 3: Rodar para confirmar que falha**

Run: `.venv/bin/python -m pytest tests/test_metricas.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'metricas'`

- [ ] **Step 4: Implementar o mínimo**

`metricas.py`:

```python
"""Métricas do treino, sem nenhuma dependência de interface.

Separado da janela de propósito: é a parte que dá para testar sozinha, e é onde
mora a decisão do que conta como bom desempenho.
"""

# Padrão da área: uma "palavra" são 5 caracteres, independente do idioma.
CARACTERES_POR_PALAVRA = 5


def wpm(caracteres, segundos):
    """Palavras por minuto brutas. Duração zero devolve zero em vez de estourar."""
    if segundos <= 0 or caracteres <= 0:
        return 0.0
    palavras = caracteres / CARACTERES_POR_PALAVRA
    return palavras / (segundos / 60.0)


def wpm_liquido(caracteres, segundos, erros):
    """WPM descontando um erro por minuto para cada erro não corrigido.

    Piso em zero: errar muito significa desempenho nulo, não negativo. No Modo
    Lição o líquido é sempre igual ao bruto, porque a trava impede que caractere
    errado entre no texto — lá quem mede qualidade é o tropeço.
    """
    if segundos <= 0:
        return 0.0
    return max(0.0, wpm(caracteres, segundos) - erros / (segundos / 60.0))
```

- [ ] **Step 5: Rodar para confirmar que passa**

Run: `.venv/bin/python -m pytest tests/test_metricas.py -v`
Expected: `5 passed`

- [ ] **Step 6: Commit**

```bash
git add requirements-dev.txt pytest.ini metricas.py tests/test_metricas.py
git commit -m "metricas: WPM bruto e liquido, com os primeiros testes do projeto"
```

---

### Task 3: Regularidade do ritmo

O índice que reprova quem caça a tecla com o olho.

**Files:**
- Modify: `metricas.py`
- Modify: `tests/test_metricas.py`

**Interfaces:**
- Consumes: `metricas` da Task 2
- Produces: `metricas.regularidade(intervalos_ms: list[float]) -> float | None`

- [ ] **Step 1: Escrever os testes que falham**

Acrescentar ao fim de `tests/test_metricas.py`:

```python
def test_regularidade_perfeita_quando_o_ritmo_e_constante():
    # 3 de aquecimento descartadas + 12 intervalos iguais
    assert metricas.regularidade([200.0] * 15) == 1.0


def test_regularidade_ignora_uma_pausa_isolada_longa():
    # Uma pausa de 2s no meio (o telefone tocou) derruba o índice, mas pouco:
    # 1 parada em 12 intervalos contados.
    intervalos = [200.0] * 15
    intervalos[8] = 2000.0
    assert metricas.regularidade(intervalos) == round(1 - 1 / 12, 4)


def test_regularidade_usa_mediana_e_nao_media():
    # Com média, a pausa de 5s puxaria o limiar para cima e nenhuma parada
    # seria detectada. Com mediana, a parada aparece.
    intervalos = [100.0] * 15
    intervalos[7] = 5000.0
    assert metricas.regularidade(intervalos) < 1.0


def test_regularidade_descarta_as_tres_primeiras_teclas():
    # Reação inicial lenta não é hesitação: as 3 primeiras não contam.
    intervalos = [3000.0, 3000.0, 3000.0] + [200.0] * 12
    assert metricas.regularidade(intervalos) == 1.0


def test_regularidade_sem_intervalos_suficientes_e_indefinida():
    # Exercício curto demais não recebe índice — e não reprova ninguém.
    assert metricas.regularidade([200.0] * 12) is None


def test_regularidade_com_mediana_zero_e_indefinida():
    # Caso degenerado (relógio sem resolução): não inventa nota.
    assert metricas.regularidade([0.0] * 20) is None
```

- [ ] **Step 2: Rodar para confirmar que falha**

Run: `.venv/bin/python -m pytest tests/test_metricas.py -k regularidade -v`
Expected: FAIL com `AttributeError: module 'metricas' has no attribute 'regularidade'`

- [ ] **Step 3: Implementar**

Acrescentar ao fim de `metricas.py`:

```python
import statistics

# As primeiras teclas de um exercício medem tempo de reação, não hesitação.
TECLAS_DE_AQUECIMENTO = 3
# Abaixo disso a amostra é pequena demais para significar alguma coisa.
MINIMO_DE_INTERVALOS = 10
# Intervalo acima de 3x a mediana é "parada": o olho foi procurar a tecla.
FATOR_DE_PARADA = 3.0


def regularidade(intervalos_ms):
    """Proporção de teclas digitadas sem parada para procurar a tecla.

    Devolve de 0 a 1, ou None quando a amostra é pequena demais para dizer
    qualquer coisa — nesse caso o exercício não reprova por ritmo.

    Usa a MEDIANA, não a média: uma única pausa longa (o telefone tocou)
    arrastaria a média e reprovaria alguém que digita bem.
    """
    contados = intervalos_ms[TECLAS_DE_AQUECIMENTO:]
    if len(contados) < MINIMO_DE_INTERVALOS:
        return None
    mediana = statistics.median(contados)
    if mediana <= 0:
        return None
    limite = mediana * FATOR_DE_PARADA
    paradas = sum(1 for i in contados if i > limite)
    return round(1 - paradas / len(contados), 4)
```

- [ ] **Step 4: Rodar para confirmar que passa**

Run: `.venv/bin/python -m pytest tests/test_metricas.py -v`
Expected: `11 passed`

- [ ] **Step 5: Commit**

```bash
git add metricas.py tests/test_metricas.py
git commit -m "metricas: indice de regularidade do ritmo por mediana dos intervalos"
```

---

### Task 4: Tropeços e resumo por tecla

**Files:**
- Modify: `metricas.py`
- Modify: `tests/test_metricas.py`

**Interfaces:**
- Consumes: `metricas` das Tasks 2-3
- Produces:
  - `metricas.Batida(esperado: str, digitado: str, ms: float)` — dataclass congelada
  - `metricas.tropecos(batidas: list[Batida]) -> int`
  - `metricas.resumo_por_tecla(batidas: list[Batida]) -> dict[str, dict]`

- [ ] **Step 1: Escrever os testes que falham**

Acrescentar ao fim de `tests/test_metricas.py`:

```python
def test_tropecos_conta_cada_tecla_errada():
    batidas = [
        metricas.Batida('a', 'a', 200.0),
        metricas.Batida('s', 'd', 300.0),
        metricas.Batida('s', 's', 250.0),
    ]
    assert metricas.tropecos(batidas) == 1


def test_resumo_por_tecla_agrupa_pelo_caractere_esperado():
    batidas = [
        metricas.Batida('a', 'a', 200.0),
        metricas.Batida('a', 's', 400.0),
        metricas.Batida('a', 'a', 300.0),
    ]
    resumo = metricas.resumo_por_tecla(batidas)
    assert resumo['a']['acertos'] == 2
    assert resumo['a']['erros'] == 1
    assert resumo['a']['ms_medio'] == 300


def test_resumo_registra_o_que_foi_digitado_no_lugar():
    # É esse par que revela dedo trocado: esperava j, saiu k = médio no lugar
    # do indicador.
    batidas = [
        metricas.Batida('j', 'k', 400.0),
        metricas.Batida('j', 'k', 380.0),
        metricas.Batida('j', 'h', 350.0),
    ]
    resumo = metricas.resumo_por_tecla(batidas)
    assert resumo['j']['confusoes'] == {'k': 2, 'h': 1}


def test_resumo_de_lista_vazia_e_dicionario_vazio():
    assert metricas.resumo_por_tecla([]) == {}
```

- [ ] **Step 2: Rodar para confirmar que falha**

Run: `.venv/bin/python -m pytest tests/test_metricas.py -k "tropecos or resumo" -v`
Expected: FAIL com `AttributeError: module 'metricas' has no attribute 'Batida'`

- [ ] **Step 3: Implementar**

Acrescentar no topo de `metricas.py`, junto dos outros imports:

```python
from dataclasses import dataclass
```

E ao fim do arquivo:

```python
@dataclass(frozen=True)
class Batida:
    """Uma tecla cobrada pelo exercício e o que o usuário respondeu.

    `ms` é o intervalo desde a batida anterior — é dele que sai a regularidade.
    """
    esperado: str
    digitado: str
    ms: float


def tropecos(batidas):
    """Quantas vezes o usuário digitou a tecla errada ao longo do exercício.

    Diferente de "erros no texto final": corrigir depois não apaga o tropeço,
    porque o que se está medindo é o caminho, não o produto.
    """
    return sum(1 for b in batidas if b.esperado != b.digitado)


def resumo_por_tecla(batidas):
    """Agrupa as batidas pelo caractere ESPERADO.

    Devolve, por tecla: acertos, erros, tempo médio de resposta e `confusoes`
    — o que foi digitado no lugar e quantas vezes. É a matéria-prima do
    diagnóstico por dedo.
    """
    resumo = {}
    for b in batidas:
        entrada = resumo.setdefault(
            b.esperado, {'acertos': 0, 'erros': 0, 'ms_total': 0.0, 'confusoes': {}})
        entrada['ms_total'] += b.ms
        if b.esperado == b.digitado:
            entrada['acertos'] += 1
        else:
            entrada['erros'] += 1
            entrada['confusoes'][b.digitado] = entrada['confusoes'].get(b.digitado, 0) + 1
    for entrada in resumo.values():
        total = entrada['acertos'] + entrada['erros']
        entrada['ms_medio'] = round(entrada.pop('ms_total') / total) if total else 0
    return resumo
```

- [ ] **Step 4: Rodar para confirmar que passa**

Run: `.venv/bin/python -m pytest tests/test_metricas.py -v`
Expected: `15 passed`

- [ ] **Step 5: Commit**

```bash
git add metricas.py tests/test_metricas.py
git commit -m "metricas: tropecos e resumo por tecla com as confusoes que revelam dedo trocado"
```

---

### Task 5: Rastreador de teclas pressionadas

O filtro de auto-repeat, isolado como lógica pura para poder ser testado sem abrir janela.

**Files:**
- Create: `teclas_pressionadas.py`
- Create: `tests/test_teclas_pressionadas.py`

**Interfaces:**
- Consumes: o relatório da Task 1
- Produces:
  - `teclas_pressionadas.Rastreador(ms_auto_repeat: float = 50.0)`
  - `.pressionou(keysym: str, ms: float) -> None`
  - `.soltou(keysym: str, ms: float) -> None`
  - `.ativas(agora_ms: float) -> set[str]`

- [ ] **Step 1: Escrever os testes que falham**

`tests/test_teclas_pressionadas.py`:

```python
"""Testes do filtro de auto-repeat, sem abrir janela nenhuma."""
import teclas_pressionadas


def test_tecla_pressionada_fica_ativa():
    r = teclas_pressionadas.Rastreador()
    r.pressionou('a', 0.0)
    assert r.ativas(10.0) == {'a'}


def test_quatro_teclas_simultaneas():
    r = teclas_pressionadas.Rastreador()
    for i, k in enumerate('asdf'):
        r.pressionou(k, i * 5.0)
    assert r.ativas(30.0) == {'a', 's', 'd', 'f'}


def test_soltar_de_verdade_desativa_a_tecla():
    r = teclas_pressionadas.Rastreador()
    r.pressionou('a', 0.0)
    r.soltou('a', 100.0)
    assert r.ativas(200.0) == set()


def test_auto_repeat_nao_desativa_a_tecla():
    # X11 segurando a tecla: release e press colados. Ingenuamente pareceria
    # que o usuário soltou, e o teste de mãos piscaria sem nunca fechar.
    r = teclas_pressionadas.Rastreador()
    r.pressionou('f', 0.0)
    r.soltou('f', 500.0)
    r.pressionou('f', 510.0)      # 10 ms depois: é auto-repeat
    assert r.ativas(600.0) == {'f'}


def test_soltar_so_vale_depois_da_janela_de_auto_repeat():
    r = teclas_pressionadas.Rastreador()
    r.pressionou('f', 0.0)
    r.soltou('f', 500.0)
    assert r.ativas(520.0) == {'f'}     # ainda na dúvida, mantém
    assert r.ativas(560.0) == set()     # passou dos 50 ms, soltou mesmo


def test_pressionar_de_novo_nao_reinicia_o_instante():
    r = teclas_pressionadas.Rastreador()
    r.pressionou('a', 0.0)
    r.pressionou('a', 100.0)
    assert r.desde('a') == 0.0


def test_soltar_tecla_que_nunca_foi_pressionada_e_ignorado():
    r = teclas_pressionadas.Rastreador()
    r.soltou('z', 10.0)
    assert r.ativas(100.0) == set()
```

- [ ] **Step 2: Rodar para confirmar que falha**

Run: `.venv/bin/python -m pytest tests/test_teclas_pressionadas.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'teclas_pressionadas'`

- [ ] **Step 3: Implementar**

`teclas_pressionadas.py`:

```python
"""Quais teclas estão pressionadas AGORA, apesar do auto-repeat do sistema.

O teste de mãos precisa saber que quatro teclas estão seguradas ao mesmo tempo.
O problema é que o X11, ao segurar uma tecla, gera KeyRelease e KeyPress
repetidos e colados — quem acreditar no KeyRelease conclui que o usuário soltou.

A solução é não acreditar num soltar imediatamente: ele fica "em dúvida" por
uma janela curta, e um novo pressionar da mesma tecla dentro dela cancela o
soltar. É por isso que `ativas()` precisa saber que horas são.

Esta classe é lógica pura, alimentada por quem escuta os eventos do tkinter —
o que permite testar o comportamento inteiro sem abrir janela.
"""

# Auto-repeat típico do X11 recoloca a tecla em bem menos que isso.
MS_AUTO_REPEAT = 50.0


class Rastreador:
    def __init__(self, ms_auto_repeat=MS_AUTO_REPEAT):
        self._ms_auto_repeat = ms_auto_repeat
        self._ativas = {}      # keysym -> instante do primeiro press
        self._soltando = {}    # keysym -> instante do release ainda em dúvida

    def pressionou(self, keysym, ms):
        # Um press cancela o soltar em dúvida: era auto-repeat, não o usuário.
        self._soltando.pop(keysym, None)
        self._ativas.setdefault(keysym, ms)

    def soltou(self, keysym, ms):
        if keysym in self._ativas:
            self._soltando[keysym] = ms

    def ativas(self, agora_ms):
        """Teclas seguradas neste instante, já resolvidas as dúvidas vencidas."""
        for keysym, instante in list(self._soltando.items()):
            if agora_ms - instante >= self._ms_auto_repeat:
                del self._soltando[keysym]
                self._ativas.pop(keysym, None)
        return set(self._ativas)

    def desde(self, keysym):
        """Instante em que a tecla começou a ser segurada, ou None."""
        return self._ativas.get(keysym)
```

- [ ] **Step 4: Rodar para confirmar que passa**

Run: `.venv/bin/python -m pytest tests/test_teclas_pressionadas.py -v`
Expected: `7 passed`

- [ ] **Step 5: Commit**

```bash
git add teclas_pressionadas.py tests/test_teclas_pressionadas.py
git commit -m "teclas: rastreador de teclas simultaneas com filtro de auto-repeat"
```

---

### Task 6: Caminho portátil do histórico

**Files:**
- Create: `historico.py`
- Create: `tests/test_historico.py`

**Interfaces:**
- Consumes: nada
- Produces: `historico.resolver_caminho(pasta_executavel: Path, pasta_usuario: Path) -> tuple[Path, bool]` — devolve `(caminho_do_arquivo, caiu_para_usuario)`

- [ ] **Step 1: Escrever os testes que falham**

`tests/test_historico.py`:

```python
"""Testes do histórico — usa tmp_path, nunca escreve no histórico de verdade."""
import os

import pytest

import historico


def test_grava_ao_lado_do_executavel_quando_da(tmp_path):
    pasta_exe = tmp_path / 'app'
    pasta_exe.mkdir()
    pasta_usuario = tmp_path / 'home'
    caminho, caiu = historico.resolver_caminho(pasta_exe, pasta_usuario)
    assert caminho == pasta_exe / 'dados' / 'progresso.jsonl'
    assert caiu is False


@pytest.mark.skipif(os.geteuid() == 0, reason='root ignora permissão de escrita')
def test_cai_para_a_pasta_do_usuario_quando_e_somente_leitura(tmp_path):
    pasta_exe = tmp_path / 'app'
    pasta_exe.mkdir()
    pasta_exe.chmod(0o555)
    pasta_usuario = tmp_path / 'home'
    try:
        caminho, caiu = historico.resolver_caminho(pasta_exe, pasta_usuario)
    finally:
        pasta_exe.chmod(0o755)
    assert caminho == pasta_usuario / 'progresso.jsonl'
    assert caiu is True


def test_cria_a_pasta_de_destino(tmp_path):
    pasta_exe = tmp_path / 'app'
    pasta_exe.mkdir()
    caminho, _ = historico.resolver_caminho(pasta_exe, tmp_path / 'home')
    assert caminho.parent.is_dir()
```

- [ ] **Step 2: Rodar para confirmar que falha**

Run: `.venv/bin/python -m pytest tests/test_historico.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'historico'`

- [ ] **Step 3: Implementar**

`historico.py`:

```python
"""Onde o progresso mora e como ele é lido e gravado.

O aplicativo é portátil: o padrão é gravar ao lado do executável, para o
progresso viajar junto quando a pasta for copiada para um pendrive. Só quando
esse lugar é somente-leitura — programa instalado em Arquivos de Programas, por
exemplo — o histórico cai para a pasta do usuário.

O formato é JSON Lines, uma linha por exercício, sempre acrescentando. Foi
escolhido sobre SQLite porque, com um usuário e sem escrita concorrente, o banco
cobraria migração de esquema a cada campo novo sem entregar nada perceptível.
"""
import json
import os
import sys
from pathlib import Path

NOME_DO_ARQUIVO = 'progresso.jsonl'


def resolver_caminho(pasta_executavel, pasta_usuario):
    """Decide onde gravar. Devolve (caminho, caiu_para_a_pasta_do_usuario)."""
    destino = Path(pasta_executavel) / 'dados'
    try:
        destino.mkdir(parents=True, exist_ok=True)
        # mkdir passar não garante escrita: a pasta pode já existir sem permissão.
        if not os.access(destino, os.W_OK):
            raise PermissionError(destino)
        return destino / NOME_DO_ARQUIVO, False
    except (OSError, PermissionError):
        alternativo = Path(pasta_usuario)
        alternativo.mkdir(parents=True, exist_ok=True)
        return alternativo / NOME_DO_ARQUIVO, True


def pasta_do_executavel():
    """Onde o programa está: ao lado do .exe empacotado, ou do fonte."""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent


def pasta_do_usuario():
    """~/.touchtypingtrainer no Linux, %APPDATA%\\TouchTypingTrainer no Windows."""
    if os.name == 'nt':
        base = os.environ.get('APPDATA') or os.path.expanduser('~')
        return Path(base) / 'TouchTypingTrainer'
    return Path(os.path.expanduser('~')) / '.touchtypingtrainer'
```

- [ ] **Step 4: Rodar para confirmar que passa**

Run: `.venv/bin/python -m pytest tests/test_historico.py -v`
Expected: `3 passed`

- [ ] **Step 5: Commit**

```bash
git add historico.py tests/test_historico.py
git commit -m "historico: caminho portatil ao lado do executavel com queda para a pasta do usuario"
```

---

### Task 7: Gravação e leitura do JSONL

**Files:**
- Modify: `historico.py`
- Modify: `tests/test_historico.py`

**Interfaces:**
- Consumes: `historico` da Task 6
- Produces:
  - `historico.gravar(registro: dict, caminho: Path) -> None`
  - `historico.ler(caminho: Path) -> list[dict]`
  - `historico.VERSAO_DO_FORMATO = 1`

- [ ] **Step 1: Escrever os testes que falham**

Acrescentar ao fim de `tests/test_historico.py`:

```python
def test_gravar_acrescenta_sem_reescrever(tmp_path):
    arquivo = tmp_path / 'progresso.jsonl'
    historico.gravar({'modo': 'licao', 'nivel': 'base-esquerda'}, arquivo)
    historico.gravar({'modo': 'livre', 'nivel': None}, arquivo)
    registros = historico.ler(arquivo)
    assert [r['modo'] for r in registros] == ['licao', 'livre']


def test_gravar_carimba_a_versao_do_formato(tmp_path):
    arquivo = tmp_path / 'progresso.jsonl'
    historico.gravar({'modo': 'livre'}, arquivo)
    assert historico.ler(arquivo)[0]['v'] == historico.VERSAO_DO_FORMATO


def test_linha_corrompida_e_pulada_sem_derrubar_o_resto(tmp_path):
    arquivo = tmp_path / 'progresso.jsonl'
    historico.gravar({'modo': 'licao'}, arquivo)
    with open(arquivo, 'a', encoding='utf-8') as f:
        f.write('{isto nao e json\n')
    historico.gravar({'modo': 'livre'}, arquivo)
    registros = historico.ler(arquivo)
    assert [r['modo'] for r in registros] == ['licao', 'livre']


def test_ler_arquivo_inexistente_devolve_lista_vazia(tmp_path):
    assert historico.ler(tmp_path / 'nao-existe.jsonl') == []


def test_acentos_sobrevivem_a_ida_e_volta(tmp_path):
    arquivo = tmp_path / 'progresso.jsonl'
    historico.gravar({'alvo': 'ação coração ç'}, arquivo)
    assert historico.ler(arquivo)[0]['alvo'] == 'ação coração ç'


def test_preferencias_inexistentes_sao_dicionario_vazio(tmp_path):
    assert historico.ler_preferencias(tmp_path / 'progresso.jsonl') == {}


def test_preferencia_gravada_sobrevive(tmp_path):
    arquivo = tmp_path / 'progresso.jsonl'
    historico.gravar_preferencia(arquivo, 'teclado_sem_rollover', True)
    assert historico.ler_preferencias(arquivo)['teclado_sem_rollover'] is True


def test_preferencia_corrompida_nao_derruba(tmp_path):
    arquivo = tmp_path / 'progresso.jsonl'
    (tmp_path / 'preferencias.json').write_text('{quebrado', encoding='utf-8')
    assert historico.ler_preferencias(arquivo) == {}
```

- [ ] **Step 2: Rodar para confirmar que falha**

Run: `.venv/bin/python -m pytest tests/test_historico.py -k "gravar or corrompida or inexistente or acentos" -v`
Expected: FAIL com `AttributeError: module 'historico' has no attribute 'gravar'`

- [ ] **Step 3: Implementar**

Acrescentar ao fim de `historico.py`:

```python
# Sobe quando o significado de um campo mudar. Campo novo NÃO exige subir:
# versão antiga simplesmente ignora o que não conhece.
VERSAO_DO_FORMATO = 1


def gravar(registro, caminho):
    """Acrescenta um exercício ao histórico. Nunca reescreve o que já está lá."""
    linha = dict(registro)
    linha['v'] = VERSAO_DO_FORMATO
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, 'a', encoding='utf-8') as f:
        f.write(json.dumps(linha, ensure_ascii=False) + '\n')


def ler(caminho):
    """Lê o histórico inteiro, pulando linha ilegível em vez de estourar.

    Arquivo truncado por queda de energia ou editado à mão não pode invalidar
    todo o progresso — a linha ruim é descartada e o resto continua valendo.
    """
    caminho = Path(caminho)
    if not caminho.exists():
        return []
    registros = []
    with open(caminho, 'r', encoding='utf-8') as f:
        for numero, linha in enumerate(f, start=1):
            linha = linha.strip()
            if not linha:
                continue
            try:
                registros.append(json.loads(linha))
            except json.JSONDecodeError:
                print(f'historico: linha {numero} ilegivel, pulada', file=sys.stderr)
    return registros


def _caminho_das_preferencias(caminho_do_progresso):
    return Path(caminho_do_progresso).parent / 'preferencias.json'


def ler_preferencias(caminho_do_progresso):
    """Preferências que não são exercício — hoje só o limite do teclado.

    Arquivo ausente ou ilegível vira dicionário vazio: preferência é conforto,
    nunca motivo para o programa não abrir.
    """
    arquivo = _caminho_das_preferencias(caminho_do_progresso)
    if not arquivo.exists():
        return {}
    try:
        with open(arquivo, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def gravar_preferencia(caminho_do_progresso, chave, valor):
    """Grava uma preferência preservando as outras."""
    arquivo = _caminho_das_preferencias(caminho_do_progresso)
    atuais = ler_preferencias(caminho_do_progresso)
    atuais[chave] = valor
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    with open(arquivo, 'w', encoding='utf-8') as f:
        json.dump(atuais, f, ensure_ascii=False, indent=2)
```

- [ ] **Step 4: Rodar para confirmar que passa**

Run: `.venv/bin/python -m pytest tests/test_historico.py -v`
Expected: `11 passed`

- [ ] **Step 5: Commit**

```bash
git add historico.py tests/test_historico.py
git commit -m "historico: gravacao JSONL tolerante a linha corrompida e preferencias do teclado"
```

---

### Task 8: Layouts de teclado e mapa tecla→dedo

O dado que hoje não existe: no projeto atual a relação dedo↔tecla só está como prosa no `i18n.py` e como gabarito da linha QWERTY no `keyboards.py`, nenhum dos dois consultável por código.

**Files:**
- Create: `layouts.py`
- Create: `tests/test_layouts.py`

**Interfaces:**
- Consumes: nada
- Produces:
  - `layouts.LAYOUT_POR_IDIOMA = {'pt': 'abnt2', 'en': 'us', 'it': 'it'}`
  - `layouts.TeclaFisica(caractere, linha, x, largura, mao, dedo)` — dataclass congelada
  - `layouts.teclas(nome_layout) -> tuple[TeclaFisica, ...]`
  - `layouts.dedo_de(caractere, nome_layout) -> tuple[str, str] | None` — `(mao, dedo)`
  - `layouts.teclas_base(nome_layout) -> tuple[tuple[str, ...], tuple[str, ...]]`
  - `layouts.caracteres_da_linha(nome_layout, numero) -> str`
  - `layouts.retangulos(nome_layout, largura_px, altura_px) -> dict[str, tuple[float, float, float, float]]`

- [ ] **Step 1: Escrever os testes que falham**

`tests/test_layouts.py`:

```python
"""Testes dos três layouts e do mapa tecla→dedo."""
import pytest

import layouts

TODOS = ('abnt2', 'us', 'it')


@pytest.mark.parametrize('nome', TODOS)
def test_toda_tecla_tem_mao_e_dedo(nome):
    for tecla in layouts.teclas(nome):
        assert tecla.mao in ('esquerda', 'direita'), tecla
        assert tecla.dedo in ('minimo', 'anelar', 'medio', 'indicador'), tecla


@pytest.mark.parametrize('nome', TODOS)
def test_nao_ha_caractere_repetido_no_layout(nome):
    caracteres = [t.caractere for t in layouts.teclas(nome)]
    assert len(caracteres) == len(set(caracteres))


@pytest.mark.parametrize('nome', TODOS)
def test_linha_base_tem_asdf_na_esquerda(nome):
    esquerda, _ = layouts.teclas_base(nome)
    assert esquerda == ('a', 's', 'd', 'f')


def test_a_quarta_tecla_da_base_direita_muda_por_layout():
    assert layouts.teclas_base('us')[1] == ('j', 'k', 'l', ';')
    assert layouts.teclas_base('abnt2')[1] == ('j', 'k', 'l', 'ç')
    assert layouts.teclas_base('it')[1] == ('j', 'k', 'l', 'ò')


def test_dedo_da_linha_base_segue_o_padrao_do_toque():
    assert layouts.dedo_de('a', 'us') == ('esquerda', 'minimo')
    assert layouts.dedo_de('f', 'us') == ('esquerda', 'indicador')
    assert layouts.dedo_de('g', 'us') == ('esquerda', 'indicador')
    assert layouts.dedo_de('j', 'us') == ('direita', 'indicador')
    assert layouts.dedo_de('k', 'us') == ('direita', 'medio')
    assert layouts.dedo_de(';', 'us') == ('direita', 'minimo')


def test_dedo_de_caractere_desconhecido_e_none():
    assert layouts.dedo_de('€', 'us') is None


def test_ce_cedilha_so_existe_no_abnt2():
    assert layouts.dedo_de('ç', 'abnt2') == ('direita', 'minimo')
    assert layouts.dedo_de('ç', 'us') is None


def test_retangulos_cabem_dentro_da_area_pedida():
    rets = layouts.retangulos('us', 1000.0, 300.0)
    assert rets['a'][0] >= 0 and rets['a'][1] >= 0
    for x0, y0, x1, y1 in rets.values():
        assert 0 <= x0 < x1 <= 1000.0
        assert 0 <= y0 < y1 <= 300.0


def test_linha_de_baixo_comeca_mais_a_direita_que_a_de_cima():
    # O escalonamento das linhas é o que faz o desenho parecer um teclado.
    rets = layouts.retangulos('us', 1000.0, 300.0)
    assert rets['z'][0] > rets['q'][0] > rets['1'][0]


def test_retangulos_acompanham_a_area_pedida():
    # O teclado precisa redesenhar proporcional quando a janela muda de tamanho.
    pequeno = layouts.retangulos('us', 500.0, 150.0)
    grande = layouts.retangulos('us', 1000.0, 300.0)
    assert grande['a'][2] > pequeno['a'][2]


def test_caracteres_da_linha_devolve_a_linha_base():
    assert layouts.caracteres_da_linha('us', 2) == "asdfghjkl;'"
```

- [ ] **Step 2: Rodar para confirmar que falha**

Run: `.venv/bin/python -m pytest tests/test_layouts.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'layouts'`

- [ ] **Step 3: Implementar**

`layouts.py`:

```python
"""Os três layouts físicos e a quem cada tecla pertence.

Substitui os desenhos ASCII do `keyboards.py`. A diferença que importa não é
estética: aqui a relação tecla→dedo é DADO consultável, e era só prosa antes.

O truque que mantém isto curto: o padrão de dedos por posição é o mesmo nos três
layouts — o que muda é o caractere que sai em cada posição. Por isso cada linha
é descrita por três strings do mesmo comprimento: os caracteres, a mão e o dedo.
"""
from dataclasses import dataclass

LAYOUT_POR_IDIOMA = {'pt': 'abnt2', 'en': 'us', 'it': 'it'}

_MAO = {'E': 'esquerda', 'D': 'direita'}
_DEDO = {'P': 'minimo', 'R': 'anelar', 'M': 'medio', 'I': 'indicador'}

# Deslocamento de cada linha, em larguras de tecla. É o escalonamento que faz o
# desenho parecer um teclado de verdade.
_DESLOCAMENTOS = (0.0, 1.5, 1.75, 2.25)

# (caracteres, mãos, dedos) por linha: números, cima, base, baixo.
_LINHAS = {
    'abnt2': (
        ("'1234567890-=", 'EEEEEEDDDDDDD', 'PPRMIIIIMRPPP'),
        ('qwertyuiop´[', 'EEEEEDDDDDDD', 'PRMIIIIMRPPP'),
        ('asdfghjklç~]', 'EEEEEDDDDDDD', 'PRMIIIIMRPPP'),
        ('zxcvbnm,.;/', 'EEEEEDDDDDD', 'PRMIIIIMRPP'),
    ),
    'us': (
        ('`1234567890-=', 'EEEEEEDDDDDDD', 'PPRMIIIIMRPPP'),
        ('qwertyuiop[]', 'EEEEEDDDDDDD', 'PRMIIIIMRPPP'),
        ("asdfghjkl;'", 'EEEEEDDDDDD', 'PRMIIIIMRPP'),
        ('zxcvbnm,./', 'EEEEEDDDDD', 'PRMIIIIMRP'),
    ),
    'it': (
        ("\\1234567890'ì", 'EEEEEEDDDDDDD', 'PPRMIIIIMRPPP'),
        ('qwertyuiopè+', 'EEEEEDDDDDDD', 'PRMIIIIMRPPP'),
        ('asdfghjklòàù', 'EEEEEDDDDDDD', 'PRMIIIIMRPPP'),
        ('zxcvbnm,.-', 'EEEEEDDDDD', 'PRMIIIIMRP'),
    ),
}


@dataclass(frozen=True)
class TeclaFisica:
    caractere: str
    linha: int          # 0 = números, 1 = cima, 2 = base, 3 = baixo
    x: float            # posição em larguras de tecla, a partir da esquerda
    largura: float      # em larguras de tecla
    mao: str            # 'esquerda' | 'direita'
    dedo: str           # 'minimo' | 'anelar' | 'medio' | 'indicador'


def teclas(nome_layout):
    """Todas as teclas de caractere do layout, já com mão e dedo atribuídos."""
    resultado = []
    for numero_da_linha, (caracteres, maos, dedos) in enumerate(_LINHAS[nome_layout]):
        assert len(caracteres) == len(maos) == len(dedos), \
            f'{nome_layout} linha {numero_da_linha}: as três strings têm de ter o mesmo tamanho'
        deslocamento = _DESLOCAMENTOS[numero_da_linha]
        for coluna, caractere in enumerate(caracteres):
            resultado.append(TeclaFisica(
                caractere=caractere, linha=numero_da_linha,
                x=deslocamento + coluna, largura=1.0,
                mao=_MAO[maos[coluna]], dedo=_DEDO[dedos[coluna]]))
    return tuple(resultado)


def dedo_de(caractere, nome_layout):
    """(mão, dedo) da tecla, ou None se o caractere não existe nesse layout.

    Maiúscula é resolvida pela minúscula correspondente: o dedo é o mesmo, o
    que muda é o Shift do mínimo oposto.
    """
    procurado = caractere.lower()
    for tecla in teclas(nome_layout):
        if tecla.caractere == procurado:
            return tecla.mao, tecla.dedo
    return None


def caracteres_da_linha(nome_layout, numero):
    """Os caracteres de uma linha física: 0 números, 1 cima, 2 base, 3 baixo.

    Existe para o `licoes.py` montar os níveis sem espiar a estrutura interna
    daqui — quem define o que é uma linha é este módulo.
    """
    return _LINHAS[nome_layout][numero][0]


def teclas_base(nome_layout):
    """As oito teclas da linha-base: (esquerda, direita).

    A quarta da direita muda por layout — `;` no US, `ç` no ABNT2, `ò` no
    italiano — e é justamente ela que o teste de mãos precisa cobrar certo.
    """
    caracteres = caracteres_da_linha(nome_layout, 2)
    return tuple(caracteres[0:4]), tuple(caracteres[5:9])


def retangulos(nome_layout, largura_px, altura_px):
    """Onde desenhar cada tecla, em pixels, dentro da área dada.

    Devolve {caractere: (x0, y0, x1, y1)} com a origem no canto superior
    esquerdo. Quem desenha não precisa saber nada de layout — só consumir isto.
    """
    todas = teclas(nome_layout)
    colunas = max(t.x + t.largura for t in todas)
    unidade = min(largura_px / colunas, altura_px / len(_LINHAS[nome_layout]))
    return {
        t.caractere: (t.x * unidade, t.linha * unidade,
                      (t.x + t.largura) * unidade, (t.linha + 1) * unidade)
        for t in todas
    }
```

- [ ] **Step 4: Rodar para confirmar que passa**

Run: `.venv/bin/python -m pytest tests/test_layouts.py -v`
Expected: `17 passed`

- [ ] **Step 5: Commit**

```bash
git add layouts.py tests/test_layouts.py
git commit -m "layouts: mapa tecla-dedo dos tres teclados como dado consultavel"
```

---

### Task 9: Currículo dos 12 níveis

**Files:**
- Create: `licoes.py`
- Create: `tests/test_licoes.py`

**Interfaces:**
- Consumes: `layouts` da Task 8
- Produces:
  - `licoes.Nivel(numero, id, teclas_novas, wpm_meta)` — dataclass congelada
  - `licoes.curriculo(nome_layout) -> tuple[Nivel, ...]`
  - `licoes.teclas_liberadas(nome_layout, ate_numero) -> frozenset[str]`
  - `licoes.limite_de_tempo(n_caracteres, wpm_meta) -> float`

- [ ] **Step 1: Escrever os testes que falham**

`tests/test_licoes.py`:

```python
"""Testes do currículo, do gerador de exercício e do critério de aprovação."""
import pytest

import licoes

TODOS = ('abnt2', 'us', 'it')


@pytest.mark.parametrize('nome', TODOS)
def test_curriculo_tem_doze_niveis_numerados_em_ordem(nome):
    niveis = licoes.curriculo(nome)
    assert len(niveis) == 12
    assert [n.numero for n in niveis] == list(range(1, 13))


@pytest.mark.parametrize('nome', TODOS)
def test_meta_de_wpm_nunca_cai_de_um_nivel_para_o_seguinte(nome):
    metas = [n.wpm_meta for n in licoes.curriculo(nome)]
    assert metas == sorted(metas)


def test_primeiro_nivel_e_so_a_base_esquerda():
    assert licoes.curriculo('us')[0].teclas_novas == ('a', 's', 'd', 'f')


def test_segundo_nivel_usa_a_quarta_tecla_do_layout():
    assert licoes.curriculo('us')[1].teclas_novas == ('j', 'k', 'l', ';')
    assert licoes.curriculo('abnt2')[1].teclas_novas == ('j', 'k', 'l', 'ç')


def test_teclas_liberadas_acumulam_dos_niveis_anteriores():
    liberadas = licoes.teclas_liberadas('us', 2)
    assert liberadas == frozenset('asdfjkl;')


def test_nivel_tres_libera_o_espaco():
    assert ' ' in licoes.teclas_liberadas('us', 3)


@pytest.mark.parametrize('nome', TODOS)
def test_toda_tecla_nova_existe_no_layout(nome):
    import layouts
    for nivel in licoes.curriculo(nome):
        for tecla in nivel.teclas_novas:
            if tecla in (' ',) or tecla.isupper() or tecla.isdigit():
                continue
            assert layouts.dedo_de(tecla, nome) is not None, (nome, nivel.id, tecla)


def test_limite_de_tempo_da_o_dobro_do_tempo_da_meta():
    # 60 caracteres = 12 palavras; a 10 WPM levaria 72s; o limite é o dobro.
    assert licoes.limite_de_tempo(60, 10) == pytest.approx(144.0)
```

- [ ] **Step 2: Rodar para confirmar que falha**

Run: `.venv/bin/python -m pytest tests/test_licoes.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'licoes'`

- [ ] **Step 3: Implementar**

`licoes.py`:

```python
"""Currículo do Modo Lição: o que se aprende, em que ordem e quando libera.

As metas de WPM são baixas de propósito nos primeiros níveis. Nessa altura o que
está sendo construído é o caminho do dedo, não velocidade — e meta agressiva
cedo empurra a pessoa de volta a olhar para o teclado, que é o hábito a matar.
"""
from dataclasses import dataclass

import layouts

CARACTERES_POR_PALAVRA = 5
# Folga sobre o tempo que o exercício levaria digitado exatamente na meta.
FOLGA_DO_LIMITE = 2.0


@dataclass(frozen=True)
class Nivel:
    numero: int
    id: str
    teclas_novas: tuple
    wpm_meta: int


# (id, wpm_meta, de onde saem as teclas novas)
_NIVEIS = (
    ('base-esquerda', 10, 'base_esquerda'),
    ('base-direita', 10, 'base_direita'),
    ('base-completa', 12, 'espaco'),
    ('indices-estendidos', 14, 'linha:2:4,5'),
    ('cima-esquerda', 16, 'linha:1:0,5'),
    ('cima-direita', 18, 'linha:1:5,10'),
    ('baixo-esquerda', 20, 'linha:3:0,5'),
    ('baixo-direita', 22, 'linha:3:5,9'),
    ('maiusculas', 25, 'maiusculas'),
    ('numeros', 28, 'linha:0:1,11'),
    ('simbolos', 30, 'simbolos'),
    ('texto-corrido', 35, 'nada'),
)


def _teclas_novas(nome_layout, origem):
    esquerda, direita = layouts.teclas_base(nome_layout)
    if origem == 'base_esquerda':
        return esquerda
    if origem == 'base_direita':
        return direita
    if origem == 'espaco':
        return (' ',)
    if origem == 'maiusculas':
        return tuple(c.upper() for c in esquerda + direita)
    if origem == 'nada':
        return ()
    if origem == 'simbolos':
        # O que sobrou do layout depois de letras, dígitos e espaço.
        ja_vistas = set('abcdefghijklmnopqrstuvwxyz0123456789 ')
        return tuple(t.caractere for t in layouts.teclas(nome_layout)
                     if t.caractere not in ja_vistas)
    if origem.startswith('linha:'):
        _, numero, faixa = origem.split(':')
        inicio, fim = (int(p) for p in faixa.split(','))
        caracteres = layouts.caracteres_da_linha(nome_layout, int(numero))
        return tuple(caracteres[inicio:fim])
    raise ValueError(f'origem desconhecida: {origem}')


def curriculo(nome_layout):
    """Os 12 níveis desse layout, do `asdf` isolado ao texto corrido."""
    return tuple(
        Nivel(numero=i, id=identificador, wpm_meta=meta,
              teclas_novas=_teclas_novas(nome_layout, origem))
        for i, (identificador, meta, origem) in enumerate(_NIVEIS, start=1))


def teclas_liberadas(nome_layout, ate_numero):
    """Tudo que o aluno já pode ver num exercício até esse nível, acumulado."""
    liberadas = set()
    for nivel in curriculo(nome_layout):
        if nivel.numero > ate_numero:
            break
        liberadas.update(nivel.teclas_novas)
    return frozenset(liberadas)


def limite_de_tempo(n_caracteres, wpm_meta):
    """Segundos disponíveis: o dobro do tempo que levaria digitando na meta.

    Deriva da própria meta para não existirem dois números soltos dizendo a
    mesma coisa — quem alcança a meta tem sempre 100% de folga.
    """
    if wpm_meta <= 0 or n_caracteres <= 0:
        return 0.0
    minutos_na_meta = (n_caracteres / CARACTERES_POR_PALAVRA) / wpm_meta
    return minutos_na_meta * 60.0 * FOLGA_DO_LIMITE
```

- [ ] **Step 4: Rodar para confirmar que passa**

Run: `.venv/bin/python -m pytest tests/test_licoes.py -v`
Expected: `14 passed`

- [ ] **Step 5: Commit**

```bash
git add licoes.py tests/test_licoes.py
git commit -m "licoes: curriculo de 12 niveis por layout, com metas e limite de tempo"
```

---

### Task 10: Gerador determinístico de exercício

**Files:**
- Modify: `licoes.py`
- Modify: `tests/test_licoes.py`

**Interfaces:**
- Consumes: `licoes` da Task 9
- Produces:
  - `licoes.gerar_exercicio(nome_layout, numero_do_nivel, semente, grupos=12) -> str`
  - `licoes.filtrar_frases(frases, teclas_permitidas) -> list[str]`

- [ ] **Step 1: Escrever os testes que falham**

Acrescentar ao fim de `tests/test_licoes.py`:

```python
def test_exercicio_so_usa_teclas_ja_liberadas():
    permitidas = licoes.teclas_liberadas('us', 5)
    texto = licoes.gerar_exercicio('us', 5, semente=42)
    assert set(texto) <= permitidas | {' '}


def test_mesma_semente_gera_o_mesmo_exercicio():
    a = licoes.gerar_exercicio('us', 4, semente=7)
    b = licoes.gerar_exercicio('us', 4, semente=7)
    assert a == b


def test_sementes_diferentes_geram_exercicios_diferentes():
    a = licoes.gerar_exercicio('us', 4, semente=7)
    b = licoes.gerar_exercicio('us', 4, semente=8)
    assert a != b


def test_primeiro_nivel_nao_usa_teclas_da_mao_direita():
    texto = licoes.gerar_exercicio('us', 1, semente=1)
    assert set(texto) <= set('asdf ')


def test_nivel_de_maiusculas_produz_maiusculas():
    texto = licoes.gerar_exercicio('us', 9, semente=3)
    assert any(c.isupper() for c in texto)


def test_nivel_de_numeros_produz_digitos():
    texto = licoes.gerar_exercicio('us', 10, semente=3)
    assert any(c.isdigit() for c in texto)


def test_exercicio_nao_e_vazio_em_nenhum_nivel():
    for numero in range(1, 12):
        assert licoes.gerar_exercicio('abnt2', numero, semente=numero).strip()


def test_filtrar_frases_descarta_as_que_usam_tecla_nao_liberada():
    frases = ['dad fads', 'quick brown fox']
    permitidas = licoes.teclas_liberadas('us', 3)
    assert licoes.filtrar_frases(frases, permitidas) == ['dad fads']


def test_filtrar_frases_ignora_diferenca_de_caixa():
    permitidas = licoes.teclas_liberadas('us', 3)
    assert licoes.filtrar_frases(['DAD'], permitidas) == ['DAD']
```

- [ ] **Step 2: Rodar para confirmar que falha**

Run: `.venv/bin/python -m pytest tests/test_licoes.py -k "exercicio or filtrar or maiusculas or numeros" -v`
Expected: FAIL com `AttributeError: module 'licoes' has no attribute 'gerar_exercicio'`

- [ ] **Step 3: Implementar**

Acrescentar no topo de `licoes.py`, junto dos outros imports:

```python
import random
```

E ao fim do arquivo:

```python
# Tamanho dos "grupos" (pseudopalavras) dos níveis de treino puro.
MENOR_GRUPO = 3
MAIOR_GRUPO = 5


def gerar_exercicio(nome_layout, numero_do_nivel, semente, grupos=12):
    """Monta o texto do exercício a partir das teclas já liberadas.

    Determinístico: a mesma semente devolve o mesmo texto, e a semente vai
    gravada no histórico — então um exercício pode ser repetido igual.

    Do nível 12 em diante o texto não é gerado: vem das frases reais, por
    `filtrar_frases`.
    """
    permitidas = teclas_liberadas(nome_layout, numero_do_nivel) - {' '}
    if not permitidas:
        return ''
    sorteio = random.Random(semente)
    alfabeto = sorted(permitidas)
    palavras = []
    for _ in range(grupos):
        tamanho = sorteio.randint(MENOR_GRUPO, MAIOR_GRUPO)
        palavras.append(''.join(sorteio.choice(alfabeto) for _ in range(tamanho)))
    return ' '.join(palavras)


def filtrar_frases(frases, teclas_permitidas):
    """Só as frases que cabem inteiras no alfabeto já aprendido.

    Compara em minúsculas porque a maiúscula usa a mesma tecla — o que muda é
    o Shift, liberado no nível 9.
    """
    permitidas = {c.lower() for c in teclas_permitidas} | {' '}
    return [f for f in frases if set(f.lower()) <= permitidas]
```

- [ ] **Step 4: Rodar para confirmar que passa**

Run: `.venv/bin/python -m pytest tests/test_licoes.py -v`
Expected: `23 passed`

- [ ] **Step 5: Commit**

```bash
git add licoes.py tests/test_licoes.py
git commit -m "licoes: gerador deterministico de exercicio e filtro de frases por alfabeto"
```

---

### Task 11: Critério de aprovação e progressão

**Files:**
- Modify: `licoes.py`
- Modify: `tests/test_licoes.py`

**Interfaces:**
- Consumes: `licoes` das Tasks 9-10
- Produces:
  - `licoes.Avaliacao(aprovado: bool, faltou: tuple[str, ...])` — dataclass congelada
  - `licoes.avaliar(resultado: dict, nivel: Nivel) -> Avaliacao`
  - `licoes.nivel_atual(registros: list[dict], nome_layout: str) -> Nivel`
  - `licoes.MAXIMO_DE_TROPECOS = 0.03`, `licoes.REGULARIDADE_MINIMA = 0.90`, `licoes.APROVACOES_SEGUIDAS = 2`

`resultado` é um dicionário com as chaves `tropecos`, `total_teclas`, `wpm_bruto`, `regularidade`, `duracao_s` e `limite_s`.

- [ ] **Step 1: Escrever os testes que falham**

Acrescentar ao fim de `tests/test_licoes.py`:

```python
def _resultado(**mudancas):
    """Um resultado que passa em tudo; os testes pioram um critério de cada vez."""
    base = {'tropecos': 0, 'total_teclas': 100, 'wpm_bruto': 20.0,
            'regularidade': 0.99, 'duracao_s': 30.0, 'limite_s': 60.0}
    base.update(mudancas)
    return base


NIVEL_1 = None


def setup_module(_):
    global NIVEL_1
    NIVEL_1 = licoes.curriculo('us')[0]


def test_aprova_quando_os_quatro_criterios_passam():
    assert licoes.avaliar(_resultado(), NIVEL_1).aprovado is True


def test_reprova_por_tropecos_e_diz_qual_criterio_faltou():
    a = licoes.avaliar(_resultado(tropecos=10), NIVEL_1)
    assert a.aprovado is False
    assert a.faltou == ('tropecos',)


def test_reprova_por_wpm_abaixo_da_meta():
    a = licoes.avaliar(_resultado(wpm_bruto=5.0), NIVEL_1)
    assert a.faltou == ('wpm',)


def test_reprova_por_ritmo_irregular_mesmo_sem_errar_nada():
    # 100% de acerto lento e picotado NÃO passa: é o caso de quem caça a tecla.
    a = licoes.avaliar(_resultado(regularidade=0.50), NIVEL_1)
    assert a.faltou == ('regularidade',)


def test_reprova_por_estourar_o_tempo():
    a = licoes.avaliar(_resultado(duracao_s=90.0), NIVEL_1)
    assert a.faltou == ('tempo',)


def test_regularidade_indefinida_nao_reprova():
    # Exercício curto demais para medir ritmo não pode punir ninguém.
    assert licoes.avaliar(_resultado(regularidade=None), NIVEL_1).aprovado is True


def test_lista_todos_os_criterios_que_faltaram():
    a = licoes.avaliar(_resultado(tropecos=10, wpm_bruto=1.0), NIVEL_1)
    assert set(a.faltou) == {'tropecos', 'wpm'}


def test_comeca_no_nivel_um_sem_historico():
    assert licoes.nivel_atual([], 'us').numero == 1


def test_uma_aprovacao_isolada_nao_libera_o_proximo_nivel():
    registros = [{'modo': 'licao', 'nivel': 'base-esquerda', 'aprovado': True}]
    assert licoes.nivel_atual(registros, 'us').numero == 1


def test_duas_aprovacoes_seguidas_liberam_o_proximo():
    registros = [{'modo': 'licao', 'nivel': 'base-esquerda', 'aprovado': True}] * 2
    assert licoes.nivel_atual(registros, 'us').numero == 2


def test_reprovar_no_meio_zera_a_contagem():
    registros = [
        {'modo': 'licao', 'nivel': 'base-esquerda', 'aprovado': True},
        {'modo': 'licao', 'nivel': 'base-esquerda', 'aprovado': False},
        {'modo': 'licao', 'nivel': 'base-esquerda', 'aprovado': True},
    ]
    assert licoes.nivel_atual(registros, 'us').numero == 1


def test_exercicio_do_modo_livre_nao_conta_para_a_progressao():
    registros = [{'modo': 'livre', 'nivel': None, 'aprovado': True}] * 5
    assert licoes.nivel_atual(registros, 'us').numero == 1


def test_nao_passa_do_ultimo_nivel():
    registros = [{'modo': 'licao', 'nivel': n.id, 'aprovado': True}
                 for n in licoes.curriculo('us') for _ in range(2)]
    assert licoes.nivel_atual(registros, 'us').numero == 12
```

- [ ] **Step 2: Rodar para confirmar que falha**

Run: `.venv/bin/python -m pytest tests/test_licoes.py -k "aprova or reprova or nivel_atual or criterios or livre" -v`
Expected: FAIL com `AttributeError: module 'licoes' has no attribute 'avaliar'`

- [ ] **Step 3: Implementar**

Acrescentar ao fim de `licoes.py`:

```python
# Um tropeço a cada 33 teclas ainda é aprendizado; mais que isso é chute.
MAXIMO_DE_TROPECOS = 0.03
REGULARIDADE_MINIMA = 0.90
# Um acerto isolado pode ser sorte; dois seguidos, não.
APROVACOES_SEGUIDAS = 2


@dataclass(frozen=True)
class Avaliacao:
    aprovado: bool
    faltou: tuple


def avaliar(resultado, nivel):
    """Diz se o exercício aprova o nível e, se não, exatamente o que faltou.

    Reprovar não pune: o aluno repete o mesmo nível, e o relatório aponta qual
    dos quatro critérios ficou para trás.
    """
    faltou = []
    total = resultado['total_teclas'] or 1
    if resultado['tropecos'] / total > MAXIMO_DE_TROPECOS:
        faltou.append('tropecos')
    if resultado['wpm_bruto'] < nivel.wpm_meta:
        faltou.append('wpm')
    regularidade = resultado.get('regularidade')
    # None = exercício curto demais para medir ritmo. Não mede, não reprova.
    if regularidade is not None and regularidade < REGULARIDADE_MINIMA:
        faltou.append('regularidade')
    if resultado['duracao_s'] > resultado['limite_s']:
        faltou.append('tempo')
    return Avaliacao(aprovado=not faltou, faltou=tuple(faltou))


def nivel_atual(registros, nome_layout):
    """Em que nível o aluno está, lido do histórico.

    Avança quando encontra `APROVACOES_SEGUIDAS` aprovações consecutivas no
    nível corrente. Exercício do modo livre é ignorado — ele não faz parte do
    currículo.
    """
    niveis = curriculo(nome_layout)
    indice = 0
    seguidas = 0
    for registro in registros:
        if registro.get('modo') != 'licao':
            continue
        if registro.get('nivel') != niveis[indice].id:
            continue
        if registro.get('aprovado'):
            seguidas += 1
            if seguidas >= APROVACOES_SEGUIDAS and indice < len(niveis) - 1:
                indice += 1
                seguidas = 0
        else:
            seguidas = 0
    return niveis[indice]
```

- [ ] **Step 4: Rodar para confirmar que passa**

Run: `.venv/bin/python -m pytest tests/ -v`
Expected: `86 passed` (15 métricas + 7 teclas + 11 histórico + 17 layouts + 36 lições)

- [ ] **Step 5: Commit**

```bash
git add licoes.py tests/test_licoes.py
git commit -m "licoes: aprovacao pelos quatro criterios e progressao por duas aprovacoes seguidas"
```

---

### Task 12: Teclado desenhado no `sg.Graph`

**Files:**
- Create: `teclado_widget.py`
- Create: `tools/ver_teclado.py`

**Interfaces:**
- Consumes: `layouts` da Task 8
- Produces:
  - `teclado_widget.CORES_DOS_DEDOS: dict[str, str]`
  - `teclado_widget.Teclado(nome_layout, largura_px, altura_px, chave)` com `.elemento() -> sg.Graph`, `.desenhar() -> None`, `.pintar(caractere, estado) -> None`, `.limpar_estados() -> None`
  - estados válidos: `'repouso'`, `'proxima'`, `'certa'`, `'errada'`

- [ ] **Step 1: Implementar o widget**

`teclado_widget.py`:

```python
"""Teclado desenhado no Canvas do Tk, com tecla e dedo acendendo ao vivo.

Desenhado em `sg.Graph`, não em imagem: cada tecla precisa mudar de cor
individualmente durante a digitação, e imagem estática exigiria uma imagem por
estado. O Graph ainda redesenha proporcional quando a janela muda de tamanho.

Só repinta a tecla que mudou de estado — repintar o teclado inteiro a cada
tecla é o caminho conhecido para a janela engasgar.
"""
import layouts
from gui_backend import sg

# Cada dedo tem cor própria, usada tanto aqui quanto na ilustração das mãos.
CORES_DOS_DEDOS = {
    'minimo': '#8e6bbf',
    'anelar': '#3f7fbf',
    'medio': '#3fa86b',
    'indicador': '#d99a2b',
}
COR_DE_FUNDO = '#f3f3f3'
CORES_DOS_ESTADOS = {
    'proxima': '#ffe066',
    'certa': '#57b85c',
    'errada': '#d9534f',
}
COR_DA_BORDA = '#9a9a9a'
COR_DO_TEXTO = '#222222'


class Teclado:
    """Um teclado desenhável. Mantém o id de cada retângulo para repintar só ele."""

    def __init__(self, nome_layout, largura_px, altura_px, chave='-TECLADO-'):
        self.nome_layout = nome_layout
        self.largura_px = largura_px
        self.altura_px = altura_px
        self.chave = chave
        self._grafico = None
        self._figuras = {}     # caractere -> (id_retangulo, id_texto)
        self._estados = {}     # caractere -> estado atual

    def elemento(self):
        """O elemento a colocar no layout da janela."""
        self._grafico = sg.Graph(
            canvas_size=(int(self.largura_px), int(self.altura_px)),
            graph_bottom_left=(0, self.altura_px),
            graph_top_right=(self.largura_px, 0),
            key=self.chave, background_color=COR_DE_FUNDO, pad=(0, 0))
        return self._grafico

    def desenhar(self, mostrar_dedos=True):
        """Desenha o teclado do zero. Chamar depois de `finalize=True`."""
        self._grafico.erase()
        self._figuras.clear()
        self._estados.clear()
        retangulos = layouts.retangulos(self.nome_layout, self.largura_px, self.altura_px)
        for tecla in layouts.teclas(self.nome_layout):
            x0, y0, x1, y1 = retangulos[tecla.caractere]
            cor = CORES_DOS_DEDOS[tecla.dedo] if mostrar_dedos else COR_DE_FUNDO
            id_retangulo = self._grafico.draw_rectangle(
                (x0 + 1, y0 + 1), (x1 - 1, y1 - 1), fill_color=cor, line_color=COR_DA_BORDA)
            id_texto = self._grafico.draw_text(
                tecla.caractere.upper(), ((x0 + x1) / 2, (y0 + y1) / 2),
                color=COR_DO_TEXTO, font=('Helvetica', 10, 'bold'))
            self._figuras[tecla.caractere] = (id_retangulo, id_texto)
            self._estados[tecla.caractere] = 'repouso'

    def pintar(self, caractere, estado):
        """Muda o estado de UMA tecla. Caractere fora do layout é ignorado."""
        caractere = caractere.lower()
        if caractere not in self._figuras or self._estados.get(caractere) == estado:
            return
        id_retangulo, id_texto = self._figuras[caractere]
        retangulos = layouts.retangulos(self.nome_layout, self.largura_px, self.altura_px)
        x0, y0, x1, y1 = retangulos[caractere]
        dedo = layouts.dedo_de(caractere, self.nome_layout)[1]
        cor = CORES_DOS_ESTADOS.get(estado, CORES_DOS_DEDOS[dedo])
        self._grafico.delete_figure(id_retangulo)
        novo = self._grafico.draw_rectangle(
            (x0 + 1, y0 + 1), (x1 - 1, y1 - 1), fill_color=cor, line_color=COR_DA_BORDA)
        # O retângulo novo nasce por cima do texto; devolver o texto para o topo.
        self._grafico.tk_canvas.tag_raise(id_texto)
        self._figuras[caractere] = (novo, id_texto)
        self._estados[caractere] = estado

    def limpar_estados(self):
        """Devolve todas as teclas ao repouso (cor do dedo)."""
        for caractere in list(self._estados):
            self.pintar(caractere, 'repouso')

    def redimensionar(self, largura_px, altura_px):
        """Redesenha o teclado noutro tamanho, preservando os estados.

        Chamado quando a janela muda de tamanho: o Graph tem tamanho fixo em
        pixels, então quem redesenha proporcional é este método.
        """
        if (int(largura_px), int(altura_px)) == (int(self.largura_px), int(self.altura_px)):
            return
        estados = dict(self._estados)
        self.largura_px = max(200.0, largura_px)
        self.altura_px = max(80.0, altura_px)
        self._grafico.set_size((int(self.largura_px), int(self.altura_px)))
        self._grafico.change_coordinates((0, self.altura_px), (self.largura_px, 0))
        self.desenhar()
        for caractere, estado in estados.items():
            if estado != 'repouso':
                self.pintar(caractere, estado)
```

- [ ] **Step 2: Escrever o visualizador manual**

`tools/ver_teclado.py`:

```python
"""Abre os três teclados desenhados para conferência a olho.

Rode com:  .venv/bin/python tools/ver_teclado.py
"""
import teclado_widget
from gui_backend import sg

for nome in ('abnt2', 'us', 'it'):
    teclado = teclado_widget.Teclado(nome, 900, 260)
    layout = [
        [sg.Text(f'Layout: {nome}', font=('Helvetica', 14))],
        [teclado.elemento()],
        [sg.Button('Acender a linha-base', key='-BASE-'),
         sg.Button('Limpar', key='-LIMPAR-'),
         sg.Button('Próximo layout', key='-FIM-')],
    ]
    janela = sg.Window(f'Teclado {nome}', layout, finalize=True)
    teclado.desenhar()
    while True:
        evento, _ = janela.read()
        if evento in (sg.WIN_CLOSED, '-FIM-'):
            break
        if evento == '-BASE-':
            import layouts
            esquerda, direita = layouts.teclas_base(nome)
            for c in esquerda + direita:
                teclado.pintar(c, 'proxima')
        if evento == '-LIMPAR-':
            teclado.limpar_estados()
    janela.close()
```

- [ ] **Step 3: Conferir a olho**

Run: `.venv/bin/python tools/ver_teclado.py`

Expected, em cada um dos três layouts:
- as quatro linhas aparecem escalonadas para a direita, como num teclado real
- cada dedo tem uma cor e as cores são simétricas entre as duas mãos
- **"Acender a linha-base"** amarela exatamente 8 teclas: `asdf` e `jkl` mais `;` (US), `ç` (ABNT2) ou `ò` (italiano)
- **"Limpar"** devolve todas à cor do dedo, e as letras continuam legíveis por cima

- [ ] **Step 4: Commit**

```bash
git add teclado_widget.py tools/ver_teclado.py
git commit -m "teclado: desenho vetorial no Graph com cor por dedo e repintura por tecla"
```

---

### Task 13: Ilustração das mãos, de SVG para PNG no build

**Files:**
- Create: `assets/maos/mao-esquerda.svg`
- Create: `assets/maos/mao-direita.svg`
- Modify: `build.py`
- Create: `tools/gerar_pngs_das_maos.py`

**Interfaces:**
- Consumes: `teclado_widget.CORES_DOS_DEDOS` da Task 12
- Produces: `assets/maos/<mao>-<dedo>.png` (10 arquivos: 2 mãos × neutra + 4 dedos), consumidos pela Task 14

- [ ] **Step 1: Desenhar os SVGs**

Cada mão é um SVG com um `<g>` por dedo, identificado por `id`, para que o
conversor consiga destacar um dedo por vez. Estrutura obrigatória de
`assets/maos/mao-esquerda.svg` (a direita é o espelho, com `transform="scale(-1,1) translate(-260,0)"` no grupo raiz):

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 260 300" width="260" height="300">
  <g id="palma">
    <path d="M60 300 L60 190 Q60 165 90 160 L170 160 Q200 165 200 190 L200 300 Z"
          fill="#f0d6c0" stroke="#b99a86" stroke-width="3"/>
  </g>
  <g id="minimo">
    <rect x="60" y="120" width="30" height="70" rx="15"
          fill="#f0d6c0" stroke="#b99a86" stroke-width="3"/>
  </g>
  <g id="anelar">
    <rect x="95" y="95" width="30" height="95" rx="15"
          fill="#f0d6c0" stroke="#b99a86" stroke-width="3"/>
  </g>
  <g id="medio">
    <rect x="130" y="85" width="30" height="105" rx="15"
          fill="#f0d6c0" stroke="#b99a86" stroke-width="3"/>
  </g>
  <g id="indicador">
    <rect x="165" y="105" width="30" height="85" rx="15"
          fill="#f0d6c0" stroke="#b99a86" stroke-width="3"/>
  </g>
  <g id="polegar">
    <rect x="195" y="185" width="60" height="28" rx="14"
          fill="#f0d6c0" stroke="#b99a86" stroke-width="3"
          transform="rotate(-20 195 185)"/>
  </g>
</svg>
```

- [ ] **Step 2: Escrever o conversor**

`tools/gerar_pngs_das_maos.py`:

```python
"""Gera os PNGs das mãos a partir dos SVGs, um por dedo em destaque.

Roda no DESENVOLVIMENTO e no empacotamento, nunca no aplicativo: converter SVG
em tempo de execução exigiria cairosvg, que arrasta a biblioteca nativa do Cairo
para dentro do executável e quebra a portabilidade.

Usa o `rsvg-convert` ou o `inkscape` do sistema, o que estiver disponível.
Instalar no Debian/Ubuntu:  sudo apt install librsvg2-bin
"""
import re
import shutil
import subprocess
import sys
from pathlib import Path

PASTA = Path(__file__).resolve().parent.parent / 'assets' / 'maos'
DEDOS = ('minimo', 'anelar', 'medio', 'indicador')
COR_DE_DESTAQUE = {
    'minimo': '#8e6bbf',
    'anelar': '#3f7fbf',
    'medio': '#3fa86b',
    'indicador': '#d99a2b',
}


def conversor():
    for programa, molde in (
            ('rsvg-convert', ['{prog}', '-w', '260', '-h', '300', '-o', '{saida}', '{entrada}']),
            ('inkscape', ['{prog}', '--export-type=png', '--export-filename={saida}', '{entrada}'])):
        caminho = shutil.which(programa)
        if caminho:
            return caminho, molde
    print('ERRO: instale librsvg2-bin (rsvg-convert) ou inkscape', file=sys.stderr)
    sys.exit(1)


def destacar(svg, dedo, cor):
    """Troca o preenchimento do grupo daquele dedo pela cor de destaque."""
    padrao = re.compile(rf'(<g id="{dedo}">.*?)fill="#f0d6c0"', re.DOTALL)
    return padrao.sub(rf'\1fill="{cor}"', svg)


def main():
    programa, molde = conversor()
    for mao in ('esquerda', 'direita'):
        original = (PASTA / f'mao-{mao}.svg').read_text(encoding='utf-8')
        variantes = {'neutra': original}
        for dedo in DEDOS:
            variantes[dedo] = destacar(original, dedo, COR_DE_DESTAQUE[dedo])
        for nome, conteudo in variantes.items():
            temporario = PASTA / f'.tmp-{mao}-{nome}.svg'
            saida = PASTA / f'{mao}-{nome}.png'
            temporario.write_text(conteudo, encoding='utf-8')
            comando = [p.format(prog=programa, saida=str(saida), entrada=str(temporario))
                       for p in molde]
            subprocess.run(comando, check=True)
            temporario.unlink()
            print(f'gerado {saida.name}')


if __name__ == '__main__':
    main()
```

- [ ] **Step 3: Gerar e conferir**

Run: `.venv/bin/python tools/gerar_pngs_das_maos.py && ls assets/maos/*.png | wc -l`
Expected: `10`

Abra `assets/maos/esquerda-indicador.png` e confirme que **só o indicador** está colorido, o resto da mão em tom de pele.

- [ ] **Step 4: Ligar ao empacotamento**

Em `build.py`, dentro da função que monta os argumentos do PyInstaller, antes de chamar o PyInstaller, acrescentar a geração e a inclusão dos PNGs:

```python
    # As mãos são PNG pré-gerado: nenhum conversor de SVG entra no executável.
    subprocess.run([sys.executable, 'tools/gerar_pngs_das_maos.py'], check=True)
    argumentos += ['--add-data', f'assets/maos{os.pathsep}assets/maos']
```

- [ ] **Step 5: Commit**

```bash
git add assets/maos build.py tools/gerar_pngs_das_maos.py
git commit -m "maos: SVG por dedo convertido para PNG no empacotamento, sem dependencia em runtime"
```

---

### Task 14: Tela prévia com o teste de mãos

**Files:**
- Create: `modo_licao.py`
- Modify: `i18n.py`

**Interfaces:**
- Consumes: `teclas_pressionadas` (Task 5), `layouts` (Task 8), `licoes` (Task 9), `teclado_widget` (Task 12), PNGs (Task 13)
- Produces: `modo_licao.tela_previa(nivel, nome_layout, idioma, sem_rollover=False) -> tuple[bool, bool]` — devolve `(comecar, sem_rollover)`. `comecar` é True se o aluno passou no teste e quer começar; `sem_rollover` volta True quando se descobriu que o teclado não reporta quatro teclas juntas, para quem chama gravar a descoberta e não repetir a espera de 15 s toda vez. `modo_licao` não toca em disco de propósito — quem persiste é a Task 17.

- [ ] **Step 1: Acrescentar os textos ao `i18n.py`**

Dentro do dicionário `translations`, no bloco `'pt'`:

```python
        'licao_titulo': 'Nível {} — {}',
        'licao_teclas_novas': 'Teclas novas neste nível:',
        'licao_criterio': 'Para passar: até {}% de tropeços, {} WPM e ritmo regular, em dois exercícios seguidos.',
        'licao_teste_esquerda': 'Pouse a mão ESQUERDA e pressione as quatro juntas:',
        'licao_teste_direita': 'Pouse a mão DIREITA e pressione as quatro juntas:',
        'licao_teste_ok': 'Mãos na posição. Pode começar.',
        'licao_teste_sequencial': 'Seu teclado não reporta quatro teclas ao mesmo tempo — é limite do equipamento, não seu. Pressione uma de cada vez, na ordem.',
        'licao_layout_diferente': 'A tecla que você pressionou produziu "{}", e neste layout deveria produzir "{}". O teclado do sistema parece estar noutro layout.',
        'licao_comecar': 'Começar o exercício',
        'licao_voltar': 'Voltar',
```

No bloco `'en'`:

```python
        'licao_titulo': 'Level {} — {}',
        'licao_teclas_novas': 'New keys in this level:',
        'licao_criterio': 'To pass: at most {}% stumbles, {} WPM and steady rhythm, on two exercises in a row.',
        'licao_teste_esquerda': 'Rest your LEFT hand and press all four together:',
        'licao_teste_direita': 'Rest your RIGHT hand and press all four together:',
        'licao_teste_ok': 'Hands in position. You may start.',
        'licao_teste_sequencial': 'Your keyboard cannot report four keys at once — that is a hardware limit, not yours. Press them one at a time, in order.',
        'licao_layout_diferente': 'The key you pressed produced "{}", but in this layout it should produce "{}". Your system keyboard seems to use a different layout.',
        'licao_comecar': 'Start the exercise',
        'licao_voltar': 'Back',
```

No bloco `'it'`:

```python
        'licao_titulo': 'Livello {} — {}',
        'licao_teclas_novas': 'Nuovi tasti di questo livello:',
        'licao_criterio': 'Per superare: massimo {}% di errori, {} WPM e ritmo regolare, in due esercizi di seguito.',
        'licao_teste_esquerda': 'Appoggia la mano SINISTRA e premi i quattro tasti insieme:',
        'licao_teste_direita': 'Appoggia la mano DESTRA e premi i quattro tasti insieme:',
        'licao_teste_ok': 'Mani in posizione. Puoi iniziare.',
        'licao_teste_sequencial': 'La tua tastiera non riesce a segnalare quattro tasti insieme — è un limite dell\'hardware, non tuo. Premili uno alla volta, in ordine.',
        'licao_layout_diferente': 'Il tasto premuto ha prodotto "{}", ma in questo layout dovrebbe produrre "{}". La tastiera di sistema sembra usare un altro layout.',
        'licao_comecar': 'Inizia l\'esercizio',
        'licao_voltar': 'Indietro',
```

- [ ] **Step 2: Implementar a tela prévia**

`modo_licao.py`:

```python
"""O Modo Lição: tela prévia com teste de mãos e exercício travado.

O teste de mãos é o único jeito honesto de verificar posição de mão por
software: exige quatro teclas pressionadas AO MESMO TEMPO, o que não dá para
simular digitando uma de cada vez. Não diz qual dedo foi usado — nada diz — mas
prova que a mão está pousada na linha-base antes de o exercício começar.
"""
import time
from datetime import datetime
from pathlib import Path

import layouts
import licoes
import metricas
import teclado_widget
import teclas_pressionadas
from gui_backend import sg
from i18n import get_text

# Tempo que as quatro teclas precisam ficar juntas para o passo valer.
MS_PARA_CONFIRMAR = 400.0
# Depois disso sem conseguir, assume-se limite de rollover do teclado.
SEGUNDOS_ATE_OFERECER_SEQUENCIAL = 15.0

PASTA_DAS_MAOS = Path(__file__).resolve().parent / 'assets' / 'maos'


def _agora_ms():
    return time.monotonic() * 1000.0


def _keysym_para_caractere(keysym):
    """Converte o keysym do tkinter no caractere que ele produz.

    Teclas de uma letra vêm como a própria letra; as demais têm nome
    (`ccedilla`, `semicolon`, `space`…).
    """
    if len(keysym) == 1:
        return keysym.lower()
    return {
        'ccedilla': 'ç', 'Ccedilla': 'ç', 'semicolon': ';', 'space': ' ',
        'ograve': 'ò', 'agrave': 'à', 'ugrave': 'ù', 'egrave': 'è',
        'apostrophe': "'", 'comma': ',', 'period': '.', 'minus': '-',
        'equal': '=', 'bracketleft': '[', 'bracketright': ']',
        'slash': '/', 'backslash': '\\', 'grave': '`', 'acute': '´',
        'asciitilde': '~', 'plus': '+', 'igrave': 'ì',
    }.get(keysym)


def tela_previa(nivel, nome_layout, idioma, sem_rollover=False):
    """Mostra o nível e cobra o teste de mãos.

    Devolve (comecar, sem_rollover). O segundo valor vira True quando se
    descobre que o teclado não reporta quatro teclas juntas — quem chama grava
    isso para não fazer o aluno esperar 15 segundos toda vez.
    """
    esquerda, direita = layouts.teclas_base(nome_layout)
    passos = [('licao_teste_esquerda', esquerda), ('licao_teste_direita', direita)]
    passo_atual = 0
    confirmando_desde = None
    sequencial = sem_rollover      # já se sabia: entra direto no modo alternativo
    proxima_sequencial = 0
    inicio = _agora_ms()

    rastreador = teclas_pressionadas.Rastreador()
    teclado = teclado_widget.Teclado(nome_layout, 860, 250, chave='-TECLADO_PREVIA-')

    percentual = int(licoes.MAXIMO_DE_TROPECOS * 100)
    layout = [
        [sg.Text(get_text('licao_titulo', idioma).format(nivel.numero, nivel.id),
                 font=('Helvetica', 20))],
        [sg.Text(get_text('licao_teclas_novas', idioma), font=('Helvetica', 11)),
         sg.Text(' '.join(nivel.teclas_novas) or '—', font=('Courier New', 14, 'bold'))],
        [sg.Text(get_text('licao_criterio', idioma).format(percentual, nivel.wpm_meta),
                 font=('Helvetica', 10))],
        [sg.HSeparator()],
        [sg.Image(filename=str(PASTA_DAS_MAOS / 'esquerda-neutra.png'), key='-MAO_E-'),
         sg.Text(get_text(passos[0][0], idioma), key='-INSTRUCAO-',
                 font=('Helvetica', 13), expand_x=True, justification='center'),
         sg.Image(filename=str(PASTA_DAS_MAOS / 'direita-neutra.png'), key='-MAO_D-')],
        [teclado.elemento()],
        [sg.Text('', key='-AVISO-', font=('Helvetica', 10), text_color='darkorange',
                 expand_x=True, justification='center')],
        [sg.Button(get_text('licao_comecar', idioma), key='-COMECAR-', disabled=True,
                   font=('Helvetica', 13)),
         sg.Button(get_text('licao_voltar', idioma), key='-VOLTAR-', font=('Helvetica', 11))],
    ]
    janela = sg.Window(get_text('licao_titulo', idioma).format(nivel.numero, nivel.id),
                       layout, modal=True, finalize=True, size=(1100, 780),
                       element_justification='center', return_keyboard_events=True)
    janela.bind('<KeyPress>', '-DOWN-')
    janela.bind('<KeyRelease>', '-UP-')
    teclado.desenhar()

    comecar = False
    while True:
        evento, _ = janela.read(timeout=50)
        agora = _agora_ms()

        if evento in (sg.WIN_CLOSED, '-VOLTAR-'):
            break
        if evento == '-COMECAR-':
            comecar = True
            break

        if evento in ('-DOWN-', '-UP-'):
            caractere = _keysym_para_caractere(
                getattr(janela.user_bind_event, 'keysym', ''))
            if caractere:
                if evento == '-DOWN-':
                    rastreador.pressionou(caractere, agora)
                    # Se a tecla produziu um caractere que este layout não tem,
                    # o teclado do sistema está noutro layout. Sem avisar, o
                    # aluno tentaria a vida inteira sem entender o que falta.
                    if (passo_atual < len(passos)
                            and layouts.dedo_de(caractere, nome_layout) is None):
                        janela['-AVISO-'].update(
                            get_text('licao_layout_diferente', idioma).format(
                                caractere, ' '.join(passos[passo_atual][1])))
                else:
                    rastreador.soltou(caractere, agora)

        if passo_atual >= len(passos):
            continue

        chave_do_texto, esperadas = passos[passo_atual]
        ativas = rastreador.ativas(agora)

        # Pinta o teclado: verde o que está pressionado, amarelo o que falta.
        for caractere in esperadas:
            teclado.pintar(caractere, 'certa' if caractere in ativas else 'proxima')

        if sequencial:
            # Modo alternativo: uma tecla por vez, na ordem, para teclado sem rollover.
            if esperadas[proxima_sequencial] in ativas:
                proxima_sequencial += 1
                if proxima_sequencial >= len(esperadas):
                    proxima_sequencial = 0
                    passo_atual += 1
        else:
            completo = set(esperadas) <= ativas
            if completo:
                confirmando_desde = confirmando_desde or agora
                if agora - confirmando_desde >= MS_PARA_CONFIRMAR:
                    confirmando_desde = None
                    passo_atual += 1
            else:
                confirmando_desde = None
            if (not completo and passo_atual == 0
                    and agora - inicio > SEGUNDOS_ATE_OFERECER_SEQUENCIAL * 1000):
                sequencial = True
                janela['-AVISO-'].update(get_text('licao_teste_sequencial', idioma))

        if passo_atual < len(passos):
            janela['-INSTRUCAO-'].update(get_text(passos[passo_atual][0], idioma))
            # A mão cobrada agora aparece destacada; a outra fica neutra.
            for mao, sufixo, cobrada in (('esquerda', 'E', passo_atual == 0),
                                         ('direita', 'D', passo_atual == 1)):
                variante = 'indicador' if cobrada else 'neutra'
                janela[f'-MAO_{sufixo}-'].update(
                    filename=str(PASTA_DAS_MAOS / f'{mao}-{variante}.png'))
        else:
            janela['-INSTRUCAO-'].update(get_text('licao_teste_ok', idioma))
            janela['-COMECAR-'].update(disabled=False)
            teclado.limpar_estados()
            for mao, sufixo in (('esquerda', 'E'), ('direita', 'D')):
                janela[f'-MAO_{sufixo}-'].update(
                    filename=str(PASTA_DAS_MAOS / f'{mao}-neutra.png'))

    janela.close()
    return comecar, sequencial
```

- [ ] **Step 3: Conferir a olho**

Run:

```bash
.venv/bin/python -c "
import licoes, modo_licao
nivel = licoes.curriculo('abnt2')[0]
print('começou, sem_rollover:', modo_licao.tela_previa(nivel, 'abnt2', 'pt'))
"
```

Expected:
- a janela abre em 1100×780, com o nível, as teclas novas e o critério
- **"Começar o exercício" nasce desabilitado**
- segurar `a s d f` juntas por meio segundo passa para a instrução da mão direita
- segurar `j k l ç` juntas habilita o botão e limpa o teclado
- soltar e segurar de novo **não** faz o passo voltar (auto-repeat filtrado)
- se você não pressionar nada por 15 s, aparece o aviso do modo sequencial em laranja

- [ ] **Step 4: Commit**

```bash
git add modo_licao.py i18n.py
git commit -m "licao: tela previa com teste de maos travando o inicio do exercicio"
```

---

### Task 15: Exercício travado

**Files:**
- Modify: `modo_licao.py`
- Modify: `i18n.py`

**Interfaces:**
- Consumes: tudo das Tasks 4, 5, 8, 9, 10, 12, 14
- Produces: `modo_licao.executar_exercicio(texto, nome_layout, idioma, limite_s) -> dict` com as chaves `batidas` (list[metricas.Batida]), `duracao_s`, `cancelado`

- [ ] **Step 1: Acrescentar os textos ao `i18n.py`**

```python
        'licao_digite': 'Digite:',
        'licao_progresso': '{} de {} teclas',
        'licao_cancelar': 'Cancelar',
        'licao_tempo': 'Tempo: {:.1f}s de {:.1f}s',
```

- [ ] **Step 2: Implementar**

Acrescentar ao fim de `modo_licao.py` (`metricas` e `datetime` já estão importados no topo, da Task 14):

```python
def executar_exercicio(texto, nome_layout, idioma, limite_s):
    """Roda o exercício travado: tecla errada não entra e o texto não avança.

    Diferente do treino livre, aqui não há campo de texto editável — a entrada é
    dirigida por evento de tecla. Isso elimina o colar (que hoje daria 100% de
    precisão de graça) e o backspace (não há o que apagar, porque caractere
    errado nunca entra).
    """
    teclado = teclado_widget.Teclado(nome_layout, 860, 250, chave='-TECLADO_EXERCICIO-')
    elementos_do_alvo = [
        sg.Text(c, key=f'-ALVO_{i}-', font=('Courier New', 16, 'bold'), pad=(0, 0),
                text_color='grey')
        for i, c in enumerate(texto)]

    layout = [
        [sg.Text(get_text('licao_digite', idioma), font=('Helvetica', 12)), sg.Push(),
         sg.Text('', key='-TEMPO-', font=('Helvetica', 11)),
         sg.Text('', key='-PROGRESSO-', font=('Helvetica', 11))],
        [sg.Column([[*elementos_do_alvo]], scrollable=True, expand_x=True,
                   background_color='#eeeeee', pad=(5, 10))],
        [sg.Image(filename=str(PASTA_DAS_MAOS / 'esquerda-neutra.png'), key='-MAO_E-'),
         sg.Push(),
         sg.Image(filename=str(PASTA_DAS_MAOS / 'direita-neutra.png'), key='-MAO_D-')],
        [teclado.elemento()],
        [sg.Button(get_text('licao_cancelar', idioma), key='-CANCELAR-')],
    ]
    janela = sg.Window(get_text('licao_digite', idioma), layout, modal=True, finalize=True,
                       size=(1100, 780), element_justification='center',
                       return_keyboard_events=True)
    janela.bind('<KeyPress>', '-DOWN-')
    teclado.desenhar()

    posicao = 0
    batidas = []
    inicio = _agora_ms()
    ultima_batida = inicio
    cancelado = False

    def destacar_proxima():
        """Acende a tecla que vem e a mão do dedo correspondente."""
        teclado.limpar_estados()
        if posicao >= len(texto):
            return
        alvo = texto[posicao]
        teclado.pintar(alvo, 'proxima')
        par = layouts.dedo_de(alvo, nome_layout)
        for mao, sufixo in (('esquerda', 'E'), ('direita', 'D')):
            dedo = par[1] if par and par[0] == mao else 'neutra'
            janela[f'-MAO_{sufixo}-'].update(
                filename=str(PASTA_DAS_MAOS / f'{mao}-{dedo}.png'))

    destacar_proxima()

    while posicao < len(texto):
        evento, _ = janela.read(timeout=100)
        agora = _agora_ms()
        decorrido = (agora - inicio) / 1000.0
        janela['-TEMPO-'].update(get_text('licao_tempo', idioma).format(decorrido, limite_s))
        janela['-PROGRESSO-'].update(
            get_text('licao_progresso', idioma).format(posicao, len(texto)))

        if evento in (sg.WIN_CLOSED, '-CANCELAR-'):
            cancelado = True
            break
        if decorrido >= limite_s:
            break
        if evento != '-DOWN-':
            continue

        caractere = _keysym_para_caractere(getattr(janela.user_bind_event, 'keysym', ''))
        if caractere is None:
            continue      # Shift, Ctrl, setas: não são resposta, são modificador

        esperado = texto[posicao]
        batidas.append(metricas.Batida(esperado=esperado, digitado=caractere,
                                       ms=agora - ultima_batida))
        ultima_batida = agora

        if caractere == esperado.lower() or caractere == esperado:
            janela[f'-ALVO_{posicao}-'].update(text_color='green')
            posicao += 1
            destacar_proxima()
        else:
            # A tecla errada NÃO entra: o alvo não avança e a tecla certa pisca.
            janela[f'-ALVO_{posicao}-'].update(text_color='red')
            teclado.pintar(caractere, 'errada')

    duracao = (_agora_ms() - inicio) / 1000.0
    janela.close()
    return {'batidas': batidas, 'duracao_s': duracao, 'cancelado': cancelado}
```

- [ ] **Step 3: Conferir a olho**

Run:

```bash
.venv/bin/python -c "
import licoes, modo_licao
texto = licoes.gerar_exercicio('abnt2', 1, semente=1, grupos=4)
print('alvo:', texto)
r = modo_licao.executar_exercicio(texto, 'abnt2', 'pt', 60.0)
print('batidas:', len(r['batidas']), 'duracao:', round(r['duracao_s'],1))
"
```

Expected:
- a tecla que vem está amarela no teclado e o dedo aceso na mão certa
- digitar a **tecla errada** deixa o caractere do alvo vermelho e **não avança**
- **colar com Ctrl+V não escreve nada** — não existe campo de texto
- **Backspace não apaga nada**
- ao completar a última tecla a janela fecha sozinha e o contador de batidas bate com o número de teclas que você pressionou (inclusive as erradas)

- [ ] **Step 4: Commit**

```bash
git add modo_licao.py i18n.py
git commit -m "licao: exercicio travado sem colar, sem backspace e sem avancar errando"
```

---

### Task 16: Relatório da lição e gravação no histórico

**Files:**
- Modify: `modo_licao.py`
- Modify: `i18n.py`
- Create: `tests/test_integracao_licao.py`

**Interfaces:**
- Consumes: tudo até a Task 15
- Produces:
  - `modo_licao.montar_registro(nivel, nome_layout, idioma, texto, semente, resultado) -> dict` — puro, testável
  - `modo_licao.mostrar_relatorio(registro, avaliacao, idioma) -> None`

- [ ] **Step 1: Escrever o teste que falha**

`tests/test_integracao_licao.py`:

```python
"""Testa a montagem do registro do histórico — a parte sem GUI do Modo Lição."""
import licoes
import metricas
import modo_licao


def _resultado_perfeito(texto):
    batidas = [metricas.Batida(c, c, 200.0) for c in texto]
    return {'batidas': batidas, 'duracao_s': 20.0, 'cancelado': False}


def test_registro_tem_os_campos_que_o_historico_espera():
    nivel = licoes.curriculo('us')[0]
    texto = licoes.gerar_exercicio('us', 1, semente=5)
    registro = modo_licao.montar_registro(nivel, 'us', 'en', texto, 5,
                                          _resultado_perfeito(texto))
    for campo in ('quando', 'modo', 'nivel', 'wpm_meta', 'idioma', 'layout', 'alvo',
                  'semente', 'duracao_s', 'limite_s', 'wpm_bruto', 'wpm_liquido',
                  'tropecos', 'total_teclas', 'regularidade', 'aprovado', 'teclas'):
        assert campo in registro, campo


def test_registro_de_licao_marca_o_modo_e_o_nivel():
    nivel = licoes.curriculo('us')[0]
    texto = licoes.gerar_exercicio('us', 1, semente=5)
    registro = modo_licao.montar_registro(nivel, 'us', 'en', texto, 5,
                                          _resultado_perfeito(texto))
    assert registro['modo'] == 'licao'
    assert registro['nivel'] == 'base-esquerda'


def test_exercicio_sem_erro_nenhum_nao_tem_tropecos():
    nivel = licoes.curriculo('us')[0]
    texto = licoes.gerar_exercicio('us', 1, semente=5)
    registro = modo_licao.montar_registro(nivel, 'us', 'en', texto, 5,
                                          _resultado_perfeito(texto))
    assert registro['tropecos'] == 0


def test_tecla_errada_aparece_como_tropeco_e_confusao():
    nivel = licoes.curriculo('us')[0]
    batidas = [metricas.Batida('a', 'a', 200.0), metricas.Batida('s', 'd', 200.0)]
    resultado = {'batidas': batidas, 'duracao_s': 5.0, 'cancelado': False}
    registro = modo_licao.montar_registro(nivel, 'us', 'en', 'as', 1, resultado)
    assert registro['tropecos'] == 1
    assert registro['teclas']['s']['confusoes'] == {'d': 1}


def test_registro_e_serializavel_em_json():
    import json
    nivel = licoes.curriculo('abnt2')[0]
    texto = licoes.gerar_exercicio('abnt2', 1, semente=2)
    registro = modo_licao.montar_registro(nivel, 'abnt2', 'pt', texto, 2,
                                          _resultado_perfeito(texto))
    assert json.loads(json.dumps(registro, ensure_ascii=False))['alvo'] == texto
```

- [ ] **Step 2: Rodar para confirmar que falha**

Run: `.venv/bin/python -m pytest tests/test_integracao_licao.py -v`
Expected: FAIL com `AttributeError: module 'modo_licao' has no attribute 'montar_registro'`

- [ ] **Step 3: Acrescentar os textos ao `i18n.py`**

```python
        'licao_relatorio_titulo': 'Resultado do nível {}',
        'licao_aprovado': 'Aprovado neste exercício.',
        'licao_reprovado': 'Ainda não. Faltou: {}',
        'licao_faltou_tropecos': 'menos tropeços',
        'licao_faltou_wpm': 'mais velocidade',
        'licao_faltou_regularidade': 'ritmo mais regular (não procure a tecla com o olho)',
        'licao_faltou_tempo': 'terminar dentro do tempo',
        'licao_wpm': 'Velocidade: {:.1f} WPM (meta {})',
        'licao_tropecos_de': 'Tropeços: {} em {} teclas',
        'licao_regularidade': 'Regularidade: {}',
        'licao_repetir': 'Repetir o nível',
        'licao_proximo': 'Próximo exercício',
```

- [ ] **Step 4: Implementar**

Acrescentar ao fim de `modo_licao.py`:

```python
def montar_registro(nivel, nome_layout, idioma, texto, semente, resultado):
    """Monta a linha do histórico a partir do que o exercício produziu.

    Puro de propósito: recebe o resultado bruto e devolve o dicionário pronto,
    sem tocar em disco nem em janela — é o que permite testá-lo.
    """
    batidas = resultado['batidas']
    duracao = resultado['duracao_s']
    acertos = sum(1 for b in batidas if b.esperado == b.digitado)
    tropecos = metricas.tropecos(batidas)
    intervalos = [b.ms for b in batidas]
    limite = licoes.limite_de_tempo(len(texto), nivel.wpm_meta)
    return {
        'quando': datetime.now().astimezone().isoformat(timespec='seconds'),
        'modo': 'licao',
        'nivel': nivel.id,
        'wpm_meta': nivel.wpm_meta,
        'idioma': idioma,
        'layout': nome_layout,
        'alvo': texto,
        'semente': semente,
        'duracao_s': round(duracao, 2),
        'limite_s': round(limite, 2),
        'wpm_bruto': round(metricas.wpm(acertos, duracao), 2),
        # Na lição o líquido é igual ao bruto: a trava impede erro no texto.
        'wpm_liquido': round(metricas.wpm(acertos, duracao), 2),
        'tropecos': tropecos,
        'total_teclas': len(batidas),
        'regularidade': metricas.regularidade(intervalos),
        'aprovado': False,     # preenchido por quem avalia, logo abaixo
        'teclas': metricas.resumo_por_tecla(batidas),
    }


def mostrar_relatorio(registro, avaliacao, idioma):
    """Mostra o resultado e, quando reprova, diz exatamente o que faltou."""
    motivos = ', '.join(
        get_text(f'licao_faltou_{f}', idioma) for f in avaliacao.faltou)
    veredito = (get_text('licao_aprovado', idioma) if avaliacao.aprovado
                else get_text('licao_reprovado', idioma).format(motivos))
    regularidade = registro['regularidade']
    layout = [
        [sg.Text(get_text('licao_relatorio_titulo', idioma).format(registro['nivel']),
                 font=('Helvetica', 16))],
        [sg.Text(veredito, font=('Helvetica', 13, 'bold'),
                 text_color='darkgreen' if avaliacao.aprovado else 'darkorange')],
        [sg.HSeparator()],
        [sg.Text(get_text('licao_wpm', idioma).format(
            registro['wpm_bruto'], registro['wpm_meta']))],
        [sg.Text(get_text('licao_tropecos_de', idioma).format(
            registro['tropecos'], registro['total_teclas']))],
        [sg.Text(get_text('licao_regularidade', idioma).format(
            '—' if regularidade is None else f'{regularidade:.0%}'))],
        [sg.Button(get_text('licao_repetir', idioma), key='-REPETIR-'),
         sg.Button(get_text('licao_proximo', idioma), key='-PROXIMO-')],
    ]
    janela = sg.Window(get_text('licao_relatorio_titulo', idioma).format(registro['nivel']),
                       layout, modal=True, element_justification='center')
    while True:
        evento, _ = janela.read()
        if evento in (sg.WIN_CLOSED, '-REPETIR-', '-PROXIMO-'):
            break
    janela.close()
```

- [ ] **Step 5: Rodar para confirmar que passa**

Run: `.venv/bin/python -m pytest tests/ -v`
Expected: `91 passed` (86 das tarefas anteriores + 5 novos)

- [ ] **Step 6: Commit**

```bash
git add modo_licao.py i18n.py tests/test_integracao_licao.py
git commit -m "licao: registro do historico e relatorio que aponta o criterio que faltou"
```

---

### Task 17: Ligar o Modo Lição ao menu e fazer o treino livre gravar histórico

**Files:**
- Modify: `TouchTypingTrainer.py`
- Modify: `i18n.py`
- Delete: `keyboards.py`

**Interfaces:**
- Consumes: tudo até a Task 16
- Produces: `TouchTypingTrainer.rodar_licao(idioma) -> None` e o botão do menu

- [ ] **Step 1: Acrescentar os textos ao `i18n.py`**

```python
        'menu_modo_licao': 'Modo Lição (aprender a digitar sem olhar)',
        'menu_treino_livre': 'Treino livre',
        'historico_caiu_para_usuario': 'A pasta do programa é somente-leitura. Seu progresso será gravado em {}.',
```

Remover do `translations`, nos três idiomas, as chaves do desenho ASCII que o teclado desenhado aposenta: `full_keyboard_ascii_art`, `hand_guide_text_intro`, `hand_guide_text_tips`, `general_keyboard_layout_label`, e a função `get_formatted_focused_ascii` junto do seu bloco de rótulos de dedo.

- [ ] **Step 2: Ligar o Modo Lição**

Em `TouchTypingTrainer.py`, trocar o import do `keyboards`/`get_formatted_focused_ascii` e acrescentar os novos:

```python
import historico
import layouts
import licoes
import metricas
import modo_licao
```

Substituir inteira a função `show_hand_positioning_guide` por uma que abre o teclado desenhado:

```python
def show_hand_positioning_guide():
    """Guia de mãos: agora o teclado desenhado, colorido por dedo.

    Substitui o desenho ASCII em fonte monoespaçada. A informação é a mesma,
    mas aqui ela é dado consultável (`layouts.py`) e não texto.
    """
    import teclado_widget
    nome_layout = layouts.LAYOUT_POR_IDIOMA[current_lang]
    teclado = teclado_widget.Teclado(nome_layout, 900, 260, chave='-TECLADO_GUIA-')
    layout = [
        [sg.Text(get_text('hand_guide_title', current_lang), font=('Helvetica', 16))],
        [teclado.elemento()],
        [sg.Button(get_text('ok_button', current_lang), key='-OK-')],
    ]
    janela = sg.Window(get_text('hand_guide_title', current_lang), layout, modal=True,
                       finalize=True, element_justification='center', size=(960, 420))
    teclado.desenhar()
    while True:
        evento, _ = janela.read()
        if evento in (sg.WIN_CLOSED, '-OK-'):
            break
    janela.close()
```

Acrescentar a função que roda uma lição:

```python
def caminho_do_historico():
    """Resolve uma vez onde o progresso mora e avisa se caiu para a home."""
    global _caminho_do_historico, _ja_avisou_da_queda
    if _caminho_do_historico is None:
        _caminho_do_historico, caiu = historico.resolver_caminho(
            historico.pasta_do_executavel(), historico.pasta_do_usuario())
        if caiu and not _ja_avisou_da_queda:
            _ja_avisou_da_queda = True
            sg.popup(get_text('historico_caiu_para_usuario', current_lang).format(
                _caminho_do_historico), keep_on_top=True)
    return _caminho_do_historico


def rodar_licao(idioma):
    """Um ciclo do Modo Lição: tela prévia, exercício, avaliação e gravação."""
    nome_layout = layouts.LAYOUT_POR_IDIOMA[idioma]
    arquivo = caminho_do_historico()
    registros = historico.ler(arquivo)
    nivel = licoes.nivel_atual(registros, nome_layout)

    preferencias = historico.ler_preferencias(arquivo)
    ja_sabia = bool(preferencias.get('teclado_sem_rollover'))
    comecar, sem_rollover = modo_licao.tela_previa(nivel, nome_layout, idioma, ja_sabia)
    if sem_rollover and not ja_sabia:
        # Descoberto agora: grava para não cobrar 15 segundos de espera de novo.
        historico.gravar_preferencia(arquivo, 'teclado_sem_rollover', True)
    if not comecar:
        return

    semente = int(time.time())
    if nivel.numero >= 12:
        frases = get_text('short_sentences', idioma) + get_text('long_sentences', idioma)
        permitidas = licoes.teclas_liberadas(nome_layout, nivel.numero)
        candidatas = licoes.filtrar_frases(frases, permitidas) or frases
        texto = random.Random(semente).choice(candidatas)
    else:
        texto = licoes.gerar_exercicio(nome_layout, nivel.numero, semente)

    limite = licoes.limite_de_tempo(len(texto), nivel.wpm_meta)
    resultado = modo_licao.executar_exercicio(texto, nome_layout, idioma, limite)
    if resultado['cancelado']:
        return

    registro = modo_licao.montar_registro(nivel, nome_layout, idioma, texto, semente, resultado)
    avaliacao = licoes.avaliar(registro, nivel)
    registro['aprovado'] = avaliacao.aprovado
    historico.gravar(registro, arquivo)
    modo_licao.mostrar_relatorio(registro, avaliacao, idioma)
```

Declarar as duas variáveis de módulo junto das outras preferências, no topo do arquivo:

```python
# Resolvido uma vez por execução; o aviso de queda só aparece na primeira vez.
_caminho_do_historico = None
_ja_avisou_da_queda = False
```

- [ ] **Step 3: Acrescentar o botão ao menu**

Em `create_main_window`, imediatamente antes do botão `-START_TRAINING-`, acrescentar:

```python
        [sg.Button(get_text('menu_modo_licao', lang_for_window), key='-MODO_LICAO-',
                   expand_x=True, font=('Helvetica', 13),
                   button_color=('white', 'darkgreen'))],
```

E trocar o rótulo do botão existente `-START_TRAINING-` de `start_training_button` para `menu_treino_livre`.

No laço de eventos de `main`, junto do tratamento de `-START_TRAINING-`:

```python
        elif event == '-MODO_LICAO-':
            rodar_licao(current_lang)
```

Aumentar o tamanho da janela principal em `create_main_window`, no `return`:

```python
    return sg.Window(app_window_title, layout, finalize=True,
                     element_justification='center', size=(800, 860))
```

- [ ] **Step 4: Fazer o treino livre gravar histórico**

Ao fim de `start_training_session`, logo antes de abrir a janela do relatório, acrescentar:

```python
    # O treino livre também entra no histórico, com modo 'livre' — ele não conta
    # para a progressão do currículo, mas conta para a evolução ao longo do tempo.
    historico.gravar({
        'quando': datetime.now().astimezone().isoformat(timespec='seconds'),
        'modo': 'livre',
        'nivel': None,
        'idioma': lang_code,
        'layout': layouts.LAYOUT_POR_IDIOMA[lang_code],
        'alvo': target_sentence,
        'duracao_s': round(final_elapsed_time, 2),
        'wpm_bruto': round(metricas.wpm(report_data['typed_length'], final_elapsed_time), 2),
        'wpm_liquido': round(metricas.wpm_liquido(
            report_data['typed_length'], final_elapsed_time, report_data['errors']), 2),
        'tropecos': final_persistent_errors,
        'total_teclas': target_len,
        'regularidade': None,      # o treino livre não mede intervalo por tecla
        'aprovado': None,
        'teclas': {},
    }, caminho_do_historico())
```

E acrescentar a linha do WPM ao layout do relatório do treino livre, logo depois da linha de `report_time_taken`:

```python
        [sg.Text(f"WPM: {metricas.wpm(report_data['typed_length'], final_elapsed_time):.1f}")],
```

Acrescentar `from datetime import datetime` aos imports do arquivo.

- [ ] **Step 5: Apagar o ASCII aposentado**

```bash
git rm keyboards.py
```

- [ ] **Step 6: Verificar o programa inteiro**

Run: `.venv/bin/python -m pytest tests/ -v && .venv/bin/python TouchTypingTrainer.py`

Expected:
- `91 passed`
- a janela principal abre em 800×860 com o botão verde **Modo Lição** acima de **Treino livre**
- **Guia de Mãos** abre o teclado desenhado, colorido por dedo, sem nenhum ASCII
- **Modo Lição** abre a tela prévia no nível 1 (`base-esquerda`)
- completar um exercício grava uma linha em `dados/progresso.jsonl`:
  `cat dados/progresso.jsonl | tail -1`
- **Treino livre** continua funcionando como antes e agora mostra WPM no relatório
- trocar de idioma continua recriando a janela sem texto cortado

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "app: Modo Licao no menu, guia de maos desenhado e treino livre gravando historico"
```

---

### Task 18: Documentação e empacotamento

**Files:**
- Modify: `LEIA-ME.md`
- Modify: `docs/ARQUITETURA.md`
- Modify: `docs/BUILD.md`
- Modify: `docs/LICOES_APRENDIDAS.md`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: tudo
- Produces: documentação em dia e binários das duas edições

- [ ] **Step 1: Ignorar os dados de progresso e os PNGs gerados**

Acrescentar ao `.gitignore`:

```
dados/
assets/maos/*.png
```

Os PNGs são gerados pelo `build.py` a partir dos SVGs versionados — versionar os
dois seria manter a mesma informação em dois lugares.

- [ ] **Step 2: Atualizar o `LEIA-ME.md`**

Na tabela **Estrutura**, remover a linha do `keyboards.py` e acrescentar:

```markdown
| `metricas.py` | WPM, tropeços e regularidade do ritmo (sem GUI) |
| `historico.py` | onde o progresso mora e como é lido/gravado (sem GUI) |
| `layouts.py` | os três teclados e o mapa tecla→dedo (sem GUI) |
| `licoes.py` | currículo de 12 níveis, gerador e critério (sem GUI) |
| `teclas_pressionadas.py` | quais teclas estão seguradas, apesar do auto-repeat |
| `teclado_widget.py` | teclado desenhado no Canvas, com cor por dedo |
| `modo_licao.py` | tela prévia com teste de mãos e exercício travado |
| `tests/` | suíte pytest dos módulos sem GUI |
```

E acrescentar uma seção nova, depois de "O que o programa faz":

```markdown
## Modo Lição

Doze níveis, do `asdf` isolado ao texto corrido, feitos para construir memória
muscular em vez de medir quem já sabe digitar:

- **Teste de mãos antes de começar** — o botão só habilita depois de você pousar
  cada mão na linha-base e pressionar as quatro teclas ao mesmo tempo. Nenhum
  software sabe qual dedo você usou, mas quatro teclas simultâneas provam que a
  mão está na posição.
- **Tecla errada não entra** — o texto não avança, não há backspace e não há
  como colar. Você repete até acertar.
- **Teclado desenhado** mostra a próxima tecla e o dedo aceso na mão.
- **Só passa de nível** com no máximo 3% de tropeços, o WPM da meta e ritmo
  regular, em dois exercícios seguidos. Ritmo picotado reprova mesmo com 100% de
  acerto: é o sinal de quem procura a tecla com o olho.

O progresso fica em `dados/progresso.jsonl`, ao lado do executável — copiou a
pasta, levou o histórico.

## Rodando os testes

```bash
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pytest tests/ -v
```
```

- [ ] **Step 3: Atualizar o `docs/ARQUITETURA.md`**

Substituir a tabela de módulos pela nova (a mesma da seção Arquitetura deste
plano) e acrescentar ao fim:

```markdown
## Por que JSON Lines e não SQLite

Com um usuário só, sem escrita concorrente e com histórico na casa dos poucos
megabytes, o SQLite cobraria migração de esquema a cada campo novo sem entregar
nada perceptível. O JSONL acrescenta linha — queda de energia não corrompe o que
já estava gravado —, aceita campo novo sem migração e abre no editor de texto.

O que se perde, e é aceito: consulta indexada. A tela de progresso lê o arquivo
inteiro. Se um dia isso incomodar, o caminho é gerar um resumo agregado, não
trocar de banco.

## Por que a regularidade usa mediana e não média

O índice conta quantos intervalos entre teclas passam de 3× o intervalo típico —
é o sinal de quem parou para procurar a tecla com o olho. Se o "típico" fosse a
média, uma única pausa longa (o telefone tocou) arrastaria o limiar para cima e
mascararia todas as outras paradas. Com a mediana, uma pausa isolada é só um
ponto fora da curva, e o restante do ritmo continua sendo medido.

As três primeiras teclas são descartadas: tempo de reação no começo do exercício
não é hesitação. E com menos de 10 intervalos válidos o índice fica indefinido em
vez de chutar — exercício curto não reprova ninguém por ritmo.

## Por que o teste de mãos é de quatro teclas e não de oito

Pedir `asdf`+`jkl;` de uma vez seria a prova mais forte de que as duas mãos estão
pousadas. Só que teclado de membrana comum reporta no máximo ~6 teclas
simultâneas, e alguns travam em combinações específicas — o programa culparia o
usuário por um limite do equipamento dele.

Por isso o teste é de uma mão por vez. Quatro teclas simultâneas passam em
praticamente qualquer teclado, e continuam sendo impossíveis de simular digitando
uma de cada vez. Quando nem isso fecha, o programa cai no modo sequencial e diz
que o limite é do teclado.
```

- [ ] **Step 4: Registrar as armadilhas em `docs/LICOES_APRENDIDAS.md`**

Acrescentar:

```markdown
## Auto-repeat do X11 desfaz o teste de teclas simultâneas

Segurar uma tecla no Linux gera `KeyRelease` + `KeyPress` repetidos e colados.
Quem acreditar no `KeyRelease` conclui que o usuário soltou, e o teste de mãos
pisca sem nunca fechar. A solução é não acreditar num soltar imediatamente:
ele fica em dúvida por 50 ms, e um novo pressionar da mesma tecla o cancela
(`teclas_pressionadas.py`).

## Rollover: teclado de membrana não reporta oito teclas

O teste de mãos foi desenhado com **quatro** teclas (uma mão por vez) porque
teclado comum reporta no máximo ~6 simultâneas e alguns travam antes disso.
Pedir as oito de uma vez faria o programa culpar o usuário por um limite do
equipamento. `tools/sonda_teclas.py` mede o limite do teclado à mão.

## Retângulo novo no Graph nasce por cima do texto

Repintar uma tecla apagando e redesenhando o retângulo esconde a letra que
estava por cima. É preciso `tk_canvas.tag_raise(id_do_texto)` depois de
redesenhar (`teclado_widget.pintar`).
```

- [ ] **Step 5: Atualizar o `docs/BUILD.md`**

Acrescentar a seção do roteiro de verificação manual, já que a parte com GUI não
tem teste automatizado:

```markdown
## Verificação manual antes de empacotar

A lógica é coberta por `pytest`; a interface não. Antes de gerar binário, rodar:

1. `.venv/bin/python -m pytest tests/ -v` — tudo verde.
2. `.venv/bin/python tools/ver_teclado.py` — os três layouts desenham certo e a
   linha-base acende exatamente 8 teclas em cada um.
3. `.venv/bin/python TouchTypingTrainer.py` → **Modo Lição**:
   - o botão Começar nasce desabilitado;
   - segurar `asdf` e depois `jkl`+quarta tecla habilita;
   - **num teclado de membrana barato**, não só no mecânico — é onde o rollover
     aparece;
   - tecla errada não avança o texto; Ctrl+V não cola; Backspace não apaga.
4. Conferir que `dados/progresso.jsonl` ganhou uma linha por exercício.
```

E acrescentar, na seção de empacotamento, que o `build.py` agora gera os PNGs das
mãos antes de chamar o PyInstaller e precisa do `rsvg-convert`
(`sudo apt install librsvg2-bin`) ou do `inkscape` no PATH.

- [ ] **Step 6: Empacotar e conferir**

Run: `.venv/bin/python build.py free`
Expected: `dist/linux/TouchTypingTrainer` gerado sem erro.

Run: `./dist/linux/TouchTypingTrainer`
Expected: o Modo Lição abre, o teste de mãos funciona, e o progresso é gravado em
`dist/linux/dados/progresso.jsonl` (ao lado do binário, não na home).

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "docs: Modo Licao no LEIA-ME, arquitetura, licoes aprendidas e roteiro de verificacao"
```

---

## Verificação final

- [ ] `.venv/bin/python -m pytest tests/ -v` → 91 passed
- [ ] `dados/progresso.jsonl` recebe uma linha por exercício, nos dois modos
- [ ] O binário empacotado grava ao lado de si, não na home
- [ ] O teste de mãos foi validado num teclado de membrana real, não só no de desenvolvimento
- [ ] Nenhum import de `keyboards` sobrou: `grep -rn "keyboards" --include=*.py .`
