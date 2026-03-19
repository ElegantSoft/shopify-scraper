# Shopify Store Scraper

Extract **title**, **logo**, **collections**, and **products** from any Shopify store using its public JSON endpoints.

## Setup

```bash
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

## Output Structure

```json
{
  "url": "https://example-store.myshopify.com",
  "title": "Example Store",
  "logo": "https://cdn.shopify.com/.../logo.png",
  "collections": [
    {
      "title": "Summer Collection",
      "handle": "summer-collection",
      "image": "https://cdn.shopify.com/.../collection.jpg",
      "products": [
        {
          "title": "Cool T-Shirt",
          "handle": "cool-t-shirt",
          "image": "https://cdn.shopify.com/.../product.jpg",
          "price": "29.99",
          "url": "https://example-store.myshopify.com/products/cool-t-shirt"
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

The scraper hits these endpoints and falls back to HTML parsing for the logo.
