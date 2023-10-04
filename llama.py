import requests
import re
import json

def ask_llama(prompt):
    api_url = "http://localhost:11434/api/generate"
    body = {
        'model': 'llama2-uncensored',
        'prompt': prompt
    }

    response = requests.post(api_url, json=body)
    text = response.text
    str_list = re.findall(r'{.+"done":false}', text)
    res_list = [json.loads(x)['response'] for x in str_list]
    concat_response = ''.join(res_list)
    print(concat_response)
    return concat_response