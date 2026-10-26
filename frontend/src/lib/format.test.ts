import { describe, expect, it } from "vitest";
import { formatDate, formatDateTime, fromRiyadhInput, toRiyadhInput } from "./format";

describe("date format (NFR-L10N-02)", () => {
  it("shows Riyadh time as DD/MM/YYYY HH:mm with Western digits", () => {
    expect(formatDateTime("2026-10-29T20:59:00Z")).toBe("29/10/2026 23:59");
  });
  it("keeps calendar dates unshifted", () => {
    expect(formatDate("2026-10-25")).toBe("25/10/2026");
  });
  it("round-trips datetime-local values in Riyadh time", () => {
    expect(toRiyadhInput("2026-10-29T20:59:00Z")).toBe("2026-10-29T23:59");
    expect(fromRiyadhInput("2026-10-29T23:59")).toBe("2026-10-29T20:59:00.000Z");
  });
});
