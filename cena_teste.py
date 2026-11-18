# Robô 2D (novo) - cena de teste: Lucas acha a portinha na árvore.
# Desenha cartoon 2D com Pillow (supersample p/ bordas lisas), voz edge_tts, legenda, mp4 9:16 1080p.
import asyncio, math, os, subprocess, json
import numpy as np
import edge_tts
from PIL import Image, ImageDraw, ImageFont, ImageFilter

AQUI = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(AQUI, "saida"); os.makedirs(SAIDA, exist_ok=True)
import shutil
_WIN_FF = r"C:\Users\USUARIO\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin\ffmpeg.exe"
FF = shutil.which("ffmpeg") or _WIN_FF
FP = shutil.which("ffprobe") or _WIN_FF.replace("ffmpeg.exe", "ffprobe.exe")

def fonte(tam):  # Arial no Windows, DejaVu na nuvem (Linux)
    for f in (r"C:\Windows\Fonts\arialbd.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        if os.path.exists(f): return ImageFont.truetype(f, tam)
    return ImageFont.load_default(tam)
W, H, SS, FPS = 1080, 1920, 2, 30
OUT = (2, 2, 2)  # cor do contorno

FALAS = [  # (quem, texto, voz, tom)
    ("narra", "O Lucas voltava pra casa pelo caminho de sempre...", "pt-BR-ThalitaMultilingualNeural", "+0Hz"),
    ("lucas", "Ué... desde quando essa árvore tem uma porta?", "pt-BR-AntonioNeural", "+25Hz"),
    ("lucas", "Ela é do tamanho da minha mão!", "pt-BR-AntonioNeural", "+25Hz"),
    ("bicho", "Ei! Fecha isso, gigante! Tá entrando vento!", "pt-BR-FranciscaNeural", "+60Hz"),
    ("lucas", "Você... fala?!", "pt-BR-AntonioNeural", "+25Hz"),
]

async def gravar():
    info = []
    for i, (q, t, v, p) in enumerate(FALAS):
        f = os.path.join(SAIDA, f"fala{i}.mp3")
        await edge_tts.Communicate(t, v, pitch=p).save(f)
        d = float(subprocess.check_output([FP, "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", f]).decode())
        info.append((f, d))
    return info

# ---------- câmera ----------
class Cam:
    def __init__(s, x, y, z): s.x, s.y, s.z = x, y, z
    def p(s, x, y): return ((x - s.x) * s.z + W / 2) * SS, ((y - s.y) * s.z + H / 2) * SS
    def r(s, v): return v * s.z * SS

def elipse(d, c, x, y, rx, ry, cor, borda=6):
    (a, b) = c.p(x - rx, y - ry); (e, f) = c.p(x + rx, y + ry)
    d.ellipse([a, b, e, f], fill=cor, outline=OUT if borda else None, width=int(c.r(borda)) if borda else 0)

def poli(d, c, pts, cor, borda=6):
    d.polygon([c.p(x, y) for x, y in pts], fill=cor, outline=OUT if borda else None, width=int(c.r(borda)) if borda else 0)

def ret(d, c, x, y, w, h, cor, raio=20, borda=6):
    (a, b) = c.p(x, y); (e, f) = c.p(x + w, y + h)
    d.rounded_rectangle([a, b, e, f], radius=c.r(raio), fill=cor, outline=OUT if borda else None, width=int(c.r(borda)) if borda else 0)

def linha(d, c, pts, cor, larg):
    d.line([c.p(x, y) for x, y in pts], fill=cor, width=max(1, int(c.r(larg))), joint="curve")

# ---------- cenário ----------
FUNDO = None
def ceu():
    global FUNDO
    if FUNDO is None:
        g = np.linspace(0, 1, H * SS)[:, None]
        top, bot = np.array([255, 170, 120]), np.array([255, 225, 170])  # fim de tarde
        col = (top * (1 - g) + bot * g).astype(np.uint8)
        FUNDO = Image.fromarray(np.repeat(col[:, None, :], W * SS, 1).reshape(H * SS, W * SS, 3))
    return FUNDO.copy()

def cenario(d, c, t):
    # sol, morros, casas ao longe, nuvens
    elipse(d, c, 700, 300, 120, 120, (255, 236, 150), 0)
    for i, (x, cor) in enumerate([(-400, (150, 190, 120)), (500, (130, 175, 105)), (1400, (150, 190, 120))]):
        elipse(d, c, x, 1250, 700, 380, cor, 0)
    for k in range(3):
        nx = (-300 + k * 650 + t * 25) % 2200 - 600
        for dx, r in [(0, 70), (70, 90), (150, 65)]:
            elipse(d, c, nx + dx, 380 + k * 90, r, r * .7, (255, 250, 245), 0)
    for i, x in enumerate([-200, 1150]):
        ret(d, c, x, 980, 220, 200, [(235, 120, 100), (120, 160, 220)][i], 10, 5)
        poli(d, c, [(x - 20, 985), (x + 110, 880), (x + 240, 985)], (120, 70, 60), 5)
        ret(d, c, x + 80, 1080, 60, 100, (110, 70, 50), 8, 4)
    # chão e calçada
    ret(d, c, -2000, 1250, 5000, 1500, (110, 175, 85), 0, 0)
    ret(d, c, -2000, 1330, 5000, 140, (215, 200, 175), 0, 5)
    for i in range(-10, 30):
        linha(d, c, [(i * 160, 1335), (i * 160, 1465)], (185, 170, 150), 4)
    # grama tufos
    for i in range(-15, 40):
        x = i * 97 % 3000 - 900
        poli(d, c, [(x, 1560), (x + 12, 1515 + (i % 3) * 8), (x + 24, 1560)], (80, 150, 70), 0)

def arvore(d, c, t, porta_aberta):
    X = 820
    poli(d, c, [(X - 85, 1330), (X - 60, 850), (X + 60, 850), (X + 85, 1330)], (140, 90, 55), 7)
    for (dx, dy) in [(-40, 1000), (30, 1150), (-10, 1250)]:
        linha(d, c, [(X + dx, dy), (X + dx + 15, dy + 50)], (110, 70, 40), 5)
    sway = math.sin(t * 1.3) * 6
    for (dx, dy, r) in [(-150, 760, 170), (130, 740, 180), (0, 620, 210), (-60, 850, 150), (110, 860, 150)]:
        elipse(d, c, X + dx + sway, dy, r, r * .85, (70, 150, 75), 7)
    for (dx, dy, r) in [(-90, 640, 60), (80, 600, 50), (10, 760, 55)]:
        elipse(d, c, X + dx + sway, dy, r, r * .7, (100, 185, 95), 0)
    # portinha (base da árvore)
    px, py = X - 22, 1255
    ret(d, c, px - 6, py - 6, 56, 82, (90, 55, 30), 26, 5)
    if porta_aberta:
        ret(d, c, px, py, 44, 70, (255, 220, 120), 22, 0)  # luz lá dentro
        poli(d, c, [(px, py), (px - 26, py + 8), (px - 26, py + 66), (px, py + 70)], (190, 60, 60), 4)
    else:
        ret(d, c, px, py, 44, 70, (200, 65, 60), 22, 4)
        elipse(d, c, px + 34, py + 40, 4, 4, (255, 210, 80), 2)
    return px + 22, py + 50

# ---------- personagens ----------
def lucas(d, c, x, y, t, fala, olhar=1, susto=0, andando=False):
    pulo = abs(math.sin(t * 9)) * 14 if andando else math.sin(t * 2) * 3
    y = y - pulo
    perna = math.sin(t * 9) * 22 if andando else 0
    # pernas e tênis
    for s in (-1, 1):
        linha(d, c, [(x + s * 22, y + 150), (x + s * 22 + perna * s, y + 240)], (40, 60, 120), 26)
        elipse(d, c, x + s * 22 + perna * s + 10 * olhar, y + 248, 30, 16, (240, 240, 245), 5)
    # corpo (moletom laranja) e mochila
    ret(d, c, x - 75 * olhar - (0 if olhar > 0 else 0) - 30, y - 10, 40, 120, (60, 120, 200), 14, 5) if olhar > 0 else None
    ret(d, c, x - 60, y - 20, 120, 180, (250, 140, 50), 45, 7)
    # braços
    bx = math.sin(t * 9) * 18 if andando else (-60 if susto else 0)
    linha(d, c, [(x + 55 * olhar, y + 20), (x + 85 * olhar, y + 110 + bx)], (250, 140, 50), 28)
    elipse(d, c, x + 85 * olhar, y + 115 + bx, 17, 17, (255, 205, 165), 5)
    # cabeça grande
    hy = y - 120
    elipse(d, c, x, hy, 115, 110, (255, 205, 165), 7)
    elipse(d, c, x - 100 * olhar, hy + 5, 20, 28, (255, 190, 150), 5)  # orelha
    # cabelo
    poli(d, c, [(x - 115, hy - 15), (x - 95, hy - 95), (x - 30, hy - 125), (x + 50, hy - 120), (x + 110, hy - 70),
                (x + 118, hy - 10), (x + 70, hy - 55), (x + 20, hy - 40), (x - 40, hy - 60)], (70, 40, 25), 6)
    # olhos (piscam)
    pisca = (t % 3.2) < .12
    for s in (-1, 1):
        ex = x + 38 * olhar + s * 38
        if pisca: linha(d, c, [(ex - 18, hy + 5), (ex + 18, hy + 5)], OUT, 6)
        else:
            r = 28 if susto else 22
            elipse(d, c, ex, hy, r, r * 1.15, (255, 255, 255), 5)
            elipse(d, c, ex + 7 * olhar, hy + 3, 10, 12, (30, 30, 40), 0)
            elipse(d, c, ex + 10 * olhar, hy - 3, 4, 4, (255, 255, 255), 0)
        sob = -10 if susto else 0
        linha(d, c, [(ex - 18, hy - 38 + sob - s * 3), (ex + 18, hy - 40 + sob + s * 3)], (70, 40, 25), 7)
    # bochecha e boca
    elipse(d, c, x + 75 * olhar, hy + 45, 16, 10, (255, 160, 150), 0)
    mx, my = x + 40 * olhar, hy + 60
    if fala:
        ab = 6 + abs(math.sin(t * 22)) * 22
        elipse(d, c, mx, my, 24, ab, (120, 30, 40), 5)
        elipse(d, c, mx, my + ab * .5, 12, ab * .35, (230, 100, 110), 0)
    elif susto: elipse(d, c, mx, my, 14, 18, (120, 30, 40), 5)
    else: linha(d, c, [(mx - 22, my - 4), (mx, my + 6), (mx + 22, my - 4)], OUT, 6)

def bicho(d, c, x, y, t, fala, apar):
    if apar <= 0: return
    apar = min(1, apar)
    y = y + (1 - apar) * 60
    b = math.sin(t * 6) * 2
    AZ, AZ2 = (140, 200, 255), (110, 170, 235)
    y = y - 8  # sobe um pouco: agora tem pernas
    # pés e pernas
    for s in (-1, 1):
        linha(d, c, [(x + s * 6, y + 18), (x + s * 7, y + 26)], AZ2, 4)
        elipse(d, c, x + s * 9, y + 28, 6, 3.5, (255, 200, 80), 2)
    # corpinho com barriga
    elipse(d, c, x, y + 14 + b * .3, 12, 11, AZ, 3)
    elipse(d, c, x, y + 16 + b * .3, 7, 6, (225, 240, 255), 0)
    # bracinhos (um acena quando fala)
    ac = math.sin(t * 12) * 6 if fala else 0
    linha(d, c, [(x - 11, y + 11), (x - 19, y + 18)], AZ2, 3.5)
    linha(d, c, [(x + 11, y + 11), (x + 20, y + 2 + ac)], AZ2, 3.5)
    # cabeça
    elipse(d, c, x, y - 4 + b, 17, 15, AZ, 3)
    for s in (-1, 1): linha(d, c, [(x + s * 7, y - 16 + b), (x + s * 13, y - 30 + b)], OUT, 2.5); elipse(d, c, x + s * 13, y - 32 + b, 4.5, 4.5, (255, 120, 180), 2)
    for s in (-1, 1): elipse(d, c, x + s * 6, y - 6 + b, 5, 6, (255, 255, 255), 2); elipse(d, c, x + s * 6 + 1, y - 5 + b, 2.5, 2.7, OUT, 0)
    for s in (-1, 1): elipse(d, c, x + s * 12, y + b, 3, 2, (255, 160, 190), 0)
    if fala: elipse(d, c, x, y + 4 + b, 4.5, 1.5 + abs(math.sin(t * 25)) * 4, (120, 30, 40), 2)
    else: linha(d, c, [(x - 4, y + 3 + b), (x, y + 5 + b), (x + 4, y + 3 + b)], OUT, 2)

# ---------- legenda ----------
FONTE = fonte(62 * SS)
def legenda(img, txt):
    d = ImageDraw.Draw(img)
    palavras, linhas, l = txt.split(), [], ""
    for p in palavras:
        if d.textlength(l + " " + p, font=FONTE) > (W - 160) * SS and l: linhas.append(l); l = p
        else: l = (l + " " + p).strip()
    linhas.append(l)
    y = 1500 * SS
    for ln in linhas:
        w = d.textlength(ln, font=FONTE)
        d.text(((W * SS - w) / 2, y), ln, font=FONTE, fill=(255, 255, 255), stroke_width=7 * SS, stroke_fill=(0, 0, 0))
        y += 80 * SS

def lerp(a, b, k): k = max(0, min(1, k)); k = k * k * (3 - 2 * k); return a + (b - a) * k

def main():
    info = asyncio.run(gravar())
    # linha do tempo: cada fala começa depois da outra + pausa
    ini, t0 = [], 0.4
    for f, dur in info: ini.append((t0, dur)); t0 += dur + .35
    total = t0 + .8
    nf = int(total * FPS)
    proc = subprocess.Popen([FF, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                             "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "medium",
                             os.path.join(SAIDA, "video_mudo.mp4")], stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    for n in range(nf):
        t = n / FPS
        falando = next((i for i, (a, dd) in enumerate(ini) if a <= t < a + dd), None)
        quem = FALAS[falando][0] if falando is not None else None
        # roteiro: anda até a árvore -> para, olha -> porta abre -> bicho aparece -> susto
        t_abre, t_bicho, t_susto = ini[2][0] + ini[2][1] * .6, ini[3][0] - .3, ini[4][0]
        lx = lerp(150, 560, t / max(.1, ini[1][0]))
        andando = t < ini[1][0]
        # câmera: plano aberto -> aproxima na porta -> volta pro Lucas no susto
        if t < ini[1][0]: cam = Cam(lerp(400, 560, t / ini[1][0]), 1000, 1.0)
        elif t < t_bicho: cam = Cam(lerp(560, 760, (t - ini[1][0]) / 1.5), lerp(1000, 1180, (t - ini[1][0]) / 1.5), lerp(1.0, 1.6, (t - ini[1][0]) / 1.5))
        elif t < t_susto: cam = Cam(800, lerp(1180, 1290, (t - t_bicho) / .6), lerp(1.6, 4.2, (t - t_bicho) / .6))
        else:
            k = (t - t_susto) / .5
            cam = Cam(lerp(800, 600, k), lerp(1290, 1050, k), lerp(4.2, 1.5, k) + (math.sin(t * 50) * .02 if k < 1 else 0))
        img = ceu(); d = ImageDraw.Draw(img)
        cenario(d, cam, t)
        porta_x, porta_y = arvore(d, cam, t, t > t_abre)
        bicho(d, cam, porta_x, porta_y, t, quem == "bicho", (t - t_bicho) / .4)
        lucas(d, cam, lx, 1120, t, quem == "lucas", 1, t >= t_susto, andando)
        if falando is not None: legenda(img, FALAS[falando][1])
        img = img.resize((W, H), Image.LANCZOS)
        proc.stdin.write(img.tobytes())
    proc.stdin.close(); proc.wait()
    # áudio: cada fala no seu tempo
    args, filt = [FF, "-y", "-i", os.path.join(SAIDA, "video_mudo.mp4")], []
    for i, ((f, _), (a, _)) in enumerate(zip(info, ini)):
        args += ["-i", f]; filt.append(f"[{i+1}]adelay={int(a*1000)}|{int(a*1000)}[a{i}]")
    filt.append("".join(f"[a{i}]" for i in range(len(info))) + f"amix=inputs={len(info)}:normalize=0[aud]")
    final = os.path.join(SAIDA, "teste_2d_lucas.mp4")
    subprocess.run(args + ["-filter_complex", ";".join(filt), "-map", "0:v", "-map", "[aud]", "-c:v", "copy", "-c:a", "aac", "-shortest", final], check=True, stderr=subprocess.DEVNULL)
    print(json.dumps({"arquivo": final, "duracao": round(total, 1)}))

if __name__ == "__main__":
    main()

