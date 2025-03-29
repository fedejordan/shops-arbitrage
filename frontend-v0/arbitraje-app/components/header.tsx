import Link from "next/link"
import { Button } from "@/components/ui/button"

export function Header() {
  return (
    <header className="border-b">
      <div className="container mx-auto px-4 py-3 flex justify-between items-center">
        <Link href="/" className="font-bold text-xl">
          ArbitrajeApp
        </Link>
        <nav>
          <Button variant="ghost" asChild>
            <Link href="/">Inicio</Link>
          </Button>
        </nav>
      </div>
    </header>
  )
}

