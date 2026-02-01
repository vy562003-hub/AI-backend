from typing import Dict, List
import statistics

# ================= CONFIG =================
TOLERANCE = 0.12
MIN_CHARS = 20
MIN_ALPHA_RATIO = 0.3


# ================= HELPERS =================
def is_valid_text(text: str) -> bool:
    if not text:
        return False

    text = text.strip()
    if len(text) >= MIN_CHARS or len(text.split()) >= 2:
        alpha = sum(c.isalpha() for c in text)
        return alpha / max(len(text), 1) >= MIN_ALPHA_RATIO

    return False


def get_y_bounds(el):
    if not el.metadata or not el.metadata.coordinates:
        return None, None

    points = el.metadata.coordinates.points
    ys = [p[1] for p in points]
    return min(ys), max(ys)


def estimate_average_row_gap(table_el, page_elements):
    table_top, table_bottom = get_y_bounds(table_el)
    if table_top is None:
        return None

    internal_rows = []

    for el in page_elements:
        if not hasattr(el, "text"):
            continue
        if not el.metadata or not el.metadata.coordinates:
            continue

        top, bottom = get_y_bounds(el)
        if top is None:
            continue

        if table_top <= top <= table_bottom:
            internal_rows.append((top, bottom))

    if len(internal_rows) < 2:
        return None

    internal_rows.sort(key=lambda x: x[0])

    gaps = []
    for i in range(len(internal_rows) - 1):
        gap = internal_rows[i + 1][0] - internal_rows[i][1]
        if gap > 0:
            gaps.append(gap)

    return statistics.mean(gaps) if gaps else None


# ================= CORE LOGIC =================
def process_table_spillover(
    pages: Dict[int, List]
) -> Dict[int, List]:
    """
    Returns:
    {
      page_number: [elements]
    }

    Behavior:
    - Table remains in element list
    - Spillover text is merged into table.text
    - Spillover elements are removed
    """

    processed_pages = {}

    for page_num, elements in pages.items():
        used_indices = set()
        updated_elements = list(elements)

        i = 0
        while i < len(elements):
            el = elements[i]

            # Structural trigger
            if el.category != "Table":
                i += 1
                continue

            table_top, table_bottom = get_y_bounds(el)
            if table_top is None:
                i += 1
                continue

            collected_texts = [el.text.strip()]

            avg_gap = estimate_average_row_gap(el, elements)
            spillover_limit = avg_gap * (1 + TOLERANCE) if avg_gap else 0

            current_bottom = table_bottom
            j = i + 1

            # ---- ITERATIVE SPILLOVER ----
            while j < len(elements):
                next_el = elements[j]

                # Order + Type rule
                if next_el.category != "UncategorizedText":
                    break

                text = (next_el.text or "").strip()
                if not is_valid_text(text):
                    break

                next_top, next_bottom = get_y_bounds(next_el)
                if next_top is None:
                    break

                # Spatial rule
                if next_top > current_bottom + spillover_limit:
                    break

                collected_texts.append(text)
                used_indices.add(j)
                current_bottom = next_bottom
                j += 1

            # 🔥 Merge into SAME Table element
            el.text = "\n".join(collected_texts)

            i = j

        # Remove spillover elements ONLY
        cleaned_elements = [
            el for idx, el in enumerate(updated_elements)
            if idx not in used_indices
        ]

        processed_pages[page_num] = cleaned_elements

    return processed_pages
