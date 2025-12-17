# pip install openai>=1.40
from openai import OpenAI
from groq import Groq
"""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"""
def requete(prompt):
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


def requetopenrouter(prompt):
    client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="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",
    )

    completion = client.chat.completions.create(
    extra_body={},
    model="openai/gpt-oss-20b:free",

    messages=[
        {
        "role": "user",
        "content": prompt
        }
    ]
    )
    return completion.choices[0].message.content


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