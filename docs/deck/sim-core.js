"use strict";
/* ══════════════════════════════════════════════════════════════════════
   sim-core.js — 제도 규칙 계산 코어
   `sim/sim.py` 와 같은 것을 계산한다. 상수·산식·적용 조건을 sim.py 에 맞췄다.

   sim.py 와 다른 점(의도적)
   - 난수 생성기가 다르다(mulberry32 vs Mersenne Twister). 같은 시드로도 값이
     완전히 같지는 않다. 반복 100회 이상에서 ±0.02 이내로 수렴한다.
   - `tie`(동점 부여 금지, 개정 2)는 이 파일에만 있는 확장이다. sim.py 에는 없다.
     체크를 풀면 균등 성향 평정자에게 순위 신호가 없는 상황을 모사한다.

   문서(01 진단 §3-3)의 수치는 sim.py 를 400회 돌린 값이다.
   ══════════════════════════════════════════════════════════════════════ */
window.SIM = (function () {

  /* ─── 상수 — sim.py 와 동일 ─────────────────────────────────── */
  const ORG = [
    ["경영본부",     { 기획조정실:10, 미래인재실:8, 재무계약실:14, 성과윤리실:6 }],
    ["정책본부",     { 정책전략실:11, 원스톱지원실:8, 사업관리실:12, 디지털AI실:9 }],
    ["스케일업본부", { 딥테크전략실:12, 민관협력실:11, 대학창업실:14, 창업확산실:16, 대전팁스팀:6 }],
    ["창업촉진본부", { 지역전략실:12, 예비재도전실:9, 초기도약실:12 }],
    ["글로벌본부",   { 글로벌전략실:11, 글로벌허브실:6, 글로벌협력실:10, 글로벌확산TF:9 }],
    ["원장직속",     { 감사실:4, 홍보실:3 }]
  ];
  const N_EXTREME = 2;                    // 본부 5개 중 극단 성향 수 [조합 관찰]
  const RANK_MIX  = [["1(나)급",4],["2급",11],["3급",29],["4급",40],["5급",107],["공무직",5]];
  const ABSOLUTE_REFORM = ["공무직"];     // 개정 7
  const W_CORE=.85, W_1ST=.60, W_2ND=.40, W_MULTI=.10, W_COMMON=.05;
  const GRADE=[["S",.20],["A",.30],["B",.40],["C",.10]];
  const BANDS={S:100,A:90,B:80,C:70};
  const SPREAD_O   = 7.0;                 // 원장직속 부여폭 — sim.py SPREAD["O"] 고정값
  const MEAN_SLACK = 3.0;                 // 현행 base = 평균 − U(0,3)  ← sim.py mean_cap_slack
  const ADJ_COEF   = 4.0;                 // [별표 9] 제7호 — 신호 1σ당 조정 점수
  const MOVE_MIX=[["잔류",.55],["1월 전보",.12],["7월 전보",.12],
                  ["연중 조직개편",.08],["중도 휴직",.07],["중도 파견",.06]];
  const SEED = 20260910;

  const DEPTS=[], DEPT_HQ=[];
  ORG.forEach(([, ds], h) => { for (const k in ds) { DEPT_HQ.push(h); DEPTS.push(ds[k]); } });
  const N_PEOPLE = DEPTS.reduce((a,b)=>a+b,0);
  const N_HQ = ORG.length, DIRECTOR_HQ = ORG.length - 1;

  /* ─── 수학 ──────────────────────────────────────────────────── */
  let _s = SEED >>> 0, _g = null;
  const srand = s => { _s = s >>> 0; _g = null; };
  function rnd(){ _s=(_s+0x6D2B79F5)>>>0; let t=_s;
    t=Math.imul(t^t>>>15,t|1); t^=t+Math.imul(t^t>>>7,t|61);
    return ((t^t>>>14)>>>0)/4294967296; }
  function gauss(){ if(_g!==null){const v=_g;_g=null;return v;}
    let u=0,v=0; while(u===0)u=rnd(); while(v===0)v=rnd();
    const r=Math.sqrt(-2*Math.log(u)), th=2*Math.PI*v; _g=r*Math.sin(th); return r*Math.cos(th); }
  function probit(p){
    const a=[-3.969683028665376e+01,2.209460984245205e+02,-2.759285104469687e+02,
             1.383577518672690e+02,-3.066479806614716e+01,2.506628277459239e+00];
    const b=[-5.447609879822406e+01,1.615858368580409e+02,-1.556989798598866e+02,
             6.680131188771972e+01,-1.328068155288572e+01];
    const c=[-7.784894002430293e-03,-3.223964580411365e-01,-2.400758277161838e+00,
             -2.549732539343734e+00,4.374664141464968e+00,2.938163982698783e+00];
    const d=[7.784695709041462e-03,3.224671290700398e-01,2.445134137142996e+00,3.754408661907416e+00];
    const pl=0.02425; let q,r;
    if(p<pl){q=Math.sqrt(-2*Math.log(p));
      return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5])/((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1);}
    if(p>1-pl){q=Math.sqrt(-2*Math.log(1-p));
      return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5])/((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1);}
    q=p-.5; r=q*q;
    return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q/(((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1);
  }
  const _bl = new Map();
  function blom(n){ if(_bl.has(n))return _bl.get(n);
    const o=[]; for(let i=1;i<=n;i++)o.push(probit((i-.375)/(n+.25))); _bl.set(n,o); return o; }
  function ranks(v){ const ix=v.map((_,i)=>i).sort((a,b)=>v[a]-v[b]);
    const r=new Array(v.length); ix.forEach((i,p)=>r[i]=p+1); return r; }
  function spearman(x,y){ const rx=ranks(x),ry=ranks(y),n=x.length,m=(n+1)/2;
    let num=0,dx=0,dy=0;
    for(let i=0;i<n;i++){const a=rx[i]-m,b=ry[i]-m;num+=a*b;dx+=a*a;dy+=b*b;}
    const den=Math.sqrt(dx*dy); return den?num/den:0; }
  const clamp=(v,lo=60,hi=100)=>v<lo?lo:v>hi?hi:v;
  const mean=a=>a.reduce((x,y)=>x+y,0)/a.length;

  /* ─── 직급 배정 (최대잔여법) ─────────────────────────────────── */
  function rankLabels(n){
    const tot=RANK_MIX.reduce((a,[,c])=>a+c,0);
    const q=RANK_MIX.map(([l,c])=>[l,n*c/tot]);
    const cnt={}; let used=0;
    q.forEach(([l,v])=>{cnt[l]=Math.floor(v);used+=cnt[l];});
    q.map((x,i)=>[i,q[i][1]-Math.floor(q[i][1])]).sort((a,b)=>b[1]-a[1]).slice(0,n-used)
      .forEach(([i])=>cnt[q[i][0]]++);
    const out=[]; RANK_MIX.forEach(([l])=>{for(let k=0;k<cnt[l];k++)out.push(l);});
    for(let i=out.length-1;i>0;i--){const j=Math.floor(rnd()*(i+1));[out[i],out[j]]=[out[j],out[i]];}
    return out.slice(0,n);
  }

  /* 본부 유형 — 어느 본부인지 지정하지 않고 반복마다 무작위 배정 */
  function drawHqTypes(){
    const ix=[]; for(let h=0;h<N_HQ;h++) if(h!==DIRECTOR_HQ) ix.push(h);
    for(let i=ix.length-1;i>0;i--){const j=Math.floor(rnd()*(i+1));[ix[i],ix[j]]=[ix[j],ix[i]];}
    const ty=new Array(N_HQ); ty[DIRECTOR_HQ]="O";
    ix.forEach((h,k)=>ty[h]= k<N_EXTREME ? "S" : "N");
    return ty;
  }

  /* ─── 등급 배정 — 규칙 제26조① 직급별 ───────────────────────── */
  function allocGroup(idx,scores,grade,pts,noC){
    const m=idx.length; if(!m)return;
    const cnt=[]; let acc=0;
    for(let k=0;k<GRADE.length-1;k++){const c=Math.round(m*GRADE[k][1]);cnt.push(c);acc+=c;}
    cnt.push(Math.max(0,m-acc));
    // 개정 10⑤ — sim.py 는 모드와 무관하게 항상 적용한다
    if(noC && m<10 && cnt[3]>0){cnt[2]+=cnt[3];cnt[3]=0;}
    const order=idx.slice().sort((a,b)=>scores[b]-scores[a]);
    let i2=0;
    for(let k=0;k<GRADE.length;k++){
      const g=GRADE[k][0],hi=BANDS[g],c=cnt[k];
      for(let j=0;j<c&&i2<m;j++,i2++){const i=order[i2];grade[i]=g;pts[i]=c?hi-(10/c)*j:hi;}
    }
  }
  function assignGrades(scores,rankOf,absolute,noC){
    const n=scores.length, grade=new Array(n), pts=new Array(n).fill(0);
    const groups=new Map();
    for(let i=0;i<n;i++){const k=rankOf(i);if(!groups.has(k))groups.set(k,[]);groups.get(k).push(i);}
    groups.forEach((idx,lbl)=>{
      if(absolute && absolute.indexOf(lbl)>=0){idx.forEach(i=>{grade[i]="B";pts[i]=BANDS.B;});return;}
      allocGroup(idx,scores,grade,pts,noC);
    });
    return [grade,pts];
  }

  /* ─── 점수 부여 ─────────────────────────────────────────────── */
  function award(members,gtype,sig,mode,P,out,adjust){
    if(!members.length)return;
    const s=members.map(sig), rk=ranks(s), bl=blom(members.length);
    let base,sd;
    if(mode==="reform"){ base=P.mean; sd=P.sd; }
    else if(gtype==="O"){ base=P.mean; sd=SPREAD_O; }      // 원장 — 평균 제약 미적용
    else { base=P.mean - rnd()*MEAN_SLACK; sd=(gtype==="S"?P.ext:P.even); }
    for(let k=0;k<members.length;k++) out[members[k]]=clamp(base+sd*bl[rk[k]-1]);
    // [별표 9] 제7호 — 1차 평가자 ±N점 조정, 평가군 내 합계 0.
    // 조정은 '평가자 자신의 신호'(선호가 섞인 값)에 따른다.
    if(mode==="reform" && adjust && P.adj>0 && members.length>1){
      const m=mean(s);
      const adj=s.map(v=>Math.max(-P.adj,Math.min(P.adj,ADJ_COEF*(v-m))));
      const ma=mean(adj);
      for(let k=0;k<members.length;k++) out[members[k]]=clamp(out[members[k]]+adj[k]-ma);
    }
  }

  const DEF = { sd:7, mean:80, ext:13, even:2, fav:.7, mix:.5, adj:5,
                reps:100, tie:true, abs:true, noC:true };

  /* ─── 본 시뮬레이션 ─────────────────────────────────────────── */
  function run(opt){
    const P=Object.assign({},DEF,opt||{});
    const modes=["current","reform"], res={};
    modes.forEach(m=>res[m]={
      sM:{S:[0,0],N:[0,0]}, cM:{S:[0,0],N:[0,0]},
      sH:{S:[0,0],N:[0,0],O:[0,0]}, rho:[],
      dist:{S:{S:0,A:0,B:0,C:0}, N:{S:0,A:0,B:0,C:0}}, nT:{S:0,N:0}
    });
    srand(SEED);
    for(let r=0;r<P.reps;r++){
      const deptTy=DEPTS.map(()=>rnd()<P.mix?"S":"N"), hqTy=drawHqTypes();
      const people=[], dmem=DEPTS.map(()=>[]), hmem=ORG.map(()=>[]);
      DEPTS.forEach((sz,d)=>{ for(let k=0;k<sz;k++){
        people.push({a:gauss(),f:gauss(),d:d});
        dmem[d].push(people.length-1); hmem[DEPT_HQ[d]].push(people.length-1); }});
      rankLabels(people.length).forEach((g,i)=>people[i].g=g);
      const ability=people.map(p=>p.a);
      modes.forEach(m=>{
        const noTie = !P.tie && m==="reform";
        const mkSig=ty=>{ const w=(ty==="S"?P.fav:0);
          return i => (noTie && ty==="N") ? rnd() : (1-w)*people[i].a + w*people[i].f; };
        const s1=new Array(people.length), s2=new Array(people.length);
        for(let d=0;d<dmem.length;d++) award(dmem[d],deptTy[d],mkSig(deptTy[d]),m,P,s1,true);
        for(let h=0;h<hmem.length;h++) award(hmem[h],hqTy[h],mkSig(hqTy[h]),m,P,s2,false);
        const total=new Array(people.length);
        for(let i=0;i<people.length;i++){
          const mu=clamp(92+4*gauss(),20,100), co=clamp(95+4*gauss(),70,100);
          total[i]=W_CORE*(W_1ST*s1[i]+W_2ND*s2[i])+W_MULTI*mu+W_COMMON*co;
        }
        const [grade,pts]=assignGrades(total, i=>people[i].g,
          (m==="reform"&&P.abs)?ABSOLUTE_REFORM:null, P.noC);
        const R=res[m];
        for(let i=0;i<people.length;i++){
          const mt=deptTy[people[i].d], ht=hqTy[DEPT_HQ[people[i].d]];
          R.sM[mt][1]++; R.cM[mt][1]++; R.sH[ht][1]++;
          if(grade[i]==="S"){R.sM[mt][0]++; R.sH[ht][0]++;}
          if(grade[i]==="C") R.cM[mt][0]++;
          if(grade[i]){ R.dist[mt][grade[i]]++; R.nT[mt]++; }
        }
        R.rho.push(spearman(ability,pts));
      });
    }
    const pc=o=>o[1]?100*o[0]/o[1]:0;
    const pack=m=>{ const R=res[m];
      const dist={}; ["S","N"].forEach(t=>{ dist[t]={};
        ["S","A","B","C"].forEach(g=>dist[t][g]= R.nT[t]?100*R.dist[t][g]/R.nT[t]:0); });
      return { sExt:pc(R.sM.S), sEven:pc(R.sM.N), cExt:pc(R.cM.S), cEven:pc(R.cM.N),
               sHqExt:pc(R.sH.S), sHqEven:pc(R.sH.N), rho:mean(R.rho), dist:dist }; };
    return { current:pack("current"), reform:pack("reform"), reps:P.reps };
  }

  /* ─── 전보 시뮬레이션 ───────────────────────────────────────── */
  function transfer(opt){
    const P=Object.assign({},DEF,{dep:.6,nw:.8,reps:60},opt||{});
    const names=MOVE_MIX.map(x=>x[0]), out={};
    ["current","reform"].forEach(m=>out[m]=Object.fromEntries(names.map(n=>[n,[0,0,0]])));
    srand(SEED);
    for(let r=0;r<P.reps;r++){
      const nd=DEPTS.length, deptTy=DEPTS.map(()=>rnd()<P.mix?"S":"N"), people=[];
      DEPTS.forEach((sz,d)=>{ for(let k=0;k<sz;k++){
        let x=rnd(),cum=0,mt=names[names.length-1];
        for(const [nm,w] of MOVE_MIX){cum+=w;if(x<=cum){mt=nm;break;}}
        let seg;
        if(mt==="잔류"||mt==="1월 전보") seg=[[d,1,false,false]];
        else if(mt==="7월 전보") seg=[[d,.5,true,false],[Math.floor(rnd()*nd),.5,false,false]];
        else if(mt==="연중 조직개편") seg=[[d,.9,true,false],[Math.floor(rnd()*nd),.1,false,true]];
        else seg=[[d,.5,true,false]];
        people.push({a:gauss(),f:gauss(),mt:mt,seg:seg}); }});
      rankLabels(people.length).forEach((g,i)=>people[i].g=g);
      ["current","reform"].forEach(m=>{
        const grp=DEPTS.map(()=>[]);
        people.forEach((p,i)=>p.seg.forEach(([d,w,o,nw])=>grp[d].push([i,w,o,nw])));
        const part=new Map();
        grp.forEach((mem,d)=>{
          if(!mem.length)return;
          const ty=deptTy[d], w=(ty==="S"?P.fav:0);
          const sig=mem.map(([i,,o,nw])=>{ let s=(1-w)*people[i].a+w*people[i].f;
            if(m!=="reform"){ if(o)s-=P.dep; if(nw)s-=P.nw; } return s; });
          const rk=ranks(sig), bl=blom(mem.length);
          const sd=(m==="reform")?P.sd:(ty==="S"?P.ext:P.even);
          const base=(m==="reform")?P.mean:(P.mean - rnd()*MEAN_SLACK);
          mem.forEach(([i],k)=>part.set(i+"|"+d, clamp(base+sd*bl[rk[k]-1])));
        });
        const total=people.map((p,i)=>{ let num=0,den=0;
          p.seg.forEach(([d,w])=>{num+=part.get(i+"|"+d)*w;den+=w;}); return num/den; });
        const [grade,pts]=assignGrades(total, i=>people[i].g,
          (m==="reform"&&P.abs)?ABSOLUTE_REFORM:null, P.noC);
        people.forEach((p,i)=>{const a=out[m][p.mt];a[1]++;a[2]+=pts[i];if(grade[i]==="S")a[0]++;});
      });
    }
    const fin={};
    ["current","reform"].forEach(m=>{ fin[m]={};
      const base=out[m]["잔류"][2]/out[m]["잔류"][1];
      names.forEach(n=>{const a=out[m][n];
        fin[m][n]={s:100*a[0]/a[1], pt:a[2]/a[1], d:a[2]/a[1]-base};}); });
    return { data:fin, names:names };
  }

  return { run, transfer, DEF, ORG, RANK_MIX, MOVE_MIX, GRADE, BANDS,
           N_PEOPLE, DEPTS, N_EXTREME, ADJ_COEF, MEAN_SLACK, SEED };
})();
