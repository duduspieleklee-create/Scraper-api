@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        now = datetime.utcnow()
        cpu = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        proc = psutil.Process(os.getpid())
        uptime_secs = int(now.timestamp() - proc.create_time())
        h, rem = divmod(uptime_secs, 3600)
        m, s = divmod(rem, 60)
        uptime_str = f"{h}h {m}m {s}s" if h else f"{m}m {s}s"
        pid = proc.pid

        # Database check
        try:
            await db.scalar(select(func.count(Search.id)))
            db_ok = True
        except Exception:
            db_ok = False

        # Worker status
        worker_online = False
        worker_last_seen_str = None
        try:
            last_hb = await db.scalar(
                select(WorkerHeartbeat.last_seen)
                .order_by(WorkerHeartbeat.last_seen.desc())
                .limit(1)
            )
            if last_hb:
                age_secs = int((now - last_hb).total_seconds())
                if age_secs < 120:
                    worker_online = True
                    worker_last_seen_str = f"vor {age_secs}s"
                else:
                    mins = age_secs // 60
                    worker_last_seen_str = f"vor {mins} Min"
        except Exception:
            pass

        # Stats
        total_searches = await db.scalar(select(func.count(Search.id))) or 0
        active_searches = (
            await db.scalar(select(func.count(Search.id)).where(Search.enabled == True)) or 0
        )
        paused_searches = total_searches - active_searches
        total_ads = await db.scalar(select(func.count(SeenAd.id))) or 0
        yesterday = now - timedelta(hours=24)
        ads_24h = (
            await db.scalar(select(func.count(SeenAd.id)).where(SeenAd.first_seen >= yesterday)) or 0
        )
        total_users = await db.scalar(select(func.count(User.id))) or 0

        # Proxy stats
        active_proxies = await db.scalar(select(func.count(Proxy.id)).where(Proxy.status == "active")) or 0
        total_proxies = await db.scalar(select(func.count(Proxy.id))) or 0
        proxy_result = await db.execute(select(Proxy).order_by(Proxy.created_at.desc()))
        proxy_list = [
            {
                "id": p.id,
                "url": p.url,
                "status": p.status,
                "protocol": p.protocol,
                "country": p.country,
                "fail_count": p.fail_count
            }
            for p in proxy_result.scalars().all()
        ]

        # Token stats
        tokens_spent_raw = await db.scalar(select(func.sum(TokenTransaction.amount)).where(TokenTransaction.amount < 0))
        tokens_spent = abs(int(tokens_spent_raw or 0))
        tokens_24h_raw = await db.scalar(select(func.sum(TokenTransaction.amount)).where(TokenTransaction.amount < 0, TokenTransaction.created_at >= yesterday))
        tokens_24h = abs(int(tokens_24h_raw or 0))

        from sqlalchemy import case as sql_case
        wh_result = await db.execute(select(
            func.count(TokenTransaction.id).label("total"),
            func.sum(sql_case((TokenTransaction.reason.ilike("%webhook_ok%"), 1), else_=0)).label("ok"),
            func.sum(sql_case((TokenTransaction.reason.ilike("%webhook_fail%"), 1), else_=0)).label("fail")
        ))
        wh_row = wh_result.first()
        webhook_ok = int(wh_row.ok or 0)
        webhook_fail = int(wh_row.fail or 0)

        # Ads per day
        from sqlalchemy import cast, Date as SQLDate
        ads_per_day_raw = await db.execute(select(
            cast(SeenAd.first_seen, SQLDate).label("day"),
            func.count(SeenAd.id).label("cnt")
        ).where(SeenAd.first_seen >= now - timedelta(days=7)).group_by("day").order_by("day"))
        day_map = {str(row.day): row.cnt for row in ads_per_day_raw}
        ads_per_day = []
        for i in range(6, -1, -1):
            d = (now - timedelta(days=i)).date()
            label = d.strftime("%d.%m")
            ads_per_day.append((label, day_map.get(str(d), 0)))

        # Top searches
        top_rows = await db.execute(
            select(Search, func.count(SeenAd.id).label("ad_count"))
            .outerjoin(SeenAd, Search.id == SeenAd.search_id)
            .group_by(Search.id)
            .order_by(func.count(SeenAd.id).desc())
            .limit(5)
        )
        top_searches_dict = []
        for search, ad_count in top_rows.all():
            top_searches_dict.append({
                "id": search.id,
                "name": search.name,
                "keyword": search.keyword,
                "ad_count": int(ad_count or 0)
            })

        # Price stats
        price_row = await db.execute(select(
            func.min(SeenAd.price).label("mn"),
            func.max(SeenAd.price).label("mx"),
            func.avg(SeenAd.price).label("av"),
            func.count(SeenAd.price).label("cnt")
        ).where(SeenAd.price.isnot(None), SeenAd.price > 0))
        pr = price_row.first()
        price_min = int(pr.mn) if pr.mn is not None else None
        price_max = int(pr.mx) if pr.mx is not None else None
        price_avg = round(float(pr.av), 2) if pr.av is not None else None
        price_count = int(pr.cnt) if pr.cnt else 0

        # All searches
        rows = await db.execute(
            select(Search, func.count(SeenAd.id).label("ad_count"))
            .outerjoin(SeenAd, Search.id == SeenAd.search_id)
            .group_by(Search.id)
            .order_by(Search.created_at.desc())
        )
        searches_dict = []
        for search, ad_count in rows.all():
            searches_dict.append({
                "id": search.id,
                "name": search.name,
                "keyword": search.keyword,
                "enabled": search.enabled,
                "ad_count": int(ad_count or 0),
                "created_at": search.created_at
            })

        # Recent ads
        recent_ads_result = await db.execute(
            select(SeenAd).order_by(SeenAd.first_seen.desc()).limit(15)
        )
        recent_ads_dict = [
            {
                "id": ad.id,
                "title": ad.title,
                "price": ad.price,
                "link": ad.link,
                "first_seen": ad.first_seen,
                "ad_id": ad.ad_id,
            }
            for ad in recent_ads_result.scalars().all()
        ]

        return templates.TemplateResponse(
            request=request,
            name="dashboard.html",
            context={
                "uptime_str": uptime_str,
                "pid": pid,
                "db_ok": db_ok,
                "worker_online": worker_online,
                "worker_last_seen_str": worker_last_seen_str,
                "cpu": cpu,
                "memory_percent": mem.percent,
                "memory_used_gb": round(mem.used / (1024 ** 3), 1),
                "memory_total_gb": round(mem.total / (1024 ** 3), 1),
                "disk_percent": disk.percent,
                "disk_used_gb": round(disk.used / (1024 ** 3), 1),
                "disk_total_gb": round(disk.total / (1024 ** 3), 1),
                "total_searches": total_searches,
                "active_searches": active_searches,
                "paused_searches": paused_searches,
                "total_ads": total_ads,
                "ads_24h": ads_24h,
                "ads_per_day": ads_per_day,
                "total_users": total_users,
                "active_proxies": active_proxies,
                "total_proxies": total_proxies,
                "proxy_list": proxy_list,
                "tokens_spent": tokens_spent,
                "tokens_24h": tokens_24h,
                "webhook_ok": webhook_ok,
                "webhook_fail": webhook_fail,
                "top_searches": top_searches_dict,
                "price_min": price_min,
                "price_max": price_max,
                "price_avg": price_avg,
                "price_count": price_count,
                "searches_with_counts": searches_dict,
                "recent_ads": recent_ads_dict,
                "now": now,
                "error": None
            }
        )

    except Exception as exc:
        import traceback
        traceback.print_exc()
        return templates.TemplateResponse(
            request=request,
            name="dashboard.html",
            context={
                "error": str(exc),
                "uptime_str": "—",
                "pid": "—",
                "db_ok": False,
                "worker_online": False,
                "worker_last_seen_str": None,
                "cpu": 0,
                "memory_percent": 0,
                "memory_used_gb": 0,
                "memory_total_gb": 0,
                "disk_percent": 0,
                "disk_used_gb": 0,
                "disk_total_gb": 0,
                "total_searches": 0,
                "active_searches": 0,
                "paused_searches": 0,
                "total_ads": 0,
                "ads_24h": 0,
                "ads_per_day": [],
                "total_users": 0,
                "active_proxies": 0,
                "total_proxies": 0,
                "proxy_list": [],
                "tokens_spent": 0,
                "tokens_24h": 0,
                "webhook_ok": 0,
                "webhook_fail": 0,
                "top_searches": [],
                "price_min": None,
                "price_max": None,
                "price_avg": None,
                "price_count": 0,
                "searches_with_counts": [],
                "recent_ads": [],
                "now": datetime.utcnow()
            }
        )
