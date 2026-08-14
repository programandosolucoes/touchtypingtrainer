"""Empacota as duas edições do TouchTypingTrainer com PyInstaller.

    python build.py            # as duas edições, para o sistema atual
    python build.py free       # só a edição livre (FreeSimpleGUI)
    python build.py trial      # só a edição de demonstração (PySimpleGUI)

A única diferença entre as edições é qual biblioteca de GUI entra no pacote — o código
do aplicativo é idêntico. O script reescreve a constante `EDICAO` em `gui_backend.py`
antes de chamar o PyInstaller e devolve o arquivo ao estado original no fim, mesmo se
o empacotamento falhar.

Para gerar o .exe do Windows a partir do Linux, rode este mesmo script sob Wine, com um
Python de Windows instalado no prefixo (ver LEIA-ME.md): PyInstaller não faz compilação
cruzada — ele empacota para o sistema em que está rodando.
"""
import glob
import os
import re
import shutil
import subprocess
import sys

RAIZ = os.path.dirname(os.path.abspath(__file__))
GUI_BACKEND = os.path.join(RAIZ, 'gui_backend.py')

EDICOES = {
    'free': {'nome': 'TouchTypingTrainer', 'lib': 'FreeSimpleGUI'},
    'trial': {'nome': 'TouchTypingTrainer-trial', 'lib': 'PySimpleGUI'},
}


def definir_edicao(edicao):
    """Reescreve a constante EDICAO em gui_backend.py e devolve o conteúdo anterior."""
    with open(GUI_BACKEND, encoding='utf-8') as fh:
        original = fh.read()
    novo = re.sub(r"^EDICAO = '\w+'", f"EDICAO = '{edicao}'", original, count=1, flags=re.M)
    with open(GUI_BACKEND, 'w', encoding='utf-8') as fh:
        fh.write(novo)
    return original


def libs_tcl_tk():
    """Bibliotecas Tcl/Tk que o PyInstaller não acha sozinho, no Linux.

    Distribuições "standalone" do Python (as do `uv`, por exemplo) guardam
    `libtcl9.0.so` e `libtcl9tk9.0.so` em `<prefixo>/lib`, fora dos caminhos que o
    PyInstaller inspeciona. Sem elas o binário até é gerado, mas quebra na primeira
    execução com "libtcl9.0.so: cannot open shared object file".
    """
    if os.name != 'posix':
        return []
    achadas = []
    for padrao in ('libtcl*.so*', 'libtk*.so*'):
        achadas += glob.glob(os.path.join(sys.base_prefix, 'lib', padrao))
    argumentos = []
    for lib in achadas:
        argumentos += ['--add-binary', f'{lib}:.']
    return argumentos


def empacotar(edicao):
    cfg = EDICOES[edicao]
    original = definir_edicao(edicao)
    try:
        # O PyInstaller joga tudo em dist/ por padrão, mas o projeto guarda os
        # binários separados por plataforma — e ele não faz compilação cruzada,
        # então a plataforma de destino é sempre a que está rodando o build.
        destino = os.path.join(RAIZ, 'dist', 'windows' if os.name == 'nt' else 'linux')
        comando = [
            sys.executable, '-m', 'PyInstaller', '--noconfirm', '--onefile',
            '--name', cfg['nome'], '--distpath', destino,
            *libs_tcl_tk(),
            # As libs de GUI são importadas dinamicamente via gui_backend; sem o
            # hidden-import o PyInstaller não enxerga a dependência da edição.
            '--hidden-import', cfg['lib'],
            # A outra biblioteca de GUI não deve entrar no pacote da edição errada.
            '--exclude-module', EDICOES['trial' if edicao == 'free' else 'free']['lib'],
            'TouchTypingTrainer.py',
        ]
        print('>>', ' '.join(comando), flush=True)
        subprocess.run(comando, cwd=RAIZ, check=True)
    finally:
        with open(GUI_BACKEND, 'w', encoding='utf-8') as fh:
            fh.write(original)


def main():
    alvos = sys.argv[1:] or list(EDICOES)
    for edicao in alvos:
        if edicao not in EDICOES:
            print(f'edição desconhecida: {edicao} (use free ou trial)')
            return 1
    if not shutil.which('pyinstaller') and not os.environ.get('SKIP_CHECK'):
        print('aviso: pyinstaller não está no PATH; usando "python -m PyInstaller"')
    for edicao in alvos:
        empacotar(edicao)
    print('\nbinários em', os.path.join(RAIZ, 'dist',
                                        'windows' if os.name == 'nt' else 'linux'))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
