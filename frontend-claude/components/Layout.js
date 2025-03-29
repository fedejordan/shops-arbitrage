import Head from 'next/head';
import Header from './Header';
import Footer from './Footer';

export default function Layout({ children, title = 'Arbitraje de Productos' }) {
  return (
    <div className="flex flex-col min-h-screen">
      <Head>
        <title>{title}</title>
        <meta name="description" content="Sistema de arbitraje de productos" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      
      <Header />
      
      <main className="flex-grow container mx-auto px-4 py-8">
        {children}
      </main>
      
      <Footer />
    </div>
  );
}