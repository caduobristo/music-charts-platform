import requests
from bs4 import BeautifulSoup

URL_HOT100 = "https://www.billboard.com/charts/hot-100/"
URL_200 = "https://www.billboard.com/charts/billboard-200/"
URL_GLOBAL200 = "https://www.billboard.com/charts/billboard-global-200/"
URL_ARTIST100 = "https://www.billboard.com/charts/artist-100/s"


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

    print("Total músicas:", len(items))

    for item in items:
        # Título
        title = item.select_one("h3").get_text(strip=True)

        # Artista
        artist = item.select_one("span.c-label").get_text(strip=True)

        # Números
        lw = extract_stat(item, "LW")
        peak = extract_stat(item, "PEAK")
        weeks = extract_stat(item, "WEEKS")

        print(f"{title} - {artist} | LW:{lw} PEAK:{peak} WEEKS:{weeks}")


if __name__ == "__main__":
    fetch_page(URL_HOT100)
    fetch_page(URL_200)
    fetch_page(URL_GLOBAL200)
    fetch_page(URL_ARTIST100)