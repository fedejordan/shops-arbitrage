import Link from 'next/link';

export default function Header() {
  return (
    <header className="bg-primary text-white shadow-md">
      <div className="container mx-auto px-4 py-4 flex justify-between items-center">
        <Link href="/" className="text-2xl font-bold">
          ProductArbitraje
        </Link>
        <nav>
          <ul className="flex space-x-4">
            <li>
              <Link href="/" className="hover:text-gray-200">
                Inicio
              </Link>
            </li>
          </ul>
        </nav>
      </div>
    </header>
  );
}