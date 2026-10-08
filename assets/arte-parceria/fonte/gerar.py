import json, os
A = json.load(open("assets.json"))
SIMB = open("simbolo.txt").read()

def face(nome, peso, chave):
    return (f"@font-face{{font-family:'{nome}';font-weight:{peso};font-style:normal;"
            f"src:url(data:font/ttf;base64,{A[chave]}) format('truetype');}}")

FONTES = "".join([face("Poppins", w, f"f_Poppins-{w}") for w in (600, 700, 800, 900)]
                 + [face("Archivo", 400, "f_ArchivoBlack-400"), face("Marker", 400, "f_Marker-400")])

ICO = {
 "escova": '<rect x="13.5" y="3.5" width="21" height="28" rx="10.5"/><path d="M24 31.5v11" stroke-linecap="round"/>'
           '<path d="M19.5 12v4.5M28.5 12v4.5M19.5 21.5V26M28.5 21.5V26" stroke-linecap="round"/>',
 "globo": '<circle cx="24" cy="24" r="17"/><path d="M7 24h34M24 7c4.5 4.8 7 10.7 7 17s-2.5 12.2-7 17c-4.5-4.8-7-10.7-7-17s2.5-12.2 7-17z"/>',
 "estrela": '<path d="M24 6l5.4 11.6L42 19.3l-9 9.1 2.2 12.9L24 35.2 12.8 41.3 15 28.4l-9-9.1 12.6-1.7z" stroke-linejoin="round"/>',
 "coracao": '<path d="M24 41S7 30.3 7 19.5C7 13.1 11.9 8 18 8c3.6 0 6.6 1.8 8 4.4C27.4 9.8 30.4 8 34 8c6.1 0 11 5.1 11 11.5C45 30.3 24 41 24 41z" stroke-linejoin="round"/>',
}
def ico(k, cor, t=3):
    if k == "spa":   # simbolo oficial de 4 petalas do fastspa
        return f'<svg viewBox="443 211 300 342"><path fill="{cor}" d="{SIMB}"/></svg>'
    return f'<svg viewBox="0 0 48 48" fill="none" stroke="{cor}" stroke-width="{t}">{ICO[k]}</svg>'


CSS = FONTES + """
*{margin:0;padding:0;box-sizing:border-box}
.peca{position:relative;overflow:hidden;font-family:Poppins,sans-serif;
  background:#140330;color:#fff;width:var(--w);height:var(--h)}
.bg{position:absolute;inset:0;
  background:
   radial-gradient(90% 55% at 12% 4%,   rgba(22,224,242,.34), transparent 62%),
   radial-gradient(85% 50% at 92% 22%,  rgba(255,47,208,.30), transparent 60%),
   radial-gradient(75% 45% at 50% 50%,  rgba(124,42,232,.46), transparent 70%),
   radial-gradient(100% 60% at 88% 100%,rgba(216,255,46,.16), transparent 62%),
   radial-gradient(90% 55% at 6% 94%,   rgba(255,47,208,.22), transparent 60%),
   linear-gradient(168deg,#1B0540 0%,#2D0A63 46%,#1A0638 100%);}
/* simbolo oficial fastspa como marca d'agua */
.marca{position:absolute;left:-9%;bottom:-6%;width:40%;opacity:.038;transform:rotate(14deg)}
.marca svg{display:block;width:100%}
.grao{position:absolute;inset:0;opacity:.5;mix-blend-mode:overlay;
  background-image:radial-gradient(rgba(255,255,255,.5) .7px,transparent .8px);background-size:4px 4px}
.conteudo{position:relative;height:100%;padding:var(--pad);
  display:flex;flex-direction:column;align-items:center;justify-content:space-between;text-align:center}

.yazigi{width:var(--yz);filter:drop-shadow(0 6px 26px rgba(0,0,0,.5))}

.kicker{position:relative;transform:rotate(-2.1deg);padding:calc(var(--u)*.52) calc(var(--u)*1.5);
  background:linear-gradient(100deg,#D8FF2E,#F2FF6B 55%,#C8F520);
  clip-path:polygon(1.2% 14%,99% 2%,98.4% 84%,2% 97%);
  box-shadow:0 0 44px rgba(216,255,46,.45)}
.kicker b{display:block;font-family:Archivo;color:#1E0545;line-height:.97;
  font-size:var(--k1);letter-spacing:-.01em;transform:skewX(-7deg)}
.kicker b.g{font-size:var(--k2)}

.stack{position:relative;width:100%;display:flex;flex-direction:column;gap:var(--gap)}
.card{position:relative;height:var(--ch);display:flex;align-items:center;gap:calc(var(--u)*1.1);
  padding:0 calc(var(--u)*1.45);border-radius:calc(var(--u)*1.5);
  border:3px solid var(--c);background:var(--fill);
  box-shadow:0 0 0 1px rgba(255,255,255,.07) inset, 0 0 30px var(--c), 0 0 70px -14px var(--c),
             0 22px 50px -18px rgba(0,0,0,.75)}
.card .ic{flex:0 0 auto;width:var(--icw);height:var(--icw);border-radius:50%;
  display:grid;place-items:center;border:2.5px solid var(--c);
  background:rgba(10,2,28,.5);box-shadow:0 0 22px -2px var(--c)}
.card .ic svg{width:62%;height:62%}
.card .mark{flex:1;display:flex;justify-content:center;align-items:center}
.card .mark img{display:block;width:auto}
.c1 .mark img{height:var(--h1);filter:drop-shadow(0 0 26px rgba(22,224,242,.85)) drop-shadow(0 3px 12px rgba(0,0,0,.6))}
.c2 .mark img{height:var(--h2);filter:drop-shadow(0 0 20px rgba(255,47,208,.45)) drop-shadow(0 3px 12px rgba(0,0,0,.6))}
.c1{--c:#16E0F2;--fill:linear-gradient(118deg,rgba(4,34,58,.90),rgba(6,16,52,.84))}
.c2{--c:#FF2FD0;--fill:linear-gradient(118deg,rgba(84,6,78,.88),rgba(44,6,76,.82))}

.plus{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);z-index:3;
  width:var(--pw);height:var(--pw);border-radius:50%;display:grid;place-items:center;
  background:linear-gradient(150deg,#7A1BE0,#4A0C9E);border:3px solid #fff;
  box-shadow:0 0 34px rgba(216,255,46,.55),0 0 0 7px #190540,0 12px 30px -8px #000}
.plus:before{content:"";position:absolute;width:46%;height:13%;background:#fff;border-radius:3px}
.plus:after{content:"";position:absolute;width:13%;height:46%;background:#fff;border-radius:3px}

.ancora{font-weight:900;font-size:var(--a1);letter-spacing:.012em;line-height:1;
  text-shadow:0 0 30px rgba(22,224,242,.5)}
.ancora i{font-style:normal;color:#D8FF2E;text-shadow:0 0 26px rgba(216,255,46,.85)}
.regua{width:var(--rw);height:4px;margin:calc(var(--u)*.62) auto 0;border-radius:4px;
  background:linear-gradient(90deg,transparent,#16E0F2,#D8FF2E,#FF2FD0,transparent)}

.apoio{font-weight:600;font-size:var(--p1);line-height:1.42;color:#E6DCFF}
.apoio b{font-weight:800;color:#fff}
.apoio em{font-style:normal;font-weight:800;color:#D8FF2E}

.benef{display:flex;align-items:flex-start;justify-content:center;gap:var(--bg_)}
.benef .b{flex:0 0 var(--cw);display:flex;flex-direction:column;align-items:center;justify-content:flex-start;gap:calc(var(--u)*.42)}
.benef .r{width:var(--bw);height:var(--bw);border-radius:50%;display:grid;place-items:center;
  border:2.5px solid var(--bc);background:rgba(255,255,255,.05);box-shadow:0 0 20px -3px var(--bc)}
.benef .r svg{width:58%;height:58%}
.benef span{font-weight:800;font-size:var(--b1);line-height:1.16;letter-spacing:.03em;text-transform:uppercase}
.benef .sep{flex:0 0 2px;margin-top:calc(var(--bw)*.18);height:calc(var(--bw)*.64);background:linear-gradient(transparent,rgba(255,255,255,.26),transparent)}

.cta{transform:rotate(1.6deg);padding:calc(var(--u)*.5) calc(var(--u)*2.1);
  background:linear-gradient(100deg,#D8FF2E,#EDFF7A 55%,#CBF520);
  clip-path:polygon(1.6% 10%,98.6% 3%,98% 88%,2.4% 96%);
  box-shadow:0 0 46px rgba(216,255,46,.5)}
.cta b{font-family:Marker;color:#1E0545;font-size:var(--c1);line-height:1.06;letter-spacing:.005em}

.rodape{display:flex;flex-direction:column;align-items:center;gap:calc(var(--u)*.3)}
.rodape .n{font-weight:800;font-size:var(--r1);letter-spacing:.17em;color:#CDBCFF}
.rodape .n u{text-decoration:none;color:#16E0F2}
.rodape .n s{text-decoration:none;color:#FF2FD0}
.rodape .t{font-weight:600;font-size:var(--r2);letter-spacing:.26em;color:#8E78C8;text-transform:uppercase}

.feed {--w:1080px;--h:1350px;--pad:62px;--u:30px;--yz:430px;--k1:46px;--k2:62px;--gap:22px;
       --ch:196px;--h1:84px;--h2:98px;--icw:94px;--pw:78px;--a1:50px;--rw:300px;--p1:25px;--bw:62px;--b1:17px;--bg_:18px;--cw:188px;
       --c1:50px;--r1:17px;--r2:12px}
.quad {--w:1080px;--h:1080px;--pad:48px;--u:24px;--yz:360px;--k1:38px;--k2:52px;--gap:18px;
       --ch:150px;--h1:64px;--h2:76px;--icw:80px;--pw:66px;--a1:43px;--rw:250px;--p1:21px;--bw:54px;--b1:15px;--bg_:15px;--cw:164px;
       --c1:42px;--r1:15px;--r2:11px}
.story{--w:1080px;--h:1920px;--pad:72px;--u:36px;--yz:486px;--k1:54px;--k2:74px;--gap:26px;
       --ch:232px;--h1:100px;--h2:116px;--icw:112px;--pw:92px;--a1:58px;--rw:350px;--p1:29px;--bw:74px;--b1:20px;--bg_:22px;--cw:222px;
       --c1:60px;--r1:19px;--r2:13px}
"""

def peca(fmt):
    return f"""<div class="peca {fmt}">
<div class="bg"></div>
<div class="marca"><svg viewBox="443 212 300 340"><path fill="#16E0F2" d="{SIMB}"/></svg></div>
<div class="grao"></div>
<div class="conteudo">

  <img class="yazigi" src="{A['yazigi']}" alt="Yázigi Limão">

  <div class="kicker"><b>UMA PARCERIA PARA</b><b class="g">VOCÊ BRILHAR</b></div>

  <div class="stack">
    <div class="card c1"><div class="ic">{ico('spa','#16E0F2')}</div>
      <div class="mark"><img src="{A['fastspa']}" alt="fastspa | LIMÃO"></div></div>
    <div class="plus"></div>
    <div class="card c2"><div class="ic">{ico('escova','#FF2FD0')}</div>
      <div class="mark"><img src="{A['escova']}" alt="fastescova LIMÃO"></div></div>
  </div>

  <div><div class="ancora">IDIOMAS <i>+</i> AUTOCUIDADO</div><div class="regua"></div></div>

  <p class="apoio">Um <em>novo idioma</em> abre caminhos.<br>
     O cuidado com a beleza <b>realça quem você é</b>.</p>

  <div class="benef">
    <div class="b"><div class="r" style="--bc:#D8FF2E">{ico('globo','#D8FF2E')}</div><span>Mais<br>confiança</span></div>
    <div class="sep"></div>
    <div class="b"><div class="r" style="--bc:#16E0F2">{ico('estrela','#16E0F2')}</div><span>Mais<br>oportunidades</span></div>
    <div class="sep"></div>
    <div class="b"><div class="r" style="--bc:#FF2FD0">{ico('coracao','#FF2FD0')}</div><span>Mais<br>você</span></div>
  </div>

  <div class="cta"><b>Vem com a gente!</b></div>

  <div class="rodape">
    <div class="n">YÁZIGI LIMÃO &nbsp;·&nbsp; <u>FAST SPA</u> &nbsp;·&nbsp; <s>FAST ESCOVA</s></div>
    <div class="t">Conexões para uma vida ainda melhor</div>
  </div>

</div></div>"""

os.makedirs("out", exist_ok=True)
for fmt, (w, h) in (("feed",(1080,1350)), ("quad",(1080,1080)), ("story",(1080,1920))):
    open(f"out/{fmt}.html","w").write(f"<style>{CSS}</style>{peca(fmt)}")
    print(f"  out/{fmt}.html  {w}x{h}")
json.dump([dict(svg=f"out/{f}.html", out=f"out/parceria-{f}.png", w=w, h=h)
           for f,(w,h) in (("feed",(1080,1350)),("quad",(1080,1080)),("story",(1080,1920)))],
          open("jobs_arte.json","w"))
