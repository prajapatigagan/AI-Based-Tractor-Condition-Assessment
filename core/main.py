import os, glob
from core.config import INPUT_FOLDER, OUTPUT_PDF, IMAGE_EXTENSIONS
from core.quality_check import check_quality
from core.image_analysis import summarize_image
from core.pdf_report import make_pdf


def get_images(folder):
    files = []
    for ext in IMAGE_EXTENSIONS:
        files += glob.glob(os.path.join(folder, ext))
    return files


def run():
    accepted, rejected = [], []

    for path in get_images(INPUT_FOLDER):
        ok, reason = check_quality(path)
        if not ok:
            rejected.append((path, reason))
            print("REJECT:", os.path.basename(path), "-", reason)
            continue

        print("Analysing:", os.path.basename(path))
        accepted.append((path, summarize_image(path)))

    make_pdf(accepted, rejected, OUTPUT_PDF)
    print("PDF ready:", OUTPUT_PDF)


if __name__ == "__main__":
    run()