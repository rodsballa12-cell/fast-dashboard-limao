# Alarme que procura a frase do erro só pega o erro de ontem

**Descoberto em:** 31/10/2026 · **Custou:** de 23 a 31/10, nenhum parecer de verdade dos
sete cargos, com as tarefas rodando todos os dias e o painel de saúde marcando "ok".

## O que aconteceu

O carimbo de saúde marcava falha quando a saída tinha "credit balance" ou "too low", que
era o erro de 22/10. O erro seguinte foi outro ("o comando /conselho não existe nesta
sessão") e passou como "ok" por uma semana. Depois o PC simplesmente parou de mandar ata.
Foram quatro silêncios em duas semanas: crédito, mídia do Spa 42h parada, comando
inexistente e PC sem ata. Nos quatro o alarme existia.

## A regra

**Confira o que o resultado PRECISA ter, não o que o erro costuma dizer.** Um parecer
tem SITUAÇÃO e FATOS (o conselho tem JANELAS e DECISÕES; a Operação tem O DIA e VIGIAR).
O que não tiver isso é falha, seja qual for o motivo, inclusive um motivo que ninguém
imaginou ainda. O verificador é `scripts/agenda/gravar_ata.py --avaliar`.

## E a outra metade

**Rotina que só roda num PC doméstico fica refém do PC.** Os cargos agora rodam primeiro
na nuvem do GitHub (`cargos_nuvem.yml`); o PC fica com o que só ele alcança (Excel,
SULTS, Obsidian) e serve de reserva.
