import uuid, os, shutil
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from icrawler.builtin import GoogleImageCrawler
import base64, io, requests
from PIL import Image
from fastapi import UploadFile
import base64, io, requests
from PIL import Image
from fastapi import Form

HF_URL = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-base"

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://image-hunter-khaki.vercel.app"],
    # allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

JOBS = {}   # tiny in-memory store (uuid -> status)

def image_to_keywords(pil_image: Image.Image) -> str:
    try:
        buf = io.BytesIO()
        pil_image.save(buf, format="JPEG")
        b64 = base64.b64encode(buf.getvalue()).decode()

        r = requests.post(
            "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-base",
            headers={"Authorization": "Bearer hf_PublicApi"},
            json={"inputs": {"image": b64}},
            timeout=20,
        )
        r.raise_for_status()
        caption = r.json()[0]["generated_text"]
        return caption or "popular"          # never empty
    except Exception as e:
        print("caption failed:", e)          # stays in server log
        return "popular"                     # fallback keyword

# ------------------------------------------------------------------
# 2.  FastAPI endpoint
# ------------------------------------------------------------------
class UploadRequest(BaseModel):
    max_num: int = 50

class Request(BaseModel):
    keyword: str
    max_num: int = 50
    
@app.post("/crawl-by-upload")
def crawl_by_upload(file: UploadFile, max_num: int = Form(50)):
    max_num = min(max_num, 200)

    # 1. validate image
    try:
        pil_image = Image.open(file.file)
    except Exception:
        raise HTTPException(400, "Invalid image file")

    # 2. generate keywords
    try:
        keyword = image_to_keywords(pil_image)
    except Exception as e:
        raise HTTPException(502, f"Caption model failed: {e}")

    # 3. hand-off to the *existing* keyword pipeline
    return crawl(Request(keyword=keyword, max_num=min(max_num, 200)))

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
