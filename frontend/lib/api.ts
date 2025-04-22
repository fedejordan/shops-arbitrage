// lib/api.ts
export const apiFetch = (path: string, options: RequestInit = {}) => {
  const isDev = process.env.NODE_ENV === "development";
  console.log("isDev", isDev);

  const baseUrl = isDev
    ? "/proxy"
    : process.env.NEXT_PUBLIC_API_BASE_URL || "";

  return fetch(`${baseUrl}${path}`, {
    credentials: "include",
    ...options,
  });
};
