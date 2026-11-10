"""uso: python camadas.py <pasta com pronto.png, obra.png, linhas.png>
Prepara camadas: alinha obra/linhas ao pronto, gera terreno sem linhas e pronto com luzes apagadas."""
import cv2, numpy as np, sys, os
S = sys.argv[1]
ld = lambda n: cv2.imread(os.path.join(S, n + '.png'), cv2.IMREAD_COLOR)
pronto, obra, linhas = ld('pronto'), ld('obra'), ld('linhas')
H, W = pronto.shape[:2]

# Mascara do fundo (fora do prédio/terreno) para alinhar só pelo entorno
mask = np.full((H, W), 255, np.uint8)
x0, x1 = int(0.27 * W), int(0.73 * W)
mask[:, x0:x1] = 0                       # faixa do prédio
mask[int(0.55 * H):, int(0.17 * W):int(0.86 * W)] = 0  # terreno/canteiro

def align(src, name):
    g1 = cv2.cvtColor(pronto, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255
    g2 = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255
    s = 0.25
    a = cv2.resize(g1, None, fx=s, fy=s); b = cv2.resize(g2, None, fx=s, fy=s)
    m = cv2.resize(mask, None, fx=s, fy=s, interpolation=cv2.INTER_NEAREST)
    warp = np.eye(2, 3, dtype=np.float32)
    try:
        cc, warp = cv2.findTransformECC(a, b, warp, cv2.MOTION_AFFINE,
                                        (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 300, 1e-6), m, 5)
    except cv2.error as e:
        print(name, 'ECC falhou', e); return src
    warp[:, 2] /= s
    print(name, 'cc=%.4f' % cc, 'desloc=(%.1f, %.1f) px' % (warp[0, 2], warp[1, 2]),
          'escala=%.4f' % warp[0, 0])
    if abs(warp[0, 2]) < 0.5 and abs(warp[1, 2]) < 0.5 and abs(warp[0, 0] - 1) < 1e-3:
        return src
    return cv2.warpAffine(src, warp, (W, H), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP,
                          borderMode=cv2.BORDER_REFLECT)

obra = align(obra, 'obra'); linhas = align(linhas, 'linhas')
cv2.imwrite(os.path.join(S, 'A_obra.png'), obra)
cv2.imwrite(os.path.join(S, 'A_linhas.png'), linhas)
cv2.imwrite(os.path.join(S, 'A_pronto.png'), pronto)

# --- Terreno sem linhas: detecta as linhas douradas finas (top-hat) e pinta por cima em duas passadas.
# Fica com "fantasmas" leves; por isso a animação nunca mostra o terreno puro, só com as linhas a 30%.
g = cv2.cvtColor(linhas, cv2.COLOR_BGR2GRAY).astype(np.float32)
hsv = cv2.cvtColor(linhas, cv2.COLOR_BGR2HSV).astype(np.int32)
el = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
top = g - cv2.morphologyEx(g, cv2.MORPH_OPEN, el)
m = ((top > 14) & (hsv[..., 0] >= 10) & (hsv[..., 0] <= 40) & (hsv[..., 1] > 25)).astype(np.uint8) * 255
reg = np.zeros_like(m); reg[int(0.04 * H):int(0.81 * H), int(0.28 * W):int(0.72 * W)] = 255
m = cv2.bitwise_and(m, reg)
m = cv2.dilate(cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8)), np.ones((3, 3), np.uint8), 2)
terreno = cv2.inpaint(linhas, m, 4, cv2.INPAINT_TELEA)
g2 = cv2.cvtColor(terreno, cv2.COLOR_BGR2GRAY).astype(np.float32)
m2 = cv2.bitwise_and(((g2 - cv2.morphologyEx(g2, cv2.MORPH_OPEN, el)) > 10).astype(np.uint8) * 255, reg)
terreno = cv2.inpaint(terreno, cv2.dilate(m2, np.ones((3, 3), np.uint8), 1), 4, cv2.INPAINT_TELEA)
cv2.imwrite(os.path.join(S, 'A_terreno.png'), terreno)

# --- Pronto com luzes apagadas: escurece e esfria os pixels quentes e claros do prédio
hsv = cv2.cvtColor(pronto, cv2.COLOR_BGR2HSV).astype(np.float32)
h, s_, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
warm = np.clip((s_ - 70) / 80, 0, 1) * np.clip((v - 140) / 80, 0, 1) * ((h > 8) & (h < 35))
reg = np.zeros((H, W), np.float32); reg[int(0.05 * H):int(0.97 * H), int(0.18 * W):int(0.82 * W)] = 1
warm = cv2.GaussianBlur(warm * reg, (0, 0), 3)
off = hsv.copy()
off[..., 1] = s_ * (1 - 0.85 * warm)
off[..., 2] = v * (1 - 0.62 * warm)
off = cv2.cvtColor(np.clip(off, 0, 255).astype(np.uint8), cv2.COLOR_HSV2BGR)
# leve tom azulado do anoitecer no vidro apagado
tint = np.array([18, 6, -6], np.float32)
off = np.clip(off.astype(np.float32) + warm[..., None] * tint, 0, 255).astype(np.uint8)
cv2.imwrite(os.path.join(S, 'A_pronto_off.png'), off)
cv2.imwrite(os.path.join(S, 'M_luzes.png'), (warm * 255).astype(np.uint8))
print('ok')
