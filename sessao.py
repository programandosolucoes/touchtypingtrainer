"""O estado de uma série de exercícios do Modo Lição.

Existe para tirar do laço de eventos as três perguntas que ele fazia mal:
qual nível está sendo treinado, quantos exercícios ainda faltam na série, e o
que gravar quando um termina. Nada aqui abre janela — o que permite testar a
progressão inteira sem tocar na interface.

## Sobre escolher o nível

O aluno pode **revisitar qualquer nível já liberado**, mas não pular adiante.
Deixar escolher livremente destruiria o portão de progressão, que é o ponto do
produto; travar em apenas um nível impediria treinar o ponto fraco, que é o
motivo real de alguém querer escolher. `niveis_disponiveis` resolve os dois.
"""
import time

import historico
import layouts
import licoes
import modo_licao
from i18n import get_text

EXERCICIOS_POR_SERIE = (1, 3, 5, 10)
PADRAO_DE_SERIE = 3


class Sessao:
    """Uma série de exercícios num nível, do começo ao fim."""

    def __init__(self, idioma, arquivo_do_historico):
        self.idioma = idioma
        self.arquivo = arquivo_do_historico
        self.tamanho_da_serie = PADRAO_DE_SERIE
        self.indice_na_serie = 0
        self.nivel = None
        self.semente = None
        self.ultimo_resultado = None      # (registro, avaliacao)
        self._texto = None
        # True quando o aluno pediu explicitamente um nível de revisão; enquanto
        # for False, a sessão acompanha o nível que o currículo liberou.
        self._escolha_manual = False
        self.recarregar()

    # --- estado vindo do histórico -------------------------------------------

    @property
    def nome_layout(self):
        return layouts.LAYOUT_POR_IDIOMA[self.idioma]

    def recarregar(self):
        """Relê o histórico e recoloca a sessão no nível corrente.

        `nivel_maximo` é o mais alto que o currículo já liberou; `nivel` é o que
        está sendo treinado agora. Os dois são quase sempre o mesmo — separá-los
        é o que permite revisar um nível antigo sem perder o progresso, e foi
        confundi-los que fazia o aluno ser jogado de volta ao nível 1 justamente
        no exercício que liberava o 2.
        """
        self.registros = historico.ler(self.arquivo)
        self.nivel_maximo = licoes.nivel_atual(self.registros, self.nome_layout)
        if not getattr(self, '_escolha_manual', False):
            self.nivel = self.nivel_maximo
        self.aprovacoes = licoes.aprovacoes_seguidas(self.registros, self.nivel)
        self.preferencias = historico.ler_preferencias(self.arquivo)

    @property
    def teclado_sem_rollover(self):
        return bool(self.preferencias.get('teclado_sem_rollover'))

    def registrar_sem_rollover(self):
        """Guarda que este teclado não reporta quatro teclas ao mesmo tempo."""
        if self.teclado_sem_rollover:
            return
        historico.gravar_preferencia(self.arquivo, 'teclado_sem_rollover', True)
        self.preferencias['teclado_sem_rollover'] = True

    def niveis_disponiveis(self):
        """Os níveis que o aluno pode treinar: do 1 até o mais alto liberado."""
        return [n for n in licoes.curriculo(self.nome_layout)
                if n.numero <= self.nivel_maximo.numero]

    def escolher_nivel(self, numero):
        """Troca o nível em treino. Ignora pedido acima do liberado."""
        for nivel in self.niveis_disponiveis():
            if nivel.numero == numero:
                self.nivel = nivel
                # Só é "escolha manual" quando difere do corrente: assim o aluno
                # que escolhe o próprio nível atual volta a acompanhar a
                # progressão automaticamente quando ela avançar.
                self._escolha_manual = numero != self.nivel_maximo.numero
                self.aprovacoes = licoes.aprovacoes_seguidas(self.registros, nivel)
                return True
        return False

    # --- a série -------------------------------------------------------------

    def iniciar_serie(self, tamanho=None):
        if tamanho:
            self.tamanho_da_serie = tamanho
        self.indice_na_serie = 0
        self.semente = None

    def tem_proximo(self):
        return self.indice_na_serie + 1 < self.tamanho_da_serie

    def avancar(self):
        """Passa ao próximo exercício da série, com texto novo."""
        self.indice_na_serie += 1
        self.semente = None

    def repetir_exercicio(self):
        """Refaz o MESMO exercício: mesma semente, mesmo texto, mesma posição na série.

        Deliberadamente não mexe em nada. Repetir com texto novo mediria outra
        coisa — quem errou uma sequência específica precisa daquela sequência de
        novo para consertar o caminho do dedo.
        """
        return self._texto

    def rotulo_da_serie(self, idioma):
        return get_text('licao_serie_de', idioma).format(
            self.indice_na_serie + 1, self.tamanho_da_serie)

    # --- o exercício ---------------------------------------------------------

    def texto_do_exercicio(self):
        """O texto a digitar. Estável enquanto a semente não mudar."""
        if self.semente is None:
            self.semente = int(time.time() * 1000) % 1_000_000
            self._texto = None
        if self._texto is None:
            self._texto = self._gerar_texto()
        return self._texto

    def _gerar_texto(self):
        if self.nivel.numero >= 12:
            import random
            frases = (get_text('short_sentences', self.idioma)
                      + get_text('long_sentences', self.idioma))
            permitidas = licoes.teclas_liberadas(self.nome_layout, self.nivel.numero)
            candidatas = licoes.filtrar_frases(frases, permitidas) or frases
            return random.Random(self.semente).choice(candidatas)
        return licoes.gerar_exercicio(self.nome_layout, self.nivel.numero, self.semente)

    def concluir_exercicio(self, texto, resultado):
        """Monta o registro, avalia, grava e devolve (registro, avaliacao)."""
        registro = modo_licao.montar_registro(
            self.nivel, self.nome_layout, self.idioma, texto, self.semente, resultado)
        avaliacao = licoes.avaliar(registro, self.nivel)
        registro['aprovado'] = avaliacao.aprovado
        registro['serie'] = [self.indice_na_serie + 1, self.tamanho_da_serie]
        historico.gravar(registro, self.arquivo)
        self.ultimo_resultado = (registro, avaliacao)
        # Relê para que o nível e a contagem reflitam o que acabou de ser
        # gravado — sem isto a tela prévia mostraria número velho. Quem escolheu
        # um nível de revisão continua nele; quem está na progressão acompanha.
        self.recarregar()
        return registro, avaliacao
