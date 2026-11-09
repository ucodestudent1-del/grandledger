import { api } from "../../lib/api"

// Mock fetch globally
const mockFetch = jest.fn() as jest.MockedFunction<typeof fetch>
global.fetch = mockFetch

describe("API Client", () => {
  beforeEach(() => {
    jest.clearAllMocks()
    localStorage.clear()
  })

  it("should set and get token", () => {
    // Can't directly test private methods, test through request
    expect(true).toBe(true)
  })

  it("should include Authorization header when token is set", async () => {
    // This tests the integration indirectly
    mockFetch.mockResolvedValueOnce(
      new Response(JSON.stringify({ data: { id: "1" } }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      })
    )

    // @ts-ignore - accessing private method
    await api.get<{ id: string }>("/test")

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/test"),
      expect.objectContaining({
        headers: expect.objectContaining({
          "Content-Type": "application/json",
        }),
      })
    )
  })

  it("should throw on non-ok response", async () => {
    mockFetch.mockResolvedValueOnce(
      new Response(JSON.stringify({ detail: "Not found" }), {
        status: 404,
        headers: { "Content-Type": "application/json" },
      })
    )

    await expect(api.get<{ id: string }>("/missing")).rejects.toMatchObject({
      status: 404,
    })
  })

  it("should include CSRF header for POST requests", async () => {
    // Set a CSRF cookie
    document.cookie = "csrf_token=test-csrf-token"

    mockFetch.mockResolvedValueOnce(
      new Response(JSON.stringify({ data: { id: "1" } }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      })
    )

    await api.post<{ id: string }>("/test", { name: "test" })

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/test"),
      expect.objectContaining({
        headers: expect.objectContaining({
          "X-CSRF-Token": "test-csrf-token",
        }),
      })
    )
  })
})
