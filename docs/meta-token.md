# Renovar o META_ACCESS_TOKEN

> **⚠️ O caminho rápido pelo Graph API Explorer NÃO serve.** Em 16/09/2026 o
> token gerado por ali durou **1h20**: nasceu às 09h40, a Meta expirou às 11h00
> em ponto, e o painel ficou zerado por mais um dia inteiro. O botão
> *Generate Access Token* do Explorer entrega um token **de curta duração** —
> uma a duas horas, arredondado para a hora cheia. Os "60 dias" só existem
> depois de **trocar** esse token por um de longa duração, que é um passo a
> mais que quase ninguém lembra de fazer.
>
> **Use o Usuário do Sistema abaixo.** Não é o caminho longo — é o único.


**Por que ele morreu:** o token em uso era um *token de usuário*, amarrado à
conta pessoal do Rodrigo no Facebook. **Trocar a senha invalida esse tipo de
token na hora** — foi o que a própria Meta respondeu:

> *"The session has been invalidated because the user changed their password."*

Gerar outro token de usuário resolve hoje e quebra de novo na próxima troca de
senha, ou em 60 dias, o que vier antes.

**A correção definitiva é um Usuário do Sistema** (*System User*): um "robô" do
Business Manager cujo token **não expira e não morre com troca de senha.**
Quinze minutos, uma vez na vida.

---

## O que o token precisa alcançar

As duas unidades usam o mesmo token:

| | Escova | Spa |
|---|---|---|
| Conta de anúncios | `act_1310973560614050` · FE - LIMÃO | `act_1381925294040065` · FS - LIMÃO |
| Instagram | `17841439811993335` · fastescova.limao | `17841441683971969` · fastspa.limao |
| Página do Facebook | `1177609485429072` | `871300609405142` |

---

## Passo 1 · Criar o usuário do sistema

1. Abra **business.facebook.com** e entre em **Configurações do negócio**
   (o ícone de engrenagem)
2. No menu da esquerda: **Usuários → Usuários do sistema**
3. **Adicionar** → nome `FAST Painel` → função **Administrador** → Criar

## Passo 2 · Dar acesso aos ativos

Ainda na tela do usuário do sistema, clique em **Adicionar ativos** e marque,
com **Controle total** em cada um:

- **Contas de anúncios** — FE - LIMÃO e FS - LIMÃO
- **Páginas** — Fast Escova Limão e Fast Spa Limão
- **Contas do Instagram** — fastescova.limao e fastspa.limao

> Se o Spa estiver num portfólio separado (`Fast Spa 2026`), repita o
> Passo 2 lá dentro, para o mesmo usuário do sistema.

## Passo 3 · Gerar o token

1. **Gerar novo token**
2. Escolha o **aplicativo** (o mesmo que já usava — se houver só um, é ele)
3. Marque estas permissões:
   - `ads_read`
   - `instagram_basic`
   - `instagram_manage_insights`
   - `pages_read_engagement`
   - `pages_show_list`
   - `business_management`
4. **Gerar token** → **copie agora**

**O token aparece uma vez só.** Fechou a janela, perdeu — é só gerar outro.

## Passo 4 · Guardar no GitHub

1. Abra
   `https://github.com/rodsballa12-cell/fast-dashboard-limao/settings/secrets/actions`
2. Na linha **META_ACCESS_TOKEN**, clique no lápis
3. Cole o token novo → **Update secret**

## Passo 5 · Testar na hora, sem esperar o dia seguinte

1. Vá em **Actions** → **Refresh Midias Sociais (diario)**
2. **Run workflow** → **Run workflow**
3. Espere ~2 minutos e abra a execução

**Verde com commit novo** = funcionou.
**Vermelho, ou verde sem commit** = o token não alcança algum ativo; quase
sempre é o Passo 2 faltando numa das seis linhas.

---

## Onde o token NÃO deve ser colado

Só existem dois lugares legítimos: a tela do Business Manager onde ele nasce, e
o campo de secret do GitHub. **Não cole em conversa, arquivo, planilha ou
e-mail** — quem tem o token move verba de anúncio nas duas contas.

Se ele vazar: Business Manager → o usuário do sistema → **Revogar token**, e
gere outro. Leva um minuto e invalida o antigo imediatamente.
