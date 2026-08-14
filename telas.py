"""As telas do Modo Lição, todas dentro de UMA janela.

## Por que não são janelas separadas

Cada `sg.Window` modal que abre rouba o foco do teclado e muda o que está sob os
olhos. Num treinador de digitação isso é pior que desconforto: o aluno tira as
mãos da linha-base para achar o botão da janela nova — que é exatamente o hábito
que o programa existe para desfazer.

Aqui cada tela é uma `sg.Column` da mesma janela, e trocar de tela é mudar
visibilidade. A janela tem tamanho fixo, então nada salta nem se redimensiona
entre uma tela e outra: o teclado desenhado fica sempre no mesmo lugar da tela.

## Como uma tela funciona

Cada uma implementa quatro coisas, e o laço de eventos da janela chama nessa
ordem:

- `coluna()`   — monta o layout, uma vez, na criação da janela;
- `preparar()` — chamado toda vez que a tela passa a ser a visível;
- `evento()`   — reage a um evento; devolve o nome da próxima tela ou None;
- `tique()`    — chamado a cada volta do laço, mesmo sem evento (cronômetro,
                 teclas seguradas); devolve o nome da próxima tela ou None.

Nenhuma tela abre janela nem tem laço próprio. Quem tem laço é o aplicativo.
"""
import time

import layouts
import licoes
import maos_widget
import metricas
import modo_licao
import teclado_widget
import teclas_pressionadas
import tema
from gui_backend import sg
from i18n import get_text

# Tempo que as quatro teclas precisam ficar juntas para o passo valer.
MS_PARA_CONFIRMAR = 400.0
# Depois disso sem conseguir, assume-se limite de rollover do teclado.
SEGUNDOS_ATE_OFERECER_SEQUENCIAL = 15.0

LARGURA_DO_TECLADO = 940
ALTURA_DO_TECLADO = 250
LARGURA_DAS_MAOS = 300
ALTURA_DAS_MAOS = 198


def agora_ms():
    return time.monotonic() * 1000.0


class Tela:
    """Contrato comum. `nome` é a chave usada para trocar de tela."""
    nome = ''

    def __init__(self, app):
        self.app = app

    @property
    def idioma(self):
        return self.app.idioma

    @property
    def nome_layout(self):
        return layouts.LAYOUT_POR_IDIOMA[self.app.idioma]

    def coluna(self):
        raise NotImplementedError

    def preparar(self, **contexto):
        pass

    def evento(self, nome, valores):
        return None

    def tique(self, instante):
        return None


class TelaGuia(Tela):
    """Consulta: o teclado inteiro colorido por dedo, com a linha-base marcada."""
    nome = 'guia'

    def coluna(self):
        self.teclado = teclado_widget.Teclado(
            self.nome_layout, LARGURA_DO_TECLADO, ALTURA_DO_TECLADO, chave='-TECLADO_GUIA-')
        self.maos = maos_widget.Maos(
            LARGURA_DAS_MAOS, ALTURA_DAS_MAOS, chave='-MAOS_GUIA-')
        return sg.Column([
            [sg.Text('', key='-GUIA_TITULO-', font=tema.texto(tema.TAMANHO_TITULO, True),
                     text_color=tema.TEXTO)],
            [sg.Text('', key='-GUIA_SUB-', font=tema.texto(tema.TAMANHO_CORPO),
                     text_color=tema.TEXTO_SECUNDARIO)],
            [self.maos.elemento()],
            [self.teclado.elemento()],
            [sg.Button('', key='-GUIA_VOLTAR-', font=tema.texto(tema.TAMANHO_CORPO))],
        ], key=f'-TELA_{self.nome.upper()}-', visible=False,
            element_justification='center', expand_x=True)

    def desenhar_inicial(self):
        self.teclado.desenhar()
        self.maos.desenhar()

    def preparar(self, **contexto):
        janela = self.app.janela
        janela['-GUIA_TITULO-'].update(get_text('hand_guide_title', self.idioma))
        janela['-GUIA_SUB-'].update(get_text('licao_teste_esquerda', self.idioma))
        janela['-GUIA_VOLTAR-'].update(get_text('licao_voltar', self.idioma))
        self.teclado.limpar_estados()
        esquerda, direita = layouts.teclas_base(self.nome_layout)
        for caractere in esquerda + direita:
            self.teclado.pintar(caractere, 'proxima')

    def evento(self, nome, valores):
        if nome == '-GUIA_VOLTAR-':
            return 'menu'
        return None


class TelaPrevia(Tela):
    """O portão: só libera o exercício depois do teste de mãos."""
    nome = 'previa'

    def coluna(self):
        self.teclado = teclado_widget.Teclado(
            self.nome_layout, LARGURA_DO_TECLADO, ALTURA_DO_TECLADO, chave='-TECLADO_PREVIA-')
        self.maos = maos_widget.Maos(
            LARGURA_DAS_MAOS, ALTURA_DAS_MAOS, chave='-MAOS_PREVIA-')
        return sg.Column([
            [sg.Text('', key='-PREVIA_TITULO-', font=tema.texto(tema.TAMANHO_TITULO, True),
                     text_color=tema.TEXTO)],
            [sg.Text('', key='-PREVIA_NOVAS-', font=tema.mono(tema.TAMANHO_DESTAQUE, True),
                     text_color=tema.PRIMARIA)],
            [sg.Text('', key='-PREVIA_CRITERIO-', font=tema.texto(tema.TAMANHO_APOIO),
                     text_color=tema.TEXTO_SECUNDARIO)],
            [sg.Text('', key='-PREVIA_AVANCAR-', font=tema.texto(tema.TAMANHO_APOIO),
                     text_color=tema.TEXTO_SECUNDARIO)],
            [sg.HorizontalSeparator()],
            [sg.Text('', key='-PREVIA_INSTRUCAO-',
                     font=tema.texto(tema.TAMANHO_SUBTITULO, True), text_color=tema.TEXTO)],
            [sg.Text('', key='-PREVIA_DETALHE-', font=tema.texto(tema.TAMANHO_CORPO),
                     text_color=tema.ERRO)],
            [self.maos.elemento()],
            [self.teclado.elemento()],
            [sg.Text('', key='-PREVIA_AVISO-', font=tema.texto(tema.TAMANHO_APOIO),
                     text_color=tema.ATENCAO, size=(110, 2))],
            [sg.Button('', key='-PREVIA_COMECAR-', disabled=True,
                       font=tema.texto(tema.TAMANHO_SUBTITULO, True),
                       button_color=(tema.SOBRE_PRIMARIA, tema.PRIMARIA)),
             sg.Button('', key='-PREVIA_VOLTAR-', font=tema.texto(tema.TAMANHO_CORPO))],
        ], key=f'-TELA_{self.nome.upper()}-', visible=False,
            element_justification='center', expand_x=True)

    def desenhar_inicial(self):
        self.teclado.desenhar()
        self.maos.desenhar()

    def preparar(self, **contexto):
        sessao = self.app.sessao
        nivel = sessao.nivel
        esquerda, direita = layouts.teclas_base(self.nome_layout)
        self.passos = [('licao_teste_esquerda', esquerda, 'esquerda'),
                       ('licao_teste_direita', direita, 'direita')]
        self.passo = 0
        self.confirmando_desde = None
        self.sequencial = sessao.teclado_sem_rollover
        self.proxima_sequencial = 0
        self.inicio = agora_ms()
        self.rastreador = teclas_pressionadas.Rastreador()

        janela = self.app.janela
        janela['-PREVIA_TITULO-'].update(
            get_text('licao_titulo', self.idioma).format(nivel.numero, nivel.id))
        janela['-PREVIA_NOVAS-'].update('   '.join(nivel.teclas_novas) or '—')
        janela['-PREVIA_CRITERIO-'].update(get_text('licao_criterio', self.idioma).format(
            int(licoes.MAXIMO_DE_TROPECOS * 100), nivel.wpm_meta))
        janela['-PREVIA_AVANCAR-'].update(get_text('licao_para_avancar', self.idioma).format(
            licoes.APROVACOES_SEGUIDAS, sessao.aprovacoes))
        janela['-PREVIA_COMECAR-'].update(get_text('licao_comecar', self.idioma), disabled=True)
        janela['-PREVIA_VOLTAR-'].update(get_text('licao_voltar', self.idioma))
        janela['-PREVIA_AVISO-'].update(
            get_text('licao_teste_sequencial', self.idioma) if self.sequencial else '')
        janela['-PREVIA_DETALHE-'].update('')
        self.teclado.limpar_estados()
        self.maos.limpar()

    def evento(self, nome, valores):
        if nome == '-PREVIA_VOLTAR-':
            return 'menu'
        if nome == '-PREVIA_COMECAR-':
            return 'exercicio'
        if nome in ('-DOWN-', '-UP-'):
            self._tecla(nome)
        return None

    def _tecla(self, evento):
        caractere = self.app.caractere_do_evento()
        if not caractere:
            return
        instante = agora_ms()
        if evento == '-UP-':
            self.rastreador.soltou(caractere, instante)
            return
        self.rastreador.pressionou(caractere, instante)
        # Caractere que este layout não tem = teclado do sistema noutro layout.
        if (self.passo < len(self.passos)
                and layouts.dedo_de(caractere, self.nome_layout) is None):
            self.app.janela['-PREVIA_AVISO-'].update(
                get_text('licao_layout_diferente', self.idioma).format(
                    caractere, ' '.join(self.passos[self.passo][1])))

    def tique(self, instante):
        if self.passo >= len(self.passos):
            return None
        janela = self.app.janela
        _, esperadas, mao_da_vez = self.passos[self.passo]
        ativas = self.rastreador.ativas(instante)

        for caractere in esperadas:
            self.teclado.pintar(caractere, 'certa' if caractere in ativas else 'proxima')

        if self.sequencial:
            alvo = esperadas[self.proxima_sequencial]
            self.maos.destacar(mao_da_vez, layouts.dedo_de(alvo, self.nome_layout)[1])
            self.teclado.marcar(alvo)
            janela['-PREVIA_DETALHE-'].update(
                modo_licao.descrever_tecla(alvo, self.nome_layout, self.idioma))
            if alvo in ativas:
                self.proxima_sequencial += 1
                if self.proxima_sequencial >= len(esperadas):
                    self.proxima_sequencial = 0
                    self._concluir_passo()
        else:
            self.maos.destacar(mao_da_vez, 'indicador')
            janela['-PREVIA_DETALHE-'].update('   '.join(
                get_text('licao_espaco', self.idioma) if c == ' ' else c.upper()
                for c in esperadas))
            completo = set(esperadas) <= ativas
            if completo:
                self.confirmando_desde = self.confirmando_desde or instante
                if instante - self.confirmando_desde >= MS_PARA_CONFIRMAR:
                    self.confirmando_desde = None
                    self._concluir_passo()
            else:
                self.confirmando_desde = None
            if (not completo and self.passo == 0
                    and instante - self.inicio > SEGUNDOS_ATE_OFERECER_SEQUENCIAL * 1000):
                self.sequencial = True
                self.app.sessao.registrar_sem_rollover()
                janela['-PREVIA_AVISO-'].update(
                    get_text('licao_teste_sequencial', self.idioma))

        if self.passo < len(self.passos):
            janela['-PREVIA_INSTRUCAO-'].update(
                get_text(self.passos[self.passo][0], self.idioma))
        return None

    def _concluir_passo(self):
        self.passo += 1
        self.teclado.limpar_estados()
        if self.passo >= len(self.passos):
            janela = self.app.janela
            janela['-PREVIA_INSTRUCAO-'].update(get_text('licao_teste_ok', self.idioma))
            janela['-PREVIA_DETALHE-'].update('')
            janela['-PREVIA_COMECAR-'].update(disabled=False)
            self.maos.limpar()


class TelaExercicio(Tela):
    """O exercício travado: tecla errada não entra e o texto não avança."""
    nome = 'exercicio'
    MAXIMO_DE_CARACTERES = 160     # teto do que cabe na faixa da frase

    def coluna(self):
        self.teclado = teclado_widget.Teclado(
            self.nome_layout, LARGURA_DO_TECLADO, ALTURA_DO_TECLADO,
            chave='-TECLADO_EXERCICIO-')
        self.maos = maos_widget.Maos(
            LARGURA_DAS_MAOS, ALTURA_DAS_MAOS, chave='-MAOS_EXERCICIO-')
        # Um Text por caractere, criado uma vez e reaproveitado a cada exercício:
        # recriar elemento exigiria recriar a janela, que é o que se quer evitar.
        self.alvos = [
            sg.Text(' ', key=f'-ALVO_{i}-', font=tema.mono(tema.TAMANHO_EXERCICIO, True),
                    pad=(0, 0), text_color=tema.TEXTO_SECUNDARIO)
            for i in range(self.MAXIMO_DE_CARACTERES)]
        return sg.Column([
            [sg.Text('', key='-EX_SERIE-', font=tema.texto(tema.TAMANHO_CORPO),
                     text_color=tema.TEXTO_SECUNDARIO),
             sg.Push(),
             sg.Text('', key='-EX_TEMPO-', font=tema.texto(tema.TAMANHO_CORPO),
                     text_color=tema.TEXTO_SECUNDARIO),
             sg.Text('    '),
             sg.Text('', key='-EX_PROGRESSO-', font=tema.texto(tema.TAMANHO_CORPO),
                     text_color=tema.TEXTO_SECUNDARIO)],
            [sg.Column([self.alvos], background_color=tema.SUPERFICIE_VARIANTE,
                       pad=(6, 12), expand_x=True, key='-EX_FAIXA-')],
            [sg.Text('', key='-EX_PROXIMA-', font=tema.texto(tema.TAMANHO_DESTAQUE, True),
                     text_color=tema.ERRO)],
            [self.maos.elemento()],
            [self.teclado.elemento()],
            [sg.Button('', key='-EX_CANCELAR-', font=tema.texto(tema.TAMANHO_CORPO))],
        ], key=f'-TELA_{self.nome.upper()}-', visible=False,
            element_justification='center', expand_x=True)

    def desenhar_inicial(self):
        self.teclado.desenhar()
        self.maos.desenhar()

    def preparar(self, **contexto):
        sessao = self.app.sessao
        self.texto = sessao.texto_do_exercicio()
        self.limite_s = licoes.limite_de_tempo(len(self.texto), sessao.nivel.wpm_meta)
        self.posicao = 0
        self.batidas = []
        self.inicio = agora_ms()
        self.ultima_batida = self.inicio

        janela = self.app.janela
        janela['-EX_CANCELAR-'].update(get_text('licao_cancelar', self.idioma))
        janela['-EX_SERIE-'].update(sessao.rotulo_da_serie(self.idioma))
        for i, elemento in enumerate(self.alvos):
            if i < len(self.texto):
                elemento.update(self.texto[i], text_color=tema.TEXTO_SECUNDARIO,
                                visible=True)
            else:
                elemento.update(' ', visible=False)
        self._destacar_proxima()

    def _destacar_proxima(self):
        janela = self.app.janela
        self.teclado.limpar_estados()
        if self.posicao >= len(self.texto):
            self.maos.limpar()
            janela['-EX_PROXIMA-'].update('')
            return
        alvo = self.texto[self.posicao]
        self.teclado.pintar(alvo, 'proxima')
        self.teclado.marcar(alvo)
        janela['-EX_PROXIMA-'].update(
            modo_licao.descrever_tecla(alvo, self.nome_layout, self.idioma))
        par = layouts.dedo_de(alvo, self.nome_layout)
        if par:
            self.maos.destacar(par[0], par[1])
        else:
            self.maos.limpar()

    def evento(self, nome, valores):
        if nome == '-EX_CANCELAR-':
            return 'menu'
        if nome != '-DOWN-':
            return None
        caractere = self.app.caractere_do_evento()
        if caractere is None:
            return None      # modificador ou navegação: não é resposta
        instante = agora_ms()
        esperado = self.texto[self.posicao]
        self.batidas.append(metricas.Batida(esperado=esperado, digitado=caractere,
                                            ms=instante - self.ultima_batida))
        self.ultima_batida = instante
        if caractere == esperado.lower():
            self.alvos[self.posicao].update(text_color=tema.SUCESSO)
            self.posicao += 1
            if self.posicao >= len(self.texto):
                return self._encerrar()
            self._destacar_proxima()
        else:
            # A tecla errada NÃO entra: o alvo não avança e a certa continua acesa.
            self.alvos[self.posicao].update(text_color=tema.ERRO)
            self.teclado.pintar(caractere, 'errada')
        return None

    def tique(self, instante):
        decorrido = (instante - self.inicio) / 1000.0
        janela = self.app.janela
        janela['-EX_TEMPO-'].update(
            get_text('licao_tempo', self.idioma).format(decorrido, self.limite_s))
        janela['-EX_PROGRESSO-'].update(
            get_text('licao_progresso', self.idioma).format(self.posicao, len(self.texto)))
        if decorrido >= self.limite_s:
            return self._encerrar()
        return None

    def _encerrar(self):
        duracao = (agora_ms() - self.inicio) / 1000.0
        self.app.sessao.concluir_exercicio(
            self.texto, {'batidas': self.batidas, 'duracao_s': duracao, 'cancelado': False})
        return 'relatorio'


class TelaRelatorio(Tela):
    """O resultado e o que fazer em seguida — sem sair da mesma área."""
    nome = 'relatorio'

    def coluna(self):
        return sg.Column([
            [sg.Text('', key='-REL_TITULO-', font=tema.texto(tema.TAMANHO_TITULO, True),
                     text_color=tema.TEXTO)],
            [sg.Text('', key='-REL_VEREDITO-', font=tema.texto(tema.TAMANHO_SUBTITULO, True))],
            [sg.HorizontalSeparator()],
            [sg.Text('', key='-REL_WPM-', font=tema.texto(tema.TAMANHO_CORPO),
                     text_color=tema.TEXTO)],
            [sg.Text('', key='-REL_TROPECOS-', font=tema.texto(tema.TAMANHO_CORPO),
                     text_color=tema.TEXTO)],
            [sg.Text('', key='-REL_RITMO-', font=tema.texto(tema.TAMANHO_CORPO),
                     text_color=tema.TEXTO)],
            [sg.Text('', key='-REL_SERIE-', font=tema.texto(tema.TAMANHO_CORPO),
                     text_color=tema.TEXTO_SECUNDARIO)],
            [sg.HorizontalSeparator()],
            [sg.Button('', key='-REL_CONTINUAR-',
                       font=tema.texto(tema.TAMANHO_SUBTITULO, True),
                       button_color=(tema.SOBRE_PRIMARIA, tema.PRIMARIA)),
             sg.Button('', key='-REL_REPETIR-', font=tema.texto(tema.TAMANHO_CORPO)),
             sg.Button('', key='-REL_MENU-', font=tema.texto(tema.TAMANHO_CORPO))],
        ], key=f'-TELA_{self.nome.upper()}-', visible=False,
            element_justification='center', expand_x=True)

    def preparar(self, **contexto):
        sessao = self.app.sessao
        registro, avaliacao = sessao.ultimo_resultado
        janela = self.app.janela
        motivos = ', '.join(get_text(f'licao_faltou_{f}', self.idioma)
                            for f in avaliacao.faltou)
        janela['-REL_TITULO-'].update(
            get_text('licao_relatorio_titulo', self.idioma).format(registro['nivel']))
        janela['-REL_VEREDITO-'].update(
            get_text('licao_aprovado', self.idioma) if avaliacao.aprovado
            else get_text('licao_reprovado', self.idioma).format(motivos),
            text_color=tema.SUCESSO if avaliacao.aprovado else tema.ATENCAO)
        janela['-REL_WPM-'].update(get_text('licao_wpm', self.idioma).format(
            registro['wpm_bruto'], registro['wpm_meta']))
        janela['-REL_TROPECOS-'].update(get_text('licao_tropecos_de', self.idioma).format(
            registro['tropecos'], registro['total_teclas']))
        ritmo = registro['regularidade']
        janela['-REL_RITMO-'].update(get_text('licao_regularidade', self.idioma).format(
            '—' if ritmo is None else f'{ritmo:.0%}'))
        janela['-REL_SERIE-'].update(sessao.rotulo_da_serie(self.idioma))
        # "Continuar" muda de sentido conforme sobrou exercício na série ou não.
        janela['-REL_CONTINUAR-'].update(
            get_text('licao_proximo' if sessao.tem_proximo() else 'licao_serie_fim',
                     self.idioma))
        janela['-REL_REPETIR-'].update(get_text('licao_repetir', self.idioma))
        janela['-REL_MENU-'].update(get_text('licao_voltar', self.idioma))

    def evento(self, nome, valores):
        sessao = self.app.sessao
        if nome == '-REL_MENU-':
            return 'menu'
        if nome == '-REL_REPETIR-':
            sessao.repetir_exercicio()
            return 'exercicio'
        if nome == '-REL_CONTINUAR-':
            if not sessao.tem_proximo():
                return 'menu'
            sessao.avancar()
            # Refaz o teste de mãos a cada exercício: é ele que garante que a
            # mão voltou à posição, e é rápido quando já se sabe fazer.
            return 'previa'
        return None


class TelaProgresso(Tela):
    """Evolução ao longo dos dias e diagnóstico de tecla e dedo.

    Só lê o histórico. Cada tabela usa `sg.Table` em vez de texto formatado à
    mão porque `sg.Table` alinha coluna sozinho — texto monoespaçado alinhado na
    unha quebra assim que uma tradução muda de largura.
    """
    nome = 'progresso'
    LINHAS_VISIVEIS = 7

    def coluna(self):
        def tabela(chave, cabecalhos, larguras):
            return sg.Table(
                values=[], headings=cabecalhos, key=chave,
                num_rows=self.LINHAS_VISIVEIS, col_widths=larguras,
                auto_size_columns=False, justification='center',
                font=tema.texto(tema.TAMANHO_APOIO),
                header_font=tema.texto(tema.TAMANHO_APOIO, True),
                background_color=tema.SUPERFICIE, text_color=tema.TEXTO,
                header_background_color=tema.SUPERFICIE_VARIANTE,
                header_text_color=tema.TEXTO, hide_vertical_scroll=True,
                expand_x=True)

        return sg.Column([
            [sg.Text('', key='-PROG_TITULO-', font=tema.texto(tema.TAMANHO_TITULO, True),
                     text_color=tema.TEXTO)],
            [sg.Text('', key='-PROG_RESUMO-', font=tema.texto(tema.TAMANHO_CORPO),
                     text_color=tema.TEXTO)],
            [sg.Text('', key='-PROG_TENDENCIA-',
                     font=tema.texto(tema.TAMANHO_SUBTITULO, True))],
            [sg.HorizontalSeparator()],
            [sg.Text('', key='-PROG_DIAS_TIT-', font=tema.texto(tema.TAMANHO_CORPO, True),
                     text_color=tema.TEXTO)],
            [tabela('-PROG_DIAS-', ['', '', '', ''], [14, 12, 12, 12])],
            [sg.Text('', key='-PROG_TECLAS_TIT-', font=tema.texto(tema.TAMANHO_CORPO, True),
                     text_color=tema.TEXTO)],
            [tabela('-PROG_TECLAS-', ['', '', '', ''], [10, 12, 12, 18])],
            [sg.Text('', key='-PROG_DEDOS_TIT-', font=tema.texto(tema.TAMANHO_CORPO, True),
                     text_color=tema.TEXTO)],
            [tabela('-PROG_DEDOS-', ['', '', ''], [26, 12, 12])],
            [sg.Button('', key='-PROG_VOLTAR-', font=tema.texto(tema.TAMANHO_CORPO))],
        ], key=f'-TELA_{self.nome.upper()}-', visible=False,
            element_justification='center', expand_x=True, scrollable=True,
            vertical_scroll_only=True)

    def preparar(self, **contexto):
        import progresso as mod_progresso
        janela = self.app.janela
        dados = mod_progresso.resumo(self.app.sessao.registros, self.nome_layout)
        t = lambda chave: get_text(chave, self.idioma)   # noqa: E731

        janela['-PROG_TITULO-'].update(t('prog_titulo'))
        janela['-PROG_VOLTAR-'].update(t('licao_voltar'))
        janela['-PROG_DIAS_TIT-'].update(t('prog_dias'))
        janela['-PROG_TECLAS_TIT-'].update(t('prog_teclas'))
        janela['-PROG_DEDOS_TIT-'].update(t('prog_dedos'))

        if not dados['exercicios']:
            janela['-PROG_RESUMO-'].update(t('prog_vazio'))
            janela['-PROG_TENDENCIA-'].update('')
            for chave in ('-PROG_DIAS-', '-PROG_TECLAS-', '-PROG_DEDOS-'):
                janela[chave].update(values=[])
            return

        janela['-PROG_RESUMO-'].update(
            t('prog_resumo').format(dados['exercicios'], dados['dias']))
        tendencia = dados['tendencia']
        if tendencia is None:
            janela['-PROG_TENDENCIA-'].update(t('prog_cedo'),
                                              text_color=tema.TEXTO_SECUNDARIO)
        elif tendencia >= 0:
            janela['-PROG_TENDENCIA-'].update(t('prog_subindo').format(tendencia),
                                              text_color=tema.SUCESSO)
        else:
            janela['-PROG_TENDENCIA-'].update(t('prog_caindo').format(abs(tendencia)),
                                              text_color=tema.ATENCAO)

        # Últimos dias primeiro: é o que interessa a quem quer saber como está hoje.
        dias = [[d['data'], d['exercicios'], f"{d['wpm_medio']:.1f}",
                 f"{d['precisao']:.1f}%"]
                for d in reversed(dados['evolucao'][-self.LINHAS_VISIVEIS:])]
        janela['-PROG_DIAS-'].update(values=dias)

        teclas = []
        for item in dados['teclas'][:self.LINHAS_VISIVEIS]:
            if not item['erros']:
                continue
            rotulo = t('licao_espaco') if item['tecla'] == ' ' else item['tecla'].upper()
            confusao = item['confusao']
            trocada = ('—' if not confusao else
                       f"{t('licao_espaco') if confusao[0] == ' ' else confusao[0].upper()}"
                       f"  ({confusao[1]}x)")
            teclas.append([rotulo, item['erros'], f"{item['taxa']:.1f}%", trocada])
        janela['-PROG_TECLAS-'].update(values=teclas)

        dedos = [[f"{get_text(f'dedo_{d['dedo']}', self.idioma)} "
                  f"{get_text(f'mao_{d['mao']}', self.idioma)}",
                  d['erros'], f"{d['taxa']:.1f}%"]
                 for d in dados['dedos'][:self.LINHAS_VISIVEIS] if d['erros']]
        janela['-PROG_DEDOS-'].update(values=dedos)

    def evento(self, nome, valores):
        if nome == '-PROG_VOLTAR-':
            return 'menu'
        return None


class TelaLivre(Tela):
    """Treino livre: frase sorteada, campo de texto solto, correção ao vivo.

    Diferente da lição de propósito. Aqui **não há trava**: dá para apagar,
    corrigir e até colar. É o modo de quem já sabe digitar e quer só medir —
    quem está aprendendo usa a lição, onde a tecla errada não entra.

    Por isso as duas métricas de erro continuam existindo só aqui: "erros no
    texto final" mede o produto, "tropeços" mede o caminho.
    """
    nome = 'livre'
    MAXIMO_DE_CARACTERES = 220

    def coluna(self):
        self.alvos = [
            sg.Text(' ', key=f'-LIVRE_ALVO_{i}-', pad=(0, 0),
                    font=tema.mono(tema.TAMANHO_DESTAQUE, True),
                    text_color=tema.TEXTO_SECUNDARIO)
            for i in range(self.MAXIMO_DE_CARACTERES)]
        return sg.Column([
            [sg.Text('', key='-LIVRE_ROTULO-', font=tema.texto(tema.TAMANHO_CORPO),
                     text_color=tema.TEXTO), sg.Push(),
             sg.Text('', key='-LIVRE_TEMPO-', font=tema.texto(tema.TAMANHO_CORPO),
                     text_color=tema.TEXTO_SECUNDARIO)],
            [sg.Column([self.alvos], scrollable=True, expand_x=True, pad=(6, 12),
                       background_color=tema.SUPERFICIE_VARIANTE, key='-LIVRE_FAIXA-')],
            [sg.Text('', key='-LIVRE_ENTRADA_ROTULO-',
                     font=tema.texto(tema.TAMANHO_CORPO), text_color=tema.TEXTO)],
            [sg.InputText(key='-LIVRE_ENTRADA-', font=tema.mono(tema.TAMANHO_DESTAQUE),
                          expand_x=True, enable_events=True)],
            [sg.Button('', key='-LIVRE_ENVIAR-', bind_return_key=True,
                       font=tema.texto(tema.TAMANHO_CORPO),
                       button_color=(tema.SOBRE_PRIMARIA, tema.PRIMARIA)),
             sg.Button('', key='-LIVRE_CANCELAR-', font=tema.texto(tema.TAMANHO_CORPO))],
        ], key=f'-TELA_{self.nome.upper()}-', visible=False,
            element_justification='center', expand_x=True)

    def preparar(self, alvo=None, limite_s=60.0, **contexto):
        self.alvo = (alvo or '')[:self.MAXIMO_DE_CARACTERES]
        self.limite_s = limite_s
        # Uma marca por caractere: True = já errou aqui. Não volta a False quando
        # o usuário corrige — é justamente o histórico de tropeços.
        self.tropecou_em = [False] * len(self.alvo)
        self.inicio = agora_ms()
        self.estourou = False

        janela = self.app.janela
        janela['-LIVRE_ROTULO-'].update(get_text('sentence_to_type_label', self.idioma))
        janela['-LIVRE_ENTRADA_ROTULO-'].update(get_text('your_input_label', self.idioma))
        janela['-LIVRE_ENVIAR-'].update(get_text('submit_button', self.idioma))
        janela['-LIVRE_CANCELAR-'].update(get_text('cancel_button', self.idioma))
        janela['-LIVRE_ENTRADA-'].update('')
        for i, elemento in enumerate(self.alvos):
            if i < len(self.alvo):
                elemento.update(self.alvo[i], text_color=tema.TEXTO_SECUNDARIO,
                                visible=True)
            else:
                elemento.update(' ', visible=False)
        janela['-LIVRE_ENTRADA-'].set_focus()

    def evento(self, nome, valores):
        if nome == '-LIVRE_CANCELAR-':
            return 'menu'
        if nome == '-LIVRE_ENVIAR-':
            return self._encerrar(valores.get('-LIVRE_ENTRADA-', ''))
        if nome == '-LIVRE_ENTRADA-':
            self._repintar(valores.get('-LIVRE_ENTRADA-', ''))
        return None

    def _repintar(self, digitado):
        """Repinta a frase inteira a cada tecla.

        Barato no tamanho de frase usado, e evita rastrear qual posição mudou —
        colar texto altera várias de uma vez.
        """
        for i, esperado in enumerate(self.alvo):
            if i < len(digitado):
                if digitado[i] != esperado:
                    self.tropecou_em[i] = True
                    self.alvos[i].update(text_color=tema.ERRO)
                else:
                    self.alvos[i].update(text_color=tema.SUCESSO)
            else:
                self.alvos[i].update(text_color=tema.TEXTO_SECUNDARIO)

    def tique(self, instante):
        decorrido = (instante - self.inicio) / 1000.0
        mostrado = min(decorrido, self.limite_s)
        self.app.janela['-LIVRE_TEMPO-'].update(
            f"{get_text('timer_label', self.idioma)} {mostrado:.1f}s / {self.limite_s:.1f}s")
        if decorrido >= self.limite_s and not self.estourou:
            self.estourou = True
            valores = self.app.janela.read(timeout=0)[1] or {}
            return self._encerrar(valores.get('-LIVRE_ENTRADA-', ''))
        return None

    def _encerrar(self, digitado):
        duracao = min((agora_ms() - self.inicio) / 1000.0, self.limite_s)
        self.app.resultado_livre = {
            'alvo': self.alvo, 'digitado': digitado, 'duracao_s': duracao,
            'tropecos': sum(self.tropecou_em), 'estourou': self.estourou,
        }
        return 'relatorio_livre'


class TelaRelatorioLivre(Tela):
    """O relatório do treino livre, com as duas medidas de erro.

    A classificação de desempenho segue a ordem herdada do programa original, e
    ela é deliberada: tempo estourado e precisão baixa vêm ANTES de qualquer
    elogio à velocidade, porque digitar rápido e errado não é progresso.
    """
    nome = 'relatorio_livre'
    PRECISAO_MINIMA = 85

    def coluna(self):
        def linha(chave, fonte=None):
            return [sg.Text('', key=chave, font=fonte or tema.texto(tema.TAMANHO_CORPO),
                            text_color=tema.TEXTO)]
        return sg.Column([
            [sg.Text('', key='-RL_TITULO-', font=tema.texto(tema.TAMANHO_TITULO, True),
                     text_color=tema.TEXTO)],
            linha('-RL_ALVO-', tema.mono(tema.TAMANHO_APOIO)),
            linha('-RL_DIGITADO-', tema.mono(tema.TAMANHO_APOIO)),
            [sg.HorizontalSeparator()],
            linha('-RL_ERROS-'), linha('-RL_TROPECOS-'), linha('-RL_PRECISAO-'),
            linha('-RL_TEMPO-'), linha('-RL_WPM-'),
            [sg.Text('', key='-RL_DESEMPENHO-',
                     font=tema.texto(tema.TAMANHO_SUBTITULO, True))],
            [sg.Button('', key='-RL_OUTRA-',
                       font=tema.texto(tema.TAMANHO_SUBTITULO, True),
                       button_color=(tema.SOBRE_PRIMARIA, tema.PRIMARIA)),
             sg.Button('', key='-RL_MENU-', font=tema.texto(tema.TAMANHO_CORPO))],
        ], key=f'-TELA_{self.nome.upper()}-', visible=False,
            element_justification='center', expand_x=True)

    def preparar(self, **contexto):
        import TouchTypingTrainer as app_mod
        dados = self.app.resultado_livre
        alvo, digitado = dados['alvo'], dados['digitado']
        duracao = dados['duracao_s']
        relatorio = app_mod.calculate_accuracy_report(alvo, digitado)
        t = lambda chave: get_text(chave, self.idioma)     # noqa: E731

        wpm = metricas.wpm(relatorio['typed_length'], duracao)
        wpm_liq = metricas.wpm_liquido(relatorio['typed_length'], duracao,
                                       relatorio['errors'])
        janela = self.app.janela
        janela['-RL_TITULO-'].update(t('report_title'))
        janela['-RL_ALVO-'].update(f"{t('report_target_sentence')} {alvo}")
        janela['-RL_DIGITADO-'].update(f"{t('report_your_sentence')} {digitado}")
        janela['-RL_ERROS-'].update(
            f"{t('report_errors')} {relatorio['errors']}",
            text_color=tema.ERRO if relatorio['errors'] else tema.SUCESSO)
        janela['-RL_TROPECOS-'].update(
            f"{t('report_total_mistakes_made')} {dados['tropecos']}",
            text_color=tema.ERRO if dados['tropecos'] else tema.SUCESSO)
        precisao = relatorio['accuracy']
        janela['-RL_PRECISAO-'].update(
            f"{t('report_accuracy')} {precisao}%",
            text_color=(tema.SUCESSO if precisao >= 95 else
                        tema.ATENCAO if precisao >= self.PRECISAO_MINIMA else tema.ERRO))
        janela['-RL_TEMPO-'].update(f"{t('report_time_taken')} {duracao:.2f}s")
        janela['-RL_WPM-'].update(f'WPM: {wpm:.1f} / {wpm_liq:.1f}')

        texto, cor = self._classificar(dados, relatorio, duracao, len(alvo))
        janela['-RL_DESEMPENHO-'].update(f"{t('report_performance_label')} {texto}",
                                         text_color=cor)
        janela['-RL_OUTRA-'].update(t('licao_proximo'))
        janela['-RL_MENU-'].update(t('licao_voltar'))

        # O arquivo vem da sessão, não do global do módulo: senão um teste (ou
        # uma segunda sessão) gravaria no histórico errado.
        app_mod.gravar_treino_livre(alvo, duracao, relatorio, dados['tropecos'],
                                    self.idioma, self.app.sessao.arquivo)

    def _classificar(self, dados, relatorio, duracao, comprimento):
        import TouchTypingTrainer as app_mod
        t = lambda chave: get_text(chave, self.idioma)     # noqa: E731
        if dados['estourou']:
            return t('perf_time_limit_exceeded'), tema.ERRO
        if relatorio['accuracy'] < self.PRECISAO_MINIMA:
            return t('perf_focus_accuracy'), tema.ATENCAO
        if duracao <= comprimento / app_mod.CPS_FAST:
            return t('perf_excellent_speed'), tema.SUCESSO
        if duracao <= comprimento / app_mod.CPS_FASTER:
            return t('perf_good_speed'), tema.SUCESSO
        return t('perf_learning_pace'), tema.TEXTO

    def evento(self, nome, valores):
        if nome == '-RL_MENU-':
            return 'menu'
        if nome == '-RL_OUTRA-':
            return 'livre_de_novo'
        return None
