export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || ""

export interface ApiResponse<T> {
  data: T
  error?: string
}

export interface ApiError extends Error {
  status: number
  detail?: string
}

class ApiClient {
  private baseURL: string
  private token: string | null = null
  private isRefreshing = false
  private refreshSubscribers: ((token: string) => void)[] = []

  constructor(baseURL: string) {
    this.baseURL = baseURL
  }

  private buildURL(endpoint: string): string {
    if (this.baseURL) {
      return `${this.baseURL}/api/v1${endpoint}`
    }
    return `/api/v1${endpoint}`
  }

  setToken(token: string | null) {
    this.token = token
    if (token) {
      localStorage.setItem("access_token", token)
    } else {
      localStorage.removeItem("access_token")
    }
  }

  getToken(): string | null {
    if (this.token) return this.token
    if (typeof window !== "undefined") {
      return localStorage.getItem("access_token")
    }
    return null
  }

  private getHeaders(customHeaders?: HeadersInit): Record<string, string> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    }
    if (customHeaders) {
      if (customHeaders instanceof Headers) {
        customHeaders.forEach((value, key) => {
          headers[key] = value
        })
      } else if (Array.isArray(customHeaders)) {
        for (const [key, value] of customHeaders) {
          headers[key] = value
        }
      } else {
        Object.assign(headers, customHeaders)
      }
    }
    const token = this.getToken()
    if (token) {
      headers["Authorization"] = `Bearer ${token}`
    }
    return headers
  }

  private async handleResponse<T>(response: Response, endpoint: string, options: RequestInit): Promise<T> {
    if (response.status === 401) {
      const newToken = await this.handle401()
      if (newToken) {
        const retryOptions: RequestInit = {
          ...options,
          headers: { ...this.getHeaders(), ...options.headers },
        }
        const retryResponse = await fetch(this.buildURL(endpoint), retryOptions)
        if (!retryResponse.ok) {
          const error = await retryResponse.json().catch(() => ({ detail: retryResponse.statusText }))
          throw this.createError(retryResponse.status, error.detail || retryResponse.statusText)
        }
        return retryResponse.json() as Promise<T>
      }
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }))
      throw this.createError(response.status, error.detail || response.statusText)
    }

    return response.json() as Promise<T>
  }

  private async handle401(): Promise<string | null> {
    if (this.isRefreshing) {
      return new Promise((resolve) => {
        this.refreshSubscribers.push((token) => resolve(token))
      })
    }

    this.isRefreshing = true
    const refreshToken = localStorage.getItem("refresh_token")

    if (!refreshToken) {
      this.setToken(null)
      this.isRefreshing = false
      return null
    }

    try {
      const response = await fetch(this.buildURL("/auth/refresh"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
      })

      if (response.ok) {
        const data = await response.json()
        this.setToken(data.access_token)
        if (data.refresh_token) {
          localStorage.setItem("refresh_token", data.refresh_token)
        }
        this.isRefreshing = false
        this.refreshSubscribers.forEach((cb) => cb(data.access_token))
        this.refreshSubscribers = []
        return data.access_token
      }
    } catch {
      // refresh failed
    }

    this.isRefreshing = false
    this.setToken(null)
    return null
  }

  private createError(status: number, detail: string): ApiError {
    const error = new Error(detail) as ApiError
    error.status = status
    error.detail = detail
    return error
  }

  async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const response = await fetch(this.buildURL(endpoint), {
      ...options,
      headers: this.getHeaders(options.headers),
    })

    return this.handleResponse<T>(response, endpoint, options)
  }

  async get<T>(endpoint: string, params?: Record<string, string | number | undefined>): Promise<T> {
    let url = endpoint
    if (params) {
      const query = Object.entries(params)
        .filter(([_, v]) => v !== undefined)
        .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`)
        .join("&")
      if (query) url = `${endpoint}?${query}`
    }
    return this.request<T>(url, { method: "GET" })
  }

  async post<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: "POST",
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  async patch<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: "PATCH",
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: "DELETE" })
  }
}

export const api = new ApiClient(API_BASE_URL)
