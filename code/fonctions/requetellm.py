from groq import Groq 
def requete(prompt : str):
    key = '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'

    client = Groq(
        api_key=key,
    )
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }

        ],
        model="llama-3.1-8b-instant",

    )

    response = chat_completion.choices[0].message.content
    return response