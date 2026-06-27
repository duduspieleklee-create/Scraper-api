import { Router, type IRouter, type Request, type Response } from "express";
import { eq, sql } from "drizzle-orm";
import { db, scraperUsersTable } from "@workspace/db";
import {
  CreateScraperUserBody,
  GetScraperUserParams,
  DeleteScraperUserParams,
  AdjustUserTokensParams,
  AdjustUserTokensBody,
} from "@workspace/api-zod";
import { requireAdmin } from "../middlewares/adminAuth";

const router: IRouter = Router();

router.use(requireAdmin);

router.get("/admin/users", async (_req: Request, res: Response): Promise<void> => {
  const users = await db.select().from(scraperUsersTable).orderBy(scraperUsersTable.createdAt);
  res.json(users);
});

router.post("/admin/users", async (req: Request, res: Response): Promise<void> => {
  const parsed = CreateScraperUserBody.safeParse(req.body);
  if (!parsed.success) {
    res.status(400).json({ error: parsed.error.message });
    return;
  }
  const { email, tokenBalance, externalId, notes } = parsed.data;
  const [user] = await db
    .insert(scraperUsersTable)
    .values({
      email,
      tokenBalance: tokenBalance ?? 20,
      externalId: externalId ?? null,
      notes: notes ?? null,
    })
    .returning();
  req.log.info({ userId: user.id, email }, "Scraper user created");
  res.status(201).json(user);
});

router.get("/admin/users/:id", async (req: Request, res: Response): Promise<void> => {
  const params = GetScraperUserParams.safeParse(req.params);
  if (!params.success) {
    res.status(400).json({ error: params.error.message });
    return;
  }
  const [user] = await db.select().from(scraperUsersTable).where(eq(scraperUsersTable.id, params.data.id));
  if (!user) {
    res.status(404).json({ error: "User not found" });
    return;
  }
  res.json(user);
});

router.delete("/admin/users/:id", async (req: Request, res: Response): Promise<void> => {
  const params = DeleteScraperUserParams.safeParse(req.params);
  if (!params.success) {
    res.status(400).json({ error: params.error.message });
    return;
  }
  const [user] = await db.delete(scraperUsersTable).where(eq(scraperUsersTable.id, params.data.id)).returning();
  if (!user) {
    res.status(404).json({ error: "User not found" });
    return;
  }
  req.log.info({ userId: params.data.id }, "Scraper user deleted");
  res.sendStatus(204);
});

router.post("/admin/users/:id/tokens", async (req: Request, res: Response): Promise<void> => {
  const params = AdjustUserTokensParams.safeParse(req.params);
  if (!params.success) {
    res.status(400).json({ error: params.error.message });
    return;
  }
  const parsed = AdjustUserTokensBody.safeParse(req.body);
  if (!parsed.success) {
    res.status(400).json({ error: parsed.error.message });
    return;
  }

  const [existing] = await db.select().from(scraperUsersTable).where(eq(scraperUsersTable.id, params.data.id));
  if (!existing) {
    res.status(404).json({ error: "User not found" });
    return;
  }

  const newBalance = existing.tokenBalance + parsed.data.amount;
  if (newBalance < 0) {
    res.status(400).json({ error: `Insufficient token balance. Current: ${existing.tokenBalance}, adjustment: ${parsed.data.amount}` });
    return;
  }

  const [user] = await db
    .update(scraperUsersTable)
    .set({ tokenBalance: newBalance })
    .where(eq(scraperUsersTable.id, params.data.id))
    .returning();

  req.log.info({ userId: user.id, adjustment: parsed.data.amount, newBalance }, "Token balance adjusted");
  res.json(user);
});

export default router;
