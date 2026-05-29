import Head from 'next/head';
import { useState } from 'react';

export default function Home() {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleScan = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/scrape');
      if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
      const data = await res.json();
      setResults(data);
    } catch (err) {
      setError('Scan failed: ' + err.message);
      console.error('Scan error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6 font-sans">
      <Head>
        <title>Telecom AI News Scanner</title>
        <meta name="description" content="Your PM-grade telecom/AI news filter" />
        <script src="https://cdn.tailwindcss.com"></script>
      </Head>

      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-8 pb-4 border-b">
          <h1 className="text-3xl font-bold text-gray-800">Telecom AI News Scanner</h1>
          <button
            onClick={handleScan}
            disabled={loading}
            className={`px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-shadow ${loading ? 'opacity-50 cursor-not-allowed' : 'shadow-md hover:shadow-lg'}`}
          >
            {loading ? 'Scanning...' : 'Scan Now'}
          </button>
        </div>

        {error && (
          <div className="bg-red-50 border-l-4 border-red-500 text-red-700 p-4 mb-6">
            <p className="font-medium">{error}</p>
          </div>
        )}

        {results.length === 0 && !loading ? (
          <div className="text-center text-gray-500 py-12">
            <p className="text-lg">Click "Scan Now" to see Telecom/AI articles</p>
            <p className="text-sm mt-2">Powered by your Neighborhood PM judgment framework</p>
          </div>
        ) : (
          <div className="grid gap-6">
            {results.map((item, index) => {
              const signalColor =
                item['Action Signal'] === 'PRIORITIZE'
                  ? 'bg-red-100 text-red-800'
                  : item['Action Signal'] === 'MONITOR'
                  ? 'bg-blue-100 text-blue-800'
                  : 'bg-gray-100 text-gray-600';

              return (
                <div key={index} className="border rounded-xl p-6 bg-white shadow-sm hover:shadow-md transition-shadow">
                  <div className="flex justify-between items-start mb-4">
                    <a
                      href={item.Link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xl font-semibold text-indigo-700 hover:text-indigo-900 hover:underline"
                    >
                      {item.Headline}
                    </a>
                    <span className={`ml-4 shrink-0 px-3 py-1 text-xs rounded-full font-medium ${signalColor}`}>
                      {item['Action Signal']}
                    </span>
                  </div>

                  <div className="flex flex-wrap items-center gap-4 text-sm text-gray-500 mb-4">
                    <span>📰 {item.Source}</span>
                    <span>📅 {new Date(item.Published).toLocaleDateString()}</span>
                    <span>⏱️ {item['Time Horizon']}</span>
                  </div>

                  {item['Vendor Tags'] && item['Vendor Tags'].length > 0 && (
                    <div className="flex flex-wrap gap-2 mb-4">
                      {item['Vendor Tags'].map((v) => (
                        <span key={v} className="px-2.5 py-0.5 bg-gray-200 text-xs rounded">
                          {v}
                        </span>
                      ))}
                    </div>
                  )}

                  {item['Cost/Savings Signal'] && (
                    <div className="bg-green-50 border-l-4 border-green-500 p-4 mb-4">
                      <p className="text-sm font-medium text-green-800">
                        💰 {item['Cost/Savings Signal']}
                      </p>
                    </div>
                  )}

                  <div className="text-xs text-gray-500 flex flex-wrap gap-4">
                    <span>📡 Telecom: {item['Telecom Relevance']}</span>
                    <span>🤖 AI: {item['AI Relevance']}</span>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        <div className="mt-12 pt-6 border-t border-gray-200 text-center text-sm text-gray-500">
          Built with <span className="text-indigo-600">❤️</span> by a telecom PM who ships <br />
          <span className="font-medium">Signal → Strategy → Shipment</span>
        </div>
      </div>
    </div>
  );
}