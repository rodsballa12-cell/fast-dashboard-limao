import numpy as np
from PIL import Image

def fundo_quadratico(a, m=7):
    """Plano de 2a ordem ajustado nas bordas: o roxo atras do logo tem glow,
    nao e um gradiente linear."""
    h, w, _ = a.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
    X, Y = xx/w, yy/h
    base = [np.ones_like(X), X, Y, X*X, Y*Y, X*Y]
    borda = np.zeros((h, w), bool)
    borda[:m], borda[-m:], borda[:, :m], borda[:, -m:] = True, True, True, True
    A = np.c_[tuple(b[borda] for b in base)]
    bg = np.empty_like(a)
    for c in range(3):
        co, *_ = np.linalg.lstsq(A, a[borda][:, c], rcond=None)
        bg[..., c] = sum(k*b for k, b in zip(co, base))
    return bg

a = np.asarray(Image.open("origem.jpg").convert("RGB").crop((252, 44, 896, 186)), np.float32)
bg = fundo_quadratico(a)
d = np.linalg.norm(a - bg, axis=2)
lo, hi = 46, 96                                   # limiar alto: mata o halo roxo
al = np.clip((d - lo) / (hi - lo), 0, 1)
cor = np.where(al[..., None] > .04, (a - bg*(1-al[..., None]))/np.maximum(al[..., None], .04), 0)
Image.fromarray(np.dstack([np.clip(cor, 0, 255), al*255]).astype(np.uint8), "RGBA").save("yazigi.png")
print(f"yazigi.png  transparente={100*(al<.02).mean():.1f}%  opaco={100*(al>.98).mean():.1f}%")
