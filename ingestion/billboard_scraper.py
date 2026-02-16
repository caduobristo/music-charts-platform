import requests
from bs4 import BeautifulSoup

URL_HOT100 = "https://www.billboard.com/charts/hot-100/"
URL_200 = "https://www.billboard.com/charts/billboard-200/"
URL_GLOBAL200 = "https://www.billboard.com/charts/billboard-global-200/"
URL_ARTIST100 = "https://www.billboard.com/charts/artist-100/"


def extract_stat(item, label_text):
    label = item.find("span", string=lambda s: s and label_text in s)
    if not label:
        return None

    value_span = label.find_next("span", class_="c-label")
    return value_span.get_text(strip=True)

def fetch_page(url:str):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    items = soup.select("li.lrv-u-width-100p.a-chart-result-item-container")

    print("Total items:", len(items))

    rank = []
    count = 0

    for item in items:
        count += 1
        # Título
        title = item.select_one("h3").get_text(strip=True)

        # Artista
        artist = item.select_one("span.c-label").get_text(strip=True)

        # Números
        lw = extract_stat(item, "LW")
        peak = extract_stat(item, "PEAK")
        weeks = extract_stat(item, "WEEKS")

        rank.append({
            "position": count, 
            "title": title, 
            "artist": artist,
            "lw": lw, 
            "peak": peak,
            "weeks": weeks
        })

    return rank

if __name__ == "__main__":
    # Teste em cada página
    print("Fetching Billboard Hot 100...")
    fetch_page(URL_HOT100)
    print("Fetching Billboard 200...")
    fetch_page(URL_200)
    print("Fetching Billboard Global 200...")
    fetch_page(URL_GLOBAL200)
    print("Fetching Billboard Artist 100...")
    fetch_page(URL_ARTIST100)