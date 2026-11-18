# IA do roteiro (Gemini). Chave: variável GEMINI_API_KEY (nuvem) ou ~/chave-gemini.txt (PC).
import json, os, re, time, urllib.request, urllib.error


def chave(var, arquivo):
    if os.environ.get(var): return os.environ[var].strip()
    p = os.path.join(os.path.expanduser("~"), arquivo)
    return open(p, encoding="utf-8-sig").read().strip() if os.path.exists(p) else None


MODELOS = ["gemini-flash-latest", "gemini-3.6-flash", "gemini-3.8-flash", "gemini-3.5-flash", "gemini-3-flash-preview",
           "gemini-flash-lite-latest", "gemini-3.5-flash-lite"]


def _json(texto):
    trecho = texto[texto.find("{"): texto.rfind("}") + 1]
    try: return json.loads(trecho)
    except ValueError: return json.loads(re.sub(r",\s*([\]}])", r"\1", trecho))


def _uma(k, modelo, prompt):
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent",
        data=json.dumps({"contents": [{"parts": [{"text": prompt}]}],
                         "generationConfig": {"responseMimeType": "application/json", "temperature": 0.9}}).encode(),
        headers={"x-goog-api-key": k, "content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        resp = json.loads(r.read())
    return _json("".join(p.get("text", "") for p in resp["candidates"][0]["content"]["parts"]))


def escrever_roteiro(prompt):
    k = chave("GEMINI_API_KEY", "chave-gemini.txt")
    if not k: raise RuntimeError("sem chave do Gemini")
    erro = None
    for volta in range(2):
        for m in list(MODELOS):
            try:
                r = _uma(k, m, prompt); MODELOS.remove(m); MODELOS.insert(0, m); return r
            except urllib.error.HTTPError as e:
                if e.code not in (404, 429, 500, 503): raise
                erro = e
            except (TimeoutError, OSError, KeyError, ValueError) as e:
                erro = e
        time.sleep(5)
    raise RuntimeError(f"o Gemini não respondeu: {erro}")
