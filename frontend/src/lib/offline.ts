/** Offline mode (FR-PWA-03 as changed by CR-10; Increment 4 design, Section 8).
 *  - The saved copy: the API answers shown in this window, kept in session storage, so pages opened earlier stay
 *    readable offline. It ends with the window, at sign-out, and at the idle limit.
 *  - Offline drafts: text typed into a report or an evaluation is kept in local storage under the user's ID until
 *    it is saved to the server, for 7 days at most, and is deleted at sign-out.
 *  Submitting and every other change still need the connection. */
import { type DehydratedState, dehydrate, hydrate, type Query, type QueryClient } from "@tanstack/react-query";
import { useCallback, useEffect, useRef, useState } from "react";
import { useOnline } from "./online";

export const SAVED_KEY = "internsync.saved";
export const ME_KEY = "internsync.me";
export const ACTIVITY_KEY = "internsync.activity";
export const DRAFT_PREFIX = "internsync.draft.";
export const DRAFT_DAYS = 7;
/** Never kept on the device: the audit log and the notification count. Files and exports are not queries. */
export const NEVER_SAVED = new Set(["audit", "audit-students", "notifications"]);

type Store = Pick<Storage, "getItem" | "setItem" | "removeItem" | "key" | "length">;

function session(): Store | null {
  try {
    return window.sessionStorage;
  } catch {
    return null;
  }
}

function local(): Store | null {
  try {
    return window.localStorage;
  } catch {
    return null;
  }
}

function read<T>(store: Store | null, key: string): T | null {
  try {
    const raw = store?.getItem(key);
    return raw ? (JSON.parse(raw) as T) : null;
  } catch {
    return null;
  }
}

function write(store: Store | null, key: string, value: unknown): void {
  try {
    store?.setItem(key, JSON.stringify(value));
  } catch {
    /* storage full or blocked: the page still works, without the offline copy */
  }
}

function remove(store: Store | null, key: string): void {
  try {
    store?.removeItem(key);
  } catch {
    /* nothing to remove */
  }
}

// ---------------------------------------------------------------- the saved copy
export function shouldSave(q: Pick<Query, "queryKey" | "state">): boolean {
  return q.state.status === "success" && !NEVER_SAVED.has(String(q.queryKey[0]));
}

interface Saved {
  user: string;
  at: number;
  state: DehydratedState;
}

export function saveCopy(client: QueryClient, user: string, store: Store | null = session()): void {
  write(store, SAVED_KEY, { user, at: Date.now(), state: dehydrate(client, { shouldDehydrateQuery: shouldSave }) });
}

/** Load the saved copy of `user` into the cache; a copy of another user is deleted. */
export function restoreCopy(client: QueryClient, user: string, store: Store | null = session()): boolean {
  const saved = read<Saved>(store, SAVED_KEY);
  if (!saved) return false;
  if (saved.user !== user) {
    remove(store, SAVED_KEY);
    return false;
  }
  hydrate(client, saved.state);
  return true;
}

/** Keep the copy up to date, at most once a second and when the page is left or reloaded; `user()` is null when
 *  nothing may be saved (Platform Admin). */
export function watchCache(client: QueryClient, user: () => string | null, store: Store | null = session()): () => void {
  let timer: ReturnType<typeof setTimeout> | null = null;
  const flush = () => {
    if (timer) clearTimeout(timer);
    timer = null;
    const id = user();
    if (id) saveCopy(client, id, store);
    else remove(store, SAVED_KEY);
  };
  const unsubscribe = client.getQueryCache().subscribe(() => {
    if (!timer) timer = setTimeout(flush, 1000);
  });
  window.addEventListener("pagehide", flush);
  return () => {
    unsubscribe();
    window.removeEventListener("pagehide", flush);
  };
}

export function saveMe(me: unknown, store: Store | null = session()): void {
  write(store, ME_KEY, me);
}

export function savedMe<T>(store: Store | null = session()): T | null {
  return read<T>(store, ME_KEY);
}

export function clearCopy(store: Store | null = session()): void {
  for (const key of [SAVED_KEY, ME_KEY, ACTIVITY_KEY]) remove(store, key);
}

// ---------------------------------------------------------------- the idle limit (FR-AUT-03), also offline
export function touch(store: Store | null = session(), now = Date.now()): void {
  write(store, ACTIVITY_KEY, now);
}

export function idleFor(store: Store | null = session(), now = Date.now()): number {
  const last = read<number>(store, ACTIVITY_KEY);
  return last ? now - last : 0;
}

// ---------------------------------------------------------------- offline drafts
export interface Draft<T> {
  values: T;
  base: T;
  at: number;
}

export function draftKey(user: string, kind: string, id: string): string {
  return `${DRAFT_PREFIX}${user}.${kind}.${id}`;
}

export function readDraft<T>(key: string, store: Store | null = local(), now = Date.now()): Draft<T> | null {
  const d = read<Draft<T>>(store, key);
  if (d && now - d.at > DRAFT_DAYS * 86_400_000) {
    remove(store, key);
    return null;
  }
  return d;
}

export function writeDraft<T>(key: string, values: T, base: T, store: Store | null = local(), now = Date.now()): void {
  write(store, key, { values, base, at: now });
}

export function removeDraft(key: string, store: Store | null = local()): void {
  remove(store, key);
}

function draftKeys(store: Store | null): string[] {
  const keys: string[] = [];
  try {
    for (let i = 0; store && i < store.length; i++) {
      const k = store.key(i);
      if (k?.startsWith(DRAFT_PREFIX)) keys.push(k);
    }
  } catch {
    /* storage blocked */
  }
  return keys;
}

/** At sign-out every draft on the device is deleted. */
export function clearDrafts(store: Store | null = local()): void {
  for (const k of draftKeys(store)) remove(store, k);
}

/** Drafts older than 7 days are deleted when the app starts. */
export function pruneDrafts(store: Store | null = local(), now = Date.now()): void {
  for (const k of draftKeys(store)) readDraft(k, store, now);
}

/** Equal content, whatever the order of the keys. */
export function same(a: unknown, b: unknown): boolean {
  const norm = (x: unknown): unknown => (x && typeof x === "object" && !Array.isArray(x)
    ? Object.fromEntries(Object.keys(x as object).sort().map((k) => [k, norm((x as Record<string, unknown>)[k])]))
    : x);
  return JSON.stringify(norm(a)) === JSON.stringify(norm(b));
}

export type DraftStatus = "server" | "device" | "saving" | "conflict";

/** The values of a form whose text is kept on the device until it reaches the server. When the connection is back,
 *  the text is saved if the server's draft still equals the one the editing started from; otherwise `conflict`, and
 *  the user chooses with `keepMine` or `keepSaved`. Call `saved()` after the form saved or submitted itself. */
export function useLocalDraft<T>(key: string | null, server: T, save: (values: T) => Promise<unknown>) {
  const online = useOnline();
  const serverJson = JSON.stringify(server);
  const initial = key ? readDraft<T>(key) : null;
  const [values, setLocal] = useState<T>(initial?.values ?? server);
  const [status, setStatus] = useState<DraftStatus>(initial ? "device" : "server");
  // Text kept from an earlier visit, or typed while offline, is saved when the page is online again. Typing while
  // online is only kept on the device until the user saves, as before.
  const [syncWanted, setSyncWanted] = useState(!!initial);
  const base = useRef<T>(initial?.base ?? server);
  const saveRef = useRef(save);
  saveRef.current = save;
  const shownKey = useRef(key);

  useEffect(() => {  // another record, or the server's draft changed while nothing is kept on the device
    const d = key ? readDraft<T>(key) : null;
    if (d) {
      setLocal(d.values);
      base.current = d.base;
      setStatus((s) => (s === "conflict" ? s : "device"));
      if (shownKey.current !== key) setSyncWanted(true);
    } else {
      setLocal(JSON.parse(serverJson) as T);
      base.current = JSON.parse(serverJson) as T;
      setStatus("server");
    }
    shownKey.current = key;
  }, [key, serverJson]);

  const setValues = useCallback((next: T | ((v: T) => T)) => {
    setLocal((v) => {
      const out = typeof next === "function" ? (next as (v: T) => T)(v) : next;
      if (key) writeDraft(key, out, base.current);
      return out;
    });
    setStatus((s) => (s === "conflict" ? s : "device"));
  }, [key]);

  const saved = useCallback(() => {
    if (key) removeDraft(key);
    setStatus("server");
  }, [key]);

  const push = useCallback(async (v: T) => {
    setStatus("saving");
    try {
      await saveRef.current(v);
      if (key) removeDraft(key);
      setStatus("server");
    } catch {
      setStatus("device");
    }
  }, [key]);

  const wasOnline = useRef(online);
  useEffect(() => {
    if (online && !wasOnline.current) setSyncWanted(true);
    wasOnline.current = online;
  }, [online]);
  useEffect(() => {
    if (!syncWanted || !online || !key) return;
    setSyncWanted(false);
    if (!readDraft<T>(key)) return;
    if (same(JSON.parse(serverJson), base.current)) void push(values);
    else setStatus("conflict");
  }, [syncWanted, online, key, serverJson, values, push]);

  const keepMine = useCallback(() => void push(values), [push, values]);
  const keepSaved = useCallback(() => {
    if (key) removeDraft(key);
    setLocal(JSON.parse(serverJson) as T);
    base.current = JSON.parse(serverJson) as T;
    setStatus("server");
  }, [key, serverJson]);

  return { values, setValues, status, saved, keepMine, keepSaved };
}
