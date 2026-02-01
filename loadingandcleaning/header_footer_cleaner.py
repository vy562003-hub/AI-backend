from collections import defaultdict
import re
from typing import Dict, List, Tuple

# ================= CONFIG =================
TOP_PERCENT = 0.15        # top 15% of page
BOTTOM_PERCENT = 0.15     # bottom 15% of page
MIN_TEXT_LEN = 10
REPEAT_THRESHOLD = 0.3    # 30% of pages


# ================= HELPERS =================
def normalize_text(text: str) -> str:
    """Normalize text for robust comparison across pages."""
    text = text.lower()
    text = re.sub(r"\d+", "", text)           # remove digits
    text = re.sub(r"[^\w\s]", "", text)       # remove punctuation
    text = re.sub(r"\s+", " ", text).strip()  # normalize spaces
    return text


def is_valid_candidate(text: str) -> bool:
    """Filter obvious noise before header/footer detection."""
    if not text:
        return False
    if len(text) < MIN_TEXT_LEN:
        return False
    if not re.search(r"\s", text):  # single-token garbage
        return False
    return True


# ================= CORE LOGIC =================
def detect_headers_footers(
    pages: Dict[int, List]
) -> Tuple[set, set]:
    """
    Detect repeating headers and footers.

    pages: { page_number: [unstructured elements] }
    """
    top_candidates = defaultdict(set)
    bottom_candidates = defaultdict(set)

    total_pages = len(pages)

    for page_num, elements in pages.items():
        if not elements:
            continue

        # Collect vertical positions
        y_positions = [
            el.metadata.coordinates.points[0][1]
            for el in elements
            if el.metadata and el.metadata.coordinates
        ]

        if not y_positions:
            continue

        min_y = min(y_positions)
        max_y = max(y_positions)
        page_height = max(max_y - min_y, 1)

        for el in elements:
            if not hasattr(el, "text"):
                continue

            raw_text = el.text.strip()
            if not is_valid_candidate(raw_text):
                continue

            if not el.metadata or not el.metadata.coordinates:
                continue

            norm_text = normalize_text(raw_text)
            y = el.metadata.coordinates.points[0][1]

            if y <= min_y + TOP_PERCENT * page_height:
                top_candidates[norm_text].add(page_num)

            elif y >= max_y - BOTTOM_PERCENT * page_height:
                bottom_candidates[norm_text].add(page_num)

    headers = {
        text
        for text, pages_seen in top_candidates.items()
        if len(pages_seen) / total_pages >= REPEAT_THRESHOLD
    }

    footers = {
        text
        for text, pages_seen in bottom_candidates.items()
        if len(pages_seen) / total_pages >= REPEAT_THRESHOLD
    }

    return headers, footers


def remove_headers_footers(
    pages: Dict[int, List],
    headers: set,
    footers: set
) -> Dict[int, List]:
    """Remove detected headers and footers from pages."""
    cleaned_pages = {}

    for page_num, elements in pages.items():
        cleaned_elements = []

        for el in elements:
            if not hasattr(el, "text"):
                cleaned_elements.append(el)
                continue

            norm = normalize_text(el.text)
            if norm in headers or norm in footers:
                continue

            cleaned_elements.append(el)

        cleaned_pages[page_num] = cleaned_elements

    return cleaned_pages


# ================= PUBLIC API =================
def clean_headers_footers_range(
    partitioned_pages: Dict[int, List],
    start_page: int,
    end_page: int
):
    """
    Clean headers & footers for a specific page range.

    partitioned_pages: { page_number: [elements] }
    """
    page_range = {
        p: els
        for p, els in partitioned_pages.items()
        if start_page <= p <= end_page
    }

    if len(page_range) < 3:
        print("⚠️ Warning: Header/footer detection works best with ≥3 pages")

    headers, footers = detect_headers_footers(page_range)

    print(f"🧹 Headers detected: {len(headers)}")
    print(f"🧹 Footers detected: {len(footers)}")

    cleaned_pages = remove_headers_footers(page_range, headers, footers)

    return cleaned_pages     
    
    
""" , headers, footers """
