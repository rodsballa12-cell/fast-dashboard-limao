# Token da Meta · passo a passo

> **Interface em português de Portugal.** Os menus do Rodrigo dizem
> *Definições*, *Utilizadores*, *Portefólio de negócios* — não "Configurações",
> "Usuários", "Portfólio". Este documento usa os nomes que ele vê na tela.

## Por que estamos fazendo isto

O painel de mídia está cego desde **10/09**. Duas tentativas falharam:

| quando | o que foi feito | quanto durou |
|---|---|---|
| 10/09 | token de utilizador comum | morreu quando ele trocou a senha |
| 16/09 | token do Graph API Explorer | **1h20** — nasceu 09h40, morreu 11h00 |

O botão *Generate Access Token* do Explorer entrega token de **curta duração**:
uma a duas horas, arredondado para a hora cheia. Os "60 dias" só existem depois
de trocar por um de longa duração — passo que quase ninguém faz.

**O Utilizador do Sistema não tem senha para trocar nem sessão para expirar.**
É um "funcionário robô": não faz login, não tem senha, serve só para o painel
ler números.

**Pré-requisito, já resolvido em 18/09:** acesso **total** ao portefólio.
Com *Acesso parcial · Básico* o item nem aparece no menu.

---

## PASSO 1 · Abrir Utilizadores do sistema

Em **business.facebook.com**, na barra da esquerda:

**Utilizadores** → **Utilizadores do sistema**

*(É o item logo abaixo de "Pessoas". Se só aparecer "Pessoas", recarregue com
**Ctrl+F5** — permissão nova demora um minuto para a interface enxergar.)*

**Você deve ver:** uma lista provavelmente vazia e um botão **Adicionar**.

---

## PASSO 2 · Criar o robô

1. **Adicionar**
2. **Nome:** `FAST Painel`
3. **Função:** **Administrador**
   ⚠️ Não escolha "Funcionário" — funcionário não consegue gerar token com
   todas as permissões, e o erro só aparece no passo 4.
4. **Criar utilizador do sistema**

**Você deve ver:** `FAST Painel` na lista, com os botões **Adicionar ativos**
e **Gerar novo token**.

---

## PASSO 3 · Os seis ativos ← **é aqui que falha calado**

Com o `FAST Painel` selecionado, clique em **Adicionar ativos**.

Abre uma janela com **abas do lado esquerdo**. Você vai repetir isto **três
vezes**, uma por aba. Quem marca só a primeira sai achando que terminou, e o
token nasce funcionando pela metade.

### 3a · Contas de anúncios
- Marcar **FE - LIMÃO** e **FS - LIMÃO**
- Ligar a chave **Gerir conta de anúncios**
- **Guardar alterações**

### 3b · Páginas
- Marcar **Fast Escova Limão** e **Fast Spa Limão**
- Ligar **Gerir página**
- **Guardar alterações**

### 3c · Contas do Instagram
- Marcar **fastescova.limao** e **fastspa.limao**
- Ligar **Gerir conta do Instagram**
- **Guardar alterações**

### ✅ Confira antes de sair

A tela do `FAST Painel` deve listar **seis ativos**. Se listar três, falta o Spa.

### Se o Spa não aparecer

O Spa mora num portefólio separado, **Fast Spa 2026**. No topo da página há um
seletor com o nome da empresa atual (*Fast Escova Limão*) — troque para
**Fast Spa 2026** e repita os passos 1 a 3 lá dentro.

Se o `FAST Painel` não existir nesse portefólio, crie outro com o mesmo nome.
Dois utilizadores do sistema homônimos em portefólios diferentes é normal — mas
aí **serão dois tokens**, e o painel só aceita um. Nesse caso me avise: a saída
é partilhar os ativos do Spa com o portefólio da Escova, e eu te guio.

---

## PASSO 4 · Gerar o token

1. **Gerar novo token**
2. **Aplicativo:** `FAST Limão · integrações`
3. **Validade:** **Nunca expira**, se a opção aparecer
4. Marque as **seis permissões** (há uma caixa de busca — procure uma a uma):

```
ads_read
instagram_basic
instagram_manage_insights
pages_read_engagement
pages_show_list
business_management
```

5. **Gerar token**

**Confira:** começa com **`EAA`** e tem umas 200 letras. Se vier curto, com
números e uma barra `|`, é token de aplicativo — refaça.

⚠️ **Aparece uma vez só.** Fechou, perdeu — é só gerar outro, sem problema.

---

## PASSO 5 · Guardar no GitHub

1. **github.com/rodsballa12-cell/fast-dashboard-limao/settings/secrets/actions**
2. Linha **META_ACCESS_TOKEN** → ícone de **lápis**
3. Apagar o conteúdo, colar o novo, **Update secret**

**Só existem dois lugares legítimos para esse token:** a tela onde ele nasce e
este campo. Nunca em conversa, arquivo ou e-mail — quem o tem move verba de
anúncio nas duas contas.

---

## PASSO 6 · Testar

1. **github.com/rodsballa12-cell/fast-dashboard-limao/actions**
2. **Refresh Midias Sociais (diario)** na lista da esquerda
3. **Run workflow** → **Run workflow**
4. ~3 minutos

| resultado | significa |
|---|---|
| ✅ verde **com commit novo** | funcionou nas duas unidades |
| ✅ verde **sem commit** | o early-exit achou que já rodou hoje — me peça para forçar |
| ❌ vermelho | falta ativo (passo 3) ou permissão (passo 4) |

**Me avise quando rodar.** Eu leio o log daqui e digo exatamente qual ativo ou
permissão ficou de fora, se for o caso.

---

## Pendência separada · a chave secreta do aplicativo

Em 16/09 a chave secreta do `FAST Limão · integrações` apareceu numa conversa.
Se ainda não foi trocada:

**developers.facebook.com/apps/964019103388501/settings/basic/**
→ *Chave Secreta do Aplicativo* → **Mostrar** → **Redefinir**

Redefinir **não derruba** o token do utilizador do sistema — são coisas
separadas — e o painel não usa a chave secreta em lugar nenhum.
