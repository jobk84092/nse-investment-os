"""NSE corporate-action watcher.

Fetches the configured NSE corporate-actions and announcements pages, extracts
candidate links/headlines, classifies events, and writes normalized events to
the append-only event store. It intentionally emits evidence for later agents;
it does not make trading decisions.
"""
from __future__ import annotations
import re
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from src.core.event_store import emit_event

KEYWORDS = {
    "dividend": ["dividend","book closure","closure of register","ex-dividend"],
    "profit_warning": ["profit warning"],
    "results": ["financial results","unaudited","audited results","interim results"],
    "agm": ["annual general meeting","agm"],
    "rights": ["rights issue","rights offer"],
    "bonus": ["bonus issue"],
    "split": ["share split","subdivision"],
}

def classify(text: str) -> str:
    t=text.lower()
    for kind, words in KEYWORDS.items():
        if any(w in t for w in words): return kind
    return "announcement"

def fetch_page(url: str) -> list[dict]:
    r=requests.get(url, timeout=30, headers={"User-Agent":"NSE-Investment-OS/1.0"})
    r.raise_for_status()
    soup=BeautifulSoup(r.text,"html.parser")
    rows=[]
    seen=set()
    for a in soup.find_all("a", href=True):
        title=" ".join(a.get_text(" ", strip=True).split())
        href=urljoin(url,a["href"])
        if len(title)<8 or href in seen: continue
        seen.add(href)
        rows.append({"title":title,"url":href})
    return rows

def run(settings: dict) -> list[dict]:
    sources=settings.get("nse_sources",{})
    emitted=[]
    for source_name,key in [("corporate_actions","corporate_actions_url"),("listed_announcements","listed_announcements_url")]:
        url=sources.get(key)
        if not url: continue
        try:
            for row in fetch_page(url):
                kind=classify(row["title"])
                if kind=="announcement" and source_name=="corporate_actions":
                    continue
                emitted.append(emit_event({
                    "source":"nse",
                    "source_page":source_name,
                    "type":kind,
                    "title":row["title"],
                    "url":row["url"],
                    "requires_review":True
                }))
        except requests.RequestException as exc:
            emit_event({"source":"nse","type":"feed_error","source_page":source_name,"detail":str(exc)})
    return emitted
