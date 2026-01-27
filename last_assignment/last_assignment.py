import time
import sqlite3
import requests
from bs4 import BeautifulSoup
import pandas as pd
import matplotlib.pyplot as plt

BASE_URL = "https://ja.wikipedia.org"
START_PAGE = "https://ja.wikipedia.org/wiki/日本の観光地一覧"
DB_PATH = "travel.db"
SLEEP_TIME = 1

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS spots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            spot_name TEXT,
            text_length INTEGER,
            section_count INTEGER
        )
    """)
    conn.commit()
    conn.close()

def save_spot(name, text_len, section_cnt):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO spots (spot_name, text_length, section_count) VALUES (?, ?, ?)",
        (name, text_len, section_cnt)
    )
    conn.commit()
    conn.close()

def get_spot_links():
    res = requests.get(START_PAGE, headers=HEADERS)
    soup = BeautifulSoup(res.text, "html.parser")

    links = []
    for a in soup.select("li a"):
        href = a.get("href")
        if href and href.startswith("/wiki/") and ":" not in href:
            links.append(BASE_URL + href)

    return list(set(links))[:30]

def scrape_spot(url):
    res = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(res.text, "html.parser")

    title = soup.find("h1").text.strip()
    paragraphs = soup.select("p")
    sections = soup.select("h2")

    text = "".join(p.text for p in paragraphs)

    return title, len(text), len(sections)

def load_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM spots", conn)
    conn.close()
    return df

def analyze():
    df = load_data()

    plt.scatter(df["text_length"], df["section_count"])
    plt.xlabel("Text Length")
    plt.ylabel("Section Count")
    plt.show()

    summary = df.describe()
    print(summary)

def main():
    init_db()
    links = get_spot_links()

    for url in links:
        try:
            name, text_len, section_cnt = scrape_spot(url)
            save_spot(name, text_len, section_cnt)
            time.sleep(SLEEP_TIME)
        except Exception:
            continue

    analyze()

if __name__ == "__main__":
    main()