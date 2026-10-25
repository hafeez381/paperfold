// The opening's two moving parts, played by ascii.rest 0.4.0 (MIT, github.com/bas3line/ascii; its player and its
// typewriter are kept beside the page, in assets/vendor/ascii.rest, with its licence): the typed line under the headline,
// and beside it a page of characters folding the way TextFold folds one, to the point of each paragraph. Where the
// script cannot run, the line keeps its own words and the page stays hidden; with reduced motion both hold one frame.
import { mount } from './assets/vendor/ascii.rest/dist/mount.js';
import * as typewriter from './assets/vendor/ascii.rest/dist/pieces/typewriter.js';

// ── A page folding the way TextFold folds one: three paragraphs, each led by its point. Folding, each draws in onto one
// line, and everything after its point gathers, letter by letter, into a bar: the logo's three (long to short, violet,
// light violet, orange), a crease shading each folding edge (▓▒░). The points stay, readable: "fold any text", "keep the
// point", "unfold". A glint crosses the bars, and the page opens out again. A coloured piece: ascii.rest draws it on a
// canvas, in the mark's colours on a light page or a dark one; with reduced motion it holds the folded page.
function mark() {
  const COLS = 56, ROWS = 16, X = 4, TW = 48;
  const PARAS = [
    ['fold any text', 'fold any text from a one screen map to every word: five levels of the same document, and as you move '
      + 'between them the words that stay slide to their new place'],
    ['keep the point', "keep the point of every paragraph, the author's key sentences kept word for word, and each line a model "
      + 'writes points back to the sentence it came from'],
    ['unfold', 'unfold to every word when you need it, the original always one key away, and the notes you wrote stay in the '
      + 'margin beside the passage you marked'],
  ];
  const wrap = (text, widths) => {   // the paragraph's words on four lines of about these widths
    const words = text.split(' '), out = [];
    for (const width of widths) {
      let line = '';
      while (words.length && (!line || line.length + 1 + words[0].length <= width)) line += (line ? ' ' : '') + words.shift();
      out.push(line);
    }
    return out;
  };
  const groups = PARAS.map(([point, text], g) => ({
    point: point.length,
    rows: [0, 1, 2, 3].map((k) => g * 5 + 1 + k),     // where its four lines stand as text
    row: g * 5 + 2,                                   // the one line it folds onto
    width: Math.round(TW * [16, 11, 5][g] / 16),       // the logo's 16, 11, 5
    color: g + 1,
    lines: wrap(text, [TW, TW - 3, TW - 1, [30, 21, 12][g]]),
  }));
  const rand = (x, y) => { let h = Math.imul(x + 3, 374761393) ^ Math.imul(y + 11, 668265263); h = Math.imul(h ^ (h >>> 13), 1274126177); return ((h ^ (h >>> 16)) >>> 0) / 4294967296; };
  const ease = (x) => (x <= 0 ? 0 : x >= 1 ? 1 : x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);
  const PERIOD = 8, FOLD = [1.8, 3.6], OPEN = [5.8, 7.6], GLINT = [4.1, 5.0];
  const progress = (t, g) => {   // 0 the page, 1 folded: each paragraph a beat after the one above when folding, before it when opening
    const u = ((t % PERIOD) + PERIOD) % PERIOD;
    if (u < OPEN[0]) return ease((u - FOLD[0] - g * 0.18) / (FOLD[1] - FOLD[0] - 0.36));
    return 1 - ease((u - OPEN[0] - (2 - g) * 0.18) / (OPEN[1] - OPEN[0] - 0.36));
  };
  const INK = 4;   // the points' colour, the page's ink; 0 the rest of the text
  return {
    meta: { name: 'textfold-fold', cols: COLS, rows: ROWS, fps: 30, still: 5.2, cell: 2,
      palette: ['#9C958B', '#6B5CE7', 'rgba(107, 92, 231, .45)', '#E08A3C', '#1A1A1A',
        '#7A746C', '#A79FF4', 'rgba(167, 159, 244, .5)', '#E8A35E', '#EDE9E3'] },
    default: () => (t, env) => {
      const grid = Array.from({ length: ROWS }, () => Array(COLS).fill(' ')), dark = env && env.paper === false ? 5 : 0;
      const put = (x, y, ch, c) => { if (x < 0 || x >= COLS || y < 0 || y >= ROWS) return; grid[y][x] = ch; if (env && env.color) env.color[y * COLS + x] = c + dark; };
      const u = ((t % PERIOD) + PERIOD) % PERIOD;
      const glint = u > GLINT[0] && u < GLINT[1] ? X - 3 + (TW + 6) * (u - GLINT[0]) / (GLINT[1] - GLINT[0]) : -99;
      for (const G of groups) {
        const f = progress(t, G.color - 1);
        for (let k = 3; k >= 0; k--) {   // the first line last, so its point lies on top
          const text = G.lines[k], keep = k === 0 ? G.point : 0;
          const y = Math.round(G.rows[k] + (G.row - G.rows[k]) * f);
          const shrink = text.length > G.width;   // a line drawn in to its bar creases at its edge; a shorter one just fills out
          const len = Math.round(text.length + (G.width - text.length) * f);
          for (let x = 0; x < len; x++) {
            const letter = x < text.length ? text[x] : ' ';
            if (x < keep) { put(X + x, y, letter, INK); continue; }   // the point: kept, as written
            if (x === keep && keep && f > 0.5) { put(X + x, y, ' ', 0); continue; }   // a space between the point and its bar
            const r = rand(x, G.rows[k]), edge = len - x;
            let ch = f > r * 0.85 + 0.1 ? '█' : f > r * 0.85 ? '▓' : letter;
            if (shrink && f > 0.04 && f < 0.98 && edge <= 3) ch = '▓▒░'[3 - edge];   // the crease, at the folding edge
            if (f >= 0.98 && Math.abs(X + x - glint) < 1.5) ch = '░';   // the glint, across the bars
            if (ch !== ' ') put(X + x, y, ch, ch === letter ? 0 : G.color);   // a gap lets the line beneath show
          }
        }
      }
      return grid.map((l) => l.join('')).join('\n');
    },
  };
}

// the typewriter centres its line in three rows of 44 columns: here, the one row, flush left with the headline
function flush(opts) {
  const { cols } = typewriter.meta;
  const x = Math.max(0, Math.floor((cols - (opts.prefix.length + Math.max(...opts.phrases.map((p) => p.length)) + 1)) / 2));
  return { meta: { ...typewriter.meta, cols: cols - x, rows: 1 }, default: (o) => { const f = typewriter.default(o); return (t) => f(t).split('\n')[1].slice(x); } };
}

for (const root of document.querySelectorAll('[data-root]')) {
  const art = root.querySelector('.logo-art');
  if (art) {   // played once it is first on screen: a canvas sized while hidden would stay empty
    art.closest('figure').hidden = false;
    const io = new IntersectionObserver((es) => { if (es.some((e) => e.isIntersecting)) { io.disconnect(); mount(art, mark()); } });
    io.observe(art);
  }
  const line = root.querySelector('.ascii-line');
  if (line) { const opts = JSON.parse(line.dataset.options); mount(line, flush(opts), opts); }
}
