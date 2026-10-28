import cv2
from core.config import MIN_RESOLUTION, BLUR_THRESHOLD, MIN_BRIGHTNESS, MAX_BRIGHTNESS

def check_quality(path):
    img = cv2.imread(path)
    if img is None:
        return False, "File corrupt hai ya image nahi hai"

    h, w = img.shape[:2]
    if min(h, w) < MIN_RESOLUTION:
        return False, f"Resolution kam hai ({w}x{h})"

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
    if blur_score < BLUR_THRESHOLD:
        return False, f"Photo blur hai (score {blur_score:.0f})"

    brightness = gray.mean()
    if brightness < MIN_BRIGHTNESS:
        return False, "Bahut andhera hai"
    if brightness > MAX_BRIGHTNESS:
        return False, "Bahut zyada bright / overexposed"

    return True, "OK"