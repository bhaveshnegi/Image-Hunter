const BASE = "http://localhost:8000";

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
