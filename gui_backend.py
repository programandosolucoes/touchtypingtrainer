"""Escolhe qual biblioteca de interface o aplicativo vai usar.

Existem duas edições do TouchTypingTrainer, com o MESMO código, mudando só a GUI:

- **free**  → FreeSimpleGUI, o fork livre (LGPL) do PySimpleGUI. É a edição completa,
  roda sem cadastro e é a que fica com o usuário final.
- **trial** → PySimpleGUI 5, que exige registro/chave de licença na primeira execução.
  É a edição de demonstração enviada a clientes: a limitação de uso vem da própria
  biblioteca, o código não é capado em nada.

O `build.py` reescreve a constante `EDICAO` abaixo antes de empacotar cada edição,
por isso ela é uma string literal simples e não algo calculado — o PyInstaller
precisa enxergar o import de forma estática para incluir a biblioteca certa.
"""

EDICAO = 'free'  # 'free' (FreeSimpleGUI) ou 'trial' (PySimpleGUI) — trocado pelo build.py

if EDICAO == 'trial':
    import PySimpleGUI as sg
else:
    import FreeSimpleGUI as sg

__all__ = ['sg', 'EDICAO']
