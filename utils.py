import requests

def download_from_url(url, filename):
    headers={'user-agent': 'Mozilla/5.0'}
    r=requests.get(url, headers=headers)
    with open(filename, 'wb') as f:
        f.write(r.content)