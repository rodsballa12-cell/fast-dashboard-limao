# Protocolo de Parecer · a língua comum dos departamentos

Todo departamento fala neste formato. Não é burocracia: é o que permite que o
Conselho leia seis pareceres lado a lado e enxergue o que nenhum departamento
sozinho consegue ver.

```
PARECER · <departamento> · <data> · dado de <hora>

SITUAÇÃO   🟢 normal | 🟡 atenção | 🔴 ação hoje

FATOS      até 3 linhas. Cada uma com número e período.
           Sem número não é fato, é opinião.

RISCO      o que piora se ninguém mexer, e em quanto tempo.

NÃO VEJO   o que está fora das minhas chaves, endereçado ao
           departamento que tem a chave.

DECISÃO    o que está acima da minha alçada e precisa do Rodrigo.
```

## O campo que faz os agentes conversarem

**`NÃO VEJO` é o mecanismo.** Cada departamento é cego por fora das próprias
chaves, e o formato obriga a declarar a cegueira em voz alta, com endereço.

> Marketing: *"NÃO VEJO se as 340 mensagens do mês viraram agendamento.
> → Operação."*

O Conselho lê esse campo de todos, casa pergunta com quem tem a chave, e a
resposta que sai do cruzamento não estava em nenhum parecer isolado.

## As três formas do cruzamento

**Cadeia causal** — dois fatos de departamentos diferentes que se explicam.
*Financeiro: margem caiu 4 pontos. Operação: 31 de 58 serviços cobrados fora
da tabela.* Nenhum dos dois é conclusão; juntos são.

**Contradição** — dois departamentos discordando sobre a mesma realidade.
*Marketing: melhor mês de alcance. Operação: pior semana de ocupação.* Uma
das duas leituras está errada, e descobrir qual vale mais que os dois pareceres.

**Silêncio suspeito** — um departamento diz 🟢 num assunto que outro marcou 🔴.
Quase sempre significa que ele não estava olhando.

## Regras que valem para todos

1. **Frescor antes de número.** Todo parecer abre dizendo de quando é o dado.
   Dado velho apresentado como atual é o pior defeito possível.
2. **Nunca preencher número não lido.** Campo que faltou vira `NÃO VEJO`.
3. **Nada de jargão.** Rodrigo não é programador. Fale em reais, clientes e dias.
4. **Três fatos no máximo.** Parecer que lista tudo não prioriza nada.
5. **Alçada é limite duro.** Acima dela você escreve em `DECISÃO` e para.
