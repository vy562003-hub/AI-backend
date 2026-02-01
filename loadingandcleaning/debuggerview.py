from io import BytesIO
from PIL import Image as PILImage
import base64
import os
import re
from unstructured.documents.elements import Element, Text, Image, FigureCaption

def debugger(partitioned_pages):
    """
    Purpose: one
    """
    # ✅ UPDATED DEBUG LOOP
    for page_num, raw_chunks in partitioned_pages.items():
        print(f"\n📄 PAGE {page_num}")
        for el in raw_chunks:
            print("Type:", type(el).__name__)
            """ print("Category:", el.category) """
            print("Page:", page_num)
            print("Text:", getattr(el, "text", None))   

            # 🔍 IMAGE PREVIEW (unchanged logic)

            if isinstance(el, Image) and el.metadata and el.metadata.image_base64:
                img_bytes = base64.b64decode(el.metadata.image_base64)
                img = PILImage.open(BytesIO(img_bytes))

                display(img)

# end def