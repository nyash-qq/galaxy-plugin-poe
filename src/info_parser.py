import json
from dataclasses import asdict, dataclass, is_dataclass

import requests
from bs4 import BeautifulSoup


@dataclass
class Achievement:
    release_per_platform_id: str
    name: str
    description: str
    api_key: str
    image_url_unlocked: str
    image_url_locked: str


def get_text(raw_str):
    return raw_str.text.strip()


def parse_achievement(row):
    columns = row.find_all("td")
    name = get_text(columns[0])
    return name, Achievement(
        release_per_platform_id="pathofexile_PathOfExile",
        name=name,
        description=get_text(columns[1]),
        api_key=str(len(achievements)),
        image_url_unlocked=str(columns[0].find_all("a", {"class": "image"})[0].img["src"]),
        image_url_locked=""
    )


achievements = {}

for row in BeautifulSoup(
    requests.get("https://pathofexile.gamepedia.com/Achievements").text,
    "lxml"
).select_one("table.wikitable.sortable").tbody.find_all("tr")[1:]:
    name, achievement = parse_achievement(row)
    achievements[name] = achievement

locked_ach_map = dict()
with open(r"d:\locked_ach.html", "r") as f:
    for row in BeautifulSoup(f.read(), "lxml").select("div.achieveRow"):
        ach = achievements.get(get_text(row.select_one("div.achieveTxt").h3))
        if ach is None:
            continue

        ach.image_url_locked = row.select_one("div.CachieveImgHolder").img["src"]


class AchievementEncoder(json.JSONEncoder):
    def default(self, o):
        if is_dataclass(o):
            return asdict(o)
        return super().default(o)


with open(r"d:\achievements.json", "w+") as f:
    json.dump(list(achievements.values()), f, cls=AchievementEncoder, indent=4)
