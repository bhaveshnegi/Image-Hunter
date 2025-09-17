import { useState } from "react";
import { crawl, getStatus } from "./api";

function App() {
  const [kw, setKw]   = useState("");
  const [max, setMax] = useState(50);
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState({});
  const [loading, setLoading] = useState(false);

  const start = async () => {
    setLoading(true);
    const { job_id } = await crawl({ keyword: kw, max_num: max });
    setJobId(job_id);
    const t = setInterval(async () => {
      const s = await getStatus(job_id);
      setStatus(s);
      if (s.status !== "running") { clearInterval(t); setLoading(false); }
    }, 1000);
  };

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center">
      <div className="bg-white rounded shadow p-8 w-full max-w-md space-y-4">
        <h1 className="text-2xl font-bold">Image Crawler</h1>
        <input
          className="w-full border px-3 py-2 rounded"
          placeholder="Keyword (e.g. Nike shoes)"
          value={kw}
          onChange={(e) => setKw(e.target.value)}
        />
        <input
          type="number"
          className="w-full border px-3 py-2 rounded"
          value={max}
          onChange={(e) => setMax(Number(e.target.value))}
          min="1"
          max="1000"
        />
        <button
          onClick={start}
          disabled={loading || !kw}
          className="w-full bg-blue-600 text-white py-2 rounded disabled:opacity-50"
        >
          {loading ? "Crawling…" : "Start"}
        </button>

        {status.status && (
          <div className="text-sm">
            Status: <span className="font-semibold">{status.status}</span>
            {status.msg && <p className="text-gray-600">{status.msg}</p>}
            {status.status === "done" && (
              <a
                className="text-blue-600 underline block mt-2"
                href={`http://localhost:8000/static/${jobId}.zip`}
                download
              >
                ⬇ Download ZIP
              </a>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
export default App;