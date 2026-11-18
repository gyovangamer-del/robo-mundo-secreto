# Roda na nuvem (GitHub Actions): faz 1 episódio novo e posta no YouTube. O estado da série fica em estado.json (no repositório).
# Segredos (variáveis de ambiente): GEMINI_API_KEY, ELEVENLABS_API_KEY, YOUTUBE_TOKEN_JSON.
import json, os, sys, datetime as dt
AQUI = os.path.dirname(os.path.abspath(__file__)); os.chdir(AQUI); sys.path.insert(0, AQUI)
import roteiro, motor, eleven

ESTADO = os.path.join(AQUI, "estado.json")
POSTAR = os.environ.get("POSTAR_YOUTUBE", "sim") == "sim"


def ler():
    with open(ESTADO, encoding="utf-8") as f: return json.load(f)


def salvar(e):
    with open(ESTADO, "w", encoding="utf-8") as f: json.dump(e, f, ensure_ascii=False, indent=1)


def youtube_postar(video, ep):
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    cred = Credentials.from_authorized_user_info(json.loads(os.environ["YOUTUBE_TOKEN_JSON"].strip().lstrip("\ufeff")))
    if not cred.valid: cred.refresh(Request())
    yt = build("youtube", "v3", credentials=cred, cache_discovery=False)
    desc = (ep.get("descricao") or ep["titulo"])
    if "#shorts" not in desc.lower(): desc += " #shorts"
    corpo = {"snippet": {"title": ep["titulo"][:100], "description": desc[:4900], "categoryId": "1",
                         "tags": ["animação", "desenho animado", "história", "mistério", "mundo secreto", "cartoon"],
                         "defaultLanguage": "pt-BR", "defaultAudioLanguage": "pt-BR"},
             "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False, "containsSyntheticMedia": True}}
    envio = yt.videos().insert(part="snippet,status", body=corpo,
                               media_body=MediaFileUpload(video, mimetype="video/mp4", chunksize=8 << 20, resumable=True))
    resp = None
    while resp is None: _, resp = envio.next_chunk()
    return "https://youtube.com/shorts/" + resp["id"]


def main():
    e = ler()
    n = max(x["numero"] for x in e["episodios"]) + 1
    print(f"Escrevendo o roteiro do Ep{n:02d}…", flush=True)
    ep = roteiro.escrever(n, e["episodios"])
    print(f"Roteiro: {ep['titulo']} ({ep['caracteres']} caracteres)", flush=True)
    os.makedirs("videos", exist_ok=True)
    video = os.path.join("videos", f"ep{n:02d}.mp4")
    dur = motor.renderizar(ep, video)
    print(f"Vídeo pronto: {dur}s", flush=True)
    reg = {"numero": n, "titulo": ep["titulo"], "resumo": ep["resumo"], "duracao": dur,
           "quando": dt.datetime.now(dt.timezone(dt.timedelta(hours=-3))).isoformat(timespec="minutes")}
    if POSTAR:
        reg["youtube"] = youtube_postar(video, ep)
        print("Postado no YouTube:", reg["youtube"], flush=True)
    if POSTAR: e["episodios"].append(reg)  # teste (sem postar) não entra na memória da série
    try: e["eleven"] = eleven.conta()
    except Exception: pass
    salvar(e)
    with open(os.environ.get("GITHUB_STEP_SUMMARY", os.devnull), "a", encoding="utf-8") as s:
        s.write(f"## Ep{n:02d}: {ep['titulo']}\n\n{ep['resumo']}\n\n- Duração: {dur}s\n- YouTube: {reg.get('youtube', 'não postado')}\n"
                f"- Créditos ElevenLabs: {e.get('eleven')}\n")


if __name__ == "__main__":
    main()


