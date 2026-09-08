import numpy as np, potrace, os, json
from PIL import Image, ImageFilter

S = 3                  # supersample -> precisao sub-pixel no contorno
TURD = 12              # area minima (px nativos) para descartar sujeira de JPEG
D = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(D, "entrega"); os.makedirs(OUT, exist_ok=True)

VERDE_AGUA="#62B1AC"; BEGE="#EADACB"; VERDE_ESC="#285A62"; GRAFITE="#454140"; BRANCO="#FFFFFF"

ART = {
 "frente1": dict(saida="frente-verde-agua", bg=(99,175,171),  bg_out=VERDE_AGUA, fit=(26,22), inks=[
     ("simbolo-e-limao","verde-escuro",(40,90,98),  VERDE_ESC),
     ("logo-e-slogan",  "branco",      (254,254,255),BRANCO)]),
 "frente2": dict(saida="frente-bege",      bg=(234,218,203), bg_out=BEGE,      fit=(26,22), inks=[
     ("simbolo-e-spa",  "verde-agua",  (98,175,171), VERDE_AGUA),
     ("limao",          "verde-escuro",(47,74,75),   VERDE_ESC),
     ("fast-e-slogan",  "grafite",     (67,63,59),   GRAFITE)]),
 "verso1": dict(saida="costas-verde-agua", bg=(98,179,173),  bg_out=VERDE_AGUA, fit=(30,34), inks=[
     ("simbolo",        "verde-escuro",(40,90,99),   VERDE_ESC),
     ("texto",          "branco",      (250,253,253),BRANCO)]),
 "verso2": dict(saida="costas-bege",       bg=(234,218,203), bg_out=BEGE,      fit=(30,34), inks=[
     ("simbolo",        "verde-escuro",(40,90,99),   VERDE_ESC),
     ("texto",          "grafite",     (76,73,71),   GRAFITE)]),
}

def classificar(v, bg, samples):
    """obs = a*tinta + (1-a)*fundo, resolvido por tinta candidata; vence a de
    menor residuo. Discrimina por direcao cromatica a partir do fundo, o que
    separa tons proximos (grafite x verde-escuro) melhor que distancia direta."""
    d = v - bg
    br = np.full(d.shape[:2], np.inf, np.float32)
    bk = np.full(d.shape[:2], -1, np.int8)
    ba = np.zeros(d.shape[:2], np.float32)
    for k, s in enumerate(samples):
        f = np.array(s, np.float32) - bg
        a = np.clip((d @ f) / (f @ f), 0, 1)
        r = np.linalg.norm(d - a[..., None] * f, axis=2)
        sel = r < br
        br, bk, ba = np.where(sel, r, br), np.where(sel, np.int8(k), bk), np.where(sel, a, ba)
    return bk, ba

def traçar(mask):
    p = potrace.Bitmap(~mask).trace(turdsize=int(TURD*S*S), alphamax=1.0,
                                    opticurve=True, opttolerance=0.2)
    s, d, nc, ns = 1.0/S, [], 0, 0
    pts = []
    for c in p:
        st = c.start_point; pts.append((st.x*s, st.y*s)); d.append(f"M{st.x*s:.2f},{st.y*s:.2f}")
        for g in c:
            pts.append((g.end_point.x*s, g.end_point.y*s))
            if g.is_corner:
                pts.append((g.c.x*s, g.c.y*s))
                d.append(f"L{g.c.x*s:.2f},{g.c.y*s:.2f}L{g.end_point.x*s:.2f},{g.end_point.y*s:.2f}")
            else:
                d.append(f"C{g.c1.x*s:.2f},{g.c1.y*s:.2f} {g.c2.x*s:.2f},{g.c2.y*s:.2f} "
                         f"{g.end_point.x*s:.2f},{g.end_point.y*s:.2f}")
            ns += 1
        d.append("Z"); nc += 1
    P = np.array(pts) if pts else np.zeros((0,2))
    bb = (P[:,0].min(), P[:,1].min(), P[:,0].max(), P[:,1].max()) if len(P) else None
    return "".join(d), nc, ns, bb

def svg(vb, w, h, camadas, bg=None):
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" width="{w:.2f}" height="{h:.2f}">']
    if bg: o.append(f'<rect x="{vb.split()[0]}" y="{vb.split()[1]}" width="{vb.split()[2]}" '
                    f'height="{vb.split()[3]}" fill="{bg}"/>')
    for gid, cor, d in camadas:
        o.append(f'<path id="{gid}" fill="{cor}" fill-rule="evenodd" d="{d}"/>')
    return "\n".join(o + ['</svg>'])

rel, jobs = {}, []
for nome, cfg in ART.items():
    im = Image.open(os.path.join(D, f"{nome}_raw.jpeg")).convert("RGB")
    im = im.crop((2, 2, im.width-2, im.height-2))      # apara borda com artefato de arquivo
    im = im.filter(ImageFilter.MedianFilter(3))
    W, H = im.size
    v = np.asarray(im.resize((W*S, H*S), Image.BICUBIC), np.float32)
    bg = np.array(cfg["bg"], np.float32)
    k, a = classificar(v, bg, [s for _, _, s, _ in cfg["inks"]])

    camadas, info, bbs = [], [], []
    for i, (gid, tinta, _, cor) in enumerate(cfg["inks"]):
        m = (k == i) & (a > 0.5)
        d, nc, ns, bb = traçar(m)
        if bb: bbs.append(bb)
        camadas.append((gid, cor, d))
        info.append(dict(camada=gid, tinta=tinta, cor=cor, curvas=nc, segmentos=ns))

    B = np.array(bbs)
    x0, y0, x1, y1 = B[:,0].min(), B[:,1].min(), B[:,2].max(), B[:,3].max()
    cw, ch = x1-x0, y1-y0
    fit_w, fit_h = cfg["fit"]                      # encaixe na area util da peca
    esc = min(fit_w/cw, fit_h/ch)
    cm_w, cm_h = cw*esc, ch*esc
    px_w = round(cm_w/2.54*300); px_h = round(cm_h/2.54*300)   # 300 dpi
    n = cfg["saida"]

    open(f"{OUT}/{n}-estampa.svg","w").write(
        svg(f"{x0:.2f} {y0:.2f} {cw:.2f} {ch:.2f}", cw, ch, camadas))
    open(f"{OUT}/{n}-mockup.svg","w").write(
        svg(f"0 0 {W} {H}", W, H, camadas, bg=cfg["bg_out"]))
    jobs += [dict(svg=f"{OUT}/{n}-estampa.svg", out=f"{OUT}/{n}-estampa.pdf",
                  pdf=True, cm_w=round(cm_w,2), cm_h=round(cm_h,2), w=1000, h=1000),
             dict(svg=f"{OUT}/{n}-estampa.svg", out=f"{OUT}/{n}-estampa-300dpi.png",
                  w=px_w, h=px_h, transparent=True),
             dict(svg=f"{OUT}/{n}-mockup.svg",  out=f"{OUT}/{n}-mockup.png", w=W, h=H)]

    rel[n] = dict(origem=nome, arte_px=[W,H], estampa_px=[round(cw),round(ch)],
                  estampa_cm=[round(cm_w,1), round(cm_h,1)], png_300dpi=[px_w,px_h],
                  fundo_camiseta=cfg["bg_out"], camadas=info)
    print(f"{n}: estampa {cw:.0f}x{ch:.0f}px -> {cm_w:.1f}x{cm_h:.1f}cm  ({px_w}x{px_h}px @300dpi)")
    for t in info: print(f"     {t['camada']:18s} {t['tinta']:13s} {t['cor']}  {t['curvas']:3d} curvas")

json.dump(jobs, open(f"{D}/jobs_final.json","w"))
json.dump(rel, open(f"{OUT}/relatorio.json","w"), indent=1, ensure_ascii=False)
