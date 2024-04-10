import requests
import re
import json

def ask_llama(messages):
    api_url = "http://localhost:11434/api/generate"
    prompt = '\n\n'.join([f"{part['role']}: {part['content']}" for part in messages])
    body = {
        'model': 'llama2-uncensored',
        'prompt': prompt + '\n\nassistant:',
        'stream': False
    }

    response = requests.post(api_url, json=body)
    if response.status_code != 200:
        raise Exception("error generating wizard response.")
    text = response.text
    json_res = json.loads(text)
    return json_res['response']