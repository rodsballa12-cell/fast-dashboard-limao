// Kit de documentos FAST Limão: Escova, Spa e Consolidado.
// Os números (cores, tamanhos, margens) estão em ../FICHA-DOCUMENTOS.md.
// Uso: const K = require('./kit'); K.salvar(K.documento({pele:'consolidado', ...}), 'saida.docx')
const fs = require('fs');
const path = require('path');
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, Footer,
  WidthType, ShadingType, AlignmentType, BorderStyle, LevelFormat, HeadingLevel, VerticalAlign,
} = require('docx');

const MARCA = path.join(__dirname, '..', 'marca');
const FONTE = 'Montserrat';

// Cores lidas dos arquivos oficiais de logo (pixel), não de memória.
const COR = {
  amarelo: 'FBD300', amareloClaro: 'FFF6C2', preto: '000000',
  agua: '00A6A4', aguaEscuro: '006C6B', aguaClaro: 'DFF5F4',
  grafite: '2B3133', cinza: '5B6568', cinzaClaro: 'F2F3F3', branco: 'FFFFFF',
};

const PELE = {
  escova:      { cab: COR.preto,   cabTxt: COR.branco, total: COR.amareloClaro, barra: COR.amarelo, titulo: COR.preto,      txt: COR.preto,   rodape: ['@fastescova.limao'] },
  spa:         { cab: COR.agua,    cabTxt: COR.branco, total: COR.aguaClaro,    barra: COR.agua,    titulo: COR.aguaEscuro, txt: COR.grafite, rodape: ['@fastspa.limao'] },
  consolidado: { cab: COR.grafite, cabTxt: COR.branco, total: COR.cinzaClaro,   barra: COR.grafite, titulo: COR.grafite,    txt: COR.grafite, rodape: ['@fastescova.limao', '@fastspa.limao'] },
};

// Tamanhos em pontos (docx usa meio-ponto: multiplicar por 2).
const PT = { titulo: 24, secao: 13, sub: 11, corpo: 10.5, tabela: 9.5, legenda: 9, rodape: 8, rotulo: 8.5 };
const hp = (pt) => Math.round(pt * 2);

const LARG = 9026; // largura útil A4 com margens de 1440
const semBorda = { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' };
const bordaFina = { style: BorderStyle.SINGLE, size: 4, color: 'DADDDD' };

function logo(arquivo, largura) {
  const f = path.join(MARCA, arquivo + '.png');
  const buf = fs.readFileSync(f);
  // PNG: largura e altura nos bytes 16-23
  const w = buf.readUInt32BE(16), h = buf.readUInt32BE(20);
  return new ImageRun({ type: 'png', data: buf, transformation: { width: largura, height: Math.round(largura * h / w) } });
}

function faixaLogo(arquivo, fundo, largura, larguraCelula) {
  return new TableCell({
    width: { size: larguraCelula, type: WidthType.DXA },
    shading: { type: ShadingType.CLEAR, color: 'auto', fill: fundo },
    verticalAlign: VerticalAlign.CENTER,
    margins: { top: 260, bottom: 260, left: 240, right: 240 },
    borders: { top: semBorda, bottom: semBorda, left: semBorda, right: semBorda },
    children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [logo(arquivo, largura)] })],
  });
}

function cabecalho(pele) {
  const cells = pele === 'escova' ? [faixaLogo('fastescova-claro', COR.preto, 210, LARG)]
    : pele === 'spa' ? [faixaLogo('fastspa-branco', COR.agua, 210, LARG)]
    : [faixaLogo('fastescova-claro', COR.preto, 170, LARG / 2), faixaLogo('fastspa-branco', COR.agua, 170, LARG / 2)];
  return new Table({
    width: { size: LARG, type: WidthType.DXA },
    columnWidths: cells.length === 1 ? [LARG] : [LARG / 2, LARG / 2],
    rows: [new TableRow({ children: cells })],
  });
}

function rodape(pele) {
  const P = PELE[pele];
  const runs = [new TextRun({ text: 'SEM HORA MARCADA', font: FONTE, bold: true, size: hp(PT.rodape), color: P.txt, characterSpacing: 20 })];
  for (const r of P.rodape) runs.push(new TextRun({ text: '   ·   ' + r, font: FONTE, size: hp(PT.rodape), color: COR.cinza }));
  return new Footer({ children: [new Paragraph({
    alignment: AlignmentType.CENTER,
    border: { top: { style: BorderStyle.SINGLE, size: 6, color: P.barra, space: 6 } },
    children: runs,
  })] });
}

// ---- blocos de texto -------------------------------------------------------
const run = (t, o = {}) => new TextRun({ text: t, font: FONTE, size: hp(PT.corpo), ...o });
const K = {
  COR, PELE, PT,
  t: (t) => run(t),
  b: (t) => run(t, { bold: true }),
  it: (t) => run(t, { italics: true, color: COR.cinza, size: hp(PT.legenda) }),
  hl: (t) => run(t, { bold: true, highlight: 'yellow' }),

  p(conteudo, pele = 'consolidado') {
    const arr = (Array.isArray(conteudo) ? conteudo : [conteudo]).map((x) => typeof x === 'string' ? run(x, { color: PELE[pele].txt }) : x);
    return new Paragraph({ spacing: { after: 120, line: 288 }, children: arr });
  },
  rotulo(t, pele = 'consolidado') {
    return new Paragraph({ spacing: { after: 40 }, children: [run(t.toUpperCase(), { bold: true, size: hp(PT.rotulo), color: pele === 'spa' ? COR.agua : COR.cinza, characterSpacing: 40 })] });
  },
  titulo(t, pele = 'consolidado') {
    return new Paragraph({ spacing: { after: 100 }, children: [run(t.toUpperCase(), { bold: true, size: hp(PT.titulo), color: PELE[pele].titulo, characterSpacing: 10 })] });
  },
  // Seção: título caixa alta espaçado, filete na cor da pele.
  secao(t, pele = 'consolidado') {
    return new Paragraph({
      heading: HeadingLevel.HEADING_1, spacing: { before: 340, after: 140 },
      border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: PELE[pele].barra, space: 4 } },
      children: [run(t.toUpperCase(), { bold: true, size: hp(PT.secao), color: PELE[pele].titulo, characterSpacing: 30 })],
    });
  },
  // Subtítulo de bloco de loja: barra lateral na cor da loja.
  sub(t, pele = 'consolidado') {
    return new Paragraph({
      heading: HeadingLevel.HEADING_2, spacing: { before: 220, after: 100 },
      border: { left: { style: BorderStyle.SINGLE, size: 28, color: PELE[pele].barra, space: 8 } },
      children: [run(t, { bold: true, size: hp(PT.sub), color: PELE[pele].titulo })],
    });
  },
  lista(conteudo, pele = 'consolidado') {
    const arr = (Array.isArray(conteudo) ? conteudo : [conteudo]).map((x) => typeof x === 'string' ? run(x, { color: PELE[pele].txt }) : x);
    return new Paragraph({ numbering: { reference: 'fast-lista', level: 0 }, spacing: { after: 80, line: 276 }, children: arr });
  },
  espaco: () => new Paragraph({ spacing: { after: 80 }, children: [] }),

  // Tabela: cabeçalho na cor da pele, zebra suave, última linha destacada se total=true.
  // Célula pode ser string ou {hl:'texto'} para campo a preencher.
  tabela(larguras, linhas, { pele = 'consolidado', total = false } = {}) {
    const P = PELE[pele];
    const soma = larguras.reduce((a, b) => a + b, 0);
    return new Table({
      width: { size: soma, type: WidthType.DXA }, columnWidths: larguras,
      rows: linhas.map((l, i) => new TableRow({ tableHeader: i === 0, cantSplit: true, children: l.map((c, j) => {
        const cab = i === 0, tot = total && i === linhas.length - 1;
        const conteudo = c && c.hl
          ? run(c.hl, { bold: true, highlight: 'yellow', size: hp(PT.tabela) })
          : run(String(c), { bold: cab || tot, size: hp(PT.tabela), color: cab ? P.cabTxt : P.txt, characterSpacing: cab ? 10 : 0 });
        return new TableCell({
          width: { size: larguras[j], type: WidthType.DXA },
          borders: { top: bordaFina, bottom: bordaFina, left: semBorda, right: semBorda },
          shading: { type: ShadingType.CLEAR, color: 'auto', fill: cab ? P.cab : tot ? P.total : (i % 2 ? COR.branco : 'F8F9F9') },
          margins: { top: 90, bottom: 90, left: 130, right: 130 }, verticalAlign: VerticalAlign.CENTER,
          children: [new Paragraph({ alignment: j === 0 ? AlignmentType.LEFT : AlignmentType.CENTER, children: [conteudo] })],
        });
      }) })),
    });
  },

  documento({ pele = 'consolidado', rotulo = '', titulo, subtitulo = '', blocos = [] }) {
    if (!PELE[pele]) throw new Error('pele deve ser escova, spa ou consolidado');
    return new Document({
      styles: { default: { document: { run: { font: FONTE, size: hp(PT.corpo) } } } },
      numbering: { config: [{ reference: 'fast-lista', levels: [{ level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 500, hanging: 260 } }, run: { color: PELE[pele].barra } } }] }] },
      sections: [{
        properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1000, bottom: 1100, left: 1440, right: 1440 } } },
        footers: { default: rodape(pele) },
        children: [
          cabecalho(pele),
          new Paragraph({ spacing: { after: 160 }, children: [] }),
          ...(rotulo ? [K.rotulo(rotulo, pele)] : []),
          K.titulo(titulo, pele),
          ...(subtitulo ? [new Paragraph({ spacing: { after: 200 }, children: [K.it(subtitulo)] })] : []),
          ...blocos,
        ],
      }],
    });
  },

  salvar(doc, arquivo) {
    return Packer.toBuffer(doc).then((buf) => fs.writeFileSync(arquivo, buf));
  },
};

module.exports = K;
