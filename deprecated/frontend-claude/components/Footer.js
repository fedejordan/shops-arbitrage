export default function Footer() {
    return (
      <footer className="bg-gray-800 text-white">
        <div className="container mx-auto px-4 py-6">
          <p className="text-center">
            &copy; {new Date().getFullYear()} ProductArbitraje - Todos los derechos reservados
          </p>
        </div>
      </footer>
    );
  }