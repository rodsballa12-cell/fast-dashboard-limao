# Token da Meta · roteiro clique a clique

Para o Rodrigo, que não é programador. Cada linha é um clique ou uma
conferência. **Se a sua tela não for o que está escrito, pare e me mande um
print** — é melhor que seguir adivinhando.

**Tempo total:** uns 20 minutos. **Uma vez na vida.**

---

## O que estamos consertando

O painel de mídia está cego desde 10/09. Tentamos duas vezes e as duas
morreram: um token acabou quando você trocou a senha, o outro durou 1h20.

Agora vamos criar um **utilizador do sistema** — um "funcionário robô" que não
faz login, não tem senha e não expira. É a única forma que não quebra.

**Você vai precisar de duas abas do navegador abertas:**
- **business.facebook.com** (onde você já está)
- **github.com** (para o passo E)

---

# PARTE A · Ligar o app ao portefólio

*Por que: na hora de gerar o token a Meta pergunta "para qual aplicativo?".
Você já tem um — o `FAST Limão · integrações` — mas o Business Manager ainda
não o conhece. Por isso apareceu a mensagem pedindo para criar um app.*

### A1
Na barra cinza da esquerda, desça até o grupo **Contas**.
É o mesmo grupo onde estão *Páginas* e *Contas de anúncios*.

### A2
Clique em **Apps**.

**Você deve ver:** uma página com o título *Apps*, provavelmente vazia, com um
botão azul no canto.

### A3
Clique em **Adicionar**.

**Abre um menu com duas ou três opções.** Escolha **Adicionar uma app**.

⚠️ **Não escolha "Criar nova app".** Você não quer um app novo — quer usar o
que já existe.

### A4
Vai pedir o **número de identificação do app**. Cole exatamente isto:

```
964019103388501
```

### A5
Clique em **Adicionar app** e confirme.

### ✅ Confira
Na lista de Apps deve aparecer **`FAST Limão · integrações`**.

### ❌ Se der erro
Provavelmente sua conta não é administradora do app. Abra numa aba nova:

**developers.facebook.com/apps/964019103388501/roles/**

Você precisa aparecer ali na lista como **Administrador**. Se não aparecer,
me avise — a saída é outra.

---

# PARTE B · Criar o robô

### B1
Volte para a barra da esquerda, grupo **Utilizadores**.

### B2
Clique em **Utilizadores do sistema**.

**Você deve ver:** uma lista vazia e um botão **Adicionar**.

### B3
Clique em **Adicionar**.

### B4
Preencha:
- **Nome:** `FAST Painel`
- **Função:** escolha **Administrador**

⚠️ **Não escolha "Funcionário".** Funcionário não consegue gerar token com
todas as permissões, e você só descobre isso lá na PARTE D — depois de ter
feito tudo.

### B5
Aceite os termos se aparecerem e clique em **Criar utilizador do sistema**.

### ✅ Confira
`FAST Painel` aparece na lista. Ao clicar nele, surgem dois botões:
**Adicionar ativos** e **Gerar novo token**.

---

# PARTE C · Dar os seis acessos ← **a parte que falha calada**

*Por que importa: se faltar um ativo, o token nasce funcionando pela metade.
Nada dá erro. Você só descobre dias depois, quando o painel do Spa estiver
vazio e ninguém souber por quê.*

### C1
Com o `FAST Painel` selecionado, clique em **Adicionar ativos**.

**Abre uma janela.** Do lado esquerdo dela há **abas** — tipo *Páginas*,
*Contas de anúncios*, *Contas do Instagram*, e outras.

**Você vai fazer a mesma coisa três vezes, numa aba de cada vez.**

---

### C2 · Aba "Contas de anúncios"

1. Clique na aba **Contas de anúncios**
2. No meio da tela aparece a lista de contas. Marque a caixinha de:
   - **FE - LIMÃO**
   - **FS - LIMÃO**
3. Do lado **direito** aparece um painel de permissões. Ligue a chave
   **Gerir conta de anúncios** (é a permissão total)
4. Clique em **Guardar alterações**

---

### C3 · Aba "Páginas"

1. Clique na aba **Páginas**
2. Marque:
   - **Fast Escova Limão**
   - **Fast Spa Limão**
3. Ligue a chave **Gerir página**
4. **Guardar alterações**

---

### C4 · Aba "Contas do Instagram"

1. Clique na aba **Contas do Instagram**
2. Marque:
   - **fastescova.limao**
   - **fastspa.limao**
3. Ligue a chave **Gerir conta do Instagram**
4. **Guardar alterações**

---

### ✅ Confira — não pule esta parte

Feche a janela. Na tela do `FAST Painel` deve haver **SEIS ativos** listados:
duas contas de anúncios, duas páginas, duas contas do Instagram.

**Conte.** Se forem três, faltou o Spa.

### ❌ Se só aparecerem os três da Escova

O Spa está guardado num portefólio separado chamado **Fast Spa 2026**.

No **alto da página** há o nome da empresa atual — *Fast Escova Limão*, com o
logotipo amarelo ao lado. Clique ali: abre um seletor com os seus portefólios.

**Antes de trocar, me mande um print dessa lista.** Trocar de portefólio cria
um segundo utilizador do sistema, e aí serão **dois tokens** — mas o painel só
aceita um. Existe uma saída melhor (partilhar os ativos do Spa com o portefólio
da Escova) e eu te guio nela.

---

# PARTE D · Gerar o token

### D1
Na tela do `FAST Painel`, clique em **Gerar novo token**.

### D2
**Aplicativo:** escolha **`FAST Limão · integrações`** no menu suspenso.

*(Se não aparecer, a PARTE A não funcionou — volte lá.)*

### D3
**Validade do token:** se aparecer essa opção, escolha **Nunca expira**.

### D4
Agora a lista de permissões. **São seis**, e há uma caixa de busca no topo.
Digite uma, marque, apague, digite a próxima:

```
ads_read
instagram_basic
instagram_manage_insights
pages_read_engagement
pages_show_list
business_management
```

**Confira que as seis estão marcadas antes de continuar.**

### D5
Clique em **Gerar token**.

### ✅ Confira
Aparece uma caixa com o token. Ele:
- **começa com `EAA`**
- tem umas **200 letras** — é bem comprido

❌ Se vier curto, com números e uma **barra `|`** no meio, é token de
aplicativo — refaça a partir de D1.

### D6
Clique no **botão de copiar** ao lado da caixa.

⚠️ **O token aparece uma vez só.** Se você fechar a janela sem copiar, não tem
como recuperar — mas não é problema: é só clicar em *Gerar novo token* e fazer
de novo.

**Não feche esta aba ainda.**

---

# PARTE E · Guardar no GitHub

### E1
Na outra aba do navegador, abra:

**github.com/rodsballa12-cell/fast-dashboard-limao/settings/secrets/actions**

### E2
Você vai ver uma lista de nomes em maiúsculas. Procure **`META_ACCESS_TOKEN`**.

### E3
Na linha dele, à direita, clique no **ícone de lápis** ✏️.

### E4
Abre uma caixa de texto com o token antigo (aparece como pontinhos ou vazia).

1. Clique dentro da caixa
2. **Ctrl+A** para selecionar tudo
3. **Delete** para apagar
4. **Ctrl+V** para colar o novo

### E5
Clique no botão verde **Update secret**.

### ✅ Confira
A linha do `META_ACCESS_TOKEN` deve mostrar *Updated now* ou *há poucos
segundos*.

---

## ⚠️ Onde esse token NUNCA pode ser colado

Só existem **dois lugares legítimos**: a tela onde ele nasceu e essa caixa do
GitHub.

**Não cole em conversa, arquivo, planilha, e-mail ou WhatsApp** — nem para mim.
Quem tem esse token consegue mexer na verba de anúncio das duas contas.

---

# PARTE F · Testar

### F1
Ainda no GitHub, abra:

**github.com/rodsballa12-cell/fast-dashboard-limao/actions**

### F2
Na coluna da **esquerda** há uma lista de rotinas. Clique em
**Refresh Midias Sociais (diario)**.

### F3
À **direita**, aparece um botão cinza **Run workflow**. Clique nele.

Abre uma caixinha com outro botão verde **Run workflow**. Clique também.

### F4
Espere uns **3 minutos** e recarregue a página (**F5**).

### ✅ O que significa cada resultado

| você vê | significa |
|---|---|
| ✅ bolinha **verde** | deu certo — me avise que eu confiro o dado |
| ❌ bolinha **vermelha** | faltou ativo na PARTE C ou permissão na D |
| 🟡 bolinha **amarela** | ainda rodando, espere mais um minuto |

**Me avise de qualquer jeito.** Eu leio o log daqui e digo exatamente o que
faltou — você não precisa caçar.

---

## Depois, com calma

**A chave secreta do app.** Em 16/09 ela apareceu numa conversa. Para trocar:

**developers.facebook.com/apps/964019103388501/settings/basic/**
→ procure *Chave Secreta do Aplicativo* → **Mostrar** → **Redefinir**

Isso **não derruba** o token que você acabou de criar — são coisas separadas.

**Quem tem acesso ao seu negócio.** Seis pessoas aparecem em *Utilizadores →
Pessoas*, pelo menos duas com *Acesso total · Tudo*. Vale uma revisão de quem
precisa de quê.
