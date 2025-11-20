import requests
from bs4 import BeautifulSoup

def search_kleinanzeigen(query):
    # Преобразуем поисковый запрос в URL-friendly формат
    query_encoded = query.replace(" ", "+")
    url = f"https://m.kleinanzeigen.de/s-suchanfrage.html?keywords={query_encoded}"

    print("Parser URL:", url)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    response = requests.get(url, headers=headers)

    print("Status code:", response.status_code)
    print("Response length:", len(response.text))

    soup = BeautifulSoup(response.text, "lxml")

    results = []

    items = soup.find_all("article")

    print("Found items:", len(items))

    for item in items[:5]:
        title = item.find("h2")
        price = item.find("p", attrs={"class": "aditem-main--middle--price"})
        link = item.find("a")

        results.append({
            "title": title.text.strip() if title else "",
            "price": price.text.strip() if price else "",
            "link": "https://www.kleinanzeigen.de" + link["href"] if link else "",
            "description": ""
        })

    return results
