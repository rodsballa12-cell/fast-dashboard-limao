// Gera os três modelos vazios do kit: node docs/marketing/modelos/gerar_modelos.js
const path = require('path');
const K = require('./kit');
const { t, b, it } = K;
const exemplo = (pele, nome) => [
  K.p('Parágrafo de corpo. Escreva aqui o texto do documento, em frases curtas e diretas.', pele),
  K.secao('1 · Título de seção', pele),
  K.p([b('Destaque em negrito. '), t('Texto normal na sequência.')], pele),
  K.lista([b('Item de lista: '), t('use para regras e condições.')], pele),
  K.lista('Segundo item.', pele),
  K.sub('Subtítulo de bloco', pele),
  K.tabela([4026, 2500, 2500], [
    ['COLUNA', 'VALOR', 'OBSERVAÇÃO'],
    ['Linha 1', 'R$ 0', '—'], ['Linha 2', 'R$ 0', '—'], ['Total', 'R$ 0', ''],
  ], { pele, total: true }),
  K.p([it('Legenda ou nota de rodapé de tabela.')], pele),
];
const peles = [['escova', 'FAST Escova Limão'], ['spa', 'FAST Spa Limão'], ['consolidado', 'FAST Limão · Escova e Spa']];
Promise.all(peles.map(([pele, nome]) => K.salvar(
  K.documento({ pele, rotulo: nome + ' · tipo de documento · mês de ano', titulo: 'Título do documento', subtitulo: 'Subtítulo opcional', blocos: exemplo(pele, nome) }),
  path.join(__dirname, `modelo-${pele}.docx`),
))).then(() => console.log('modelos gerados'));
