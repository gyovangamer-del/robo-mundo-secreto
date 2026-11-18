# Motor do robô 2D: transforma um roteiro (JSON) em vídeo 9:16 1080p com vozes, legenda e câmera.
# Roteiro: {"cenas": [{"lugar": "rua|miudopolis|quarto_gigante|casa_lucas", "falas": [{"quem": "...", "texto": "..."}]}]}
import asyncio, math, os, subprocess, hashlib
from PIL import Image, ImageDraw, ImageFont
import edge_tts
import cena_teste as B
import episodio as E
import eleven
from cena_teste import Cam, elipse, poli, ret, linha, lerp, W, H, SS, FPS, OUT, FF, FP, SAIDA

LUGARES = ("rua", "miudopolis", "quarto_gigante", "casa_lucas")
VOZES = {  # (voz grátis, velocidade, tom, voz ElevenLabs)
    "lucas": E.LUCAS, "pipo": E.PIPO, "prefeito": E.PREF, "nina": E.GIGA, "mae": E.MAE,
    "tonho": ("pt-BR-AntonioNeural", "-12%", "-12Hz", "N2lVS1w4EtoT3dr4eOWO"),
}
PEQUENOS = ("pipo", "prefeito", "tonho")
FONTE1 = B.fonte(60)
ID = Cam(W / 2, H / 2, 1)


def em(sx, sy, k):  # câmera pra desenhar um personagem (origem 0,0) no ponto da tela sx,sy com escala k
    return E.camchar(ID, 0, 0, sx, sy, k)


def tonho(d, c, t, fala):
    b = math.sin(t * 1.5) * 1.5
    elipse(d, c, 0, 8 + b, 24, 18, (200, 170, 230), 3)
    for s in (-1, 1):
        if fala: elipse(d, c, s * 9, 2 + b, 4, 3, (255, 255, 255), 2); elipse(d, c, s * 9, 3 + b, 1.8, 1.5, OUT, 0)
        else: linha(d, c, [(s * 9 - 5, 3 + b), (s * 9 + 5, 3 + b)], OUT, 2.5)
    if fala: elipse(d, c, 0, 14 + b, 4, 1.5 + abs(math.sin(t * 20)) * 3, (120, 30, 40), 2)
    elipse(d, c, -2, -10 + b, 14, 5, (90, 90, 160), 2)  # touquinha de dormir


def pequeno(nome, d, c, t, fala):
    if nome == "pipo": B.bicho(d, c, 0, 0, t, fala, 1)
    elif nome == "prefeito": E.prefeito(d, c, 0, 0, t, fala)
    else: tonho(d, c, t, fala)


def olho_na_porta(d, t, quem):
    c = ID
    elipse(d, c, 60, 950, 210, 300, (255, 225, 170), 10)
    elipse(d, c, 75, 950, 150, 150, (255, 205, 165), 0)
    if (t % 3.7) < .15: linha(d, c, [(-30, 950), (180, 950)], OUT, 12); return
    elipse(d, c, 85, 950, 110, 90, (255, 255, 255), 8)
    ox = 35 if quem in PEQUENOS else 0
    elipse(d, c, 85 + ox, 955, 52, 52, (90, 60, 35), 0); elipse(d, c, 85 + ox, 955, 26, 26, OUT, 0)
    elipse(d, c, 100 + ox, 935, 12, 12, (255, 255, 255), 0)
    linha(d, c, [(-10, 830), (90, 810), (190, 835)], (70, 40, 25), 14)


def casa_fundo(d, t):
    c = ID
    ret(d, c, -50, -50, 1200, 1400, (250, 225, 185), 0, 0)
    for i in range(0, 1100, 120): linha(d, c, [(i, 0), (i, 1300)], (240, 212, 170), 26)
    ret(d, c, 560, 330, 380, 330, (150, 205, 245), 20, 8)                       # janela
    elipse(d, c, 860, 420, 45, 45, (255, 236, 150), 0)
    linha(d, c, [(750, 330), (750, 660)], (255, 255, 255), 10); linha(d, c, [(560, 495), (940, 495)], (255, 255, 255), 10)
    ret(d, c, 520, 640, 460, 30, (200, 140, 90), 8, 5)                          # parapeito
    ret(d, c, -50, 1300, 1200, 700, (180, 120, 80), 0, 0)
    for i in range(-1, 12): linha(d, c, [(i * 110, 1300), (i * 110 - 60, 1920)], (160, 105, 70), 5)
    ret(d, c, 620, 1060, 420, 40, (150, 95, 60), 10, 6)                         # escrivaninha
    for x in (650, 990): ret(d, c, x, 1095, 24, 210, (130, 80, 50), 6, 5)
    ret(d, c, 700, 960, 90, 100, (90, 160, 220), 10, 5)                          # livros
    ret(d, c, 795, 990, 70, 70, (240, 110, 90), 10, 5)
    ret(d, c, -40, 1150, 300, 160, (90, 120, 200), 30, 6)                        # cama
    ret(d, c, -40, 1120, 150, 70, (255, 255, 255), 25, 5)


def desenhar(lugar, t, quem, presentes, t_cena):
    """Desenha um quadro (tamanho SS). Devolve (imagem, ponto de foco na tela ou None)."""
    pequenos = [p for p in PEQUENOS if p in presentes]  # ordem fixa: cada um sempre no mesmo lugar
    foco = None
    if lugar == "rua" or lugar == "quarto_gigante":
        img = B.ceu(); d = ImageDraw.Draw(img)
        B.cenario(d, ID, t)
        px, py = B.arvore(d, ID, t, bool(pequenos))
        for i, p in enumerate(pequenos[:3]):
            sx = px + [0, 55, -55][i]
            pequeno(p, d, em(sx, py, 1), t, quem == p)
            if quem == p: foco = (sx, py - 120)
        if "lucas" in presentes or lugar == "quarto_gigante":
            B.lucas(d, ID, 380, 1120, t, quem == "lucas", 1, lugar == "quarto_gigante", False)
            if quem == "lucas": foco = (420, 1000)
        if lugar == "quarto_gigante":
            fala_nina = "giga" if quem == "nina" else quem
            return E.cena_pote(img, t_cena, t, fala_nina), None
        return img, foco
    img = Image.new("RGB", (W * SS, H * SS)); d = ImageDraw.Draw(img)
    if lugar == "miudopolis":
        E.fundo_dentro(d, ID, t)
        for i in range(8):
            cx = [90, 180, 560, 610, 1010, 1060, 250, 960][i]
            E.criaturinha(d, em(cx, 1282, 2.0), 0, 0, t, [(255, 200, 90), (150, 230, 160), (240, 140, 200), (140, 200, 255)][i % 4], i)
        if "tonho" not in pequenos:  # Seu Tonho dorme em cima do cogumelo
            tonho(d, em(130, 1070, 1.6), t, False)
        vagas = [(420, 1180, 4.2), (790, 1200, 3.4), (620, 1240, 3.4)]
        for p in pequenos:
            sx, sy, k = vagas[PEQUENOS.index(p)]
            pequeno(p, d, em(sx, sy, k), t, quem == p)
            if quem == p: foco = (sx, sy - 60)
        if "lucas" in presentes or True:
            olho_na_porta(d, t, quem)
            if quem == "lucas": foco = (300, 1000)
    else:  # casa_lucas
        casa_fundo(d, t)
        B.lucas(d, ID, 330, 1120, t, quem == "lucas", 1, False, False)
        if quem == "lucas": foco = (380, 1000)
        lugares = {"pipo": (690, 1035, 2.6), "prefeito": (905, 1035, 2.4), "tonho": (110, 1118, 2.6)}
        for p in pequenos:
            sx, sy, k = lugares[p]
            pequeno(p, d, em(sx, sy, k), t, quem == p)
            if quem == p: foco = (sx, sy - 60)
    return img, foco


def legenda(img, txt, quem):
    d = ImageDraw.Draw(img)
    linhas, l = [], ""
    for p in txt.split():
        if d.textlength(l + " " + p, font=FONTE1) > W - 160 and l: linhas.append(l); l = p
        else: l = (l + " " + p).strip()
    linhas.append(l)
    y = 1500
    cor = {"lucas": (255, 255, 255), "pipo": (170, 220, 255), "prefeito": (190, 240, 170), "nina": (255, 200, 220),
           "mae": (255, 220, 160), "tonho": (220, 200, 255)}.get(quem, (255, 255, 255))
    for ln in linhas:
        w = d.textlength(ln, font=FONTE1)
        d.text(((W - w) / 2, y), ln, font=FONTE1, fill=cor, stroke_width=7, stroke_fill=(0, 0, 0)); y += 78


def zoom(img, foco, z):
    if not foco or z <= 1.001: return img.resize((W, H), Image.LANCZOS)
    cw, ch = W * SS / z, H * SS / z
    fx, fy = foco[0] * SS, foco[1] * SS
    x0 = min(max(fx - cw / 2, 0), W * SS - cw); y0 = min(max(fy - ch * .45, 0), H * SS - ch)
    return img.resize((W, H), Image.LANCZOS, box=(x0, y0, x0 + cw, y0 + ch))


async def _gravar(falas):
    out = []
    for quem, txt in falas:
        v, r, p, eid = VOZES.get(quem, VOZES["lucas"])
        f = os.path.join(SAIDA, "ep_" + hashlib.sha1((txt + eid).encode()).hexdigest()[:12] + ".mp3")
        if not (os.path.exists(f) and os.path.getsize(f) > 1000):
            try: eleven.falar(txt, eid, f)
            except Exception as e:
                print("ElevenLabs falhou, usando voz grátis:", type(e).__name__, flush=True)
                await edge_tts.Communicate(txt, v, rate=r, pitch=p).save(f)
        d = float(subprocess.check_output([FP, "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", f]).decode())
        out.append((f, d))
    return out


def renderizar(roteiro, destino, cartela="CONTINUA..."):
    falas, cena_de = [], []
    for ci, cena in enumerate(roteiro["cenas"]):
        for f in cena["falas"]:
            falas.append((f["quem"], f["texto"])); cena_de.append(ci)
    audio = asyncio.run(_gravar(falas))
    tl, t0, ini_cena = [], .4, {}
    for i, (_, dur) in enumerate(audio):
        ci = cena_de[i]
        if ci not in ini_cena:
            if i > 0: t0 += .5
            if roteiro["cenas"][ci]["lugar"] == "quarto_gigante": ini_cena[ci] = t0; t0 += 1.6
            else: ini_cena[ci] = t0 - .4 if i == 0 else t0
        tl.append((t0, dur)); t0 += dur + .3
    t_fim = t0 + .6; total = t_fim + 1.8
    presentes = [{f["quem"] for f in c["falas"]} for c in roteiro["cenas"]]
    mudo = destino + ".mudo.mp4"
    proc = subprocess.Popen([FF, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                             "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "medium", mudo],
                            stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    z = 1.0
    for n in range(int(total * FPS)):
        t = n / FPS
        fi = next((i for i, (a, dd) in enumerate(tl) if a <= t < a + dd), None)
        ci = max([c for c, a in ini_cena.items() if a <= t] or [0])
        quem = falas[fi][0] if fi is not None else None
        lugar = roteiro["cenas"][ci]["lugar"]
        img, foco = desenhar(lugar, t, quem, presentes[ci], ini_cena[ci])
        z += ((1.22 if foco else 1.0) - z) * .08
        if lugar == "quarto_gigante": z = 1.0
        quadro = zoom(img, foco or (W / 2, H / 2), z)
        if fi is not None: legenda(quadro, falas[fi][1], quem)
        if t > t_fim:
            d = ImageDraw.Draw(quadro); w = d.textlength(cartela, font=FONTE1)
            d.text(((W - w) / 2, 860), cartela, font=FONTE1, fill=(255, 230, 90), stroke_width=8, stroke_fill=(0, 0, 0))
        proc.stdin.write(quadro.tobytes())
    proc.stdin.close(); proc.wait()
    args, filt = [FF, "-y", "-i", mudo], []
    for i, ((f, _), (a, _)) in enumerate(zip(audio, tl)):
        args += ["-i", f]; filt.append(f"[{i+1}]adelay={int(a*1000)}|{int(a*1000)}[a{i}]")
    filt.append("".join(f"[a{i}]" for i in range(len(audio))) + f"amix=inputs={len(audio)}:normalize=0[aud]")
    subprocess.run(args + ["-filter_complex", ";".join(filt), "-map", "0:v", "-map", "[aud]", "-c:v", "copy", "-c:a", "aac", destino],
                   check=True, stderr=subprocess.DEVNULL)
    os.remove(mudo)
    return round(total, 1)



