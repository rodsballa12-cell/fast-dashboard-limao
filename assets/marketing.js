/* Aba Marketing — lê data/marketing_data.json e renderiza dentro de #mk-app.
   Autocontido de propósito: o index.html é regenerado pelo publish_pages.py, então
   este módulo não depende de nenhum helper definido lá dentro. */
(function () {
  'use strict';

  var FONTE = 'data/marketing_data.json';
  var CANAIS = { instagram: 'Instagram', facebook: 'Facebook', gmn: 'Google' };
  var DOW = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb'];
  var estado = { dados: null, filtro: 'todos' };

  // ---------- helpers ----------
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function num(v) { return (v || 0).toLocaleString('pt-BR'); }
  function aviso(msg, erro) {
    if (typeof window.toast === 'function') { window.toast(msg, !!erro); }
  }
  function hojeISO() {
    var d = new Date();
    return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' +
      String(d.getDate()).padStart(2, '0');
  }
  function dataBR(iso) {
    var p = String(iso || '').slice(0, 10).split('-');
    if (p.length !== 3) return iso || '';
    return p[2] + '/' + p[1];
  }
  function dowDe(iso) {
    var p = String(iso || '').slice(0, 10).split('-');
    if (p.length !== 3) return '';
    return DOW[new Date(+p[0], +p[1] - 1, +p[2]).getDay()];
  }
  function estrelas(n) {
    n = Math.max(0, Math.min(5, n || 0));
    return '★'.repeat(n) + '☆'.repeat(5 - n);
  }
  function kpi(cls, label, valor, rodape) {
    return '<div class="kpi ' + cls + '"><div class="label">' + esc(label) + '</div>' +
      '<div class="value accent">' + esc(valor) + '</div>' +
      '<div class="foot">' + (rodape || '') + '</div></div>';
  }
  function card(titulo, cap, corpo) {
    return '<div class="card"><h2>' + esc(titulo) + '</h2>' +
      '<div class="cap">' + esc(cap) + '</div>' + corpo + '</div>';
  }

  // ---------- blocos ----------
  function conexoes(d) {
    var g = d.gmn || {}, m = d.meta || {};
    function chip(ok, rotulo, motivo) {
      return '<span class="chip ' + (ok ? 'on' : 'off') + '" title="' + esc(motivo || '') + '">' +
        '<span class="dot"></span> ' + esc(rotulo) + ' · ' + (ok ? 'conectado' : 'não conectado') +
        '</span>';
    }
    return '<div class="mk-conn">' +
      chip(g.conectado, 'Google Meu Negócio', g.motivo) +
      chip(m.conectado, 'Instagram', m.motivo) +
      chip(!!(m.facebook && m.facebook.nome), 'Facebook', (m.facebook || {}).motivo) +
      chip((d.conteudo_sugerido || []).length > 0, 'Claude · pauta',
        d.motivo_conteudo || 'rode marketing_refresh.py --conteudo') +
      '</div>';
  }

  function kpis(d) {
    var r = d.resumo || {};
    var g = d.gmn || {}, ins = g.insights || {};
    var ig = (d.meta || {}).instagram || {};
    return '<div class="kpi-grid">' +
      kpi('', 'Nota Google', r.nota_google ? r.nota_google.toFixed(1) : '—',
        num(r.avaliacoes_total) + ' avaliações · <strong class="' +
        (r.avaliacoes_sem_resposta ? 'dn' : 'up') + '">' + num(r.avaliacoes_sem_resposta) +
        '</strong> sem resposta') +
      kpi('k2', 'Seguidores Instagram', num(ig.seguidores || 0),
        'alcance 28d: ' + num((ig.insights || {}).reach || 0)) +
      kpi('k3', 'Ficha do Google · 30d', num(ins.impressoes || 0) + ' views',
        num(ins.rotas || 0) + ' rotas · ' + num(ins.ligacoes || 0) + ' ligações') +
      kpi('k4', 'Pauta', num(r.posts_pendentes || 0) + ' pendentes',
        num(r.posts_agendados || 0) + ' agendados' +
        (r.posts_atrasados ? ' · <strong class="dn">' + num(r.posts_atrasados) + ' atrasados</strong>' : '')) +
      '</div>';
  }

  function postHTML(p, opts) {
    opts = opts || {};
    var canal = p.canal || 'instagram';
    var status = p.status || 'ideia';
    var hj = hojeISO();
    var atrasado = (status === 'aprovado' || status === 'agendado') && p.data && p.data < hj;
    var tags = (p.hashtags || []).join(' ');
    var texto = (p.legenda || '') + (tags ? '\n\n' + tags : '');

    var h = '<div class="mk-post ' + esc(canal) + '">' +
      '<div class="mk-head">' +
      '<span class="mk-badge canal-' + esc(canal) + '">' + esc(CANAIS[canal] || canal) + '</span>' +
      '<span class="mk-badge st-' + esc(atrasado ? 'atrasado' : status) + '">' +
      esc(atrasado ? 'atrasado' : status) + '</span>' +
      '<span class="mk-titulo">' + esc(p.titulo || '(sem título)') + '</span>' +
      (opts.mostrarData && p.data ? '<span class="quando" style="font-size:11px;color:var(--ink-3)">' +
        esc(dataBR(p.data)) + '</span>' : '') +
      '</div>';
    if (p.legenda) h += '<div class="mk-legenda">' + esc(p.legenda) + '</div>';
    if (tags) h += '<div class="mk-tags">' + esc(tags) + '</div>';
    if (p.cta) h += '<div class="mk-tags"><strong>CTA:</strong> ' + esc(p.cta) + '</div>';
    if (p.porque) h += '<div class="mk-porque">' + esc(p.porque) + '</div>';
    h += '<div class="mk-acoes">' +
      '<button class="mk-btn" data-copiar="' + esc(texto) + '">📋 Copiar legenda</button>' +
      (p.url_publicado ? '<a class="mk-btn" href="' + esc(p.url_publicado) + '" target="_blank" rel="noopener">abrir</a>' : '') +
      '</div></div>';
    return h;
  }

  function calendario(d) {
    var itens = (d.calendario || []).slice();
    if (estado.filtro !== 'todos') {
      itens = itens.filter(function (i) { return i.canal === estado.filtro; });
    }
    var hj = hojeISO();
    var porDia = {};
    itens.forEach(function (i) {
      var k = (i.data || '').slice(0, 10) || 'sem-data';
      (porDia[k] = porDia[k] || []).push(i);
    });

    // 14 dias a partir de hoje, mais qualquer dia passado que ainda tenha pendência
    var dias = [];
    var base = new Date();
    for (var k = 0; k < 14; k++) {
      var dt = new Date(base.getFullYear(), base.getMonth(), base.getDate() + k);
      dias.push(dt.getFullYear() + '-' + String(dt.getMonth() + 1).padStart(2, '0') + '-' +
        String(dt.getDate()).padStart(2, '0'));
    }
    Object.keys(porDia).forEach(function (k) {
      if (k < hj && k !== 'sem-data' && dias.indexOf(k) < 0) dias.unshift(k);
    });
    dias.sort();

    var filtros = ['todos', 'instagram', 'facebook', 'gmn'].map(function (f) {
      return '<button class="mk-filtro" data-filtro="' + f + '" aria-pressed="' +
        (estado.filtro === f ? 'true' : 'false') + '">' +
        (f === 'todos' ? 'Todos os canais' : CANAIS[f]) + '</button>';
    }).join('');

    // Dias livres em sequência viram uma linha só — 14 linhas de "nada programado"
    // não informam nada e afogam os dias que têm publicação.
    function linhaDia(dia, lista) {
      return '<div class="mk-dia' + (dia === hj ? ' hoje' : '') + '">' +
        '<div class="mk-data"><span class="dow">' + esc(dowDe(dia)) +
        (dia === hj ? ' · hoje' : '') + '</span>' + esc(dataBR(dia)) + '</div>' +
        '<div class="mk-itens">' +
        (lista.length ? lista.map(function (p) { return postHTML(p, {}); }).join('')
          : '<div class="mk-vazio">nada programado</div>') +
        '</div></div>';
    }
    function linhaLivre(inicio, fim, n) {
      return '<div class="mk-dia livre"><div class="mk-data">' +
        '<span class="dow">livres</span>' + esc(dataBR(inicio)) +
        (n > 1 ? '–' + esc(dataBR(fim)) : '') + '</div>' +
        '<div class="mk-itens"><div class="mk-vazio">' + n +
        (n > 1 ? ' dias sem nada programado' : ' dia sem nada programado') +
        '</div></div></div>';
    }

    var linhas = [];
    var livres = [];
    function drenar() {
      if (!livres.length) return;
      linhas.push(livres.length === 1 ? linhaDia(livres[0], [])
        : linhaLivre(livres[0], livres[livres.length - 1], livres.length));
      livres = [];
    }
    dias.forEach(function (dia) {
      var lista = porDia[dia] || [];
      if (!lista.length && dia < hj) return;      // passado vazio não interessa
      if (!lista.length && dia !== hj) { livres.push(dia); return; }
      drenar();
      linhas.push(linhaDia(dia, lista));
    });
    drenar();

    var corpo = '<div class="mk-toolbar">' + filtros + '</div><div class="mk-cal">' +
      linhas.join('') + '</div>';

    if (!itens.length) {
      corpo += '<div class="mk-setup" style="margin-top:12px">Calendário vazio. As pautas ' +
        'geradas pelo Claude aparecem no bloco acima — mova para cá editando ' +
        '<code>data/marketing_data.json</code> (campo <code>calendario</code>) ou peça ao Claude.</div>';
    }
    return card('📅 Calendário editorial', 'Próximos 14 dias · plano de publicação', corpo);
  }

  function sugestoes(d) {
    var s = d.conteudo_sugerido || [];
    if (!s.length) {
      if (!d.motivo_conteudo) return '';
      return card('🤖 Pauta sugerida pelo Claude', 'Gerada a partir dos números do Trinks',
        '<div class="mk-setup">Ainda não gerada. Motivo: <code>' + esc(d.motivo_conteudo) +
        '</code><br>Rode <code>python scripts/marketing_refresh.py --conteudo</code>.</div>');
    }
    return card('🤖 Pauta sugerida pelo Claude',
      s.length + ' ideias ancoradas nos números reais do mês',
      '<div class="mk-itens">' + s.map(function (p) {
        return postHTML(p, { mostrarData: true });
      }).join('') + '</div>');
  }

  function avaliacoes(d) {
    var g = d.gmn || {};
    var lista = g.avaliacoes || [];
    var rascunhos = {};
    (d.respostas_avaliacoes || []).forEach(function (r) { rascunhos[r.id] = r; });

    if (!g.conectado) {
      return card('⭐ Avaliações do Google', 'Google Meu Negócio',
        '<div class="mk-setup">Não conectado. <code>' + esc(g.motivo || 'sem credenciais') +
        '</code><br>Passo a passo em <code>docs/MARKETING_SETUP.md</code>.</div>');
    }
    if (!lista.length) {
      return card('⭐ Avaliações do Google', 'Nenhuma avaliação ainda',
        '<div class="mk-setup">A ficha ainda não tem avaliações. Peça às clientes: o link ' +
        'direto está em <code>gmn.perfil.url_avaliacao</code>.</div>');
    }

    var corpo = lista.slice(0, 25).map(function (a) {
      var cls = a.nota <= 2 ? 'baixa' : (a.nota === 3 ? 'media' : '');
      var h = '<div class="mk-aval ' + cls + '">' +
        '<div class="mk-head"><span class="autor">' + esc(a.autor) + '</span>' +
        '<span class="estrelas">' + estrelas(a.nota) + '</span>' +
        '<span class="quando">' + esc(dataBR(a.quando)) + '</span></div>' +
        (a.texto ? '<div class="texto">' + esc(a.texto) + '</div>' : '');
      if (a.respondida) {
        h += '<div class="mk-resposta"><span class="rot">respondida</span>' + esc(a.resposta) + '</div>';
      } else if (rascunhos[a.id]) {
        h += '<div class="mk-resposta rascunho"><span class="rot">rascunho do Claude · revise antes de publicar</span>' +
          esc(rascunhos[a.id].resposta) +
          '<div class="mk-acoes"><button class="mk-btn" data-copiar="' +
          esc(rascunhos[a.id].resposta) + '">📋 Copiar</button></div></div>';
      } else {
        h += '<div class="mk-resposta"><span class="rot">sem resposta</span>' +
          'Rode <code>marketing_refresh.py --conteudo</code> para gerar um rascunho.</div>';
      }
      return h + '</div>';
    }).join('');

    var r = d.resumo || {};
    return card('⭐ Avaliações do Google',
      'Nota ' + (r.nota_google || 0).toFixed(1) + ' · ' + num(r.avaliacoes_total) +
      ' avaliações · ' + num(r.avaliacoes_sem_resposta) + ' sem resposta', corpo);
  }

  function publicacoes(d) {
    var lista = ((d.meta || {}).publicacoes || []);
    if (!lista.length) return '';
    var corpo = '<div class="mk-grid-posts">' + lista.slice(0, 12).map(function (p) {
      return '<a class="mk-mid" href="' + esc(p.url) + '" target="_blank" rel="noopener">' +
        (p.midia ? '<img src="' + esc(p.midia) + '" alt="" loading="lazy">' : '') +
        '<div class="mk-mid-txt">' + esc((p.legenda || '').slice(0, 70)) + '…</div>' +
        '<div class="mk-mid-num">❤ ' + num(p.curtidas) + ' · 💬 ' + num(p.comentarios) +
        ' · ' + esc(dataBR(p.quando)) + '</div></a>';
    }).join('') + '</div>';
    return card('📸 Publicações recentes', 'Instagram · o que já foi ao ar', corpo);
  }

  function campanhas(d) {
    var lista = d.campanhas || [];
    if (!lista.length) return '';
    var linhas = lista.map(function (c) {
      return '<tr><td>' + esc(c.nome) + '</td><td>' + esc(c.objetivo || '') + '</td>' +
        '<td>' + esc(dataBR(c.inicio)) + ' → ' + esc(dataBR(c.fim)) + '</td>' +
        '<td>' + esc((c.canais || []).map(function (x) { return CANAIS[x] || x; }).join(', ')) + '</td>' +
        '<td>' + esc(c.status || '') + '</td></tr>';
    }).join('');
    return card('🎯 Campanhas', 'Ações com começo, meio e fim',
      '<table class="simple"><thead><tr><th>Campanha</th><th>Objetivo</th><th>Período</th>' +
      '<th>Canais</th><th>Status</th></tr></thead><tbody>' + linhas + '</tbody></table>');
  }

  function erros(d) {
    var e = d.erros || [];
    if (!e.length) return '';
    return card('⚠️ Erros do último refresh', 'O que não conseguiu atualizar',
      e.map(function (x) {
        return '<div class="mk-erro"><strong>' + esc(x.fonte) + '</strong> · ' + esc(x.msg) + '</div>';
      }).join(''));
  }

  function setup(d) {
    if ((d.gmn || {}).conectado && (d.meta || {}).conectado) return '';
    return card('🔌 Conectar as contas', 'Cada canal funciona de forma independente',
      '<div class="mk-setup">O painel já funciona sem conexão nenhuma — o calendário é seu. ' +
      'Para puxar métricas e avaliações automaticamente:' +
      '<ol>' +
      '<li><strong>Google Meu Negócio:</strong> <code>GMN_CLIENT_ID</code>, ' +
      '<code>GMN_CLIENT_SECRET</code>, <code>GMN_REFRESH_TOKEN</code></li>' +
      '<li><strong>Instagram/Facebook:</strong> <code>META_ACCESS_TOKEN</code>, ' +
      '<code>META_IG_USER_ID</code>, <code>META_PAGE_ID</code></li>' +
      '<li><strong>Pauta com Claude:</strong> <code>ANTHROPIC_API_KEY</code></li>' +
      '</ol>Passo a passo completo em <code>docs/MARKETING_SETUP.md</code>.</div>');
  }

  // ---------- render ----------
  function render() {
    var app = document.getElementById('mk-app');
    if (!app) return;
    var d = estado.dados || {};
    app.innerHTML = conexoes(d) + kpis(d) + sugestoes(d) + calendario(d) +
      avaliacoes(d) + publicacoes(d) + campanhas(d) + setup(d) + erros(d);

    var sub = document.getElementById('tab-marketing-sub');
    if (sub) {
      var r = d.resumo || {};
      sub.textContent = r.posts_pendentes ? '· ' + r.posts_pendentes + ' pendentes' : '';
    }

    app.querySelectorAll('[data-copiar]').forEach(function (b) {
      b.addEventListener('click', function () {
        var txt = b.getAttribute('data-copiar');
        navigator.clipboard.writeText(txt).then(function () {
          b.textContent = '✅ Copiado';
          b.classList.add('ok');
          setTimeout(function () { b.textContent = '📋 Copiar legenda'; b.classList.remove('ok'); }, 2000);
        }, function () { aviso('Não consegui copiar — selecione o texto à mão.', true); });
      });
    });
    app.querySelectorAll('[data-filtro]').forEach(function (b) {
      b.addEventListener('click', function () {
        estado.filtro = b.getAttribute('data-filtro');
        render();
      });
    });
  }

  async function carregar() {
    var app = document.getElementById('mk-app');
    if (!app) return;
    try {
      var r = await fetch(FONTE + '?_=' + Date.now(), { cache: 'no-store' });
      if (!r.ok) throw new Error('HTTP ' + r.status);
      estado.dados = await r.json();
      render();
    } catch (e) {
      app.innerHTML = card('Marketing', 'Dados ainda não gerados',
        '<div class="mk-setup">Não achei <code>' + FONTE + '</code> (' + esc(e.message) + ').<br>' +
        'Rode <code>python scripts/marketing_refresh.py</code> e commite o resultado.</div>');
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', carregar);
  } else {
    carregar();
  }
  setInterval(function () { if (!document.hidden) carregar(); }, 10 * 60 * 1000);
  window.mkRecarregar = carregar;
})();
