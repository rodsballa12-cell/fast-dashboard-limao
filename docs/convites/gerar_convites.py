#!/usr/bin/env python3
"""Gera os 4 cartões de convite (1080x1350) da inauguração do Fast SPA Limão.

Cores da rede: amarelo FAST #FFD100 · turquesa SPA #24B3A6 · preto #141414.
A marca usada é a mesma do painel (LOGOS_UNIDADE em index.html). Quando o
arquivo oficial do logo chegar, troque a constante MARCA por um <img>.

Uso: python3 gerar_convites.py   (precisa do Chromium do Playwright)
"""
import pathlib, subprocess, sys

BASE = pathlib.Path(__file__).parent
FONTS = (BASE / "fonts2.css").read_text()
CHROME = "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell"

CARDS = [
    dict(
        arq="convite-24-qui",
        num="24", dow="quinta",
        selo="Noite de inauguração",
        selo_bg="#141414", selo_fg="#FFD100",
        titulo="A noite em que<br>o SPA abre as portas",
        bullets=["Corte de fita às 19h30",
                 "Tour pela casa nova",
                 "Coquetel de boas-vindas"],
        carimbo="convite pessoal",
        hora="18h às 22h",
    ),
    dict(
        arq="convite-25-sex",
        num="25", dow="sexta",
        selo="Abertura oficial",
        selo_bg="#24B3A6", selo_fg="#FFFFFF",
        titulo="Sexta é o dia<br>das clientes de casa",
        bullets=["Sessão de 20 minutos por nossa conta",
                 "Hora marcada — você não pega fila",
                 "Brinde de inauguração"],
        carimbo="é por nossa conta",
        hora="10h às 20h · hora marcada",
    ),
    dict(
        arq="convite-26-sab",
        num="26", dow="sábado",
        selo="Dia da comunidade",
        selo_bg="#24B3A6", selo_fg="#FFFFFF",
        titulo="Venha<br>e traga uma amiga",
        bullets=["20 minutos de experiência para vocês duas",
                 "Música e mini-bar o dia inteiro",
                 "Hora marcada, das 9h às 19h"],
        carimbo="as duas de graça",
        hora="9h às 19h · hora marcada",
    ),
    dict(
        arq="convite-27-dom",
        num="27", dow="domingo",
        selo="Portas abertas",
        selo_bg="#24B3A6", selo_fg="#FFFFFF",
        titulo="Domingo<br>o SPA é do bairro",
        bullets=["Sem hora marcada: chegue e pegue sua senha",
                 "15 minutos do que a casa faz de melhor",
                 "Voucher para voltar na semana seguinte"],
        carimbo="entrada livre",
        hora="10h às 17h · por ordem de chegada",
    ),
]

MARCA = """<svg class="marca" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Fast SPA">
  <rect width="100" height="100" rx="18" fill="#24B3A6"/>
  <circle cx="50" cy="45" r="30" fill="#FFFFFF"/>
  <text x="50" y="86" text-anchor="middle" font-family="Lora, Georgia, serif" font-style="italic" font-weight="500" font-size="100" fill="#4A4A4A">f</text>
</svg>"""

TPL = """<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><style>
{fonts}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:1080px;height:1350px;overflow:hidden}}
body{{
  background:linear-gradient(180deg,#FFFFFF 0%,#FFFFFF 46%,#EFF9F7 100%);
  font-family:'Poppins',sans-serif;color:#16201F;-webkit-font-smoothing:antialiased;
}}
.topbar{{position:absolute;top:0;left:0;right:0;height:16px;background:#FFD100}}
.card{{position:absolute;inset:0;padding:70px 78px 0;display:flex;flex-direction:column;
  align-items:center;text-align:center}}

.marca{{width:88px;height:88px;display:block}}
.wordmark{{margin-top:15px;font-size:21px;font-weight:600;letter-spacing:.34em;
  text-transform:uppercase;color:#0B6B62}}

.selo{{margin-top:28px;background:{selo_bg};color:{selo_fg};font-size:20px;font-weight:600;
  letter-spacing:.16em;text-transform:uppercase;padding:12px 28px;border-radius:999px}}

.dia{{position:relative;margin-top:32px;width:344px;height:344px;border-radius:50%;
  background:#FFD100;display:flex;flex-direction:column;align-items:center;justify-content:center}}
.dia b{{font-size:180px;font-weight:700;line-height:.9;color:#141414;letter-spacing:-.03em}}
.dia span{{margin-top:6px;font-size:25px;font-weight:600;letter-spacing:.28em;
  text-transform:uppercase;color:#141414}}
.dia small{{font-size:18px;font-weight:500;letter-spacing:.22em;text-transform:uppercase;
  color:rgba(20,20,20,.55);margin-top:4px}}
.carimbo{{position:absolute;right:-96px;bottom:-14px;transform:rotate(-8deg);
  background:#FFFFFF;border:2px solid #24B3A6;color:#0B6B62;border-radius:999px;
  font-family:'Lora',Georgia,serif;font-style:italic;font-weight:500;font-size:26px;
  padding:10px 22px;white-space:nowrap;box-shadow:0 6px 18px rgba(11,107,98,.14)}}

.titulo{{margin-top:40px;font-size:55px;font-weight:700;line-height:1.16;color:#0B6B62;
  letter-spacing:-.015em}}

.bullets{{margin-top:30px;display:flex;flex-direction:column;gap:17px;align-items:flex-start;
  background:#F1FAF8;border:1px solid #D8EFEB;border-radius:26px;padding:30px 38px}}
.bl{{display:flex;align-items:center;gap:15px;font-size:26px;font-weight:400;color:#33423F;text-align:left}}
.bl i{{width:12px;height:12px;border-radius:50%;background:#24B3A6;flex:none}}

.rodape{{margin-top:auto;width:100%;padding-top:34px}}
.hora{{font-size:32px;font-weight:700;color:#141414}}
.end{{margin-top:11px;font-size:23px;font-weight:400;line-height:1.5;color:#5B6B69}}
.end b{{font-weight:600;color:#3D4B49}}
.zap{{margin:24px -78px 0;background:#FFD100;padding:25px 40px;font-size:26px;font-weight:700;color:#141414}}
.zap span{{font-weight:500}}
</style></head><body>
<div class="topbar"></div>
<div class="card">
  {marca}
  <div class="wordmark">Fast SPA · Limão</div>
  <div class="selo">{selo}</div>
  <div class="dia">
    <b>{num}</b>
    <span>{dow}</span>
    <small>setembro</small>
    <div class="carimbo">{carimbo}</div>
  </div>
  <h1 class="titulo">{titulo}</h1>
  <div class="bullets">{bullets_html}</div>
  <div class="rodape">
    <div class="hora">{hora}</div>
    <p class="end">Av. Dep. Emílio Carlos, 358 · Limão · São Paulo<br><b>no mesmo prédio da Fast Escova Limão</b></p>
    <div class="zap"><span>Confirme pelo WhatsApp</span> (11) 99024-3927</div>
  </div>
</div>
</body></html>"""

for c in CARDS:
    bullets_html = "".join('<div class="bl"><i></i>%s</div>' % b for b in c["bullets"])
    html = TPL.format(fonts=FONTS, marca=MARCA, bullets_html=bullets_html, **c)
    p = BASE / (c["arq"] + ".html")
    p.write_text(html, encoding="utf-8")
    out = BASE / (c["arq"] + ".png")
    if out.exists():
        out.unlink()
    r = subprocess.run([
        CHROME, "--headless", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
        "--force-color-profile=srgb", "--window-size=1080,1350",
        "--screenshot=" + str(out), p.as_uri(),
    ], capture_output=True, text=True)
    if not out.exists():
        print("FALHOU", c["arq"], r.stderr[-600:], file=sys.stderr)
        sys.exit(1)
    print(out.name, out.stat().st_size // 1024, "KB")
