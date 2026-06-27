import { Router, type IRouter, type Request, type Response } from "express";
import { eq, count } from "drizzle-orm";
import { db, proxiesTable } from "@workspace/db";
import {
  CreateProxyBody,
  UpdateProxyBody,
  GetProxyParams,
  UpdateProxyParams,
  DeleteProxyParams,
  ToggleProxyParams,
} from "@workspace/api-zod";
import { requireAdmin, type AdminJwtPayload } from "../middlewares/adminAuth";

const router: IRouter = Router();

router.use(requireAdmin);

router.get("/admin/proxies/stats", async (_req: Request, res: Response): Promise<void> => {
  const rows = await db.select().from(proxiesTable);
  const total = rows.length;
  const enabled = rows.filter((r) => r.enabled).length;
  res.json({ total, enabled, disabled: total - enabled });
});

router.get("/admin/proxies", async (_req: Request, res: Response): Promise<void> => {
  const proxies = await db.select().from(proxiesTable).orderBy(proxiesTable.createdAt);
  res.json(proxies);
});

router.post("/admin/proxies", async (req: Request, res: Response): Promise<void> => {
  const parsed = CreateProxyBody.safeParse(req.body);
  if (!parsed.success) {
    res.status(400).json({ error: parsed.error.message });
    return;
  }

  const { host, port, protocol, username, password, label, enabled } = parsed.data;
  const [proxy] = await db
    .insert(proxiesTable)
    .values({
      host,
      port,
      protocol,
      username: username ?? null,
      password: password ?? null,
      label: label ?? null,
      enabled: enabled ?? true,
    })
    .returning();

  req.log.info({ proxyId: proxy.id }, "Proxy created");
  res.status(201).json(proxy);
});

router.get("/admin/proxies/:id", async (req: Request, res: Response): Promise<void> => {
  const params = GetProxyParams.safeParse(req.params);
  if (!params.success) {
    res.status(400).json({ error: params.error.message });
    return;
  }
  const [proxy] = await db.select().from(proxiesTable).where(eq(proxiesTable.id, params.data.id));
  if (!proxy) {
    res.status(404).json({ error: "Proxy not found" });
    return;
  }
  res.json(proxy);
});

router.patch("/admin/proxies/:id", async (req: Request, res: Response): Promise<void> => {
  const params = UpdateProxyParams.safeParse(req.params);
  if (!params.success) {
    res.status(400).json({ error: params.error.message });
    return;
  }
  const parsed = UpdateProxyBody.safeParse(req.body);
  if (!parsed.success) {
    res.status(400).json({ error: parsed.error.message });
    return;
  }

  const updates: Partial<typeof proxiesTable.$inferInsert> = {};
  if (parsed.data.host !== undefined) updates.host = parsed.data.host;
  if (parsed.data.port !== undefined) updates.port = parsed.data.port;
  if (parsed.data.protocol !== undefined) updates.protocol = parsed.data.protocol;
  if (parsed.data.username !== undefined) updates.username = parsed.data.username;
  if (parsed.data.password !== undefined) updates.password = parsed.data.password;
  if (parsed.data.label !== undefined) updates.label = parsed.data.label;
  if (parsed.data.enabled !== undefined) updates.enabled = parsed.data.enabled;

  const [proxy] = await db
    .update(proxiesTable)
    .set(updates)
    .where(eq(proxiesTable.id, params.data.id))
    .returning();

  if (!proxy) {
    res.status(404).json({ error: "Proxy not found" });
    return;
  }
  res.json(proxy);
});

router.delete("/admin/proxies/:id", async (req: Request, res: Response): Promise<void> => {
  const params = DeleteProxyParams.safeParse(req.params);
  if (!params.success) {
    res.status(400).json({ error: params.error.message });
    return;
  }
  const [proxy] = await db.delete(proxiesTable).where(eq(proxiesTable.id, params.data.id)).returning();
  if (!proxy) {
    res.status(404).json({ error: "Proxy not found" });
    return;
  }
  req.log.info({ proxyId: params.data.id }, "Proxy deleted");
  res.sendStatus(204);
});

router.post("/admin/proxies/:id/toggle", async (req: Request, res: Response): Promise<void> => {
  const params = ToggleProxyParams.safeParse(req.params);
  if (!params.success) {
    res.status(400).json({ error: params.error.message });
    return;
  }
  const [existing] = await db.select().from(proxiesTable).where(eq(proxiesTable.id, params.data.id));
  if (!existing) {
    res.status(404).json({ error: "Proxy not found" });
    return;
  }
  const [proxy] = await db
    .update(proxiesTable)
    .set({ enabled: !existing.enabled })
    .where(eq(proxiesTable.id, params.data.id))
    .returning();
  req.log.info({ proxyId: proxy.id, enabled: proxy.enabled }, "Proxy toggled");
  res.json(proxy);
});

export default router;
