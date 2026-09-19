# A chave do Trinks do Spa — o que falta e por quê

**Escrito em 19/09/2026. O Spa abre em 25/09.**

Hoje o painel do Spa não tem de onde puxar receita. Mídia entra por um lado,
faturamento não entra por lado nenhum — e sem os dois não existe custo por
cliente, ticket, nem meta cumprida.

## O que eu já verifiquei (não é chute)

Rodei a rotina que pergunta ao Trinks "quais lojas esta chave enxerga?".
A resposta, em 19/09 às 12h39:

```
{"data": [{"id": 276461, "nome": "SAO PAULO - SP - LIMAO FE"}],
 "totalRecords": 1}
```

**Uma loja só: a Escova.** Testei também pedindo inativas e pedindo página
maior — continua uma. Não é filtro escondido: a chave de hoje não alcança o
Spa.

## O detalhe que muda o caminho

Pela documentação do próprio Trinks, **o token é da PESSOA, não da loja** — e
dá acesso a *todos os estabelecimentos daquele usuário*.

Se a chave atual vê só a Escova, então o Spa **não está pendurado no mesmo
login do Trinks**. Daí saem dois caminhos, e o primeiro é bem melhor:

### Caminho A — juntar as duas lojas no mesmo login (preferível)

Pedir ao Trinks que vincule o estabelecimento do Spa ao mesmo usuário que já
administra a Escova. Feito isso, **a chave que já existe passa a enxergar as
duas** e não é preciso gerar nada novo.

Fica faltando só descobrir o número do Spa — e isso eu faço sozinho: é rodar
de novo a mesma rotina de descoberta, que vai listar as duas.

Vantagem: uma chave só para manter, uma só para trocar no dia em que vazar.

### Caminho B — token próprio do login do Spa

Se o Spa tiver que ficar em outro login:

1. Entrar no Trinks **com o login do Spa**
2. Ir em **Meu Cadastro**
3. Procurar **Token de API Pessoal**
4. **Gerar token** (ou **Visualizar token**, se já existir)

⚠️ **Existe uma liberação prévia da equipe Trinks, que leva até 48 horas.**
Com a abertura em 25/09, esse pedido precisa sair **hoje ou amanhã**. É a
parte do processo que não depende de nós e não dá para acelerar depois.

## Onde a chave é guardada

Nunca em conversa, arquivo, planilha ou e-mail. Só em dois lugares: a tela do
Trinks onde ela nasce, e o cofre do GitHub.

O cofre fica em:

**https://github.com/rodsballa12-cell/fast-dashboard-limao/settings/secrets/actions**

Lá, botão **New repository secret**, e criar estes dois — o nome tem que ser
exatamente assim, maiúsculas e underscores inclusive:

| Name | Secret |
|---|---|
| `TRINKS_API_KEY_SPA` | a chave que o Trinks mostrou |
| `TRINKS_ESTABELECIMENTO_ID_SPA` | o número da loja do Spa |

No **Caminho A**, o `TRINKS_API_KEY_SPA` recebe a mesma chave que a Escova já
usa — o que separa as duas lojas é só o número do estabelecimento.

Depois de salvo, a chave fica invisível até para quem a cadastrou: o GitHub
mostra só o nome. Isso é proposital e é o motivo de ela ficar ali.

## Como eu confirmo que funcionou

Assim que os dois estiverem salvos, eu rodo a rotina de descoberta de novo.
Ela responde em um minuto e diz se a chave passou a enxergar o Spa — sem que
a chave apareça em lugar nenhum. Se enxergar, disparo o refresh e o painel do
Spa começa a ter receita no mesmo dia.

## Se o Trinks disser não

Se a liberação não sair antes de 25/09, o Spa abre com o painel de receita em
branco. Isso é ruim mas não é perda: o Trinks guarda o histórico, e quando a
chave entrar o refresh traz os dias anteriores junto. O que se perde é
**enxergar em tempo real na semana de abertura** — justamente a semana em que
mais adianta corrigir alguma coisa.
