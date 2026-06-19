# Blacksmith Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the existing single-file blacksmith prototype clearer, more polished, and more decision-driven while preserving the core balance.

**Architecture:** Keep the app in `blacksmith.html` and add narrowly scoped UI helpers for slot verdicts, request status, and action guidance. Reuse the existing logic core and simulator so the balance can be checked before and after the UI work.

**Tech Stack:** Vanilla HTML, CSS, JavaScript, local WebP assets, Web Audio API, Node.js simulator.

## Global Constraints

- Single playable file: `blacksmith.html`.
- No external CDN, framework, or network dependency.
- Mobile portrait first, centered max-width around 480px on desktop.
- All user-facing text is Korean.
- Local asset fallbacks must continue to work.
- Keep the satisfaction formula and roll probabilities unchanged.
- Existing `simulate.mjs` must continue to run.

---

### Task 1: Add Request And Decision UI

**Files:**
- Modify: `blacksmith.html`

**Interfaces:**
- Consumes: `cur.adv`, `cur.slots`, `cur.revealed`, `cur.rerollsLeft`, `partialPct()`, `SATISFACTION_GOAL`.
- Produces: `renderRequestPanel()`, `slotVerdict(slot)`, `updateDecisionPanel(slot)`.

- [ ] **Step 1: Add HTML containers**

Add a request panel below narration and a decision panel above action buttons:

```html
<div id="requestPanel">
  <div class="request-main"><span id="requestTitle">의뢰 대기 중</span><b id="requestGoal">목표 —</b></div>
  <div class="request-sub" id="requestSub">손님이 오면 의뢰 조건이 표시됩니다.</div>
</div>
```

```html
<div id="decisionPanel">
  <span id="decisionBadge">대기</span>
  <b id="decisionTitle">슬롯을 제련하세요</b>
  <span id="decisionHint">결과를 보고 확정하거나 리롤할 수 있습니다.</span>
</div>
```

- [ ] **Step 2: Add CSS for request and decision panels**

Add styles near the existing gauge and action sections:

```css
#requestPanel{border:1px solid rgba(255,210,74,.24); background:rgba(20,14,9,.58); border-radius:8px; padding:8px 10px; margin:5px 0 6px;}
.request-main{display:flex; justify-content:space-between; gap:8px; align-items:center; font-size:12px;}
.request-main span{font-weight:800; color:#f7ead5; min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;}
.request-main b{color:var(--gold); font-size:12px; white-space:nowrap;}
.request-sub{font-size:11px; color:var(--dim); margin-top:3px; line-height:1.35; word-break:keep-all;}
#decisionPanel{display:grid; grid-template-columns:auto 1fr; gap:2px 8px; align-items:center; min-height:42px; border:1px solid var(--line); border-radius:8px; padding:7px 9px; background:rgba(13,9,6,.62); margin-top:4px;}
#decisionBadge{grid-row:1 / span 2; min-width:48px; text-align:center; border-radius:7px; padding:4px 6px; font-size:11px; font-weight:900; color:#241a10; background:var(--gold);}
#decisionTitle{font-size:13px; line-height:1.2; color:#f7ead5;}
#decisionHint{font-size:11px; line-height:1.25; color:var(--dim); word-break:keep-all;}
#decisionPanel.v-good #decisionBadge{background:#7df59b;}
#decisionPanel.v-ok #decisionBadge{background:#f0e6d6;}
#decisionPanel.v-bad #decisionBadge{background:#9a8b78; color:#120d08;}
#decisionPanel.v-curse #decisionBadge{background:#b774ff; color:#fff;}
#decisionPanel.v-jackpot #decisionBadge{background:var(--gold); box-shadow:0 0 12px rgba(255,210,74,.45);}
```

- [ ] **Step 3: Add JS helpers**

Add these helpers near `partialPct()`:

```javascript
function slotVerdict(slot){
  const q = attrQuality(slot.attr, slot.tier, cur.adv.weapon, cur.adv.job, cur.adv.mood);
  const grade = TIER_GRADE[slot.tier];
  if(grade === "초대박") return { cls:"v-jackpot", label:"대박", title:"놓치기 아까운 슬롯", hint:"높은 티어입니다. 보통은 확정하는 쪽이 좋습니다." };
  if(ATTRS.저주.includes(slot.attr)){
    return DARK_MOODS.includes(cur.adv.mood)
      ? { cls:"v-curse", label:"저주+", title:"이 손님은 저주를 반깁니다", hint:"어둠 성향 손님에게는 강한 선택입니다." }
      : { cls:"v-curse", label:"저주", title:"대부분 손님에게 위험한 슬롯", hint:"리롤이 남았다면 다시 굴릴 만합니다." };
  }
  if(q >= 1.0) return { cls:"v-good", label:"적중", title:"무기와 손님에게 잘 맞습니다", hint:"목표 만족도에 크게 기여합니다." };
  if(q === 0) return { cls:"v-bad", label:"빗나감", title:"만족도에 기여하지 않습니다", hint:"리롤을 쓰기 좋은 후보입니다." };
  return { cls:"v-ok", label:"무난", title:"쓸 수는 있는 슬롯", hint:"목표까지 여유가 없다면 리롤을 고민하세요." };
}

function renderRequestPanel(){
  if(!cur){
    el("requestTitle").textContent = "의뢰 대기 중";
    el("requestGoal").textContent = "목표 —";
    el("requestSub").textContent = "손님이 오면 의뢰 조건이 표시됩니다.";
    return;
  }
  const a = cur.adv;
  const pct = partialPct();
  const gap = Math.max(0, a.goal - pct);
  el("requestTitle").textContent = `${a.grade} ${a.weapon} · ${a.job}`;
  el("requestGoal").textContent = `목표 ${a.goal}%`;
  el("requestSub").textContent = cur.revealed === 0 && cur.vals.length === 0
    ? "선호 속성과 무효 카테고리를 보고 첫 슬롯을 제련하세요."
    : `현재 ${pct}% · 목표까지 ${gap}% 남음 · 리롤 ${cur.rerollsLeft}회`;
}

function updateDecisionPanel(slot){
  const panel = el("decisionPanel");
  panel.className = "";
  if(!slot){
    el("decisionBadge").textContent = "대기";
    el("decisionTitle").textContent = "슬롯을 제련하세요";
    el("decisionHint").textContent = "결과를 보고 확정하거나 리롤할 수 있습니다.";
    return;
  }
  const v = slotVerdict(slot);
  panel.classList.add(v.cls);
  el("decisionBadge").textContent = v.label;
  el("decisionTitle").textContent = v.title;
  el("decisionHint").textContent = `${v.hint} 현재 리롤 ${cur.rerollsLeft}회.`;
}
```

- [ ] **Step 4: Wire helpers into flow**

Call `renderRequestPanel()` and `updateDecisionPanel(null)` in `nextCustomer()`. Call `renderRequestPanel()` after `updateGauge(partialPct(), false)` in `doReveal()`. Call `updateDecisionPanel(slot)` after the slot is committed. Call `renderRequestPanel()` after reroll count changes.

- [ ] **Step 5: Verify manually**

Open `blacksmith.html`, start the game, reveal one slot, and confirm the request panel and decision panel update.

### Task 2: Polish Slot Tray And Overlays

**Files:**
- Modify: `blacksmith.html`

**Interfaces:**
- Consumes: `slotVerdict(slot)`, `showGameOver()`, existing start overlay.
- Produces: clearer slot classes and refined overlay copy.

- [ ] **Step 1: Add slot verdict classes**

Update `commitSlot(i, slot)` to add the verdict class:

```javascript
const verdict = slotVerdict(slot);
d.classList.add(verdict.cls);
d.innerHTML = `<div class="s-tier">${slot.tier}</div><div class="s-attr">${slot.attr}</div><div class="s-note">${verdict.label}</div>`;
```

- [ ] **Step 2: Add slot note CSS**

```css
.slot .s-note{font-size:9px; margin-top:2px; font-weight:900; opacity:.9;}
.slot.v-good .s-note{color:#7df59b;}
.slot.v-ok .s-note{color:#f0e6d6;}
.slot.v-bad .s-note{color:#b8a888;}
.slot.v-curse .s-note{color:#cda2ff;}
.slot.v-jackpot .s-note{color:var(--gold);}
```

- [ ] **Step 3: Refresh overlay copy**

Keep the same buttons but make the start copy shorter:

```html
<p>모험가가 들고 온 무기에 네 개의 슬롯을 박아 목표 만족도를 넘기세요.<br>슬롯 결과를 보고 손님마다 한 번, 마음에 안 드는 결과를 다시 굴릴 수 있습니다.</p>
```

- [ ] **Step 4: Verify no layout overflow**

At 390px width, the four slot cards must remain one row and each card's text must stay inside the card.

### Task 3: Verify Balance And Browser Behavior

**Files:**
- Modify: no source changes expected unless verification finds a bug.

**Interfaces:**
- Consumes: `simulate.mjs`, `blacksmith.html`.
- Produces: verified prototype.

- [ ] **Step 1: Run simulator**

Run: `node simulate.mjs`
Expected: command exits successfully and prints both sanity and reroll strategy tables.

- [ ] **Step 2: Browser smoke test**

Use a browser at mobile width. Start game, reveal, reroll, advance, and finish at least one customer. Expected: no JavaScript console errors, panels update, buttons enable and disable correctly.

- [ ] **Step 3: Record residual risks**

If no browser automation is available, record that visual verification was limited and provide the exact simulator output summary.

## Self-Review

- Spec coverage: request clarity, slot quality feedback, reroll decision clarity, overlay polish, single-file constraint, and simulator verification are covered.
- Placeholder scan: no TBD or undefined future tasks remain.
- Type consistency: all new helpers consume existing `cur`, `el`, `attrQuality`, `TIER_GRADE`, `ATTRS`, and `DARK_MOODS` names already present in `blacksmith.html`.
