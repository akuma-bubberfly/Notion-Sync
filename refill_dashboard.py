import os
from notion_client import Client

# Read secrets from environment variables
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("DATABASE_ID")

notion = Client(auth=NOTION_TOKEN)

def refill_energy_mana():
    try:
        # Try the normal databases.query first
        response = notion.databases.query(
            database_id=DATABASE_ID,
            filter={}
        )
        pages = response.get("results", [])
    except Exception as e:
        print("⚠️ databases.query failed, using search fallback:", e)
        # fallback using search
        results = notion.search(filter={"property": "object", "value": "page"}).get("results", [])
        pages = [p for p in results if p.get("parent", {}).get("database_id") == DATABASE_ID]

    if not pages:
        print("ℹ️ No pages found in database.")
        return

    # Loop over all pages
    for page in pages:
        page_id = page["id"]
        properties = page.get("properties", {})

        max_energy = properties.get("Max Energy", {}).get("number", 0) or 0
        max_mana = properties.get("Max Mana", {}).get("number", 0) or 0

        # Update Energy and Mana
        notion.pages.update(
            page_id=page_id,
            properties={
                "Energy": {"number": max_energy},
                "Mana": {"number": max_mana}
            }
        )
        print(f"Refilled page {page_id}: Energy={max_energy}, Mana={max_mana}")

if __name__ == "__main__":
    refill_energy_mana()