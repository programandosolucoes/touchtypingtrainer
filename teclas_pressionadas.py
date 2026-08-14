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
