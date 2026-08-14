"""Confere a aparência na JANELA MONTADA, não na paleta.

Este arquivo existe por causa de um defeito que passou por todos os outros
testes: a paleta estava correta, o contraste calculado passava, e mesmo assim o
aplicativo abria com fundo cinza-ardósia e texto cinza em cima — ilegível — só
porque o tema nunca era aplicado à janela nova.

A lição: contraste medido na constante não prova nada sobre o que chegou à tela.
Aqui as cores são lidas dos widgets Tk de verdade.
"""
import math
import os

import pytest

import tema

pytestmark = pytest.mark.skipif(
    not os.environ.get('DISPLAY') and not os.environ.get('WAYLAND_DISPLAY'),
    reason='sem servidor gráfico para montar a janela')


def _rgb(widget, cor):
    """Converte a cor de um widget Tk (nome ou #hex) em (r, g, b) 0-255."""
    r, g, b = widget.winfo_rgb(cor)
    return (r >> 8, g >> 8, b >> 8)


def _luminancia(rgb):
    canais = []
    for v in rgb:
        c = v / 255
        canais.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * canais[0] + 0.7152 * canais[1] + 0.0722 * canais[2]


def _contraste(a, b):
    la, lb = _luminancia(a), _luminancia(b)
    claro, escuro = max(la, lb), min(la, lb)
    return (claro + 0.05) / (escuro + 0.05)


@pytest.fixture
def previa(tmp_path):
    """A tela prévia montada de verdade, com o tema aplicado."""
    import aplicativo
    app = aplicativo.Aplicativo('pt', tmp_path / 'progresso.jsonl')
    app._montar()
    app.ir_para('previa')
    yield app
    app.janela.close()


def test_o_fundo_da_janela_e_claro(previa):
    fundo = _rgb(previa.janela.TKroot, previa.janela.TKroot['background'])
    assert _luminancia(fundo) > 0.6, f'fundo escuro demais: {fundo}'


@pytest.mark.parametrize('chave', [
    '-PREVIA_TITULO-', '-PREVIA_CRITERIO-', '-PREVIA_AVANCAR-',
    '-PREVIA_INSTRUCAO-', '-PREVIA_NOVAS-',
])
def test_todo_texto_da_tela_previa_e_legivel(previa, chave):
    """Contraste do texto contra o fundo QUE ELE REALMENTE TEM na tela.

    O defeito original era exatamente isto: `#5f6368` sobre `#ffffff` dá 5,9:1,
    mas sobre o cinza do tema padrão dava menos de 2:1.
    """
    widget = previa.janela[chave].Widget
    frente = _rgb(widget, widget.cget('foreground'))
    fundo = _rgb(widget, widget.cget('background'))
    razao = _contraste(frente, fundo)
    assert razao >= 4.5, f'{chave}: {razao:.2f}:1 (frente {frente}, fundo {fundo})'


def test_o_fundo_do_texto_bate_com_o_fundo_do_desenho(previa):
    """O teclado é uma imagem com fundo próprio; se não bater, vira um retângulo
    recortado no meio da tela."""
    rotulo = previa.janela['-PREVIA_TITULO-'].Widget
    fundo_da_tela = _rgb(rotulo, rotulo.cget('background'))
    import teclado_widget
    fundo_do_desenho = _rgb(rotulo, teclado_widget.COR_DE_FUNDO)
    assert math.dist(fundo_da_tela, fundo_do_desenho) < 12, (
        f'tela {fundo_da_tela} x desenho {fundo_do_desenho}')


def test_o_botao_de_comecar_tem_texto_legivel(previa):
    botao = previa.janela['-PREVIA_COMECAR-'].Widget
    frente = _rgb(botao, botao.cget('foreground'))
    fundo = _rgb(botao, botao.cget('background'))
    assert _contraste(frente, fundo) >= 4.5


def test_o_tema_do_projeto_esta_ativo(previa):
    from gui_backend import sg
    assert sg.theme() == tema.NOME_DO_TEMA


@pytest.mark.parametrize('nome_da_tela', ['guia', 'exercicio', 'relatorio'])
def test_as_outras_telas_tambem_montam_com_o_tema(tmp_path, nome_da_tela):
    import aplicativo
    import licoes
    import metricas
    app = aplicativo.Aplicativo('pt', tmp_path / 'progresso.jsonl')
    app._montar()
    try:
        if nome_da_tela == 'relatorio':
            # O relatório precisa de um resultado já apurado para se montar.
            texto = app.sessao.texto_do_exercicio()
            app.sessao.concluir_exercicio(texto, {
                'batidas': [metricas.Batida(c, c, 200.0) for c in texto],
                'duracao_s': 20.0, 'cancelado': False})
        assert app.ir_para(nome_da_tela)
        rotulo = app.janela.TKroot
        fundo = _rgb(rotulo, rotulo['background'])
        assert _luminancia(fundo) > 0.6
        assert licoes.curriculo('abnt2')      # sanidade do módulo
    finally:
        app.janela.close()


def test_a_tela_de_progresso_monta_com_historico_de_verdade(tmp_path):
    """Monta a tela com dados reais gravados, não com histórico vazio.

    Tela que só foi vista vazia esconde erro de formatação de número, de coluna
    a mais na tabela e de chave de tradução usada só quando há dado.
    """
    import aplicativo
    import historico
    import licoes
    import metricas
    import modo_licao

    arquivo = tmp_path / 'progresso.jsonl'
    nivel = licoes.curriculo('abnt2')[0]
    for semente in (1, 2, 3):
        texto = licoes.gerar_exercicio('abnt2', 1, semente)
        # Um erro a cada cinco teclas, para o ranking ter o que mostrar.
        batidas = [metricas.Batida(c, 'x' if i % 5 == 0 else c, 220.0)
                   for i, c in enumerate(texto)]
        registro = modo_licao.montar_registro(
            nivel, 'abnt2', 'pt', texto, semente,
            {'batidas': batidas, 'duracao_s': 25.0, 'cancelado': False})
        registro['aprovado'] = False
        historico.gravar(registro, arquivo)

    app = aplicativo.Aplicativo('pt', arquivo)
    app._montar()
    try:
        assert app.ir_para('progresso')
        janela = app.janela
        assert janela['-PROG_RESUMO-'].get()
        # As três tabelas têm de ter linha: com erro gravado, nenhuma pode estar
        # vazia — vazio aqui significaria que o diagnóstico não achou o dado.
        assert janela['-PROG_DIAS-'].Values
        assert janela['-PROG_TECLAS-'].Values
        assert janela['-PROG_DEDOS-'].Values
        # E o texto do dedo tem de estar traduzido, não com a chave crua.
        primeiro_dedo = janela['-PROG_DEDOS-'].Values[0][0]
        assert 'dedo_' not in primeiro_dedo and 'mao_' not in primeiro_dedo
    finally:
        app.janela.close()


def test_a_tela_de_progresso_monta_sem_historico(tmp_path):
    import aplicativo
    app = aplicativo.Aplicativo('pt', tmp_path / 'vazio.jsonl')
    app._montar()
    try:
        assert app.ir_para('progresso')
        assert app.janela['-PROG_TECLAS-'].Values == []
        assert app.janela['-PROG_RESUMO-'].get()      # mostra o aviso de vazio
    finally:
        app.janela.close()
