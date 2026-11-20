// Vice Panels is an offline GTA-style cover maker with four layouts, four colour grades, and bundled sample images.
// Its static app runs in a desktop browser without network requests or libraries. This entrypoint packages app/ and
// screenshots/ and writes the make.fun dossier to /output.
//
// Serve it locally with `node serve.ts`, then open http://localhost:8080.
// Outside the grader's container, MAKEFUN_OUTPUT_DIR stands in for /output:
//   mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts

import { cpSync, existsSync, mkdirSync, readdirSync, statSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { buildDossier } from './vendor/makefun-app.ts';

const here = fileURLToPath(new URL('.', import.meta.url));
const out = process.env.MAKEFUN_OUTPUT_DIR ?? '/output';

mkdirSync(out, { recursive: true });
cpSync(join(here, 'app'), join(out, 'app'), { recursive: true });
mkdirSync(join(out, 'screenshots'), { recursive: true });
if (existsSync(join(here, 'screenshots'))) cpSync(join(here, 'screenshots'), join(out, 'screenshots'), { recursive: true });

// The scorer's own caps (reference/gate.json): only text_max_bytes shapes the bytes; the others refuse an entry the
// scorer would refuse (more than 4 screenshots or one over 256 KiB; more than 993 files in app/ or 48 MiB of app
// files, in all, or a path under app/ over 1000 bytes: app/ counts beside /output's own 1000-entry cap, its
// screenshots/ and dossier.json).
writeFileSync(
  join(out, 'dossier.json'),
  buildDossier(out, {
    text_max_bytes: 163840,
    screenshots: { max: 4, max_bytes: 262144 },
    app_max_files: 993,
    app_max_bytes: 50331648,
    app_path_max_bytes: 1000,
  }),
);


const files = [];
function collectFiles(directory, relative = '') {
  for (const name of readdirSync(directory).sort()) {
    const path = join(directory, name);
    const file = relative ? join(relative, name) : name;
    if (statSync(path).isDirectory()) collectFiles(path, file);
    else if (file !== 'manifest.json') files.push({ path: file, bytes: statSync(path).size });
  }
}
collectFiles(out);
const totalBytes = files.reduce((total, file) => total + file.bytes, 0);
const imageFiles = files.filter(file => file.path.startsWith('screenshots/') && /\.(avif|gif|jpe?g|png|webp)$/i.test(file.path));
const manifest = {
  files,
  totalBytes,
  screenshots: { count: imageFiles.length, bytes: imageFiles.reduce((total, file) => total + file.bytes, 0) },
};
writeFileSync(join(out, 'manifest.json'), JSON.stringify(manifest, null, 2) + '\n');
console.log(`Manifest: ${files.length} files, ${totalBytes} bytes`);
