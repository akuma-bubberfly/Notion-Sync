import os
import random
from notion_client import Client

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
PLAYERSTATS_DB_ID = os.getenv("PLAYERSTATS_DB_ID")

client = Client(auth=NOTION_TOKEN)

WEATHER_WEIGHTS = {
    "Sunny": 40,
    "Rainy": 25,
    "Windy": 15,
    "Snowy": 10,
    "Meteor": 5,
    "Aurora": 5,
}

def choose_weather():
    weathers = list(WEATHER_WEIGHTS.keys())
    weights = list(WEATHER_WEIGHTS.values())
    return random.choices(weathers, weights=weights, k=1)[0]

def get_weather_page():
    results = client.search(filter={"value": "page", "property": "object"}, page_size=100)

    for page in results["results"]:
        parent = page.get("parent", {})
        if parent.get("database_id") != PLAYERSTATS_DB_ID:
            continue
        props = page.get("properties", {})
        player_label = props.get("Player", {}).get("select", {}).get("name")
        if player_label == "Weather":
            return page
    return None

def update_weather(new_weather):
    page = get_weather_page()
    if not page:
        print("Could not find weather page.")
        return

    page_id = page["id"]
    print(f"Updating weather to {new_weather}...")
    client.pages.update(
        page_id=page_id,
        properties={
            "Current weather": {"select": {"name": new_weather}}
        }
    )
    print("Weather updated successfully.")

if __name__ == "__main__":
    new_weather = choose_weather()
    update_weather(new_weather)
