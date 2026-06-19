// 대장장이 키우기 — 밸런스 시뮬레이터 (Node 러너)
// blacksmith.html 의 게임 로직을 그대로 로드해 window.__simulate / __simulateGame 을 실행.
// 사용:  node simulate.mjs
import fs from 'fs';
import vm from 'vm';

const html = fs.readFileSync(new URL('./blacksmith.html', import.meta.url), 'utf8');
const code = html.match(/<script>([\s\S]*?)<\/script>/)[1];

// --- 최소 DOM 스텁(로직 코어는 DOM 비의존, 상단 바인딩만 통과시키면 됨) ---
const cache = {};
const makeEl = () => new Proxy({ style:{}, dataset:{}, classList:{add(){},remove(){},toggle(){},contains(){return false;}} }, {
  get(t,p){ if(p in t) return t[p];
    if(p==='children') return [makeEl()];
    if(p==='querySelector') return ()=> (t.__img ||= makeEl());
    if(['appendChild','removeChild','remove','setAttribute','addEventListener','animate'].includes(p)) return ()=>{};
    if(p==='offsetWidth'||p==='offsetHeight') return 56;
    return undefined; },
  set(t,p,v){ t[p]=v; return true; }
});
const document = { getElementById:(id)=> (cache[id] ||= makeEl()), createElement:()=>makeEl(), querySelector:()=>makeEl() };
class A { constructor(){this.currentTime=0;this.destination={};this.state='running';}
  createOscillator(){return{frequency:{},connect(){},start(){},stop(){}};} createGain(){return{gain:{setValueAtTime(){},exponentialRampToValueAtTime(){}},connect(){}};} resume(){} }
const ctx = { document, console, Math, Object, Array, Number, String, JSON,
  localStorage:{getItem(){return null;},setItem(){}}, AudioContext:A, webkitAudioContext:A,
  setTimeout:(fn)=>{Promise.resolve().then(fn);return 0;}, clearTimeout(){} };
ctx.window = ctx;
vm.createContext(ctx);
vm.runInContext(code, ctx, { filename:'blacksmith.inline.js' });

// ---- 출력 헬퍼 ----
const N = 30000;
const pad = (s,w)=> String(s).padEnd(w);
const padL = (s,w)=> String(s).padStart(w);

console.log('\n════════ (1) 만족도 공식 sanity — 중급 고정·리롤 없음 (SPEC §12 기준) ════════');
console.log('   기준값: 초급~97% 중급~82% 고급~31% 특급~8%, 평균~44%');
const f = ctx.__simulate(N);
console.log('   결과 : 초급 %s  중급 %s  고급 %s  특급 %s  | 평균만족도 %s',
  f.초급, f.중급, f.고급, f.특급, f.평균만족도);

console.log('\n════════ (2) 실제 한 판 생존 시뮬 — 리롤 전략 비교 ════════');
console.log('   (생명3·난이도곡선 포함. rerolls=0 은 리롤 도입 전 원본과 동일 분포)\n');

const rows = [
  { label:'리롤 0 (원본)',        opts:{ games:N, rerolls:0, quiet:true } },
  { label:'리롤 1 · 죽은슬롯만',   opts:{ games:N, rerolls:1, threshold:0, quiet:true } },
  { label:'리롤 2 · 죽은슬롯만',   opts:{ games:N, rerolls:2, threshold:0, quiet:true } },
  { label:'리롤 2 · 약슬롯(≤0.3)', opts:{ games:N, rerolls:2, threshold:0.3, quiet:true } },
];

const head = ['전략','평균만족','중앙','상위10%','최고','평균점수','초급','중급','고급','특급'];
const W    = [16, 8, 5, 8, 6, 9, 7, 7, 7, 7];
console.log(head.map((h,i)=> i===0?pad(h,W[i]):padL(h,W[i])).join(' '));
console.log(W.map(w=>'─'.repeat(w)).join(' '));
for(const r of rows){
  const o = ctx.__simulateGame(r.opts);
  const c = o.등급별클리어율;
  const cells = [
    pad(r.label, W[0]),
    padL(o.평균만족손님, W[1]),
    padL(o.중앙값, W[2]),
    padL(o.상위10퍼, W[3]),
    padL(o.최고, W[4]),
    padL(o.평균점수, W[5]),
    padL((c.초급??'-')+'%', W[6]),
    padL((c.중급??'-')+'%', W[7]),
    padL((c.고급??'-')+'%', W[8]),
    padL((c.특급??'-')+'%', W[9]),
  ];
  console.log(cells.join(' '));
}
console.log('\n(클리어율 = 실제 게임에서 등장한 해당 등급 손님 중 만족시킨 비율)');
