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

