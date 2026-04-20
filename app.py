import streamlit as st
import fitz  # PyMuPDF
import os
import requests
import cloudinary
import cloudinary.uploader
import cloudinary.api

# --- 1. Cloudinary Configuration ---
cloudinary.config(
    cloud_name="dg7joeqah",
    api_key="113129119585444",
    api_secret="v54z2aiNtORNanSQ1ulnkiRMabs",
    secure=True
)

# --- 2. Page Config ---
st.set_page_config(page_title="PDF Cloud Viewer Pro", layout="wide", initial_sidebar_state="expanded")

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
            padding: 10px 30px;
            background: rgba(255,255,255,0.03);
            border-bottom: 1px solid rgba(255,255,255,0.08);
        }

        /* Slide Image Styling */
        [data-testid="stImage"] img {
            border-radius: 8px;
            box-shadow: 0 30px 80px rgba(0,0,0,0.8);
            border: 1px solid rgba(255,255,255,0.1);
            max-height: 82vh !important; 
            width: auto !important;
            margin: 0 auto;
            display: block;
        }

        /* Navigation Buttons */
        button:has(div p:contains("〈")), 
        button:has(div p:contains("〉")) {
            background-color: rgba(255, 255, 255, 0.05) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 50% !important;
            width: 80px !important;
            height: 80px !important;
            color: #ffffff !important;
            font-size: 35px !important;
            transition: all 0.3s ease !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }

        button:has(div p:contains("〈")):hover, 
        button:has(div p:contains("〉")):hover {
            background-color: rgba(255, 255, 255, 0.15) !important;
            transform: scale(1.1);
            border-color: rgba(255, 255, 255, 0.4) !important;
        }

        .page-info {
            color: #555;
            font-family: 'Inter', sans-serif;
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 2px;
            text-align: center;
            margin-top: 15px;
        }
        </style>
    """, unsafe_allow_html=True)

# --- 3. State Management ---
if "page_num" not in st.session_state: st.session_state.page_num = 0
if "file_data" not in st.session_state: st.session_state.file_data = None
if "current_filename" not in st.session_state: st.session_state.current_filename = ""

def reset_state():
    st.session_state.file_data = None
    st.session_state.page_num = 0
    st.session_state.current_filename = ""

# --- 4. Cloudinary Helpers ---
def upload_to_cloudinary(file_bytes, filename):
    try:
        # Upload as 'raw' to preserve PDF structure
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
        resources = cloudinary.api.resources(resource_type="raw")
        return resources.get('resources', [])
    except Exception:
        return []

def rename_cloudinary_file(old_id, new_id):
    try:
        # In Cloudinary raw files, renaming usually requires moving the resource
        cloudinary.uploader.rename(old_id, new_id, resource_type="raw")
        return True
    except Exception as e:
        st.error(f"Rename Error: {e}")
        return False

# --- 5. Sidebar Library & Controls ---
with st.sidebar:
    st.title("📚 PDF Library")
    st.caption("Cloud-synced presentations")
    st.markdown("---")
    
    files = get_cloudinary_files()
    if not files:
        st.info("No PDFs found in cloud.")
    else:
        for f in files:
            # We filter for PDF specifically if other raw files exist
            if f['public_id'].lower().endswith(('.pdf', '')) : 
                if st.button(f"📄 {f['public_id']}", key=f['public_id'], use_container_width=True):
                    with st.spinner("Loading from Cloud..."):
                        resp = requests.get(f['secure_url'])
                        st.session_state.file_data = resp.content
                        st.session_state.current_filename = f['public_id']
                        st.session_state.page_num = 0
                        st.rerun()
    
    st.markdown("---")
    if st.session_state.current_filename:
        st.subheader("Settings")
        new_name = st.text_input("Rename File", value=st.session_state.current_filename)
        if st.button("Save New Name"):
            if rename_cloudinary_file(st.session_state.current_filename, new_name):
                st.session_state.current_filename = new_name
                st.success("Renamed successfully!")
                st.rerun()

# --- 6. Main Logic ---
if st.session_state.file_data is None:
    apply_ultra_style()
    st.markdown("<div style='height: 25vh;'></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("Pro PDF Viewer")
        st.write("Upload a PDF to sync it with your Cloudinary library.")
        uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])
        if uploaded_file:
            with st.spinner("Uploading to Cloudinary..."):
                file_bytes = uploaded_file.read()
                url = upload_to_cloudinary(file_bytes, uploaded_file.name)
                if url:
                    st.session_state.file_data = file_bytes
                    st.session_state.current_filename = uploaded_file.name.split(".")[0]
                    st.session_state.page_num = 0
                    st.rerun()
else:
    apply_ultra_style()
    
    # Elegant Header
    st.markdown('<div class="header-bar">', unsafe_allow_html=True)
    h_col1, h_col2 = st.columns([1, 1])
    with h_col1:
        if st.button("✖ Close Viewer", key="close_btn"):
            reset_state()
            st.rerun()
    with h_col2:
        st.markdown(f"<div style='text-align:right; color:#666; font-size:12px; font-weight:bold;'>FILE: {st.session_state.current_filename.upper()}</div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # PDF Rendering with PyMuPDF
    try:
        doc = fitz.open(stream=st.session_state.file_data, filetype="pdf")
        st.session_state.total_pages = len(doc)
        
        page = doc.load_page(st.session_state.page_num)
        # 3.0 Zoom for high-quality display on large screens
        pix = page.get_pixmap(matrix=fitz.Matrix(3.0, 3.0)) 
        img_bytes = pix.tobytes("png")

        # Navigation Layout
        st.markdown("<div style='height: 2vh;'></div>", unsafe_allow_html=True)
        nav_prev, main_area, nav_next = st.columns([2, 10, 2], vertical_alignment="center")

        with nav_prev:
            if st.button("〈", key="prev") and st.session_state.page_num > 0:
                st.session_state.page_num -= 1
                st.rerun()

        with main_area:
            st.image(img_bytes, use_container_width=True)
            st.markdown(f"<div class='page-info'>PAGE {st.session_state.page_num + 1} / {st.session_state.total_pages}</div>", unsafe_allow_html=True)

        with nav_next:
            if st.button("〉", key="next") and st.session_state.page_num < st.session_state.total_pages - 1:
                st.session_state.page_num += 1
                st.rerun()

    except Exception as e:
        st.error(f"Error viewing PDF: {e}")
        if st.button("Back to Upload"): reset_state()

    # JS for Keyboard Arrows
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
