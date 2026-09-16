# FAST Limão · o que qualquer sessão precisa saber antes de mexer

Rodrigo Garcia é dono de duas lojas — **FAST Escova Limão** (aberta em 23/07/2026)
e **FAST Spa Limão** (inaugura 25/09/2026). Ele **não é programador**. Fale em
reais, clientes e dias; nunca em nome de função ou nome de arquivo sem dizer o
que a coisa faz.

## As duas máquinas, e o que só existe em cada uma

| | onde roda | alcança |
|---|---|---|
| **Sessão na nuvem** (claude.ai/code) | container efêmero | só o repositório |
| **Sessão no PC** (`C:\Users\rods_\dev\fast-dashboard-limao`) | Windows, PowerShell 5.1 | repositório **+ Excel + vault do Obsidian** |

O que **só a sessão do PC** alcança:

- **`C:\Users\rods_\OneDrive\Franquia - FAST\Claude\Painel_Gestao_Financeira_SIIBELLO.xlsx`**
  — o DRE. Aba `DRE`, bloco FAST ESCOVA nas linhas 8-22, FAST SPA nas 25-40,
  uma coluna por mês. `scripts/gerar_financeiro.py` lê e gera `financeiro.json`.
- **`C:\Users\rods_\OneDrive\Documentos\Obsidian Vault\Cerebro_Claude`** — onde o
  Rodrigo lê. Os briefings são gravados lá por `scripts/agenda/rodar_agente.ps1`.

**Uma sessão da nuvem que precisar de qualquer um dos dois tem que dizer isso
na hora, não no fim.** Já aconteceu de eu perguntar algo cuja resposta estava
no próprio repositório — o nome do Excel responde "o que é a Siibello" (é a
holding). Procure aqui antes de perguntar.

## De onde vem cada número

```
Trinks (API)  ──► github_refresh.py ──► data/dashboard_data.json ──► index.html
Excel (mão)   ──► gerar_financeiro.py ─► data/financeiro.json
Stone (CSV)   ──► stone_processor.py ──► bloco `stone` do dashboard
Meta Graph    ──► refresh_midias.py ──► data/midias_sociais.json
XP (CSV)      ──► extrato_xp.py ─────► conferência do custo real (não entra no painel)
```

**Receita vem do Trinks. Custo vem do Excel. Conciliação vem da Stone.** A conta
XP é conta de **pagamento**: o dinheiro de venda chega lá em lotes que não batem
com dia nenhum de caixa, e aporte entre os sócios passa por ela — R$ 1,2 milhão
em 90 dias, trinta vezes o movimento da loja. **Nunca leia receita do extrato XP.**

Três unidades, três pastas: `data/` (Escova), `data/spa/`, `data/consolidado/`.
O consolidado é gerado, não digitado.

## Dois relógios de atraso, independentes

O Financeiro tem **dois** frescores que se somam em silêncio, e todo parecer
precisa citar os dois:

1. **DRE** (`financeiro.json` → `baseline`) — entra à mão, atrasa dias.
2. **Extrato Stone** (`stone.periodo_fim`) — CSV carregado à parte.

Em 15/09 um briefing abriu com *"15 PIX sem confirmação, R$ 1.599, ligue para
cada cliente hoje"*. Catorze eram **posteriores ao último dia do extrato** — não
era dinheiro sumido, era extrato atrasado. **Antes de repetir um alarme do
painel, confira até quando vai a fonte que o gerou e o que exatamente foi somado.**

## A empresa digital

Sete cargos em `.claude/skills/`, cada um com sua ficha. `PROTOCOLO.md` é a
língua comum (SITUAÇÃO / FATOS / RISCO / NÃO VEJO / DECISÃO) e `PAINEL.md` diz
quem responde por cada card dos 50. Leia os dois antes de escrever qualquer
parecer.

A regra que mais importa: **o número do card é o começo do parecer, nunca o
parecer.** Se o Rodrigo chegaria sozinho naquela linha olhando o painel, corte.

## Antes de mexer

- **Rodar `python3 scripts/auditoria_coerencia.py`** depois de mudar qualquer
  coisa que toque em dado. Ele confere se unidades somam no consolidado, se os
  períodos são coerentes e se os blocos derivados sobreviveram.
- **Comparar períodos de tamanhos diferentes inventa quedas.** Sábado pesa 37,6%
  do movimento e terça 6,2% (`sazonalidade.peso_dow`). Compare sempre contra a
  meta ponderada do próprio dia, ou contra o mesmo dia da semana.
- **Bloco que some não avisa.** Passos que gravam dado derivado (`densidade_dow`,
  `balcao_vendedor`) já sumiram do payload sem ninguém notar. Se você criar um,
  ensine a auditoria a exigi-lo.
- **`.ps1` precisa de BOM UTF-8.** O PowerShell 5.1 do PC dele lê arquivo sem BOM
  na codepage do sistema e quebra todo acento. E **comando externo não dispara
  `try/catch` no PowerShell** — só seta `$LASTEXITCODE`.
- **Tarefa agendada não tem console.** `Write-Output` lá escreve para lugar
  nenhum; o rastro vai para `_execucoes.log`, no vault.

## Nunca

- **Publicar mensagem para cliente** sem aprovação explícita dele na mesma conversa.
- **Estimar comissão** — não há regra cadastrada no Trinks (`comissoes.habilitado`
  é `false`). O plano está em `config.json > plano_comissao_recepcao`, mas
  calcular pagamento a partir de percentual suposto é proibido.
- **Alterar meta, `financeiro.json` ou a planilha** sem ele mandar.
- **Preencher número que não foi lido.** Campo que faltou vira `NÃO VEJO`.

## Onde a memória fica

`docs/decisoes/` (o que foi decidido, com data de revisão) e `docs/aprendizados/`
(o que custou caro descobrir). O cargo **Memória** é o único que escreve lá.
**Consulte antes de propor algo que pareça novo** — pode já ter sido tentado.

`docs/atas/` guarda os briefings, para as sessões da nuvem lerem o que a do PC
produziu.

`docs/conhecimento/` guarda os nove meses de construção do negócio, vindos do
Obsidian. **Não é lido automaticamente** — o acesso é por busca, sob demanda:

```bash
grep -ril "<assunto>" docs/conhecimento/
```

Carregar a pasta inteira seria gastar quase uma sessão só nisso. E atenção ao
frontmatter de cada arquivo: `status: histórico` significa que aquilo já foi
revertido, e recomendar de volta é o erro mais fácil de cometer ali.
