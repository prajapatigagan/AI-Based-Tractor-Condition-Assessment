import cv2
import numpy as np
from PIL import Image

from core.config import MIN_RESOLUTION, BLUR_THRESHOLD, MIN_BRIGHTNESS, MAX_BRIGHTNESS

ANALYSIS_SIZE = 1000  # blur/brightness check isi long-side size par hoga


def check_quality(path):
    # 1) Resolution sirf header se padho, poori image decode kiye bina
    try:
        with Image.open(path) as im:
            w, h = im.size
    except Exception:
        return False, "File corrupt hai ya image nahi hai"

    if min(w, h) < MIN_RESOLUTION:
        return False, f"Resolution kam hai ({w}x{h})"

    # 2) Seedha grayscale mein decode karo (np.fromfile non-ASCII paths par bhi chalta hai)
    try:
        gray = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
    except Exception:
        gray = None
    if gray is None:
        return False, "File corrupt hai ya image nahi hai"

    # 3) Fixed size par laao, taaki score har resolution par comparable rahe
    scale = ANALYSIS_SIZE / max(w, h)
    if scale < 1:
        gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)

    # 4) Sasta check pehle: brightness
    brightness = float(gray.mean())
    if brightness < MIN_BRIGHTNESS:
        return False, "Bahut andhera hai"
    if brightness > MAX_BRIGHTNESS:
        return False, "Bahut zyada bright / overexposed"

    # 5) Mehnga check baad mein: blur
    blur_score = cv2.Laplacian(gray, cv2.CV_32F).var()
    if blur_score < BLUR_THRESHOLD:
        return False, f"Photo blur hai (score {blur_score:.0f})"

    return True, "OK"
