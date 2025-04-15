export default function EnvCheck() {
    return (
      <div>
        API URL: {process.env.NEXT_PUBLIC_API_BASE_URL}
      </div>
    )
  }
  