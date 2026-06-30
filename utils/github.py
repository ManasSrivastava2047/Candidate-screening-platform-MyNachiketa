import os
import re

import requests

API = "https://api.github.com"
TIMEOUT = 20
HEADERS = {"Accept": "application/vnd.github+json"}


def _headers() -> dict:
    h = dict(HEADERS)
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def extract_username(url: str) -> str | None:
    if not url or url == "NA":
        return None
    m = re.search(r"github\.com/([A-Za-z0-9_-]+)", url.strip())
    if not m:
        return None
    user = m.group(1)
    if user.lower() in ("orgs", "organizations", "settings", "login"):
        return None
    return user


def fetch_github_profile(username: str) -> dict:
    r = requests.get(f"{API}/users/{username}", headers=_headers(), timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def fetch_repos(username: str, limit: int = 8) -> list[dict]:
    r = requests.get(
        f"{API}/users/{username}/repos",
        headers=_headers(),
        params={"per_page": 30, "sort": "updated"},
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    repos = r.json()
    repos.sort(key=lambda x: x.get("stargazers_count", 0), reverse=True)
    return repos[:limit]


def fetch_repo_languages(languages_url: str) -> dict:
    if not languages_url:
        return {}
    r = requests.get(languages_url, headers=_headers(), timeout=TIMEOUT)
    if r.status_code != 200:
        return {}
    return r.json()


def build_github_summary(username: str) -> dict:
    profile = fetch_github_profile(username)
    repos = fetch_repos(username)

    repo_summaries = []
    all_languages: dict[str, int] = {}

    for repo in repos:
        langs = fetch_repo_languages(repo.get("languages_url", ""))
        for lang, bytes_ in langs.items():
            all_languages[lang] = all_languages.get(lang, 0) + bytes_

        repo_summaries.append({
            "name": repo.get("name"),
            "description": repo.get("description") or "",
            "language": repo.get("language") or "",
            "stars": repo.get("stargazers_count", 0),
            "forks": repo.get("forks_count", 0),
            "topics": repo.get("topics", []),
            "updated_at": repo.get("updated_at", ""),
            "languages": list(langs.keys()),
        })

    top_languages = sorted(all_languages.keys(), key=lambda l: all_languages[l], reverse=True)

    return {
        "username": username,
        "public_repos": profile.get("public_repos", 0),
        "followers": profile.get("followers", 0),
        "bio": profile.get("bio") or "",
        "top_languages": top_languages[:8],
        "repos": repo_summaries,
    }
