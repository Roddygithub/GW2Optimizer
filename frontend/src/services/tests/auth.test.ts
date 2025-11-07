import { describe, it, expect, vi } from "vitest";
import { api } from "../api";
import * as auth from "../auth";

describe("auth service", () => {
  it("POST /auth/login", async () => {
    const spy = vi.spyOn(api, "post").mockResolvedValue({ data: { ok: true } } as any);
    const res = await auth.login("a@b.com", "x");
    expect(spy).toHaveBeenCalledWith("/auth/login", { email: "a@b.com", password: "x" });
    expect(res.ok).toBe(true);
  });

  it("POST /auth/logout", async () => {
    const spy = vi.spyOn(api, "post").mockResolvedValue({ data: { ok: true } } as any);
    const res = await auth.logout();
    expect(spy).toHaveBeenCalledWith("/auth/logout");
    expect(res.ok).toBe(true);
  });
});
