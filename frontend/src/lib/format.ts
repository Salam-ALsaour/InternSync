/** Dates as DD/MM/YYYY HH:mm in Asia/Riyadh with Western digits in both languages (NFR-L10N-02). */
const DATE_TIME = new Intl.DateTimeFormat("en-GB", {
  timeZone: "Asia/Riyadh",
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
  hourCycle: "h23",
});
const DATE = new Intl.DateTimeFormat("en-GB", {
  timeZone: "Asia/Riyadh",
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
});

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "—";
  return DATE_TIME.format(new Date(value)).replace(",", "");
}

/** A calendar date from the API (YYYY-MM-DD) shown as DD/MM/YYYY without a time-zone shift. */
export function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  if (/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    const [y, m, d] = value.split("-");
    return `${d}/${m}/${y}`;
  }
  return DATE.format(new Date(value));
}

/** The value for an <input type="datetime-local"> in Riyadh time, from an ISO instant. */
export function toRiyadhInput(value: string | null | undefined): string {
  if (!value) return "";
  const parts = Object.fromEntries(
    new Intl.DateTimeFormat("en-GB", {
      timeZone: "Asia/Riyadh",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      hourCycle: "h23",
    })
      .formatToParts(new Date(value))
      .map((p) => [p.type, p.value]),
  );
  return `${parts.year}-${parts.month}-${parts.day}T${parts.hour}:${parts.minute}`;
}

/** An ISO instant from a datetime-local value entered in Riyadh time (UTC+3, no daylight saving). */
export function fromRiyadhInput(value: string): string {
  return new Date(`${value}:00+03:00`).toISOString();
}

/** Pick the name in the interface language. */
export function nameOf(x: { name_en: string; name_ar: string } | null | undefined, lang: string): string {
  if (!x) return "—";
  return lang === "en" ? x.name_en : x.name_ar;
}
