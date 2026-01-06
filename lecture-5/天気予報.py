import flet as ft
import requests

AREA_URL = "https://www.jma.go.jp/bosai/common/const/area.json"
FORECAST_URL = "https://www.jma.go.jp/bosai/forecast/data/forecast/{}.json"


# -------------------------
# 天気文を自然な日本語に
# -------------------------
def normalize_weather(text: str) -> str:
    return (
        text.replace("　", "")
            .replace("時々", "、時々")
            .replace("所により", "、所により")
            .replace("後", "のち")
    )


# -------------------------
# 天気 → アイコン
# -------------------------
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


class WeatherApp(ft.Container):
    def __init__(self):
        super().__init__()
        self.expand = True
        self.padding = 10

        self.area_data = self.load_area_data()

        self.content_area = ft.Column(
            controls=[ft.Text("地域を選択してください", size=20)],
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )

        self.nav = self.create_navigation()

        self.content = ft.Row(
            [
                self.nav,
                ft.VerticalDivider(width=1),
                ft.Container(
                    content=self.content_area,
                    padding=20,
                    expand=True,
                ),
            ],
            expand=True,
        )

    # -------------------------
    # 地域リスト取得
    # -------------------------
    def load_area_data(self):
        res = requests.get(AREA_URL)
        return res.json()["offices"]

    # -------------------------
    # NavigationRail
    # -------------------------
    def create_navigation(self):
        destinations = []

        for code, info in self.area_data.items():
            destinations.append(
                ft.NavigationRailDestination(
                    icon=ft.Icons.LOCATION_ON_OUTLINED,
                    selected_icon=ft.Icons.LOCATION_ON,
                    label=info["name"],
                )
            )

        return ft.NavigationRail(
            destinations=destinations,
            label_type=ft.NavigationRailLabelType.ALL,
            on_change=self.on_area_selected,
            selected_index=0,
        )

    # -------------------------
    # 地域選択時
    # -------------------------
    def on_area_selected(self, e):
        area_codes = list(self.area_data.keys())
        area_code = area_codes[e.control.selected_index]
        area_name = self.area_data[area_code]["name"]

        self.content_area.controls.clear()
        self.content_area.controls.append(
            ft.Text(f"{area_name} の天気予報", size=24, weight="bold")
        )

        self.show_weather(area_code)
        self.update()

    # -------------------------
    # 天気表示
    # -------------------------
    def show_weather(self, area_code):
        res = requests.get(FORECAST_URL.format(area_code))
        data = res.json()

        time_series = data[0]["timeSeries"][0]
        dates = time_series["timeDefines"]
        areas = time_series["areas"][0]

        labels = ["今日", "明日", "明後日"]

        for i in range(min(3, len(dates))):
            raw_weather = areas["weathers"][i]
            weather = normalize_weather(raw_weather)
            icon = weather_icon(raw_weather)

            tile = ft.ExpansionTile(
                title=ft.Row(
                    [
                        ft.Text(icon, size=24),
                        ft.Text(labels[i], size=18),
                    ],
                    spacing=10,
                ),
                controls=[
                    ft.ListTile(
                        title=ft.Text(weather, size=16)
                    )
                ],
            )

            self.content_area.controls.append(tile)


def main(page: ft.Page):
    page.title = "気象庁 天気予報アプリ"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.horizontal_alignment = "stretch"
    page.vertical_alignment = "stretch"
    page.add(WeatherApp())


ft.app(target=main)