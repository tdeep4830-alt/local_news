import { useState, useEffect } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { apiFetch } from "@/api/client"
import { ChevronLeft, X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"

export default function DateNewsPage() {
  const { date } = useParams()
  const navigate = useNavigate()
  const [news, setNews] = useState([])
  const [loading, setLoading] = useState(true)
  const [rejecting, setRejecting] = useState(null)

  useEffect(() => {
    async function fetchNews() {
      try {
        const res = await apiFetch(`/api/news/date/${date}`)
        if (!res || !res.ok) { setNews([]); return }
        const data = await res.json()
        setNews(data.filter(item => item.status === "PENDING"))
      } catch (e) {
        setNews([])
      } finally {
        setLoading(false)
      }
    }
    fetchNews()
  }, [date])

  async function handleReject(e, newsId) {
    e.stopPropagation()
    setRejecting(newsId)
    try {
      const res = await apiFetch(`/api/news/reject/${newsId}`, { method: "POST" })
      if (res?.ok) {
        setNews(prev => prev.filter(item => item.id !== newsId))
      }
    } finally {
      setRejecting(null)
    }
  }

  return (
    <div className="max-w-3xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <Button variant="ghost" size="icon" onClick={() => navigate("/calendar")}>
          <ChevronLeft className="w-5 h-5" />
        </Button>
        <h2 className="text-xl font-bold">{date} 待處理新聞</h2>
        <span className="text-sm text-slate-400">({news.length} 篇)</span>
      </div>

      {loading ? (
        <div className="text-slate-400 text-sm">載入中...</div>
      ) : news.length === 0 ? (
        <div className="text-slate-400 text-sm">當日冇待處理新聞</div>
      ) : (
        <div className="flex flex-col gap-3">
          {news.map(item => (
            <Card
              key={item.id}
              className="cursor-pointer hover:shadow-md transition-shadow"
              onClick={() => navigate(`/edit/${item.id}`)}
            >
              <CardContent className="py-4 px-5 flex items-center justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="text-xs text-slate-400 mb-1">{item.area}</div>
                  <div className="text-sm font-medium leading-snug">{item.title}</div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-red-500 hover:text-red-700 hover:bg-red-50 shrink-0"
                  disabled={rejecting === item.id}
                  onClick={(e) => handleReject(e, item.id)}
                >
                  <X className="w-4 h-4 mr-1" />
                  {rejecting === item.id ? "拒絕中..." : "拒絕"}
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
