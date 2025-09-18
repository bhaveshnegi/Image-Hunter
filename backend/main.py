import uuid, os, shutil
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from icrawler.builtin import GoogleImageCrawler

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite default
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

JOBS = {}   # tiny in-memory store (uuid -> status)

class Request(BaseModel):
    keyword: str
    max_num: int = 50

@app.post("/crawl")
def crawl(req: Request):
    uid = str(uuid.uuid4())
    JOBS[uid] = {"status": "running", "msg": ""}
    output_dir = f"images/{uid}"
    os.makedirs(output_dir, exist_ok=True)

    def done_callback():
        JOBS[uid]["status"] = "done"
        JOBS[uid]["msg"] = "Downloaded images"

    def error_callback(msg):
        JOBS[uid]["status"] = "error"
        JOBS[uid]["msg"] = msg

    try:
        crawler = GoogleImageCrawler(
            storage={"root_dir": output_dir},
            log_level=20,   # INFO
        )
        crawler.crawl(
            keyword=req.keyword,
            max_num=req.max_num,
            file_idx_offset="auto",
            max_size=None,
            min_size=(64, 64),
        )
        done_callback()
    except Exception as e:
        error_callback(str(e))
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

# serve zipped file
from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory="images"), name="static")