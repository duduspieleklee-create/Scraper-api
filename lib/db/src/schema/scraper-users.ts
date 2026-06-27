import { pgTable, text, serial, timestamp, integer } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod/v4";

export const scraperUsersTable = pgTable("scraper_users", {
  id: serial("id").primaryKey(),
  email: text("email").notNull().unique(),
  tokenBalance: integer("token_balance").notNull().default(20),
  externalId: text("external_id"),
  notes: text("notes"),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
  updatedAt: timestamp("updated_at", { withTimezone: true }).notNull().defaultNow().$onUpdate(() => new Date()),
});

export const insertScraperUserSchema = createInsertSchema(scraperUsersTable).omit({ id: true, createdAt: true, updatedAt: true });
export type InsertScraperUser = z.infer<typeof insertScraperUserSchema>;
export type ScraperUser = typeof scraperUsersTable.$inferSelect;
