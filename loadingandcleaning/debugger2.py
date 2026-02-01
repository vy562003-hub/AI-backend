from io import BytesIO
from PIL import Image as PILImage
import base64
from unstructured.documents.elements import Image


def debugger(pages: dict):
    """
    Debugger for NEW pipeline format.
    Shows:
    - Elements (Text, NarrativeText, Title, etc.)
    - Tables (resolved + spillover merged)
    - Images (inline preview if base64 exists)
    """

    for page_num, page_data in pages.items():
        print(f"\n📄 PAGE {page_num}")

        # ===============================
        # ELEMENTS
        # ===============================
        elements = page_data.get("elements", [])

        print("\n🧾 ELEMENTS")
        for el in elements:
            print("Type:", type(el).__name__)
            print("Page:", page_num)
            print("Text:", getattr(el, "text", None))

            # 🔍 IMAGE PREVIEW (safe)
            if isinstance(el, Image) and el.metadata and el.metadata.image_base64:
                try:
                    img_bytes = base64.b64decode(el.metadata.image_base64)
                    img = PILImage.open(BytesIO(img_bytes))
                    display(img)
                except Exception as e:
                    print("⚠️ Image preview failed:", e)

            print("----")

        # ===============================
        # TABLES
        # ===============================
        tables = page_data.get("tables", [])

        if tables:
            print("\n📊 TABLES")
            for idx, table_text in enumerate(tables, start=1):
                print(f"\n[TABLE {idx}]")
                print(table_text)

        # ===============================
        # IMAGES (future-proof)
        # ===============================
        images = page_data.get("images", [])
        if images:
            print("\n🖼️ IMAGES (metadata only)")
            for idx, img in enumerate(images, start=1):
                print(f"[IMAGE {idx}] {img}")
