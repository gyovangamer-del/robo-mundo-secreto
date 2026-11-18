# Robô 2D - Episódio 1 completo: "O Menino que Encontrou um Mundo Secreto" (~60 s, 9:16, 1080p)
import asyncio, math, os, subprocess, json, hashlib
from PIL import Image, ImageDraw
import edge_tts
import cena_teste as B
import eleven
from cena_teste import Cam, elipse, poli, ret, linha, lerp, W, H, SS, FPS, OUT, FF, FP, SAIDA

LUCAS = ("pt-BR-ThalitaMultilingualNeural", "+8%", "-6Hz", "TX3LPaxmHKxFdv7VOQHJ")   # voz A
PIPO = ("pt-BR-FranciscaNeural", "+15%", "+20Hz", "cgSgspJ2msm6clMCkdW9")            # bichinho opção 1
PREF = ("pt-BR-AntonioNeural", "-5%", "-4Hz", "pqHfZKP75CvOlQylNhV4")                # adulto (opção 1)
GIGA = ("pt-BR-FranciscaNeural", "-12%", "-25Hz", "FGY2WhTYpPnrIDTdsKH5")            # criança gigante
MAE = ("pt-BR-FranciscaNeural", "-5%", "-10Hz", "EXAVITQu4vr4xnSDxMaL")              # mãe da gigante (fora de cena)

# (cena, quem, texto, voz)
ROT = [
    ("rua", "lucas", "Mesmo caminho de sempre... ué. Desde quando essa árvore tem uma porta?", LUCAS),
    ("rua", "lucas", "Ela é do tamanho da minha mão!", LUCAS),
    ("rua", "pipo", "Ei! Fecha isso, gigante! Tá entrando vento!", PIPO),
    ("rua", "lucas", "Você... fala?!", LUCAS),
    ("dentro", "pipo", "Falo, canto e cobro pedágio. Bem-vindo a Miudópolis!", PIPO),
    ("dentro", "lucas", "Uma cidade inteira aqui dentro?!", LUCAS),
    ("dentro", "pipo", "Tem padaria de migalha, piscina de gota de orvalho e o Seu Tonho ali, ó.", PIPO),
    ("dentro", "lucas", "Ele tá dormindo?", LUCAS),
    ("dentro", "pipo", "Desde terça. Do ano passado.", PIPO),
    ("dentro", "pref", "Pipo! De novo trazendo gigante? Ele vai pisar na praça!", PREF),
    ("dentro", "pipo", "Calma, prefeito. Esse é legal. Só tem um olho meio grande.", PIPO),
    ("dentro", "lucas", "É que eu tô olhando pela porta!", LUCAS),
    ("dentro", "pref", "Gigante, escuta bem. Nunca conte pra ninguém que a gente existe.", PREF),
    ("dentro", "lucas", "Por quê?", LUCAS),
    ("dentro", "pref", "Porque eles também nunca contaram que vocês existem.", PREF),
    ("dentro", "lucas", "Eles... quem?", LUCAS),
    ("pote", "giga", "Mãe! Olha! O homenzinho do meu pote achou a porta!", GIGA),
    ("pote", "mae", "Que bom, filha. Agora fecha a tampa, que tá entrando vento.", MAE),
    ("pote", "lucas", "...ah, não.", LUCAS),
]

async def gravar():
    out = []
    for i, (_, _, txt, (v, r, p, eid)) in enumerate(ROT):
        f = os.path.join(SAIDA, "ep_" + hashlib.sha1((txt + eid).encode()).hexdigest()[:12] + ".mp3")
        if os.path.exists(f) and os.path.getsize(f) > 1000: pass  # já gravada: não gasta cota de novo
        else:
         try: eleven.falar(txt, eid, f)            # ElevenLabs
         except Exception as e:                    # sem cota/sem internet: volta pra voz grátis
            print("ElevenLabs falhou, usando voz grátis:", type(e).__name__)
            await edge_tts.Communicate(txt, v, rate=r, pitch=p).save(f)
        d = float(subprocess.check_output([FP, "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", f]).decode())
        out.append((f, d))
    return out

def camchar(base, x0, y0, sx, sy, k):
    """câmera pra desenhar um personagem (pos. mundo x0,y0) na tela em sx,sy com escala k."""
    z = base.z * k
    return Cam(x0 - (sx - W / 2) / z, y0 - (sy - H / 2) / z, z)

# ---------- personagens novos ----------
def prefeito(d, c, x, y, t, fala):
    # caracol virado pra esquerda (olhando pro Pipo), pescoço em pé, cara grande e expressiva
    b = math.sin(t * 2.5) * 1.5
    PELE, PELE2 = (150, 205, 130), (120, 180, 105)
    # pé/corpo comprido no chão
    ret(d, c, x - 48, y + 8, 90, 18, PELE, 9, 3)
    # concha nas costas (direita) com espiral
    cx, cy = x + 18, y - 12 + b
    elipse(d, c, cx, cy, 28, 26, (235, 160, 70), 3)
    esp = [(cx + math.cos(a) * (2 + a * 3.1), cy + math.sin(a) * (2 + a * 2.9)) for a in [i * .25 for i in range(30)]]
    linha(d, c, esp, (170, 95, 35), 3)
    # pescoço + cabeça na frente (esquerda)
    ret(d, c, x - 42, y - 22 + b, 22, 40, PELE, 10, 3)
    hx, hy = x - 32, y - 30 + b
    elipse(d, c, hx, hy, 19, 17, PELE, 3)
    # antenas com olhos
    for s, dx in ((0, -18), (1, 13)):
        linha(d, c, [(hx + dx * .4, hy - 12), (hx + dx, hy - 30)], PELE2, 3)
        elipse(d, c, hx + dx, hy - 32, 6, 6.5, (255, 255, 255), 2)
        elipse(d, c, hx + dx - 1.5, hy - 31.5, 2.6, 2.8, OUT, 0)
    # monóculo
    elipse(d, c, hx + 13, hy - 32, 8, 8, None, 2); linha(d, c, [(hx + 20, hy - 28), (hx + 22, hy - 14)], (200, 170, 60), 1.5)
    # bigode e boca
    if fala: elipse(d, c, hx - 6, hy + 7, 4.5, 1.5 + abs(math.sin(t * 22)) * 4, (120, 30, 40), 2)
    else: linha(d, c, [(hx - 10, hy + 7), (hx - 2, hy + 8)], OUT, 2)
    linha(d, c, [(hx + 2, hy + 3), (hx - 6, hy + 1), (hx - 16, hy + 5)], (90, 60, 40), 3.5)
    elipse(d, c, hx + 8, hy + 4, 4, 2.5, (240, 150, 150), 0)  # bochecha
    # cartola entre as antenas
    ret(d, c, hx - 13, hy - 18, 22, 4, (40, 40, 50), 2, 2); ret(d, c, hx - 9, hy - 31, 14, 14, (40, 40, 50), 3, 2)
    ret(d, c, hx - 9, hy - 22, 14, 3, (200, 60, 60), 1, 0)

def criaturinha(d, c, x, y, t, cor, fase):
    b = abs(math.sin(t * 5 + fase)) * 4
    elipse(d, c, x, y - b, 12, 11, cor, 3)
    for s in (-1, 1): elipse(d, c, x + s * 4, y - 3 - b, 3, 3.5, (255, 255, 255), 1); elipse(d, c, x + s * 4, y - 2.5 - b, 1.4, 1.4, OUT, 0)

# ---------- cenas ----------
def cena_rua(img, t, falas, iloc, quem):
    a1, a2, a3 = falas[1], falas[2], falas[3]
    t_abre, t_pipo, t_susto = a1[0] + a1[1] * .6, a2[0] - .3, a3[0]
    andando = t < falas[0][0] + falas[0][1] * .55
    lx = lerp(150, 560, t / max(.1, falas[0][0] + falas[0][1] * .55))
    tp = falas[0][0] + falas[0][1] * .55
    if t < tp: cam = Cam(lerp(400, 560, t / tp), 1000, 1.0)
    elif t < t_pipo: k = (t - tp) / 1.5; cam = Cam(lerp(560, 760, k), lerp(1000, 1180, k), lerp(1.0, 1.6, k))
    elif t < t_susto: k = (t - t_pipo) / .6; cam = Cam(800, lerp(1180, 1290, k), lerp(1.6, 4.2, k))
    else:
        k = (t - t_susto) / .5
        cam = Cam(lerp(800, 600, k), lerp(1290, 1050, k), lerp(4.2, 1.5, k) + (math.sin(t * 50) * .02 if k < 1 else 0))
    d = ImageDraw.Draw(img)
    B.cenario(d, cam, t)
    px, py = B.arvore(d, cam, t, t > t_abre)
    B.bicho(d, cam, px, py, t, quem == "pipo", (t - t_pipo) / .4)
    B.lucas(d, cam, lx, 1120, t, quem == "lucas", 1, t >= t_susto, andando)

def fundo_dentro(d, c, t):
    ret(d, c, -500, -200, 2200, 2400, (120, 75, 45), 0, 0)                    # parede de madeira (dentro da árvore)
    for i in range(9): elipse(d, c, 540, 300, 300 + i * 110, 200 + i * 80, None, 0) if False else linha(d, c, [(-200, 200 + i * 130 + math.sin(i) * 20), (1300, 230 + i * 130)], (105, 65, 40), 6)
    for k in range(7):                                                         # varal de lanternas
        x = 60 + k * 160; y = 640 + math.sin(k * 1.7) * 30
        linha(d, c, [(x - 80, 620), (x, y), (x + 80, 620)], (60, 40, 25), 3)
        brilho = 220 + int(math.sin(t * 3 + k) * 30)
        elipse(d, c, x, y + 30, 26, 32, (255, brilho, 120), 4)
    ret(d, c, -500, 1300, 2200, 900, (95, 160, 80), 0, 0)                      # chão de musgo
    for (x, s, cor) in [(120, 1.0, (220, 60, 60)), (420, .8, (240, 160, 60)), (880, 1.1, (200, 80, 180)), (1050, .7, (90, 150, 230))]:
        ret(d, c, x - 45 * s, 1300 - 170 * s, 90 * s, 175 * s, (245, 235, 210), 18, 5)    # cogumelo-casa
        ret(d, c, x - 18 * s, 1300 - 90 * s, 36 * s, 60 * s, (255, 210, 110), 10, 4)       # janela acesa
        elipse(d, c, x, 1300 - 175 * s, 130 * s, 80 * s, cor, 6)
        for dx, dy in [(-60, -10), (10, -40), (60, 0), (-20, 20)]: elipse(d, c, x + dx * s, 1300 - 175 * s + dy * s, 14 * s, 11 * s, (255, 255, 255), 0)

def cena_dentro(img, t, tl, quem):
    # câmera vai até quem fala; olho do Lucas na porta à esquerda
    alvo = {"pipo": (480, 1120, 1.2), "pref": (720, 1130, 1.2), "lucas": (420, 1000, 1.0)}.get(quem, (540, 1050, 1.0))
    if not hasattr(cena_dentro, "cam"): cena_dentro.cam = [540, 1050, 1.0]
    cc = cena_dentro.cam
    for i in range(3): cc[i] += (alvo[i] - cc[i]) * .12
    cam = Cam(*cc)
    d = ImageDraw.Draw(img)
    fundo_dentro(d, cam, t)
    for i in range(10):  # povo de Miudópolis ao fundo
        criaturinha(d, camchar(cam, 0, 0, 0, 0, 1), 0, 0, 0, (0, 0, 0), 0) if False else None
        cx = [90, 180, 560, 610, 1010, 1060, 250, 960, 140, 1000][i]; cy = 1302 - (i // 6) * 6
        criaturinha(d, camchar(cam, 0, 0, cx, cy - 20, 2.0), 0, 0, t, [(255, 200, 90), (150, 230, 160), (240, 140, 200), (140, 200, 255)][i % 4], i)
    # Seu Tonho dormindo em cima do cogumelo laranja (zzz)
    tc = camchar(cam, 0, 0, *cam.p(130, 1068), 1) if False else None
    elipse(d, cam, 130, 1078, 34, 22, (200, 170, 230), 5)
    for s in (-1, 1): linha(d, cam, [(130 + s * 14 - 6, 1074), (130 + s * 14 + 6, 1074)], OUT, 4)
    for k2 in range(3):
        fz = (t * .6 + k2 / 3) % 1
        tx, ty = cam.p(160 + fz * 60, 1040 - fz * 120)
        d.text((tx, ty), "z", font=B.FONTE, fill=(255, 255, 255), stroke_width=4 * SS, stroke_fill=OUT)
    # porta redonda com o OLHO gigante do Lucas
    elipse(d, cam, 60, 950, 210, 300, (255, 225, 170), 10)
    elipse(d, cam, 75, 950, 150, 150, (255, 205, 165), 0)
    pis = (t % 3.7) < .15
    if pis: linha(d, cam, [(-30, 950), (180, 950)], OUT, 12)
    else:
        elipse(d, cam, 85, 950, 110, 90, (255, 255, 255), 8)
        ox = {"pipo": 30, "pref": 40}.get(quem, 0)
        elipse(d, cam, 85 + ox, 955, 52, 52, (90, 60, 35), 0); elipse(d, cam, 85 + ox, 955, 26, 26, OUT, 0); elipse(d, cam, 100 + ox, 935, 12, 12, (255, 255, 255), 0)
        linha(d, cam, [(-10, 830), (90, 810), (190, 835)], (70, 40, 25), 14)
    # Pipo e prefeito em escala grande
    B.bicho(d, camchar(cam, 0, 0, 420, 1180, 4.2), 0, 0, t, quem == "pipo", 1)
    prefeito(d, camchar(cam, 0, 0, 800, 1200, 3.4), 0, 0, t, quem == "pref")

OLHO = None
def cena_pote(img_rua, t0, t, quem):
    # zoom-out: a rua inteira está dentro de um pote no quarto de uma criança gigante
    k = lerp(1.0, .42, (t - t0) / 1.6)
    quarto = Image.new("RGB", (W * SS, H * SS), (160, 190, 230))
    d = ImageDraw.Draw(quarto); c = Cam(W / 2, H / 2, 1)
    for i in range(0, 1100, 90): linha(d, c, [(i, 0), (i, 1300)], (150, 180, 222), 30)     # papel de parede listrado
    ret(d, c, -50, 1300, 1200, 700, (170, 115, 70), 0, 0); linha(d, c, [(-50, 1300), (1200, 1300)], (120, 80, 45), 14)  # mesa
    pw, ph = int(W * SS * k), int(H * SS * k)
    cena = img_rua.resize((pw, ph))
    px, py = (W * SS - pw) // 2, int(1300 * SS - ph * .97)
    quarto.paste(cena, (px, py))
    d = ImageDraw.Draw(quarto)
    d.rounded_rectangle([px - 8, py - 8, px + pw + 8, py + ph + 8], radius=int(60 * k * SS), outline=(230, 245, 255), width=int(14 * SS))
    d.rectangle([px + int(pw * .06), py + int(ph * .05), px + int(pw * .1), py + int(ph * .6)], fill=(245, 250, 255))  # reflexo do vidro
    d.rounded_rectangle([px - 30, py - 70 * SS * k * 2, px + pw + 30, py - 4], radius=int(20 * SS), fill=(200, 60, 60), outline=OUT, width=int(8 * SS))  # tampa
    if t - t0 > 1.0:  # a menina gigante aparece por trás do pote
        ap = min(1, (t - t0 - 1.0) / .7)
        PELE, CAB = (255, 205, 165), (120, 65, 35)
        fx, fy = 540, lerp(-450, 130, ap)
        # maria-chiquinhas
        for s in (-1, 1):
            elipse(d, c, fx + s * 330, fy - 40, 90, 150, CAB, 9)
            elipse(d, c, fx + s * 265, fy - 120, 28, 28, (240, 80, 120), 6)
        elipse(d, c, fx, fy, 300, 280, PELE, 10)                                  # rosto
        poli(d, c, [(fx - 300, fy - 30), (fx - 260, fy - 220), (fx, fy - 300), (fx + 260, fy - 220), (fx + 300, fy - 30),
                    (fx + 200, fy - 150), (fx + 60, fy - 120), (fx - 90, fy - 170), (fx - 220, fy - 120)], CAB, 9)  # franja
        pis = (t % 2.9) < .13
        for s in (-1, 1):
            ex = fx + s * 115
            if pis: linha(d, c, [(ex - 60, fy + 10), (ex + 60, fy + 10)], OUT, 12)
            else:
                elipse(d, c, ex, fy + 5, 70, 80, (255, 255, 255), 9)
                elipse(d, c, ex - 10, fy + 25, 38, 42, (60, 140, 90), 0); elipse(d, c, ex - 10, fy + 27, 20, 22, OUT, 0)
                elipse(d, c, ex + 2, fy + 8, 11, 11, (255, 255, 255), 0)
            elipse(d, c, fx + s * 200, fy + 110, 42, 24, (255, 160, 150), 0)    # bochechas
        if quem == "giga":
            ab = 25 + abs(math.sin(t * 16)) * 45
            elipse(d, c, fx, fy + 150, 75, ab, (120, 30, 40), 9); elipse(d, c, fx, fy + 150 + ab * .45, 40, ab * .35, (230, 100, 110), 0)
        else:
            linha(d, c, [(fx - 90, fy + 140), (fx, fy + 185), (fx + 90, fy + 140)], OUT, 12)   # sorrisão
        # mãos segurando o pote
        for s in (-1, 1):
            hx = 540 + s * (pw / SS / 2 + 30)
            elipse(d, c, hx, 1000, 75, 105, PELE, 9)
            for k2 in range(3): linha(d, c, [(hx - s * 40, 950 + k2 * 40), (hx - s * 75, 950 + k2 * 40)], (230, 170, 135), 8)
    return quarto

def main():
    info = asyncio.run(gravar())
    tl, t0 = [], .4
    for i, (f, dur) in enumerate(info):
        if i > 0 and ROT[i][0] != ROT[i - 1][0]: t0 += .5
        if ROT[i][0] == "pote" and ROT[i - 1][0] != "pote": t0 += 1.6
        tl.append((t0, dur)); t0 += dur + .3
    t_fim = t0 + .6; total = t_fim + 1.8
    ini_cena = {c: next(a for (a, _), r in zip(tl, ROT) if r[0] == c) for c in ("dentro", "pote")}
    ini_cena["pote"] -= 1.6
    proc = subprocess.Popen([FF, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                             "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "medium",
                             os.path.join(SAIDA, "ep_mudo.mp4")], stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    for n in range(int(total * FPS)):
        t = n / FPS
        fi = next((i for i, (a, dd) in enumerate(tl) if a <= t < a + dd), None)
        quem = ROT[fi][1] if fi is not None else None
        if t < ini_cena["dentro"]:
            img = B.ceu(); cena_rua(img, t, tl, fi, quem)
        elif t < ini_cena["pote"]:
            img = Image.new("RGB", (W * SS, H * SS)); cena_dentro(img, t, tl, quem)
        else:
            rua = B.ceu(); dr = ImageDraw.Draw(rua); cam = Cam(600, 1050, 1.0)
            B.cenario(dr, cam, t); px, py = B.arvore(dr, cam, t, True); B.bicho(dr, cam, px, py, t, False, 1)
            B.lucas(dr, cam, 560, 1120, t, quem == "lucas", 1, True, False)
            img = cena_pote(rua, ini_cena["pote"], t, quem)
        if fi is not None: B.legenda(img, ROT[fi][2])
        if t > t_fim:  # cartela final
            dd = ImageDraw.Draw(img)
            tx = "CONTINUA..."; w = dd.textlength(tx, font=B.FONTE)
            dd.text(((W * SS - w) / 2, 860 * SS), tx, font=B.FONTE, fill=(255, 230, 90), stroke_width=8 * SS, stroke_fill=(0, 0, 0))
        img = img.resize((W, H), Image.LANCZOS)
        proc.stdin.write(img.tobytes())
    proc.stdin.close(); proc.wait()
    args, filt = [FF, "-y", "-i", os.path.join(SAIDA, "ep_mudo.mp4")], []
    for i, ((f, _), (a, _)) in enumerate(zip(info, tl)):
        args += ["-i", f]; filt.append(f"[{i+1}]adelay={int(a*1000)}|{int(a*1000)}[a{i}]")
    filt.append("".join(f"[a{i}]" for i in range(len(info))) + f"amix=inputs={len(info)}:normalize=0[aud]")
    final = os.path.join(SAIDA, "ep01_mundo_secreto.mp4")
    subprocess.run(args + ["-filter_complex", ";".join(filt), "-map", "0:v", "-map", "[aud]", "-c:v", "copy", "-c:a", "aac", final], check=True, stderr=subprocess.DEVNULL)
    print(json.dumps({"arquivo": final, "duracao": round(total, 1)}))

if __name__ == "__main__":
    main()






