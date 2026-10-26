import { describe, expect, it } from "vitest";
import { ApiError, unwrap } from "./client";

const problem = { type: "about:blank", title: "Conflict", status: 409, code: "PRECONDITIONS_UNMET",
  detail: "لا يمكن إرسال الدرجة بعد.", errors: [], missing: [{ item: "final_report" }] };

describe("API errors (API 1)", () => {
  it("keeps the server's message when the typed client has already read the body", async () => {
    const response = new Response(JSON.stringify(problem), { status: 409, statusText: "Conflict" });
    await response.text(); // openapi-fetch reads error bodies itself
    const error = await unwrap(Promise.resolve({ error: problem, response })).catch((e: unknown) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).detail).toBe(problem.detail);
    expect((error as ApiError).code).toBe("PRECONDITIONS_UNMET");
    expect((error as ApiError).extra.missing).toEqual(problem.missing);
  });
});
