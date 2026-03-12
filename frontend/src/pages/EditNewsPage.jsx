// src/pages/EditNewsPage.jsx
import { useParams, useNavigate } from "react-router-dom"
import { EditNewsForm } from "@/layer/user-form"
import { Button } from "@/components/ui/button"

export function EditNewsFormWrapper() {
  const { newsId } = useParams() // 從 URL 攞到 :newsId
  const navigate = useNavigate()

  return (
    <div className="space-y-4">
      <Button variant="outline" onClick={() => navigate("/news")}>
        ← 返回列表
      </Button>
      <EditNewsForm newsId={newsId} />尸
    </div>
  )
}