import { useState } from "react";
import { Search, Download, Sparkles, ArrowRight, CheckCircle2 } from "lucide-react";
import { crawl, getStatus, getDownloadLink } from "./api.js";   // new file shown below
import "./App.css";

function App() {
  const [kw, setKw] = useState("");
  const [max, setMax] = useState(50);
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState({});
  const [loading, setLoading] = useState(false);
  const [focusedInput, setFocusedInput] = useState(null);

  const start = async () => {
    setLoading(true);
    const { job_id } = await crawl({ keyword: kw, max_num: max });
    setJobId(job_id);
    const t = setInterval(async () => {
      const s = await getStatus(job_id);
      setStatus(s);
      if (s.status !== "running") { 
        clearInterval(t); 
        setLoading(false); 
      }
    }, 1000);
  };

  const handleDownload = async () => {
  try {
    const url = await getDownloadLink(jobId);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${jobId}.zip`;
    document.body.appendChild(a);
    a.click();
    a.remove();
  } catch (e) {
    alert("Download link not ready yet");
  }
};

  const canStart = kw.trim() && !loading;

  return (
    <div className="app-container">
      <div className="card-wrapper">
        
        {/* Header */}
        <div className="header">
          <div className="header-icon">
            <Sparkles className="icon" />
          </div>
          <h1>Image Hunter</h1>
          <p>Find and collect images from across the web</p>
        </div>

        {/* Form Card */}
        <div className="card">
          <div className="form-group">
            <label className={focusedInput === 'keyword' || kw ? "label focused" : "label"}>
              What would you like to find?
            </label>
            <input
              type="text"
              value={kw}
              onChange={(e) => setKw(e.target.value)}
              onFocus={() => setFocusedInput('keyword')}
              onBlur={() => setFocusedInput(null)}
            />
            <Search className="input-icon" />
          </div>

          <div className="form-group">
            <label className={focusedInput === 'max' || max ? "label focused" : "label"}>
              Maximum images
            </label>
            <input
              type="number"
              value={max}
              onChange={(e) => {
                const v = Math.min(Number(e.target.value), 500); // clamp to 500
                setMax(v);
              }}
              onFocus={() => setFocusedInput('max')}
              onBlur={() => setFocusedInput(null)}
              min="1"
              max="500"          // hard browser cap
            />
            <div className="input-emoji">
              {max > 100 ? '🔥' : max > 50 ? '⚡' : '📱'}
            </div>
          </div>

          <button
            onClick={start}
            disabled={!canStart}
            className={canStart ? "btn" : "btn disabled"}
          >
            {loading ? (
              <>
                <div className="spinner"></div>
                <span>Hunting images...</span>
              </>
            ) : (
              <>
                <span>Start Hunt</span>
                <ArrowRight className="arrow" />
              </>
            )}
          </button>
        </div>

        {/* Status Card */}
        {status.status && (
          <div className="card status-card">
            <div className="status-row">
              <div className={`status-dot ${status.status}`}></div>
              <div className="status-text">
                <span>Status: <strong>{status.status}</strong></span>
                {status.msg && <p>{status.msg}</p>}
              </div>
            </div>

            {status.status === "running" && (
              <div className="progress-bar">
                <div className="progress"></div>
              </div>
            )}

            {status.status === "done" && (
              <div className="success">
                <CheckCircle2 className="success-icon" />
                <button onClick={handleDownload} className="btn success-btn">
                  <Download /> Download Collection
                </button>
              </div>
            )}
          </div>
        )}

        {/* Footer */}
        <div className="footer">
          <p>Discover • Collect • Download</p>
        </div>
      </div>
    </div>
  );
}

export default App;
