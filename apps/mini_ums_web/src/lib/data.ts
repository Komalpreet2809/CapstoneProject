import "server-only";
import { cacheLife } from "next/cache";
import { connection } from "next/server";
import { cache } from "react";
import { api } from "./api";
import { asStudent } from "./session";
import type {
  Announcement,
  Assignment,
  CampusEvent,
  Course,
  DemoAccount,
  Fees,
  MenuCatalogue,
  Message,
  News,
  PlacementDrive,
  RmsCatalogue,
  StudentProfile,
  TicketDetail,
  TicketHistory,
} from "./types";

// --- the signed-in student (deduplicated within one request) --------------------------------

export const getProfile = cache(() => asStudent<StudentProfile>("/me"));
export const getCourses = cache(() => asStudent<Course[]>("/me/courses"));
export const getFees = () => asStudent<Fees>("/me/fees");
export const getPendingAssignments = () =>
  asStudent<Assignment[]>("/me/assignments?status=pending");
export const getMessages = (limit = 5) => asStudent<Message[]>(`/me/messages?limit=${limit}`);
export const getPendingDrives = () =>
  asStudent<PlacementDrive[]>("/me/placement-drives?pending_only=true");
export const getPlacementDrives = () => asStudent<PlacementDrive[]>("/me/placement-drives");
export const getTicketHistory = () => asStudent<TicketHistory>("/me/tickets");
export const getTicket = (number: string) => asStudent<TicketDetail>(`/me/tickets/${number}`);

// --- public data ----------------------------------------------------------------------------
// The API isn't running at build time, so every read waits for a request (`connection()`)
// rather than being baked into the prerendered shell.

export async function getMenu() {
  await connection();
  return cachedMenu();
}

async function cachedMenu() {
  "use cache";
  cacheLife("hours");
  return api<MenuCatalogue>("/catalogue/menu");
}

export async function getRmsCatalogue() {
  await connection();
  return cachedRms();
}

async function cachedRms() {
  "use cache";
  cacheLife("hours");
  return api<RmsCatalogue>("/catalogue/rms");
}

export const getAnnouncements = cache(async () => {
  await connection();
  return api<Announcement[]>("/content/announcements");
});

export async function getNews() {
  await connection();
  return api<News[]>("/content/news?limit=5");
}

export async function getEvents() {
  await connection();
  return api<CampusEvent[]>("/content/events?limit=5");
}

/** Demo personas for the login page. The API only serves them when ENVIRONMENT=dev. */
export async function getDemoAccounts(): Promise<DemoAccount[]> {
  await connection();
  return api<DemoAccount[]>("/dev/demo-accounts").catch(() => []);
}
