import asyncio, httpx, uuid, os, shutil, aiofiles
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware   # <-- add this line
# serve zipped file
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
load_dotenv()          # <-- pulls everything in .env into os.environ

PEXELS_KEY = os.getenv("PEXELS_API_KEY")          # <-- put your key here
if not PEXELS_KEY:
    raise RuntimeError("Env-var PEXELS_API_KEY required")

PEXELS_ROOT = "https://api.pexels.com/v1/search"

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://image-hunter-khaki.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

JOBS = {}  

class Request(BaseModel):
    keyword: str
    max_num: int = 50


async def _download_one(url: str, path: str, client: httpx.AsyncClient):
    async with client.stream("GET", url) as resp:
        resp.raise_for_status()
        async with aiofiles.open(path, "wb") as fh:
            async for chunk in resp.aiter_bytes():
                await fh.write(chunk)


async def _pexels_crawl_job(uid: str, keyword: str, max_num: int):
    output_dir = f"images/{uid}"
    os.makedirs(output_dir, exist_ok=True)

    headers = {"Authorization": PEXELS_KEY}
    per_page = min(80, max_num)          # Pexels allows max 80 per request
    downloaded = 0
    page = 1

    async with httpx.AsyncClient(timeout=30) as client:
        while downloaded < max_num:
            params = {"query": keyword, "per_page": per_page, "page": page}
            r = await client.get(PEXELS_ROOT, headers=headers, params=params)
            if r.status_code != 200:
                JOBS[uid].update(status="error", msg=f"Pexels API error {r.status_code}")
                return
            data = r.json()
            photos = data.get("photos", [])
            if not photos:
                break

            tasks = []
            for photo in photos:
                if downloaded >= max_num:
                    break
                url = photo["src"]["original"]          # pick any size you prefer
                ext = url.split("?")[0].split(".")[-1] or "jpg"
                tasks.append(
                    _download_one(url, f"{output_dir}/{downloaded:03d}.{ext}", client)
                )
                downloaded += 1

            await asyncio.gather(*tasks)
            page += 1

    JOBS[uid].update(status="done", msg="Downloaded images")


@app.post("/crawl")
def crawl(req: Request, bg: BackgroundTasks):
    uid = str(uuid.uuid4())
    JOBS[uid] = {"status": "running", "msg": ""}
    bg.add_task(_pexels_crawl_job, uid, req.keyword, req.max_num)
    return {"job_id": uid}

@app.get("/status/{job_id}")
def status(job_id: str):
    if job_id not in JOBS:
        raise HTTPException(404, "job not found")
    return JOBS[job_id]

@app.get("/download/{job_id}")
def download(job_id: str):
    zip_path = f"images/{job_id}.zip"
    if not os.path.exists(f"images/{job_id}"):
        raise HTTPException(404, "images folder missing")
    if not os.path.exists(zip_path):               # create only once
        shutil.make_archive(f"images/{job_id}", "zip", f"images/{job_id}")
    return {"url": f"/static/{job_id}.zip"}


app.mount("/static", StaticFiles(directory="images"), name="static")