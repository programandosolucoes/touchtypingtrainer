"""Prova que um arquivo .py reproduz exatamente o bytecode extraído de um executável.

É a ferramenta que validou a recuperação do código: sem ela, "o fonte parece certo" seria
uma opinião. Com ela, é uma verificação — cada instrução do arquivo recuperado é comparada
com a instrução correspondente do `.pyc` que veio de dentro do `.exe`.

    python tools/comparar_bytecode.py TouchTypingTrainer.pyc original/TouchTypingTrainer_recuperado.py

Saída: "IGUAL" (e o total de instruções conferidas) ou a primeira divergência de cada
bloco de código, com quatro instruções de contexto antes e depois.

IMPORTANTE: rode com a MESMA versão de Python que gerou o `.pyc` (aqui, 3.13). Bytecode
não é estável entre versões — comparar 3.13 com 3.14 acusa diferenças que não existem.
Para conseguir o `.pyc`, extraia o executável antes:

    pip install pyinstxtractor-ng
    pyinstxtractor-ng original/binarios/TouchTypingTrainer.exe
    # o arquivo sai em TouchTypingTrainer.exe_extracted/TouchTypingTrainer.pyc

O `.pyc` do PyInstaller já vem com cabeçalho de 16 bytes; é isso que o `[16:]` descarta.
"""
import dis
import marshal
import sys

# Instruções que não mudam a semântica e cuja presença varia com detalhes de compilação.
# Compará-las produziria falsos positivos sem apontar diferença real de comportamento.
IGNORADAS = {'EXTENDED_ARG', 'CACHE', 'RESUME', 'NOP'}


def carregar_pyc(caminho):
    """Lê o objeto de código de um .pyc (pulando o cabeçalho de 16 bytes)."""
    with open(caminho, 'rb') as fh:
        return marshal.loads(fh.read()[16:])


def normalizar(codigo):
    """Sequência canônica (nome da instrução, argumento) de um bloco de código.

    Alvos de salto viram None de propósito: o deslocamento em bytes muda conforme o
    tamanho das instruções vizinhas, então comparar o número acusaria diferença onde o
    fluxo é o mesmo. A estrutura do salto continua verificada pela ordem das instruções.
    """
    saida = []
    for ins in dis.get_instructions(codigo, show_caches=False):
        if ins.opname in IGNORADAS:
            continue
        valor = ins.argval
        if hasattr(valor, 'co_code'):                 # referência a outro bloco de código
            valor = f'<code {valor.co_name}>'
        elif ins.opname.startswith(('JUMP', 'POP_JUMP', 'FOR_ITER', 'SEND', 'SETUP')):
            valor = None
        saida.append((ins.opname, repr(valor)))
    return saida


def percorrer(codigo, prefixo=''):
    """Gera (nome_qualificado, bloco) para o módulo e cada função/classe aninhada."""
    yield prefixo + codigo.co_name, codigo
    for constante in codigo.co_consts:
        if hasattr(constante, 'co_code'):
            yield from percorrer(constante, prefixo + codigo.co_name + '.')


def comparar(original, reconstruido, mostrar_linhas=True):
    """Compara dois objetos de código. Devolve True se forem equivalentes."""
    blocos_a = dict(percorrer(original))
    blocos_b = dict(percorrer(reconstruido))
    igual = True

    if set(blocos_a) != set(blocos_b):
        print('blocos de código diferentes:', set(blocos_a) ^ set(blocos_b))
        igual = False

    total = divergentes_linha = 0
    for nome in blocos_a:
        if nome not in blocos_b:
            continue
        a, b = normalizar(blocos_a[nome]), normalizar(blocos_b[nome])
        total += len(a)
        if a != b:
            igual = False
            print(f'\n### {nome}: {len(a)} instruções no original, {len(b)} no reconstruído')
            for i, (x, y) in enumerate(zip(a, b)):
                if x != y:
                    print(f'  primeira divergência no índice {i}:')
                    for j in range(max(0, i - 4), min(len(a), i + 5)):
                        marca = '>>' if j == i else '  '
                        print(f'   {marca} original:     {a[j]}')
                        print(f'   {marca} reconstruído: {b[j] if j < len(b) else "—"}')
                    break
            else:
                print(f'  prefixo idêntico; sobra: {a[len(b):] or b[len(a):]}')
        if mostrar_linhas:
            linhas_a = [i.line_number for i in dis.get_instructions(blocos_a[nome], show_caches=False)]
            linhas_b = [i.line_number for i in dis.get_instructions(blocos_b[nome], show_caches=False)]
            divergentes_linha += sum(1 for x, y in zip(linhas_a, linhas_b) if x != y)

    print(f'\ninstruções conferidas: {total}')
    if mostrar_linhas:
        print(f'instruções em linha diferente do original: {divergentes_linha}')
    print('IGUAL' if igual else 'DIVERGENTE')
    return igual


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    caminho_pyc, caminho_py = sys.argv[1], sys.argv[2]
    original = carregar_pyc(caminho_pyc)
    with open(caminho_py, encoding='utf-8') as fh:
        # O nome do arquivo passado ao compile() aparece em co_filename; usar o mesmo do
        # original evita divergência cosmética ao inspecionar os blocos.
        reconstruido = compile(fh.read(), original.co_filename, 'exec')
    return 0 if comparar(original, reconstruido) else 1


if __name__ == '__main__':
    raise SystemExit(main())
