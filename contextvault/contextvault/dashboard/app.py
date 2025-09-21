"""
ContextVault Web Dashboard

Simple web dashboard for monitoring and managing ContextVault.
Access at http://localhost:8080
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from ..services.troubleshooting import get_troubleshooting_agent
from ..database import get_db_context
from ..models.context import ContextEntry
from ..models.permissions import Permission

app = FastAPI(title="ContextVault Dashboard", version="0.1.0")

# Setup templates
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

# Mount static files
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page."""
    
    # Get system status
    troubleshooter = get_troubleshooting_agent()
    diagnostics = troubleshooter.run_full_diagnostics()
    
    # Get context statistics
    with get_db_context() as db:
        context_count = db.query(ContextEntry).count()
        permission_count = db.query(Permission).count()
        
        # Get recent context entries
        recent_entries = db.query(ContextEntry).order_by(
            ContextEntry.created_at.desc()
        ).limit(5).all()
        
        # Get context by type
        context_by_type = {}
        for entry in db.query(ContextEntry).all():
            ctx_type = entry.context_type
            context_by_type[ctx_type] = context_by_type.get(ctx_type, 0) + 1
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "diagnostics": diagnostics,
        "context_count": context_count,
        "permission_count": permission_count,
        "recent_entries": recent_entries,
        "context_by_type": context_by_type,
        "timestamp": datetime.now().isoformat()
    })

@app.get("/api/status")
async def api_status():
    """API endpoint for system status."""
    try:
        troubleshooter = get_troubleshooting_agent()
        diagnostics = troubleshooter.run_full_diagnostics()
        
        return {
            "status": "success",
            "data": diagnostics
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/context")
async def api_context():
    """API endpoint for context entries."""
    try:
        with get_db_context() as db:
            entries = db.query(ContextEntry).order_by(
                ContextEntry.created_at.desc()
            ).limit(50).all()
            
            context_data = []
            for entry in entries:
                context_data.append({
                    "id": entry.id,
                    "content": entry.content,
                    "context_type": entry.context_type,
                    "source": entry.source,
                    "tags": entry.tags,
                    "created_at": entry.created_at.isoformat(),
                    "access_count": entry.access_count
                })
            
            return {
                "status": "success",
                "data": context_data
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/permissions")
async def api_permissions():
    """API endpoint for permissions."""
    try:
        with get_db_context() as db:
            permissions = db.query(Permission).all()
            
            permission_data = []
            for perm in permissions:
                permission_data.append({
                    "id": perm.id,
                    "model_id": perm.model_id,
                    "model_name": perm.model_name,
                    "allowed_scopes": perm.get_allowed_scopes(),
                    "is_active": perm.is_active,
                    "created_at": perm.created_at.isoformat()
                })
            
            return {
                "status": "success",
                "data": permission_data
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/context/add")
async def api_add_context(request: Request):
    """API endpoint to add context."""
    try:
        data = await request.json()
        
        with get_db_context() as db:
            entry = ContextEntry(
                content=data.get("content", ""),
                context_type=data.get("context_type", "note"),
                source=data.get("source", "dashboard"),
                tags=data.get("tags", [])
            )
            db.add(entry)
            db.commit()
            
            return {
                "status": "success",
                "message": "Context added successfully",
                "data": {"id": entry.id}
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/context/{context_id}")
async def api_delete_context(context_id: str):
    """API endpoint to delete context."""
    try:
        with get_db_context() as db:
            entry = db.query(ContextEntry).filter(ContextEntry.id == context_id).first()
            if not entry:
                raise HTTPException(status_code=404, detail="Context not found")
            
            db.delete(entry)
            db.commit()
            
            return {
                "status": "success",
                "message": "Context deleted successfully"
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8080)
