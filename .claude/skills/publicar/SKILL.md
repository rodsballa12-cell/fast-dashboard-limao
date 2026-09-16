---
name: publicar
description: Republica o painel no Artifact "Ritmo Fast · Escova Limão" com os dados atuais do repositório. Use depois de um refresh, depois que o Excel entrar, ou quando o Rodrigo pedir "atualiza o artefato" / "publica o painel". Sempre no mesmo endereço — nunca cria artefato novo.
---

# Publicar o painel · FAST Limão

## Cargo

Você leva o painel do repositório para o celular do Rodrigo. É a única ponte
entre o que o pipeline gerou e o que ele abre no bolso.

**O endereço é fixo e nunca muda:**

```
https://claude.ai/artifact/3hfZcJU65a4VfNy8VYjmWD
```

Publicar sem esse `url` **cria um artefato novo** — e aí existem dois painéis,
o Rodrigo abre o antigo pelo link que já tinha, e ninguém percebe por dias.

## Rotina

### Passo 1 — garantir que o dado é o de agora

```bash
git pull --rebase origin main
python3 scripts/auditoria_coerencia.py
```

Auditoria vermelha **não publica**. Painel bonito com número que não bate é
pior que painel velho: o velho pelo menos avisa a idade.

### Passo 2 — gerar o HTML

```bash
python3 scripts/build_artifact.py /tmp/painel.html
```

O script embute os quatro JSON que o `index.html` busca em runtime — a CSP do
Artifact bloqueia fetch externo, e sem embutir as abas Financeiro e Mídias
abrem **vazias, sem erro visível**, porque os loaders engolem a falha.

Confira na saída do script os dois `gerado_em` que ele imprime. Se algum for de
ontem, diga isso ao Rodrigo **antes** de publicar.

### Passo 3 — ler antes de publicar

```
Artifact action=read url=https://claude.ai/artifact/3hfZcJU65a4VfNy8VYjmWD
```

Obrigatório: publicar num artefato que a conversa não leu é recusado. Aproveite
para comparar o `gerado_em` que está no ar com o que você vai subir — se forem
iguais, não há o que publicar, e dizer isso é a resposta certa.

### Passo 4 — publicar no mesmo endereço

```
Artifact file_path=/tmp/painel.html
         url=https://claude.ai/artifact/3hfZcJU65a4VfNy8VYjmWD
         label="<de quando é o dado>"
```

**Não passe `favicon` nem `capabilities`** — republicação carrega os dois do
que já está lá. Passar `favicon` de novo troca o ícone que o Rodrigo reconhece.

### Passo 5 — dizer o que mudou, não que publicou

"Publicado" não é informação. O que vale é o que ele vai ver de diferente:
qual número se moveu, qual card novo apareceu, de quando é o dado agora.

## Alçada

**Decide sozinho:** se o dado está fresco o bastante para subir.

**Nunca:** publica com auditoria vermelha · cria artefato novo · troca o
favicon · publica dado de ontem sem avisar que é de ontem.

## Por que isto não roda sozinho no GitHub

O GitHub Actions **não consegue publicar no claude.ai** — a ferramenta de
Artifact só existe dentro de uma sessão do Claude. Por isso a publicação
depende de alguém rodar este cargo.

O encaixe natural é o **Conselho das 22h30**, que já roda diariamente na
máquina do Rodrigo: o dia fechou, o dado é o final, e o painel amanhece
atualizado. Publicar a cada refresh seria publicar sete vezes por dia para
mudar centavos.
