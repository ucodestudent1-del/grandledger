// Mock Response constructor for tests
if (typeof globalThis.Response === "undefined") {
  globalThis.Response = function (body, init) {
    this.body = body
    this.status = (init && init.status) || 200
    this.headers = (init && init.headers) || new Headers()
    this.ok = this.status >= 200 && this.status < 300
  }

  globalThis.Response.prototype.json = async function () {
    if (typeof this.body === "string") {
      return JSON.parse(this.body)
    }
    return this.body
  }

  globalThis.Response.prototype.text = async function () {
    if (typeof this.body === "string") {
      return this.body
    }
    return ""
  }
}
