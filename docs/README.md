# Documentação do TouchTypingTrainer

Todo o conhecimento do projeto está aqui — do método que recuperou o código-fonte perdido
até as armadilhas da API de IA e do empacotamento. Comece pelo documento que responde à
sua pergunta:

| documento | responde |
|---|---|
| [ARQUITETURA.md](ARQUITETURA.md) | como o programa é organizado e **por que** cada decisão estranha existe |
| [API_IA.md](API_IA.md) | como funciona a geração de exercícios, qual serviço, e o que fazer se ele cair |
| [BUILD.md](BUILD.md) | como gerar os binários, inclusive `.exe` a partir do Linux |
| [RECUPERACAO.md](RECUPERACAO.md) | como o fonte foi recuperado do `.exe` e como refazer a verificação |
| [LICOES_APRENDIDAS.md](LICOES_APRENDIDAS.md) | índice das armadilhas que custaram tempo |
| [REGISTRO_SSH.md](REGISTRO_SSH.md) | comandos executados no servidor do painel git |
| [../LEIA-ME.md](../LEIA-ME.md) | o que o programa faz e como rodar |
| [../original/LEIA-ME.md](../original/LEIA-ME.md) | os binários e o fonte originais preservados |

## Linha do tempo do projeto

**Antes** — o programa existia só como dois `.exe` em `~/Downloads`; o fonte tinha sido
perdido. As duas versões eram o mesmo código, mudando só a biblioteca de interface
(PySimpleGUI passou a exigir registro, daí a migração para o fork livre FreeSimpleGUI).

**02/08/2026** — o fonte foi recuperado do bytecode e verificado instrução a instrução;
depois foi comentado, dividido em módulos e ganhou a geração de exercícios por IA. As duas
edições passaram a sair de um único código, e os quatro binários foram gerados e testados.

## Onde este repositório vive

Repositório `touchtypingtrainer.git` no painel git próprio
(`git.programandosolucoes.com.br`), branch `main`. O remoto usa SSH na porta 65002:

```bash
git remote add origin "ssh://u560021660@git.programandosolucoes.com.br:65002\
/home/u560021660/domains/git.programandosolucoes.com.br/public_html/git/repos/touchtypingtrainer.git"
git push -u origin main
```

Os binários são versionados de propósito (`dist/` e `original/binarios/`), o que faz o
repositório passar de 80 MB. Foi uma escolha: o valor de ter o executável exato que foi
entregue a um cliente, junto com o código que o gerou, supera o custo de espaço.

## O que ainda não foi verificado

Honestidade sobre os limites do que foi testado:

- os `.exe` rodaram **sob Wine**, não em um Windows real;
- o botão "Gerar Exercícios (IA)" foi validado nas partes (API, parser, threading,
  construção da janela), mas não clicado numa sessão interativa;
- a tela de registro do PySimpleGUI na edição trial não foi vista em execução.
