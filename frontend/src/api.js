const BASE = "https://image-hunter.onrender.com";
// const BASE = "http://localhost:8000";

// append to api.js
export async function uploadCrawl(file, max_num = 50){
  const fd = new FormData();
  fd.append("file", file);
  fd.append("max_num", String(max_num));
  const res = await fetch(`${BASE}/crawl-by-upload`, {method:"POST", body: fd});
  return res.json();          // {job_id}
}

export async function crawl(body) {
  const r = await fetch(`${BASE}/crawl`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return r.json();
}

export async function getStatus(id) {
  const r = await fetch(`${BASE}/status/${id}`);
  return r.json();
}

export async function getDownloadLink(id) {
  const r = await fetch(`${BASE}/download/${id}`);
  const data = await r.json();
  return `${BASE}${data.url}`;
}
