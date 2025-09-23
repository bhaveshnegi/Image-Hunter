# keywords.py
import io
from typing import List
from PIL import Image
import torch
import easyocr
import cv2
import numpy as np
from sklearn.cluster import KMeans
from transformers import BlipProcessor, BlipForConditionalGeneration

# ------------------------------
# Load models once (global)
# ------------------------------
processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
reader = easyocr.Reader(['en'])   # OCR
yolo = torch.hub.load("ultralytics/yolov5", "yolov5s", pretrained=True)  # object detection

# ------------------------------
# helpers
# ------------------------------
def _blip_caption(pil_image: Image.Image) -> str:
    inputs = processor(images=pil_image, return_tensors="pt")
    out = model.generate(**inputs, max_length=20)
    return processor.decode(out[0], skip_special_tokens=True)

def _ocr_text(pil_image: Image.Image) -> List[str]:
    arr = np.array(pil_image.convert("RGB"))
    results = reader.readtext(arr)
    return [text for (_, text, conf) in results if conf > 0.6]

def _yolo_objects(pil_image: Image.Image, conf=0.4) -> List[str]:
    arr = np.array(pil_image.convert("RGB"))
    results = yolo(arr)
    df = results.pandas().xyxy[0]
    return df[df["confidence"] > conf]["name"].unique().tolist()

def _dominant_colors(pil_image: Image.Image, n=2) -> List[str]:
    arr = np.array(pil_image.resize((150, 150)))
    arr = arr.reshape((-1, 3))
    kmeans = KMeans(n_clusters=n, random_state=0).fit(arr)
    centers = kmeans.cluster_centers_.astype(int)

    def rgb_to_name(rgb):
        r, g, b = rgb
        if r > 200 and g < 100 and b < 100: return "red"
        if g > 200 and r < 100 and b < 100: return "green"
        if b > 200 and r < 100 and g < 100: return "blue"
        if r > 200 and g > 200: return "yellow"
        return "color"

    return [rgb_to_name(c) for c in centers]

# ------------------------------
# main entry
# ------------------------------
def image_to_keywords(pil_image: Image.Image) -> str:
    try:
        caption = _blip_caption(pil_image)
        texts   = _ocr_text(pil_image)
        objects = _yolo_objects(pil_image)
        colors  = _dominant_colors(pil_image)

        terms = [caption] + texts + objects + colors
        terms = list(dict.fromkeys([t for t in terms if t]))  # unique

        # quote multi-word phrases
        quoted = [f'"{w}"' if " " in w else w for w in terms]
        return " OR ".join(quoted[:8]) or "popular"
    except Exception as e:
        print("keyword extraction failed:", e)
        return "popular"


def extract_keywords(pil_image: Image.Image):
    """Return both search query and raw keyword components."""
    caption = texts = objects = colors = []
    try:
        caption = _blip_caption(pil_image)
        texts   = _ocr_text(pil_image)
        objects = _yolo_objects(pil_image)
        colors  = _dominant_colors(pil_image)

        terms = [caption] + texts + objects + colors
        terms = list(dict.fromkeys([t for t in terms if t]))

        quoted = [f'"{w}"' if " " in w else w for w in terms]
        query = " OR ".join(quoted[:8]) or "popular"

        return {
            "query": query,
            "caption": caption,
            "ocr": texts,
            "objects": objects,
            "colors": colors,
        }
    except Exception as e:
        print("keyword extraction failed:", e)
        return {
            "query": "popular",
            "caption": "",
            "ocr": [],
            "objects": [],
            "colors": []
        }
