# Shopify Store Scraper

Extract **title**, **logo**, **collections**, and **products** (with options) from any Shopify store using its public JSON endpoints.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

### Pretty terminal output

```bash
python main.py https://example-store.myshopify.com
```

### JSON output

```bash
python main.py https://example-store.myshopify.com --json
```

### Save to file

```bash
python main.py https://example-store.myshopify.com -o store.json
```

### Collections only (skip products)

```bash
python main.py https://example-store.myshopify.com --no-products
```

### Limit collections and products

```bash
# 10 collections, 50 products per collection
python main.py https://example-store.myshopify.com -c 10 -p 50

# Unlimited
python main.py https://example-store.myshopify.com -c 0 -p 0
```

Defaults: **5 collections**, **20 products per collection**.

## Options

| Flag | Description | Default |
|------|-------------|---------|
| `--json` | Output raw JSON | Pretty table |
| `-o FILE` | Save JSON to file | — |
| `--no-products` | Skip product fetching | Fetch products |
| `-c N` | Max collections (0 = unlimited) | 5 |
| `-p N` | Max products per collection (0 = unlimited) | 20 |

## Output Structure

Collections and products are separate top-level arrays. Products are deduplicated across collections.

```json
{
  "url": "https://example-store.myshopify.com",
  "title": "Example Store",
  "logo": "https://cdn.shopify.com/.../logo.png",
  "collections": [
    {
      "title": "Summer Collection",
      "handle": "summer-collection",
      "image": "https://cdn.shopify.com/.../collection.jpg"
    }
  ],
  "products": [
    {
      "title": "Cool T-Shirt",
      "handle": "cool-t-shirt",
      "description": "<p>A lightweight, breathable t-shirt...</p>",
      "image": "https://cdn.shopify.com/.../product-thumb.jpg",
      "images": [
        "https://cdn.shopify.com/.../product-thumb.jpg",
        "https://cdn.shopify.com/.../product-side.jpg",
        "https://cdn.shopify.com/.../product-back.jpg"
      ],
      "price": "29.99",
      "url": "https://example-store.myshopify.com/products/cool-t-shirt",
      "options": [
        {
          "name": "Size",
          "values": ["S", "M", "L", "XL"]
        },
        {
          "name": "Color",
          "values": ["Black", "White"]
        }
      ]
    }
  ]
}
```

## How It Works

Shopify stores expose public JSON endpoints:

- `/meta.json` — store name
- `/collections.json` — all collections
- `/collections/{handle}/products.json` — products per collection

The scraper hits these endpoints and falls back to HTML parsing for the logo and collection images.
