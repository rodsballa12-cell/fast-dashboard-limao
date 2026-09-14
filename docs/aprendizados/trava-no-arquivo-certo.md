# Trava larga demais não protege — atrapalha, e ainda deixa a janela aberta

**Descoberto em:** 14/09/2026 · **Custo:** uma sessão travada sem conseguir
publicar, e uma proteção que quase foi desmontada por engano.

## O que aconteceu

Ao montar as tarefas agendadas dos cargos, escrevi uma lista de bloqueios no
`.claude/settings.json` pensando só no agente rodando sozinho de madrugada.
Entraram lá `git push`, `git commit`, `rm` e `curl`.

Dois defeitos, em direções opostas:

**Largo demais para quem trabalha.** O `settings.json` governa **todas** as
sessões do projeto — a do dono, a minha, e a agendada. Bloquear `git push`
travou a própria sessão que tinha acabado de escrever a regra. E `deny` é
absoluto: não existe prompt de aprovação para contornar, como existe no "ask".

**Estreito demais para o risco real.** Ao propor o conserto, pedi para remover
os quatro de uma vez — incluindo o `curl`. Foi outro agente, revisando, que
apontou o furo: bloquear `wa_dispatch.py` e `campanhas_wa.py` não impede nada
se o `curl` estiver livre. **A API da Meta atende um `curl` igual atende o
script.** Eu tinha trancado a porta e ia abrir a janela ao lado.

O mesmo revisor apontou o segundo custo: liberar `rm` e `git push/commit` para
um agente sem supervisão não é só "deixar de impedir mensagem" — é abrir mão
de reversibilidade.

## As regras

**1. A trava vai no escopo de quem ela deve limitar.** Um arquivo que vale para
todas as sessões não consegue ser permissivo para quem trabalha e restritivo
para quem roda sozinho. Restrição de agente autônomo pertence à configuração
daquela execução, não à do projeto inteiro.

**2. Bloquear a ferramenta não é bloquear a capacidade.** Pergunte sempre: *o
que mais alcança o mesmo resultado por outro caminho?* Bloquear o script sem
bloquear o `curl` é teatro de segurança. Vale para qualquer trava: liste os
caminhos, não as ferramentas.

**3. A alçada da ficha é o limite primário; o deny é cinto de segurança.** As
fichas já dizem "nunca altera arquivo", "nunca dispara mensagem". O deny
existe para o caso de a instrução não bastar — e por isso deve ser *estreito e
certeiro*, não largo e incômodo.

## O que ficou combinado

`curl` permanece bloqueado — é o único dos quatro que protege o objetivo
declarado. `git push`, `git commit` e `rm` foram liberados, com a concessão
registrada de que um agente agendado passa a poder publicar e apagar.

Pendente: um arquivo de permissões exclusivo das tarefas agendadas, para
devolver `rm` e `push` ao bloqueio sem travar quem trabalha.

## O detalhe que não deve se perder

**Eu não consegui consertar sozinho.** Ao tentar editar minha própria lista de
permissões, fui bloqueado por uma trava de auto-modificação — e ela estava
certa. É a mesma ideia de alçada que escrevemos para os cargos, aplicada a
quem escreve as alçadas.

E o furo do `curl` foi achado por **outro agente revisando**, não por mim. A
revisão cruzada não é formalidade: foi ela que impediu a proteção de virar
enfeite.
