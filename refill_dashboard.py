import os
import sys
from notion_client import Client

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("DATABASE_ID")

if not NOTION_TOKEN or not DATABASE_ID:
    print("❌ Missing environment variables. Set NOTION_TOKEN and DATABASE_ID.")
    sys.exit(1)

notion = Client(auth=NOTION_TOKEN)

def normalize_id(i):
    return (i or "").replace("-", "").lower()

def fetch_pages_from_database(database_id):
    pages = []

    db_endpoint = getattr(notion, "databases", None)
    has_db_query = bool(db_endpoint and hasattr(db_endpoint, "query"))
    if has_db_query:
        try:
            cursor = None
            while True:
                resp = notion.databases.query(
                    database_id=database_id,
                    start_cursor=cursor,
                    page_size=100
                )
                results = resp.get("results", [])
                pages.extend(results)
                cursor = resp.get("next_cursor") or resp.get("nextCursor")
                if not cursor:
                    break
            print(f"ℹ️ databases.query returned {len(pages)} page(s).")
            return pages
        except Exception as e:
            print("⚠️ databases.query failed, falling back to search:", e)

    # Fallback: use search and filter pages whose parent database_id matches
    try:
        cursor = None
        while True:
            # some SDK versions accept start_cursor/page_size/filter
            resp = notion.search(
                start_cursor=cursor,
                page_size=100,
                filter={"property": "object", "value": "page"}
            )
            results = resp.get("results", [])
            for p in results:
                parent = p.get("parent") or {}
                dbid = parent.get("database_id") or parent.get("database_id")
                if not dbid:
                    # defensive: scan parent values for matching id
                    for v in parent.values():
                        if isinstance(v, str) and normalize_id(v) == normalize_id(database_id):
                            dbid = v
                            break
                if dbid and normalize_id(dbid) == normalize_id(database_id):
                    pages.append(p)
            cursor = resp.get("next_cursor") or resp.get("nextCursor")
            if not cursor:
                break
        print(f"ℹ️ search fallback matched {len(pages)} page(s).")
        return pages
    except TypeError:
        # older/newer SDKs may have different signature; try a minimal call
        try:
            resp = notion.search(filter={"property": "object", "value": "page"})
            results = resp.get("results", [])
            for p in results:
                parent = p.get("parent") or {}
                dbid = parent.get("database_id")
                if dbid and normalize_id(dbid) == normalize_id(database_id):
                    pages.append(p)
            print(f"ℹ️ search (minimal) matched {len(pages)} page(s).")
            return pages
        except Exception as e:
            print("❌ search also failed:", e)
            return []
    except Exception as e:
        print("❌ search failed:", e)
        return []

def refill_energy_mana():
    pages = fetch_pages_from_database(DATABASE_ID)

    if not pages:
        print("ℹ️ No pages found in database.")
        return

    for page in pages:
        page_id = page.get("id")
        properties = page.get("properties", {}) or {}

        max_energy = (properties.get("Max Energy") or {}).get("number") or 0
        max_mana = (properties.get("Max Mana") or {}).get("number") or 0

        try:
            notion.pages.update(
                page_id=page_id,
                properties={
                    "Energy": {"number": max_energy},
                    "Mana": {"number": max_mana}
                }
            )
            print(f"Refilled page {page_id}: Energy={max_energy}, Mana={max_mana}")
        except Exception as e:
            print(f"❌ Failed to update page {page_id}:", e)

if __name__ == "__main__":
    refill_energy_mana()