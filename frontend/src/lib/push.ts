/** Web push subscription of this browser (FR-PWA-02; Increment 3 design, Section 6). Email stays the fallback, so
 *  every failure here only means "no push". */
import { api, unwrap } from "../api/client";

export type PushState = "unsupported" | "unavailable" | "denied" | "off" | "on";

function supported(): boolean {
  return "serviceWorker" in navigator && "PushManager" in window && "Notification" in window;
}

function keyBytes(base64url: string): Uint8Array<ArrayBuffer> {
  const padded = base64url.replace(/-/g, "+").replace(/_/g, "/") + "=".repeat((4 - (base64url.length % 4)) % 4);
  const raw = atob(padded);
  const out = new Uint8Array(new ArrayBuffer(raw.length));
  for (let i = 0; i < raw.length; i++) out[i] = raw.charCodeAt(i);
  return out;
}

async function registration(): Promise<ServiceWorkerRegistration | null> {
  if (!supported()) return null;
  return (await navigator.serviceWorker.getRegistration()) ?? null;
}

export async function pushState(): Promise<PushState> {
  if (!supported()) return "unsupported";
  const reg = await registration();
  const { key } = await unwrap(api.GET("/api/v1/push/vapid-public-key"));
  if (!reg || !key) return "unavailable";  // no service worker (development) or no keys on the server
  if (Notification.permission === "denied") return "denied";
  return (await reg.pushManager.getSubscription()) ? "on" : "off";
}

export async function turnOn(): Promise<PushState> {
  const reg = await registration();
  const { key } = await unwrap(api.GET("/api/v1/push/vapid-public-key"));
  if (!reg || !key) return "unavailable";
  if ((await Notification.requestPermission()) !== "granted") return "denied";
  const sub = await reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: keyBytes(key) });
  const json = sub.toJSON();
  await unwrap(api.POST("/api/v1/push/subscriptions", { body: {
    endpoint: sub.endpoint, keys: { p256dh: json.keys?.p256dh ?? "", auth: json.keys?.auth ?? "" } } }));
  return "on";
}

export async function turnOff(): Promise<PushState> {
  const sub = await (await registration())?.pushManager.getSubscription();
  if (sub) {
    await unwrap(api.DELETE("/api/v1/push/subscriptions", { body: { endpoint: sub.endpoint } }));
    await sub.unsubscribe();
  }
  return "off";
}
