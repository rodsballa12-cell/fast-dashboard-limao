#!/usr/bin/env python3
"""Gera os 4 convites (1080x1350) da inauguração do Fast SPA Limão.

Paleta e marca da arte oficial (arte_5.pdf):
  verde-petróleo #005A65 · turquesa #00A6A4 · pêssego #F6E3D2
  creme #FEF4E9 · oliva #8BA229 · verde claro #C9DC94
  títulos em Playfair Display · textos em Montserrat
Composição de convite: tarja da marca, moldura dupla, data em destaque,
campo para o nome e o horário, e a assinatura da rede no rodapé.
Os ornamentos de pétala são desenhados em CSS, na cor da paleta.

Uso: python3 gerar_convites.py   (precisa do Chromium do Playwright)
"""
import pathlib, subprocess, sys

BASE = pathlib.Path(__file__).parent
FONTS = (BASE / "fonts3.css").read_text()
CHROME = "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell"

CARDS = [
    dict(
        arq="convite-24-qui",
        kicker="Noite de inauguração",
        abre="Temos o prazer de convidar você para",
        dow="quinta-feira", num="24", mes="setembro de 2026", horas="das 18h às 22h",
        titulo="A noite em que as portas se abrem",
        sub="Corte de fita às 19h30, tour pela casa e coquetel de boas-vindas.",
        cortesia="Convite pessoal e intransferível",
        cortesia_dir="confirme até 21/09",
        campo="Convite de", campo2="chegada sugerida",
    ),
    dict(
        arq="convite-25-sex",
        kicker="Abertura oficial",
        abre="Você está convidada para",
        dow="sexta-feira", num="25", mes="setembro de 2026", horas="das 10h às 20h · hora marcada",
        titulo="O dia das clientes de casa",
        sub="O SPA abre primeiro para quem já é da Fast, antes do bairro.",
        cortesia="Renove-se em 45' · sessão de 20 min",
        cortesia_dir="cortesia · valor R$ 149",
        campo="Convite de", campo2="seu horário",
    ),
    dict(
        arq="convite-26-sab",
        kicker="Dia da comunidade",
        abre="Você e uma amiga estão convidadas para",
        dow="sábado", num="26", mes="setembro de 2026", horas="das 9h às 19h · hora marcada",
        titulo="O dia de trazer quem você gosta",
        sub="Duas cortesias no mesmo horário, em salas vizinhas.",
        cortesia="Quick Massage · 20 min para as duas",
        cortesia_dir="cortesia · valor R$ 118",
        campo="Convite de", campo2="seu horário",
    ),
    dict(
        arq="convite-27-dom",
        kicker="Portas abertas",
        abre="Você está convidada para",
        dow="domingo", num="27", mes="setembro de 2026", horas="das 10h às 17h · por ordem de chegada",
        titulo="O domingo em que o SPA é do bairro",
        sub="Sem hora marcada: é chegar, pegar sua senha e conhecer.",
        cortesia="Revitalização das Mãos · 10 min",
        cortesia_dir="cortesia · valor R$ 59",
        campo="Convite de", campo2="",
    ),
]

TPL = """<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><style>
{fonts}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:1080px;height:1350px;overflow:hidden}}
body{{background:#F6E3D2;font-family:'Montserrat',sans-serif;color:#123C44;
  -webkit-font-smoothing:antialiased}}

/* tarja da marca */
.marca{{height:146px;background:#005A65;display:flex;align-items:center;justify-content:center}}
.marca img{{height:70px}}

/* moldura */
.folha{{position:relative;height:calc(1350px - 146px - 120px);padding:34px}}
.moldura{{position:absolute;inset:26px;border:1.6px solid rgba(0,90,101,.45)}}
.moldura::after{{content:"";position:absolute;inset:9px;border:1px solid rgba(0,90,101,.22)}}
.canto{{position:absolute;width:30px;height:30px;background:#00A6A4;opacity:.5;
  border-radius:50% 0 50% 0}}
.c1{{left:46px;top:46px;transform:rotate(0deg)}}
.c2{{right:46px;top:46px;transform:rotate(90deg)}}
.c3{{right:46px;bottom:46px;transform:rotate(180deg)}}
.c4{{left:46px;bottom:46px;transform:rotate(270deg)}}

.dentro{{position:relative;height:100%;display:flex;flex-direction:column;
  align-items:center;text-align:center;padding:46px 80px 40px}}

.kicker{{font-size:19px;font-weight:600;letter-spacing:.30em;text-transform:uppercase;
  color:#8BA229}}
.abre{{font-family:'Playfair Display',serif;font-style:italic;font-size:34px;
  color:#0E7A80;margin-top:26px;line-height:1.3}}

/* data */
.data{{margin-top:18px;display:flex;flex-direction:column;align-items:center}}
.data .dow{{font-size:22px;font-weight:600;letter-spacing:.34em;text-transform:uppercase;
  color:#005A65}}
.data .nrow{{display:flex;align-items:center;gap:26px;margin:6px 0 18px}}
.data .rule{{width:118px;height:1.4px;background:rgba(0,90,101,.4)}}
.data .num{{font-family:'Playfair Display',serif;font-weight:700;font-size:182px;
  line-height:1;color:#005A65;letter-spacing:-.02em}}
.data .mes{{font-size:21px;font-weight:500;letter-spacing:.26em;text-transform:uppercase;
  color:#005A65}}
.data .horas{{margin-top:16px;font-size:24px;font-weight:600;color:#0E7A80}}

/* divisor com pétalas */
.div{{display:flex;align-items:center;gap:12px;margin-top:30px}}
.div .ln{{width:150px;height:1.2px;background:rgba(0,90,101,.32)}}
.div .pt{{width:16px;height:16px;background:#00A6A4;border-radius:50% 0 50% 0}}
.div .pt.d{{background:#005A65}}

h1{{font-family:'Playfair Display',serif;font-weight:700;font-size:52px;line-height:1.16;
  color:#0A4C55;margin-top:28px;max-width:820px}}
.sub{{font-style:italic;font-size:24px;line-height:1.5;color:#0E7A80;margin-top:14px;
  max-width:740px}}

.cortesia{{margin-top:30px;background:#FEF4E9;border:1px solid rgba(0,90,101,.16);
  border-radius:8px;padding:16px 28px;display:flex;align-items:baseline;gap:18px}}
.cortesia b{{font-size:24px;font-weight:600;color:#123C44}}
.cortesia span{{font-style:italic;font-size:21px;color:#8BA229;font-weight:500}}

.campos{{margin-top:auto;width:100%;display:flex;gap:34px;justify-content:center;
  align-items:flex-end}}
.campo{{display:flex;flex-direction:column;align-items:flex-start;gap:9px}}
.campo i{{font-style:normal;font-size:16px;font-weight:600;letter-spacing:.20em;
  text-transform:uppercase;color:#0E7A80}}
.campo u{{display:block;height:1.4px;background:rgba(0,90,101,.42);text-decoration:none}}
.campo.nome u{{width:420px}}
.campo.hora u{{width:190px}}

.local{{margin-top:34px;font-size:21px;font-weight:500;line-height:1.55;color:#123C44}}
.local em{{font-style:italic;font-weight:400;color:#0E7A80}}
.local .zap{{display:block;margin-top:14px;font-size:23px;font-weight:700;color:#005A65}}

/* rodapé */
.pe{{height:120px;background:#00A6A4;display:flex;align-items:center;
  justify-content:center;gap:30px}}
.pe .tag{{font-family:'Playfair Display',serif;font-size:32px;color:#FFFFFF}}
.pe .tag i{{font-style:italic;font-weight:600}}
.pe .ig{{font-size:20px;font-weight:500;color:rgba(255,255,255,.9)}}
.pe .sep{{width:12px;height:12px;background:#005A65;border-radius:50% 0 50% 0}}
</style></head><body>

<div class="marca"><img src="marca/logo_fastspa.png" alt="fast spa"></div>

<div class="folha">
  <div class="moldura"></div>
  <span class="canto c1"></span><span class="canto c2"></span>
  <span class="canto c3"></span><span class="canto c4"></span>

  <div class="dentro">
    <div class="kicker">{kicker}</div>
    <p class="abre">{abre}</p>

    <div class="data">
      <span class="dow">{dow}</span>
      <span class="nrow"><i class="rule"></i><span class="num">{num}</span><i class="rule"></i></span>
      <span class="mes">{mes}</span>
      <span class="horas">{horas}</span>
    </div>

    <div class="div"><i class="ln"></i><i class="pt"></i><i class="pt d"></i><i class="pt"></i><i class="ln"></i></div>

    <h1>{titulo}</h1>
    <p class="sub">{sub}</p>

    <div class="cortesia"><b>{cortesia}</b><span>{cortesia_dir}</span></div>

    <div class="campos">{campos_html}</div>

    <p class="local">Av. Dep. Emílio Carlos, 358 · Limão · São Paulo<br>
      <em>no mesmo prédio da Fast Escova Limão</em>
      <span class="zap">Confirme pelo WhatsApp (11) 99024-3927</span></p>
  </div>
</div>

<div class="pe">
  <span class="ig">@fastspa.limao</span>
  <i class="sep"></i>
  <span class="tag">Este lugar <i>é pra você</i>!</span>
</div>

</body></html>"""

for c in CARDS:
    campos = '<div class="campo nome"><i>%s</i><u></u></div>' % c["campo"]
    if c["campo2"]:
        campos += '<div class="campo hora"><i>%s</i><u></u></div>' % c["campo2"]
    html = TPL.format(fonts=FONTS, campos_html=campos, **c)
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
