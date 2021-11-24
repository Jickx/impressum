from bs4 import BeautifulSoup
import requests
import csv
import re

impressum_url_list = []

def read_csv():
    """Open csv file with urls and return url list."""

    url_list = []
    with open('url_list.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                line_count += 1
            else:
                if row == []:
                    url_list.append("")
                else:
                    url_list.append(row[0])
                line_count += 1
    print(f'Read {line_count} lines from file.')
    return(url_list)

def find_imperssum_url(url):
    """Take site url and return impressum url"""
    
    impressum_url = None
    if url == "":
        return ""
    
    try:
        page = requests.get("http://" + url, timeout=10)
    except requests.RequestException:
        print("Connection error")
        return ""    

    url = page.url

    soup = BeautifulSoup(page.text, "html.parser")

    # for php generated
    try:
        php_link = soup.find('meta', {'http-equiv': 'Refresh'}).attrs['content'].split("=", 1)[1]
        if php_link:
            url = url + php_link.split("/",1)[0] + "/"
            url_php = url + php_link.split("/",1)[1]
            try:
                page = requests.get(url_php, timeout=10)
            except requests.RequestException:
                print("Connection error")
                return ""
            soup = BeautifulSoup(page.text, "html.parser")
    except AttributeError:
        pass

    links = soup.findAll('a', href=True)

    print(f"Searching impressum URL in {url}")

    if "impressum" in soup.text.lower():
        for link in links:
            if "impressum" in link.text.lower():
                if link["href"].startswith("http"):
                    impressum_url = link['href']
                    return impressum_url
                else:
                    impressum_url = url + link['href'].lstrip("/")
                    return impressum_url

        if impressum_url == None:
            return url
    else:
        return ""

def write_csv(impressum_url_list):
    """Write impressum url list in file"""

    fieldnames = ['SCRAPE_URL', 'IMPRESSUM_URL', 'EMAIL_URL']

    # old file will be cleared
    with open('impressum_list.csv', 'w+', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(impressum_url_list)

def find_emails(impressum_url):
    """ Finding emails in impressum page """

    if impressum_url == "":
        return ""
    try:
        page = requests.get(impressum_url, timeout=10)
    except requests.RequestException:
        print("Connection error")
        return ""

    soup = BeautifulSoup(page.text, 'html.parser')
    text = soup.get_text(separator=' ')

    email_list = []

    print(f"Searching emails in {impressum_url}")

    for word in text.split():
        keywords = [
            r'[\w.+-]+\[at\][\w-]+\.[\w.-]+', 
            r'[\w.+-]+@[\w-]+\.[\w.-]+',
            r'[\w.+-]+at[\w-]+\.[\w.-]+',
            '_AT_'
            ]

        for keyword in keywords:
            if re.search(keyword, word):
                if word not in email_list:
                    email_list.append(word)
    
    if email_list == []:
        text = soup.find_all("a", href=re.compile(r"^mailto:"))
        for i in range(len(text)):
            word = (text[i]["href"])
            if word not in email_list:
                email_list.append(word.replace("mailto:", ""))
            return email_list[:2]

    return email_list[:2]

# def find_names(impressum_url):
#     try:
#         page = requests.get(impressum_url, timeout=10)
#     except requests.RequestException:
#         print("Connection error")
#         return ""

#     soup = BeautifulSoup(page.text, "html.parser")
    
#     words = soup.get_text(separator=' ').split()
    
#     for tag in soup.find_all():
#         if 'Geschäftsführer' in str(tag):
#             print(tag.text)

url_list = read_csv()
for url in url_list:
    row = {}
    impressum_url = find_imperssum_url(url)
    email_list = find_emails(impressum_url)
    row['SCRAPE_URL'] = url
    row['IMPRESSUM_URL'] = impressum_url
    row['EMAIL_URL'] = email_list

    impressum_url_list.append(row)    
write_csv(impressum_url_list)