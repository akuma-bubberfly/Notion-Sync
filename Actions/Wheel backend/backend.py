import os
from fastapi import FastAPI, Request
from pydantic import BaseModel
from notion_client import Client

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

notion = Client(auth=NOTION_TOKEN)
app = FastAPI()

class SpinRequest(BaseModel):
    user: str
    reward: str

@app.post("/spin")
async def record_spin(spin: SpinRequest):
    try:
        notion.pages.create(
            parent={"database_id": NOTION_DATABASE_ID},
            properties={
                "User": {"rich_text": [{"text": {"content": spin.user}}]},
                "Reward": {"select": {"name": spin.reward}}
            }
        )
        return {"status": "success", "message": f"Recorded reward {spin.reward} for {spin.user}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
