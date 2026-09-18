# Token da Meta · o caminho que não morre

> **Não use o Graph API Explorer.** Já tentamos duas vezes:
> **10/09** — token de usuário, morreu quando o Rodrigo trocou a senha.
> **16/09** — token do Explorer, nasceu 09h40 e **morreu 11h00 do mesmo dia**.
> O botão *Generate Access Token* entrega token de curta duração: uma a duas
> horas, arredondado para a hora cheia. Os "60 dias" só existem depois de
> trocar por um de longa duração — passo que quase ninguém faz.
>
> O **Usuário do Sistema** não tem senha para trocar nem sessão para expirar.

**Tempo:** 15 minutos. **Uma vez na vida.**

---

## O que você vai criar

Um "funcionário robô" dentro do Business Manager. Ele não é pessoa, não faz
login, não tem senha. Serve só para o painel ler os números — e como não tem
sessão, não expira.

## Os seis ativos que ele precisa alcançar

Anote, porque o passo 3 falha silenciosamente se faltar um:

| | Escova | Spa |
|---|---|---|
| **Conta de anúncios** | FE - LIMÃO | FS - LIMÃO |
| **Página do Facebook** | Fast Escova Limão | Fast Spa Limão |
| **Instagram** | fastescova.limao | fastspa.limao |

⚠️ O Spa está num portfólio separado chamado **Fast Spa 2026**. Se a lista do
passo 3 só mostrar os três da Escova, é isso — veja "Se o Spa não aparecer".

---

## PASSO 1 · Abrir a página certa

Cole no navegador:

**https://business.facebook.com/settings/system-users**

**Você deve ver:** uma página com o título *Usuários do sistema* e um botão
azul **Adicionar**. Provavelmente a lista está vazia.

**Se cair numa tela pedindo para escolher uma empresa:** escolha o portfólio
da Escova e cole o link de novo.

**Se der erro ou abrir outra coisa:** vá em business.facebook.com, clique na
engrenagem ⚙️ (canto inferior esquerdo), e procure **Usuários** no menu da
esquerda. Dentro dele, *Usuários do sistema*.

---

## PASSO 2 · Criar o robô

1. Clique em **Adicionar**
2. **Nome:** `FAST Painel`
3. **Função:** escolha **Administrador** (não "Funcionário" — funcionário não
   consegue gerar token com todas as permissões)
4. Aceite os termos e **Criar usuário do sistema**

**Você deve ver:** `FAST Painel` na lista, com dois botões à direita —
**Adicionar ativos** e **Gerar novo token**.

---

## PASSO 3 · Dar acesso aos ativos ← **é aqui que dá errado**

Com o `FAST Painel` selecionado, clique em **Adicionar ativos**.

Abre uma janela com abas do lado esquerdo. **Você vai fazer isso três vezes**,
uma por aba:

### 3a · Contas de anúncios
- Clique na aba **Contas de anúncios**
- Marque **FE - LIMÃO** e **FS - LIMÃO**
- À direita, ligue a chave **Gerenciar conta de anúncios** (controle total)
- **Salvar alterações**

### 3b · Páginas
- Aba **Páginas**
- Marque **Fast Escova Limão** e **Fast Spa Limão**
- Ligue **Gerenciar página**
- **Salvar alterações**

### 3c · Contas do Instagram
- Aba **Contas do Instagram**
- Marque **fastescova.limao** e **fastspa.limao**
- Ligue **Gerenciar conta do Instagram**
- **Salvar alterações**

**Confira antes de sair:** a tela do `FAST Painel` deve listar **seis ativos**.
Se listar três, falta o Spa.

### Se o Spa não aparecer

O portfólio é outro. No topo da página do Business Manager tem um seletor com
o nome da empresa — troque para **Fast Spa 2026** e repita o passo 1 e o passo
3 lá dentro, **para o mesmo usuário do sistema**.

Se o `FAST Painel` não existir nesse portfólio, crie um com o mesmo nome. Dois
usuários do sistema com o mesmo nome em portfólios diferentes é normal e
funciona — o token do segundo cobre os ativos do segundo.

---

## PASSO 4 · Gerar o token

1. Botão **Gerar novo token**
2. **Aplicativo:** `FAST Limão · integrações`
3. **Validade do token:** escolha **Nunca expira** se aparecer essa opção
4. Marque estas **seis permissões** (tem uma caixa de busca — procure uma a uma):

```
ads_read
instagram_basic
instagram_manage_insights
pages_read_engagement
pages_show_list
business_management
```

5. **Gerar token**

**O token começa com `EAA`** e tem umas 200 letras.

⚠️ **Ele aparece uma vez só.** Fechou a janela, perdeu — não tem problema, é
só gerar outro.

---

## PASSO 5 · Guardar no GitHub

1. **https://github.com/rodsballa12-cell/fast-dashboard-limao/settings/secrets/actions**
2. Na linha **META_ACCESS_TOKEN**, clique no **lápis**
3. Apague o que está lá, cole o novo, **Update secret**

**Não cole em mais lugar nenhum** — nem em conversa, nem em arquivo, nem em
e-mail. Quem tem esse token move verba de anúncio nas duas contas.

---

## PASSO 6 · Testar na hora

1. **https://github.com/rodsballa12-cell/fast-dashboard-limao/actions**
2. Clique em **Refresh Midias Sociais (diario)** na lista da esquerda
3. Botão **Run workflow** → **Run workflow**
4. Espere ~3 minutos e recarregue

| o que aparecer | o que significa |
|---|---|
| ✅ verde **com commit novo** | funcionou nas duas unidades |
| ✅ verde **sem commit** | o early-exit achou que já rodou hoje — peça para eu forçar |
| ❌ vermelho | falta ativo no passo 3, ou permissão no passo 4 |

**Me avise quando rodar** — eu leio o log daqui e digo exatamente qual ativo
ou permissão ficou de fora, se for o caso.

---

## Ainda pendente: a chave secreta do aplicativo

Em 16/09 a chave secreta do `FAST Limão · integrações` apareceu numa conversa.
Se você ainda não trocou:

**https://developers.facebook.com/apps/964019103388501/settings/basic/**
→ *Chave Secreta do Aplicativo* → **Mostrar** → **Redefinir**

Isso **não derruba** o token do usuário do sistema — são coisas separadas.
E o nosso painel não usa a chave secreta em lugar nenhum.
