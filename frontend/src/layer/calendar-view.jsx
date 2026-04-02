import { useState, useEffect } from "react"
import { useNavigate } from "react-router-dom"
import { Calendar, dateFnsLocalizer } from "react-big-calendar"
import { format, parse, startOfWeek, getDay } from "date-fns"
import { zhHK } from "date-fns/locale"
import { apiFetch } from "@/api/client"
import "react-big-calendar/lib/css/react-big-calendar.css"

const localizer = dateFnsLocalizer({
  format,
  parse,
  startOfWeek: () => startOfWeek(new Date(), { weekStartsOn: 0 }),
  getDay,
  locales: { "zh-HK": zhHK },
})

export function CalendarView() {
  const navigate = useNavigate()
  const [events, setEvents] = useState([])
  const [currentDate, setCurrentDate] = useState(new Date())

  useEffect(() => {
    async function fetchMonthNews() {
      const monthStr = format(currentDate, "yyyy-MM")
      try {
        const res = await apiFetch(`/api/news/month/${monthStr}`)
        if (!res || !res.ok) return
        const data = await res.json()
        // data: [{ date: "2026-03-31", count: 5, titles: [...] }]
        const mapped = data.map(item => ({
          title: item.pending > 0 ? `${item.count} 篇新聞 (${item.pending} 待處理)` : `${item.count} 篇新聞`,
          start: new Date(item.date + "T00:00:00"),
          end: new Date(item.date + "T00:00:00"),
          allDay: true,
          date: item.date,
        }))
        setEvents(mapped)
      } catch (e) {
        console.error("Failed to fetch month news:", e)
      }
    }
    fetchMonthNews()
  }, [currentDate])

  function handleSelectEvent(event) {
    navigate(`/news/date/${event.date}`)
  }

  function handleNavigate(date) {
    setCurrentDate(date)
  }

  return (
    <div style={{ height: "calc(100vh - 120px)" }}>
      <Calendar
        localizer={localizer}
        events={events}
        startAccessor="start"
        endAccessor="end"
        onSelectEvent={handleSelectEvent}
        onNavigate={handleNavigate}
        date={currentDate}
        view="month"
        onView={() => {}}
        views={["month"]}
        culture="zh-HK"
        messages={{
          today: "今日",
          previous: "上月",
          next: "下月",
          month: "月",
          noEventsInRange: "本月冇新聞",
        }}
        style={{ height: "100%" }}
      />
    </div>
  )
}

export default CalendarView
