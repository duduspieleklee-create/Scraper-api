@app.get("/dashboard", include_in_schema=False)
async def dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(text("SELECT * FROM searches"))
        
        # Robuste Umwandlung in einfache Python-Dicts
        searches_list = []
        for row in result:
            searches_list.append({
                "id": row.id,
                "name": row.name,
                "keyword": row.keyword,
                "interval_minutes": row.interval_minutes,
                "enabled": row.enabled,
                "last_run": row.last_run.isoformat() if row.last_run else None,
                "created_at": row.created_at.isoformat() if hasattr(row, 'created_at') and row.created_at else None
            })
        
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "searches": searches_list
        })
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Dashboard Error: {e}")
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "searches": [],
            "error": str(e)
        })
