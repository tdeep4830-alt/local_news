import { describe, it, expect, vi, beforeEach, afterEach } from "vitest"
import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Routes, Route } from "react-router-dom"
import LoginPage from "../src/pages/LoginPage"

function renderLoginPage() {
  return render(
    <MemoryRouter initialEntries={["/login"]}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/" element={<div>Dashboard</div>} />
      </Routes>
    </MemoryRouter>
  )
}

beforeEach(() => {
  localStorage.clear()
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe("LoginPage", () => {
  it("renders username, password inputs and submit button", () => {
    renderLoginPage()
    expect(screen.getByLabelText("用戶名")).toBeInTheDocument()
    expect(screen.getByLabelText("密碼")).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "登入" })).toBeInTheDocument()
  })

  it("stores token and navigates to / on successful login", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ access_token: "fake-jwt", token_type: "bearer" }),
      })
    )

    renderLoginPage()
    await userEvent.type(screen.getByLabelText("用戶名"), "admin")
    await userEvent.type(screen.getByLabelText("密碼"), "testpass")
    await userEvent.click(screen.getByRole("button", { name: "登入" }))

    await waitFor(() => {
      expect(localStorage.getItem("access_token")).toBe("fake-jwt")
      expect(screen.getByText("Dashboard")).toBeInTheDocument()
    })
  })

  it("shows error message on failed login", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        json: async () => ({ detail: "用戶名或密碼錯誤" }),
      })
    )

    renderLoginPage()
    await userEvent.type(screen.getByLabelText("用戶名"), "admin")
    await userEvent.type(screen.getByLabelText("密碼"), "wrongpass")
    await userEvent.click(screen.getByRole("button", { name: "登入" }))

    await waitFor(() => {
      expect(screen.getByText("用戶名或密碼錯誤")).toBeInTheDocument()
    })
    expect(localStorage.getItem("access_token")).toBeNull()
  })

  it("shows generic error on network failure", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("Network error")))

    renderLoginPage()
    await userEvent.type(screen.getByLabelText("用戶名"), "admin")
    await userEvent.type(screen.getByLabelText("密碼"), "pass")
    await userEvent.click(screen.getByRole("button", { name: "登入" }))

    await waitFor(() => {
      expect(screen.getByText("連線錯誤，請稍後再試")).toBeInTheDocument()
    })
  })

  it("disables button while submitting", async () => {
    let resolveLogin
    vi.stubGlobal(
      "fetch",
      vi.fn().mockReturnValue(
        new Promise((res) => { resolveLogin = res })
      )
    )

    renderLoginPage()
    await userEvent.type(screen.getByLabelText("用戶名"), "admin")
    await userEvent.type(screen.getByLabelText("密碼"), "pass")
    await userEvent.click(screen.getByRole("button", { name: "登入" }))

    expect(screen.getByRole("button", { name: "登入中..." })).toBeDisabled()

    // Resolve to avoid hanging
    resolveLogin({ ok: false, json: async () => ({ detail: "err" }) })
  })
})
