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
  const [loading, setLoading] = useState(false)

  const generateTweets = async () => {
    setLoading(true)
    try {
      const url = process.env.NEXT_PUBLIC_API_BASE_URL || ""
      const res = await fetch(`${url}/tweets/suggestions`)
      const data = await res.json()

      if (Array.isArray(data)) {
        setTweetGroups(data)
      } else {
        console.error("Respuesta inesperada:", data)
        setTweetGroups([])
      }
    } catch (err) {
      console.error("Error al obtener tweets", err)
      setTweetGroups([])
    } finally {
      setLoading(false)
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

  const handleTweet = (text: string) => {
    const url = `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}`
    window.open(url, "_blank")
  }

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold">Sugerencias de Tweets</h1>
      <p className="text-muted-foreground text-sm">
        Generá automáticamente ideas de tweets en base a la base de datos de productos.
      </p>
      <Button onClick={generateTweets} disabled={loading}>
        {loading ? "Generando..." : "Generar tweets"}
      </Button>

      {tweetGroups.map((group, idx) => (
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
                      onClick={() => handleTweet(text)}
                    >
                      <Twitter className="w-4 h-4 mr-1" /> Tweetear ahora
                    </Button>
                  </div>
                </div>
              )
            })}
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
