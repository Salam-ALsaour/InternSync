/** Offline mode (AT-PWA-03 as changed by CR-10): what the saved copy keeps and leaves out, when it is deleted, the
 *  idle limit, and the drafts kept on the device. */
import { QueryClient } from "@tanstack/react-query";
import { describe, expect, it } from "vitest";
import {
  ACTIVITY_KEY, clearCopy, clearDrafts, draftKey, DRAFT_DAYS, idleFor, ME_KEY, pruneDrafts, readDraft, removeDraft,
  restoreCopy, same, SAVED_KEY, saveCopy, saveMe, savedMe, touch, writeDraft,
} from "./offline";

class Memory {
  private data = new Map<string, string>();
  get length() { return this.data.size; }
  key(i: number) { return [...this.data.keys()][i] ?? null; }
  getItem(k: string) { return this.data.get(k) ?? null; }
  setItem(k: string, v: string) { this.data.set(k, v); }
  removeItem(k: string) { this.data.delete(k); }
}

function filled(): QueryClient {
  const client = new QueryClient();
  client.setQueryData(["slot", "s1"], { id: "s1", status: "draft" });
  client.setQueryData(["dashboard"], { items: [] });
  client.setQueryData(["audit", {}], { items: [{ id: 1 }] });
  client.setQueryData(["notifications", "unread"], { unread_count: 3 });
  return client;
}

describe("saved copy", () => {
  it("keeps the pages shown, never the audit log or the notifications", () => {
    const store = new Memory();
    saveCopy(filled(), "u1", store);
    const fresh = new QueryClient();
    expect(restoreCopy(fresh, "u1", store)).toBe(true);
    expect(fresh.getQueryData(["slot", "s1"])).toEqual({ id: "s1", status: "draft" });
    expect(fresh.getQueryData(["dashboard"])).toEqual({ items: [] });
    expect(fresh.getQueryData(["audit", {}])).toBeUndefined();
    expect(fresh.getQueryData(["notifications", "unread"])).toBeUndefined();
  });

  it("is never shown to another user, and that user's sign-in deletes it", () => {
    const store = new Memory();
    saveCopy(filled(), "u1", store);
    const other = new QueryClient();
    expect(restoreCopy(other, "u2", store)).toBe(false);
    expect(other.getQueryData(["slot", "s1"])).toBeUndefined();
    expect(store.getItem(SAVED_KEY)).toBeNull();
  });

  it("is deleted with the saved user and the activity time at sign-out", () => {
    const store = new Memory();
    saveCopy(filled(), "u1", store);
    saveMe({ id: "u1" }, store);
    touch(store);
    clearCopy(store);
    for (const key of [SAVED_KEY, ME_KEY, ACTIVITY_KEY]) expect(store.getItem(key)).toBeNull();
    expect(savedMe(store)).toBeNull();
  });
});

describe("idle limit (FR-AUT-03)", () => {
  it("counts from the last key, click, or touch", () => {
    const store = new Memory();
    expect(idleFor(store, 1_000)).toBe(0);
    touch(store, 1_000);
    expect(idleFor(store, 1_000 + 31 * 60_000)).toBe(31 * 60_000);
  });
});

describe("drafts on the device", () => {
  const key = draftKey("u1", "report", "s1");

  it("keep the text and the server draft it started from", () => {
    const store = new Memory();
    writeDraft(key, { learning: "offline text" }, { learning: "" }, store, 0);
    expect(readDraft(key, store, 1)).toEqual({ values: { learning: "offline text" }, base: { learning: "" }, at: 0 });
    removeDraft(key, store);
    expect(readDraft(key, store, 1)).toBeNull();
  });

  it(`expire after ${DRAFT_DAYS} days`, () => {
    const store = new Memory();
    writeDraft(key, { learning: "x" }, { learning: "" }, store, 0);
    writeDraft(draftKey("u1", "report", "s2"), { learning: "y" }, { learning: "" }, store, 6 * 86_400_000);
    pruneDrafts(store, 7 * 86_400_000 + 1);
    expect(store.getItem(key)).toBeNull();
    expect(store.length).toBe(1);
  });

  it("are all deleted at sign-out, other keys stay", () => {
    const store = new Memory();
    writeDraft(key, { a: 1 }, { a: 0 }, store);
    writeDraft(draftKey("u2", "evaluation-final", "p1"), { a: 1 }, { a: 0 }, store);
    store.setItem("internsync.lang", "ar");
    clearDrafts(store);
    expect(store.length).toBe(1);
    expect(store.getItem("internsync.lang")).toBe("ar");
  });

  it("compare content whatever the order of the keys", () => {
    expect(same({ a: 1, b: { c: 2, d: 3 } }, { b: { d: 3, c: 2 }, a: 1 })).toBe(true);
    expect(same({ a: 1 }, { a: 2 })).toBe(false);
  });
});
