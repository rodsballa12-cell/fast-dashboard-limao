/* Cofre da RECEPCAO (12/11/2026).
 * A pagina recepcao.html mostra so a aba Clientes. Os dados ficam no
 * repositorio publico apenas CRIPTOGRAFADOS em data/recepcao_clientes.json.enc,
 * com uma senha PROPRIA da recepcao (FAST_RECEPCAO_SENHA) — diferente da senha
 * do Ritmo Fast completo, para quem so atende nunca abrir o financeiro.
 * Algoritmo: igual ao cofre-painel.js (AES-256-GCM + PBKDF2-SHA256).
 */
(function () {
  var ARQ = 'data/recepcao_clientes.json.enc';
  var CHAVE_LS = 'fast_recepcao_senha';
  var origFetch = window.fetch.bind(window);
  var cache = null, senhaPromessa = null;

  function lerSenha() { try { return localStorage.getItem(CHAVE_LS); } catch (e) { return null; } }
  function gravarSenha(s) { try { localStorage.setItem(CHAVE_LS, s); } catch (e) {} }
  function esquecerSenha() { try { localStorage.removeItem(CHAVE_LS); } catch (e) {} }
  window.fastRecepcaoSair = function () { esquecerSenha(); location.reload(); };

  function pedirSenha(msg) {
    return new Promise(function (resolve) {
      function montar() {
        var fundo = document.createElement('div');
        fundo.setAttribute('style', 'position:fixed;inset:0;z-index:2147483647;background:rgba(11,11,15,.85);display:flex;align-items:center;justify-content:center;padding:16px;font-family:system-ui,-apple-system,sans-serif');
        fundo.innerHTML =
          '<form style="background:#fff;color:#111;border-radius:14px;padding:22px;width:100%;max-width:340px;box-shadow:0 10px 40px rgba(0,0,0,.4)">' +
          '<div style="font-size:18px;font-weight:700;margin-bottom:6px">🔒 Atendimento Fast</div>' +
          '<div style="font-size:13px;color:#555;margin-bottom:14px">' + (msg || 'Digite a senha da recepção. Ela fica salva só neste aparelho.') + '</div>' +
          '<input type="password" autocomplete="current-password" required style="width:100%;box-sizing:border-box;font-size:16px;padding:10px 12px;border:1px solid #ccc;border-radius:8px;margin-bottom:12px">' +
          '<button type="submit" style="width:100%;font-size:15px;font-weight:600;padding:10px;border:0;border-radius:8px;background:#F5B800;color:#111">Entrar</button>' +
          '</form>';
        document.body.appendChild(fundo);
        var campo = fundo.querySelector('input');
        setTimeout(function () { campo.focus(); }, 50);
        fundo.querySelector('form').addEventListener('submit', function (ev) {
          ev.preventDefault();
          var v = campo.value;
          fundo.remove();
          resolve(v);
        });
      }
      if (document.body) montar(); else document.addEventListener('DOMContentLoaded', montar);
    });
  }

  function obterSenha() {
    var s = lerSenha();
    if (s) return Promise.resolve(s);
    if (!senhaPromessa) senhaPromessa = pedirSenha();
    return senhaPromessa;
  }

  function b64(s) { return Uint8Array.from(atob(s), function (c) { return c.charCodeAt(0); }); }

  function decifrar(env, senha) {
    return crypto.subtle.importKey('raw', new TextEncoder().encode(senha), 'PBKDF2', false, ['deriveKey'])
      .then(function (base) {
        return crypto.subtle.deriveKey({ name: 'PBKDF2', salt: b64(env.salt), iterations: env.iter, hash: 'SHA-256' },
          base, { name: 'AES-GCM', length: 256 }, false, ['decrypt']);
      })
      .then(function (k) { return crypto.subtle.decrypt({ name: 'AES-GCM', iv: b64(env.iv) }, k, b64(env.ct)); })
      .then(function (buf) { return JSON.parse(new TextDecoder().decode(buf)); });
  }

  // Abre o cofre uma vez e guarda o conteudo (as duas unidades vem juntas).
  function abrir() {
    if (cache) return cache;
    cache = origFetch(ARQ + '?_=' + Date.now(), { cache: 'no-store' }).then(function (r) {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    }).then(function (env) {
      function tentar(n) {
        return obterSenha().then(function (senha) {
          var usada = senhaPromessa;
          return decifrar(env, senha).then(function (obj) {
            gravarSenha(senha);
            return obj;
          }, function () {
            esquecerSenha();
            if (n >= 4) throw new Error('Senha incorreta');
            if (senhaPromessa === usada) senhaPromessa = pedirSenha('Senha incorreta. Tente de novo.');
            return tentar(n + 1);
          });
        });
      }
      return tentar(0);
    });
    cache.catch(function () { cache = null; });
    // Depois que a senha entrou, abre tambem o saldo de pacotes (mesma senha).
    cache.then(function () { carregarPacotes(); });
    return cache;
  }

  // Saldo de pacotes por cliente: arquivo proprio, atualizado a mao a partir
  // do relatorio do Trinks (a API nao entrega o saldo). Se nao existir, a
  // secao simplesmente nao aparece.
  var pacotesIniciado = false;
  function carregarPacotes() {
    if (pacotesIniciado) return;
    pacotesIniciado = true;
    origFetch('data/recepcao_pacotes.json.enc?_=' + Date.now(), { cache: 'no-store' })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (env) { return env ? decifrar(env, lerSenha()) : null; })
      .then(function (obj) {
        window.fastRecepcaoPacotes = obj;
        document.dispatchEvent(new CustomEvent('recepcao-pacotes', { detail: obj }));
      })
      .catch(function (e) { console.warn('[recepcao] pacotes indisponiveis:', e); });
  }

  // A pagina pede data/dashboard_data.json (Escova) e data/spa/dashboard_data.json.
  // Entrega o recorte de clientes de cada uma. Dado financeiro vira 404.
  var UNIDADE = { 'data/dashboard_data.json': 'escova', 'data/spa/dashboard_data.json': 'spa' };

  window.fetch = function (entrada, init) {
    var url = typeof entrada === 'string' ? entrada : (entrada && entrada.url) || '';
    var u;
    try { u = new URL(url, location.href); } catch (e) { return origFetch(entrada, init); }
    var m = u.origin === location.origin && u.pathname.match(/\/(data\/.+)$/);
    if (!m) return origFetch(entrada, init);
    if (Object.prototype.hasOwnProperty.call(UNIDADE, m[1])) {
      return abrir().then(function (obj) {
        return new Response(JSON.stringify(obj[UNIDADE[m[1]]]), { status: 200, headers: { 'Content-Type': 'application/json' } });
      }, function (e) {
        return new Response('', { status: 401, statusText: String(e.message || e) });
      });
    }
    if (/^data\/(financeiro|consolidado\/|spa\/financeiro|wa_|stone|comissoes|trinks_)/.test(m[1])) {
      return Promise.resolve(new Response('', { status: 404, statusText: 'Not Found' }));
    }
    return origFetch(entrada, init);
  };
})();
