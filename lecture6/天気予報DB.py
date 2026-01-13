import flet as ft
import requests
import sqlite3
from datetime import datetime

# =========================
# API URL
# =========================
AREA_URL = "https://www.jma.go.jp/bosai/common/const/area.json"
FORECAST_URL = "https://www.jma.go.jp/bosai/forecast/data/forecast/{}.json"

DB_NAME = "weather.db"


# =========================
# DB 初期化
# =========================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS weather_forecast (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            area_code TEXT,
            area_name TEXT,
            forecast_date TEXT,
            weather TEXT,
            fetched_at TEXT,
            UNIQUE(area_code, forecast_date)
        )
    """)
    conn.commit()
    conn.close()


# =========================
# 天気文整形
# =========================
def normalize_weather(text):
    return (
        text.replace("　", "")
            .replace("時々", "、時々")
            .replace("所により", "、所により")
            .replace("後", "のち")
    )


# =========================
# weathers を含む timeSeries を探す
# =========================
def find_weather_series(time_series_list):
    for ts in time_series_list:
        for area in ts.get("areas", []):
            if "weathers" in area:
                return ts
    return None


# ==================================================
# アプリ本体
# ==================================================
class WeatherDBApp(ft.Container):
    def __init__(self):
        super().__init__()
        self.expand = True
        self.padding = 10

        init_db()

        self.area_data = self.load_area_data()
        self.area_codes = list(self.area_data.keys())

        self.content_area = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO)
        self.nav = self.create_navigation()

        self.content = ft.Row(
            [
                self.nav,
                ft.VerticalDivider(width=1),
                ft.Container(self.content_area, padding=20, expand=True),
            ],
            expand=True,
        )

    # -------------------------
    # 地域データ
    # -------------------------
    def load_area_data(self):
        return requests.get(AREA_URL).json()["offices"]

    def create_navigation(self):
        return ft.NavigationRail(
            destinations=[
                ft.NavigationRailDestination(
                    icon=ft.Icons.LOCATION_ON_OUTLINED,
                    selected_icon=ft.Icons.LOCATION_ON,
                    label=info["name"],
                )
                for info in self.area_data.values()
            ],
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            on_change=self.on_area_selected,
        )

    def on_area_selected(self, e):
        self.show_area(self.area_codes[e.control.selected_index])

    # -------------------------
    # 表示処理
    # -------------------------
    def show_area(self, area_code):
        area_name = self.area_data[area_code]["name"]
        self.content_area.controls.clear()
        self.content_area.controls.append(
            ft.Text(f"{area_name} の天気予報（DB）", size=24, weight="bold")
        )

        # API → DB
        self.fetch_and_store(area_code, area_name)

        # DB → 表示
        forecasts = self.load_from_db(area_code)
        for date, weather in forecasts:
            self.content_area.controls.append(
                ft.ListTile(
                    title=ft.Text(date),
                    subtitle=ft.Text(weather),
                )
            )

        self.update()

    # -------------------------
    # API取得 → DB保存
    # -------------------------
    def fetch_and_store(self, area_code, area_name):
        res = requests.get(FORECAST_URL.format(area_code))
        data = res.json()

        series = find_weather_series(data[0]["timeSeries"])
        if series is None:
            return

        # 陸上のみ
        area = next(
            a for a in series["areas"]
            if "海上" not in a["area"]["name"]
        )

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        for date, weather in zip(series["timeDefines"], area["weathers"]):
            cur.execute("""
                INSERT OR REPLACE INTO weather_forecast
                (area_code, area_name, forecast_date, weather, fetched_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                area_code,
                area_name,
                date[:10],
                normalize_weather(weather),
                datetime.now().isoformat()
            ))

        conn.commit()
        conn.close()

    # -------------------------
    # DB → 表示用取得
    # -------------------------
    def load_from_db(self, area_code):
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("""
            SELECT forecast_date, weather
            FROM weather_forecast
            WHERE area_code = ?
            ORDER BY forecast_date
        """, (area_code,))
        rows = cur.fetchall()
        conn.close()
        return rows


# ==================================================
# 起動
# ==================================================
def main(page: ft.Page):
    page.title = "気象庁 天気予報アプリ（DB版）"
    app = WeatherDBApp()
    page.add(app)
    app.show_area(app.area_codes[0])


ft.app(target=main)