# Regras de captura de chats no claude.ai via browser

Origem: log de incidentes em
`Cerebro_Claude/03-APRENDIZADOS/Erros-e-Licoes/Captura-de-Chats-Online-Claude-ai.md`,
destilado em set/2026.

Aplicável a qualquer automação que leia claude.ai via extensão claude-in-chrome.

---

## Regra de 11/09 — nunca `navigate` para `/recents` ou `/chat/<id>`

O servidor negocia `Content-Encoding: zstd` nessas rotas. Quando a aba
reaproveitada ou o handler de navegação erra a descompressão, a página
devolve `HTTP 200` com bytes ilegíveis — indistinguível de "página vazia"
para a ferramenta.

**Sequência correta:**

1. Abrir **aba nova** (nunca reaproveitar aba de execução anterior).
2. `navigate` para **`https://claude.ai/new`** — só esta rota é confiável.
3. `find "recent conversation links in sidebar"` — devolve só os `href` e
   títulos, sem trazer a árvore inteira da página.
4. Para abrir conversa: `left_click` no `ref` → `get_page_text`.
   **Nunca `navigate` diretamente para `/chat/<id>`.**
5. A data fica no rodapé da conversa, não na lista — a sidebar não traz
   data, então não filtre por data antes de abrir.

A diferença entre `navigate` e clique: `navigate` faz page load (negocia
encoding de novo e pode errar); clique faz roteamento client-side dentro
do SPA já carregado (busca JSON via `fetch`, que descomprime corretamente).

---

## Regra de 14/09 — distinguir "não logado" de "sem canal"

Dois estados diferentes produzem o mesmo texto no relatório de falha:

| Estado | Sintoma | Ação corretiva |
|---|---|---|
| Navegador conectado, sessão expirada | `list_connected_browsers` retorna IDs, mas navegar para claude.ai pede login | Fazer login |
| Extensão desconectada / sem permissão | `list_connected_browsers` retorna `[]` | Reconectar a extensão claude-in-chrome |

"Navegador não logado" e "nenhum canal de navegador disponível" pedem
ações opostas — escrever a mesma linha de log para os dois é o defeito.

O SKILL que usa este canal deve separar os dois rótulos. Enquanto não
separar, toda execução que falha vai gerar diagnóstico errado.

---

## Armadilha: ausência de dado ≠ ausência de acesso ao dado

Canal que devolve erro é honesto — a rotina registra falha e o operador
sabe que há buraco. Canal que devolve `HTTP 200` com lixo parece "rodou
certo" — a ausência de dado e a ausência de acesso ao dado produzem o
mesmo relatório verde.

Requer uma segunda rota para desmentir. Sem ela, a leitura ingênua está
errada e parece certa.
