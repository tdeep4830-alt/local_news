import { useState, useEffect } from "react"
import { useNavigate } from "react-router-dom"
import { apiFetch } from "@/api/client"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ArrowUpDown, Edit2 } from "lucide-react"


export function NewsTable({ onEdit }) {
  const [news, setNews] = useState([])
  const [sortConfig, setSortConfig] = useState({ key: 'date', direction: 'desc' })

  // 1. Fetch Data
  useEffect(() => {
    apiFetch("/api/news")
      .then(res => res && res.json())
      .then(data => data && setNews(data))
  }, [])

  // 2. Sorting Logic
  const handleSort = (key) => {
    let direction = 'asc'
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc'
    }
    setSortConfig({ key, direction })

    const sortedData = [...news].sort((a, b) => {
      if (a[key] < b[key]) return direction === 'asc' ? -1 : 1
      if (a[key] > b[key]) return direction === 'asc' ? 1 : -1
      return 0
    })
    setNews(sortedData)
  }

  const navigate = useNavigate()


  // Status 顏色標籤
  const getStatusBadge = (status) => {
    const variants = {
      PENDING: "secondary",
      APPROVED: "outline",
      POSTED: "default", // 黑色
      REJECTED: "destructive"
    }
    return <Badge variant={variants[status] || "outline"}>{status}</Badge>
  }

  return (
    <div className="rounded-md border bg-white">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-[100px]">ID</TableHead>
            <TableHead className="max-w-[300px]">標題</TableHead>
            {/* 撳 Heading 觸發 Sorting */}
            <TableHead onClick={() => handleSort('area')} className="cursor-pointer hover:text-primary">
              地區 <ArrowUpDown className="inline ml-1 h-4 w-4" />
            </TableHead>
            <TableHead onClick={() => handleSort('status')} className="cursor-pointer hover:text-primary">
              狀態 <ArrowUpDown className="inline ml-1 h-4 w-4" />
            </TableHead>
            <TableHead onClick={() => handleSort('date')} className="cursor-pointer hover:text-primary">
              建立日期 <ArrowUpDown className="inline ml-1 h-4 w-4" />
            </TableHead>
            <TableHead className="text-right">操作</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {news.map((item) => (
            <TableRow key={item.id}>
              <TableCell className="font-medium">{item.id}</TableCell>
              <TableCell className="truncate">{item.title}</TableCell>
              <TableCell>{item.area}</TableCell>
              <TableCell>{getStatusBadge(item.status)}</TableCell>
              <TableCell>{new Date(item.date).toLocaleDateString()}</TableCell>
              <TableCell className="text-right">
                <Button variant="ghost" size="sm" onClick={() => navigate(`/edit/${item.id}`)}>
                  <Edit2 className="h-4 w-4 mr-1" /> 修改
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}