# pip install openai>=1.40
from openai import OpenAI
from groq import Groq

def requete(prompt):
    client = OpenAI(
        base_url="http://localhost:1234/v1",  # port par défaut LM Studio
        api_key="lm-studio"                   # n'importe quelle chaîne non vide
    )

    resp = client.chat.completions.create(
        model="openai/gpt-oss-20b",               # exactement comme affiché dans LM Studio
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=300,
        timeout=200000
    )

    return resp.choices[0].message.content



def requetGroq(prompt):

    client = Groq(api_key="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")
    completion = client.chat.completions.create(
        
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return completion.choices[0].message.content