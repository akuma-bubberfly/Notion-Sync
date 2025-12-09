import os
from notion-client import Client

# Read secrets from environment variables
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("DATABASE_ID")

notion = Client(auth=NOTION_TOKEN)

def refill_energy_mana():
    # Query all pages in the database
    results = notion.databases.query(database_id=DATABASE_ID).get("results", [])

    for page in results:
        page_id = page["id"]
        properties = page["properties"]

        max_energy = properties.get("Max Energy", {}).get("number", 0)
        max_mana = properties.get("Max Mana", {}).get("number", 0)

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
