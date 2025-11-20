import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import quote

def search_kleinanzeigen(query: str):
    # Превращаем запрос в URL-friendly формат
    q = quote(query)

    url = f"https://www.kleinanzeigen.de/s-suche/{q}/k0"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "de,en;q=0.9",
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return json.dumps({"error": "Failed to load page"})

    soup = BeautifulSoup(response.text, "html.parser")

    items = soup.select("article.aditem")[:5]  # первые 5 результатов

    results = []

    for item in items:
        title_el = item.select_one(".ellipsis")
        price_el = item.select_one(".aditem-main--middle--price-shipping--price")
        desc_el = item.select_one(".aditem-main--middle--description")
        link_el = item.select_one("a")

        title = title_el.get_text(strip=True) if title_el else "Нет заголовка"
        price = price_el.get_text(strip=True) if price_el else "Цена не указана"
        desc = desc_el.get_text(strip=True) if desc_el else "Описание отсутствует"

        # формируем полный URL
        link = (
            "https://www.kleinanzeigen.de" + link_el.get("href")
            if link_el and link_el.get("href")
            else ""
        )

        results.append({
            "title": title,
            "price": price,
            "link": link,
            "description": desc
        })

    return json.dumps(results, ensure_ascii=False, indent=2)
