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

  const handleAppendToGoogle = async () => {
    setIsSubmitting(true)
    try {
      const res = await apiFetch(`/api/news/${newsId}/google`, {
        method: "POST",
      })
      if (!res) return
      if (res.ok) alert("✅ 已成功發布到 Google！")
    } catch (error) {
      console.error("Error posting to Google:", error)
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
                src={`http://localhost:8001/images/${formData.img_path}`}
                alt="新聞圖片"
                className="w-full max-h-80 object-contain rounded border"
              />
            ) : (
              <div className="text-sm text-muted-foreground border p-4 text-center">尚未有圖片</div>
            )}
          </div>

          <div className="grid gap-2">
            <Label>狀態 (Status)</Label>
            <Select 
              value={formData.status} // 2. 修正：用 value 而唔係 itemValue
              onValueChange={(value) => setFormData({ ...formData, status: value })}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="選擇一個狀態" />
              </SelectTrigger>
              <SelectContent>
                <SelectGroup>
                  {status.map((item) => (
                    <SelectItem key={item.value} value={item.value}>
                      {item.label}
                    </SelectItem>
                  ))}
                </SelectGroup>
              </SelectContent>
            </Select>
          </div>

          <div className="flex flex-col gap-3">
            <Button type="submit" className="w-full" disabled={isSaving}>
              {isSaving ? "儲存中..." : "儲存所有修改"}
            </Button>
            <Button 
              type="button" 
              onClick={handleAppendToGoogle} 
              variant="secondary" 
              className="bg-green-600 hover:bg-green-700 text-white w-full" 
              disabled={isSubmitting || isSaving}
            >
              <Send className="w-4 h-4 mr-2" /> {isSubmitting ? "發布中..." : "出 Post"}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}

export default EditNewsForm