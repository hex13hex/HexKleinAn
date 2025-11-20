# parser.py
import requests
from bs4 import BeautifulSoup
import time
import json
from urllib.parse import quote_plus

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.kleinanzeigen.de/"
}

def try_get(url, headers=None, timeout=10):
    headers = headers or HEADERS
    try:
        r = requests.get(url, headers=headers, timeout=timeout)
        print(f"[HTTP] {url} -> {r.status_code}, len={len(r.text)}")
        return r
    except Exception as e:
        print(f"[HTTP ERROR] {url} -> {e}")
        return None

def parse_items_from_soup(soup, max_items=5):
    results = []
    # здесь пробуем несколько селекторов — сайт менялся, поэтому пробуем варианты
    selectors = [
        "article",  # общий
        "div.ad-listitem",
        "li.ad-listitem",
        "div.entry"
    ]
    found = []
    for sel in selectors:
        items = soup.select(sel)
        if items:
            found = items
            print(f"[PARSER] selector '{sel}' found {len(items)} items")
            break
    if not found:
        print("[PARSER] no items found with known selectors")
        return results

    for item in found[:max_items]:
        # Заголовок
        title = ""
        t = item.select_one("h2") or item.select_one(".title") or item.select_one(".headline") or item.select_one(".aditem__title")
        if t:
            title = t.get_text(strip=True)

        # Цена
        price = ""
        p = item.select_one(".aditem-main--middle--price") or item.select_one(".price") or item.select_one(".aditem__price") or item.select_one("p.price")
        if p:
            price = p.get_text(strip=True)

        # Ссылка
        link = ""
        a = item.select_one("a")
        if a and a.get("href"):
            href = a.get("href")
            if href.startswith("/"):
                link = "https://www.kleinanzeigen.de" + href
            else:
                link = href

        # Описание
        desc = ""
        d = item.select_one(".aditem-main--middle--description") or item.select_one(".description") or item.select_one("p")
        if d:
            desc = d.get_text(strip=True)

        results.append({
            "title": title,
            "price": price,
            "link": link,
            "description": desc
        })
    return results

def search_kleinanzeigen(query: str, max_items=5):
    query_enc = quote_plus(query)

    # 1) Попытка: мобильный JSON (если доступен)
    json_urls = [
        f"https://m.kleinanzeigen.de/s-suchanfrage.json?keywords={query_enc}",
        f"https://m.ebay-kleinanzeigen.de/s-suchanfrage.json?keywords={query_enc}"
    ]
    for url in json_urls:
        print("[TRY] JSON endpoint:", url)
        r = try_get(url)
        if r and r.status_code == 200:
            try:
                data = r.json()
                print("[JSON] keys:", list(data.keys())[:10])
                ads = data.get("ads") or data.get("results") or data.get("items") or []
                results = []
                for ad in ads[:max_items]:
                    title = ad.get("title") or ad.get("headline") or ad.get("name") or ""
                    price = ad.get("price") or ad.get("formattedPrice") or ""
                    url_path = ad.get("url") or ad.get("link") or ad.get("adUrl") or ""
                    link = ("https://www.kleinanzeigen.de" + url_path) if url_path.startswith("/") else url_path
                    desc = ad.get("description") or ad.get("snippet") or ""
                    results.append({"title": title, "price": price, "link": link, "description": desc})
                if results:
                    print(f"[JSON] found {len(results)} items")
                    return results
                else:
                    print("[JSON] parsed JSON but no ads extracted")
            except Exception as e:
                print("[JSON parse error]", e)
        time.sleep(0.5)

    # 2) Попытка: мобильная HTML страница (меньше защиты)
    mobile_urls = [
        f"https://m.kleinanzeigen.de/s-suchanfrage.html?keywords={query_enc}",
        f"https://m.ebay-kleinanzeigen.de/s-suchanfrage.html?keywords={query_enc}",
        f"https://www.ebay-kleinanzeigen.de/s-suche/{query_enc}/k0"
    ]
    for url in mobile_urls:
        print("[TRY] mobile/html:", url)
        r = try_get(url)
        if not r or r.status_code != 200:
            time.sleep(0.6)
            continue
        soup = BeautifulSoup(r.text, "html.parser")
        items = parse_items_from_soup(soup, max_items=max_items)
        if items:
            return items
        time.sleep(0.6)

    # 3) Попытка: desktop search page (последний шанс)
    desktop_url = f"https://www.kleinanzeigen.de/s-suche/{quote_plus(query)}/k0"
    print("[TRY] desktop:", desktop_url)
    r = try_get(desktop_url)
    if r and r.status_code == 200:
        soup = BeautifulSoup(r.text, "html.parser")
        items = parse_items_from_soup(soup, max_items=max_items)
        if items:
            return items

    print("[RESULT] nothing found, returning []")
    return []
