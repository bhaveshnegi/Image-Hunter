import { useState,useEffect } from "react";
import { Search, Download, Sparkles, ArrowRight, CheckCircle2, Upload, Image, Zap } from "lucide-react";
import { crawl, getStatus, getDownloadLink, uploadCrawl } from "./api.js";
import "./App.css";


function App() {
  const [kw, setKw] = useState("");
  const [max, setMax] = useState(1);
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState({});
  const [loading, setLoading] = useState(false);
  const [focusedInput, setFocusedInput] = useState(null);
  const [searchMode, setSearchMode] = useState('text'); // 'text' or 'upload'
  const [uploadFile, setUploadFile] = useState(null);   // <- NEW

const start = async () => {
  setLoading(true);
  let job;
  if (searchMode === 'text') {
    job = await crawl({ keyword: kw, max_num: max });
  } else {
    // upload mode – we already have the file
    job = await uploadCrawl(uploadFile, max);
  }

  const { job_id } = job;
  setJobId(job_id);
  const t = setInterval(async () => {
    const s = await getStatus(job_id);
    setStatus(s);
    if (s.status !== 'running') {
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

  const handleUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadFile(file);  
    setSearchMode('upload');
    const { job_id } = await uploadCrawl(file, max);
    setJobId(job_id);
    // const t = setInterval(async () => {
    //   const s = await getStatus(job_id);
    //   setStatus(s);
    //   if (s.status !== "running") { clearInterval(t); setLoading(false); }
    // }, 1000);
      const t = setInterval(async () => {
      const s = await getStatus(job_id);
      setStatus(s);
      if (s.status !== "running") {
        clearInterval(t);
        setLoading(false);
      }
    }, 1000);
  };

  const canStart =
  !loading &&
  max >= 1 &&
  max <= 500 &&
  (searchMode === 'text' ? kw.trim().length > 0 : uploadFile !== null);

  useEffect(() => {
  setUploadFile(null);
  setStatus({});
  setJobId(null);
  }, [searchMode]);

  return (
    <div className="app-container">
      <div className="content-wrapper">

        {/* Floating Header */}
        <div className="header animate-fadeIn">
          <div className="header-icon">
            <Sparkles className="header-icon-sparkles" />
          </div>
          <h1 className="header-title">
            Image Hunter
          </h1>
          <p className="header-subtitle">
            Discover amazing images across the web ✨
          </p>
        </div>

        {/* Main Search Card */}
        <div className="main-card">

          {/* Search Mode Toggle */}
          <div className="mode-toggle">
            <button
              onClick={() => setSearchMode('text')}
              className={`mode-btn ${searchMode === 'text' ? 'mode-btn-active' : ''}`}
            >
              <Search className="mode-icon" />
              Text Search
            </button>
            <button
              onClick={() => setSearchMode('upload')}
              className={`mode-btn ${searchMode === 'upload' ? 'mode-btn-active mode-btn-upload' : ''}`}
            >
              <Upload className="mode-icon" />
              Image Upload
            </button>
          </div>

          {/* Text Search */}
          {searchMode === 'text' && (
            <div className="search-section animate-slideIn">
              <div className="input-group">
                <div className={`input-glow ${focusedInput === 'keyword' ? 'input-glow-active' : ''}`}></div>
                <div className="input-wrapper">
                  <input
                    type="text"
                    value={kw}
                    onChange={(e) => setKw(e.target.value)}
                    onFocus={() => setFocusedInput('keyword')}
                    onBlur={() => setFocusedInput(null)}
                    placeholder="What images are you looking for?"
                    className="text-input"
                  />
                  <Search className="input-icon" />
                </div>
              </div>
            </div>
          )}

          {/* Upload Search */}
          {searchMode === 'upload' && (
            <div className="upload-section animate-slideIn">
              <input
                type="file"
                accept="image/*"
                id="upload-input"
                className="upload-input-hidden"
                onChange={handleUpload}
              />
              <label htmlFor="upload-input" className="upload-label">
                <div className="upload-icon-wrapper">
                  <Image className="upload-icon" />
                </div>
                <p className="upload-title">Upload an image</p>
                <p className="upload-subtitle">
                  Find similar images across the web
                </p>
              </label>
            </div>
          )}
          <div className="form-group">
            <label className={focusedInput === 'max' || max ? "label focused" : "label"}>
              Maximum images 500
            </label>
            <input
              type="number"
              value={max}
              onChange={(e) => setMax(Math.min(Math.max(Number(e.target.value)), 500))}
              onFocus={() => setFocusedInput('max')}
              onBlur={() => setFocusedInput(null)}
              min="1"
              max="500"
            />
            <div className="input-emoji">
              {max > 100 ? '🔥' : max > 50 ? '⚡' : '📱'}
            </div>
          </div>

          {/* Action Button */}
          <button
            onClick={start}
            disabled={!canStart}
            className={`action-btn ${canStart ? 'action-btn-active' : 'action-btn-disabled'}`}
          >
            {loading ? (
              <div className="loading-content">
                <div className="spinner"></div>
                <span>Hunting Images...</span>
              </div>
            ) : (
              <div className="button-content">
                <span>Start Hunt</span>
                <ArrowRight className="arrow-icon" />
              </div>
            )}
          </button>
        </div>

        {/* Status Card */}
        {status.status && (
          <div className="status-card animate-slideUp">
            <div className="status-header">
              <div className={`status-dot ${status.status}`}></div>
              <div className="status-text">
                <p className="status-title">
                  Status: {status.status}
                </p>
                {status.msg && (
                  <p className="status-message">{status.msg}</p>
                )}
              </div>
            </div>

            {status.status === "running" && (
              <div className="progress-bar">
                <div className="progress-fill"></div>
              </div>
            )}

            {status.status === "done" && (
              <div className="success-section">
                <CheckCircle2 className="success-icon" />
                <button
                  onClick={handleDownload}
                  className="download-btn"
                >
                  <Download className="download-icon" />
                  Download Collection
                </button>
              </div>
            )}
          </div>
        )}

        {/* Footer */}
        <div className="footer">
          <p className="footer-content">
            <span>Discover</span>
            <span className="footer-dot"></span>
            <span>Collect</span>
            <span className="footer-dot"></span>
            <span>Download</span>
          </p>
        </div>
      </div>
    </div>
  );
}

export default App;