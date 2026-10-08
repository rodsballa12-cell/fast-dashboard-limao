# Checkpoint do Facebook · mídia cega 06→08/10/2026

> ## ✅ RESOLVIDO em 08/10, 20:44
>
> A coleta voltou sozinha no fire das 20:44 BRT. **Nada foi perdido:** a Meta
> devolveu 06, 07 e 08/10 retroativamente, com entrega normal nos três dias
> (Escova R$ 125,75 · R$ 104,81 · R$ 78,95 — mediana da conta é R$ 100/dia).
> Os três dias foram cegueira de *leitura*, nunca parada de entrega.
>
> **Eu não sei qual das duas coisas destravou:** você entrar no facebook.com,
> ou o checkpoint cair sozinho. Se você não entrou, ele foi embora por conta
> própria — e pode voltar. Por isso este roteiro fica guardado.
>
> **O que continua pendente:** o PASSO 2 (trocar a chave secreta do app, do
> vazamento de 16/09). Esse não se resolve sozinho.

---

## Se voltar a acontecer

Para o Rodrigo, que não é programador. **Não é o token.** Não refaça o
roteiro do `docs/meta-token.md` — o `FAST Painel` continua válido.

**Tempo:** 5 minutos no Passo 1. **Quem pode fazer:** só você.

---

## O que a Meta está respondendo

De 06 a 08/10, toda vez que a rotina pediu os números de anúncio, a Meta
devolveu isto, palavra por palavra:

> *"You cannot access the app till you log in to www.facebook.com and follow
> the instructions given."* — código 190, com um `checkpoint_url`.

Traduzido: **existe um aviso de segurança pendente esperando um humano.**
Enquanto ninguém o lê, a Meta bloqueia o acesso do aplicativo inteiro.

O que isso **não** é:

| | |
|---|---|
| token expirado? | **não** — o `FAST Painel` é utilizador do sistema, não expira |
| senha trocada derrubou? | **não** — token de sistema não depende da sua senha |
| falta de ativo na PARTE C? | **não** — a mensagem seria outra, de permissão |
| conta de anúncio parada? | **não dá para saber** — é justamente isso que ficou cego |

**Ninguém além de você pode resolver.** O `FAST Painel` é um robô: não tem
senha, não faz login. Quem tem de entrar no facebook.com é a pessoa que
administra o portefólio.

---

# PASSO 1 · abrir o facebook.com (5 min)

### 1.1
No **computador**, não no celular. A tela de checkpoint no app às vezes mostra
só parte do aviso.

### 1.2
Abra **facebook.com** logado na conta que administra o portefólio
*Fast Escova Limão*.

### 1.3
**Deve aparecer um aviso** — faixa no topo, ou uma tela cheia que não deixa
passar. Pode pedir uma destas coisas:

- confirmar logins recentes ("foi você que entrou de tal lugar?")
- trocar a senha
- confirmar identidade
- revisar aplicativos ligados à conta

### 1.4
**Vá até o fim.** O checkpoint só libera quando a última tela confirma que está
tudo certo. Parar no meio deixa o bloqueio de pé.

### ✅ Confira
Você volta a navegar no Facebook normalmente, sem nenhuma faixa de aviso.

### ❌ Se não aparecer aviso nenhum

Então o bloqueio está em outro lugar. Confira estes dois endereços e **me
mande um print de cada**:

- **facebook.com/support** — é a *Caixa de Entrada de Suporte*, onde a Meta
  guarda avisos de restrição de conta
- **business.facebook.com/accountquality** — *Qualidade da conta*, onde
  aparecem restrições nos ativos do negócio (páginas, contas de anúncio)

---

# PASSO 2 · trocar a chave secreta do app (10 min)

Isto estava na lista "depois, com calma" do `docs/meta-token.md`. **Agora não
está mais.**

**Por que:** em 16/09 a chave secreta do app apareceu numa conversa. A Meta
varre a internet procurando chave vazada e bloqueia o app quando acha. Vinte e
dois dias depois, o app está bloqueado.

**Eu não consigo provar que é a causa** — a mensagem da Meta não diz. Mas é o
único risco conhecido que ficou aberto neste app, trocar é de graça, e **não
derruba o token** que você criou.

### 2.1
Abra **developers.facebook.com/apps/964019103388501/settings/basic/**

### 2.2
Procure **Chave Secreta do Aplicativo** → **Mostrar** → **Redefinir**.

### 2.3
Ainda nessa aba, olhe o **topo da página do app**. Se houver faixa vermelha ou
amarela dizendo que o app está restrito, **me mande um print** — o caminho de
saída aí é outro (recurso/apelo, não conserto).

---

# PASSO 3 · testar

### 3.1
**github.com/rodsballa12-cell/fast-dashboard-limao/actions**

### 3.2
Coluna da esquerda → **Refresh Midias Sociais (diario)** → botão
**Run workflow** → de novo **Run workflow**.

### 3.3
Espere uns **5 minutos** (com a Meta recusando, a rotina demora: ela tenta
cada chamada três vezes antes de desistir) e recarregue com **F5**.

| você vê | significa |
|---|---|
| ✅ verde | coleta voltou — me avise que eu confiro o dado e republico o painel |
| ❌ vermelho | ainda bloqueado — me avise, eu leio o log e digo o que mudou na mensagem |

---

## O que NÃO fazer

- **Não gere token novo.** Com o checkpoint de pé, o token novo toma o mesmo
  erro 190 — você gastaria 20 minutos para chegar no mesmo lugar. Se depois do
  Passo 1 ainda falhar, *aí* a gente refaz o token.
- **Não cole o token em lugar nenhum** além da tela onde ele nasce e da caixa
  do segredo no GitHub. Nem para mim.

---

## Enquanto estiver bloqueado, o que fica cego e o que não

| | |
|---|---|
| **cego** | gasto de anúncio, CPA por conversa, alcance, frequência, seguidores do Instagram — das **duas** unidades |
| **em dia** | receita (Trinks), conciliação (Stone), agendamentos, ticket |
| **atrasado por outro motivo** | DRE (`financeiro.json`, de 02/10 — só a sessão do PC alcança o Excel) |

**O risco real:** de 27 a 31/08 a conta parou de entregar quatro dias com tudo
ativo, ninguém viu, e custou ~R$ 480. Com a coleta bloqueada eu **não consigo
dizer** se ela está entregando — é exatamente o número que não chega. (Em
06→08/10 ela estava entregando normalmente, mas isso só se soube depois.)

**O que você consegue conferir sozinho em 30 segundos:** abra o
**Gerenciador de Anúncios** no celular. Se houver gasto hoje, a conta está
entregando e o problema é só a leitura. Se estiver zerado, é entrega parada
*também* — e aí é urgente.

---

*Criado em 08/10/2026. A aba Mídia do painel agora mostra uma faixa vermelha
dizendo "mídia cega há N dias" em vez de desenhar os zeros em silêncio, e o
`alerta_entrega.py` volta a mandar e-mail quando a coleta falha dois dias
seguidos.*
