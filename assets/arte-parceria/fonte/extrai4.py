import numpy as np
from PIL import Image
exec(open("extrai2.py").read().split("a = np.asarray")[0])   # fundo_quadratico

def unmatte(box, lo, hi):
    a  = np.asarray(Image.open("origem.jpg").convert("RGB").crop(box), np.float32)
    bg = fundo_quadratico(a)
    d  = np.linalg.norm(a - bg, axis=2)
    al = np.clip((d - lo)/(hi - lo), 0, 1)
    cor = np.where(al[..., None] > .04, (a - bg*(1-al[..., None]))/np.maximum(al[..., None], .04), 0)
    return a, np.clip(cor, 0, 255), al

# --- simbolo: mascara circular exata, pixels originais intactos ---
SB = (248, 42, 433, 227); CX = CY = 92.5; R = 89.5
a, _, _ = unmatte(SB, 58, 110)
yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]]
disco = np.clip(R + .5 - np.hypot(xx-CX, yy-CY), 0, 1)
simb = np.dstack([a, disco*255]).astype(np.uint8)

# --- wordmark: unmatte com limiar alto, longe do brush amarelo ---
_, cor, al = unmatte((455, 76, 878, 184), 58, 110)
txt = np.dstack([cor, al*255]).astype(np.uint8)

GAP = 32
W = simb.shape[1] + GAP + txt.shape[1]; H = simb.shape[0]
out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
out.paste(Image.fromarray(simb, "RGBA"), (0, 0))
out.paste(Image.fromarray(txt, "RGBA"), (simb.shape[1] + GAP, 34))
out.save("yazigi.png")
al_f = np.array(out)[..., 3]
print(f"yazigi.png {W}x{H}  transparente={100*(al_f<5).mean():.1f}%  opaco={100*(al_f>250).mean():.1f}%")
