"""A janela única do Modo Lição e o laço de eventos que troca de tela.

Uma janela, tamanho fixo, e as telas empilhadas como `sg.Column` — trocar de
tela é mudar visibilidade, nunca abrir janela nova. Ver o cabeçalho de
`telas.py` para o porquê disso importar num treinador de digitação.

Quem tem laço de eventos é esta classe; as telas só respondem. Isso concentra
num lugar só as três coisas que precisam existir uma vez por janela: o `bind`
das teclas, o cronômetro do laço e o roteamento.
"""
import layouts
import sessao as mod_sessao
import telas as mod_telas
import tema
from gui_backend import sg
from i18n import get_text

# Tamanho fixo. Nada salta nem se redimensiona ao trocar de tela: o teclado
# desenhado fica sempre no mesmo lugar, que é o ponto de treinar sem olhar.
LARGURA = 1120
ALTURA = 880

# 50 ms mantém o cronômetro suave e o teste de mãos responsivo sem torrar CPU.
INTERVALO_DO_LACO = 50


class Aplicativo:
    """Hospeda as telas do Modo Lição numa janela só."""

    def __init__(self, idioma, arquivo_do_historico):
        self.idioma = idioma
        self.sessao = mod_sessao.Sessao(idioma, arquivo_do_historico)
        self.janela = None
        self.tela_atual = None
        self.telas = {}
        # O que o treino livre acabou de produzir, lido pelo relatório dele.
        self.resultado_livre = None
        # Como sortear o próximo exercício livre. Quem abre o treino define.
        self.sortear_livre = None

    # --- construção -----------------------------------------------------------

    def _montar(self):
        tema.aplicar(sg)   # antes de criar qualquer elemento
        for classe in (mod_telas.TelaGuia, mod_telas.TelaPrevia,
                       mod_telas.TelaExercicio, mod_telas.TelaRelatorio,
                       mod_telas.TelaProgresso, mod_telas.TelaLivre,
                       mod_telas.TelaRelatorioLivre):
            tela = classe(self)
            self.telas[tela.nome] = tela
        colunas = [[tela.coluna()] for tela in self.telas.values()]
        layout = [[sg.Column(colunas, expand_x=True, expand_y=True,
                             element_justification='center',
                             background_color=tema.SUPERFICIE)]]
        self.janela = sg.Window(
            get_text('menu_modo_licao', self.idioma), layout, finalize=True,
            size=(LARGURA, ALTURA), resizable=False, return_keyboard_events=True,
            element_justification='center', background_color=tema.SUPERFICIE,
            modal=True, keep_on_top=False)
        # Um bind só, na janela: as telas recebem o evento já roteado.
        self.janela.bind('<KeyPress>', '-DOWN-')
        self.janela.bind('<KeyRelease>', '-UP-')
        for tela in self.telas.values():
            if hasattr(tela, 'desenhar_inicial'):
                tela.desenhar_inicial()

    def caractere_do_evento(self):
        """O caractere da tecla que gerou o evento corrente, ou None."""
        import modo_licao
        return modo_licao.keysym_para_caractere(
            getattr(self.janela.user_bind_event, 'keysym', ''))

    # --- troca de tela --------------------------------------------------------

    def ir_para(self, nome, **contexto):
        """Mostra uma tela e esconde a anterior. `menu` encerra a janela."""
        if nome == 'livre_de_novo':
            # Pseudo-tela: sorteia outro exercício e volta ao treino livre, sem
            # o usuário passar pelo menu.
            sorteado = self.sortear_livre() if self.sortear_livre else None
            if not sorteado:
                return False
            frase, limite = sorteado
            return self.ir_para('livre', alvo=frase, limite_s=limite)
        if nome == 'menu':
            self.tela_atual = None
            return False
        for chave, tela in self.telas.items():
            self.janela[f'-TELA_{chave.upper()}-'].update(visible=(chave == nome))
        self.tela_atual = self.telas[nome]
        self.tela_atual.preparar(**contexto)
        self._atualizar_desenhos()
        return True

    def _atualizar_desenhos(self):
        """Rasteriza o que mudou. Só a tela visível tem desenho para atualizar."""
        tela = self.tela_atual
        for atributo in ('teclado', 'maos'):
            widget = getattr(tela, atributo, None)
            if widget is not None:
                widget.atualizar()

    # --- laço -----------------------------------------------------------------

    def rodar(self, tela_inicial, **contexto):
        """Abre a janela na tela pedida e roda até voltar ao menu."""
        self._montar()
        if not self.ir_para(tela_inicial, **contexto):
            self.janela.close()
            return
        while True:
            evento, valores = self.janela.read(timeout=INTERVALO_DO_LACO)
            if evento == sg.WIN_CLOSED:
                break
            proxima = None
            if evento != sg.TIMEOUT_KEY:
                proxima = self.tela_atual.evento(evento, valores)
            if proxima is None:
                proxima = self.tela_atual.tique(mod_telas.agora_ms())
            if proxima is not None:
                if not self.ir_para(proxima):
                    break
            else:
                self._atualizar_desenhos()
        self.janela.close()
        self.janela = None


def abrir_guia(idioma, arquivo_do_historico):
    """Guia de mãos: teclado colorido por dedo, na mesma janela do resto."""
    Aplicativo(idioma, arquivo_do_historico).rodar('guia')


def abrir_progresso(idioma, arquivo_do_historico):
    """Evolução e diagnóstico, na mesma janela do resto."""
    Aplicativo(idioma, arquivo_do_historico).rodar('progresso')


def abrir_treino_livre(idioma, arquivo_do_historico, sortear):
    """Treino livre e seu relatório, na mesma janela do resto.

    `sortear` é a função que devolve (frase, limite_em_segundos) — quem sabe as
    preferências é o menu, não este módulo.
    """
    sorteado = sortear()
    if not sorteado:
        return
    app = Aplicativo(idioma, arquivo_do_historico)
    app.sortear_livre = sortear
    frase, limite = sorteado
    app.rodar('livre', alvo=frase, limite_s=limite)


def abrir_licao(idioma, arquivo_do_historico, tamanho_da_serie=None, nivel=None):
    """Uma série de exercícios, da tela prévia ao relatório, sem trocar de janela."""
    app = Aplicativo(idioma, arquivo_do_historico)
    if nivel:
        app.sessao.escolher_nivel(nivel)
    app.sessao.iniciar_serie(tamanho_da_serie)
    app.rodar('previa')


def rotulo_do_nivel(nivel, sessao, idioma):
    """Como o nível aparece no seletor do menu."""
    chave = ('menu_nivel_atual' if nivel.numero == sessao.nivel_maximo.numero
             else 'menu_nivel_revisao')
    return get_text(chave, idioma).format(nivel.numero, nivel.id)


def layout_por_idioma(idioma):
    return layouts.LAYOUT_POR_IDIOMA[idioma]
