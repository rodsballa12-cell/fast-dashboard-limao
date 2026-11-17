# Comissão por quinzena: nota fiscal pelo Forms, conferida contra o Trinks na aba Comissões

**Data:** 2026-11-17
**Origem:** pedido direto do Rodrigo (sessão da nuvem)
**Status:** em vigor (a aba só aparece no ar depois do merge e da próxima publicação)

## Decisão

1. **A quinzena de pagamento.** A 1ª quinzena vai do dia 1 ao 14 e é paga no dia 15. A 2ª vai do
   dia 15 ao último dia do mês e é paga no dia 30 (em fevereiro, no último dia).
   Até aqui a conciliação contra os Pix (`conciliacao_comissoes.py`) cortava em 1–15 / 16–fim. Agora
   ela usa a mesma regra, que fica num lugar só: `scripts/comissao_quinzena.py`.
2. **A nota fiscal chega pelo Forms** "Envio de notas — Profissionais" até o dia do pagamento.
3. **Quem cobra e fecha o valor no Trinks é o Lucas.**
4. **A aba 🧾 Comissões do painel** mostra, para cada quinzena e cada profissional, o valor pelo
   Trinks, o valor da nota, quanto foi pago e a diferença. Quem fecha as três pontas fica
   "Conciliado". As outras situações: pago diferente da nota, pago sem nota, nota diverge do
   Trinks, falta a nota, prazo passou, nota ok aguardando pagamento. A aba também traz a mensagem de cobrança pronta (nada é enviado
   pelo painel) e as notas cujo nome não casou com o cadastro.

## Como funciona

| Lado | De onde vem | Quem roda |
|---|---|---|
| Trinks | serviço × taxa da categoria (`data/comissoes.json`; Spa 25%), pela data de referência da transação | refresh do GitHub, passo "Comissao por quinzena" |
| Nota | planilha de respostas do Forms no OneDrive → `data/notas_profissionais.json` (cofre) | PC: `scripts/notas_forms.py`, dentro do `rodar_agente.ps1` e antes de publicar |
| Pago | Pix "OPEX (Comissão)" do razão (aba Conta_XP do Excel) + Pix de saída da Stone do Spa → `data/comissoes_pagas.json` (cofre) | PC: `scripts/conciliacao_comissoes.py`, que já rodava todo dia |

O valor do Trinks é **referência para conferir a nota**, não a decisão de pagamento: a regra de
comissão não está cadastrada por profissional no Trinks (`comissoes.habilitado` = falso).
Atendimento de pacote entra pelo preço de tabela.

**Pago entra no painel (decisão do Rodrigo, 17/11/2026).** Até aqui o valor pago por pessoa
ficava só no OneDrive, porque o repositório é público. Agora ele vai também para o painel,
**sempre criptografado** pelo cofre. Um Pix paga a quinzena mais recente cujo dia de pagamento
já chegou, com 3 dias de tolerância. Sem lançamento no razão até o dia do pagamento, a aba
diz "aguardando", e não "não pago": o razão entra à mão e atrasa.

## Pendências

- **Ajustar o Forms** para a conferência funcionar: nome em lista, quinzena em lista, campo de valor
  e campo de número da nota. Os números da conferência só são confiáveis depois disso.
- **Onde ficam as respostas.** Baixar (ou sincronizar) a planilha do Forms para
  `OneDrive\Franquia - FAST\Claude\Notas profissionais\`.
- **Apelidos.** Apelido que não casar automaticamente vai em `comissoes_aliases.json`, na chave
  `forms_para_trinks`.
- **Valor da nota.** Confirmar se a nota cobre só a comissão de serviço, sem produto e sem desconto
  de taxa. Se não for assim, a coluna "Diferença" vai acusar todo mundo.

## Revisão

Em 30/11/2026, depois da primeira quinzena inteira pelo Forms: quantas notas casaram sozinhas e
quantas divergiram, e por quê.
