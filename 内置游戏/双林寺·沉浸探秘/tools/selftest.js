// 自检：起点连通性 + 各交互点可达
const fs = require('fs');
const path = require('path');
const base = path.join(__dirname, '..');
function jsObj(file, name) {
    const src = fs.readFileSync(path.join(base, file), 'utf8');
    return new Function(src + `; return ${name};`)();
}
const M = jsObj('data/map.js', 'MAPDATA');
const HALLS = jsObj('data/halls.js', 'HALLS');
const W = M.w, H = M.h;
const B = Buffer.from(M.collisionBits, 'base64');
const walk = (x, y) => {
    const mx = x | 0, my = y | 0;
    if (mx < 0 || my < 0 || mx >= W || my >= H) return false;
    const i = my * W + mx; return ((B[i >> 3] >> (7 - (i & 7))) & 1) === 1;
};
const start = { x: 349, y: 918 };
while (!walk(start.x, start.y) && start.y > 0) start.y--;
const reach = new Uint8Array(W * H);
const q = [[start.x | 0, start.y | 0]]; reach[(start.y | 0) * W + (start.x | 0)] = 1;
const dirs = [[1, 0], [-1, 0], [0, 1], [0, -1]];
while (q.length) {
    const [x, y] = q.pop();
    for (const [dx, dy] of dirs) {
        const nx = x + dx, ny = y + dy;
        if (nx < 0 || ny < 0 || nx >= W || ny >= H) continue;
        const i = ny * W + nx;
        if (reach[i] || !walk(nx, ny)) continue;
        reach[i] = 1; q.push([nx, ny]);
    }
}
console.log('start', start, 'walkable', walk(start.x, start.y));
for (const h of HALLS) {
    let ok = false, bd = -1;
    for (let r = 0; r <= 30 && !ok; r++) {
        for (let a = 0; a < 360; a += 10) {
            const nx = h.x + Math.cos(a * Math.PI / 180) * r, ny = h.y + Math.sin(a * Math.PI / 180) * r;
            if (nx < 0 || ny < 0 || nx >= W || ny >= H) continue;
            if (reach[(ny | 0) * W + (nx | 0)]) { ok = true; bd = r; break; }
        }
    }
    console.log((ok ? 'OK ' : 'XX '), h.id.padEnd(10), 'near-dist', bd);
}
console.log('reach cells', reach.reduce((a, b) => a + b, 0), '/', W * H, '(' + Math.round(100 * reach.reduce((a, b) => a + b, 0) / (W * H)) + '% of map)');
