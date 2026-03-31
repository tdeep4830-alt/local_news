import { useState, useEffect } from "react"
import { apiFetch } from "@/api/client"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox" // 1. 引入 Checkbox
import { Send } from "lucide-react"
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

export function EditNewsForm({ newsId }) {
  const [formData, setFormData] = useState({
    o_title: "",
    o_content: "",
    t_title: "",
    t_content: "",
    area: "",
    shortened_title: "",
    o_url: "",
    img_path: "",
    breaking: 0 // 2. 加入 breaking 初始值 (0)
  })

  const [isSaving, setIsSaving] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [loading, setLoading] = useState(true)

useEffect(() => {
  async function fetchNews() {
    try {
      const res = await apiFetch(`/api/news/${newsId}`)
      if (!res) return
      const data = await res.json()
      
      // ✅ 修正：先攞原本嘅預設值，再用 API 返嚟嘅資料覆蓋
      setFormData(prev => ({
        ...prev, 
        ...data,
        // 如果 API 返嚟係 null 或者 undefined，就俾返 0 佢
        breaking: data.breaking ?? 0 
      }))
    } catch (error) {
      console.error("Fetch error:", error)
    } finally {
      setLoading(false)
    }
  }
  fetchNews()
}, [newsId])

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value })
  }

  // 3. 處理 Checkbox 的特殊改變函數
  const handleCheckboxChange = (checked) => {
    setFormData({ ...formData, breaking: checked ? 1 : 0 })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setIsSaving(true)
    try {
      // 呢度會一次過將包含 breaking (0/1) 的 formData 傳去 Backend
      const res = await apiFetch(`/api/news/${newsId}`, {
        method: "PUT",
        body: JSON.stringify(formData),
      })
      if (res.ok) alert("✅ 資料已更新！")
    } catch (error) {
      console.error("Update failed:", error)
    } finally {
      setIsSaving(false)
    }
  }

  const handleReject = async () => {
    setIsSubmitting(true)
    try {
      const res = await apiFetch(`/api/news/reject/${newsId}`, {
        method: "POST",
      })
      if (!res) return
      if (res.ok) alert("✅ 已成功拒絕！")
    } catch (error) {
      console.error("Error rejecting:", error)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handlePostToFacebook = async () => {
    setIsSubmitting(true)
    try {
      const res = await apiFetch(`/api/social/facebook/${newsId}`, {
        method: "POST",
      })
      if (!res) return
      if (res.ok) alert("✅ 已成功發布到 Facebook！")
    } catch (error) {
      console.error("Error posting to Facebook:", error)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handlePostToInstagram = async () => {
    setIsSubmitting(true)
    try {
      const res = await apiFetch(`/api/social/instagram/${newsId}/`, {
        method: "POST",
      })
      if (!res) return
      if (res.ok) alert("✅ 已成功發布到 Facebook！")
    } catch (error) {
      console.error("Error posting to Facebook:", error)
    } finally {
      setIsSubmitting(false) 
    }
  }

  const handlePublishAll = async () => {
    // 先儲存目前的修改，確保發布的是最新內容 (非必須，但建議)
    setIsSubmitting(true)
    
    try {
      // 定義所有要執行的任務
      const tasks = [
        { name: "Google", url: `/api/social/google-doc/${newsId}`, method: "POST" },
        { name: "Facebook", url: `/api/social/facebook/${newsId}`, method: "POST" },
        { name: "Instagram", url: `/api/social/instagram/${newsId}/`, method: "POST" }
      ]

      // 同步執行所有請求
      const results = await Promise.all(
        tasks.map(task => 
          apiFetch(task.url, { method: task.method })
            .then(res => ({ name: task.name, ok: res?.ok }))
            .catch(() => ({ name: task.name, ok: false }))
        )
      )

      const failedTasks = results.filter(r => !r.ok).map(r => r.name)
      
      if (failedTasks.length === 0) {
        alert("✅ 已成功發布到所有平台 (Google, FB, IG)！")
      } else {
        alert(`⚠️ 部份發布失敗: ${failedTasks.join(", ")}，請檢查後台。`)
      }

    } catch (error) {
      console.error("Publish all failed:", error)
      alert("❌ 發布過程中發生錯誤")
    } finally {
      setIsSubmitting(false)
    }
  }

  const status = [
    { value: "PENDING", label: "待處理" },
    { value: "APPROVED", label: "已批准" },
    { value: "POSTED", label: "已發布" },
    { value: "REJECTED", label: "已拒絕" }
  ]

  if (loading) return <div>載入中...</div>

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle>修改新聞內容 (ID: {newsId})</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          
          {/* 4. Breaking News 剔格仔 */}
          <div className="flex items-center space-x-2 border p-3 rounded-md bg-slate-50">
            <Checkbox 
              id="breaking" 
              checked={formData.breaking === 1} 
              onCheckedChange={handleCheckboxChange} 
            />
            <div className="grid gap-1.5 leading-none">
              <Label htmlFor="breaking" className="text-sm font-bold text-red-600 cursor-pointer">
                🔥 Breaking News (緊急新聞)
              </Label>
              <p className="text-xs text-muted-foreground">
                剔選後，發布時會加上標籤提示。
              </p>
            </div>
          </div>

          <div className="grid gap-2">
            <Label>原文標題</Label>
            <Input name="o_title" value={formData.o_title} onChange={handleChange} />
          </div>

          <div className="grid gap-2">
            <Label>內容</Label>
            <Textarea name="t_content" value={formData.t_content} onChange={handleChange} rows={15} />
          </div>

          <div className="grid gap-2">
            <Label>翻譯標題</Label>
            <Input name="t_title" value={formData.t_title} onChange={handleChange} />
          </div>

          <div className="grid gap-2 flex-1">
            <Label>地區</Label>
            <Input name="area" value={formData.area} onChange={handleChange} />
          </div>

          <div className="grid gap-2">
            <Label>縮短標題</Label>
            <Input name="shortened_title" value={formData.shortened_title} onChange={handleChange} />
          </div>

          <div className="grid gap-2">
            <Label>原文連結</Label>
            <Input name="o_url" value={formData.o_url} onChange={handleChange} />
          </div>

          <div className="grid gap-2">
            <Label>圖片</Label>
            {formData.img_path ? (
              <img
                src={`${formData.img_path}`}
                alt="新聞圖片"
                className="w-full max-h-80 object-contain rounded border"
              />
            ) : (
              <div className="text-sm text-muted-foreground border p-4 text-center">尚未有圖片</div>
            )}
          </div>

          <div className="grid gap-2">
            <Button className="w-full bg-red-600 hover:bg-red-700 text-white" onClick={handleReject} disabled={isSaving}>
              {isSaving ? "拒絕中..." : "拒絕"}
            </Button>
          </div>

          <div className="flex flex-col gap-3">
            <Button type="submit" className="w-full" disabled={isSaving}>
              {isSaving ? "儲存中..." : "儲存所有修改"}
            </Button>
            <Button 
              type="button" 
              onClick={handlePublishAll} 
              variant="secondary" 
              className="bg-indigo-600 hover:bg-indigo-700 text-white w-full" 
              disabled={isSubmitting || isSaving}
            >
              <Send className="w-4 h-4 mr-2" /> {isSubmitting ? "發布中..." : "Post to Instagram"}
            </Button>
          </div>
         
        </form>
      </CardContent>
    </Card>
  )
}

export default EditNewsForm