import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat("es-AR", {
    style: "currency",
    currency: "ARS",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount)
}

export function calculateDiscount(originalPrice: number, finalPrice: number): number {
  if (originalPrice <= 0 || finalPrice >= originalPrice) return 0
  const discount = ((originalPrice - finalPrice) / originalPrice) * 100
  return Math.round(discount)
}

export function timeAgo(dateString: string): string {
  const date = new Date(dateString.split(".")[0])
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000)

  const intervals: [number, string, number][] = [
    [60 * 60 * 24 * 365, "año", 1],
    [60 * 60 * 24 * 30, "mes", 1],
    [60 * 60 * 24, "día", 1],
    [60 * 60, "hora", 1],
    [60, "minuto", 1],
    [1, "segundo", 1],
  ]

  for (const [unitSeconds, unitName] of intervals) {
    const value = Math.floor(seconds / unitSeconds)
    if (value >= 1) {
      return `${value} ${unitName}${value > 1 ? "s" : ""}`
    }
  }

  return "unos segundos"
}

