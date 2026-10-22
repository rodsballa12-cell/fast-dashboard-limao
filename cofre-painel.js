/* Cofre do painel FAST (21/10/2026).
 * Os arquivos com dado de cliente e financeiro ficam no repositório público
 * apenas CRIPTOGRAFADOS (.enc). Este script intercepta o fetch do painel:
 * quando o painel pede data/...json sensível, busca o .enc, pede a senha
 * (uma vez por aparelho) e devolve o JSON aberto, como se nada tivesse mudado.
 * Formato e algoritmo: ver scripts/cofre.py (AES-256-GCM + PBKDF2-SHA256).
 */
(function () {
  var SENSIVEIS = /^data\/(?:(?:spa|consolidado)\/)?(?:dashboard_data|financeiro)\.json$|^data\/wa_fila\.json$/;
  var CHAVE_LS = 'fast_painel_senha';
  var origFetch = window.fetch.bind(window);
  var senhaPromessa = null;

  function lerSenha() { try { return localStorage.getItem(CHAVE_LS); } catch (e) { return null; } }
  function gravarSenha(s) { try { localStorage.setItem(CHAVE_LS, s); } catch (e) {} }
  function esquecerSenha() { try { localStorage.removeItem(CHAVE_LS); } catch (e) {} }
  window.fastCofreSair = function () { esquecerSenha(); location.reload(); };

  function pedirSenha(msg) {
    return new Promise(function (resolve) {
      function montar() {
        var fundo = document.createElement('div');
        fundo.setAttribute('style', 'position:fixed;inset:0;z-index:2147483647;background:rgba(11,11,15,.85);display:flex;align-items:center;justify-content:center;padding:16px;font-family:system-ui,-apple-system,sans-serif');
        fundo.innerHTML =
          '<form style="background:#fff;color:#111;border-radius:14px;padding:22px;width:100%;max-width:340px;box-shadow:0 10px 40px rgba(0,0,0,.4)">' +
          '<div style="font-size:18px;font-weight:700;margin-bottom:6px">🔒 Painel FAST</div>' +
          '<div style="font-size:13px;color:#555;margin-bottom:14px">' + (msg || 'Digite a senha do painel. Ela fica salva só neste aparelho.') + '</div>' +
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
      .then(function (buf) { return new TextDecoder().decode(buf); });
  }

  window.fetch = function (entrada, init) {
    var url = typeof entrada === 'string' ? entrada : (entrada && entrada.url) || '';
    var u;
    try { u = new URL(url, location.href); } catch (e) { return origFetch(entrada, init); }
    var m = u.origin === location.origin && u.pathname.match(/\/(data\/.+)$/);
    if (!m || !SENSIVEIS.test(m[1])) return origFetch(entrada, init);

    return origFetch(u.pathname + '.enc' + u.search, init).then(function (r) {
      if (!r.ok) return r;  // 404 continua 404: o fallback de unidade do painel segue funcionando
      return r.json().then(function (env) {
        function tentar(n) {
          return obterSenha().then(function (senha) {
            var usada = senhaPromessa;
            return decifrar(env, senha).then(function (txt) {
              gravarSenha(senha);
              return new Response(txt, { status: 200, headers: { 'Content-Type': 'application/json' } });
            }, function () {
              esquecerSenha();
              if (n >= 4) return new Response('', { status: 401, statusText: 'Senha incorreta' });
              if (senhaPromessa === usada) senhaPromessa = pedirSenha('Senha incorreta. Tente de novo.');
              return tentar(n + 1);
            });
          });
        }
        return tentar(0);
      });
    });
  };
})();
