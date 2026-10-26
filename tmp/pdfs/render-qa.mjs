import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import {createRequire} from 'node:module';
import {pathToFileURL} from 'node:url';

const runtime = path.join(os.tmpdir(), 'oop-book-reference-tools');
const require = createRequire(path.join(runtime, 'package.json'));
const canvasLib = require('@napi-rs/canvas');
for (const k of ['DOMMatrix', 'ImageData', 'Path2D']) globalThis[k] = canvasLib[k];
const pdfjs = await import(pathToFileURL(path.join(runtime, 'node_modules/pdfjs-dist/legacy/build/pdf.mjs')));
pdfjs.GlobalWorkerOptions.workerSrc = pathToFileURL(path.join(runtime, 'node_modules/pdfjs-dist/legacy/build/pdf.worker.mjs')).href;

for (const file of process.argv.slice(2)) {
  const base = path.basename(file, '.pdf');
  const dir = path.join(path.dirname(file), base + '-qa');
  fs.mkdirSync(dir, {recursive:true});
  const task = pdfjs.getDocument({data:new Uint8Array(fs.readFileSync(file)), isEvalSupported:false, verbosity:0});
  const doc = await task.promise;
  const index = [];
  const thumbs = [];
  for (let n=1;n<=doc.numPages;n++) {
    const page = await doc.getPage(n);
    const content = await page.getTextContent();
    const text = content.items.map(i=>i.str).join(' ');
    index.push({page:n,text});
    const viewport = page.getViewport({scale:1.25});
    const canvas = canvasLib.createCanvas(Math.ceil(viewport.width), Math.ceil(viewport.height));
    await page.render({canvasContext:canvas.getContext('2d'), viewport}).promise;
    fs.writeFileSync(path.join(dir, `page-${n}.png`), canvas.toBuffer('image/png'));
    thumbs.push(canvas);
  }
  for (let start=0;start<thumbs.length;start+=12) {
    const sheet=canvasLib.createCanvas(900, 4*447);
    const ctx=sheet.getContext('2d'); ctx.fillStyle='#ddd';ctx.fillRect(0,0,sheet.width,sheet.height);
    for(let i=start;i<Math.min(start+12,thumbs.length);i++) {
      const col=(i-start)%3, row=Math.floor((i-start)/3);
      ctx.drawImage(thumbs[i],col*300+4,row*447+22,292,413);
      ctx.fillStyle='#000';ctx.font='16px sans-serif';ctx.fillText(`PDF ${i+1}`,col*300+8,row*447+17);
    }
    fs.writeFileSync(path.join(dir, `contact-${start+1}.png`), sheet.toBuffer('image/png'));
  }
  fs.writeFileSync(path.join(dir, 'index.json'), JSON.stringify(index));
  console.log(base + ': ' + doc.numPages + ' halaman');
  for(const p of index) {
    console.log(p.page+': '+p.text.slice(0,150));
  }
  await task.destroy();
}
