#!/usr/bin/env python3
"""Gera os 4 convites (1080x1350) da inauguração do Fast SPA Limão.

Segue o padrão da Tabela de Serviços oficial (arte_5.pdf):
  verde-petróleo #005A65 · pêssego #F6E3D2 · linha creme #FEF4E9
  oliva #8BA229 · turquesa #00A6A4 · carvão #555350
  títulos em Playfair Display · textos em Montserrat
A marca e os ornamentos foram recortados da própria arte (pasta marca/).

Uso: python3 gerar_convites.py   (precisa do Chromium do Playwright)
"""
import pathlib, subprocess, sys

BASE = pathlib.Path(__file__).parent
FONTS = (BASE / "fonts3.css").read_text()
CHROME = "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell"

CARDS = [
    dict(
        arq="convite-24-qui",
        barra="Quinta · 24 de setembro", horas="18h — 22h",
        titulo="A noite em que as<br>portas se abrem",
        linha="Um grupo pequeno, antes de a casa abrir para o bairro.",
        itens=[
            ("CORTE DE FITA — 19h30",
             "O momento em que o Fast SPA Limão abre oficialmente as portas."),
            ("TOUR PELA CASA",
             "Conheça as salas de terapia, a área de relaxamento e a equipe."),
            ("COQUETEL DE BOAS-VINDAS",
             "Brinde com a gente e leve um mimo de inauguração."),
        ],
        destaque="CONVITE PESSOAL", destaque_dir="confirme até 21/09",
        destaque_bg="#005A65", destaque_fg="#FDF6EC",
    ),
    dict(
        arq="convite-25-sex",
        barra="Sexta · 25 de setembro", horas="10h — 20h · hora marcada",
        titulo="Sexta é o dia<br>das clientes de casa",
        linha="O SPA abre primeiro para quem já é da Fast.",
        itens=[
            ("RENOVE-SE EM 45' — sessão de 20min",
             "Massagem personalizada: você escolhe relaxante, drenagem ou modeladora."),
            ("DRENAGEM LINFÁTICA FACIAL — 15min",
             "Desincha o rosto e devolve viço e leveza em poucos minutos."),
            ("HORA MARCADA NO SEU NOME",
             "Você chega no seu horário e não pega fila."),
        ],
        destaque="CORTESIA DE INAUGURAÇÃO", destaque_dir="valor R$ 149,00",
        destaque_bg="#C9DC94", destaque_fg="#3C4F14",
    ),
    dict(
        arq="convite-26-sab",
        barra="Sábado · 26 de setembro", horas="9h — 19h · hora marcada",
        titulo="Venha<br>e traga uma amiga",
        linha="Duas cortesias no mesmo horário, lado a lado.",
        itens=[
            ("VOCÊ E UMA AMIGA",
             "As duas experimentam juntas, no mesmo horário, em salas vizinhas."),
            ("QUICK MASSAGE — 20min",
             "Solta pescoço, ombros e trapézio — o clássico de quem passa o dia sentada."),
            ("MÚSICA E MINI-BAR",
             "A casa aberta o dia inteiro, das 9h às 19h."),
        ],
        destaque="DUAS CORTESIAS", destaque_dir="valor R$ 118,00",
        destaque_bg="#C9DC94", destaque_fg="#3C4F14",
    ),
    dict(
        arq="convite-27-dom",
        barra="Domingo · 27 de setembro", horas="10h — 17h · por ordem de chegada",
        titulo="Domingo<br>o SPA é do bairro",
        linha="Sem hora marcada: é chegar e conhecer.",
        itens=[
            ("SEM AGENDAMENTO",
             "Chegue, pegue sua senha na entrada e aguarde pouco."),
            ("REVITALIZAÇÃO DAS MÃOS — 10min",
             "Hidrata intensamente e suaviza as linhas finas causadas pela rotina."),
            ("VOUCHER PARA VOLTAR",
             "Você sai com um voucher válido na semana seguinte."),
        ],
        destaque="ENTRADA LIVRE", destaque_dir="valor R$ 59,00",
        destaque_bg="#C9DC94", destaque_fg="#3C4F14",
    ),
]

TPL = """<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><style>
{fonts}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:1080px;height:1350px;overflow:hidden}}
body{{background:#F6E3D2;font-family:'Montserrat',sans-serif;color:#123C44;
  -webkit-font-smoothing:antialiased}}

/* ---------- cabeçalho ---------- */
.head{{height:208px;background:#005A65;position:relative;display:flex;
  align-items:center;justify-content:flex-end;padding:0 54px 0 0;overflow:hidden}}
.head .comma{{position:absolute;left:-26px;top:-34px;height:262px}}
.head .titulo{{font-family:'Playfair Display',serif;font-style:italic;font-weight:400;
  font-size:70px;color:#F2E7DB;line-height:1}}
.head .barra{{width:2px;height:88px;background:rgba(242,231,219,.55);margin:0 34px}}
.head .logo{{height:74px}}

/* ---------- corpo ---------- */
.corpo{{padding:44px 54px 0;display:flex;flex-direction:column;height:calc(1350px - 208px - 158px)}}

.faixa{{background:#8BA229;border-radius:9px;padding:17px 26px;display:flex;
  align-items:baseline;justify-content:space-between;gap:20px}}
.faixa b{{font-family:'Playfair Display',serif;font-weight:600;font-size:37px;color:#FDF6EC}}
.faixa span{{font-size:23px;font-weight:600;color:#FDF6EC;letter-spacing:.01em}}

h1{{font-family:'Playfair Display',serif;font-weight:700;font-size:56px;line-height:1.14;
  color:#0A4C55;margin-top:32px}}
.linha{{font-style:italic;font-size:25px;color:#0E7A80;margin-top:12px}}

.itens{{margin-top:30px;display:flex;flex-direction:column;gap:20px}}
.item .nome{{background:#FEF4E9;border-radius:7px;padding:13px 20px;font-size:25px;
  font-weight:500;color:#123C44;letter-spacing:.005em}}
.item .desc{{font-style:italic;font-size:21.5px;line-height:1.45;color:#0E7A80;
  padding:8px 20px 0}}

.destaque{{margin-top:26px;background:{destaque_bg};border-radius:7px;padding:16px 22px;
  display:flex;align-items:center;justify-content:space-between;gap:18px}}
.destaque b{{font-size:25px;font-weight:700;color:{destaque_fg};letter-spacing:.06em}}
.destaque span{{font-style:italic;font-size:23px;color:{destaque_fg};opacity:.92}}

.local{{margin-top:auto;padding-bottom:26px;text-align:center}}
.local .end{{font-size:23px;font-weight:500;color:#123C44;line-height:1.5}}
.local .end em{{font-style:italic;font-weight:400;color:#0E7A80}}
.local .zap{{margin-top:12px;font-size:26px;font-weight:700;color:#0A4C55}}

/* ---------- rodapé ---------- */
.pe{{height:158px;background:#00A6A4;display:flex;align-items:center;
  justify-content:space-between;padding:0 54px;gap:26px}}
.pe .ig{{font-size:22px;font-weight:500;color:#FFFFFF;white-space:nowrap}}
.pe .faixa-orn{{height:46px;flex:none}}
.pe .tag{{font-family:'Playfair Display',serif;font-size:34px;color:#FFFFFF;white-space:nowrap}}
.pe .tag i{{font-style:italic;font-weight:600}}
</style></head><body>

<div class="head">
  <img class="comma" src="marca/ornamento_comma.png" alt="">
  <span class="titulo">Convite</span>
  <span class="barra"></span>
  <img class="logo" src="marca/logo_fastspa.png" alt="fast spa">
</div>

<div class="corpo">
  <div class="faixa"><b>{barra}</b><span>{horas}</span></div>
  <h1>{titulo}</h1>
  <p class="linha">{linha}</p>
  <div class="itens">{itens_html}</div>
  <div class="destaque"><b>{destaque}</b><span>{destaque_dir}</span></div>
  <div class="local">
    <p class="end">Av. Dep. Emílio Carlos, 358 · Limão · São Paulo<br>
      <em>no mesmo prédio da Fast Escova Limão</em></p>
    <p class="zap">Confirme pelo WhatsApp (11) 99024-3927</p>
  </div>
</div>

<div class="pe">
  <span class="ig">@fastspa.limao</span>
  <img class="faixa-orn" src="marca/ornamento_faixa.png" alt="">
  <span class="tag">Este lugar <i>é pra você</i>!</span>
</div>

</body></html>"""

for c in CARDS:
    itens_html = "".join(
        '<div class="item"><div class="nome">%s</div><div class="desc">%s</div></div>' % (n, d)
        for n, d in c["itens"])
    html = TPL.format(fonts=FONTS, itens_html=itens_html, **c)
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
