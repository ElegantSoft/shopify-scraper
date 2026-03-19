#!/usr/bin/env python3
"""Shopify Store Scraper — extract title, logo, collections & products."""

from __future__ import annotations

import argparse
import json
import sys

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from scraper import scrape

console = Console()


def display(store):
    console.print()
    console.print(
        Panel(
            f"[bold cyan]{store.title or 'Unknown'}[/]\n"
            f"[dim]{store.url}[/]\n"
            f"Logo: [link={store.logo or ''}]{store.logo or 'not found'}[/link]",
            title="Store Info",
            border_style="bright_blue",
        )
    )

    if not store.collections:
        console.print("[yellow]No collections found.[/]")
        return

    tree = Tree(f"[bold]Collections ({len(store.collections)})[/]")
    for col in store.collections:
        branch = tree.add(f"[bold green]{col.title}[/] [dim]({col.handle})[/]")
        if col.products:
            tbl = Table(show_header=True, header_style="bold magenta", pad_edge=False)
            tbl.add_column("#", style="dim", width=4)
            tbl.add_column("Product", min_width=20)
            tbl.add_column("Price", justify="right", width=10)
            tbl.add_column("Options", min_width=30)
            for i, p in enumerate(col.products, 1):
                options_parts = []
                for o in p.options:
                    vals = ", ".join(o["values"][:5])
                    if len(o["values"]) > 5:
                        vals += f" +{len(o['values']) - 5} more"
                    options_parts.append(f"{o['name']}: {vals}")
                options_text = " | ".join(options_parts) if options_parts else "—"
                tbl.add_row(
                    str(i),
                    p.title,
                    f"${p.price}" if p.price else "—",
                    options_text,
                )
            branch.add(tbl)
        else:
            branch.add("[dim]No products[/]")

    console.print(tree)
    console.print()


def main():
    parser = argparse.ArgumentParser(description="Scrape a Shopify store")
    parser.add_argument("url", help="Shopify store URL (e.g. https://example.myshopify.com)")
    parser.add_argument(
        "--json",
        dest="as_json",
        action="store_true",
        help="Output raw JSON instead of pretty table",
    )
    parser.add_argument(
        "-o", "--output",
        help="Save JSON output to a file",
    )
    parser.add_argument(
        "--no-products",
        action="store_true",
        help="Only fetch collections, skip individual products",
    )
    parser.add_argument(
        "-c", "--collections",
        type=int,
        default=5,
        help="Max collections to fetch (default: 5, 0 = unlimited)",
    )
    parser.add_argument(
        "-p", "--products",
        type=int,
        default=20,
        help="Max products per collection (default: 20, 0 = unlimited)",
    )
    args = parser.parse_args()

    console.print(f"\n[bold]Scraping [cyan]{args.url}[/cyan] ...[/]\n")

    try:
        store = scrape(
            args.url,
            include_products=not args.no_products,
            max_collections=args.collections,
            max_products=args.products,
        )
    except Exception as exc:
        console.print(f"[bold red]Error:[/] {exc}")
        sys.exit(1)

    if args.as_json or args.output:
        data = json.dumps(store.to_dict(), indent=2, ensure_ascii=False)
        if args.output:
            with open(args.output, "w") as f:
                f.write(data)
            console.print(f"[green]Saved to {args.output}[/]")
        else:
            print(data)
    else:
        display(store)

    seen = set()
    for c in store.collections:
        for p in c.products:
            seen.add(p.handle)
    console.print(
        f"[dim]Done — {len(store.collections)} collections, "
        f"{len(seen)} unique products[/]\n"
    )


if __name__ == "__main__":
    main()
