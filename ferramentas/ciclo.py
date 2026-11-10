"""Animação do ciclo do prédio a partir de 3 imagens-chave (terreno/linhas, obra, pronto).

uso: python render.py <pasta_camadas> <saida> [video]
  gera <saida>/1600/001..096.webp, <saida>/960/..., <saida>/etapas/*.webp e (opcional) <saida>/previa.mp4
Linha do tempo (progresso p de 0 a 1, igual à rolagem do site):
  0.00-0.13 terreno: linhas do projeto acendem de baixo para cima
  0.13-0.30 projeto: holograma completo, pulsando leve
  0.30-0.68 estrutura: concreto sobe andar por andar no lugar das linhas, canteiro e grua aparecem
  0.68-0.90 fechamento: fachada fecha de baixo para cima, grua e canteiro somem, paisagismo aparece
  0.90-1.00 entrega: luzes acendem janela por janela
"""
import cv2, numpy as np, os, sys, subprocess
from PIL import Image

S, OUT = sys.argv[1], sys.argv[2]
VIDEO = len(sys.argv) > 3 and sys.argv[3] == 'video'
rd = lambda n: cv2.imread(os.path.join(S, n), cv2.IMREAD_COLOR).astype(np.float32)
T, L, O, P, Poff = (rd('A_terreno.png'), rd('A_linhas.png'), rd('A_obra.png'),
                    rd('A_pronto.png'), rd('A_pronto_off.png'))
H, W = P.shape[:2]
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)

def ss(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)

def rect(x0, x1, y0, y1, f):
    return (ss(x0 - f, x0 + f, xx) * (1 - ss(x1 - f, x1 + f, xx)) *
            ss(y0 - f, y0 + f, yy) * (1 - ss(y1 - f, y1 + f, yy)))[..., None]

# zonas (coordenadas da imagem 2752x1536)
ZB = (ss(700 - 80, 700 + 80, xx) * (1 - ss(2070 - 80, 2070 + 80, xx)) *
      (1 - ss(1235 - 18, 1235 + 18, yy)))[..., None]   # prédio (inclui a grua), borda larga p/ não marcar o céu
ZL = rect(470, 2340, 1150, 1470, 40) * (1 - ZB)  # terreno / canteiro
ZF = np.clip(1 - ZB - ZL, 0, 1)                  # entorno
BASE, TOPO = 1225.0, 105.0
NIVEIS = [1225, 1066, 943, 812, 681, 550, 427, 296, 40]  # base, lajes e topo da estrutura
BX0, BX1 = 805, 1955

DL = L - T                                        # brilho das linhas
DLm = np.clip(DL.max(axis=2, keepdims=True) / 60, 0, 1)   # onde há linha

# luzes acendendo por janela: componentes da máscara com atraso aleatório
mL = cv2.imread(os.path.join(S, 'M_luzes.png'), 0)
n, lab = cv2.connectedComponents((mL > 40).astype(np.uint8), connectivity=8)
rng = np.random.default_rng(7)
atraso = rng.uniform(0, 0.6, n + 1).astype(np.float32); atraso[0] = 0.3
ATR = cv2.GaussianBlur(atraso[lab], (0, 0), 4)[..., None]

def frente(p, a, b, niveis, degraus=True):
    u = np.clip((p - a) / (b - a), 0, 1)
    if not degraus:
        e = u * u * (3 - 2 * u); return niveis[0] + (niveis[-1] - niveis[0]) * e
    k = len(niveis) - 1; v = u * k; i = min(int(v), k - 1); f = v - i
    f = float(ss(0.12, 0.88, f))
    return niveis[i] + (niveis[i + 1] - niveis[i]) * f

def brilho_frente(y, larg, cor, inten):
    band = np.exp(-((yy - y) / larg) ** 2)[..., None] * rect(BX0, BX1, -9999, 9999, 25)
    return band * np.array(cor, np.float32) * inten

def quadro(p):
    # 1) projeto / holograma
    if p < 0.13:
        y = frente(p, 0.0, 0.13, [BASE + 30, TOPO - 60], degraus=False)
        acesa = 1 - ss(y - 40, y + 40, yy)[..., None]        # abaixo da linha de varredura: acesa
        acesa = 1 - acesa                                       # inverte: acende de baixo p/ cima
        k = 0.3 + 0.7 * acesa
        img = T + DL * k
        img += brilho_frente(y, 14, (90, 190, 255), 0.55 * float(ss(0, 0.02, p)) * (1 - float(ss(0.11, 0.13, p)))) * (0.4 + DLm)
        return img
    puls = 1 + 0.07 * np.sin((p - 0.13) / 0.17 * np.pi * 2)
    holo = T + DL * (puls if p < 0.30 else 1.0)
    if p < 0.30:
        return holo
    # 2) estrutura
    if p < 0.68:
        y = frente(p, 0.30, 0.68, NIVEIS)
        abaixo = ss(y - 10, y + 10, yy)[..., None]
        canteiro = float(ss(0.30, 0.37, p))
        fundo = float(ss(0.30, 0.68, p))
        img = (ZB * (O * abaixo + holo * (1 - abaixo)) +
               ZL * (O * canteiro + holo * (1 - canteiro)) +
               ZF * (O * fundo + holo * (1 - fundo)))
        g = 0.5 * (1 - float(ss(0.64, 0.68, p)))
        img += brilho_frente(y, 9, (80, 180, 255), g)
        return img
    # 3) fechamento
    if p < 0.90:
        y = frente(p, 0.68, 0.89, [BASE, TOPO - 40], degraus=False)
        abaixo = ss(y - 30, y + 30, yy)[..., None]
        verde = float(ss(0.68, 0.78, p))
        fundo = float(ss(0.68, 0.90, p))
        img = (ZB * (Poff * abaixo + O * (1 - abaixo)) +
               ZL * (Poff * verde + O * (1 - verde)) +
               ZF * (P * fundo + O * (1 - fundo)))
        img += brilho_frente(y, 16, (235, 240, 245), 0.18 * (1 - float(ss(0.86, 0.90, p))))
        return img
    # 4) luzes
    u = (p - 0.90) / 0.10
    a = np.clip((u * 1.25 - ATR) / 0.35, 0, 1)
    a = a * a * (3 - 2 * a)
    base = ZB + ZL
    return base * (Poff * (1 - a) + P * a) + ZF * P

def camera(img, p, w, h):
    e = p * p * (3 - 2 * p)
    z = 1.035 + 0.085 * e                       # aproxima devagar
    cx = W * (0.488 + 0.024 * e)                # desliza para a direita
    cy = H * (0.505 - 0.012 * e)
    cw = (H * 16 / 9) / z; ch = H / z
    s = w / cw
    M = np.array([[s, 0, w / 2 - s * cx], [0, s, h / 2 - s * cy]], np.float32)
    return cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_AREA if s < 1 else cv2.INTER_LINEAR,
                          borderMode=cv2.BORDER_REFLECT)

def salvar_webp(arr, caminho, q):
    Image.fromarray(cv2.cvtColor(arr, cv2.COLOR_BGR2RGB)).save(caminho, 'WEBP', quality=q, method=6)

def out8(x): return np.clip(x, 0, 255).astype(np.uint8)

if __name__ == '__main__':
    for d in ('1600', '960', 'etapas'):
        os.makedirs(os.path.join(OUT, d), exist_ok=True)
    TOTAL = 96
    for i in range(TOTAL):
        p = i / (TOTAL - 1)
        f = quadro(p)
        a = out8(camera(f, p, 1600, 900)); salvar_webp(a, os.path.join(OUT, '1600', '%03d.webp' % (i + 1)), 72)
        b = out8(camera(f, p, 960, 540)); salvar_webp(b, os.path.join(OUT, '960', '%03d.webp' % (i + 1)), 70)
        print('quadro', i + 1, flush=True) if (i + 1) % 12 == 0 else None
    # imagens dos serviços (sem movimento de câmera, enquadramento neutro)
    for nome, p in [('projeto', 0.22), ('gestao', 0.62), ('obra', 0.47), ('vistoria', 0.80), ('laudo', 1.0)]:
        salvar_webp(out8(camera(quadro(p), 0.5, 960, 540)), os.path.join(OUT, 'etapas', nome + '.webp'), 80)
    if VIDEO:
        fps, dur = 24, 16
        cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', '1600x900',
               '-r', str(fps), '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20',
               '-pix_fmt', 'yuv420p', '-movflags', '+faststart', os.path.join(OUT, 'previa.mp4')]
        pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        N = fps * dur
        for j in range(N):
            p = j / (N - 1)
            pr.stdin.write(out8(camera(quadro(p), p, 1600, 900)).tobytes())
        pr.stdin.close(); pr.wait()
        print('video ok')
