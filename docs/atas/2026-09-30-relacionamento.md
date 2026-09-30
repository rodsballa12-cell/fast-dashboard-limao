---
agente: relacionamento
data: 2026-09-30
hora: 09:00
gerado_por: tarefa agendada
---

# relacionamento · 2026-09-30 às 09:00

> [!warning] Nao consegui atualizar o repositorio. Os numeros podem estar atrasados.
Nenhum aprendizado prévio específico sobre WhatsApp/relacionamento — sigo com o que apurei na base.

---

**SITUAÇÃO** — 🟡

Carteira saudável, canal automatizado mudo há 16 dias, e a fila de aniversariantes parou de ser montada há 21 dias — sem relação com o bloqueio do WhatsApp.

**FATOS**

- **75 clientes em alerta de churn early** (vieram 3+ vezes, sumiram há 14+ dias) — **LTV em risco R$ 18.270,00**. Em 20/09 o Conselho tinha aprovado ligar a fila para 69 desses clientes (R$ 16.862,00); 10 dias depois são 6 a mais e +R$ 1.408 — decisão aprovada, nunca executada, porque o canal segue mudo. *(Fonte: `data/dashboard_data.json`, gerado 28/09 16:36 — é o dado mais recente disponível, ver RISCO.)*
- **WhatsApp Cloud API: `conectado: false`.** Não é pendência nova — o Conselho de 14/09 já decidiu **não** perseguir isso no curto prazo: Rodrigo não tem acesso admin ao portfolio Meta para recriar o App apagado, e buscar essa promoção não está no radar dele. Recriar o App não é uma recomendação disponível até isso mudar.
- **`disparo_wa.ativo: false`** no `config.json` — o kill switch geral, independente do conector. Fila de 27/09 mostra **21 clientes prontos e recusados** só por causa do interruptor (`"kill switch desligado": 21`), 0 enviados.
- **HubSpot: 0 contatos**, mensagem "aguardando import da base" — igual à última leitura, sem mudança. Segue pendência conhecida, não escalo.
- **`aniversarios_fila.json` não atualiza desde 09/09** (21 dias) — enquanto isso, pelo menos 3 aniversariantes já passaram sem entrar em fila nenhuma (Gabriella 28/09, Renata e Claudete 29/09), e o painel de 28/09 apontava mais 10 nos 7 dias seguintes, LTV combinado R$ 1.311. Isso é diferente do bloqueio de envio: a fila nem está sendo *montada*.

**RISCO**

- **R$ 18.270 de LTV represado, crescendo ~R$ 140/dia** no ritmo dos últimos 10 dias, sem nenhum canal automatizado tocando esses clientes. O próprio painel estima resgate de 30-40% via WhatsApp pessoal (~R$ 6.394,50) — hoje isso depende de alguém ligar um a um.
- **O dado mais recente que tenho é de 28/09 16:36**, dois dias atrasado: o repositório está no meio de um `git rebase` travado por conflito em `data/clientes_detalhes.json`, `dashboard_data.json` e outros arquivos de dado (commit "refresh 26/09"). Nenhum refresh novo entra enquanto isso não for resolvido — não é algo que eu, Relacionamento, deva mexer, mas até resolver, meus números de churn e aniversariantes ficam presos em 28/09.

**NÃO VEJO**

- Por que `aniversarios_fila.json` parou de atualizar em 09/09 enquanto `wa_fila.json` seguiu rodando até 27/09 — são rotinas diferentes e uma delas emperrou; não tenho o log da tarefa agendada pra saber a causa.
- Os números de churn/aniversariantes de hoje (30/09) — presos no 28/09 pelo rebase travado.

**DECISÃO**

Nada a decidir sobre o WhatsApp — já foi decidido em 14/09 não perseguir. O que está em aberto:

1. **A fila de aniversariantes está parada e isso é consertável sem depender de admin Meta** — vale um item técnico pra alguém olhar por que o job de 09/09 não rodou de novo (isso é chamado técnico, não meu).
2. **O `git rebase` travado é do repositório, não da minha alçada** — mas até resolver, todo parecer meu (e dos outros cargos) está lendo dado de 28/09.
