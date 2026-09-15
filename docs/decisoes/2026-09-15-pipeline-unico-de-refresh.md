# Um pipeline só de refresh — a nuvem executa, o PC para

**Data:** 2026-09-15 · **Quem decidiu:** Rodrigo
**Departamentos ouvidos:** Memória (auditoria de coerência)

## Contexto

O painel era atualizado por **dois caminhos independentes** escrevendo os
mesmos arquivos:

| | O que fazia |
|---|---|
| `refresh.yml` no GitHub Actions | Escova + Spa + consolidado + mapa de escala |
| Tarefa agendada no PC do Rodrigo | **somente a Escova**, e push |

Quando o PC rodava por último, o consolidado ficava para trás. Em 14/09/2026 a
auditoria de coerência pegou um consolidado de 20h05 convivendo com uma Escova
de 21h00 — **o painel da holding descreveu por uma hora um momento que já tinha
passado.** Ninguém notaria olhando: a diferença era de uma hora de operação num
número de três dígitos.

O defeito não era de nenhum dos dois scripts. Era de não existir dono único.

## O que foi conferido antes de desligar

**Os dois pipelines produziam payload idêntico:** 110 chaves, mesmo tamanho,
nenhuma chave exclusiva de um lado. Comparação feita entre o último commit do
robô e o último commit do PC.

**O `index.html` busca os JSON em tempo real.** A parte do script do PC que
regenerava o HTML era legado — o painel lê o dado na hora que abre.

**Frequência:** o PC não rodava de hora em hora como o README dizia. Pelo
histórico de commits eram ~5 execuções por dia, mesma ordem da nuvem.

## Alternativas descartadas

**Fazer o script do PC chamar o consolidador também** — resolveria o sintoma e
manteria dois donos do mesmo arquivo. O próximo passo que alguém acrescentasse
a um dos lados voltaria a divergir.

**Deixar como estava e confiar no auditor** — o auditor avisa depois do fato.
Melhor não produzir a divergência.

## O que foi decidido

O refresh passa a ser responsabilidade **exclusiva da nuvem**. A tarefa
agendada do PC é desligada.

Coerente com a divisão já registrada: **PC julga, nuvem executa.** Buscar dado
e publicar é execução.

## O que mudou junto

Os slots foram realinhados ao que cada um alimenta, e passaram de 5 para 7:

| BRT | Serve a |
|---|---|
| 09h | baseline da manhã |
| **11h** | o briefing `/operacao-diaria` das 11h30 |
| 14h · 16h · 18h | o dia em andamento, cobrindo o pico de 16h-18h |
| **20h** | depois do corte de entrada das 19h15 — receita do dia fechada |
| **22h** | o `/conselho` das 22h30 |

Custo: ~190 requisições/dia contra cota de 10.000/mês. **Menos que os ~259/dia
que os dois pipelines juntos gastavam**, com mais cobertura.

## O que esperamos

Consolidado nunca mais defasado em relação à unidade, e o auditor de coerência
deixando de acusar diferença de frescor.

## Revisar em

2026-10-15 — conferir se sete slots bastam e se a cota ficou onde se projetou.

## Resultado

_(em branco até a revisão)_
