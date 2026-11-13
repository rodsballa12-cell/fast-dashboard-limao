# Inventário das automações da FAST Limão · 01/11/2026

Onde cada rotina roda, do que depende e o que acontece quando ela para.
Atualize esta tabela sempre que criar, mudar ou desligar uma rotina.

## Nuvem do GitHub: roda com o PC ligado ou não

| Rotina | Arquivo | Quando (BRT) | Faz o quê |
|---|---|---|---|
| Refresh do painel | `refresh.yml` | 03h, 06h, 07h e de hora em hora das 10h à 21h | Trinks das duas lojas → dashboard, saúde e decisões abertas |
| Mídias | `midias_refresh.yml` | 07h, 09h e 11h | Meta Ads, Instagram e Facebook das duas lojas; Google Business via Supermetrics |
| Trinks scrape | `trinks_scrape.yml` | 06h, 12h, 18h e 23h | relatório de movimentações financeiras |
| WhatsApp automático | `campanhas_wa.yml` | 10h | aniversário e reativação (fila) |
| **Cargos na nuvem** | `cargos_nuvem.yml` | **horários desligados em 13/11** (chave dava 401 e a falha sobrescrevia a ata boa do PC); só disparo manual | os sete pareceres e o conselho, conferidos pelo formato; ata em `docs/atas/`; o conselho vira issue (e-mail e celular) |
| A empresa se reuniu ontem? | `auditoria_agenda.yml` | 09h20 e 10h20 | confere se as atas do dia anterior existem |
| Watchdog | `watchdog.yml` | 09h e 15h | abre issue quando o pipeline local trava |
| Conselho Sync | `conselho_sync.yml` | quando `Briefings/*-conselho.md` chega na main | aplica as decisões aprovadas no painel |
| HubSpot sync | `hubspot_sync.yml` | desativado desde 14/09 | — |
| Sob demanda | `aniversarios*`, `stone_entrada`, `historico_cliente`, `fechamento_dia`, `cofre_checar`, `debug_*`, `probe_*`, `sults_probe`, `trinks_discover`, `audit_consolidado` | manual | — |

## Rotina do claude.ai (sem PC, sem chave)

"Conselho FAST Limão · noite", todo dia às 22h17, notificação no celular. Não tem o cofre (lê só o que é aberto) e não consegue gravar no repositório.

## PC do Rodrigo: só roda se o PC estiver ligado

Sete tarefas no Agendador do Windows (`scripts/agenda/instalar_tarefas.ps1`), nos mesmos
horários dos cargos. Cada uma chama `rodar_agente.ps1`, que faz:

1. `git pull` e **abre o cofre** com o dado novo (desde 13/11; antes lia a última cópia aberta à mão);
2. **o que só o PC alcança**: reserva Stone no Excel, Stone do Spa no razão, dados frescos
   no Excel, DRE → `financeiro.json`, comissões Trinks × Pix, leitura do SULTS;
3. **se a nuvem já gravou o parecer do dia**: só copia a ata para o Obsidian e termina;
4. senão, roda o cargo no próprio PC (fallback), confere o formato e grava a ata no vault
   e em `docs/atas/`.

## O que só existe no PC (e por isso continua lá)

Excel da Siibello (DRE), vault do Obsidian, SULTS (franqueadora), OneDrive (logos, contratos).

## Segredos de que a nuvem precisa

| Segredo | Para quê | Situação |
|---|---|---|
| `FAST_COFRE_CHAVE`, `FAST_PAINEL_SENHA` | abrir o cofre | já existem |
| `TRINKS_*`, `META_*`, `SUPERMETRICS_*` | refresh e mídias | já existem |
| **`CLAUDE_CODE_OAUTH_TOKEN`** | rodar os cargos com a assinatura Max, sem custo extra | **falta criar**: no PC, `claude setup-token` e colar em Settings → Secrets → Actions do repositório |

## Linha do tempo da falha que motivou a mudança (23 a 31/10/2026)

| Período | O que os cargos responderam | Causa |
|---|---|---|
| até 22/10 | "Credit balance is too low" | crédito acabou |
| 23/10 manhã | último parecer de verdade | — |
| 23/10 22h30 a 30/10 | "o comando /conselho não existe nesta sessão" | o claude do PC parou de reconhecer o atalho `/cargo` (provável atualização); de 29/10 em diante somou-se o `Start-Job` rodando fora da pasta |
| 30/10 tarde em diante | nenhuma ata | PC desligado ou script parado — a confirmar no `_execucoes.log` |

Nas quatro vezes o alarme existia e não tocou, porque procurava a frase do erro anterior.
A partir de agora vale o **formato do parecer** (`scripts/agenda/gravar_ata.py`).
