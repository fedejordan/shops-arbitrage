// next.config.ts
import type { NextConfig } from "next";

const isDev = process.env.NODE_ENV === "development";
const nextConfig: NextConfig = {
  reactStrictMode: true, // u otras opciones
  async rewrites() {
    console.log("isDev", isDev);
    return isDev
      ? [
          {
            source: "/proxy/:path*",
            destination: "http://localhost:8000/:path*",
          },
        ]
      : [];
  },
};

export default nextConfig;
