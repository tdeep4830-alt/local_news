import { BrowserRouter, Routes, Route, useNavigate } from "react-router-dom"
import { SidebarProvider, SidebarInset, SidebarTrigger } from "@/components/ui/sidebar"
import { AppSidebar } from "@/layer/app-sidebar"
import { NewsTable } from "@/layer/news_table"
import { EditNewsFormWrapper } from "./pages/EditNewsPage"
import ProtectedRoute from "@/components/ProtectedRoute"
import LoginPage from "@/pages/LoginPage"
import { Button } from "@/components/ui/button"

function LogoutButton() {
  const navigate = useNavigate()
  const handleLogout = () => {
    localStorage.removeItem("access_token")
    navigate("/login")
  }
  return (
    <Button variant="outline" size="sm" onClick={handleLogout}>
      登出
    </Button>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/*" element={
          <ProtectedRoute>
            <SidebarProvider>
              <AppSidebar />
              <SidebarInset style={{ marginLeft: "var(--sidebar-width)" }} className="flex-1 w-full">
                <header className="flex h-16 shrink-0 items-center gap-2 border-b px-4 bg-white">
                  <SidebarTrigger />
                  <span className="text-slate-300">|</span>
                  <h1 className="text-lg font-semibold flex-1">新聞管理後台</h1>
                  <LogoutButton />
                </header>

                <div className="p-6">
                  <Routes>
                    <Route path="/" element={<NewsTable />} />
                    <Route path="/news" element={<NewsTable />} />
                    <Route path="/edit/:newsId" element={<EditNewsFormWrapper />} />
                  </Routes>
                </div>
              </SidebarInset>
            </SidebarProvider>
          </ProtectedRoute>
        } />
      </Routes>
    </BrowserRouter>
  )
}
