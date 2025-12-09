import os
import pronotepy
from datetime import datetime, timedelta
from dotenv import load_dotenv
from notion_client import Client

load_dotenv()

PRONOTE_URL = os.getenv("PRONOTE_URL")
PRONOTE_USERNAME = os.getenv("PRONOTE_USERNAME")
PRONOTE_PASSWORD = os.getenv("PRONOTE_PASSWORD")
NOTION_TOKEN = os.getenv("NOTION_TOKEN_P")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

missing = [var for var, val in [
    ("PRONOTE_URL", PRONOTE_URL),
    ("PRONOTE_USERNAME", PRONOTE_USERNAME),
    ("PRONOTE_PASSWORD", PRONOTE_PASSWORD),
    ("NOTION_TOKEN", NOTION_TOKEN),
    ("NOTION_DATABASE_ID", NOTION_DATABASE_ID)
] if not val]

if missing:
    print(f"❌ Variables manquantes : {', '.join(missing)}")
    exit(1)

notion = Client(auth=NOTION_TOKEN)

print("Connexion à Pronote...")
client = pronotepy.Client(PRONOTE_URL, username=PRONOTE_USERNAME, password=PRONOTE_PASSWORD)

if not client.logged_in:
    print("❌ Échec de connexion à Pronote.")
    exit(1)

print("✅ Connecté à Pronote.")


# ------------------------------------------------------------
#   SUPPRESSION TOTALE DE LA DATABASE
# ------------------------------------------------------------

def clear_notion_database():
    def normalize_id(i):
        return (i or "").replace("-", "").lower()

    print("🗑️ Suppression des anciennes pages Notion...")
    print("NOTION_DATABASE_ID:", NOTION_DATABASE_ID)
    print("NOTION_DATABASE_ID (normalized):", normalize_id(NOTION_DATABASE_ID))

    page_ids = []

    db_endpoint = getattr(notion, "databases", None)
    has_db_query = bool(db_endpoint and hasattr(db_endpoint, "query"))
    print("has databases.query:", has_db_query)

    if has_db_query:
        try:
            cursor = None
            total = 0
            while True:
                resp = notion.databases.query(
                    database_id=NOTION_DATABASE_ID,
                    start_cursor=cursor,
                    page_size=100
                )
                results = resp.get("results", [])
                for p in results:
                    pid = p.get("id")
                    page_ids.append(pid)
                    total += 1
                cursor = resp.get("next_cursor")
                if not cursor:
                    break
            print("databases.query total pages found:", total)
        except Exception as e:
            print("⚠️ Erreur lors de databases.query, fallback sur search :", e)

    if not page_ids:
        try:
            cursor = None
            total = 0
            while True:
                resp = notion.search(
                    start_cursor=cursor,
                    page_size=100,
                    filter={"property": "object", "value": "page"}
                )
                results = resp.get("results", [])
                print(f"search returned {len(results)} results, next_cursor={resp.get('next_cursor')}")
                for idx, p in enumerate(results[:10]):  # log up to 10 samples to inspect parent shape
                    print(f" sample[{idx}] id={p.get('id')} parent={p.get('parent')}")
                for p in results:
                    parent = p.get("parent", {}) or {}
                    dbid = parent.get("database_id") or parent.get("database_id")  # defensive
                    # try to find database_id in parent values if structure differs
                    if not dbid:
                        for v in parent.values():
                            if isinstance(v, str) and normalize_id(v) == normalize_id(NOTION_DATABASE_ID):
                                dbid = v
                                break
                    if dbid and normalize_id(dbid) == normalize_id(NOTION_DATABASE_ID):
                        page_ids.append(p.get("id"))
                        total += 1
                cursor = resp.get("next_cursor")
                if not cursor:
                    break
            print("search total pages matched database:", total)
        except Exception as e:
            print("❌ Erreur pendant la requête search :", e)
            return

    if not page_ids:
        print("ℹ️ Aucune page trouvée à archiver. Vérifier : token, permissions, et que les pages sont bien dans la DB indiquée.")
        return

    print(f"ℹ️ {len(page_ids)} page(s) trouvée(s). Archivage en cours...")
    for pid in page_ids:
        try:
            notion.pages.update(page_id=pid, archived=True)
            print(" - Page archivée :", pid)
        except Exception as e:
            print("❌ Erreur archivage :", pid, e)

    print("✔️ Base Notion vidée.")
# ...existing code...

# ------------------------------------------------------------
#   CRÉATION DES PAGES
# ------------------------------------------------------------

def get_lesson_end(lesson):
    for attr in ("end", "end_time", "stop", "end_date", "finish"):
        val = getattr(lesson, attr, None)
        if val:
            return val
    duration = getattr(lesson, "duration", None) or getattr(lesson, "length", None)
    if isinstance(duration, (int, float)):
        return lesson.start + timedelta(minutes=int(duration))
    return lesson.start + timedelta(hours=1)

def add_lesson_to_notion(lesson):
    start = getattr(lesson, "start", None)
    if not start:
        print("❌ Lesson has no start, skipping:", lesson)
        return

    end = getattr(lesson, "end", None) or get_lesson_end(lesson)
    subject_name = getattr(getattr(lesson, "subject", None), "name", None) or getattr(lesson, "subject", None) or "Cours"
    classroom = getattr(lesson, "classroom", "") or ""
    teacher = getattr(lesson, "teacher_name", "") or ""

    start_iso = start.strftime("%Y-%m-%dT%H:%M:%S")
    end_iso = end.strftime("%Y-%m-%dT%H:%M:%S")

    properties = {
        "Name": {"title": [{"text": {"content": subject_name}}]},
        "Date": {"date": {"start": start_iso, "end": end_iso}},
        "Subject": {"select": {"name": subject_name}},
        "Class": {"rich_text": [{"text": {"content": classroom}}]},
        "Teacher": {"rich_text": [{"text": {"content": teacher}}]},
    }

    try:
        notion.pages.create(
            parent={"database_id": NOTION_DATABASE_ID},
            properties=properties
        )
        print(f"✅ Created: {subject_name} — {start_iso} → {end_iso}")
    except Exception as e:
        print("❌ Error creating Notion page:", e, "lesson:", subject_name, start_iso, end_iso)

def main():
    clear_notion_database()

    today = datetime.now()
    end_date = today + timedelta(days=7)

    try:
        lessons = client.lessons(today, end_date)
    except Exception as e:
        print("❌ Erreur récupération Pronote :", e)
        return

    print(f"{len(lessons)} cours trouvés. Envoi vers Notion...")

    for lesson in lessons:
        add_lesson_to_notion(lesson)

if __name__ == "__main__":
    main()