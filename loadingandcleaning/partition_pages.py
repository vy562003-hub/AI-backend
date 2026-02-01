
    # %%

from unstructured.partition.pdf import partition_pdf
from unstructured.documents.elements import Element, Text, Image, FigureCaption
from pypdf import PdfReader, PdfWriter
from io import BytesIO
from PIL import Image as PILImage
import base64
import os
import re

base_dir = "../engine.pdf"
pdfPages = "../pdfPages"


def split_pdf_into_pages(input_pdf, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    reader = PdfReader(input_pdf)
    total_pages = len(reader.pages)

    page_files = []

    for i in range(total_pages):
        writer = PdfWriter()
        writer.add_page(reader.pages[i])

        page_path = os.path.join(output_dir, f"page_{i+1}.pdf")
        with open(page_path, "wb") as f:
            writer.write(f)

        page_files.append((i + 1, page_path))

    return page_files


def get_page_pdfs(folder_path):
    files = os.listdir(folder_path)

    files = sorted(
        files,
        key=lambda x: int(re.search(r"\d+", x).group())
    )

    return [(i + 1, os.path.join(folder_path, f)) for i, f in enumerate(files)]


def partition_pages_from_folder(folder_path,start:int,end:int):
    page_files = get_page_pdfs(folder_path)

    # ✅ CHANGE: dict instead of list
    partitioned_pages = {}

    for page_num, base_dir in page_files[start:end]:
        print(f"🔍 Partitioning page {page_num}")

        raw_chunks = partition_pdf(
            filename=base_dir,
            stategy="hi_res",
            include_page_break=True,
            include_image_element=True,
            infer_table_structure=True,
            extract_image_block_types=["Image", "Table", "Figure"],
            extract_image_block_to_payload=True,
            chunking_strategy=None,
        )

        # ✅ CHANGE: page_num → raw_chunks
        partitioned_pages[page_num] = raw_chunks

        print(f"✅ Page {page_num} partitioned ({len(raw_chunks)} elements)")

    return partitioned_pages


""" partitioned_pages = partition_pages_from_folder(pdfPages,4,10)


# ✅ UPDATED DEBUG LOOP
for page_num, raw_chunks in partitioned_pages.items():
    print(f"\n📄 PAGE {page_num}")
    for el in raw_chunks:
        print("Type:", type(el).__name__)
        print("Category:", el.category)
        print("Page:", page_num)
        print("Text:", getattr(el, "text", None))

        # 🔍 IMAGE PREVIEW (unchanged logic)
        
        if isinstance(el, Image) and el.metadata and el.metadata.image_base64:
            img_bytes = base64.b64decode(el.metadata.image_base64)
            img = PILImage.open(BytesIO(img_bytes))
            
            display(img) """





# %%
