import requests
from bs4 import BeautifulSoup
import time
from urllib.parse import quote_plus

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.kleinanzeigen.de/"
}

def try_get(url, headers=None, timeout=10):
    headers = headers or HEADERS
    try:
        r = requests.get(url, headers=headers, timeout=timeout)
        print(f"[HTTP] {url} -> {r.status_code}")
        return r
    except Exception as e:
        print(f"[HTTP ERROR] {url} -> {e}")
        return None

def parse_items_from_soup(soup, max_items=5):
    results = []
    selectors = ["article", "div.ad-listitem", "li.ad-listitem", "div.entry"]
    found = []
    for sel in selectors:
        items = soup.select(sel)
        if items:
            found = items
            print(f"[PARSER] selector '{sel}' found {len(items)} items")
            break
    if not found:
        return results

    for item in found[:max_items]:
        title = (item.select_one("h2") or item.select_one(".title") or item.select_one(".headline"))
        price = item.select_one(".aditem-main--middle--price") or item.select_one(".price")
        link = item.select_one("a")
        desc = item.select_one(".aditem-main--middle--description") or item.select_one("p")

        results.append({
            "title": title.get_text(strip=True) if title else "",
            "price": price.get_text(strip=True) if price else "",
            "link": "https://www.kleinanzeigen.de" + link["href"] if link and link.get("href", "").startswith("/") else (link.get("href") if link else ""),
            "description": desc.get_text(strip=True) if desc else ""
        })
    return results

def search_kleinanzeigen(query: str, max_items=5):
    query_enc = quote_plus(query)

    # Метод 1: JSON endpoint
    json_url = f"https://m.kleinanzeigen.de/s-suchanfrage.json?keywords={query_enc}"
    r = try_get(json_url)
    if r and r.status_code == 200:
        try:
            data = r.json()
            ads = data.get("ads", [])[:max_items]
            results = []
            for ad in ads:
                results.append({
                    "title": ad.get("title",""),
                    "price": ad.get("price",""),
                    "link": ad.get("url",""),
                    "description": ad.get("description","")
                })
            if results:
                return {"method": "1", "results": results}
        except:
            pass

    # Метод 2: mobile HTML
    mobile_url = f"https://m.kleinanzeigen.de/s-suchanfrage.html?keywords={query_enc}"
    r = try_get(mobile_url)
    if r and r.status_code == 200:
        soup = BeautifulSoup(r.text, "html.parser")
        items = parse_items_from_soup(soup, max_items)
        if items:
            return {"method": "2", "results": items}

    # Метод 3: desktop HTML
    desktop_url = f"https://www.kleinanzeigen.de/s-suche/{query_enc}/k0"
    r = try_get(desktop_url)
    if r and r.status_code == 200:
        soup = BeautifulSoup(r.text, "html.parser")
        items = parse_items_from_soup(soup, max_items)
        if items:
            return {"method": "3", "results": items}

    return {"method": "none", "results": []}
