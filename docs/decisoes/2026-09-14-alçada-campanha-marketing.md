# Gerente de Marketing passa de "só lê" para "pode gastar"

**Data:** 2026-09-14 · **Quem decidiu:** Rodrigo
**Departamentos ouvidos:** Marketing

## Contexto

O cargo `/marketing` no repo nascia sem alçada de execução: só lia JSON e
entregava parecer. A fusão com o `/marketing-fast` (máquina local) trouxe
acesso ao Supermetrics com ferramentas de gestão de campanha — o cargo
passou a ter a chave técnica para criar e alterar campanhas pagas.

Isso muda o perfil de risco: um erro de execução queima verba real, não
apenas gera um relatório errado.

## Alternativas descartadas

**Manter só-leitura:** perdia a capacidade de executar ajustes rápidos
(pausar campanha que parou de entregar, subir orçamento com ROAS alto).
O custo de uma campanha parada por 4 dias em ago/2026 foi ~R$ 480.

**Aprovação livre ("aprovado" na sessão):** risco de aprovação ambígua
cobrir campanha errada ou valor não discutido.

## O que foi decidido

O cargo pode executar criação e alteração de campanha **somente** quando
o Rodrigo escrever, na mesma sessão, uma mensagem que contenha:
1. A palavra "aprovado" (ou "criar campanha" / "publicar")
2. O nome da campanha
3. O valor diário

"Aprovado" isolado não autoriza nada. Qualquer um dos três elementos
faltando → preparar e aguardar, não executar.

## O que esperamos

Que nenhuma campanha seja criada ou alterada por iniciativa do agente,
e que toda execução seja rastreável a uma mensagem específica do Rodrigo.

## Revisar em

2027-03-14 — avaliar se a trava está gerando atrito desnecessário ou
se deveria ser relaxada para ajustes de orçamento dentro de faixa pré-aprovada.

## Resultado

_(em branco até a revisão)_
