from openai import OpenAI
def requete(prompt : str):
   
    client = OpenAI(base_url="http://127.0.0.1:1234/v1", api_key="lm-studio")

    completion = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": prompt}]
        )


    response = completion.choices[0].message.content
    return response