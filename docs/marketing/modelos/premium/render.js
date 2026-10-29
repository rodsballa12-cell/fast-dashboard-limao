// HTML do padrão premium → PDF A4 (e PNG de prévia por página, opcional).
// Uso: node docs/marketing/modelos/premium/render.js entrada.html saida.pdf [pasta_previas]
const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const [entrada, saida, previas] = process.argv.slice(2);
  if (!entrada || !saida) { console.error('uso: render.js entrada.html saida.pdf [pasta_previas]'); process.exit(1); }
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 794, height: 1123 }, deviceScaleFactor: 2 });
  await page.goto('file://' + path.resolve(entrada), { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts.ready);
  const fonte = await page.evaluate(() => [...document.fonts].some((f) => f.family.includes('Montserrat') && f.status === 'loaded'));
  if (!fonte) console.warn('AVISO: Montserrat não carregou; o PDF sairá em fonte substituta.');
  await page.pdf({ path: saida, format: 'A4', printBackground: true, preferCSSPageSize: true });
  if (previas) {
    const n = await page.locator('.pagina').count();
    for (let i = 0; i < n; i++) await page.locator('.pagina').nth(i).screenshot({ path: path.join(previas, `pagina-${i + 1}.png`) });
  }
  await browser.close();
  console.log('ok', saida);
})();
