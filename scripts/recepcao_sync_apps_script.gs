/**
 * Registro compartilhado de mensagens enviadas da recepcao FAST Limao.
 * Cole este codigo em Extensoes > Apps Script de uma PLANILHA NOVA do Google
 * (so a recepcao deve ter acesso a ela: ela guarda nomes de clientes).
 *
 * Antes de publicar:
 *   Configuracoes do projeto > Propriedades do script > Adicionar:  TOKEN = <o token que o Claude entregar>
 * Publicar:
 *   Implantar > Nova implantacao > Tipo: App da Web
 *   Executar como: Eu   ·   Quem tem acesso: Qualquer pessoa
 * Copie o endereco da implantacao (termina em /exec) e entregue ao Claude.
 * O token e conferido em TODA chamada; sem ele, nada e lido nem gravado.
 */
var ABA = 'registro';

function aba_() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sh = ss.getSheetByName(ABA);
  if (!sh) {
    sh = ss.insertSheet(ABA);
    sh.appendRow(['chave', 'quando (ISO)', 'cliente', 'tipo', 'marcado por', 'desfeito']);
    sh.setFrozenRows(1);
  }
  return sh;
}

function saida_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}

function token_() {
  return PropertiesService.getScriptProperties().getProperty('TOKEN');
}

function doGet(e) {
  if (!token_() || (e.parameter && e.parameter.token) !== token_()) return saida_({ ok: false, erro: 'token' });
  var vals = aba_().getDataRange().getValues();
  var corte = Date.now() - 60 * 86400000, reg = {};
  for (var i = 1; i < vals.length; i++) {
    var r = vals[i];
    if (!r[0] || new Date(r[1]).getTime() < corte) continue;
    reg[r[0]] = { t: r[1], n: r[2], tp: r[3], por: r[4], x: r[5] ? 1 : 0 };
  }
  return saida_({ ok: true, registros: reg });
}

function doPost(e) {
  var body;
  try { body = JSON.parse(e.postData.contents); } catch (err) { return saida_({ ok: false, erro: 'json' }); }
  if (!token_() || body.token !== token_()) return saida_({ ok: false, erro: 'token' });
  var lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    var sh = aba_(), vals = sh.getDataRange().getValues(), linha = {};
    for (var i = 1; i < vals.length; i++) linha[vals[i][0]] = i + 1;
    (body.itens || []).forEach(function (it) {
      var rec = it.rec || {}, row = [it.key, rec.t, rec.n || '', rec.tp || '', rec.por || '', rec.x ? 'sim' : ''];
      if (linha[it.key]) {
        var atual = sh.getRange(linha[it.key], 2).getValue();
        if (new Date(rec.t).getTime() >= new Date(atual).getTime()) sh.getRange(linha[it.key], 1, 1, 6).setValues([row]);
      } else {
        sh.appendRow(row);
        linha[it.key] = sh.getLastRow();
      }
    });
  } finally {
    lock.releaseLock();
  }
  return saida_({ ok: true });
}
