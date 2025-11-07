import { describe, it, expect, vi, beforeEach } from "vitest";
import { api, onResponseError } from "../api";
import * as auth from "../auth";
import * as nav from "../../lib/navigation";
import { useAuthStore } from "../../store/auth";

describe("axios 401 interceptor", () => {
  beforeEach(() => {
    useAuthStore.setState({ user: { id: "u", email: "u@test" } });
  });

  it("refreshes then retries request", async () => {
    vi.spyOn(auth, "refresh").mockResolvedValue({ ok: true } as any);
    const reqSpy = vi.spyOn(api, "request").mockResolvedValue({ data: { ok: true } } as any);
    const err = { response: { status: 401 }, config: {} } as any;

    const result = await onResponseError(err).catch(() => undefined);

    expect(auth.refresh).toHaveBeenCalledTimes(1);
    expect(reqSpy).toHaveBeenCalledTimes(1);
    expect(result).toEqual({ data: { ok: true } });
  });

  it("logs out and redirects to /login if refresh fails", async () => {
    vi.spyOn(auth, "refresh").mockRejectedValue(new Error("fail"));
    const logoutSpy = vi.spyOn(useAuthStore.getState(), "logout");
    const navSpy = vi.spyOn(nav, "navigate").mockImplementation(() => {});
    const err = { response: { status: 401 }, config: {} } as any;

    await onResponseError(err).catch(() => undefined);

    expect(logoutSpy).toHaveBeenCalledTimes(1);
    expect(navSpy).toHaveBeenCalledWith("/login");
  });
});
