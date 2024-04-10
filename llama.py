import requests
import re
import json

def ask_llama(messages):
    api_url = "http://localhost:11434/api/generate"
    body = {
        'model': 'llama2-uncensored',
        'messages': messages
    }

    response = requests.post(api_url, json=body)
    if response.status_code != 200:
        raise Exception("error generating wizard response.")
    text = response.text
    str_list = re.findall(r'{.+"done":false}', text)
    res_list = [json.loads(x)['response'] for x in str_list]
    concat_response = ''.join(res_list)
    return concat_response