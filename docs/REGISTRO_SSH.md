# Registro de comandos executados no servidor remoto

Servidor: `git.programandosolucoes.com.br` (Hostinger), acesso
`ssh -p 65002 u560021660@git.programandosolucoes.com.br`.
Base do painel: `~/domains/git.programandosolucoes.com.br/public_html/git`.

## 2026-08-02 — criação do repositório do projeto

**Leitura (inspeção antes de mexer):**

```bash
cd ~/domains/.../git && ls repos/ | head -20 && ls repos/ | wc -l     # 38 repositórios
ls repos/curriculo.git/                                                # estrutura de um repo
cat repos/curriculo.git/gitpanel-policy                                # política aplicada
cat repos/curriculo.git/description; cat repos/curriculo.git/HEAD      # HEAD aponta para main
ls repos/curriculo.git/hooks/ | grep -v sample                         # hooks: update, post-receive
php -r '...' _private/config.json                                      # só as CHAVES do config
```

**Escrita (criação do repositório):**

```bash
cd ~/domains/.../git/repos
test -e touchtypingtrainer.git && echo 'JA EXISTE - abortando' || {
  git init --bare -q touchtypingtrainer.git
  cp curriculo.git/gitpanel-policy touchtypingtrainer.git/
  cp curriculo.git/hooks/update curriculo.git/hooks/post-receive touchtypingtrainer.git/hooks/
  echo 'ref: refs/heads/main' > touchtypingtrainer.git/HEAD
  echo 'TouchTypingTrainer - ...' > touchtypingtrainer.git/description
}
```

O `test -e` antes do `git init` é proposital: se o repositório já existisse, o script
abortaria em vez de reinicializar por cima.

Nenhum arquivo de outro repositório foi alterado; a política e os hooks foram **copiados**
de `curriculo.git`, que é o padrão dos demais repositórios do painel.
