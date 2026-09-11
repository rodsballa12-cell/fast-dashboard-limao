#!/usr/bin/env python3
"""Gera os 4 cartões de convite (1080x1350) da inauguração do Fast SPA Limão."""
import pathlib, subprocess, sys

BASE = pathlib.Path(__file__).parent
FONTS = (BASE / "fonts.css").read_text()
CHROME = "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell"

CARDS = [
    dict(
        arq="convite-24-qui",
        num="24", dow="quinta-feira", mes="setembro 2026",
        selo="Noite de inauguração",
        titulo="As portas abrem<br>pela primeira vez",
        detalhe="Corte de fita às 19h30, tour pela casa e coquetel.<br>Uma noite pequena, para quem construiu isso com a gente.",
        hora="18h às 22h",
        accent="#E0B44A", wash="rgba(224,180,74,.14)",
    ),
    dict(
        arq="convite-25-sex",
        num="25", dow="sexta-feira", mes="setembro 2026",
        selo="Abertura oficial",
        titulo="Sexta é o dia<br>das clientes de casa",
        detalhe="Uma sessão de 20 minutos por nossa conta, com hora marcada<br>— antes de o SPA abrir para o bairro.",
        hora="10h às 20h · hora marcada",
        accent="#4ECDBF", wash="rgba(78,205,191,.13)",
    ),
    dict(
        arq="convite-26-sab",
        num="26", dow="sábado", mes="setembro 2026",
        selo="Dia da comunidade",
        titulo="Venha<br>e traga uma amiga",
        detalhe="Vocês duas têm uma experiência de 20 minutos por nossa conta.<br>Música, mini-bar e a casa inteira para conhecer.",
        hora="9h às 19h · hora marcada",
        accent="#6FD8CC", wash="rgba(111,216,204,.13)",
    ),
    dict(
        arq="convite-27-dom",
        num="27", dow="domingo", mes="setembro 2026",
        selo="Portas abertas",
        titulo="Domingo<br>o SPA é do bairro",
        detalhe="Sem hora marcada: chegue, pegue sua senha e experimente<br>15 minutos do que a casa faz de melhor.",
        hora="10h às 17h · por ordem de chegada",
        accent="#A7DED6", wash="rgba(167,222,214,.12)",
    ),
]

TPL = """<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><style>
{fonts}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:1080px;height:1350px;overflow:hidden}}
body{{
  background:
    radial-gradient(90% 55% at 50% 8%, rgba(255,255,255,.055), transparent 70%),
    linear-gradient(168deg,#0D2A26 0%,#0A1F1C 52%,#081B18 100%);
  background-color:#0A1F1C;
  font-family:'Karla',sans-serif;color:#EAF1EF;
  -webkit-font-smoothing:antialiased;
}}
.frame{{position:absolute;inset:38px;border:1px solid rgba(234,241,239,.16)}}
.frame::after{{content:"";position:absolute;inset:11px;border:1px solid rgba(234,241,239,.07)}}
.card{{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;
  text-align:center;padding:104px 96px 92px}}
.brand{{font-size:19px;letter-spacing:.44em;text-transform:uppercase;color:{accent};font-weight:600}}
.selo{{margin-top:40px;font-size:20px;letter-spacing:.20em;text-transform:uppercase;
  color:#EAF1EF;background:{wash};border:1px solid {accent}58;border-radius:3px;padding:11px 24px}}
.num{{font-family:'Marcellus',serif;font-size:300px;line-height:.86;color:{accent};margin-top:34px;
  letter-spacing:-.01em}}
.dow{{font-size:26px;letter-spacing:.30em;text-transform:uppercase;color:rgba(234,241,239,.66);margin-top:14px}}
.mes{{font-size:19px;letter-spacing:.26em;text-transform:uppercase;color:rgba(234,241,239,.40);margin-top:10px}}
.rule{{width:112px;height:1px;background:rgba(234,241,239,.26);margin:46px 0 0}}
.titulo{{font-family:'Marcellus',serif;font-size:62px;line-height:1.16;margin-top:42px;color:#F4F9F7}}
.detalhe{{font-size:25px;line-height:1.64;color:rgba(234,241,239,.72);margin-top:26px;max-width:884px}}
.hora{{margin-top:auto;font-size:31px;color:#F4F9F7;letter-spacing:.02em;font-weight:600}}
.end{{font-size:24px;line-height:1.55;color:rgba(234,241,239,.62);margin-top:22px}}
.end b{{color:rgba(234,241,239,.85);font-weight:600}}
.rsvp{{margin-top:30px;padding-top:26px;border-top:1px solid rgba(234,241,239,.14);width:100%;
  font-size:23px;color:{accent};letter-spacing:.02em}}
</style></head><body>
<div class="frame"></div>
<div class="card">
  <div class="brand">Fast SPA · Limão</div>
  <div class="selo">{selo}</div>
  <div class="num">{num}</div>
  <div class="dow">{dow}</div>
  <div class="mes">{mes}</div>
  <div class="rule"></div>
  <h1 class="titulo">{titulo}</h1>
  <p class="detalhe">{detalhe}</p>
  <div class="hora">{hora}</div>
  <p class="end">Av. Dep. Emílio Carlos, 358 · Limão · São Paulo<br><b>no mesmo prédio da Fast Escova Limão</b></p>
  <p class="rsvp">Confirme pelo WhatsApp (11) 99024-3927</p>
</div>
</body></html>"""

for c in CARDS:
    html = TPL.format(fonts=FONTS, **c)
    p = BASE / (c["arq"] + ".html")
    p.write_text(html, encoding="utf-8")
    out = BASE / (c["arq"] + ".png")
    r = subprocess.run([
        CHROME, "--headless", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
        "--force-color-profile=srgb", "--window-size=1080,1350",
        "--screenshot=" + str(out),
        p.as_uri(),
    ], capture_output=True, text=True)
    if not out.exists():
        print("FALHOU", c["arq"], r.stderr[-600:], file=sys.stderr)
        sys.exit(1)
    print(out.name, out.stat().st_size // 1024, "KB")
