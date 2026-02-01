import base64
import numpy as np
from io import BytesIO
from PIL import Image as PILImage
from typing import Dict, List

# ================= CONFIG =================
MIN_WIDTH_PX = 50
MIN_HEIGHT_PX = 50
NEAR_BLACK_MAX = 40
NEAR_WHITE_MIN = 2225
MIN_AREA_PX = 300 * 300
UNIFORM_PIXEL_THRESHOLD = 0.98
BLACK_FILL_THRESHOLD = 0.85 

# ================= HELPERS =================
def is_useful_image(image_base64: str) -> bool:
    try:
        img_bytes = base64.b64decode(image_base64)
        img = PILImage.open(BytesIO(img_bytes)).convert("L")
    except Exception:
        return False

    width, height = img.size
    area = width * height

    # tiny images → noise
    if area < 50 * 50:
        return False

    pixels = np.array(img)

    # binary mask of dark pixels
    mask = pixels <= NEAR_BLACK_MAX
    black_pixels = np.sum(mask)

    if black_pixels == 0:
        return False

    # bounding box of black region
    ys, xs = np.where(mask)
    x_min, x_max = xs.min(), xs.max()
    y_min, y_max = ys.min(), ys.max()

    box_width = x_max - x_min + 1
    box_height = y_max - y_min + 1
    box_area = box_width * box_height

    # how filled is the bounding box
    fill_ratio = black_pixels / box_area

    aspect_ratio = box_width / max(box_height, 1)

    # 🔥 THIS catches your black circles
    if (
        fill_ratio > 0.75 and          # dense blob
        0.75 < aspect_ratio < 1.25 and # roughly square
        box_area < area * 0.8          # not whole page
    ):
        return False

    return True

# ================= CORE LOGIC =================
def filter_images_per_page(
    pages: Dict[int, List]
) -> Dict[int, List]:
    """
    Remove useless images from each page.

    pages: { page_number: [unstructured elements] }
    """
    cleaned_pages = {}

    for page_num, elements in pages.items():
        print("image cleaning page no",page_num)
        cleaned_elements = []

        for el in elements:
            print("going in elements")
            if el.category != "Image":
                cleaned_elements.append(el)
                continue

            image_b64 = getattr(el.metadata, "image_base64", None)
            if not image_b64:
                print("did not found image attr")
                continue

            if is_useful_image(image_b64):
                cleaned_elements.append(el)
            # else: drop silently (noise image)

        cleaned_pages[page_num] = cleaned_elements

    return cleaned_pages
