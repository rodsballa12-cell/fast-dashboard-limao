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

  // Um aviso por sessao, visivel na tela. Console sozinho nao serve: quem le o
  // painel no celular nunca abre console.
  var jaAvisou = false;
  window.fastCofreIncompleto = false;
  function avisarCofreAberto(arquivo) {
    window.fastCofreIncompleto = true;
    console.warn('[cofre] ' + arquivo + ' lido SEM criptografia: o .enc nao existe. Rode `python scripts/cofre.py migrar` no PC.');
    if (jaAvisou) return;
    jaAvisou = true;
    function montar() {
      var b = document.createElement('div');
      b.setAttribute('style', 'position:fixed;left:0;right:0;top:0;z-index:2147483646;background:#b45309;color:#fff;font:600 12.5px system-ui,-apple-system,sans-serif;padding:8px 14px;text-align:center;box-shadow:0 2px 10px rgba(0,0,0,.3)');
      b.textContent = '\u26A0\uFE0F Cofre nao fechado \u2014 o painel esta lendo os dados sem criptografia. Rode a migracao no PC: python scripts/cofre.py migrar';
      b.addEventListener('click', function () { b.remove(); });
      document.body.appendChild(b);
    }
    if (document.body) montar(); else document.addEventListener('DOMContentLoaded', montar);
  }

  window.fetch = function (entrada, init) {
    var url = typeof entrada === 'string' ? entrada : (entrada && entrada.url) || '';
    var u;
    try { u = new URL(url, location.href); } catch (e) { return origFetch(entrada, init); }
    var m = u.origin === location.origin && u.pathname.match(/\/(data\/.+)$/);
    if (!m || !SENSIVEIS.test(m[1])) return origFetch(entrada, init);

    return origFetch(u.pathname + '.enc' + u.search, init).then(function (r) {
      // Cofre AINDA NAO FECHADO: o .enc nao existe, mas o arquivo em texto
      // puro existe. Em 22/10/2026 o codigo do cofre entrou no repositorio
      // (commit abba1e8) sem que a migracao `cofre.py migrar` tivesse rodado:
      // nenhum .enc foi gerado e nenhum .json foi tirado do git. Resultado --
      // toda leitura sensivel virava 404 e o painel ficava fora do ar, com os
      // dados intactos no repositorio ao lado. A fechadura entrou antes do
      // conteudo do cofre.
      //
      // Entao: .enc ausente cai de volta no arquivo original, e AVISA. Nao e
      // brecha -- enquanto o .enc nao existe o texto puro esta publico de
      // qualquer jeito, e assim que a migracao rodar o original deixa de ser
      // servido e este caminho morre sozinho. O que nao se admite e cair
      // calado: bloco que some tem de doer.
      if (r.status === 404) {
        return origFetch(entrada, init).then(function (claro) {
          if (claro.ok) avisarCofreAberto(m[1]);
          return claro;
        });
      }
      if (!r.ok) return r;
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
