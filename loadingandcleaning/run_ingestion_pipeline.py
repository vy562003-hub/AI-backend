"""
End-to-end ingestion pipeline
Runs on a page range and prepares data for vector DB
"""

from loadingandcleaning.header_footer_cleaner import clean_headers_footers_range
from loadingandcleaning.image_filter import filter_images_per_page
from loadingandcleaning.table_spillover import process_table_spillover
from loadingandcleaning.page_resolver_with_summaries import resolve_pages_with_summaries
from loadingandcleaning.vector_store_builder import store_pages_in_vector_db
from loadingandcleaning.partition_pages import partition_pages_from_folder
from loadingandcleaning.debuggerview import debugger
from loadingandcleaning.debugger2 import debugger as debugger2

# ================= CONFIG =================
PDF_PATH = "engine.pdf"
FOLDER_PATH="./assignment"
START_PAGE = 0
END_PAGE = 1
CHROMA_DIR = "./chroma_store"


# ================= PIPELINE =================
def run_pipeline(pdf_path: str, start_page: int, end_page: int):

    partitioned_pages = partition_pages_from_folder(pdf_path,start_page,end_page)
    """ debugger(partitioned_pages) """
    print(f"🚀 Starting ingestion for pages {start_page}–{end_page}")

    # 1️⃣ Header / Footer removal
    print("🧹 Removing headers & footers...")

    cleaned_pages = clean_headers_footers_range(
        partitioned_pages=partitioned_pages,
        start_page=start_page,
        end_page=end_page,
    )

    print('cleaned_pages',cleaned_pages)
    """ debugger(cleaned_pages) """
    

    # cleaned_pages format:
    # { page_number: [elements] }

    # 2️⃣ Image filtering
    print("🖼️ Filtering useless images...")
    image_filtered_pages = filter_images_per_page(cleaned_pages)

    
    # 3️⃣ Table spillover resolution
    print("📊 Resolving table spillover...")
    table_processed_pages = process_table_spillover(image_filtered_pages)

    print('table_processed_pages',table_processed_pages)
    #debugger(table_processed_pages)

    

    # 4️⃣ Page resolution + summaries
    print("🧠 Resolving pages & generating summaries...")
    resolved_pages = resolve_pages_with_summaries(
        pages=table_processed_pages
        
    )

    print('resolved_pages',resolved_pages)
    #debugger(resolved_pages)

    # 5️⃣ Store in vector DB
    print("🧬 Storing pages in vector database...")
    vectorstore = store_pages_in_vector_db(
        resolved_pages=resolved_pages,
        persist_dir=CHROMA_DIR
    )

    print("✅ Ingestion complete")
    return vectorstore


# ================= RUN =================
""" if __name__ == "__main__":
    run_pipeline(FOLDER_PATH, START_PAGE, END_PAGE)
 """
000000000000000000000000# %%

# %%
