'use client'

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Check, Clipboard, Twitter } from "lucide-react"

type TweetGroup = {
  case: number
  title: string
  retailer_barato: string
  precio_barato: number
  retailer_caro: string
  precio_caro: number
  diff: number
  tweets: string[]
}

export default function TweetSuggestions() {
  const [tweetGroups, setTweetGroups] = useState<TweetGroup[]>([])
  const [copiedId, setCopiedId] = useState<string | null>(null)
  const [loadingArbitrajes, setLoadingArbitrajes] = useState(false)
  const [loadingDescuentos, setLoadingDescuentos] = useState(false)
  const [loadingTop, setLoadingTop] = useState(false)
  const [loadingHistorico, setLoadingHistorico] = useState(false)
  const [weeklyDrops, setWeeklyDrops] = useState<any[]>([])
  const [loadingWeekly, setLoadingWeekly] = useState(false)
  const [historicTweet, setHistoricTweet] = useState<any | null>(null)
  const [topDiscountTweets, setTopDiscountTweets] = useState<string[]>([])
  const [discountGroups, setDiscountGroups] = useState<any[]>([])
  const [loadingTips, setLoadingTips] = useState(false)
const [educationalTweets, setEducationalTweets] = useState<string[]>([])
  const [view, setView] = useState<"arbitrajes" | "descuentos" | "top" | "historic" | "weekly" | "educational" | "polls">("arbitrajes")
  const [loadingPolls, setLoadingPolls] = useState(false)
  const [pollTweets, setPollTweets] = useState<string[]>([])
  const [tweetingId, setTweetingId] = useState<string | null>(null)

  
  const generatePolls = async () => {
    setLoadingPolls(true)
    try {
      const url = process.env.NEXT_PUBLIC_API_BASE_URL || ""
      const res = await fetch(`${url}/tweets/polls`, { credentials: "include" })
      const data = await res.json()
      if (Array.isArray(data)) {
        setPollTweets(data)
        setView("polls")
      }
    } catch (err) {
      console.error("Error al obtener encuestas", err)
    } finally {
      setLoadingPolls(false)
    }
  }
  
  const generateEducational = async () => {
    setLoadingTips(true)
    try {
      const url = process.env.NEXT_PUBLIC_API_BASE_URL || ""
      const res = await fetch(`${url}/tweets/educational`, { credentials: "include" })
      const data = await res.json()
      if (Array.isArray(data)) {
        setEducationalTweets(data)
        setView("educational")
      }
    } catch (err) {
      console.error("Error al obtener tips educativos", err)
    } finally {
      setLoadingTips(false)
    }
  }

  const generateWeeklyDrops = async () => {
    setLoadingWeekly(true)
    try {
      const url = process.env.NEXT_PUBLIC_API_BASE_URL || ""
      const res = await fetch(`${url}/tweets/weekly-drops`, { credentials: "include" })
      const data = await res.json()
      setWeeklyDrops(data)
      setView("weekly")
    } catch (err) {
      console.error("Error al obtener bajadas semanales", err)
    } finally {
      setLoadingWeekly(false)
    }
  }
  
  const generateHistoricDrop = async () => {
    setLoadingHistorico(true)
    try {
      const url = process.env.NEXT_PUBLIC_API_BASE_URL || ""
      const res = await fetch(`${url}/tweets/historical-difference`, { credentials: "include" })
      const data = await res.json()
      setHistoricTweet(data)
      setView("historic")
    } catch (err) {
      console.error("Error al obtener descuento histórico", err)
    } finally {
      setLoadingHistorico(false)
    }
  }
  

  const generateArbitrages = async () => {
    setLoadingArbitrajes(true)
    try {
      const url = process.env.NEXT_PUBLIC_API_BASE_URL || ""
      const res = await fetch(`${url}/tweets/suggestions`, { credentials: "include" })
      const data = await res.json()
  
      if (Array.isArray(data)) {
        setTweetGroups(data)
        setView("arbitrajes")
      } else {
        console.error("Respuesta inesperada:", data)
        setTweetGroups([])
      }
    } catch (err) {
      console.error("Error al obtener tweets", err)
      setTweetGroups([])
    } finally {
      setLoadingArbitrajes(false)
    }
  }

  const generateDiscounts = async () => {
    setLoadingDescuentos(true)
    try {
      const url = process.env.NEXT_PUBLIC_API_BASE_URL || ""
      const res = await fetch(`${url}/tweets/discounts`, { credentials: "include" })
      const data = await res.json()
      if (Array.isArray(data)) {
        setDiscountGroups(data)
        setView("descuentos")
      } else {
        console.error("Respuesta inesperada:", data)
      }
    } catch (err) {
      console.error("Error al obtener descuentos", err)
    } finally {
      setLoadingDescuentos(false)
    }
  }
  
  const generateTopDiscounts = async () => {
    setLoadingTop(true)
    try {
      const url = process.env.NEXT_PUBLIC_API_BASE_URL || ""
      const res = await fetch(`${url}/tweets/top-discounts`, { credentials: "include" })
      const data = await res.json()
      if (Array.isArray(data)) {
        setTopDiscountTweets(data)
        setView("top")
      }
    } catch (err) {
      console.error("Error al obtener top descuentos", err)
    } finally {
      setLoadingTop(false)
    }
  }
  
  
  const handleCopy = async (id: string, text: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopiedId(id)
      setTimeout(() => setCopiedId(null), 2000)
    } catch (err) {
      console.error("Error al copiar", err)
    }
  }

  const handleTweet = async (text: string, id: string) => {
    const url = process.env.NEXT_PUBLIC_API_BASE_URL + "/tweets/post"
    setTweetingId(id)
    try {
      const res = await fetch(url, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ text }),
      })
  
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || "Error desconocido")
      }
  
      alert("✅ Tweet publicado correctamente desde TuPrecioIdeal.")
    } catch (err: any) {
      console.error("Error al postear:", err)
      alert("❌ Error al postear el tweet: " + err.message)
    } finally {
      setTweetingId(null)
    }
  }
  

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold">Sugerencias de Tweets</h1>
      <p className="text-muted-foreground text-sm">
        Generá automáticamente ideas de tweets en base a la base de datos de productos.
      </p>
      <div className="flex gap-4">
        <Button onClick={generateArbitrages} disabled={loadingWeekly || loadingHistorico || loadingTop || loadingDescuentos || loadingArbitrajes || loadingTips || loadingPolls}>
            {loadingArbitrajes ? "Generando..." : "Tweets de arbitrajes"}
        </Button>
        <Button onClick={generateDiscounts} disabled={loadingWeekly || loadingHistorico || loadingTop || loadingDescuentos || loadingArbitrajes || loadingTips || loadingPolls}>
            {loadingDescuentos ? "Buscando..." : "Tweets de ofertas individuales"}
        </Button>
        <Button onClick={generateTopDiscounts} disabled={loadingWeekly || loadingHistorico || loadingTop || loadingDescuentos || loadingArbitrajes || loadingTips || loadingPolls}>
            {loadingTop ? "Cargando..." : "Top descuentos de hoy"}
        </Button>
        <Button onClick={generateHistoricDrop} disabled={loadingWeekly || loadingHistorico || loadingTop || loadingDescuentos || loadingArbitrajes || loadingTips || loadingPolls}>
            {loadingHistorico ? "Analizando..." : "Mayor baja histórica"}
        </Button>
        <Button onClick={generateWeeklyDrops} disabled={loadingWeekly || loadingHistorico || loadingTop || loadingDescuentos || loadingArbitrajes || loadingTips || loadingPolls}>
            {loadingWeekly ? "Buscando..." : "Bajas de precio esta semana"}
        </Button>
        <Button onClick={generateEducational} disabled={loadingTips || loadingTop || loadingHistorico || loadingPolls || loadingDescuentos || loadingArbitrajes || loadingWeekly}>
            {loadingTips ? "Generando..." : "Tips educativos"}
        </Button>
        <Button onClick={generatePolls} disabled={loadingPolls || loadingTop || loadingHistorico || loadingDescuentos || loadingArbitrajes || loadingWeekly || loadingTips}>
            {loadingPolls ? "Cargando..." : "Tweets con encuesta"}
        </Button>


      </div>

      {view === "arbitrajes" && tweetGroups.map((group, idx) => (
        <Card key={idx}>
          <CardContent className="p-4 space-y-2">
            <div className="font-semibold text-sm text-muted-foreground">
              <span className="text-black">{group.title}</span> — {group.retailer_barato} (${group.precio_barato.toLocaleString()}) vs {group.retailer_caro} (${group.precio_caro.toLocaleString()}) → diferencia: ${group.diff.toLocaleString()}
            </div>

            {group.tweets.map((text, i) => {
              const uid = `${group.case}-${i}`
              return (
                <div key={uid} className="border rounded p-3 text-sm flex flex-col gap-2">
                  <p>{text}</p>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleCopy(uid, text)}
                    >
                      {copiedId === uid ? (
                        <><Check className="w-4 h-4 mr-1 text-green-500" /> Copiado</>
                      ) : (
                        <><Clipboard className="w-4 h-4 mr-1" /> Copiar</>
                      )}
                    </Button>
                    <Button
                      variant="default"
                      size="sm"
                      disabled={tweetingId === uid}
                      onClick={() => handleTweet(text, uid)}
                    >
                      {tweetingId === uid ? (
                        <>⏳ Posteando...</>
                      ) : (
                        <>
                          <Twitter className="w-4 h-4 mr-1" /> Tweetear ahora
                        </>
                      )}
                    </Button>
                  </div>
                </div>
              )
            })}
          </CardContent>
        </Card>
      ))}
      {view === "descuentos" && discountGroups.map((group, idx) => (
        <Card key={idx}>
            <CardContent className="p-4 space-y-2">
            <div className="font-semibold text-sm text-muted-foreground">
                {group.title} en {group.retailer} — <span className="text-green-600">-{group.discount_pct}%</span><br />
                <span className="text-xs text-muted-foreground">
                Precio original: ${group.original_price.toLocaleString()} • Ahora: ${group.final_price.toLocaleString()}
                </span>
            </div>
            {group.tweets.map((tweet: string, i: number) => {
                const uid = `${idx}-${i}`
                return (
                <div key={uid} className="border rounded p-3 text-sm flex flex-col gap-2">
                    <p>{tweet}</p>
                    <div className="flex gap-2">
                    <Button variant="outline" size="sm" onClick={() => handleCopy(uid, tweet)}>
                        {copiedId === uid ? <><Check className="w-4 h-4 mr-1 text-green-500" /> Copiado</> : <><Clipboard className="w-4 h-4 mr-1" /> Copiar</>}
                    </Button>
                    <Button
                      variant="default"
                      size="sm"
                      disabled={tweetingId === uid}
                      onClick={() => handleTweet(tweet, uid)}
                    >
                      {tweetingId === uid ? (
                        <>⏳ Posteando...</>
                      ) : (
                        <>
                          <Twitter className="w-4 h-4 mr-1" /> Tweetear ahora
                        </>
                      )}
                    </Button>
                    </div>
                </div>
                )
            })}
            </CardContent>
        </Card>
     ))}
      {view === "top" && topDiscountTweets.map((text, idx) => {
        const uid = `top-${idx}`
        return (
            <Card key={uid}>
            <CardContent className="p-4 space-y-2">
                <p>{text}</p>
                <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={() => handleCopy(uid, text)}>
                    {copiedId === uid ? <><Check className="w-4 h-4 mr-1 text-green-500" /> Copiado</> : <><Clipboard className="w-4 h-4 mr-1" /> Copiar</>}
                </Button>
                <Button
                      variant="default"
                      size="sm"
                      disabled={tweetingId === uid}
                      onClick={() => handleTweet(text, uid)}
                    >
                      {tweetingId === uid ? (
                        <>⏳ Posteando...</>
                      ) : (
                        <>
                          <Twitter className="w-4 h-4 mr-1" /> Tweetear ahora
                        </>
                      )}
                    </Button>
                </div>
            </CardContent>
            </Card>
        )
     })}
     {view === "historic" && historicTweet && (
        <Card>
            <CardContent className="p-4 space-y-2">
            <div className="font-semibold text-sm text-muted-foreground">
                {historicTweet.title} en {historicTweet.retailer} — 
                <span className="text-green-600"> -{historicTweet.discount_pct}%</span><br />
                <span className="text-xs text-muted-foreground">
                De ${historicTweet.original_price.toLocaleString()} a ${historicTweet.final_price.toLocaleString()}
                </span>
            </div>
            {historicTweet.tweets.map((text: string, i: number) => {
                const uid = `historic-${i}`
                return (
                <div key={uid} className="border rounded p-3 text-sm flex flex-col gap-2">
                    <p>{text}</p>
                    <div className="flex gap-2">
                    <Button variant="outline" size="sm" onClick={() => handleCopy(uid, text)}>
                        {copiedId === uid ? <><Check className="w-4 h-4 mr-1 text-green-500" /> Copiado</> : <><Clipboard className="w-4 h-4 mr-1" /> Copiar</>}
                    </Button>
                    <Button
                      variant="default"
                      size="sm"
                      disabled={tweetingId === uid}
                      onClick={() => handleTweet(text, uid)}
                    >
                      {tweetingId === uid ? (
                        <>⏳ Posteando...</>
                      ) : (
                        <>
                          <Twitter className="w-4 h-4 mr-1" /> Tweetear ahora
                        </>
                      )}
                    </Button>
                    </div>
                </div>
                )
            })}
            </CardContent>
        </Card>
        )}

        {view === "weekly" && weeklyDrops.map((group, idx) => (
        <Card key={idx}>
            <CardContent className="p-4 space-y-2">
            <div className="font-semibold text-sm text-muted-foreground">
                {group.title} en {group.retailer} — bajó <span className="text-green-600">${group.diff.toLocaleString()}</span><br />
                <span className="text-xs text-muted-foreground">
                Antes: ${group.old_price.toLocaleString()} • Ahora: ${group.new_price.toLocaleString()}
                </span>
            </div>
            {group.tweets.map((tweet: string, i: number) => {
                const uid = `weekly-${idx}-${i}`
                return (
                <div key={uid} className="border rounded p-3 text-sm flex flex-col gap-2">
                    <p>{tweet}</p>
                    <div className="flex gap-2">
                    <Button variant="outline" size="sm" onClick={() => handleCopy(uid, tweet)}>
                        {copiedId === uid ? <><Check className="w-4 h-4 mr-1 text-green-500" /> Copiado</> : <><Clipboard className="w-4 h-4 mr-1" /> Copiar</>}
                    </Button>
                    <Button
                      variant="default"
                      size="sm"
                      disabled={tweetingId === uid}
                      onClick={() => handleTweet(text, uid)}
                    >
                      {tweetingId === uid ? (
                        <>⏳ Posteando...</>
                      ) : (
                        <>
                          <Twitter className="w-4 h-4 mr-1" /> Tweetear ahora
                        </>
                      )}
                    </Button>
                    </div>
                </div>
                )
            })}
            </CardContent>
        </Card>
        ))}
        
        {view === "educational" && educationalTweets.map((text, idx) => {
        const uid = `educational-${idx}`
        return (
            <Card key={uid}>
            <CardContent className="p-4 space-y-2">
                <p>{text}</p>
                <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={() => handleCopy(uid, text)}>
                    {copiedId === uid ? <><Check className="w-4 h-4 mr-1 text-green-500" /> Copiado</> : <><Clipboard className="w-4 h-4 mr-1" /> Copiar</>}
                </Button>
                <Button
                      variant="default"
                      size="sm"
                      disabled={tweetingId === uid}
                      onClick={() => handleTweet(text, uid)}
                    >
                      {tweetingId === uid ? (
                        <>⏳ Posteando...</>
                      ) : (
                        <>
                          <Twitter className="w-4 h-4 mr-1" /> Tweetear ahora
                        </>
                      )}
                    </Button>
                </div>
            </CardContent>
            </Card>
        )
        })}
        {view === "polls" && pollTweets.map((text, idx) => {
            const uid = `poll-${idx}`
            return (
                <Card key={uid}>
                <CardContent className="p-4 space-y-2">
                    <p>{text}</p>
                    <div className="flex gap-2">
                    <Button variant="outline" size="sm" onClick={() => handleCopy(uid, text)}>
                        {copiedId === uid ? <><Check className="w-4 h-4 mr-1 text-green-500" /> Copiado</> : <><Clipboard className="w-4 h-4 mr-1" /> Copiar</>}
                    </Button>
                    <Button
                      variant="default"
                      size="sm"
                      disabled={tweetingId === uid}
                      onClick={() => handleTweet(text, uid)}
                    >
                      {tweetingId === uid ? (
                        <>⏳ Posteando...</>
                      ) : (
                        <>
                          <Twitter className="w-4 h-4 mr-1" /> Tweetear ahora
                        </>
                      )}
                    </Button>
                    </div>
                </CardContent>
                </Card>
            )
            })}


    </div>
  )
}
