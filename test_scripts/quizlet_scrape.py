import requests
from bs4 import BeautifulSoup

headers = {
  'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
  'accept-encoding': 'gzip, deflate, br',
  'accept-language': 'en-US,en;q=0.9',
  'cache-control': 'max-age=0',
  'cookie': 'yourcookie',
  'sec-fetch-mode': 'navigate',
  'sec-fetch-site': 'none',
  'sec-fetch-user': '?1',
  'upgrade-insecure-requests': '1',
  'user-agent': 'Mozilla/5.0 (X11; CrOS x86_64 12239.92.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.136 Safari/537.36',
}

# The URL of the Quizlet set you want to scrape
quizlet_url = "https://quizlet.com/kr/932705417/%EC%84%B8%EC%A2%85%ED%95%99%EB%8B%B9-%ED%95%9C%EA%B5%AD%EC%96%B4-2-7%EA%B3%BC-flash-cards/?funnelUUID=720a1cde-6d66-4009-aa56-9451a72a1adb"  # Replace with the actual URL

# Send a GET request to fetch the page content
response = requests.get(quizlet_url, headers=headers)

text = response.text

print(text)

# Check if the request was successful
if response.status_code == 200:
    # Parse the page content with BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find the section that contains the terms
    terms_section = soup.find('section', class_='SetPageTerms-termsList')
    
    # Check if the section exists
    if terms_section:
        # Find all div elements with the class 'SetPageTerms-term'
        terms = terms_section.find_all('div', class_='SetPageTerms-term')
        
        # Loop through the terms and extract the term and definition
        for term in terms:
            # Find the text for the term and definition, both in the 'TermText' class
            term_definitions = term.find_all('div', class_='TermText')
            
            # Check if there are at least two 'TermText' elements (term and definition)
            if len(term_definitions) >= 2:
                term_name = term_definitions[0].get_text(strip=True)  # First is the term
                definition = term_definitions[1].get_text(strip=True)  # Second is the definition
                
                # Print the term and definition
                print(f"Term: {term_name}")
                print(f"Definition: {definition}")
                print('-' * 40)
    else:
        print("Terms section not found!")
else:
    print(f"Failed to retrieve the page. Status code: {response.status_code}")
