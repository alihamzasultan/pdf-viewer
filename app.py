import streamlit as st
import fitz  # PyMuPDF
import aspose.slides as slides
import os
import requests
import cloudinary
import cloudinary.uploader
import cloudinary.api
from io import BytesIO

# --- 1. Cloudinary Configuration ---
cloudinary.config(
    cloud_name="dg7joeqah",
    api_key="113129119585444",
    api_secret="v54z2aiNtORNanSQ1ulnkiRMabs",
    secure=True
)

# --- 2. Page Config ---
st.set_page_config(page_title="Pro Slide Viewer", layout="wide", initial_sidebar_state="expanded")

def apply_ultra_style():
    st.markdown("""
        <style>
        .stApp { background-color: #0B0E11; }
        header, footer { visibility: hidden !important; }
        [data-testid="block-container"] { padding: 0rem !important; max-width: 100% !important; }
        
        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background-color: #161a1d !important;
            border-right: 1px solid rgba(255,255,255,0.1);
        }

        .header-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 30px;
            background: rgba(255,255,255,0.03);
            border-bottom: 1px solid rgba(255,255,255,0.08);
        }

        [data-testid="stImage"] img {
            border-radius: 4px;
            box-shadow: 0 30px 60px rgba(0,0,0,0.9);
            border: 1px solid rgba(255,255,255,0.1);
            max-height: 85vh !important; 
            width: auto !important;
            margin: 0 auto;
            display: block;
        }

        button:has(div p:contains("〈")), 
        button:has(div p:contains("〉")) {
            background-color: rgba(255, 255, 255, 0.04) !important;
            border: 1px solid rgba(255, 255, 255, 0.15) !important;
            border-radius: 50% !important;
            width: 80px !important;
            height: 80px !important;
            color: #ffffff !important;
            font-size: 35px !important;
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }

        button:has(div p:contains("〈")):hover, 
        button:has(div p:contains("〉")):hover {
            background-color: rgba(255, 255, 255, 0.15) !important;
            transform: scale(1.1);
        }

        .page-info {
            color: #666;
            font-family: 'Inter', sans-serif;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 2px;
            text-align: center;
            margin-top: 10px;
        }
        </style>
    """, unsafe_allow_html=True)

# --- 3. State Management ---
if "page_num" not in st.session_state: st.session_state.page_num = 0
if "file_data" not in st.session_state: st.session_state.file_data = None
if "current_filename" not in st.session_state: st.session_state.current_filename = ""
if "refresh_sidebar" not in st.session_state: st.session_state.refresh_sidebar = False

def reset_state():
    st.session_state.file_data = None
    st.session_state.page_num = 0
    st.session_state.current_filename = ""
    if os.path.exists("temp_ppt.pptx"): os.remove("temp_ppt.pptx")

# --- 4. Cloudinary Helpers ---
def upload_to_cloudinary(file_bytes, filename):
    try:
        # Use resource_type="raw" for non-image files like PDF/PPTX
        response = cloudinary.uploader.upload(
            file_bytes, 
            public_id=filename.split('.')[0], 
            resource_type="raw",
            overwrite=True
        )
        return response['secure_url']
    except Exception as e:
        st.error(f"Cloudinary Upload Error: {e}")
        return None

def get_cloudinary_files():
    try:
        # Fetching raw resources (PDFs/PPTs)
        resources = cloudinary.api.resources(resource_type="raw")
        return resources.get('resources', [])
    except Exception:
        return []

def rename_cloudinary_file(old_id, new_id):
    try:
        cloudinary.uploader.rename(old_id, new_id, resource_type="raw")
        return True
    except Exception as e:
        st.error(f"Rename Error: {e}")
        return False

# --- 5. Sidebar Library ---
with st.sidebar:
    st.title("📂 Library")
    st.markdown("---")
    
    # List files from Cloudinary
    files = get_cloudinary_files()
    if not files:
        st.info("No files in cloud storage.")
    else:
        for f in files:
            col1, col2 = st.columns([4, 1])
            with col1:
                if st.button(f"📄 {f['public_id']}", key=f['public_id'], use_container_width=True):
                    # Download file data to view it
                    resp = requests.get(f['secure_url'])
                    st.session_state.file_data = resp.content
                    st.session_state.file_ext = f['format'] if 'format' in f else f['url'].split('.')[-1]
                    st.session_state.current_filename = f['public_id']
                    st.session_state.page_num = 0
                    st.rerun()
    
    st.markdown("---")
    if st.session_state.current_filename:
        st.subheader("Edit Current File")
        new_name = st.text_input("Rename to:", value=st.session_state.current_filename)
        if st.button("Apply Rename"):
            if rename_cloudinary_file(st.session_state.current_filename, new_name):
                st.session_state.current_filename = new_name
                st.success("Renamed!")
                st.rerun()

# --- 6. Main View Logic ---
if st.session_state.file_data is None:
    apply_ultra_style()
    st.markdown("<div style='height: 20vh;'></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("Presentation Viewer Pro")
        uploaded_file = st.file_uploader("Upload to Cloud & View (PDF/PPTX)", type=["pdf", "pptx"])
        if uploaded_file:
            with st.spinner("Uploading to Cloudinary..."):
                file_bytes = uploaded_file.read()
                url = upload_to_cloudinary(file_bytes, uploaded_file.name)
                if url:
                    st.session_state.file_data = file_bytes
                    st.session_state.file_ext = uploaded_file.name.split(".")[-1].lower()
                    st.session_state.current_filename = uploaded_file.name.split(".")[0]
                    st.rerun()
else:
    apply_ultra_style()
    
    # Header
    st.markdown('<div class="header-bar">', unsafe_allow_html=True)
    h_col1, h_col2 = st.columns([1, 1])
    with h_col1:
        if st.button("✖ Close & Exit", key="close_btn"):
            reset_state()
            st.rerun()
    with h_col2:
        st.markdown(f"<div style='text-align:right; color:#777; font-size:12px;'>VIEWING: {st.session_state.current_filename.upper()}</div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Rendering
    img_bytes = None
    try:
        if st.session_state.file_ext == "pdf":
            doc = fitz.open(stream=st.session_state.file_data, filetype="pdf")
            st.session_state.total_pages = len(doc)
            page = doc.load_page(st.session_state.page_num)
            pix = page.get_pixmap(matrix=fitz.Matrix(2.5, 2.5)) 
            img_bytes = pix.tobytes("png")
        else:
            with open("temp_ppt.pptx", "wb") as f: f.write(st.session_state.file_data)
            with slides.Presentation("temp_ppt.pptx") as pres:
                st.session_state.total_pages = len(pres.slides)
                slide = pres.slides[st.session_state.page_num]
                img_path = f"tmp_{st.session_state.page_num}.png"
                slide.get_image(2.0, 2.0).save(img_path)
                with open(img_path, "rb") as f: img_bytes = f.read()
                os.remove(img_path)

        # Navigation Layout
        nav_prev, main_area, nav_next = st.columns([2, 10, 2], vertical_alignment="center")

        with nav_prev:
            if st.button("〈", key="nav_prev_btn") and st.session_state.page_num > 0:
                st.session_state.page_num -= 1
                st.rerun()

        with main_area:
            if img_bytes:
                st.image(img_bytes, use_container_width=True)
                st.markdown(f"<div class='page-info'>SLIDE {st.session_state.page_num + 1} OF {st.session_state.total_pages}</div>", unsafe_allow_html=True)

        with nav_next:
            if st.button("〉", key="nav_next_btn") and st.session_state.page_num < st.session_state.total_pages - 1:
                st.session_state.page_num += 1
                st.rerun()

    except Exception as e:
        st.error(f"Render Error: {e}")
        if st.button("Reset View"): reset_state()

    # Keyboard logic
    st.components.v1.html("""
        <script>
        const doc = window.parent.document;
        doc.onkeydown = function(e) {
            if (e.key === 'ArrowLeft') {
                const btn = Array.from(doc.querySelectorAll('button')).find(el => el.innerText.includes('〈'));
                if(btn) btn.click();
            } else if (e.key === 'ArrowRight') {
                const btn = Array.from(doc.querySelectorAll('button')).find(el => el.innerText.includes('〉'));
                if(btn) btn.click();
            }
        };
        </script>
    """, height=0)
