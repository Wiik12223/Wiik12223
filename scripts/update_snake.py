from __future__ import annotations

import os
import re
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


USERNAME = os.environ.get("GITHUB_USERNAME", "Wiik12223")
ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets" / "snake-commits.gif"


def get_public_contributions() -> list[list[int]]:
    url = f"https://github.com/users/{USERNAME}/contributions"
    request = urllib.request.Request(url, headers={"User-Agent": "github-profile-snake"})
    html = urllib.request.urlopen(request, timeout=30).read().decode("utf-8")
    values = re.findall(r'<rect[^>]*data-count="(\d+)"[^>]*data-date="([^"]+)"', html)
    if not values:
        values = re.findall(r'data-count="(\d+)"[^>]*data-date="([^"]+)"', html)
    by_date = {date: int(count) for count, date in values}
    dates = sorted(by_date)
    if not dates:
        raise RuntimeError("Não foi possível ler o gráfico público de contribuições.")
    # Seven rows per week, matching GitHub's contribution calendar.
    first = dates[0]
    from datetime import date, timedelta

    start = date.fromisoformat(first)
    start -= timedelta(days=(start.weekday() + 1) % 7)
    weeks = max(1, (date.fromisoformat(dates[-1]) - start).days // 7 + 1)
    grid = [[0 for _ in range(7)] for _ in range(weeks)]
    for week in range(weeks):
        for day in range(7):
            current = start + timedelta(days=week * 7 + day)
            grid[week][day] = by_date.get(current.isoformat(), 0)
    return grid


def render(grid: list[list[int]]) -> None:
    cols, rows = len(grid), 7
    cell, gap = 13, 4
    left, top = 34, 68
    width, height = left * 2 + cols * (cell + gap), 210
    font = ImageFont.load_default()
    max_count = max(1, max(max(column) for column in grid))
    commits = [(x, y) for x, column in enumerate(grid) for y, count in enumerate(column) if count]
    route = [(x, y) for x in range(cols) for y in range(rows)]
    route += list(reversed(route))
    food = commits or [(x, 3) for x in range(4, cols, 8)]
    frames = []
    for tick in range(max(80, len(route))):
        image = Image.new("RGB", (width, height), (13, 17, 23))
        draw = ImageDraw.Draw(image)
        draw.text((left, 18), "> snake_game --target public_commits", fill=(139, 148, 158), font=font)
        draw.text((left, 39), "[ ONLINE ]", fill=(169, 112, 255), font=font)
        for x, column in enumerate(grid):
            for y, count in enumerate(column):
                px, py = left + x * (cell + gap), top + y * (cell + gap)
                level = min(3, (count * 3 + max_count - 1) // max_count) if count else 0
                colors = [(26, 22, 38), (63, 35, 89), (113, 55, 164), (169, 82, 255)]
                draw.rectangle((px, py, px + cell, py + cell), fill=colors[level])
        target = food[(tick // 8) % len(food)]
        tx, ty = target
        px, py = left + tx * (cell + gap), top + ty * (cell + gap)
        draw.rectangle((px - 2, py - 2, px + cell + 2, py + cell + 2), outline=(226, 159, 255), width=2)
        for segment in range(7):
            sx, sy = route[(tick - segment * 2) % len(route)]
            px, py = left + sx * (cell + gap), top + sy * (cell + gap)
            color = (226, 159, 255) if segment == 0 else (126, 58 + segment * 5, 214 + min(segment * 5, 35))
            draw.rectangle((px, py, px + cell, py + cell), fill=color)
        eaten = min(len(food), tick // 8)
        draw.text((width - 160, 39), f"commits: {eaten:02d}", fill=(169, 112, 255), font=font)
        if tick % 19 in (3, 4):
            draw.rectangle((0, top + (tick * 13) % 100, width, top + (tick * 13) % 100 + 1), fill=(201, 108, 255))
        frames.append(image)
    frames[0].save(OUTPUT, save_all=True, append_images=frames[1:], duration=85, loop=0, disposal=2)


if __name__ == "__main__":
    render(get_public_contributions())
