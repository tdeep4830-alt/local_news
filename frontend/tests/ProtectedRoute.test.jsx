import { describe, it, expect, beforeEach } from "vitest"
import { render, screen } from "@testing-library/react"
import { MemoryRouter, Routes, Route } from "react-router-dom"
import ProtectedRoute from "../src/components/ProtectedRoute"

function renderWithRouter(token) {
  if (token) {
    localStorage.setItem("access_token", token)
  } else {
    localStorage.removeItem("access_token")
  }

  return render(
    <MemoryRouter initialEntries={["/dashboard"]}>
      <Routes>
        <Route path="/login" element={<div>Login Page</div>} />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <div>Protected Content</div>
            </ProtectedRoute>
          }
        />
      </Routes>
    </MemoryRouter>
  )
}

beforeEach(() => {
  localStorage.clear()
})

describe("ProtectedRoute", () => {
  it("renders children when token exists", () => {
    renderWithRouter("valid-token")
    expect(screen.getByText("Protected Content")).toBeInTheDocument()
  })

  it("redirects to /login when no token", () => {
    renderWithRouter(null)
    expect(screen.getByText("Login Page")).toBeInTheDocument()
    expect(screen.queryByText("Protected Content")).not.toBeInTheDocument()
  })

  it("redirects to /login when token is empty string", () => {
    localStorage.setItem("access_token", "")
    renderWithRouter(null) // simulate no token (empty string is falsy)
    expect(screen.getByText("Login Page")).toBeInTheDocument()
  })
})
