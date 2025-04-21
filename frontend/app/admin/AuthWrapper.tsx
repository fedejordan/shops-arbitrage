"use client"

import { useEffect, useState } from "react"

export default function AuthWrapper({ children }: { children: React.ReactNode }) {
  const [authenticated, setAuthenticated] = useState(false)
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [loading, setLoading] = useState(true)
  const url = process.env.NEXT_PUBLIC_API_BASE_URL

  useEffect(() => {
    const isLoggedIn = localStorage.getItem("authenticated") === "true"
    setAuthenticated(isLoggedIn)
    setLoading(false)
  }, [])

  const handleLogin = async () => {
    try {
      const res = await fetch(`${url}/admin/login-check`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      })

      if (res.ok) {
        setAuthenticated(true)
        localStorage.setItem("authenticated", "true")
      } else if (res.status == 429) {
        alert("Demasiados intentos de inicio de sesión. Por favor, espere un momento e intente nuevamente.")
      } else{
        alert("Credenciales incorrectas")
      }
    } catch {
      alert("Error al verificar las credenciales")
    }
  }

  const handleLogout = () => {
    localStorage.removeItem("authenticated")
    setAuthenticated(false)
  }

  if (loading) return null

  if (!authenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="bg-white p-6 rounded-lg shadow-lg w-80 space-y-4">
          <h2 className="text-xl font-bold text-center">Login</h2>
          <input
            type="text"
            placeholder="Usuario"
            className="w-full border px-3 py-2 rounded"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
          <input
            type="password"
            placeholder="Contraseña"
            className="w-full border px-3 py-2 rounded"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <button
            onClick={handleLogin}
            className="w-full bg-black text-white py-2 rounded hover:bg-gray-800 transition"
          >
            Ingresar
          </button>
        </div>
      </div>
    )
  }

  return (
    <>
      <button
        onClick={handleLogout}
        className="absolute top-4 right-4 text-sm text-gray-500 hover:underline"
      >
        Logout
      </button>
      {children}
    </>
  )
}
