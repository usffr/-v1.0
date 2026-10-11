/* 双林寺 · 沉浸探秘 —— 游戏引擎
 * 分层渲染 + 景深排序 + 碰撞 + 交互 + 剧情 UI
 * 依赖 data/map.js, data/characters.js, data/photos.js, data/halls.js, data/story.js
 */
/* global MAPDATA, CHARDATA, PHOTOS, HALLS, STORY */

const W = MAPDATA.w, H = MAPDATA.h;
const pctX = (px) => (px / W) * 100;
const pctY = (px) => (px / H) * 100;
const DIRS = CHARDATA.dirs;                 // down, up, left, right
const CELL = { w: CHARDATA.cellW, h: CHARDATA.cellH, cols: CHARDATA.cols };

const SPEED = 1.7;                          // 地图像素 / 帧
const RANGE = 26;                           // 交互范围（地图像素）
const IDLE_SEQ = CHARDATA.idleSeq || [0];
const WALK_SEQ = CHARDATA.walkSeq || [0];

// ---- 碰撞位图 ----
const collisionBits = (() => {
    const bin = atob(MAPDATA.collisionBits);
    const arr = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
    return arr;
})();
function walkable(x, y) {
    const mx = Math.floor(x), my = Math.floor(y);
    if (mx < 0 || my < 0 || mx >= W || my >= H) return false;
    const idx = my * W + mx;
    return ((collisionBits[idx >> 3] >> (7 - (idx & 7))) & 1) === 1;
}
function findWalkable(x, y) {
    if (walkable(x, y)) return { x, y };
    for (let r = 2; r < 120; r += 2)
        for (let a = 0; a < 360; a += 20) {
            const nx = x + Math.cos(a * Math.PI / 180) * r, ny = y + Math.sin(a * Math.PI / 180) * r;
            if (walkable(nx, ny)) return { x: nx, y: ny };
        }
    return { x, y };
}

// ---- 状态 ----
const state = {
    gender: "male",
    started: false,
    keys: {},
    dir: "down",
    frame: 0,
    animPos: 0,
    frameTimer: 0,
    pos: { x: 349, y: 918 },
    fragments: new Set(),
    busy: false,            // 剧情/弹窗中禁止移动
    dlgQueue: [],
    dlgIndex: 0,
};
const FRAG_HALLS = HALLS.filter((h) => !h.secret && h.id !== "shanmen" && h.fragment);

// ---- DOM ----
const $ = (id) => document.getElementById(id);
const world = $("world"), player = $("player"), sprite = $("sprite"), prompt = $("prompt");
const bgm = $("bgm");

// ---- 构建世界 ----
function buildWorld() {
    $("ground").src = MAPDATA.ground;
    const frag = document.createDocumentFragment();
    for (const p of MAPDATA.props) {
        const img = document.createElement("img");
        img.className = "prop";
        img.src = p.file;
        img.style.left = pctX(p.x) + "%";
        img.style.top = pctY(p.y) + "%";
        img.style.width = pctX(p.w) + "%";
        img.style.height = pctY(p.h) + "%";
        img.style.zIndex = String(Math.round(p.anchorY));
        frag.appendChild(img);
    }
    world.insertBefore(frag, player);
}
function buildPoints() {
    for (const h of HALLS) {
        const el = document.createElement("div");
        el.className = "point" + (h.secret ? " secret" : "");
        el.id = "pt-" + h.id;
        el.style.left = pctX(h.x) + "%";
        el.style.top = pctY(h.y) + "%";
        el.innerHTML = `<div class="glow"></div><div class="tag">${h.name}</div>`;
        el.addEventListener("click", () => { if (el.classList.contains("near")) interact(h); });
        world.appendChild(el);
    }
}

// ---- 殿宇目录 ----
function buildIndex() {
    const list = $("idx-list");
    list.innerHTML = "";
    for (const h of HALLS) {
        const el = document.createElement("div");
        el.className = "idx-item" + (h.secret ? " secret" : "");
        el.id = "idx-" + h.id;
        el.innerHTML = `<span class="n">${h.num >= 0 ? "第" + h.num + "号" : "·"}</span>` +
            `<span class="nm">${h.name}</span><span class="tg">${h.tag}</span>`;
        el.addEventListener("click", () => { closeIndex(); flashMarker(h.id); });
        list.appendChild(el);
    }
}
function openIndex() { state.busy = true; $("index-panel").classList.add("show"); }
function closeIndex() { $("index-panel").classList.remove("show"); state.busy = false; checkNear(); }
function flashMarker(id) {
    const el = $("pt-" + id);
    if (!el) return;
    el.classList.add("flash");
    setTimeout(() => el.classList.remove("flash"), 1400);
}

// ---- 玩家 ----
function setChar() {
    sprite.style.backgroundImage = `url('${state.gender === "female" ? CHARDATA.female : CHARDATA.male}')`;
    sprite.style.backgroundSize = `${CELL.cols * 100}% ${DIRS.length * 100}%`;
}
function updatePlayer() {
    player.style.left = pctX(state.pos.x) + "%";
    player.style.top = pctY(state.pos.y) + "%";
    player.style.zIndex = String(Math.round(state.pos.y));
    const r = DIRS.indexOf(state.dir);
    const c = state.frame || 0;
    sprite.style.backgroundPosition = `${(c / (CELL.cols - 1)) * 100}% ${(r / (DIRS.length - 1)) * 100}%`;
}

// ---- 主循环 ----
let raf = 0;
function loop() {
    if (state.started && !state.busy) {
        let dx = 0, dy = 0;
        if (state.keys.ArrowUp) { dy -= SPEED; state.dir = "up"; }
        if (state.keys.ArrowDown) { dy += SPEED; state.dir = "down"; }
        if (state.keys.ArrowLeft) { dx -= SPEED; state.dir = "left"; }
        if (state.keys.ArrowRight) { dx += SPEED; state.dir = "right"; }
        if (dx || dy) {
            if (dx && walkable(state.pos.x + dx, state.pos.y)) state.pos.x += dx;
            if (dy && walkable(state.pos.x, state.pos.y + dy)) state.pos.y += dy;
            state.frameTimer++;
            if (state.frameTimer % 6 === 0) state.animPos = (state.animPos + 1) % WALK_SEQ.length;
            state.frame = WALK_SEQ[state.animPos];
            updatePlayer();
        } else {
            state.frameTimer++;
            if (state.frameTimer % 34 === 0) state.animPos = (state.animPos + 1) % IDLE_SEQ.length;
            state.frame = IDLE_SEQ[state.animPos];
            updatePlayer();
        }
        checkNear();
    }
    raf = requestAnimationFrame(loop);
}

let nearHall = null;
function checkNear() {
    let best = null, bd = RANGE;
    for (const h of HALLS) {
        const el = $("pt-" + h.id);
        if (el.classList.contains("done")) { el.classList.remove("near"); continue; }
        const d = Math.hypot(state.pos.x - h.x, state.pos.y - h.y);
        if (d < bd) { bd = d; best = h; }
    }
    document.querySelectorAll(".point").forEach((e) => e.classList.remove("near"));
    if (best) best && $("pt-" + best.id).classList.add("near");
    nearHall = best;
    prompt.classList.toggle("show", !!best);
    if (best) prompt.innerHTML = `按 <b>E</b> · ${best.name}`;
}

// ---- 交互 ----
function interact(h) {
    if (state.busy) return;
    if (h.id === "shanmen" && state.fragments.size >= FRAG_HALLS.length) return ending();
    openCard(h);
}
function openCard(h) {
    state.currentHall = h;
    state.busy = true;
    $("card-num").textContent = h.num >= 0 ? "第 " + h.num + " 号 · " + h.tag : h.tag;
    $("card-title").textContent = h.name;
    $("card-tag").textContent = "";
    $("card-poem").textContent = h.poem;
    $("card-lore").textContent = h.lore;
    // 有照片才显示殿内漫游按钮
    $("hall-walk").style.display = (h.id !== "shanmen" && h.group && PHOTOS[h.group] && PHOTOS[h.group].length > 0) ? "block" : "none";
    const gal = $("card-gallery");
    gal.innerHTML = "";
    (PHOTOS[h.group] || []).forEach((src) => {
        const im = document.createElement("img");
        im.src = src; im.alt = h.name; gal.appendChild(im);
    });
    const owned = state.fragments.has(h.fragment);
    const frag = $("card-frag");
    frag.classList.toggle("owned", owned);
    if (h.secret) {
        frag.innerHTML = owned
            ? `<span class="seal">${h.fragment}</span> 已收录佚名拓片。`
            : `<span class="seal">?</span> 橱中似有一片无名拓片… <button class="go" id="take-btn" style="margin-left:auto;padding:5px 14px;font-size:13px">拓下</button>`;
    } else if (h.id === "shanmen") {
        const n = state.fragments.size;
        frag.innerHTML = `<span class="seal">碑</span> 拓片 ${n} / ${FRAG_HALLS.length}${n >= FRAG_HALLS.length ? ` — <b style="color:#8b6914;font-size:16px;">⭐ 拓片已齐，回到山门触发结局 ⭐</b>` : " — 还需走遍诸殿。"}`;
    } else if (!h.fragment) {
        frag.innerHTML = `<span class="seal">考</span> 此殿暂无实拍拓片，仅存文字考述。`;
    } else {
        frag.innerHTML = owned
            ? `<span class="seal">${h.fragment}</span> 「${h.fragment}」拓片已收录。`
            : `<span class="seal">${h.fragment}</span> 收下这片「${h.fragment}」拓片。 <button class="go" id="take-btn" style="margin-left:auto;padding:5px 14px;font-size:13px">收下拓片</button>`;
    }
    $("card").classList.add("show");
    const btn = $("take-btn");
    if (btn) btn.addEventListener("click", () => {
        state.fragments.add(h.fragment);
        $("pt-" + h.id).classList.add("done");
        const it = $("idx-" + h.id); if (it) it.classList.add("done");
        updateQuest();
        $("card").classList.remove("show");
        state.busy = false;
        if (h.secret) { dialogue([{ sp: "旁白", t: "你拓下了那片无名的「器」——它不属于六片之列，却似乎更古老。" }]); }
        else if (state.fragments.size >= FRAG_HALLS.length) {
            $("foot-hint").textContent = STORY.readyHint;
            dialogue([{ sp: "旁白", t: "六片拓片在你掌心微微发烫。该回山门了。" }]);
        } else { checkNear(); }
    });
}
function updateQuest() {
    $("frag-count").textContent = state.fragments.size;
    const dots = $("frag-dots");
    dots.innerHTML = "";
    for (let i = 0; i < FRAG_HALLS.length; i++) {
        const d = document.createElement("i");
        if (i < state.fragments.size) d.className = "on";
        dots.appendChild(d);
    }
}

// ---- 剧情对白 ----
function dialogue(lines, onEnd) {
    state.busy = true;
    state.dlgQueue = lines.slice();
    state.dlgIndex = 0;
    state.dlgOnEnd = onEnd;
    $("dialogue").classList.add("show");
    showDlgLine();
}
function showDlgLine() {
    const line = state.dlgQueue[state.dlgIndex];
    if (!line) return closeDialogue();
    $("dlg-sp").textContent = line.sp || "";
    $("dlg-t").textContent = line.t;
}
function advanceDialogue() {
    state.dlgIndex++;
    if (state.dlgIndex >= state.dlgQueue.length) closeDialogue();
    else showDlgLine();
}
function closeDialogue() {
    $("dialogue").classList.remove("show");
    state.busy = false;
    if (state.dlgOnEnd) { const f = state.dlgOnEnd; state.dlgOnEnd = null; f(); }
    checkNear();
}

// ---- 结局 ----
function ending() {
    state.busy = true;
    const box = $("end-frags");
    box.innerHTML = "";
    for (const h of FRAG_HALLS) { const s = document.createElement("span"); s.textContent = h.fragment; box.appendChild(s); }
    $("ending").classList.add("show");
}

// ---- 启动 / 重开 ----
function startGame() {
    $("start-screen").classList.remove("show");
    state.started = true; state.busy = false;
    bgm.play().catch(() => {});
    dialogue(STORY.prologue, () => { $("foot-hint").textContent = STORY.hint; });
}
function reset() {
    state.fragments.clear();
    state.pos = findWalkable(349, 918);
    state.dir = "down"; state.frame = 0; state.animPos = 0;
    updatePlayer(); updateQuest();
    document.querySelectorAll(".point").forEach((p) => p.classList.remove("done", "near"));
    document.querySelectorAll(".idx-item").forEach((e) => e.classList.remove("done"));
    $("ending").classList.remove("show");
    $("foot-hint").textContent = STORY.hint;
    state.busy = true;
    dialogue(STORY.prologue, () => { $("foot-hint").textContent = STORY.hint; });
}

// ---- 初始化 ----
function init() {
    buildWorld();
    buildPoints();
    buildIndex();
    setChar();
    state.pos = findWalkable(349, 918);
    updatePlayer();
    updateQuest();

    $("start-sub").textContent = STORY.subtitle;

    document.addEventListener("keydown", (e) => {
        if (e.key.startsWith("Arrow")) e.preventDefault();
        state.keys[e.key] = true;
        if ((e.key === "e" || e.key === "E") && nearHall && !state.busy) interact(nearHall);
        if ((e.key === " " || e.key === "Enter" || e.key === "ArrowDown") && $("dialogue").classList.contains("show")) { e.preventDefault(); advanceDialogue(); }
    });
    document.addEventListener("keyup", (e) => { state.keys[e.key] = false; });

    document.querySelectorAll(".char").forEach((b) => b.addEventListener("click", () => {
        document.querySelectorAll(".char").forEach((x) => x.classList.remove("selected"));
        b.classList.add("selected");
        state.gender = b.dataset.g;
        setChar();
    }));
    $("start-bird").addEventListener("click", () => { $("bird-panel").classList.add("show"); });
    $("bird-close").addEventListener("click", () => { $("bird-panel").classList.remove("show"); });
    $("start-help").addEventListener("click", () => { $("help-panel").classList.add("show"); });
    $("start-video").addEventListener("click", () => {
        $("start-screen").classList.remove("show");
        $("video").classList.add("show");
        $("v").play().catch(() => {});
    });
    // 唤醒视频：播放→(结束或跳过)→进入游戏（统一走同一条路）
    var wakeV = $("wake"), wakeSkip = $("wake-skip"), wakePlay = $("wake-play");
    function finishWake() {
        if (wakeV) { try { wakeV.pause(); } catch (e) {} }
        $("wake-video").style.display = "none";
        $("start-screen").classList.remove("show");
        if (!state.started) startGame();
    }
    if (wakePlay) wakePlay.addEventListener("click", function () {
        this.style.display = "none";
        if (wakeSkip) wakeSkip.style.display = "block";
        if (wakeV) wakeV.play().catch(function () {});
    });
    if (wakeSkip) wakeSkip.addEventListener("click", finishWake);
    if (wakeV) wakeV.addEventListener("ended", finishWake);
        $("dlg").addEventListener("click", (e) => {
        if (e.target.id === "dlg-skip") return;
        advanceDialogue();
    });
    $("dlg-skip").addEventListener("click", (e) => {
        e.stopPropagation();
        state.dlgIndex = state.dlgQueue.length;
        closeDialogue();
    });

    $("card-close").addEventListener("click", () => { $("card").classList.remove("show"); state.busy = false; checkNear(); });
    // 殿内漫游
    let hallTimer = null;
    $("hall-walk").addEventListener("click", () => {
        const h = state.currentHall;
        if (!h || !h.group || !PHOTOS[h.group]) return;
        const imgs = PHOTOS[h.group];
        let i = 0;
        $("hall-view").classList.add("show");
        const img = $("hall-img");
        function showNext() {
            img.style.opacity = 0;
            setTimeout(() => {
                img.src = imgs[i];
                img.style.opacity = 1;
                i = (i + 1) % imgs.length;
            }, 800);
        }
        showNext();
        hallTimer = setInterval(showNext, 3500);
    });
    $("hall-close").addEventListener("click", () => {
        $("hall-view").classList.remove("show");
        if (hallTimer) { clearInterval(hallTimer); hallTimer = null; }
    });
    $("btn-help").addEventListener("click", () => { $("help-panel").classList.add("show"); });
    $("help-close").addEventListener("click", () => { $("help-panel").classList.remove("show"); });
    $("btn-index").addEventListener("click", openIndex);
    $("index-close").addEventListener("click", closeIndex);
    $("video-close").addEventListener("click", closeVideo);
    $("video-after").addEventListener("click", closeVideo);
    $("btn-video").addEventListener("click", () => { bgm.pause(); $("video").classList.add("show"); $("v").play().catch(() => {}); });
    $("btn-audio").addEventListener("click", () => {
        if (bgm.paused) { bgm.play(); $("btn-audio").textContent = "🔊"; } else { bgm.pause(); $("btn-audio").textContent = "🔇"; }
    });
    // 随时退出 · 返回首页
    $("btn-exit").addEventListener("click", () => { location.href = "../../index.html#game-banner"; });
    $("end-btn").addEventListener("click", () => { $("ending").classList.remove("show"); reset(); });
    $("end-continue").addEventListener("click", () => { $("ending").classList.remove("show"); state.busy = false; $("foot-hint").textContent = "你已集齐所有拓片，可继续自由探索"; checkNear(); });
    $("end-exit").addEventListener("click", () => { $("ending").classList.remove("show"); location.reload(); });

    loop();
}
let videoFromWelcome = false;
function openVideoFromWelcome() {
    videoFromWelcome = true;
    $("start-screen").classList.remove("show");
    $("video").classList.add("show");
    $("v").play().catch(() => {});
}
function closeVideo() {
    $("v").pause();
    $("video").classList.remove("show");
    if (videoFromWelcome) {
        $("start-screen").classList.add("show");
        videoFromWelcome = false;
    } else {
        bgm.play().catch(() => {});
        state.busy = false;
    }
}

init();
