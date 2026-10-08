import numpy as np, potrace
from PIL import Image, ImageFilter
S = 4                                  # supersample
BRANCO, AMARELO = (252,248,252), (250,226,7)

a0 = Image.open("origem.jpg").convert("RGB").crop((234,651,846,800)).filter(ImageFilter.MedianFilter(3))
W, H = a0.size
a = np.asarray(a0.resize((W*S, H*S), Image.BICUBIC), np.float32)

# fundo roxo varia -> ajusta um plano linear RGB pelas bordas do recorte
h, w, _ = a.shape
yy, xx = np.mgrid[0:h, 0:w]
m = np.zeros((h, w), bool); k = 6*S
m[:k], m[-k:], m[:, :k], m[:, -k:] = True, True, True, True
A = np.c_[xx[m], yy[m], np.ones(m.sum())]
bg = np.empty_like(a)
for c in range(3):
    co, *_ = np.linalg.lstsq(A, a[m][:, c], rcond=None)
    bg[..., c] = co[0]*xx + co[1]*yy + co[2]

d = a - bg
melhor_r = np.full((h, w), np.inf, np.float32)
melhor_k = np.full((h, w), -1, np.int8); melhor_a = np.zeros((h, w), np.float32)
for i, tinta in enumerate((BRANCO, AMARELO)):
    f = np.array(tinta, np.float32) - bg
    al = np.clip((d*f).sum(2) / (f*f).sum(2), 0, 1)
    r = np.linalg.norm(d - al[..., None]*f, axis=2)
    sel = r < melhor_r
    melhor_r, melhor_k, melhor_a = np.where(sel, r, melhor_r), np.where(sel, np.int8(i), melhor_k), np.where(sel, al, melhor_a)

paths = []
for i, (tinta, hexa, nome) in enumerate(((BRANCO,"#FFFFFF","fast-limao"), (AMARELO,"#FBE007","escova"))):
    mk = (melhor_k == i) & (melhor_a > 0.5)
    p = potrace.Bitmap(~mk).trace(turdsize=int(8*S*S), alphamax=1.0, opttolerance=0.2)
    s, dd, n = 1.0/S, [], 0
    for c in p:
        st = c.start_point; dd.append(f"M{st.x*s:.2f},{st.y*s:.2f}")
        for g in c:
            if g.is_corner: dd.append(f"L{g.c.x*s:.2f},{g.c.y*s:.2f}L{g.end_point.x*s:.2f},{g.end_point.y*s:.2f}")
            else: dd.append(f"C{g.c1.x*s:.2f},{g.c1.y*s:.2f} {g.c2.x*s:.2f},{g.c2.y*s:.2f} {g.end_point.x*s:.2f},{g.end_point.y*s:.2f}")
        dd.append("Z"); n += 1
    paths.append(f'<path id="{nome}" fill="{hexa}" fill-rule="evenodd" d="{"".join(dd)}"/>')
    print(f"  {nome:12s} {hexa}  {n:3d} curvas")
open("fastescova.svg","w").write(
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
    + "".join(paths) + '</svg>')
print("  ->", W, "x", H)
