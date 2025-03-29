import { useState } from 'react';

export default function SearchBar({ onSearch }) {
  const [query, setQuery] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-2xl mx-auto">
      <div className="flex items-center border-b-2 border-primary py-2">
        <input
          className="appearance-none bg-transparent border-none w-full text-gray-700 mr-3 py-1 px-2 leading-tight focus:outline-none"
          type="text"
          placeholder="Buscar productos..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button
          className="flex-shrink-0 bg-primary hover:bg-secondary border-primary hover:border-secondary text-sm border-4 text-white py-1 px-2 rounded"
          type="submit"
        >
          Buscar
        </button>
      </div>
    </form>
  );
}
