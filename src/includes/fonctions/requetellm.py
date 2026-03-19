# pip install openai>=1.40
from openai import OpenAI
from groq import Groq
"""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"""
def requete(prompt):
    """Cette fonction permet de faire des appelles à LM Studio elle est actuelle setter pour faire des requêtes chez Pascal :)"""
    client = OpenAI(
        base_url="http://100.103.185.35:5000/v1",  # port par défaut LM Studio
        api_key="lm-studio"                   # n'importe quelle chaîne non vide
    )
    
    resp = client.chat.completions.create(
        model="Qwen3-30B-A3B-exl2",               # exactement comme affiché dans LM Studio
        messages=[
            {"role": "user", "content": prompt}
        ],
        
        timeout = None
    )

    return resp.choices[0].message.content


import os
from openai import OpenAI

def requetopenrouter(prompt):
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY n'est pas défini dans les variables d'environnement.")

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key="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",
        timeout=60,
        default_headers={
            "HTTP-Referer": "http://127.0.0.1:5000",
            "X-Title": "llmethique"
        }
    )

    completion = client.chat.completions.create(
        model="meta-llama/llama-3.1-8b-instruct",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return completion.choices[0].message.content




def requetGrok(prompt):
    """Permet de faire des appelles à Grok avec le modèle 8B (fallback)"""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY n'est pas défini dans les variables d'environnement.")

    client = Groq(api_key=api_key)
    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return completion.choices[0].message.content


def requetGrok405B(prompt, max_retries=2):
    """
    Permet de faire des appels a Groq avec Llama 4 Scout (30k contexte).
    Avec retry automatique et fallback sur le 8B si Scout echoue.
    """
    import time
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY n'est pas defini dans les variables d'environnement.")

    client = Groq(api_key=api_key)
    
    # Alerte si contexte est trop volumineux
    token_estimate = len(prompt) // 4  # Approximation: 4 chars ≈ 1 token
    if token_estimate > 28000:
        print(f"Contexte proche de la limite (~{token_estimate} tokens sur 30k max).")
    
    for attempt in range(max_retries):
        try:
            completion = client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                timeout=120
            )
            print(f"Succes avec llama-4-scout (attempt {attempt + 1})")
            return completion.choices[0].message.content
            
        except Exception as e:
            error_msg = str(e)
            print(f"Tentative {attempt + 1}/{max_retries} echouee (Scout): {error_msg}")
            
            # Rate limit: attendre avant retry
            if "429" in error_msg or "rate_limit" in error_msg:
                wait_time = (2 ** attempt) * 5  # 5s, 10s, 20s...
                print(f"Rate limit detecte. Attente {wait_time}s avant retry...")
                time.sleep(wait_time)
                continue
            
            # Erreur authentification: fail immediat
            if "401" in error_msg or "403" in error_msg:
                print(f"Erreur d'authentification (Scout): {error_msg}")
                break
            
            # Autre erreur: retry
            if attempt < max_retries - 1:
                time.sleep(5)
                continue
    
    # Fallback sur le 8B
    print("\nFallback sur llama-3.1-8b-instant...")
    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        print("Succes avec llama-3.1-8b-instant (fallback)")
        return completion.choices[0].message.content
    except Exception as e:
        print(f"Fallback echoue: {e}")
        raise