from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup


@dataclass
class Product:
    title: str
    handle: str
    image: str | None = None
    images: list[str] = field(default_factory=list)
    price: str | None = None
    url: str | None = None
    options: list[dict] = field(default_factory=list)


@dataclass
class Collection:
    title: str
    handle: str
    image: str | None = None
    products: list[Product] = field(default_factory=list)


@dataclass
class StoreData:
    url: str
    title: str | None = None
    logo: str | None = None
    collections: list[Collection] = field(default_factory=list)

    def to_dict(self) -> dict:
        seen: set[str] = set()
        all_products: list[dict] = []
        for c in self.collections:
            for p in c.products:
                if p.handle not in seen:
                    seen.add(p.handle)
                    all_products.append({
                        "title": p.title,
                        "handle": p.handle,
                        "image": p.image,
                        "images": p.images,
                        "price": p.price,
                        "url": p.url,
                        "options": p.options,
                    })

        return {
            "url": self.url,
            "title": self.title,
            "logo": self.logo,
            "collections": [
                {
                    "title": c.title,
                    "handle": c.handle,
                    "image": c.image,
                }
                for c in self.collections
            ],
            "products": all_products,
        }


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/html",
}


def _normalise_url(raw: str) -> str:
    raw = raw.strip().rstrip("/")
    if not raw.startswith(("http://", "https://")):
        raw = "https://" + raw
    parsed = urlparse(raw)
    return f"{parsed.scheme}://{parsed.netloc}"


def _get_json(client: httpx.Client, url: str) -> dict | list | None:
    try:
        resp = client.get(url, headers=HEADERS, follow_redirects=True, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except (httpx.HTTPError, json.JSONDecodeError):
        return None


def _get_html(client: httpx.Client, url: str) -> str | None:
    try:
        resp = client.get(url, headers=HEADERS, follow_redirects=True, timeout=15)
        resp.raise_for_status()
        return resp.text
    except httpx.HTTPError:
        return None


def _scrape_meta(client: httpx.Client, base: str) -> tuple[str | None, str | None]:
    """Extract title and logo from the store homepage."""
    title, logo = None, None

    meta = _get_json(client, f"{base}/meta.json")
    if meta and isinstance(meta, dict):
        title = meta.get("name")

    html = _get_html(client, base)
    if html:
        soup = BeautifulSoup(html, "html.parser")
        if not title:
            og_title = soup.find("meta", property="og:site_name")
            if og_title:
                title = og_title.get("content")
            elif soup.title:
                title = soup.title.string

        og_image = soup.find("meta", property="og:image")
        if og_image:
            logo = og_image.get("content")

        if not logo:
            for img in soup.select("img"):
                src = img.get("src", "")
                if "logo" in src.lower() or "logo" in img.get("alt", "").lower():
                    logo = src
                    break

        if not logo:
            link_icon = soup.find("link", rel=re.compile(r"icon", re.I))
            if link_icon:
                logo = link_icon.get("href")

    if logo and logo.startswith("//"):
        logo = "https:" + logo

    return title, logo


def _scrape_collections(
    client: httpx.Client, base: str, max_collections: int = 0
) -> list[Collection]:
    collections: list[Collection] = []
    page = 1
    while True:
        data = _get_json(client, f"{base}/collections.json?limit=250&page={page}")
        if not data or not isinstance(data, dict):
            break
        batch = data.get("collections", [])
        if not batch:
            break
        for c in batch:
            collections.append(
                Collection(
                    title=c.get("title", ""),
                    handle=c.get("handle", ""),
                    image=(c.get("image") or {}).get("src"),
                )
            )
            if max_collections and len(collections) >= max_collections:
                return collections
        page += 1
    return collections


def _scrape_products_for_collection(
    client: httpx.Client, base: str, collection: Collection, max_products: int = 0
) -> None:
    page = 1
    per_page = min(max_products, 250) if max_products else 250
    while True:
        data = _get_json(
            client,
            f"{base}/collections/{collection.handle}/products.json?limit={per_page}&page={page}",
        )
        if not data or not isinstance(data, dict):
            break
        batch = data.get("products", [])
        if not batch:
            break
        for p in batch:
            all_images = [img["src"] for img in p.get("images", []) if img.get("src")]
            raw_variants = p.get("variants", [])
            price = raw_variants[0]["price"] if raw_variants else None
            options = [
                {"name": o.get("name", ""), "values": o.get("values", [])}
                for o in p.get("options", [])
            ]
            collection.products.append(
                Product(
                    title=p.get("title", ""),
                    handle=p.get("handle", ""),
                    image=all_images[0] if all_images else None,
                    images=all_images,
                    price=price,
                    url=f"{base}/products/{p.get('handle', '')}",
                    options=options,
                )
            )
            if max_products and len(collection.products) >= max_products:
                return
        page += 1


def _scrape_collection_image(
    client: httpx.Client, base: str, collection: Collection
) -> None:
    """Try to get the collection image from the collection page."""
    html = _get_html(client, f"{base}/collections/{collection.handle}")
    if not html:
        return
    soup = BeautifulSoup(html, "html.parser")
    og = soup.find("meta", property="og:image")
    if og and og.get("content"):
        img = og["content"]
        if img.startswith("//"):
            img = "https:" + img
        collection.image = img


def scrape(
    url: str,
    *,
    include_products: bool = True,
    max_collections: int = 5,
    max_products: int = 20,
) -> StoreData:
    base = _normalise_url(url)
    store = StoreData(url=base)

    with httpx.Client() as client:
        store.title, store.logo = _scrape_meta(client, base)
        store.collections = _scrape_collections(client, base, max_collections)

        if include_products:
            for collection in store.collections:
                _scrape_products_for_collection(client, base, collection, max_products)

        for collection in store.collections:
            if not collection.image:
                _scrape_collection_image(client, base, collection)

    return store
