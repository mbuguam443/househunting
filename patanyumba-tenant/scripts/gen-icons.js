const fs = require('fs');
const path = require('path');
const { PNG } = require('pngjs');

const source = process.argv[2];
const outDir = process.argv[3];
const bg = process.argv[4] || '#ffffff';

function makeCanvas(size) {
  const png = new PNG({ width: size, height: size });
  for (let y = 0; y < size; y++) {
    for (let x = 0; x < size; x++) {
      const idx = (size * y + x) << 2;
      png.data[idx] = 0;
      png.data[idx + 1] = 0;
      png.data[idx + 2] = 0;
      png.data[idx + 3] = 0;
    }
  }
  return png;
}

function hexToRgb(hex) {
  const h = hex.replace('#', '');
  return [parseInt(h.substring(0, 2), 16), parseInt(h.substring(2, 4), 16), parseInt(h.substring(4, 6), 16)];
}

function drawIcon(size, marginFrac, file) {
  const canvas = makeCanvas(size);
  const src = PNG.sync.read(fs.readFileSync(source));
  const m = Math.round(size * marginFrac);
  const inner = size - m * 2;
  const [r, g, b] = hexToRgb(bg);
  // filled rounded background
  for (let y = 0; y < size; y++) {
    for (let x = 0; x < size; x++) {
      canvas.data[(size * y + x) << 2] = r;
      canvas.data[(size * y + x) << 2 + 1] = g;
      canvas.data[(size * y + x) << 2 + 2] = b;
      canvas.data[(size * y + x) << 2 + 3] = 255;
    }
  }
  // draw source scaled into inner region (nearest neighbor)
  for (let y = 0; y < inner; y++) {
    for (let x = 0; x < inner; x++) {
      const sx = Math.floor((x / inner) * src.width);
      const sy = Math.floor((y / inner) * src.height);
      const sIdx = (src.width * sy + sx) << 2;
      const dIdx = (size * (y + m) + (x + m)) << 2;
      const a = src.data[sIdx + 3] / 255;
      for (let c = 0; c < 3; c++) {
        canvas.data[dIdx + c] = Math.round(
          src.data[sIdx + c] * a + canvas.data[dIdx + c] * (1 - a)
        );
      }
      canvas.data[dIdx + 3] = 255;
    }
  }
  fs.writeFileSync(file, PNG.sync.write(canvas));
  console.log('wrote', file);
}

if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });

drawIcon(1024, 0.08, path.join(outDir, 'icon.png'));
drawIcon(512, 0.25, path.join(outDir, 'adaptive-icon.png'));
drawIcon(256, 0.25, path.join(outDir, 'favicon.png'));

// splash is a proportional PNG (e.g. 1080x1920). Use existing splash if available.
const splashSrc = path.join(path.dirname(source), 'splash-1080x1920.png');
const splashDest = path.join(outDir, 'splash.png');
if (fs.existsSync(splashSrc)) {
  const s = PNG.sync.read(fs.readFileSync(splashSrc));
  if (s.width !== 1080 || s.height !== 1920) {
    fs.copyFileSync(splashSrc, splashDest);
  } else {
    fs.writeFileSync(splashDest, fs.readFileSync(splashSrc));
  }
  console.log('wrote', splashDest);
} else {
  drawIcon(1080, 0, splashDest); // fallback square
  console.log('wrote (fallback)', splashDest);
}
