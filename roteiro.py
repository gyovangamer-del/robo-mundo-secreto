# Escreve sozinho o roteiro do próximo episódio da série, com a IA (Gemini/Claude do servidor antigo).
import json, os, sys
import ia as servidor  # escrever_roteiro(prompt) -> dict (Gemini)
from motor import LUGARES, VOZES

BIBLIA = """SÉRIE DE ANIMAÇÃO 2D: "O Menino que Encontrou um Mundo Secreto" (vídeos verticais de ~60 s pro Instagram e YouTube Shorts).
Público: crianças, adolescentes e famílias. Tom: humor + mistério + reviravoltas. Português do Brasil natural, frases curtas.

PERSONAGENS (use só estes, pelo código entre parênteses):
- (lucas) Lucas, 11 anos, curioso, um pouco medroso, faz piadas quando fica nervoso.
- (pipo) Pipo, bichinho azul minúsculo de Miudópolis, folgado, rápido, sempre exagera, amigo do Lucas.
- (prefeito) Prefeito de Miudópolis, um caracol velho de cartola e monóculo, formal e desconfiado.
- (tonho) Seu Tonho, morador que vive dormindo e às vezes acorda falando coisas sábias ou sem sentido.
- (nina) Nina, menina GIGANTE. A rua do Lucas inteira fica dentro de um pote no quarto dela (segredo revelado no Ep01).
- (mae) Mãe da Nina, só a voz, fora de cena.

LUGARES (use só estes códigos):
- rua: a calçada do Lucas com a árvore da portinha. Os bichinhos aparecem pequenininhos na porta.
- miudopolis: dentro da árvore, a cidade minúscula (casas de cogumelo, lanternas). O Lucas aparece só como um olho gigante espiando pela porta.
- casa_lucas: o quarto do Lucas. Os bichinhos podem visitar e ficam em cima da escrivaninha.
- quarto_gigante: o quarto da Nina; a câmera mostra o pote com a rua dentro e o rosto dela por cima. Use pra revelações.

RESUMO DO EP01: Lucas achou uma portinha numa árvore, conheceu o Pipo e o Prefeito em Miudópolis. O Prefeito disse "nunca conte que a gente existe, porque eles também nunca contaram que vocês existem". Revelação: o mundo do Lucas está dentro de um pote no quarto da Nina, uma menina gigante. A mãe dela disse "fecha a tampa que tá entrando vento".
"""

FORMATO = """Responda SÓ com um JSON válido, sem texto fora dele, neste formato:
{"titulo": "título curto e curioso, até 60 caracteres, terminando com EpNN",
 "descricao": "2 frases que dão vontade de assistir + pergunta pros comentários + 5 hashtags",
 "resumo": "resumo do que aconteceu neste episódio em 2 frases (pra memória da série)",
 "cenas": [{"lugar": "codigo", "falas": [{"quem": "codigo", "texto": "fala"}]}]}
Regras: 2 a 4 cenas; 12 a 17 falas no total; cada fala até 90 caracteres; total de texto falado até 850 caracteres
(o vídeo tem que dar ~60 s). Comece com um gancho forte na 1ª fala. Tenha pelo menos uma piada e uma reviravolta.
Termine num suspense que faça querer o próximo episódio. Nada de violência, terror pesado ou palavrão.
História ORIGINAL: não copie desenhos, filmes ou vídeos existentes."""


def escrever(numero, historico):
    passado = "\n".join(f"- Ep{h['numero']:02d}: {h['resumo']}" for h in historico[-8:]) or "- (só o Ep01)"
    prompt = (f"{BIBLIA}\nEPISÓDIOS ANTERIORES:\n{passado}\n\nEscreva o roteiro do Ep{numero:02d}, continuando direto de onde o último parou. "
              f"Avance a história (novo mistério, personagem descobrindo algo, uma consequência), sem repetir piadas.\n\n{FORMATO}")
    for tentativa in range(3):
        r = servidor.escrever_roteiro(prompt)
        try:
            return validar(r, numero)
        except ValueError as e:
            prompt += f"\n\nATENÇÃO: a resposta anterior veio errada ({e}). Siga o formato à risca."
    raise RuntimeError("a IA não conseguiu escrever um roteiro válido")


def validar(r, numero):
    if not isinstance(r, dict) or not r.get("cenas"): raise ValueError("sem cenas")
    cenas = []
    for c in r["cenas"][:4]:
        if c.get("lugar") not in LUGARES: raise ValueError(f"lugar inválido {c.get('lugar')}")
        falas = [{"quem": f["quem"], "texto": str(f["texto"]).strip()[:120]} for f in c.get("falas", [])
                 if f.get("quem") in VOZES and str(f.get("texto", "")).strip()]
        if falas: cenas.append({"lugar": c["lugar"], "falas": falas})
    total = sum(len(f["texto"]) for c in cenas for f in c["falas"])
    n = sum(len(c["falas"]) for c in cenas)
    if n < 8: raise ValueError("falas de menos")
    if total > 1100: raise ValueError(f"texto longo demais ({total} caracteres, máximo 850)")
    titulo = str(r.get("titulo") or f"Miudópolis Ep{numero:02d}")[:90]
    if f"Ep{numero:02d}".lower() not in titulo.lower(): titulo = f"{titulo} Ep{numero:02d}"
    return {"titulo": titulo, "descricao": str(r.get("descricao", ""))[:1500], "resumo": str(r.get("resumo", ""))[:400],
            "cenas": cenas, "caracteres": total}


if __name__ == "__main__":
    print(json.dumps(escrever(2, []), ensure_ascii=False, indent=1))

