# WhatsApp oficial (API) nos números das lojas, por coexistência

**Data:** 2026-11-17 · **Quem decidiu:** Rodrigo (sessão da nuvem)
**Status:** em andamento
**Reabre:** [2026-09-14-conselho-nao-configurar-whatsapp-cloud.md](./2026-09-14-conselho-nao-configurar-whatsapp-cloud.md)

## Decisão

Configurar o envio pela API oficial do WhatsApp **nos números que as lojas já usam**:

| Unidade | Número |
|---|---|
| Escova | +55 11 96612-9197 |
| Spa | +55 11 99024-3927 |

Não haverá chip novo. As clientes e a equipe já têm esses números salvos.

Usos previstos, em ordem:

1. Equipe: lembrete e cobrança da nota fiscal da comissão (aba Comissões).
2. Clientes: aniversário e clientes sumidos. A sequência está pronta desde setembro e nunca enviou.

## Por que agora dá, e em setembro não dava

Desde 2025 a Meta permite a **coexistência**: o número continua no aplicativo WhatsApp Business do
celular da loja e passa a enviar pela API ao mesmo tempo, com o histórico sincronizado. Em 14/09 a
migração tiraria o número do aplicativo, e a recepção perderia o atendimento.

## O que isso exige (descoberto em 17/11)

- **Um parceiro oficial da Meta** (Solution Partner ou Tech Provider). A conexão por coexistência
  é feita por um fluxo de cadastro que só esses parceiros oferecem. Cadastrar o número direto no
  developers.facebook.com o **tira do aplicativo**, então esse caminho está descartado.
- **Acesso de administrador** à conta Meta Business. Foi o que travou em 14/09.
- **A pessoa com o celular de cada loja** na hora de conectar: o aplicativo mostra o código QR para
  escanear.
- **Cartão cadastrado.** A Meta cobra por mensagem: aviso para a equipe custa cerca de
  US$ 0,007 no Brasil; mensagem de marketing para cliente custa bem mais. O parceiro costuma
  cobrar uma mensalidade à parte.
- **Textos aprovados pela Meta** antes do primeiro envio.

## O que a Meta mostrou em 17/11 (sonda só de leitura, `meta_probe.yml`, alvo=whatsapp)

| Portfolio | ID | Papel do Rodrigo | Verificado | Observação |
|---|---|---|---|---|
| Fast Escova Limão | 1493087112411026 | **ADMIN** (único) | não | |
| FAST Escova Limao | 1091274630024583 | **ADMIN** (único) | não | dono do app "FAST Limão · integrações" (964019103388501) |
| Fast Spa 2026 | 1042081858063235 | só funcionário | não | o administrador é outra pessoa |

- **O bloqueio de 14/09 caiu na Escova.** O Rodrigo agora é administrador dos dois portfolios da
  Escova, mas é o único administrador de cada um: se perder o acesso, ninguém recupera.
- **No Spa ele ainda não é administrador.**
- **Nenhuma página está ligada a um WhatsApp.** Nenhum portfolio tem usuário do sistema.
- **O token do painel não tem as permissões de WhatsApp** (`whatsapp_business_management` e
  `whatsapp_business_messaging`). Por isso não deu para ver se já existe conta de WhatsApp (WABA).
  É token de usuário e vence; o de usuário do sistema não vence.
- **Há dois portfolios da Escova com quase o mesmo nome.** É preciso escolher um para ser a casa
  do WhatsApp.

## O que muda no código

`scripts/wa_dispatch.py` fala direto com a Graph API da Meta. Conforme o parceiro escolhido, muda
o endereço e a chave. A trava continua: `disparo_wa.ativo` segue `false` até o primeiro teste no
celular do Rodrigo.

## Pendências

- [ ] Rodrigo: confirmar quem é administrador da conta Meta Business ("Fast Escova Limão").
- [ ] Escolher o parceiro: aceita coexistência, dá acesso à API (não só uma caixa de entrada),
      repassa o custo da Meta sem margem e fatura em reais.
- [ ] Telefones da equipe: puxar do Trinks ou lista do Lucas, sempre no cofre.
- [ ] Aprovar os textos (rascunho na conversa de 17/11).

## Revisão

2026-12-01: o parceiro foi escolhido e o teste no celular do Rodrigo foi feito?
