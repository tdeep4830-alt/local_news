import { describe, it, expect, vi, beforeEach, afterEach } from "vitest"

// Dynamically import so we can control localStorage before the module loads
let apiFetch

beforeEach(async () => {
  vi.resetModules()
  // Reset localStorage
  localStorage.clear()
  // Re-import fresh module
  const mod = await import("../src/api/client.js")
  apiFetch = mod.apiFetch
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe("apiFetch", () => {
  it("adds Authorization header when token is in localStorage", async () => {
    localStorage.setItem("access_token", "my-test-token")
    const mockFetch = vi.fn().mockResolvedValue({ status: 200 })
    vi.stubGlobal("fetch", mockFetch)

    await apiFetch("/api/news")

    const [, options] = mockFetch.mock.calls[0]
    expect(options.headers["Authorization"]).toBe("Bearer my-test-token")
  })

  it("does not add Authorization header when no token", async () => {
    const mockFetch = vi.fn().mockResolvedValue({ status: 200 })
    vi.stubGlobal("fetch", mockFetch)

    await apiFetch("/api/news")

    const [, options] = mockFetch.mock.calls[0]
    expect(options.headers["Authorization"]).toBeUndefined()
  })

  it("builds the correct full URL", async () => {
    const mockFetch = vi.fn().mockResolvedValue({ status: 200 })
    vi.stubGlobal("fetch", mockFetch)

    await apiFetch("/api/news/1")

    const [url] = mockFetch.mock.calls[0]
    expect(url).toBe("http://localhost:8001/api/news/1")
  })

  it("returns the response on success", async () => {
    const fakeResponse = { status: 200, json: async () => [] }
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(fakeResponse))

    const res = await apiFetch("/api/news")
    expect(res).toBe(fakeResponse)
  })

  it("removes token and redirects on 401", async () => {
    localStorage.setItem("access_token", "expired-token")
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ status: 401 }))

    // jsdom doesn't support location.href assignment — spy on it
    const hrefSetter = vi.fn()
    vi.spyOn(window, "location", "get").mockReturnValue({
      ...window.location,
      set href(val) { hrefSetter(val) },
    })

    const result = await apiFetch("/api/news")

    expect(localStorage.getItem("access_token")).toBeNull()
    expect(hrefSetter).toHaveBeenCalledWith("/login")
    expect(result).toBeUndefined()
  })

  it("passes extra options (method, body) to fetch", async () => {
    const mockFetch = vi.fn().mockResolvedValue({ status: 200 })
    vi.stubGlobal("fetch", mockFetch)

    await apiFetch("/api/news/1", { method: "PUT", body: JSON.stringify({ title: "x" }) })

    const [, options] = mockFetch.mock.calls[0]
    expect(options.method).toBe("PUT")
    expect(options.body).toBe(JSON.stringify({ title: "x" }))
  })
})
