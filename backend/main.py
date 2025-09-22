import uuid, os, shutil
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from icrawler.builtin import GoogleImageCrawler
import base64, io, requests
from PIL import Image
from fastapi import UploadFile

GOOGLE_REVERSE_URL = "https://lens.google.com/upload"

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    # allow_origins=["https://image-hunter-khaki.vercel.app"],
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

JOBS = {}   # tiny in-memory store (uuid -> status)

def google_similar_urls(pil_image: Image.Image, max_results: int = 50) -> list[str]:
    """
    Returns a list of *raw* image URLs that Google Lens considers similar.
    Very small footprint – no Selenium, no external services.
    """
    # 1.  Save as JPEG in memory
    buf = io.BytesIO()
    pil_image.save(buf, format="JPEG")
    buf.seek(0)

    # 2.  Upload to Google Lens
    files = {"encoded_image": ("image.jpg", buf, "image/jpeg")}
    params = {"hl": "en"}
    resp = requests.post(GOOGLE_REVERSE_URL, files=files, params=params, timeout=30)
    resp.raise_for_status()

    # 3.  Very crude parser – extract URLs that end with image extensions
    import re
    urls = re.findall(r'(https?://[^"\']+\.(?:jpg|jpeg|png|webp))', resp.text, re.I)
    return list(dict.fromkeys(urls))[:max_results]   # de-duplicate

# ------------------------------------------------------------------
# 2.  FastAPI endpoint
# ------------------------------------------------------------------
class UploadRequest(BaseModel):
    max_num: int = 50

class Request(BaseModel):
    keyword: str
    max_num: int = 50
    
@app.post("/crawl-by-upload")
def crawl_by_upload(file: UploadFile, max_num: int = 50):
    """
    User uploads an image → we fetch similar images → download them.
    Returns exactly the same shape as /crawl so the front-end can poll /status
    and /download with the returned job_id.
    """
    max_num = min(max_num, 200)

    # 1.  Validate image
    try:
        pil_image = Image.open(file.file)
    except Exception:
        raise HTTPException(400, "Invalid image file")

    # 2.  Create job exactly like /crawl does
    uid = str(uuid.uuid4())
    JOBS[uid] = {"status": "running", "msg": ""}
    output_dir = f"images/{uid}"
    os.makedirs(output_dir, exist_ok=True)

    def done():
        JOBS[uid].update(status="done", msg="Downloaded similar images")

    def error(msg):
        JOBS[uid].update(status="error", msg=msg)

    # 3.  Fetch similar URLs then download them
    try:
        similar = google_similar_urls(pil_image, max_num)
        if not similar:
            error("No similar images found")
            return {"job_id": uid}

        # Re-use icrawler’s downloader only (no search)
        from icrawler import ImageDownloader
        from icrawler.utils import Downloader

        class DirectDownloader(ImageDownloader):
            def get_filename(self, task, default_ext):
                return f"{task['file_idx']}.{default_ext}"

        downloader = DirectDownloader(root_dir=output_dir)
        for idx, url in enumerate(similar):
            downloader.download(
                task={"file_url": url, "file_idx": f"{idx:05d}"},
                default_ext="jpg",
                timeout=10,
            )
        done()
    except Exception as e:
        error(str(e))

    return {"job_id": uid}


@app.post("/crawl")
def crawl(req: Request):
    req.max_num = min(req.max_num, 200)
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
