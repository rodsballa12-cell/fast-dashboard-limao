# Prompt para a sessão do PC · migrar o Obsidian para o repositório

Abra o Claude Code em `C:\Users\rods_\dev\fast-dashboard-limao` e cole isto:

---

Faça `git pull` e leia o `CLAUDE.md` antes de começar.

Preciso migrar o que vale do meu Obsidian para o repositório. A pasta é:

`C:\Users\rods_\OneDrive\Documentos\Obsidian Vault\Cerebro_Claude\02-PROJETOS\Franquia_FAST_Limao`

**Não copie a pasta para o repositório.** A maior parte dela é histórico de
conversa e é minha, não da empresa.

## O teste, aplicado nota por nota

Para cada arquivo, uma pergunta só:

> **Isso muda uma decisão futura, ou só conta o que já aconteceu?**

- **Muda uma decisão** → migra. Contrato, regra combinada, número que alguém
  definiu, prazo assumido, o que a franqueadora prometeu, acordo de rateio,
  tabela de preço, escala combinada.
- **Só conta** → fica no Obsidian. Resumo de reunião, histórico de conversa,
  rascunho, nota de leitura.

Na dúvida, não migre. Me pergunte.

## Onde cada coisa vai

| o que é | onde vai |
|---|---|
| Número que o sistema precisa ler (meta, percentual, prazo, ID) | `data/config.json`, num bloco novo com `_desc` e `_fonte` |
| Decisão tomada, com data de revisão | `docs/decisoes/AAAA-MM-DD-assunto.md` |
| Coisa que custou caro descobrir | `docs/aprendizados/assunto.md` |
| Regra de como um cargo deve trabalhar | a ficha dele em `.claude/skills/` |

Siga o formato dos arquivos que já existem nessas pastas.

## Como quero que você trabalhe

1. **Primeiro, só o inventário.** Liste os arquivos da pasta com uma linha
   dizendo o que cada um é e o seu veredito (migra / fica / dúvida). **Pare aí
   e me mostre.** Não escreva nada no repositório ainda.
2. Depois que eu aprovar, migre **em lotes de no máximo cinco**, e me mostre o
   que escreveu a cada lote.
3. Nada de `git push` sem eu ver.

Se dois arquivos disserem coisas diferentes sobre o mesmo assunto, **não escolha
o mais recente** — me mostre os dois. Já aconteceu de duas sessões escreverem a
mesma nota em paralelo e gerarem memória duplicada.

---

## Por que em duas etapas

Migração é o momento em que lixo entra e vira verdade permanente. O inventário
antes da escrita custa uma mensagem e evita um repositório cheio de nota que
ninguém vai ler — que é pior que não ter nota nenhuma, porque parece completo.
