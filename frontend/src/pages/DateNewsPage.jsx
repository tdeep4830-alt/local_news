import { useState, useEffect } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { apiFetch } from "@/api/client"
import { ChevronLeft } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"

const statusMap = {
  PENDING: { label: "待處理", variant: "outline" },
  APPROVED: { label: "已批准", variant: "secondary" },
  POSTED: { label: "已發布", variant: "default" },
  REJECTED: { label: "已拒絕", variant: "destructive" },
}

export default function DateNewsPage() {
  const { date } = useParams()
  const navigate = useNavigate()
  const [news, setNews] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchNews() {
      try {
        const res = await apiFetch(`/api/news/date/${date}`)
        if (!res || !res.ok) { setNews([]); return }
        const data = await res.json()
        setNews(data)
      } catch (e) {
        setNews([])
      } finally {
        setLoading(false)
      }
    }
    fetchNews()
  }, [date])

  return (
    <div className="max-w-3xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <Button variant="ghost" size="icon" onClick={() => navigate("/calendar")}>
          <ChevronLeft className="w-5 h-5" />
        </Button>
        <h2 className="text-xl font-bold">{date} 的新聞</h2>
        <span className="text-sm text-slate-400">({news.length} 篇)</span>
      </div>

      {loading ? (
        <div className="text-slate-400 text-sm">載入中...</div>
      ) : news.length === 0 ? (
        <div className="text-slate-400 text-sm">當日冇新聞</div>
      ) : (
        <div className="flex flex-col gap-3">
          {news.map(item => (
            <Card
              key={item.id}
              className="cursor-pointer hover:shadow-md transition-shadow"
              onClick={() => navigate(`/edit/${item.id}`)}
            >
              <CardContent className="py-4 px-5 flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="text-xs text-slate-400 mb-1">{item.area}</div>
                  <div className="text-sm font-medium leading-snug">{item.title}</div>
                </div>
                <Badge variant={statusMap[item.status]?.variant ?? "outline"}>
                  {statusMap[item.status]?.label ?? item.status}
                </Badge>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
