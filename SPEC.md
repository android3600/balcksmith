# 대장장이 키우기 — 프로토타입 구현 명세 (SPEC.md)

> 이 문서 하나로 프로토타입을 구현한다. 외부 자료 없이 자체 완결.
> 작성 기준: 단발성 스코어 어택 프로토타입 (키우기·보상·경제는 v2로 보류).

---

## 0. 한눈에 보기

- **장르**: 단발성 스코어 어택. 찾아온 모험가의 무기를 제련해 만족시키고, 실패가 누적되면 게임오버.
- **목표 지표**: ① 만족시킨 모험가 수 ② 점수.
- **핵심 루프**: 모험가 등장 → 제련 4회(티어→속성 슬롯머신) → 만족도 판정 → 성공(점수+다음) / 실패(생명-1) → 생명 0이면 게임오버.
- **산출물**: **단일 HTML 파일**(`blacksmith.html`), Vanilla JS + CSS, 외부 라이브러리 없음. 모바일 세로 우선.
- **저장**: 최고 기록은 `localStorage`(bestCount, bestScore).
- **에셋**: `assets/` 폴더의 이미지(webp). 경로는 §8 참조. 에셋이 아직 없어도 동작하도록 플레이스홀더(색 박스/텍스트) 폴백을 둘 것.

---

## 1. 기술 요건

- 단일 `blacksmith.html` 한 파일에 HTML/CSS/JS 모두 포함 (참고: 기존 `job-dungeon.html` 방식).
- 외부 CDN·프레임워크 금지(오프라인 동작). 폰트는 시스템 폰트 또는 로컬.
- 세로 화면(모바일) 기준. 데스크톱에서도 세로 비율 유지(가운데 정렬, max-width ~480px).
- 사운드는 Web Audio API 또는 `<audio>`. 파일이 없으면 무음으로 폴백.
- 모든 텍스트 한국어.

---

## 2. 게임 데이터 (그대로 사용)

```javascript
// ===== 속성 풀 =====
const ATTRS = {
  물리: ["공격력","공격속도","정확도","방어구무시","치명피해","연속공격","출혈","처형","흡혈"],
  주문: ["주문력","시전속도","마나","저항관통","원소피해","마나재생","주문연쇄","보호막","둔화"],
  회복: ["치유량증가","저주해제","버프","재생","부활","신성","보호막부여","활력"],
  공통: ["치명타","소켓","범위증가","내구도","쿨다운감소","이동속도","행운","경험치","반사"],
  스탯: ["힘","민첩","지능","체력","정신력","전스탯"],
  저주: ["불안정","폭주","흡정","균열"],
};

// ===== 직업 7종 =====
// stat: 주스탯(이중 스탯은 배열 2개), special: T0 특화속성, weapons: 들고 오는 무기
const JOBS = {
  기사:   { stat:["힘"],        special:"도발",       weapons:["한손검","양손검"] },
  성기사: { stat:["힘","지능"],  special:"오라강화",   weapons:["한손검","메이스"] },
  힐러:   { stat:["지능"],      special:"치유강화",   weapons:["메이스","지팡이"] },
  마법사: { stat:["지능"],      special:"원소강화",   weapons:["지팡이","완드"] },
  도적:   { stat:["민첩"],      special:"훔치기",     weapons:["단검"] },
  레인저: { stat:["민첩","힘"],  special:"무조건명중", weapons:["활","장궁"] },
  용병:   { stat:["힘","민첩"],  special:"꿰뚫기",     weapons:["양손검","양손해머"] },
};

// ===== 무기 9종 적합도 =====
// 무효: 해당 카테고리 속성은 0점. 선호: 1.0. 나머지 유효 속성: 기본 0.5.
const WEAPON_AFFINITY = {
  단검:     { 무효:["주문","회복"], 선호:["공격속도","치명타","치명피해","방어구무시","출혈","흡혈","연속공격"] },
  한손검:   { 무효:["주문"],       선호:["공격력","정확도","치명타","신성","흡혈","반사"] },
  양손검:   { 무효:["주문","회복"], 선호:["공격력","치명피해","처형","방어구무시","출혈","연속공격"] },
  활:       { 무효:["주문","회복"], 선호:["정확도","공격속도","치명타","연속공격","출혈","이동속도"] },
  장궁:     { 무효:["주문","회복"], 선호:["공격력","치명피해","방어구무시","처형","정확도","범위증가"] },
  메이스:   { 무효:[],             선호:["공격력","신성","치유량증가","보호막부여","활력","정신력"] },
  양손해머: { 무효:["주문","회복"], 선호:["공격력","방어구무시","처형","출혈","둔화","내구도"] },
  지팡이:   { 무효:["물리"],       선호:["주문력","마나","시전속도","원소피해","주문연쇄","치유량증가","재생"] },
  완드:     { 무효:["물리","회복"], 선호:["주문력","시전속도","마나재생","원소피해","주문연쇄","보호막","둔화"] },
};

// ===== 모험가 묘사 변수 =====
const WEATHER = ["어느 날","화창한 날","비 오는 날","깜깜한 밤","안개 낀 날","눈 오는 날"];
const MOOD    = ["느긋한","다급한","숨을 헐떡이는","고통에 찬","이상해 보이는","후드를 쓴","침착한","평범한"];
const RACE    = ["인간 여성","인간 남성","드워프 여성","드워프 남성","엘프 여성","엘프 남성","다크엘프 여성","다크엘프 남성"];
const DARK_MOODS = ["이상해 보이는","후드를 쓴"];   // 저주 속성을 선호하는 성향
const RACE_TRAIT = { 다크엘프:"은신" };              // 종족 특성(연출용, v1에선 표시만)

// ===== 확률·가중치 (시뮬레이션 검증값) =====
const TIER_PROB      = { T0:2, T1:6, T2:10, T3:13, T4:16, T5:16, T6:13, T7:10, T8:7, T9:4, T10:3 }; // 상대 가중
const P_CURSE        = 0.05;   // 슬롯이 저주일 확률
const P_SOCKET_IN_T1 = 0.22;   // T1 결과 중 소켓일 확률
const PREF_WEIGHT    = 3;      // 일반 속성 추첨 시 선호 속성 가중

const TIER_WEIGHT = { T0:1.2, T1:1.0, T2:0.9, T3:0.8, T4:0.65, T5:0.55, T6:0.45, T7:0.3, T8:0.2, T9:0.1, T10:0.05 };
const TIER_GRADE  = { T0:"초대박", T1:"초대박", T2:"대박", T3:"대박", T4:"중박", T5:"중박", T6:"중박", T7:"별로", T8:"별로", T9:"최악", T10:"최악" };

const SATISFACTION_GOAL = { 초급:20, 중급:30, 고급:50, 특급:70 };   // 등급별 목표 만족도(%)
const SPECIALS = Object.values(JOBS).map(j => j.special);
```

---

## 3. 모험가 생성

문장 템플릿(입장 시 표시):
> `"{날씨}, 대장간으로 {상태} 모습의 {종족·성별} {직업}이(가) {등급} {무기}을(를) 들고 찾아왔습니다."`
> 예) "비 오는 날, 대장간으로 다급한 모습의 엘프 여성 마법사가 고급 지팡이를 들고 찾아왔습니다."
> 조사(이/가, 을/를)는 받침 판별로 자동 처리.

```javascript
const pick = (a) => a[Math.floor(Math.random() * a.length)];

// grade는 게임 진행도로 결정(§5). job→무기 풀에서 무기 선택.
function spawnAdventurer(grade) {
  const jobName = pick(Object.keys(JOBS));
  const job = JOBS[jobName];
  return {
    weather: pick(WEATHER),
    mood:    pick(MOOD),
    race:    pick(RACE),
    job:     jobName,
    grade,                       // 초급/중급/고급/특급
    weapon:  pick(job.weapons),
    goal:    SATISFACTION_GOAL[grade],
  };
}
```

---

## 4. 제련 (슬롯 생성)

- 한 무기당 **4슬롯**, 각 슬롯에 (티어, 속성) 1쌍. **속성 중복 금지.**
- 각 슬롯 결정 순서: ① 저주 판정(5%) → ② 티어 추첨 → ③ 속성 결정.
- **T0이 뜨면 그 손님 직업의 특화속성**(잭팟). **T1**은 22% 확률로 소켓. **T2~T10**은 일반 속성(선호 가중 3배).

```javascript
function rollTier() {
  const total = Object.values(TIER_PROB).reduce((a,b)=>a+b,0);
  let r = Math.random()*total;
  for (const [t,w] of Object.entries(TIER_PROB)) { r-=w; if (r<=0) return t; }
  return "T10";
}

function validNormalAttrs(weapon) {
  const aff = WEAPON_AFFINITY[weapon], out = [];
  for (const cat of ["물리","주문","회복","공통","스탯"]) {
    if (aff.무효.includes(cat)) continue;
    for (const a of ATTRS[cat]) if (a !== "소켓") out.push(a);
  }
  return out;
}

function pickNormalAttr(weapon) {
  const pool = validNormalAttrs(weapon), aff = WEAPON_AFFINITY[weapon];
  const w = pool.map(a => aff.선호.includes(a) ? PREF_WEIGHT : 1);
  let r = Math.random()*w.reduce((a,b)=>a+b,0);
  for (let i=0;i<pool.length;i++){ r-=w[i]; if (r<=0) return pool[i]; }
  return pool[pool.length-1];
}

// used: 이미 나온 속성 배열 (중복 방지)
function rollSlot(weapon, job, used) {
  if (Math.random() < P_CURSE) {
    const pool = ATTRS.저주.filter(c => !used.includes(c));
    const attr = pool.length ? pick(pool) : pick(ATTRS.저주);
    return { attr, tier: rollTier() };
  }
  const tier = rollTier();
  if (tier === "T0") return { attr: JOBS[job].special, tier };           // 본인 특화 잭팟
  if (tier === "T1" && Math.random() < P_SOCKET_IN_T1 && !used.includes("소켓"))
    return { attr: "소켓", tier };
  let attr, guard = 0;
  do { attr = pickNormalAttr(weapon); } while (used.includes(attr) && ++guard < 30);
  return { attr, tier };
}
```

---

## 5. 만족도 평가 + 게임 모드

### 5.1 만족도 공식
슬롯 1칸 점수 `v = (무기적합도 + 직업보너스) × 티어가중치` (무효면 0). 4칸 합산 → `min(100, round(Σv/4·100))`.

```javascript
function weaponFit(attr, weapon) {
  const aff = WEAPON_AFFINITY[weapon];
  if (attr === "소켓") return 0.8;                       // 만능
  if (aff.무효.some(c => ATTRS[c]?.includes(attr))) return 0;
  if (aff.선호.includes(attr)) return 1.0;
  return 0.5;                                            // 기타 유효 = 기본
}

// 저주: 어둠 성향 손님이면 선호+보너스, 아니면 무효
function slotValue(attr, tier, weapon, job, mood) {
  const J = JOBS[job];
  if (ATTRS.저주.includes(attr)) {
    if (!DARK_MOODS.includes(mood)) return 0;
    return (1.0 + 0.4) * TIER_WEIGHT[tier];
  }
  if (SPECIALS.includes(attr) && J.special !== attr) return 0;   // 특화가 비대상 직업 → 무효
  const own = (attr === J.special);
  const fit = own ? 1.0 : weaponFit(attr, weapon);
  if (fit === 0) return 0;
  let bonus = 0;
  if (["힘","민첩","지능"].includes(attr) && J.stat.includes(attr)) bonus += 0.3;
  if (own && tier === "T0") bonus += 0.6;
  return (fit + bonus) * TIER_WEIGHT[tier];
}

// slots: [{attr, tier} × 4]
function satisfaction(slots, weapon, job, mood) {
  const sum = slots.reduce((s,x)=> s + slotValue(x.attr, x.tier, weapon, job, mood), 0);
  return Math.min(100, Math.round(sum / 4.0 * 100));
}
```

### 5.2 게임 모드 (생명·난이도·점수)

```javascript
const LIVES = 3;                                  // 권장 생명 수
const BASE  = { 초급:10, 중급:25, 고급:60, 특급:150 };

// 난이도 곡선: 만족시킨 손님 수 n에 따라 등급 분포 상향
function weighted(pairs) {                         // [[값,가중], ...]
  const total = pairs.reduce((s,[,w])=>s+w,0);
  let r = Math.random()*total;
  for (const [v,w] of pairs){ r-=w; if (r<=0) return v; }
  return pairs[pairs.length-1][0];
}
function gradeByProgress(n) {
  if (n < 5)  return weighted([["초급",60],["중급",40]]);
  if (n < 10) return weighted([["초급",25],["중급",50],["고급",25]]);
  if (n < 16) return weighted([["중급",40],["고급",45],["특급",15]]);
  return weighted([["고급",45],["특급",55]]);
}

function newGame() { return { lives: LIVES, satisfied: 0, score: 0, streak: 0, over: false }; }

// 손님 1명 결과 반영. sat = 만족도(%), grade = 손님 등급
function resolveCustomer(s, grade, sat) {
  if (sat >= SATISFACTION_GOAL[grade]) {
    s.satisfied++; s.streak++;
    const mult = 1 + 0.1 * Math.min(s.streak, 10);            // 연속 콤보 최대 2배
    const over = Math.max(0, sat - SATISFACTION_GOAL[grade]) * 2;
    s.score += Math.floor((BASE[grade] + over) * mult);
  } else {
    s.lives--; s.streak = 0;
    if (s.lives <= 0) s.over = true;
  }
  return s;
}
```

### 5.3 한 라운드 전체 흐름
```
newGame()
반복:
  grade = gradeByProgress(state.satisfied)
  adv   = spawnAdventurer(grade)
  used=[]; slots=[]
  4회: slot = rollSlot(adv.weapon, adv.job, used); used.push(slot.attr); slots.push(slot)
  sat = satisfaction(slots, adv.weapon, adv.job, adv.mood)
  resolveCustomer(state, grade, sat)
  state.over 면 → 결과 화면
```

---

## 6. 연출 흐름 (슬롯머신)

한 슬롯 처리(4회 반복). **티어 먼저 → 속성 다음**, 단계마다 연출+리액션:
1. SPIN_TIER — 티어 릴 회전(가속→감속). 회전 SFX.
2. TIER_REVEAL — 티어 확정. 등급별 연출(아래) + SFX. 모험가 리액션 #1 (`DIALOGUE.tier[등급]`).
3. PAUSE — 약 0.4초 정적(기대감).
4. SPIN_ATTR — 속성 릴 회전.
5. ATTR_REVEAL — 속성 확정. 연출 + SFX. 모험가 리액션 #2 (아래 분기).
6. SLOT_COMMIT — 슬롯에 박힘, 만족도 게이지 갱신.
→ 4칸 끝나면 최종 만족도 판정 → 성공/실패 연출 → `DIALOGUE.result`.

**속성 발표 리액션 분기**: `slotValue`가
- 1.0 이상(선호/본인 특화) → `DIALOGUE.attr.적중`
- 0(무효) → `DIALOGUE.attr.빗나감`
- 그 외(기본 0.5대) → `DIALOGUE.attr.무난`
- 저주 + 어둠 성향 → `DIALOGUE.attr.저주_환희` / 저주 + 일반 → `DIALOGUE.attr.저주_경악`

**등급별 연출(이펙트 + 화면 흔들림 + 색)** — 에셋 `assets/vfx/` 사용, 없으면 CSS 색/애니로 폴백:
| 등급 | 비주얼 | 화면 | 리액션 톤 |
| --- | --- | --- | --- |
| 초대박 | 황금 폭발·파티클 | 강한 흔들림+플래시 | 환호 |
| 대박 | 파랑/보라 별빛 | 약한 흔들림 | 흡족 |
| 중박 | 흰 빛 | 없음 | 무덤덤 |
| 별로 | 회색 연기 | 없음 | 실망 |
| 최악 | 검은 연기·금간 효과 | 어두워짐 | 분노 |

구현 힌트: 릴은 CSS `transform: translateY` + ease-out / 화면 흔들림은 `@keyframes shake` / 시퀀스 제어는 `async/await` + `sleep(ms)`.

---

## 7. 대사 풀

```javascript
const DIALOGUE = {
  enter: {
    느긋한: ["이 무기 좀 손봐주게","천천히 봐주게나"],
    침착한: ["실력 있다는 소문 듣고 왔네","자네가 그 유명한 대장장이인가?"],
    평범한: ["이 무기 좀 손봐주게","강화 부탁하네"],
    다급한: ["빨리! 시간이 없어!","급하다, 서둘러주게!"],
    "숨을 헐떡이는": ["헉헉… 어서 강화를!","쫓기기 전에 끝내야 해!"],
    "고통에 찬": ["윽… 이 무기가 내 마지막 희망이야","쿨럭… 제발 서둘러…"],
    "이상해 보이는": ["…….","내가 원하는 게 뭔지 알 텐데?"],
    "후드를 쓴": ["흥미로운 손재주로군… 후훗","어둠을 두려워하지 않겠지?"],
  },
  tier: {
    초대박: ["큰거 왔나!?","자넬 믿어보겠네","제발 좋은거..","오오, 이건 빛부터 다르잖아!","이런 명품이 내 손에…!","심장이 떨리는군. 이거다!","역시 이 바닥 최고야!","전설로 남을 물건이 되겠어","내 평생 이런 건 처음 봐","신의 손길이 깃들었군"],
    대박: ["역시 믿었다구","좋은거 부탁드립니다. 선생님","오, 제법인데?","이 정도면 훌륭하지","솜씨가 살아있구만","기대 이상이야","흠, 마음에 드는군","값은 톡톡히 하겠어","맡기길 잘했어","이거라면 싸울 맛 나겠어"],
    중박: ["그저그런 대장장이구만","길거리에 널린 평범한 대장장이놈","뭐… 나쁘진 않네","그럭저럭이군","특별할 건 없구만","이걸로 만족해야 하나?","흠… 무난하군","딱 값어치만큼이네","감흥은 없지만 쓸 만은 해","기대도 안 했다만"],
    별로: ["망치는 잡아본적이 있냐?","망치가 뭔줄 알기나 아냐?","이게 최선이야? 진심으로?","허… 시간 낭비였군","돈이 아깝다 아까워","견습생이 만든 줄 알았네","이런 걸 물건이라고…","실력이 영 녹슬었구만","내 무기가 운다, 울어","다른 대장간을 찾아야 하나"],
    최악: ["쓸모없는 놈이구나","찢어죽일 놈","후회하게 만들어주마","이 사기꾼 같으니!","내 무기를 망쳐놨어!","당장 물어내라!","두 번 다시 오나 봐라","이딴 게 대장장이라고?","차라리 돌멩이가 낫겠다","네놈 솜씨에 치가 떨린다"],
  },
  attr: {
    적중: ["그래, 바로 이거야!","내가 원하던 속성이군!","완벽해, 완벽하다고!","이거면 충분해!","역시 통하는군!","내 무기에 딱이야","이런 옵션을 노렸지","오, 제대로 박혔어!"],
    무난: ["뭐, 없는 것보단 낫지","쓸 데가 있으려나","나쁘진 않군","그럭저럭 쓰겠어","흠, 이것도 받아두지","아쉽지만 넘어가지"],
    빗나감: ["이게 나한테 무슨 소용이야","쯧… 헛수고군","(깊은 한숨)","내 무기엔 안 맞잖아!","(말없이 고개를 젓는다)","이런 걸 누가 쓰라고","버리는 슬롯이군","허탈하구만…"],
    저주_환희: ["크큭… 바로 이 어둠이야","금지된 힘이라… 좋아","이거다. 내가 찾던 저주!","위험할수록 끌리는 법이지","어둠이 날 선택했군"],
    저주_경악: ["이… 이건 저주받은 물건이잖아!","당장 치워! 불길해","사악한 기운이… 싫어!","이런 걸 내게 주려는 건가?","(겁에 질려 물러선다)"],
  },
  result: {
    만족: ["훌륭하군. 값은 후하게 쳐주지","이거면 됐어. 고맙네","자네 이름을 기억해두겠어","또 오겠네, 대장장이","이제야 싸울 맛 나는군","명성이 헛되지 않았어","친구들에게도 알리지","만족스럽군. 떠나겠네"],
    불만족: ["실망이군. 두 번 다시 안 와","이런 곳에 시간을 버리다니","네 명성도 여기까지군","다신 자네에게 맡기지 않겠어","최악이야. 소문내고 다니지","이게 끝이야? 한심하군","내 기대를 저버렸어","이 대장간은 곧 망할 거야"],
  },
  jobEnter: {
    기사:"기사의 검에 부끄럽지 않게 해주게", 성기사:"신의 가호가 이 무기에 깃들기를",
    힐러:"누군가를 지킬 도구라네. 정성껏 부탁하네", 마법사:"마력을 견딜 물건이어야 하네",
    도적:"조용하고, 날카롭게… 알지?", 레인저:"백 보 밖을 꿰뚫을 물건으로", 용병:"돈값만 하면 된다. 잔말 말고",
  },
};
const line = (arr) => arr[Math.floor(Math.random()*arr.length)];
```

---

## 8. 에셋 (경로·파일명)

`assets/` 아래. **이미지가 없으면 색 박스/이름 텍스트로 폴백**(에셋 없이도 게임이 돌아가야 함).

```
assets/
  bg/        forge.webp, forge_rain.webp, forge_night.webp, forge_fog.webp, forge_snow.webp
  weapons/   dagger.webp, sword_1h.webp, sword_2h.webp, bow.webp, longbow.webp,
             mace.webp, hammer_2h.webp, staff.webp, wand.webp
  portraits/ knight.webp, paladin.webp, healer.webp, mage.webp, rogue.webp, ranger.webp, mercenary.webp
  ui/        anvil.webp, hammer.webp, heart_full.webp, heart_empty.webp, coin.webp,
             ore.webp, gem.webp, badge_bronze.webp, badge_silver.webp, badge_gold.webp,
             badge_diamond.webp, reel_frame.webp, bubble.webp
  vfx/       jackpot.webp, great.webp, normal.webp, bad.webp, worst.webp   (선택)
```

키 ↔ 파일 매핑(코드에서 사용):
- 무기: 단검→dagger, 한손검→sword_1h, 양손검→sword_2h, 활→bow, 장궁→longbow, 메이스→mace, 양손해머→hammer_2h, 지팡이→staff, 완드→wand
- 직업: 기사→knight, 성기사→paladin, 힐러→healer, 마법사→mage, 도적→rogue, 레인저→ranger, 용병→mercenary
- 등급 뱃지: 초급→badge_bronze, 중급→badge_silver, 고급→badge_gold, 특급→badge_diamond
- 배경: 날씨(WEATHER) → forge(어느날/화창=forge), 비→forge_rain, 깜깜한 밤→forge_night, 안개→forge_fog, 눈→forge_snow

---

## 9. 화면 레이아웃 (모바일 세로, 위→아래)

1. **모험가 영역** — 초상화 + 등급 뱃지 + 이름(종족·성별·직업) + 말풍선(리액션)
2. **만족도 게이지** — 현재 만족도 / 목표선 표시(채워지는 막대는 CSS)
3. **작업 영역** — 대상 무기 + 슬롯머신 릴 2단(티어 릴 / 속성 릴) + 모루·망치
4. **슬롯 트레이** — 확정된 속성 4칸(확정/미확정)
5. **상태 바** — 생명(하트 ×3) · 만족시킨 수 · 점수
6. **액션 버튼** — "제련하기 (n/4)" · 음소거 토글

- 게이지 막대·버튼·릴 안의 텍스트/숫자는 **CSS/DOM으로** 그린다(이미지 아님).
- 등급·숫자·로고 글자는 코드로 얹는다(이미지에 글자 넣지 않음).

---

## 10. 결과 화면 (게임오버)

- 표시: 만족시킨 손님 수, 최종 점수, 최고 기록(localStorage `bestCount`/`bestScore`, 갱신 시 강조).
- "다시 도전" 버튼 → `newGame()` 재시작.

---

## 11. 구현 순서 (이 순서로 진행)

1. **로직 코어(텍스트만)**: §2~§5 데이터·함수로 모험가 생성→제련 4슬롯→만족도→점수/생명/게임오버가 콘솔/단순 DOM으로 한 판 돌아가게.
2. **화면 골격**: §9 레이아웃을 CSS로(에셋 없이 색 박스 폴백). 제련 버튼으로 한 슬롯씩 진행.
3. **연출**: §6 슬롯머신 시퀀스(릴 회전·감속·정적), 등급별 효과, 만족도 게이지 애니메이션.
4. **대사**: §7 DIALOGUE 연결(입장/티어/속성/결과).
5. **이미지·사운드**: §8 에셋 경로 연결(폴백 유지), SFX.
6. **마감**: 결과 화면·최고기록·음소거·재시작.

---

## 12. 검증 기준 (밸런스 sanity check)

구현 후, 손님 10,000명을 자동 시뮬(에셋·연출 없이 satisfaction만)했을 때 **등급별 클리어율**이 대략 아래 범위면 정상:
- 초급(목표 20%): **~97%**
- 중급(목표 30%): **~82%**
- 고급(목표 50%): **~31%**
- 특급(목표 70%): **~8%**
- 평균 만족도 ~44%. 한 판(생명 3) 평균 만족 손님 수 ~10명(상위 13~21명).

크게 벗어나면 §2의 `TIER_PROB` / `PREF_WEIGHT` / `P_CURSE` / `P_SOCKET_IN_T1` 또는 §5.2 난이도 곡선을 조정. 만족도 공식(§5.1) 자체는 고정.

---

## 13. 범위 밖 (v2 이후, 지금은 구현하지 않음)

- 키우기·보상·경제(골드·재료 사용, 대장간/도구 업그레이드)
- 플레이어 주도성(리롤, 속성 잠금, 재료 투입)
- 직업×성별 전체 초상화, 표정 5종 세트, 직업 2번째 특화, 종족 특성 효과
- 손님 거절/스킵, 생명 회복, 시간 제한
