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
| Sob demanda | `aniversarios`, `aniversarios_dispatch` (por comentário), `stone_entrada`, `historico_cliente`, `fechamento_dia`, `cofre_checar`, `audit_consolidado`, `meta_probe`, `trinks_probe` | manual | — |
| Deploy do site | `pages-build-deployment` (do GitHub) | a cada commit na main | publica o painel no GitHub Pages; falhou por timeout em 19/11 12:03 e 12:33, reexecutado e passou |

## Conferido em 19/11/2026 (só GitHub)

- **Refresh do painel**: os quatro passos opcionais (densidade, preço, WhatsApp das profissionais e quinzena)
  não usam mais `|| true`. Se falharem a rodada continua verde, mas o carimbo de saúde lista quais
  falharam (`passos opcionais com erro: ...`). Antes o erro de `dotenv` no WhatsApp das profissionais
  passou semanas sem aparecer.
- **Mídias**: a coleta grava antes da auditoria. Em 13 a 17/11 a rodada ficou vermelha só por causa da
  auditoria de coerência (4 divergências); o dado de mídia chegou e o carimbo registra "nao e midia".
- **Instagram**: a métrica `profile_activity` retorna HTTP 400 (a Meta não a aceita mais). O erro agora
  aparece inteiro no log, com a lista de métricas válidas, para escolher a substituta. Até lá o campo vale 0.
- **Cargos na nuvem**: continuam parados (token 401). As issues "Cargo sem parecer" (#67 a #74) ficam
  abertas de propósito: são o alarme enquanto o `CLAUDE_CODE_OAUTH_TOKEN` não for renovado.

## Rotina do claude.ai (sem PC, sem chave)

"Conselho FAST Limão · noite" (22h17): **pausada em 18/11/2026**. Repetia o conselho do PC
sem o cofre e gastava a mesma cota. Para religar: pedir numa sessão "religue o conselho do claude.ai".

## Quem gasta a cota do Claude, hora a hora (18/11/2026)

A assinatura tem uma cota que vale por 5 horas e outra por semana, **divididas por tudo abaixo**
e pelas conversas do Rodrigo. Quando uma acaba, quem roda depois fica sem resposta.

| Hora (BRT) | Rotina | Peso |
|---|---|---|
| **00h40 → ~03h** | **FAST: os sete cargos em fila, conselho por último** | alto |
| 06h00 | backup do espólio (navegador) | baixo |
| 07h00 | Google Business (Supermetrics) | baixo |
| 07h14 e 19h14 (dias úteis) | painel patrimonial, rodada da manhã e do fechamento | alto |
| 07h23 (quarta) | post do LinkedIn | médio |
| 08h00 e 18h00 | mídias sociais (Supermetrics) | médio |
| 10h07 a 18h07 e 10h37 a 17h37 (dias úteis) | cotações do pregão (+ notícias no :07) | médio, somado |
| 19h00 | rotina diária do cérebro (Obsidian) | alto |

De 00h40 às 06h nada mais roda: é a única janela que fica só para a FAST.

## PC do Rodrigo: só roda se o PC estiver ligado

Uma tarefa no Agendador do Windows, `FAST\Rodada da madrugada` (`scripts/agenda/instalar_tarefas.ps1`),
às **00h40**, com os sete cargos **em fila** (memória, marketing, financeiro, relacionamento,
pessoas, operação, conselho + publicar o painel). Antes do meio-dia o dia de referência é
**ontem**: a ata leva a data do dia fechado. Até 18/11 eram sete tarefas de dia (07h30 a 11h30
e conselho 22h30), e caíam no limite de cota das outras rotinas. Cada cargo da fila chama `rodar_agente.ps1`, que faz:

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
