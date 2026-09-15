# Atas — o que cada cargo disse, dia a dia

Cópia versionada dos briefings que as tarefas agendadas geram no Obsidian.

`AAAA-MM-DD-<cargo>.md`

## Por que existe

O briefing no vault vive só na máquina do Rodrigo. Aqui ele ganha três coisas
que o vault não dá: **histórico versionado**, **leitura por qualquer sessão**
— inclusive as que rodam na nuvem e não alcançam o disco dele — e **consulta
pela Memória**, que passa a poder responder "isso já apareceu num conselho
antes?".

Em 15/09/2026 o Rodrigo perguntou como tinha sido o Conselho da véspera e não
houve resposta possível: a ata existia, mas do outro lado de uma parede.

## Como chega aqui

`scripts/agenda/rodar_agente.ps1` grava no vault, copia para cá e dá push —
**apenas deste diretório**, apenas do markdown que ele mesmo acabou de gerar.

Se o push falhar, o briefing continua no vault e o próprio arquivo avisa. A
publicação nunca derruba a entrega.

## O que não vem para cá

Nada além das atas. Decisões continuam em `docs/decisoes/`, aprendizados em
`docs/aprendizados/`. Ata é o que foi observado num dia; decisão é o que se
resolveu fazer.
