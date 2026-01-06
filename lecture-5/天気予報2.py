import flet as ft
import requests

# =========================
# API URL
# =========================
AREA_URL = "https://www.jma.go.jp/bosai/common/const/area.json"
FORECAST_URL = "https://www.jma.go.jp/bosai/forecast/data/forecast/{}.json"


# =========================
# 天気文を読みやすく
# =========================
def normalize_weather(text: str) -> str:
    return (
        text.replace("　", "")
            .replace("時々", "、時々")
            .replace("所により", "、所により")
            .replace("後", "のち")
    )


# =========================
# 天気 → アイコン
# =========================
def weather_icon(weather: str) -> str:
    if "雪" in weather:
        return "❄️"
    if "雷" in weather:
        return "⛈"
    if "雨" in weather:
        return "🌧"
    if "くもり" in weather or "曇" in weather:
        return "☁️"
    if "晴" in weather:
        return "☀️"
    return "🌈"


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
# 天気予報アプリ
# ==================================================
class WeatherApp(ft.Container):
    def __init__(self):
        super().__init__()
        self.expand = True
        self.padding = 10

        self.area_data = self.load_area_data()
        self.area_codes = list(self.area_data.keys())

        self.content_area = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )

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
    # 地域リスト取得
    # -------------------------
    def load_area_data(self):
        res = requests.get(AREA_URL)
        res.raise_for_status()
        return res.json()["offices"]

    # -------------------------
    # NavigationRail
    # -------------------------
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
            label_type=ft.NavigationRailLabelType.ALL,
            selected_index=0,
            on_change=self.on_area_selected,
        )

    # -------------------------
    # 地域選択時
    # -------------------------
    def on_area_selected(self, e):
        self.show_area_by_index(e.control.selected_index)

    # -------------------------
    # 地域表示（共通）
    # -------------------------
    def show_area_by_index(self, index):
        area_code = self.area_codes[index]
        area_name = self.area_data[area_code]["name"]

        self.content_area.controls.clear()
        self.content_area.controls.append(
            ft.Text(f"{area_name} の天気予報", size=24, weight="bold")
        )

        self.show_weather(area_code)
        self.update()

    # -------------------------
    # 天気表示（十勝・北海道完全対応）
    # -------------------------
    def show_weather(self, area_code):
        res = requests.get(FORECAST_URL.format(area_code))
        res.raise_for_status()
        data = res.json()

        # ✅ weathers を含む timeSeries を探す
        weather_series = find_weather_series(data[0]["timeSeries"])
        if weather_series is None:
            self.content_area.controls.append(
                ft.Text("天気データが取得できません", color="red")
            )
            return

        # ✅ 陸上エリア（海上除外）を選択
        target_area = None
        for a in weather_series["areas"]:
            if "海上" not in a["area"]["name"]:
                target_area = a
                break
        if target_area is None:
            target_area = weather_series["areas"][0]

        labels = ["今日", "明日", "明後日"]

        for i in range(min(3, len(target_area["weathers"]))):
            raw = target_area["weathers"][i]
            weather = normalize_weather(raw)
            icon = weather_icon(raw)

            self.content_area.controls.append(
                ft.ExpansionTile(
                    title=ft.Row(
                        [
                            ft.Text(icon, size=24),
                            ft.Text(labels[i], size=18),
                        ],
                        spacing=10,
                    ),
                    controls=[
                        ft.ListTile(title=ft.Text(weather, size=16))
                    ],
                )
            )


# ==================================================
# 起動
# ==================================================
def main(page: ft.Page):
    page.title = "気象庁 天気予報アプリ"
    page.theme_mode = ft.ThemeMode.LIGHT

    app = WeatherApp()
    page.add(app)

    # 初期表示
    app.show_area_by_index(0)


ft.app(target=main)