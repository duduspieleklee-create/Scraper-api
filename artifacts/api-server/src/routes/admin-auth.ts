import { Router, type IRouter, type Request, type Response } from "express";
import bcrypt from "bcryptjs";
import { eq } from "drizzle-orm";
import { db, adminUsersTable } from "@workspace/db";
import { AdminLoginBody } from "@workspace/api-zod";
import { requireAdmin, signAdminToken, type AdminJwtPayload } from "../middlewares/adminAuth";
import { logger } from "../lib/logger";

const router: IRouter = Router();

router.post("/admin/login", async (req: Request, res: Response): Promise<void> => {
  const parsed = AdminLoginBody.safeParse(req.body);
  if (!parsed.success) {
    res.status(400).json({ error: parsed.error.message });
    return;
  }

  const { username, password } = parsed.data;
  const [user] = await db.select().from(adminUsersTable).where(eq(adminUsersTable.username, username));

  if (!user) {
    res.status(401).json({ error: "Invalid credentials" });
    return;
  }

  const valid = await bcrypt.compare(password, user.passwordHash);
  if (!valid) {
    res.status(401).json({ error: "Invalid credentials" });
    return;
  }

  const token = signAdminToken({ adminId: user.id, username: user.username });
  req.log.info({ username }, "Admin logged in");
  res.json({ token, username: user.username });
});

router.get("/admin/me", requireAdmin, async (req: Request, res: Response): Promise<void> => {
  const admin = (req as Request & { admin: AdminJwtPayload }).admin;
  const [user] = await db.select().from(adminUsersTable).where(eq(adminUsersTable.id, admin.adminId));
  if (!user) {
    res.status(401).json({ error: "Admin not found" });
    return;
  }
  res.json({ id: user.id, username: user.username, createdAt: user.createdAt });
});

export default router;
