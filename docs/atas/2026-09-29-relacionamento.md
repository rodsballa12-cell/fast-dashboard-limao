---
agente: relacionamento
data: 2026-09-29
hora: 09:00
gerado_por: tarefa agendada
---

# relacionamento · 2026-09-29 às 09:00

> [!warning] Nao consegui atualizar o repositorio. Os numeros podem estar atrasados.
PARECER · Relacionamento · 29/09/2026 · dado de 28/09 16:36 (Escova)

**Aviso de acesso, antes do resto:** o repositório está com um rebase do Git parado no meio (`data/clientes_detalhes.json`, `data/dashboard_data.json` e as 3 versões do painel estão com conflito não resolvido). Não dá pra ler o dado de hoje com segurança — usei o último commit limpo, de ontem à tarde (28/09 16:36). Isso não é coisa minha pra mexer; sinalizo abaixo pra você decidir.

SITUAÇÃO 🟡 atenção

FATOS
1. **75 clientes em alerta de sumiço**, R$ 18.270 em histórico de gasto (LTV) parado — o caso mais antigo é Juliana Cavalieri, 30 dias sem vir, 6 visitas, R$ 760 de histórico. Isso subiu de 58 clientes em 14/09 pra 75 agora.
2. **Hoje (29/09) tem 2 aniversariantes** — Renata Vaillati (4 visitas, R$ 198 de histórico) e Claudete Souza Pena (1 visita, R$ 79) — e mais 13 nos próximos 14 dias. Nenhuma recebe mensagem: o robô tentou mandar 21 mensagens em 27/09 e recusou todas ("kill switch desligado").
3. A carteira cresceu: 506 clientes cadastrados hoje contra 411 na última contagem registrada, 214 novos só nos últimos 30 dias, 60% já são clientes recorrentes. A base está saudável — o problema é só o canal mudo.

RISCO
O silêncio não é novo, mas está aumentando: 17 clientes a mais em risco de sumiço em 15 dias, sem ninguém ser chamado de volta. Enquanto o WhatsApp seguir apagado, esse número só cresce — e cada dia que passa empurra mais gente pra fora da janela de reativação (o robô só tenta reativar quem está entre 14 e 120 dias sem vir; depois de 120 ele nem tenta mais).

NÃO VEJO
- O dado de **hoje** em clientes e painel — travado pelo rebase parado. → quem mexeu no repositório por último.
- HubSpot: continua em "0 contatos, aguardando import da base" — mesma pendência já conhecida, sem mudança pra reportar.

DECISÃO
- Recriar o WhatsApp Cloud já foi decidido em 14/09 como "não fazer agora" — falta acesso admin seu no portfolio da Meta, não é coisa de código. Não estou reabrindo essa discussão, só atualizando o preço: são R$ 18.270 em clientes represados, subindo.
- O rebase parado no Git merece sua atenção antes de qualquer outro cargo ler o painel de novo — hoje todo mundo estaria lendo dado de ontem sem saber, se eu não tivesse checado.
