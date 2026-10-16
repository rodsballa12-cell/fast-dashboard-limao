# Corte de jornada só economiza onde há salário fixo

**Descoberto em:** 16/10/2026 · **Quase custou:** uma recomendação de Pessoas
para fechar a manhã fraca de segunda/terça/quarta como medida de economia.

## O que aconteceu

A Escova tem manhãs quase vazias em segunda, terça e quarta (0,30 a 0,34
atendimento simultâneo, contra 2,62 no sábado — `densidade_dow.py`). A
tentação natural foi propor abrir mais tarde nesses dias para "economizar
jornada".

Mas o DRE de setembro mostra que a Comissão sobre produção é 35,1% da
receita e é a **única** forma de remuneração dos profissionais de
atendimento — cabeleireiros, manicures, maquiador(a). Rodrigo confirmou:
**todos são comissionados, sem salário fixo para os atendimentos.** Sem
cliente na cadeira, não existe comissão a pagar de qualquer jeito — fechar a
cadeira numa manhã vazia não corta nenhum custo, porque não havia custo ali
para começo de conversa.

O único custo que roda com a loja aberta, independente de volume, é o
**Pessoal fixo** do DRE: Recepção + limpeza (CLT) e a fatia da Gerente (PJ) —
R$ 11.941/mês somados em setembro, alheios ao movimento do dia.

## A regra

**Antes de propor corte de jornada como economia, pergunte: essa pessoa tem
piso salarial fixo, ou só ganha se atender?** Se é 100% comissionada, o corte
de horário não move a folha — só move a oferta de atendimento, que é outra
decisão (e tem outro risco: perder o cliente que aparece fora do horário
"ótimo"). A economia real só existe no custo fixo que persiste com a loja
fechada — na FAST, hoje, isso é recepção e gerência.

Sintoma de alerta: a proposta de corte fala em "horas vazias" mas nunca cita
em qual linha do DRE (fixo ou variável) a pessoa está. Se ela está em
variável/comissão, pare e pergunte pelo fixo antes de recomendar qualquer
coisa.

## Onde isso mora no projeto

`.claude/skills/pessoas/SKILL.md`, Passo 4, já avisava para nunca propor
"corte de jornada sem dizer quanto economiza" — mas faltava a pergunta
anterior: **se economiza alguma coisa**. A ficha de Pessoas deveria checar o
regime de remuneração (`grupos` do `financeiro.json`, bloco `VARIAVEL` vs
`PESSOAL`) antes de qualquer proposta de escala.

Vale também para o Spa quando a base de dados dele amadurecer: mesma
estrutura de comissão, mesma pergunta antes de propor qualquer corte.
