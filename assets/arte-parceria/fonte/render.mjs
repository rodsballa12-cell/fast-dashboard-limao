import { chromium } from 'playwright';
import fs from 'fs';
const [,, mode, ...args] = process.argv;
const b = await chromium.launch();
const jobs = JSON.parse(fs.readFileSync(args[0], 'utf8'));
for (const j of jobs) {
  const svg = fs.readFileSync(j.svg, 'utf8');
  const p = await b.newPage({ viewport: { width: j.w, height: j.h },
                              deviceScaleFactor: 1 });
  const css = j.pdf
    ? `@page{size:${j.cm_w}cm ${j.cm_h}cm;margin:0}html,body{margin:0;padding:0}
       svg{width:${j.cm_w}cm;height:${j.cm_h}cm;display:block}`
    : `html,body{margin:0;padding:0;background:transparent}
       svg{width:${j.w}px;height:${j.h}px;display:block}`;
  await p.setContent(`<style>${css}</style>${svg}`);
  if (j.pdf) await p.pdf({ path: j.out, preferCSSPageSize: true, printBackground: true });
  else await p.screenshot({ path: j.out, omitBackground: !!j.transparent });
  await p.close();
  console.log('ok', j.out);
}
await b.close();
