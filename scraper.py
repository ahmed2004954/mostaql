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


def _get_soup(url: str, *, params: dict | None = None) -> tuple[BeautifulSoup, str]:
    response = requests.get(url, params=params, headers=HEADERS, timeout=15)
    response.raise_for_status()
    return BeautifulSoup(response.text, "lxml"), response.url


def _clean_text(value: str) -> str:
    return " ".join(value.split())


def _extract_meta_rows(panel) -> dict[str, str]:
    rows: dict[str, str] = {}
    if panel is None:
        return rows

    for row in panel.select(".meta-row"):
        label_node = row.select_one(".meta-label")
        value_node = row.select_one(".meta-value")
        if not label_node or not value_node:
            continue

        label = _clean_text(label_node.get_text(" ", strip=True))
        value = _clean_text(value_node.get_text(" ", strip=True))
        if label and value:
            rows[label] = value

    return rows


def _extract_employer_stats(soup: BeautifulSoup) -> dict[str, str]:
    stats: dict[str, str] = {}
    employer_widget = soup.select_one("[data-type='employer_widget']")
    if employer_widget is None:
        return stats

    for row in employer_widget.select("table.table-meta tr"):
        cells = row.find_all("td", recursive=False)
        if len(cells) != 2:
            continue

        label = _clean_text(cells[0].get_text(" ", strip=True))
        value = _clean_text(cells[1].get_text(" ", strip=True))
        if label and value:
            stats[label] = value

    return stats


def fetch_projects() -> list[dict]:
    """
    Returns a list of project dicts, newest first.
    Each dict has: id, title, url, client, bids, time_posted, raw
    """
    soup, response_url = _get_soup(URL, params=PARAMS)

    # User requirement: never fetch the base projects URL without both query params.
    final_params = parse_qs(urlparse(response_url).query)
    if final_params.get("category", [""])[0] != "development" or final_params.get(
        "sort", [""]
    )[0] != "latest":
        raise RuntimeError(
            f"Required query params missing from response URL: {response_url}"
        )

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


def enrich_project(project: dict) -> dict:
    """
    Fetches the Mostaql project page and augments the project dict with:
    details, published_at, budget, execution_duration, hiring_rate, applicants_count.
    """
    soup, _ = _get_soup(project["url"])

    details_panel = soup.select_one("#project-brief .text-wrapper-div.carda__content")
    details = _clean_text(details_panel.get_text("\n", strip=True)) if details_panel else ""

    meta_panel = soup.select_one("#project-meta-panel-panel")
    meta_rows = _extract_meta_rows(meta_panel)
    employer_stats = _extract_employer_stats(soup)
    applicants_count = str(len(soup.select("#bidsCollection-panel [data-bid-item]")))

    enriched = dict(project)
    enriched["details"] = details
    enriched["published_at"] = meta_rows.get("تاريخ النشر", "")
    enriched["budget"] = meta_rows.get("الميزانية", "")
    enriched["execution_duration"] = meta_rows.get("مدة التنفيذ", "")
    enriched["hiring_rate"] = employer_stats.get("معدل التوظيف", "")
    enriched["applicants_count"] = applicants_count
    return enriched
