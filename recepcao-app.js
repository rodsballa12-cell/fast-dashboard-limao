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
    escova: { nome: '', google: '', brRen: '', brResg: 'uma Nutrição Capilar', brAniv: 'uma Hidratação com Ozonioterapia', brAmiga: 'uma Ozonioterapia' },
    spa: { nome: '', google: '', brRen: '', brResg: '', brAniv: '', brAmiga: '' }
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
  function msgRenovar(u, c, p, total) {
    var n = primeiro(p.cliente), L = LOJAS[u];
    var resta = total + (total === 1 ? ' serviço restante' : ' serviços restantes');
    return 'Oi ' + n + '! Tudo bem?\n\nPassando para te avisar que o seu pacote de ' + bonito(p.pacote) + ' está terminando. Você tem apenas ' + resta + '.\n\n' +
      'Como sabemos que sua rotina é super corrida e você não abre mão da praticidade da Fast, já deixei tudo engatilhado para sua renovação. Assim, você garante que seu crédito de beleza esteja sempre ativo para quando você precisar chegar e ser atendida rapidinho.\n\n' +
      (c.brRen ? 'Na renovação deste mês, você ganha ' + c.brRen + ' de presente na primeira ' + (u === 'escova' ? 'escova' : 'sessão') + ' do novo pacote. ' : '') +
      'Vamos garantir sua tranquilidade?';
  }
  function msgResgate(u, c, cli) {
    var n = primeiro(cli.cliente), L = LOJAS[u];
    var mimo = c.brResg ? "Preparamos um 'Mimo de Retorno' exclusivo para você: ao realizar qualquer serviço nesta semana, você ganha " + c.brResg + '.\n' : '';
    if (u === 'escova') {
      return 'Olá, ' + n + '! Sentimos sua falta por aqui!\n\nSua última visita já faz um tempinho e seu cabelo deve estar sentindo falta daquele brilho que só a nossa finalização entrega. ' + mimo + 'Vamos renovar esse visual hoje?';
    }
    return 'Olá, ' + n + '! Sentimos sua falta por aqui!\n\nSua última visita ao ' + L.nome + ' já faz um tempinho. ' + mimo + 'Vamos cuidar de você hoje?';
  }
  function msgAniv(u, c, a) {
    var n = primeiro(a.cliente), L = LOJAS[u];
    var abre = a.dias === 0 ? 'Hoje o dia é todo seu' : 'Seu aniversário está chegando';
    var corpo;
    if (u === 'escova' && c.brAniv) {
      corpo = 'Sabemos que no seu aniversário você quer estar ainda mais maravilhosa, por isso preparamos um presente especial: na sua visita de aniversário, ao realizar sua Escova, você ganha ' + c.brAniv + ' para sair daqui pronta para comemorar! 💄✨' +
        (c.brAmiga ? '\nE tem mais: se você quiser trazer uma amiga para se produzir com você, ela ganha ' + c.brAmiga + ' de presente.' : '');
    } else {
      corpo = c.brAniv ? 'Preparamos um presente especial: na sua visita de aniversário, você ganha ' + c.brAniv + '!' : 'Venha comemorar com a gente!';
    }
    return 'Oi, ' + n + '! Tudo bem?\n' + abre + ' e a equipe do ' + L.nome + ' quer celebrar com você! 🎉\n' + corpo + '\nNão precisa de hora marcada, é só chegar' + (u === 'escova' ? ' e brilhar' : '') + '! Parabéns' + (a.dias === 0 ? ' pelo seu dia' : ' antecipado') + '!';
  }
  function msgPos1(u, c, cli) {
    var n = primeiro(cli.cliente), L = LOJAS[u];
    return 'Oi, ' + n + '! Aqui é a ' + (c.nome || 'equipe') + ' da ' + L.nome + '.\nPassando para agradecer a confiança no nosso trabalho ontem! Esperamos que tenha amado a experiência.\n' +
      'Se puder, nos conte o que achou: sua opinião ajuda nossa equipe a ser cada vez melhor! Ah, e se tirou aquela foto incrível, marca a gente no Instagram (@' + L.ig + '), queremos te ver brilhar! ✨ Até a próxima!';
  }
  function msgPos2(u, c) {
    return 'Ficamos muito felizes que você gostou do atendimento!\nNossa missão é valorizar o seu tempo com resultados incríveis.\nVocê poderia dedicar 30 segundinhos para nos avaliar no Google?\nSua avaliação ajuda outras pessoas a nos encontrarem!\nClique aqui para avaliar: ' + c.google;
  }

  // Retoque (documento "Gestão de clientes Fast Retoque", da diretora comercial)
  function msgRetoque(u, c, x) {
    return 'Olá ' + primeiro(x.cliente) + '! Passando para lembrar que sua raiz está no ponto ideal para o Fast Retoque. Para te incentivar a manter o brilho, se você vier entre hoje e amanhã, sua Hidratação é por nossa conta. É só apresentar esta mensagem na recepção.';
  }
  function msgRetoquePacote(u, c, x) {
    return 'Oi, ' + primeiro(x.cliente) + '! Vi que você é super certinha com o seu Fast Retoque. Pensando em clientes fiéis como você, temos o Pacote de Fast Retoque: fechando 4 retoques (que você já faria de qualquer jeito), você ganha 2 Hidratações de presente. Quer que eu deixe separado para você?';
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
  function linha(u, tipo, cliente, detalhe, acoes, extra, chave) {
    chave = chave || cliente;
    var f = feito(u, tipo, chave);
    return '<div class="rp-l' + (f ? ' rp-f' : '') + '"><div class="rp-t"><label><input type="checkbox" class="rp-ck" data-k="' + esc(u + '_' + tipo + '_' + chave) + '"' + (f ? ' checked' : '') + '> <strong>' + esc(bonito(cliente)) + '</strong></label>' +
      '<div class="rp-d">' + detalhe + '</div>' + (extra || '') + '</div><div class="rp-a">' + acoes + '</div></div>';
  }
  var ABERTO = {}; // lembra o que a recepcao expandiu
  var VISIVEIS = 5; // quantas ficam a vista em cada tema; o resto abre em "Ver todas"
  function bloco(id, titulo, sub, itens, vazio, vis) {
    if (vis == null) vis = VISIVEIS;
    var corpo = itens.length ? itens.slice(0, vis).join('') : '<div class="rp-vazio">' + vazio + '</div>';
    var resto = itens.length > vis ? '<details class="rp-mais" data-id="' + id + '"' + (ABERTO[id] ? ' open' : '') + '><summary>Ver todas (' + itens.length + ')</summary>' + itens.slice(vis).join('') + '</details>' : '';
    return '<section class="rp-s" id="rp-' + id + '"><h3>' + titulo + ' <span class="rp-n">' + itens.length + '</span></h3><div class="rp-sub">' + sub + '</div>' + corpo + resto + '</section>';
  }
  function pct(v) { return v == null ? '–' : String(v).replace('.', ',') + '%'; }
  function num(v) { return v == null ? '–' : Number(v).toLocaleString('pt-BR'); }
  function tile(rot, val, dica, tom) { return '<div class="rp-k' + (tom ? ' rp-k-' + tom : '') + '"><div class="rp-kv">' + val + '</div><div class="rp-kr">' + rot + '</div><div class="rp-kd">' + dica + '</div></div>'; }
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
      (g4 ? '<div class="rp-kg"><h3>📲 Leads dos anúncios (Meta)</h3><div class="rp-kw">' + g4 + '</div></div>' : '');
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
      var b2 = c.google ? botoes('', 'pos2', x.cliente, x.telefone, msgPos2(u, c), '2ª: avaliação Google') : '<span class="rp-b rp-off" title="Preencha o link do Google em Meus dados">2ª: falta o link do Google</span>';
      return linha(u, 'pos', x.cliente, 'atendida ' + (x.dia ? (x.dia === ontemISO() ? 'ontem' : 'em ' + dataBR(x.dia).slice(0, 5)) : 'ontem') + fone(x.telefone) + ' · envie a 2ª só se a resposta da 1ª for positiva', b1 + b2);
    });

    // consulta de qualquer cliente da base (a partir de 3 letras)
    var consulta = [];
    if (qn.length >= 3) {
      consulta = (D.base || []).filter(function (x) { return x.n.toLowerCase().indexOf(qn) >= 0; }).slice(0, 15).map(function (x) {
        var pk = ((PACOTES && PACOTES[u]) || []).filter(function (p) { return p.cliente.split(/\s+/).join(' ').toLowerCase() === x.n.toLowerCase(); });
        var pt = pk.length ? pk.map(function (p) { return esc(bonito(p.pacote)) + ': ' + p.itens.map(function (it) { return '<strong>' + it.restante + '</strong> × ' + esc(bonito(it.servico)); }).join(', '); }).join(' | ') : 'sem pacote com saldo';
        var det = pt + (x.a ? ' · aniversário ' + esc(x.a) : '') + fone(x.t);
        return linha(u, 'consulta', x.n, det, botoes('', 'consulta', x.n, x.t, 'Oi, ' + primeiro(x.n) + '! Tudo bem?', 'Abrir WhatsApp'));
      });
    }
    // lista completa da base (ordem alfabetica), com saldo de pacote e aniversario
    var pmap = {};
    ((PACOTES && PACOTES[u]) || []).forEach(function (p) { var k = p.cliente.split(/\s+/).join(' ').toLowerCase(); (pmap[k] = pmap[k] || []).push(p); });
    var todos = (D.base || []).filter(function (x) { return pass(x.n); }).map(function (x) {
      var pk = pmap[x.n.toLowerCase()] || [];
      var pt = pk.length ? pk.map(function (p) { return esc(bonito(p.pacote)) + ': ' + p.itens.map(function (it) { return '<strong>' + it.restante + '</strong> × ' + esc(bonito(it.servico)); }).join(', '); }).join(' | ') : '';
      var det = [pt, x.a ? 'aniversário ' + esc(x.a) : ''].filter(Boolean).join(' · ') || '&nbsp;';
      return linha(u, 'consulta', x.n, det, botoes('', 'consulta', x.n, x.t, 'Oi, ' + primeiro(x.n) + '! Tudo bem?', 'WhatsApp'));
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
      '<input id="rp-busca" type="search" placeholder="🔎 Cliente chegou? Digite o nome…" value="' + esc(q) + '">' +
      '<details class="rp-cfg"><summary>⚙️ Meus dados e brindes (ficam só neste aparelho)</summary>' +
      inputCfg('nome', 'Seu nome (assina o pós-venda)', c.nome, 'ex.: Ana') +
      inputCfg('google', 'Link de avaliação do Google da loja', c.google, 'cole o link') +
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
  css.textContent =
    '#tab-clientes > :not(#recepcao-app){display:none!important}' +
    '#recepcao-app{font-size:15px}' +
    '.rp-top h2{margin:0 0 4px;font-size:20px}.rp-meta{color:var(--ink-3);font-size:12.5px;margin-bottom:10px}' +
    '#rp-busca{width:100%;box-sizing:border-box;padding:12px 14px;font-size:17px;border:2px solid var(--border);border-radius:10px;background:var(--surface);color:var(--ink);margin-bottom:10px}' +
    '.rp-cfg{background:var(--surface-2);border-radius:10px;padding:10px 12px;margin-bottom:14px}.rp-cfg summary{cursor:pointer;font-weight:600}' +
    '.rp-f1{display:block;margin-top:10px}.rp-f1 span{display:block;font-size:12.5px;color:var(--ink-3);margin-bottom:3px}.rp-f1 input{width:100%;box-sizing:border-box;padding:9px 10px;font-size:15px;border:1px solid var(--border);border-radius:8px;background:var(--surface);color:var(--ink)}' +
    '.rp-s{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:14px;margin-bottom:14px}.rp-s summary{cursor:pointer;list-style:none;font-size:17px;font-weight:700;padding:2px 0}.rp-s summary::-webkit-details-marker{display:none}.rp-s summary::before{content:\"▸ \";color:var(--ink-3)}.rp-s[open] summary::before{content:\"▾ \"}.rp-n{background:var(--surface-2);border-radius:20px;padding:1px 10px;font-size:13px;margin-left:6px}' +
    '.rp-sub{color:var(--ink-3);font-size:13px;margin:4px 0 8px}.rp-vazio{color:var(--ink-3);padding:8px 0}' +
    '.rp-l{display:flex;gap:10px;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;padding:11px 0;border-top:1px solid var(--border)}.rp-l.rp-f{opacity:.45}' +
    '.rp-t{flex:1 1 240px;min-width:0}.rp-t label{cursor:pointer;font-size:16px}.rp-t input[type=checkbox]{width:20px;height:20px;vertical-align:-4px}.rp-env{flex-basis:100%;font-size:13px;color:#1e7e34;font-weight:600}.rp-env a{color:var(--ink-3);font-weight:500}.rp-ok{background:#e7f6ec;color:#1e7e34;border:1px solid #b7e1c4}.rp-mais{margin-top:6px}.rp-kg{margin:0 0 12px}.rp-kg h3{margin:0 0 6px;font-size:15px}.rp-kw{display:grid;grid-template-columns:repeat(auto-fill,minmax(138px,1fr));gap:8px}.rp-k{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:10px 12px}.rp-kv{font-size:22px;font-weight:800;line-height:1.1}.rp-kr{font-size:13px;font-weight:600;margin-top:2px}.rp-kd{font-size:11.5px;color:var(--ink-3)}.rp-k-ok{border-left:4px solid #1e9e4a}.rp-k-at{border-left:4px solid #e0a100}.rp-k-ruim{border-left:4px solid #c0392b}.rp-sf{color:#b7791f}.rp-d{color:var(--ink-2);font-size:13.5px;margin:2px 0 0 28px}' +
    '.rp-a{display:flex;gap:8px;flex-wrap:wrap}.rp-b{display:inline-block;padding:10px 14px;border-radius:9px;font-size:14.5px;font-weight:600;text-decoration:none;border:0;cursor:pointer;white-space:nowrap}' +
    '.rp-wa{background:#25D366;color:#06260f}.rp-cp{background:var(--surface-2);color:var(--ink);border:1px solid var(--border)}.rp-off{background:var(--surface-2);color:var(--ink-3);cursor:default;font-weight:500;white-space:normal}' +
    '.rp-cb,.rp-mais{margin:6px 0 0 28px;font-size:13.5px}.rp-cb summary,.rp-mais summary{cursor:pointer;color:var(--ink-2);font-weight:600}.rp-cb ul{margin:6px 0;padding-left:18px}' +
    '.rp-mais{margin-left:0}';
  document.head.appendChild(css);

  document.addEventListener('recepcao-dados', function (ev) { DADOS = ev.detail; desenhar(); });
  document.addEventListener('recepcao-pacotes', function (ev) { PACOTES = ev.detail; desenhar(); });
  document.addEventListener('click', function (ev) { if (ev.target.closest && ev.target.closest('.unid-btn')) setTimeout(desenhar, 80); });
})();
