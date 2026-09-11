"""Generate the opening animation for the video's first beat.

    python scripts/make_opening.py             # writes assets/opening.html
    python scripts/make_opening.py --open      # and opens it

Screen-record the result. One self-contained HTML file, like `out/report.html`:
inline CSS, inline SVG, one inline script, no CDN, no webfonts, no network
request, nothing to install. Space plays and replays, h hides the hint.

**Every word on screen is read from `data/seed_reports.json`.** The claim this
beat makes is that four real reports name one place four ways and share no
content word. Typing an approximation of them in here would turn a
demonstration back into a claim. The four are found by the place each one names,
and this exits with an error if the seed set stops containing them.


Why this beat is not amber on dusk
----------------------------------

The rest of the project is BRANDING.md's dusk palette. This beat is warm paper,
deliberately, and then it becomes dusk in the last two seconds.

Everything before the product exists happens in daylight: a street, a group
chat, ordinary life, more of it than anyone can read. That is not Porchlight's
world, it is the world Porchlight is answering. Dropping to dusk on the wordmark
is the light going down and the porch light coming on, which is the transition
the name is built on.

The rule that matters survives intact: **no amber anywhere in this file.** Amber
stays dormant until the single alert later in the video, so the restraint still
reads as restraint. If this ever needs to be dusk throughout, the palette is one
block of custom properties at the top of the template.


The sequence
------------

    pile      ordinary neighbourhood traffic arriving, accelerating
    mute      it recedes: blurs, desaturates, stops moving. Nobody is reading
    surface   the four that matter rise in front of that blurred noise
    ring      the place each one names, ringed in ink
    strike    all four struck through in one gesture
    converge  the four names lift off the cards and collapse into the one place
    dusk      the ground turns and the wordmark lands

Motion follows the motion-design tokens. This is illustrative rather than
product UI, so it earns the long durations: ease-out-expo for entrances at
around a second, ease-in-out-quart for the ground turning. Transform, opacity
and filter only, so nothing here touches layout. Nothing scales from zero.
"""

from __future__ import annotations

import json
import sys
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEED = ROOT / "data" / "seed_reports.json"
OUT = ROOT / "assets" / "opening.html"

# The place each cluster report names, in filing order. That no two share a
# content word is the premise of the video's first minute.
PLACES = ["mailboxes", "post boxes", "where the packages get dropped",
          "delivery lockers"]

# Ordinary traffic for the pile-up. Picked for being unmistakably the stuff of a
# real neighbourhood chat, not for any property of the run.
CHATTER_HINTS = ["pothole", "street light", "Bins have been left",
                 "branch came down", "Fireworks", "flattened boxes",
                 "graffiti", "hose reel"]

# Seconds. Read against roughly 150 words of narration.
TIMING = {
    "pile_start": 0.5, "pile_gap": 1.55, "pile_decay": 0.9,
    "mute": 11.2, "quiet": 2.6,
    "card_gap": 5.4,
    "ring_gap": 1.1, "strike_gap": 0.22,
    "converge": 1.6, "dusk": 2.0,
}


def load() -> dict:
    rows = json.loads(SEED.read_text(encoding="utf-8"))["reports"]
    rows = sorted(rows, key=lambda r: r["timestamp"])

    cluster = []
    for place in PLACES:
        hit = next((r for r in rows if place in r["text"]), None)
        if hit is None:
            raise SystemExit(
                f"No seed report mentions {place!r}. This beat is built from the "
                f"four reports that name one place four ways. If the seed set "
                f"changed, update PLACES to match it."
            )
        cluster.append({"text": hit["text"], "place": place, "zone": hit["zone"]})

    zones = {c["zone"] for c in cluster}
    if len(zones) != 1:
        raise SystemExit(
            f"The four reports resolve to more than one zone ({sorted(zones)}). "
            f"The closing move collapses them into a single place, which only "
            f"means anything if there is one."
        )

    taken = {c["text"] for c in cluster}
    chatter = []
    for hint in CHATTER_HINTS:
        hit = next((r for r in rows
                    if hint in r["text"] and r["text"] not in taken), None)
        if hit:
            chatter.append(hit["text"])
    if len(chatter) < 6:
        raise SystemExit("Not enough ordinary reports found for the pile-up.")

    return {"cluster": cluster, "chatter": chatter, "zone": zones.pop()}


PAGE = r"""<title>Porchlight opening</title>
<style>
  :root {
    /* Warm paper. The world before the product. */
    --paper:#F5F1E8;
    --paper-lo:#EFEADE;
    --ink:#16233F;          /* deep blue, used as type and never as ground */
    --ink-soft:#42526F;
    --accent:#2E5BD8;       /* the annotating hand */

    /* Where it lands. BRANDING.md, unchanged. */
    --dusk:#14161A;
    --chalk:#EFEAE0;
    --dim:#9A958D;

    --ease-out-expo:cubic-bezier(.19,1,.22,1);
    --ease-out-quart:cubic-bezier(.165,.84,.44,1);
    --ease-in-out-quart:cubic-bezier(.77,0,.175,1);
  }

  * { box-sizing:border-box; }
  html,body { margin:0; height:100%; background:#000; overflow:hidden; }

  /* Fixed 1920x1080 stage scaled to the window, so what you record is what was
     composed rather than whatever the browser reflowed it into. */
  #fit { position:fixed; inset:0; overflow:hidden; }
  #stage {
    width:1920px; height:1080px; position:absolute; left:50%; top:50%; overflow:hidden;
    transform-origin:center center;
    font-family:ui-sans-serif,system-ui,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
    color:var(--ink); background:var(--paper);
  }

  #wash {
    position:absolute; inset:0;
    background:radial-gradient(120% 90% at 50% -10%,
      #FCFAF4 0%, var(--paper) 45%, var(--paper-lo) 100%);
  }
  #night {
    position:absolute; inset:0; background:var(--dusk);
    opacity:0; transition:opacity 1.5s var(--ease-in-out-quart);
  }
  #night.on { opacity:1; }

  /* ---- layer 1: the chatter --------------------------------------------- */
  #pile {
    position:absolute; left:50%; top:50%; width:1020px;
    transform:translate(-50%,-50%);
    display:flex; flex-direction:column; gap:16px;
    transition:transform 1.15s var(--ease-in-out-quart),
               opacity 1.15s var(--ease-in-out-quart),
               filter 1.15s var(--ease-in-out-quart);
  }
  /* Nobody is reading it any more. It does not leave, it stops being legible. */
  #pile.recede {
    transform:translate(-50%,-50%) scale(.9) translateY(-18px);
    opacity:.34; filter:blur(7px) saturate(.35);
  }

  .note {
    display:flex; gap:16px; align-items:flex-start;
    background:#FFFDF8; border-radius:20px; padding:20px 26px;
    box-shadow:0 1px 2px rgba(22,35,63,.045),
               0 10px 26px rgba(22,35,63,.055),
               0 28px 64px rgba(22,35,63,.045);
    font-size:27px; line-height:1.42; color:var(--ink-soft);
    opacity:0; transform:translateY(30px) scale(.965); filter:blur(9px);
    transition:opacity .95s var(--ease-out-expo),
               transform .95s var(--ease-out-expo),
               filter .95s var(--ease-out-expo);
    will-change:transform,opacity,filter;
  }
  .note.in { opacity:1; transform:none; filter:none; }
  .dot { width:15px; height:15px; border-radius:50%; margin-top:9px; flex:0 0 auto; }

  /* ---- layer 2: the four ------------------------------------------------ */
  #cards {
    position:absolute; left:50%; top:50%; width:1180px;
    transform:translate(-50%,-50%);
    display:flex; flex-direction:column; gap:22px;
  }
  .card {
    background:#FFFFFF; border-radius:24px; padding:30px 38px;
    box-shadow:0 2px 4px rgba(22,35,63,.05),
               0 16px 40px rgba(22,35,63,.09),
               0 46px 90px rgba(22,35,63,.07);
    font-size:33px; line-height:1.46; color:var(--ink);
    opacity:0; transform:translateY(38px) scale(.965); filter:blur(12px);
    transition:opacity 1.05s var(--ease-out-expo),
               transform 1.05s var(--ease-out-expo),
               filter 1.05s var(--ease-out-expo);
    will-change:transform,opacity,filter;
  }
  .card.in { opacity:1; transform:none; filter:none; }
  /* Already spoken for, so it settles back without leaving. */
  .card.set { color:var(--ink-soft); transform:scale(.985); }
  .card .place { position:relative; white-space:nowrap; font-weight:500; }

  /* ---- the annotating hand ---------------------------------------------- */
  #ink { position:absolute; inset:0; pointer-events:none; overflow:visible; }
  #ink path,#ink line {
    fill:none; stroke:var(--accent); stroke-width:3.6;
    stroke-linecap:round; stroke-linejoin:round;
  }

  /* ---- the four names collapsing into one ------------------------------- */
  .fly {
    position:absolute; white-space:nowrap; font-size:33px; font-weight:500;
    color:var(--accent); will-change:transform,opacity;
  }
  #one {
    position:absolute; left:50%; top:50%;
    transform:translate(-50%,-50%) scale(.94); opacity:0;
    padding:22px 44px; border-radius:999px;
    background:#FFFFFF; color:var(--ink); font-size:42px; font-weight:500;
    box-shadow:0 2px 6px rgba(22,35,63,.06),
               0 20px 50px rgba(46,91,216,.16),
               0 50px 100px rgba(22,35,63,.08);
    transition:opacity .8s var(--ease-out-expo),
               transform .8s var(--ease-out-expo);
  }
  #one.in { opacity:1; transform:translate(-50%,-50%) scale(1); }
  #one.out { opacity:0; transform:translate(-50%,-50%) scale(1.04); }

  /* ---- the wordmark ------------------------------------------------------ */
  #mark {
    position:absolute; inset:0; display:grid; place-content:center;
    text-align:center; gap:22px; opacity:0;
    transition:opacity 1.1s var(--ease-out-expo);
  }
  #mark.in { opacity:1; }
  #mark h1 {
    font-family:Georgia,"Times New Roman",serif; font-weight:400; font-size:104px;
    margin:0; color:var(--chalk); letter-spacing:.004em;
    opacity:0; transform:translateY(20px); filter:blur(10px);
    transition:opacity 1.1s var(--ease-out-expo) .1s,
               transform 1.1s var(--ease-out-expo) .1s,
               filter 1.1s var(--ease-out-expo) .1s;
  }
  #mark p {
    font-family:Georgia,"Times New Roman",serif; font-style:italic; font-size:38px;
    margin:0; color:var(--dim);
    opacity:0; transform:translateY(16px); filter:blur(8px);
    transition:opacity 1.1s var(--ease-out-expo) .34s,
               transform 1.1s var(--ease-out-expo) .34s,
               filter 1.1s var(--ease-out-expo) .34s;
  }
  #mark.in h1, #mark.in p { opacity:1; transform:none; filter:none; }

  #hint {
    position:fixed; left:16px; bottom:12px; z-index:9; color:#8a8578;
    font:13px/1.5 ui-monospace,SFMono-Regular,Consolas,monospace; opacity:.7;
  }
  #hint.gone { display:none; }

  @media (prefers-reduced-motion:reduce) {
    .note,.card,#pile,#night,#one,#mark,#mark h1,#mark p {
      transition-duration:.01ms !important;
    }
  }
</style>

<div id="fit"><div id="stage">
  <div id="wash"></div>
  <div id="pile"></div>
  <div id="cards"></div>
  <svg id="ink"></svg>
  <div id="one"></div>
  <div id="night"></div>
  <div id="mark">
    <h1>Porchlight</h1>
    <p>your friendly neighborhood agent</p>
  </div>
</div></div>
<div id="hint">space play / replay &nbsp; h hide &nbsp; 1920x1080</div>

<script>
var DATA = /*__DATA__*/;
var T = /*__TIMING__*/;

var stage=document.getElementById('stage'), pile=document.getElementById('pile'),
    cards=document.getElementById('cards'), ink=document.getElementById('ink'),
    one=document.getElementById('one'), night=document.getElementById('night'),
    mark=document.getElementById('mark'), hint=document.getElementById('hint');
var timers=[], flies=[];

/* Muted, unsaturated marks so the pile reads as many voices without turning
   into a colour chart. Fixed order, so every take is identical. */
var DOTS=['#B9C4D6','#C7BFAE','#AEC0B4','#D2BEB2','#B6B4CB','#C4CBB6','#CBBBC4','#B2C2CB'];

function fit(){ stage.style.transform='translate(-50%,-50%) scale('+Math.min(innerWidth/1920,innerHeight/1080)+')'; }
addEventListener('resize',fit); fit();

function at(s,fn){ timers.push(setTimeout(fn,s*1000)); }
function esc(s){ return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

function withPlace(text,place){
  var i=text.indexOf(place);
  if(i<0) return esc(text);
  return esc(text.slice(0,i))+"<span class='place'>"+esc(place)+"</span>"+
         esc(text.slice(i+place.length));
}

function addNote(text,i){
  var el=document.createElement('div');
  el.className='note';
  el.innerHTML="<span class='dot' style='background:"+DOTS[i%DOTS.length]+"'></span>"+
               "<span>"+esc(text)+"</span>";
  pile.appendChild(el);
  requestAnimationFrame(function(){ el.classList.add('in'); });
  while(pile.children.length>7) pile.removeChild(pile.firstChild);
}

function addCard(r){
  var el=document.createElement('div');
  el.className='card';
  el.innerHTML=withPlace(r.text,r.place);
  cards.appendChild(el);
  requestAnimationFrame(function(){ el.classList.add('in'); });
  return el;
}

/* Where something sits in stage coordinates, whatever the window scale is. */
function rectOf(node){
  var s=stage.getBoundingClientRect(), b=node.getBoundingClientRect(), k=s.width/1920;
  return { x:(b.left-s.left)/k, y:(b.top-s.top)/k, w:b.width/k, h:b.height/k };
}

/* A ring drawn the way a hand draws one: not a true ellipse, and not closed. */
function ringPath(r,pad){
  var x=r.x-pad, y=r.y-pad*.72, w=r.w+pad*2, h=r.h+pad*1.44;
  var cx=x+w/2, cy=y+h/2, rx=w/2, ry=h/2, p=[];
  for(var i=0;i<=34;i++){
    var a=-0.42+(i/34)*(Math.PI*2+0.62);
    var wob=1+Math.sin(i*1.9+rx*.03)*0.026;
    p.push((cx+Math.cos(a)*rx*wob).toFixed(1)+' '+
           (cy+Math.sin(a)*ry*wob*1.05).toFixed(1));
  }
  return 'M'+p.join(' L');
}

function drawOn(el,kind){
  var span=el.querySelector('.place'); if(!span) return;
  var r=rectOf(span), node;
  if(kind==='ring'){
    node=document.createElementNS('http://www.w3.org/2000/svg','path');
    node.setAttribute('d',ringPath(r,13));
  }else{
    node=document.createElementNS('http://www.w3.org/2000/svg','line');
    node.setAttribute('x1',r.x-8); node.setAttribute('x2',r.x+r.w+8);
    node.setAttribute('y1',r.y+r.h*.60); node.setAttribute('y2',r.y+r.h*.52);
  }
  ink.appendChild(node);
  var len=node.getTotalLength?node.getTotalLength():420;
  node.style.strokeDasharray=len; node.style.strokeDashoffset=len;
  node.style.transition='stroke-dashoffset '+(kind==='ring'?.72:.40)+
                        's var(--ease-out-quart)';
  requestAnimationFrame(function(){ node.style.strokeDashoffset=0; });
}

/* The four names lift off the cards and collapse into the one place they all
   meant. The product, in a single move. */
function converge(els){
  var tx=960, ty=540;
  els.forEach(function(el,i){
    var span=el.querySelector('.place'); if(!span) return;
    var r=rectOf(span);
    var f=document.createElement('div');
    f.className='fly'; f.textContent=span.textContent;
    f.style.left=r.x+'px'; f.style.top=r.y+'px';
    f.style.transition='transform 1.25s var(--ease-in-out-quart) '+(i*0.05)+'s,'+
                       'opacity .9s var(--ease-out-quart) '+(0.5+i*0.05)+'s';
    stage.appendChild(f); flies.push(f);
    span.style.transition='opacity .35s ease'; span.style.opacity=0;
    requestAnimationFrame(function(){
      f.style.transform='translate('+(tx-r.x-r.w/2)+'px,'+(ty-r.y-r.h/2)+
                        'px) scale(.82)';
      f.style.opacity=0;
    });
  });
  cards.style.transition='opacity .9s var(--ease-out-quart),'+
                         'transform .9s var(--ease-out-quart)';
  cards.style.opacity=0;
  cards.style.transform='translate(-50%,-50%) scale(.97)';
  ink.style.transition='opacity .7s ease'; ink.style.opacity=0;
}

function reset(){
  timers.forEach(clearTimeout); timers=[];
  flies.forEach(function(f){ f.remove(); }); flies=[];
  pile.innerHTML=''; cards.innerHTML=''; ink.innerHTML='';
  pile.classList.remove('recede');
  cards.style.cssText=''; ink.style.cssText='';
  one.className=''; one.textContent=DATA.zone;
  night.classList.remove('on'); mark.classList.remove('in');
}

function play(){
  reset();

  var t=T.pile_start;
  DATA.chatter.forEach(function(text,i){
    at(t,function(){ addNote(text,i); });
    t+=T.pile_gap*Math.pow(T.pile_decay,i);
  });

  at(T.mute,function(){ pile.classList.add('recede'); });

  var base=T.mute+T.quiet, els=[];
  DATA.cluster.forEach(function(r,i){
    at(base+i*T.card_gap,function(){
      els.forEach(function(e){ e.classList.add('set'); });
      els.push(addCard(r));
    });
  });

  var ringAt=base+DATA.cluster.length*T.card_gap;
  DATA.cluster.forEach(function(_,i){
    at(ringAt+i*T.ring_gap,function(){ drawOn(els[i],'ring'); });
  });

  var strikeAt=ringAt+DATA.cluster.length*T.ring_gap+0.55;
  DATA.cluster.forEach(function(_,i){
    at(strikeAt+i*T.strike_gap,function(){ drawOn(els[i],'strike'); });
  });

  var convAt=strikeAt+DATA.cluster.length*T.strike_gap+1.5;
  at(convAt,function(){ converge(els); });
  at(convAt+T.converge*.62,function(){ one.classList.add('in'); });

  var duskAt=convAt+T.converge+1.5;
  at(duskAt,function(){ one.classList.add('out'); });
  at(duskAt+.35,function(){ night.classList.add('on'); });
  at(duskAt+T.dusk,function(){ mark.classList.add('in'); });
}

addEventListener('keydown',function(e){
  if(e.code==='Space'){ e.preventDefault(); play(); }
  if(e.key==='h'||e.key==='H') hint.classList.toggle('gone');
});
</script>
"""


def build() -> str:
    data = load()
    return (PAGE.replace("/*__DATA__*/", json.dumps(data, ensure_ascii=False, indent=2))
                .replace("/*__TIMING__*/", json.dumps(TIMING)))


def main(argv: list[str]) -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build(), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")
    print("  space plays and replays, h hides the hint")
    print("  record the browser full screen at 1920x1080")
    if "--open" in argv:
        webbrowser.open(OUT.as_uri())
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
