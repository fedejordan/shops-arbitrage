export interface Product {
  id: number
  title: string
  original_price: number
  final_price: number
  url: string
  image: string | null
  category_name: string | null
  retailer: {
    name: string
  } | null
  added_date: string
  updated_date: string
  ai_description?: string | null
}


export interface ProductResponse {
  data: Product[]
  total: number
  page: number
  limit: number
}
