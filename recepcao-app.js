/* Tela "Hoje na recepção" (12/11/2026).
 * Substitui os cards de gestão por 4 blocos de ação + pacotes, com a mensagem
 * pronta de cada caso (textos da diretora comercial, 12/11/2026).
 * Nada é enviado sozinho: a recepção abre o WhatsApp com o texto preenchido
 * ou copia, e confere antes de enviar.
 * Dados: cofre-recepcao.js (eventos recepcao-dados e recepcao-pacotes).
 */
(function () {
  var DADOS = null, PACOTES = null;
  var LOJAS = {
    escova: { nome: 'Fast Escova Limão', ig: 'fastescova.limao', rotulo: 'Escova' },
    spa: { nome: 'Fast Spa Limão', ig: 'fastspa.limao', rotulo: 'Spa' }
  };
  // Brindes: só o que o documento da comercial já define para a Escova.
  // Spa e renovação começam vazios: a recepção preenche (e a frase some se vazio).
  var CFG_PADRAO = {
    escova: { nome: '', google: 'https://search.google.com/local/writereview?placeid=ChIJ0wkZd4z5zpQRO9VrCLQoAEE', brRen: '', brResg: 'uma Nutrição Capilar', brAniv: 'uma Hidratação com Ozonioterapia', brAmiga: 'uma Ozonioterapia' },
    spa: { nome: '', google: 'https://search.google.com/local/writereview?placeid=ChIJ2-w36075zpQREVX7xtpVpno', brRen: '', brResg: '', brAniv: '', brAmiga: '' }
  };

  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function unidade() { try { return localStorage.getItem('unidade_ativa_recepcao') === 'spa' ? 'spa' : 'escova'; } catch (e) { return 'escova'; } }
  function hojeISO() { var d = new Date(); return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0'); }
  function ontemISO() { var d = new Date(Date.now() - 86400000); return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0'); }
  function dataBR(iso) { var p = String(iso || '').slice(0, 10).split('-'); return p.length === 3 ? p[2] + '/' + p[1] + '/' + p[0] : ''; }
  function ls(k, v) { try { if (v === undefined) return localStorage.getItem(k); if (v === null) localStorage.removeItem(k); else localStorage.setItem(k, v); } catch (e) {} return null; }
  function cfg(u) { var c = {}, base = CFG_PADRAO[u], salvo = {}; try { salvo = JSON.parse(ls('rp_cfg_' + u) || '{}'); } catch (e) {} Object.keys(base).forEach(function (k) { c[k] = (k in salvo) ? salvo[k] : base[k]; }); return c; }
  function salvarCfg(u, c) { ls('rp_cfg_' + u, JSON.stringify(c)); }
  function primeiro(n) { var t = String(n || '').trim().split(/\s+/)[0] || ''; return t.charAt(0).toUpperCase() + t.slice(1).toLowerCase(); }
  function tel(t) { var d = String(t || '').replace(/\D/g, ''); if (!d) return ''; if (d.length <= 11) d = '55' + d; return d; }
  // O numero nao aparece na tela: so o botao do WhatsApp o carrega. Aqui so o aviso de falta.
  function fone() { return ''; } // o botao ja avisa "sem telefone"
  function bonito(s) { return String(s || '').toLowerCase().replace(/(^|[\s(+\-])(\S)/g, function (m, a, b) { return a + b.toUpperCase(); }); }

  // ---------- mensagens (textos da diretora comercial) ----------
  // Tom de recepcionista no WhatsApp: simples, especifico, sem exagero. Quase sem emoji, sem preco.
  // Brinde so entra na frase se estiver preenchido em "Meus dados e brindes".
  function msgOi(u, nome) { return 'Oi, ' + primeiro(nome) + ', tudo bem?'; }
  function quandoAtendida(x) {
    if (!x || !x.dia) return 'ontem';
    return x.dia === ontemISO() ? 'ontem' : 'no dia ' + dataBR(x.dia).slice(0, 5);
  }
  function msgRenovar(u, c, p, total) {
    var n = primeiro(p.cliente), falta = total === 1 ? 'falta só 1 sessão' : 'faltam só ' + total + ' sessões';
    var presente = c.brRen ? ' Renovando agora, você ganha ' + c.brRen + ' na 1ª ' + (u === 'escova' ? 'escova' : 'sessão') + ' do pacote novo.' : '';
    return 'Oi, ' + n + ', tudo bem? Seu pacote de ' + bonito(p.pacote) + ' está no fim: ' + falta + '.' + presente +
      ' Se quiser, já deixo a renovação pronta para a sua próxima vinda.';
  }
  function msgResgate(u, c, cli) {
    var n = primeiro(cli.cliente), loja = u === 'spa' ? 'no Fast Spa' : 'na Fast';
    var mimo = c.brResg ? ' Se vier essa semana, ganha ' + c.brResg + '.' : '';
    return 'Oi, ' + n + ', tudo bem? Faz um tempinho que você não aparece ' + loja + '.' + mimo +
      (u === 'spa' ? ' Pode vir como está, sem hora marcada.' : ' Não precisa agendar, é só chegar.');
  }
  function msgAniv(u, c, a) {
    var n = primeiro(a.cliente);
    var abre = a.dias === 0 ? 'Oi, ' + n + ', parabéns pelo seu dia! 🎂' : 'Oi, ' + n + ', seu aniversário está chegando.';
    if (u === 'spa') {
      return abre + (c.brAniv ? ' Para comemorar, vem aqui no Fast Spa e ganha ' + c.brAniv + '.' : ' Vem comemorar com a gente no Fast Spa.') + ' Pode vir como está, sem hora marcada.';
    }
    return abre + (c.brAniv ? ' Na sua escova de aniversário você ganha ' + c.brAniv + '.' : ' Vem comemorar com a gente.') +
      (c.brAmiga ? ' Se trouxer uma amiga, ela ganha ' + c.brAmiga + '.' : '') + ' Sem hora marcada, é só chegar.';
  }
  function msgPos1(u, c, cli) {
    var L = LOJAS[u], quem = c.nome ? 'aqui é a ' + c.nome + ', da ' + L.nome : 'aqui é da ' + L.nome;
    return 'Oi, ' + primeiro(cli.cliente) + ', ' + quem + '. Obrigada por ter vindo ' + quandoAtendida(cli) + '. Gostou do atendimento? Se postar, marca a gente: @' + L.ig;
  }
  function msgPos2(u, c) {
    return 'Que bom que gostou! Se puder, avalia a gente no Google. Leva 30 segundos e ajuda muito: ' + c.google + ' Obrigada!';
  }
  // Retoque (documento "Gestão de clientes Fast Retoque", da diretora comercial)
  function msgRetoque(u, c, x) {
    return 'Oi, ' + primeiro(x.cliente) + ', tudo bem? Já deve estar na hora de retocar a raiz. O Fast Retoque leva 30 minutos. Se vier até amanhã, a hidratação é por nossa conta: é só mostrar esta mensagem na recepção.';
  }
  function msgRetoquePacote(u, c, x) {
    return 'Oi, ' + primeiro(x.cliente) + ', tudo bem? Como você faz o Fast Retoque com frequência, tenho uma proposta: no pacote com 4 retoques você ganha 2 hidratações de bônus. Quer que eu deixe reservado?';
  }

  // ---------- combos do documento "Combos para clientes de pacotes" ----------
  function combos(u, pacote) {
    if (u !== 'escova') return [];
    var p = String(pacote).toUpperCase();
    if (/M[ÃA]OS|P[ÉE]S|UNHAS/.test(p)) return [
      'Combo Olhar Prático: design de sobrancelhas, buço ou epilação facial na própria mesa da manicure (cerca de 15 min).',
      'Combo Plástica dos Pés: esfoliação profunda e hidratação enquanto a manicure faz as mãos.',
      'Combo Cutícula & Mãos Perfeitas: sérum de cutícula e hidratante de mãos; para cliente com pacote, o sérum sai por metade do valor no dia do uso.',
      'Turbine seu Pacote Hoje: ofereça Blindagem, Spa dos Pés ou Sobrancelha.'
    ];
    return [
      'Combo Tratamento: aplicar o tratamento durante o tempo de ação da ozonioterapia.',
      'Combo Detox & Brilho: esfoliação/peeling do couro com o efeito do ozônio.',
      'Combo Express Mãos & Buço: manicure rápida e buço enquanto faz a escova.'
    ];
  }

  // ---------- peças de tela ----------
  function copiar(txt, btn) {
    function ok() { var o = btn.textContent; btn.textContent = 'Copiado ✓'; setTimeout(function () { btn.textContent = o; }, 1600); }
    if (navigator.clipboard && navigator.clipboard.writeText) { navigator.clipboard.writeText(txt).then(ok, fallback); } else fallback();
    function fallback() { var t = document.createElement('textarea'); t.value = txt; document.body.appendChild(t); t.select(); try { document.execCommand('copy'); ok(); } catch (e) {} t.remove(); }
  }
  // ---------- registro de mensagens enviadas (so neste aparelho) ----------
  var _envc = null;
  function envLer() { if (_envc) return _envc; try { _envc = JSON.parse(ls('rp_env') || '{}'); } catch (e) { _envc = {}; } return _envc; }
  function envGravar(o) {
    var corte = Date.now() - 60 * 86400000;
    Object.keys(o).forEach(function (k) { if (new Date(o[k].t).getTime() < corte) delete o[k]; });
    ls('rp_env', JSON.stringify(o));
    _envc = null;
  }
  function quando(iso) { var d = new Date(iso); return String(d.getDate()).padStart(2, '0') + '/' + String(d.getMonth() + 1).padStart(2, '0') + ' ' + String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0'); }
  var TIPOS = { renovar: 'Renovação', aniv: 'Aniversário', resg: 'Resgate', pos: 'Pós-venda (1ª)', pos2: 'Pós-venda (Google)', ret15: 'Lembrete de retoque', retatr: 'Retoque atrasado', retpkg: 'Pacote de retoque', consulta: 'Contato' };
  var MSGS = []; // textos por índice (evita jogar texto longo em atributo)
  function botoes(chave, tipo, cliente, telefone, texto, rotulo) {
    var i = MSGS.push(texto) - 1, t = tel(telefone), u = unidade();
    var ek = esc(u + '|' + tipo + '|' + (chave || cliente)), en = esc(cliente);
    var wa = t ? '<a class="rp-b rp-wa" data-ek="' + ek + '" data-en="' + en + '" data-tp="' + tipo + '" target="_blank" rel="noopener" href="https://wa.me/' + t + '?text=' + encodeURIComponent(texto) + '">💬 ' + (rotulo || 'Abrir WhatsApp') + '</a>' : '<span class="rp-b rp-off" title="Sem telefone cadastrado">sem telefone</span>';
    var rec = envLer()[u + '|' + tipo + '|' + (chave || cliente)];
    var sel = rec ? '<div class="rp-env">✅ ' + 'Mensagem enviada (' + (TIPOS[tipo] || 'contato') + ') em ' + quando(rec.t) + ' · <a href="#" class="rp-und" data-ek="' + ek + '">desfazer</a></div>' : '';
    var mk = rec ? '' : '<button class="rp-b rp-ok" data-ek="' + ek + '" data-en="' + en + '" data-tp="' + tipo + '" title="Toque depois de mandar a mensagem">✅ Marcar como enviada</button>';
    return wa + mk + sel;
  }
  function feito(u, tipo, cliente) { return ls('rp_feito_' + hojeISO() + '_' + u + '_' + tipo + '_' + cliente) === '1'; }
  function hue(n) { var h = 0, s = String(n); for (var i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) % 360; return h; }
  function iniciais(n) { var p = String(n).trim().split(/\s+/).filter(Boolean); return (((p[0] || '')[0] || '') + (p.length > 1 ? p[p.length - 1][0] : '')).toUpperCase(); }
  function linha(u, tipo, cliente, detalhe, acoes, extra, chave) {
    return '<div class="rp-l"><div class="rp-av" style="--h:' + hue(cliente) + '">' + esc(iniciais(cliente)) + '</div><div class="rp-t"><div class="rp-nm">' + esc(bonito(cliente)) + '</div>' +
      '<div class="rp-d">' + detalhe + '</div>' + (extra || '') + '</div><div class="rp-a">' + acoes + '</div></div>';
  }
  var ABERTO = {}; // lembra o que a recepcao expandiu
  var VISIVEIS = 5; // quantas ficam a vista em cada tema; o resto abre em "Ver todas"
  function bloco(id, titulo, sub, itens, vazio, vis) {
    if (vis == null) vis = VISIVEIS;
    var corpo = itens.length ? itens.slice(0, vis).join('') : '<div class="rp-vazio">' + vazio + '</div>';
    var resto = itens.length > vis ? '<details class="rp-mais" data-id="' + id + '"' + (ABERTO[id] ? ' open' : '') + '><summary>Ver todas (' + itens.length + ')</summary>' + itens.slice(vis).join('') + '</details>' : '';
    return '<section class="rp-s rp-t-' + id + '" id="rp-' + id + '"><div class="rp-sh"><h3>' + titulo + '</h3><span class="rp-n">' + itens.length + '</span></div><div class="rp-sub">' + sub + '</div><div class="rp-lst">' + corpo + '</div>' + resto + '</section>';
  }
  function pct(v) { return v == null ? '–' : String(v).replace('.', ',') + '%'; }
  function num(v) { return v == null ? '–' : Number(v).toLocaleString('pt-BR'); }
  var ICO = { 'Clientes na base': '👥', 'Ativas (30 dias)': '🟢', 'Novas (30 dias)': '✨', 'Sem vir há +60 dias': '😴', 'Em risco de sumir': '⚠️', 'Voltam à loja': '🔁', 'Recorrentes': '⭐', 'Vieram uma vez só': '☝️', 'Visitas por cliente': '📈', 'Telefone': '📞', 'Aniversário': '🎂', 'E-mail': '✉️', 'Como nos conheceu': '🧭', 'Hoje': '📲', 'Últimos 7 dias': '📅', 'Últimos 30 dias': '🗓️' };
  function tile(rot, val, dica, tom) {
    var m = /^([0-9]+(?:,[0-9]+)?)%$/.exec(String(val)), barra = m ? '<div class="rp-bar"><i style="width:' + Math.min(100, parseFloat(m[1].replace(',', '.'))) + '%"></i></div>' : '';
    return '<div class="rp-k' + (tom ? ' rp-k-' + tom : '') + '"><div class="rp-ki">' + (ICO[rot] || '•') + '</div><div class="rp-kv">' + val + '</div><div class="rp-kr">' + rot + '</div><div class="rp-kd">' + dica + '</div>' + barra + '</div>';
  }
  function kpis(a, L) {
    var s = a.clientes_snapshot, cad = (a.clientes_cadastro || {}).cobertura;
    if (!s) return '';
    function cob(v) { return v == null ? '' : (v >= 90 ? 'ok' : (v >= 60 ? 'at' : 'ruim')); }
    var g1 = tile('Clientes na base', num(s.total_base), 'cadastradas na loja') +
      tile('Ativas (30 dias)', num(s.ativos_30d), 'vieram no último mês') +
      tile('Novas (30 dias)', num(s.novos_30d), 'primeira visita recente') +
      tile('Sem vir há +60 dias', num(s.dormentes_60d), 'chamar de volta', s.dormentes_60d ? 'at' : '') +
      tile('Em risco de sumir', num(s.n_alerta_churn), 'lista de Resgate abaixo', s.n_alerta_churn ? 'at' : '');
    var g2 = tile('Voltam à loja', pct(s.pct_recorrentes), 'clientes com 2+ visitas', s.pct_recorrentes >= 60 ? 'ok' : 'at') +
      tile('Recorrentes', num(s.n_recorrentes), 'vieram 2 vezes ou mais') +
      tile('Vieram uma vez só', num(s.n_uma_vez), 'oportunidade de fidelizar', s.n_uma_vez ? 'at' : '') +
      tile('Visitas por cliente', s.freq_media_visitas == null ? '–' : String(s.freq_media_visitas).replace('.', ','), 'média no ano');
    var g3 = cad ? tile('Telefone', pct(cad.telefone), 'sem ele não há WhatsApp', cob(cad.telefone)) +
      tile('Aniversário', pct(cad.data_nasc), 'permite o parabéns', cob(cad.data_nasc)) +
      tile('E-mail', pct(cad.email), 'cadastrar na recepção', cob(cad.email)) +
      tile('Como nos conheceu', pct(cad.canal_aquisicao), 'ajuda a medir a divulgação', cob(cad.canal_aquisicao)) : '';
    var g4 = (L && (L.hoje != null || L['7d'] != null)) ? tile('Hoje', num(L.hoje), 'conversas iniciadas pelos anúncios') + tile('Últimos 7 dias', num(L['7d']), 'cada uma é uma cliente a retornar') + tile('Últimos 30 dias', num(L['30d']), 'responder e checar se veio') : '';
    return '<div class="rp-kg"><h3>👥 Clientes</h3><div class="rp-kw">' + g1 + '</div></div>' +
      '<div class="rp-kg"><h3>🔁 Recorrência</h3><div class="rp-kw">' + g2 + '</div></div>' +
      (g3 ? '<div class="rp-kg"><h3>✅ Qualidade do cadastro</h3><div class="rp-kw">' + g3 + '</div></div>' : '') +
      (g4 ? '<div class="rp-kg rp-kg-hero"><h3>📲 Leads dos anúncios (Meta)</h3><div class="rp-kw">' + g4 + '</div></div>' : '');
  }
  function inputCfg(k, rot, v, dica) { return '<label class="rp-f1"><span>' + rot + '</span><input data-cfg="' + k + '" value="' + esc(v) + '" placeholder="' + esc(dica || '') + '"></label>'; }

  function desenhar() {
    var raiz = document.getElementById('tab-clientes');
    if (!raiz || !DADOS) return;
    var alvo = document.getElementById('recepcao-app');
    if (!alvo) { alvo = document.createElement('div'); alvo.id = 'recepcao-app'; raiz.insertBefore(alvo, raiz.firstChild); }
    var u = unidade(), L = LOJAS[u], c = cfg(u), D = DADOS[u] || {}, a = (D.abas || {}).anual || {};
    var qEl = document.getElementById('rp-busca'), q = qEl ? qEl.value : '', qn = q.trim().toLowerCase();
    function pass(n) { return !qn || String(n).toLowerCase().indexOf(qn) >= 0; }
    MSGS = [];
    _envc = null;

    // pacotes
    var pacs = ((PACOTES && PACOTES[u]) || []).map(function (p) {
      return { cliente: p.cliente, pacote: p.pacote, itens: p.itens, telefone: p.telefone || '', total: p.itens.reduce(function (s, it) { return s + it.restante; }, 0) };
    }).filter(function (p) { return pass(p.cliente); });
    pacs.sort(function (x, y) { var px = x.total <= 1 ? 0 : (x.total === 2 ? 1 : 2), py = y.total <= 1 ? 0 : (y.total === 2 ? 1 : 2); return px - py || x.cliente.localeCompare(y.cliente, 'pt-BR'); });
    function linhaPacote(p, comMsg) {
      var itens = p.itens.map(function (it) { return '<strong>' + it.restante + '</strong> × ' + esc(bonito(it.servico)); }).join(' · ');
      var det = esc(bonito(p.pacote)) + ' — falta ' + itens + '' + fone(p.telefone);
      var cb = combos(u, p.pacote);
      var extra = (comMsg && cb.length) ? '<details class="rp-cb"><summary>Combos para oferecer hoje</summary><ul>' + cb.map(function (x) { return '<li>' + esc(x) + '</li>'; }).join('') + '</ul></details>' : '';
      var ac = comMsg ? botoes(p.cliente + '|' + p.pacote, 'renovar', p.cliente, p.telefone, msgRenovar(u, c, p, p.total), 'Mensagem de renovação') : '';
      return linha(u, 'renovar', p.cliente, det, ac, extra, p.cliente + '|' + p.pacote);
    }
    var renovar = pacs.filter(function (p) { return p.total <= 1; }).map(function (p) { return linhaPacote(p, true); });
    var poucos = pacs.filter(function (p) { return p.total === 2; }).map(function (p) { return linhaPacote(p, true); });
    var emUso = pacs.filter(function (p) { return p.total > 2; }).map(function (p) { return linhaPacote(p, false); });

    // aniversariantes (hoje até +3 dias)
    var aniv = ((D.aniv30 && D.aniv30.length ? D.aniv30 : a.aniversariantes) || []).filter(function (x) { return x.dias <= 30 && pass(x.cliente); }).map(function (x) {
      return linha(u, 'aniv', x.cliente, (x.dias === 0 ? '<strong>HOJE</strong>' : (x.dias === 1 ? 'amanhã' : 'em ' + x.dias + ' dias')) + ' · ' + esc(x.data_aniv) + (x.n_visitas != null ? ' · ' + x.n_visitas + ' visita(s)' : '') + fone(x.telefone), botoes('', 'aniv', x.cliente, x.telefone, msgAniv(u, c, x), 'Parabéns no WhatsApp'));
    });
    // resgate (+30 dias)
    var resg = ((D.resgate && D.resgate.length ? D.resgate : (a.churn_early || {}).top) || []).filter(function (x) { return x.dias_sem_vir >= 30 && pass(x.cliente); }).map(function (x) {
      return linha(u, 'resg', x.cliente, 'sem vir há <strong>' + x.dias_sem_vir + ' dias</strong> · ' + x.n_visitas + ' visita(s) · última em ' + dataBR(x.ultima_visita) + (x.ultimos_servicos && x.ultimos_servicos.length ? ' · fez: ' + esc(x.ultimos_servicos.slice(0, 2).join(', ')) : '') + '' + fone(x.telefone), botoes('', 'resg', x.cliente, x.telefone, msgResgate(u, c, x), 'Chamar de volta'));
    });
    // pós-venda (clientes de ontem)
    var pos = (D.ontem || []).filter(function (x) { return pass(x.cliente); }).map(function (x) {
      var b1 = botoes('', 'pos', x.cliente, x.telefone, msgPos1(u, c, x), '1ª mensagem');
      var b2 = c.google ? botoes('', 'pos2', x.cliente, x.telefone, msgPos2(u, c), '2ª: avaliação Google') : '<span class="rp-b rp-off" title="Cole o link em Meus dados e brindes">2ª: falta o link do Google desta loja (⚙️ Meus dados)</span>';
      return linha(u, 'pos', x.cliente, 'atendida ' + (x.dia ? (x.dia === ontemISO() ? 'ontem' : 'em ' + dataBR(x.dia).slice(0, 5)) : 'ontem') + fone(x.telefone) + ' · envie a 2ª só se a resposta da 1ª for positiva', b1 + b2);
    });

    // consulta de qualquer cliente da base (a partir de 3 letras)
    var consulta = [];
    if (qn.length >= 3) {
      consulta = (D.base || []).filter(function (x) { return x.n.toLowerCase().indexOf(qn) >= 0; }).slice(0, 15).map(function (x) {
        var pk = ((PACOTES && PACOTES[u]) || []).filter(function (p) { return p.cliente.split(/\s+/).join(' ').toLowerCase() === x.n.toLowerCase(); });
        var pt = pk.length ? pk.map(function (p) { return esc(bonito(p.pacote)) + ': ' + p.itens.map(function (it) { return '<strong>' + it.restante + '</strong> × ' + esc(bonito(it.servico)); }).join(', '); }).join(' | ') : 'sem pacote com saldo';
        var det = pt + (x.a ? ' · aniversário ' + esc(x.a) : '') + fone(x.t);
        return linha(u, 'consulta', x.n, det, botoes('', 'consulta', x.n, x.t, msgOi(u, x.n), 'Abrir WhatsApp'));
      });
    }
    // lista completa da base (ordem alfabetica), com saldo de pacote e aniversario
    var pmap = {};
    ((PACOTES && PACOTES[u]) || []).forEach(function (p) { var k = p.cliente.split(/\s+/).join(' ').toLowerCase(); (pmap[k] = pmap[k] || []).push(p); });
    var todos = (D.base || []).filter(function (x) { return pass(x.n); }).map(function (x) {
      var pk = pmap[x.n.toLowerCase()] || [];
      var pt = pk.length ? pk.map(function (p) { return esc(bonito(p.pacote)) + ': ' + p.itens.map(function (it) { return '<strong>' + it.restante + '</strong> × ' + esc(bonito(it.servico)); }).join(', '); }).join(' | ') : '';
      var det = [pt, x.a ? 'aniversário ' + esc(x.a) : ''].filter(Boolean).join(' · ') || '&nbsp;';
      return linha(u, 'consulta', x.n, det, botoes('', 'consulta', x.n, x.t, msgOi(u, x.n), 'WhatsApp'));
    });

    // Fast Retoque (so Escova)
    var R = D.retoque || {}, ret = { lembrar: [], atrasadas: [], pacote: [], nunca: [] };
    if (u === 'escova') {
      ret.lembrar = (R.lembrar || []).filter(function (x) { return pass(x.cliente); }).map(function (x) {
        return linha(u, 'ret15', x.cliente, 'último retoque há <strong>' + x.dias + ' dias</strong> · ' + x.n + ' retoque(s) · voucher de hidratação vale até 25 dias', botoes('', 'ret15', x.cliente, x.telefone, msgRetoque(u, c, x), 'Lembrete de retoque'));
      });
      ret.atrasadas = (R.atrasadas || []).filter(function (x) { return pass(x.cliente); }).map(function (x) {
        return linha(u, 'retatr', x.cliente, 'último retoque há <strong>' + x.dias + ' dias</strong> · ' + x.n + ' retoque(s) · raiz já passou do ponto', botoes('', 'retatr', x.cliente, x.telefone, msgRetoque(u, c, x), 'Chamar para retoque'));
      });
      ret.pacote = (R.pacote || []).filter(function (x) { return pass(x.cliente); }).map(function (x) {
        return linha(u, 'retpkg', x.cliente, x.n + ' retoques avulsos · último há ' + x.dias + ' dias · ofereça o pacote de 4 retoques + 2 hidratações', botoes('', 'retpkg', x.cliente, x.telefone, msgRetoquePacote(u, c, x), 'Oferecer pacote'));
      });
      ret.nunca = (R.nunca || []).filter(function (x) { return pass(x.cliente); }).map(function (x) {
        return linha(u, 'retnunca', x.cliente, 'veio <strong>' + x.dias_escova + ' vezes</strong> fazer escova e nunca fez retoque · última escova há ' + x.dias + ' dias', '<span class="rp-b rp-off" style="white-space:normal">abordar na cadeira</span>');
      });
    }

    // historico de envios (60 dias), mais recentes primeiro
    var env = envLer(), hist = Object.keys(env).filter(function (k) { return k.indexOf(u + '|') === 0 && pass(env[k].n); }).map(function (k) { return { k: k, r: env[k] }; });
    hist.sort(function (x, y) { return new Date(y.r.t) - new Date(x.r.t); });
    var enviadas = hist.map(function (h) {
      return '<div class="rp-l"><div class="rp-t"><strong>' + esc(bonito(h.r.n)) + '</strong><div class="rp-d">' + esc(TIPOS[h.r.tp] || 'Mensagem') + ' · enviada em ' + quando(h.r.t) + '</div></div><div class="rp-a"><a href="#" class="rp-b rp-cp rp-und" data-ek="' + esc(h.k) + '">desfazer</a></div></div>';
    });

    var datadado = dataBR(D.gerado_em) + ' ' + String(D.gerado_em || '').slice(11, 16);
    var bt = document.getElementById('brand-title'), bs = document.getElementById('brand-sub');
    if (bt) bt.innerHTML = 'Atendimento <span style="color:var(--accent-ink)">Fast</span>';
    if (bs) bs.textContent = 'Recepção · ' + L.nome;
    var cab = '<div class="rp-top"><h2>📋 Hoje na recepção · ' + L.nome + '</h2>' +
      '<div class="rp-meta">Dados dos clientes de ' + esc(datadado) + ' · pacotes: posição do Trinks em ' + (PACOTES ? dataBR(PACOTES.posicao) : '<strong>indisponível</strong>') + '</div>' +
      kpis(a, D.leads) +
      '<div class="rp-busca-w"><input id="rp-busca" type="search" placeholder="Cliente chegou? Digite o nome…" value="' + esc(q) + '"></div>' +
      '<details class="rp-cfg"><summary>⚙️ Meus dados e brindes (ficam só neste aparelho)</summary>' +
      inputCfg('nome', 'Seu nome (assina o pós-venda)', c.nome, 'ex.: Ana') +
      inputCfg('google', 'Link de avaliação do Google (já vem preenchido)', c.google, 'cole o link') +
      inputCfg('brRen', 'Brinde da renovação do pacote', c.brRen, 'ex.: uma Hidratação (vazio = sem brinde)') +
      inputCfg('brResg', 'Brinde do resgate (sumidas)', c.brResg, 'vazio = sem brinde') +
      inputCfg('brAniv', 'Brinde de aniversário', c.brAniv, 'vazio = sem brinde') +
      (u === 'escova' ? inputCfg('brAmiga', 'Presente para a amiga (aniversário)', c.brAmiga, 'vazio = sem') : '') +
      '</details></div>';

    var secoes =
      (qn.length >= 3 ? bloco('consulta', '🔎 Consulta de cliente', 'Qualquer cliente da base, mesmo sem pacote ou aniversário.', consulta, 'Ninguém com esse nome na base.') : '') +
      bloco('renovar', '🔴 Renovar pacote agora', 'Falta 1 sessão. Ofereça a renovação e não deixe sair com a comanda zerada.', renovar, qn ? 'Nenhum encontrado.' : 'Nenhum pacote com 1 sessão restante.') +
      bloco('poucos', '🟡 Pacote acabando', 'Faltam 2 sessões: já vá preparando a renovação.', poucos, qn ? 'Nenhum encontrado.' : 'Nenhum no momento.') +
      bloco('aniv', '🎂 Aniversariantes (próximos 30 dias)', 'Mande o parabéns com o presente.', aniv, qn ? 'Nenhum encontrado.' : 'Ninguém faz aniversário nos próximos 30 dias.') +
      bloco('pos', '⭐ Pós-venda (atendidas nos últimos 3 dias)', 'Agradeça e peça a opinião. A 2ª mensagem (Google) só se responderem de forma positiva.', pos, qn ? 'Nenhum encontrado.' : 'Sem clientes de ontem nos dados.') +
      bloco('resg', '💛 Resgate (sumidas há mais de 30 dias)', 'Mensagem de saudade com o mimo de retorno.', resg, qn ? 'Nenhum encontrado.' : 'Nenhuma cliente em risco.') +
      (u === 'escova' ? bloco('retlem', '💇 Retoque: lembrar agora (15 a 25 dias)', 'Última vez há 15 a 25 dias. Mande o lembrete com o voucher de hidratação, que vale até 25 dias.', ret.lembrar, qn ? 'Nenhum encontrado.' : 'Ninguém nessa janela hoje.') +
        bloco('retatr', '💇 Retoque: raiz já passou do ponto (26 a 60 dias)', 'Fizeram há mais de 25 dias. Chame de volta.', ret.atrasadas, qn ? 'Nenhum encontrado.' : 'Ninguém nessa janela hoje.') +
        bloco('retpkg', '💇 Retoque: oferecer o pacote', 'Já fizeram 2 ou mais retoques avulsos. Pacote: 4 retoques + 2 hidratações de bônus (valor do pacote: confira com a gerente).', ret.pacote, qn ? 'Nenhum encontrado.' : 'Nenhuma cliente com 2 retoques ainda.') +
        bloco('retnunca', '👀 Retoque: nunca fez e faz escova sempre', 'Olhe a raiz na lavagem e ofereça: "Notei que sua raiz já está pedindo um carinho! Aqui a gente resolve em 30 minutos, enquanto você toma um café. Como você já está na cadeira para a escova, podemos fazer agora?"', ret.nunca, qn ? 'Nenhum encontrado.' : 'Nenhuma cliente nesse perfil.') : '') +
      bloco('env', '✅ Mensagens enviadas (60 dias)', 'Clientes marcadas como enviadas neste aparelho, e quando. Vale só aqui: outros aparelhos têm o próprio registro.', enviadas, 'Nenhuma mensagem registrada ainda.') +
      bloco('uso', '🎁 Outros pacotes em uso', 'Mais de 2 sessões restantes.', emUso, qn ? 'Nenhum encontrado.' : 'Nenhum.') +
      bloco('todos', '📇 Todas as clientes', 'A base inteira em ordem alfabética. Toque em "Ver todas" para abrir; a busca do topo também filtra aqui.', todos, 'Nenhuma cliente encontrada.', 0);

    alvo.innerHTML = cab + secoes;
    var b = document.getElementById('rp-busca');
    b.addEventListener('input', function () { var pos = b.selectionStart; desenhar(); var n = document.getElementById('rp-busca'); n.focus(); try { n.setSelectionRange(pos, pos); } catch (e) {} });
    alvo.querySelectorAll('details.rp-mais').forEach(function (el) { el.addEventListener('toggle', function () { ABERTO[el.getAttribute('data-id')] = el.open; }); });
    function registrar(el) { var o = envLer(); o[el.getAttribute('data-ek')] = { t: new Date().toISOString(), n: el.getAttribute('data-en'), tp: el.getAttribute('data-tp') }; envGravar(o); setTimeout(desenhar, 150); }
    alvo.querySelectorAll('.rp-ok').forEach(function (el) { el.addEventListener('click', function () { registrar(el); }); });
    alvo.querySelectorAll('.rp-cp[data-i]').forEach(function (el) { el.addEventListener('click', function () { copiar(MSGS[+el.getAttribute('data-i')], el); }); });
    alvo.querySelectorAll('.rp-und').forEach(function (el) { el.addEventListener('click', function (ev) { ev.preventDefault(); var o = envLer(); delete o[el.getAttribute('data-ek')]; envGravar(o); desenhar(); }); });
    alvo.querySelectorAll('.rp-ck').forEach(function (el) { el.addEventListener('change', function () { ls('rp_feito_' + hojeISO() + '_' + el.getAttribute('data-k'), el.checked ? '1' : null); el.closest('.rp-l').classList.toggle('rp-f', el.checked); }); });
    alvo.querySelectorAll('[data-cfg]').forEach(function (el) { el.addEventListener('change', function () { var cc = cfg(u); cc[el.getAttribute('data-cfg')] = el.value.trim(); salvarCfg(u, cc); desenhar(); }); });
  }

  var css = document.createElement('style');
  css.textContent = `
#tab-clientes > :not(#recepcao-app){display:none!important}
#recepcao-app{font-size:15px;--rad:16px;--sombra:0 1px 2px rgba(16,24,40,.06),0 4px 14px rgba(16,24,40,.06);max-width:1100px;margin:0 auto}
.rp-top{margin-bottom:6px}
.rp-top h2{margin:0;font-size:24px;font-weight:800;letter-spacing:-.02em;line-height:1.15}
.rp-meta{display:inline-block;margin:8px 0 14px;padding:5px 12px;border-radius:999px;background:var(--surface-2);color:var(--ink-3);font-size:12px}
/* busca fixa */
.rp-busca-w{position:sticky;top:0;z-index:20;margin:0 -4px 16px;padding:8px 4px;background:linear-gradient(var(--bg) 70%,transparent)}
#rp-busca{width:100%;box-sizing:border-box;padding:14px 18px 14px 46px;font-size:16px;border:1px solid var(--border);border-radius:999px;background:var(--surface) url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='20' height='20' viewBox='0 0 24 24' fill='none' stroke='%23999' stroke-width='2.2' stroke-linecap='round'%3E%3Ccircle cx='11' cy='11' r='7'/%3E%3Cpath d='M21 21l-4.3-4.3'/%3E%3C/svg%3E") no-repeat 16px center;color:var(--ink);box-shadow:var(--sombra);outline:none;transition:border-color .15s,box-shadow .15s}
#rp-busca:focus{border-color:var(--accent-ink);box-shadow:0 0 0 4px color-mix(in srgb,var(--accent-ink) 18%,transparent)}
/* KPIs */
.rp-kg{margin:0 0 18px}
.rp-kg h3{margin:0 0 8px;font-size:11.5px;font-weight:700;letter-spacing:.09em;text-transform:uppercase;color:var(--ink-3)}
.rp-kw{display:grid;grid-template-columns:repeat(auto-fill,minmax(158px,1fr));gap:10px}
.rp-k{position:relative;background:var(--surface);border:1px solid var(--border);border-radius:var(--rad);padding:14px 14px 13px;box-shadow:var(--sombra);overflow:hidden;--kc:var(--ink-3)}
.rp-k::before{content:"";position:absolute;left:0;top:0;bottom:0;width:4px;background:var(--kc);opacity:.85}
.rp-k-ok{--kc:#1e9e4a}.rp-k-at{--kc:#e0a100}.rp-k-ruim{--kc:#d64545}
.rp-ki{display:flex;align-items:center;justify-content:center;width:30px;height:30px;border-radius:10px;font-size:16px;background:color-mix(in srgb,var(--kc) 14%,var(--surface-2));margin-bottom:8px}
.rp-kv{font-size:28px;font-weight:800;line-height:1;letter-spacing:-.02em;font-variant-numeric:tabular-nums}
.rp-kr{font-size:13px;font-weight:700;margin-top:6px}
.rp-kd{font-size:11.5px;color:var(--ink-3);margin-top:2px;line-height:1.3}
.rp-bar{height:6px;border-radius:999px;background:var(--surface-2);margin-top:9px;overflow:hidden}
.rp-bar i{display:block;height:100%;border-radius:999px;background:var(--kc);opacity:.9}
.rp-kg-hero .rp-k{background:linear-gradient(135deg,color-mix(in srgb,var(--accent-ink) 10%,var(--surface)),var(--surface));--kc:var(--accent-ink)}
/* configuracoes */
.rp-cfg{background:var(--surface);border:1px dashed var(--border);border-radius:var(--rad);padding:10px 14px;margin:0 0 18px}
.rp-cfg summary{cursor:pointer;font-weight:600;color:var(--ink-2);font-size:14px}
.rp-f1{display:block;margin-top:10px}.rp-f1 span{display:block;font-size:12.5px;color:var(--ink-3);margin-bottom:4px}
.rp-f1 input{width:100%;box-sizing:border-box;padding:10px 12px;font-size:15px;border:1px solid var(--border);border-radius:10px;background:var(--surface);color:var(--ink)}
/* blocos de contato */
.rp-s{--tc:#6b7280;background:var(--surface);border:1px solid var(--border);border-radius:var(--rad);margin:0 0 16px;box-shadow:var(--sombra);overflow:hidden}
.rp-t-renovar{--tc:#e5484d}.rp-t-poucos{--tc:#f5a524}.rp-t-aniv{--tc:#e93d82}.rp-t-pos{--tc:#7c5cfa}.rp-t-resg{--tc:#f76808}
.rp-t-retlem,.rp-t-retatr{--tc:#8e4ec6}.rp-t-retpkg{--tc:#12a594}.rp-t-retnunca{--tc:#6e56cf}.rp-t-consulta{--tc:#0090ff}.rp-t-env{--tc:#30a46c}
.rp-sh{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:14px 16px 4px;border-top:4px solid var(--tc);background:linear-gradient(color-mix(in srgb,var(--tc) 9%,var(--surface)),var(--surface))}
.rp-sh h3{margin:0;font-size:16.5px;font-weight:800;letter-spacing:-.01em}
.rp-n{min-width:28px;text-align:center;padding:3px 10px;border-radius:999px;background:var(--tc);color:#fff;font-size:12.5px;font-weight:800}
.rp-sub{color:var(--ink-3);font-size:12.8px;line-height:1.4;padding:0 16px 10px}
.rp-lst{padding:0 6px 6px}
.rp-vazio{color:var(--ink-3);padding:14px 12px 16px;font-size:14px}
/* linha de cliente */
.rp-l{display:grid;grid-template-columns:44px 1fr auto;gap:12px;align-items:center;padding:11px 10px;border-radius:12px;transition:background .12s}
.rp-l+.rp-l{border-top:1px solid color-mix(in srgb,var(--border) 70%,transparent)}
.rp-l:hover{background:var(--surface-2)}
.rp-av{width:44px;height:44px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:15px;background:hsl(var(--h) 65% 55% / .2);color:var(--ink);letter-spacing:.02em}
.rp-t{min-width:0}
.rp-nm{font-weight:700;font-size:15.5px;line-height:1.25;overflow:hidden;text-overflow:ellipsis}
.rp-d{color:var(--ink-2);font-size:13px;line-height:1.4;margin-top:2px}.rp-d strong{color:var(--ink)}
.rp-a{display:flex;gap:8px;flex-wrap:wrap;justify-content:flex-end;align-items:center}
.rp-b{display:inline-flex;align-items:center;gap:6px;padding:9px 15px;border-radius:999px;font-size:13.5px;font-weight:700;text-decoration:none;border:1px solid transparent;cursor:pointer;white-space:nowrap;line-height:1.1;transition:transform .08s,filter .12s}
.rp-b:active{transform:scale(.97)}
.rp-wa{background:#1fa855;color:#fff;box-shadow:0 2px 8px rgba(31,168,85,.3)}.rp-wa:hover{filter:brightness(1.06)}
.rp-ok{background:transparent;color:var(--ink-2);border-color:var(--border)}.rp-ok:hover{background:var(--surface-2)}
.rp-off{background:var(--surface-2);color:var(--ink-3);cursor:default;font-weight:600;white-space:normal}
.rp-env{flex-basis:100%;white-space:normal;line-height:1.35;text-align:right;font-size:12px;font-weight:700;color:#1e8a45;background:color-mix(in srgb,#1e8a45 12%,transparent);padding:4px 10px;border-radius:999px;align-self:center}
.rp-env a{color:var(--ink-3);font-weight:500}
.rp-l:has(.rp-env){opacity:.72}
.rp-sf{color:#b7791f}
.rp-cb{margin:6px 0 0;font-size:13px}.rp-cb summary{cursor:pointer;color:var(--accent-ink);font-weight:700}.rp-cb ul{margin:6px 0;padding-left:18px;color:var(--ink-2)}
/* ver todas */
.rp-mais{margin:4px 6px 8px}
.rp-mais summary{cursor:pointer;list-style:none;text-align:center;padding:10px;border-radius:12px;background:var(--surface-2);color:var(--ink-2);font-weight:700;font-size:13.5px}
.rp-mais summary::-webkit-details-marker{display:none}.rp-mais summary:hover{background:color-mix(in srgb,var(--tc) 12%,var(--surface-2))}
.rp-mais[open] summary{margin-bottom:6px}
.rp-mais[open] summary::after{content:" · recolher"}
@media(max-width:640px){
 #recepcao-app{font-size:14.5px}.rp-top h2{font-size:21px}
 .rp-kw{grid-template-columns:repeat(2,1fr)}.rp-kv{font-size:25px}
 .rp-l{grid-template-columns:40px 1fr;row-gap:8px}.rp-av{width:40px;height:40px;font-size:14px}
 .rp-a{grid-column:1 / -1;justify-content:flex-start;padding-left:52px}.rp-env{text-align:left}
 .rp-b{padding:10px 16px}
}
`;
  document.head.appendChild(css);

  document.addEventListener('recepcao-dados', function (ev) { DADOS = ev.detail; desenhar(); });
  document.addEventListener('recepcao-pacotes', function (ev) { PACOTES = ev.detail; desenhar(); });
  document.addEventListener('click', function (ev) { if (ev.target.closest && ev.target.closest('.unid-btn')) setTimeout(desenhar, 80); });
})();
