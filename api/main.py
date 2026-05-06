import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from dotenv import load_dotenv
from src.analyzer import MatchAnalyzer
from src.data_manager import DataManager

load_dotenv()

app = FastAPI(title="LolAnalyzer API")
dm = DataManager()
api_key = os.getenv("RIOT_API_KEY")

class AnalyzeRequest(BaseModel):
    name: str
    tag: str
    region: Optional[str] = None
    count: Optional[int] = 52
    queue: Optional[int] = None

@app.get("/api/players")
async def get_players():
    return dm.list_all_users()

@app.get("/api/players/{user_id}")
async def get_player_details(user_id: str):
    # user_id is expected to be "name#tag"
    user_id_lower = user_id.lower()
    if user_id_lower not in dm.registry.users:
        raise HTTPException(status_code=404, detail="Player not found")
    
    metadata = dm.registry.users[user_id_lower]
    return {
        "metadata": metadata.to_dict(),
        "reports": dm.get_player_reports(metadata.name, metadata.tag),
        "matches": dm.get_player_matches(metadata.name, metadata.tag)
    }

@app.post("/api/analyze")
async def analyze_player(req: AnalyzeRequest):
    if not api_key:
        raise HTTPException(status_code=500, detail="RIOT_API_KEY not configured on server")
    
    try:
        analyzer = MatchAnalyzer(api_key.strip(), req.name, req.tag, req.region, req.count)
        result = analyzer.run(queue=req.queue)
        if not result:
            raise HTTPException(status_code=404, detail="No matches found or analysis failed")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")

@app.get("/api/reports/{player_slug}/{report_id}")
async def get_report_content(player_slug: str, report_id: str):
    # We need to find the report path from the player's report history
    # For simplicity in this local version, we'll extract name and tag from slug or just search all users
    # But better to use the registry
    
    found_user = None
    for uid, user in dm.registry.users.items():
        safe_id = uid.replace("#", "_").replace(" ", "_")
        if safe_id == player_slug.lower():
            found_user = user
            break
            
    if not found_user:
        raise HTTPException(status_code=404, detail="Player not found")
        
    reports = dm.get_player_reports(found_user.name, found_user.tag)
    if report_id not in reports:
        raise HTTPException(status_code=404, detail="Report not found")
        
    report_path = reports[report_id]["file_path"]
    if not os.path.exists(report_path):
        raise HTTPException(status_code=404, detail="Report file missing")
        
    with open(report_path, "r") as f:
        return {"content": f.read()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
