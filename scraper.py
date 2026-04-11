from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup

URL = "https://mostaql.com/projects"
PARAMS = {
    "category": "development",
    "sort": "latest",
}
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ar,en;q=0.9",
}


def fetch_projects() -> list[dict]:
    """
    Returns a list of project dicts, newest first.
    Each dict has: id, title, url, client, bids, time_posted, raw
    """
    response = requests.get(URL, params=PARAMS, headers=HEADERS, timeout=15)
    response.raise_for_status()

    # User requirement: never fetch the base projects URL without both query params.
    final_params = parse_qs(urlparse(response.url).query)
    if final_params.get("category", [""])[0] != "development" or final_params.get(
        "sort", [""]
    )[0] != "latest":
        raise RuntimeError(f"Required query params missing from response URL: {response.url}")

    soup = BeautifulSoup(response.text, "lxml")

    first_match = soup.find(
        "a",
        href=lambda h: h and "/project/" in h and "template" not in h and "create" not in h,
    )
    # DEBUG: Uncomment on first run to inspect the first matched anchor parent HTML.
    # print(first_match.parent.prettify() if first_match and first_match.parent else "No matching anchor parent found")

    projects = []

    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]

        # Discard non-project links:
        # - /project/create?template=... (copy-project links)
        # - Any href that does not match /project/<numeric-id>-slug
        if "/project/" not in href:
            continue
        if "template" in href or "create" in href:
            continue

        if not href.startswith("http"):
            href = "https://mostaql.com" + href

        # Extract numeric project ID from URL slug
        # e.g. https://mostaql.com/project/1229028-some-title -> "1229028"
        try:
            slug = href.split("/project/")[1].split("?")[0]
            project_id = slug.split("-")[0]
        except IndexError:
            continue

        if not project_id.isdigit():
            continue

        title = anchor.get_text(strip=True)
        if not title:
            continue

        # Assumption from plan: keep find_parent() exactly as the baseline behavior
        # even though Mostaql's richer card metadata currently appears higher up.
        card = anchor.find_parent()
        raw_text = card.get_text(" ", strip=True) if card else ""

        projects.append(
            {
                "id": project_id,
                "title": title,
                "url": href,
                "raw": raw_text,
            }
        )

    # Deduplicate by ID (multiple anchors per card point to the same project)
    seen_ids: set[str] = set()
    unique: list[dict] = []
    for project in projects:
        if project["id"] not in seen_ids:
            seen_ids.add(project["id"])
            unique.append(project)

    return unique
