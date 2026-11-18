# Vozes do ElevenLabs pro robô 2D. Lê a chave de C:\Users\USUARIO\chave-elevenlabs.txt (nunca imprime).
import json, os, sys, urllib.request

CHAVE = (os.environ.get("ELEVENLABS_API_KEY") or open(os.path.join(os.path.expanduser("~"), "chave-elevenlabs.txt"), encoding="utf-8-sig").read()).strip()
API = "https://api.elevenlabs.io"

def _req(path, data=None):
    r = urllib.request.Request(API + path, data=json.dumps(data).encode() if data else None,
                               headers={"xi-api-key": CHAVE, "Content-Type": "application/json"})
    return urllib.request.urlopen(r, timeout=60)

def conta():
    s = json.load(_req("/v1/user/subscription"))
    return {"plano": s.get("tier"), "usado": s.get("character_count"), "limite": s.get("character_limit")}

def vozes():
    return [(v["voice_id"], v["name"], v.get("labels", {})) for v in json.load(_req("/v2/voices?page_size=100"))["voices"]]

def biblioteca_pt(n=40):
    j = json.load(_req(f"/v1/shared-voices?page_size={n}&language=pt&locale=pt-BR"))
    return [(v["voice_id"], v["public_owner_id"], v["name"], v.get("gender"), v.get("age"), v.get("use_case"), v.get("descriptive")) for v in j["voices"]]

def falar(texto, voice_id, arquivo, estab=.45, estilo=.35):
    corpo = {"text": texto, "model_id": "eleven_multilingual_v2",
             "voice_settings": {"stability": estab, "similarity_boost": .8, "style": estilo, "use_speaker_boost": True}}
    with _req(f"/v1/text-to-speech/{voice_id}?output_format=mp3_44100_128", corpo) as r, open(arquivo, "wb") as f:
        f.write(r.read())

if __name__ == "__main__":
    print(json.dumps(conta(), ensure_ascii=False))
    for v in biblioteca_pt(): print(v)

