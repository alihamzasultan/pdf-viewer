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
st.set_page_config(page_title="Ultra PDF Viewer", layout="wide", initial_sidebar_state="expanded")

def apply_pro_style():
    st.markdown("""
        <style>
        /* Global Background */
        .stApp { background-color: #050708; }
        
        /* UI Cleanup */
        footer { visibility: hidden !important; }
        #MainMenu { visibility: hidden !important; }
        header { background-color: rgba(0,0,0,0) !important; }

        /* Sidebar Toggle */
        [data-testid="stSidebarCollapseButton"] {
            background-color: rgba(255,255,255,0.05) !important;
            border-radius: 8px !important;
            color: white !important;
        }

        /* Remove padding to maximize space */
        [data-testid="block-container"] { 
            padding: 0rem 1rem !important; 
            max-width: 100% !important; 
        }
        
        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background-color: #0e1116 !important;
            border-right: 1px solid rgba(255,255,255,0.05);
        }

        /* --- THE SLIDE SIZE (HUGE) --- */
        [data-testid="stImage"] img {
            border-radius: 4px;
            box-shadow: 0 50px 100px rgba(0,0,0,0.9);
            border: 1px solid rgba(255,255,255,0.08);
            /* Increased height and width */
            max-height: 90vh !important; 
            width: 100% !important;
            margin: 0 auto;
            display: block;
        }

        /* Nav Buttons - Made slightly slimmer for tight side columns */
        button:has(div p:contains("〈")), 
        button:has(div p:contains("〉")) {
            background-color: transparent !important;
            border: 1px solid rgba(255, 255, 255, 0.05) !important;
            border-radius: 50% !important;
            width: 60px !important;
            height: 60px !important;
            color: #ffffff !important;
            font-size: 28px !important;
            transition: all 0.3s ease !important;
        }

        button:has(div p:contains("〈")):hover, 
        button:has(div p:contains("〉")):hover {
            background-color: rgba(255, 255, 255, 0.1) !important;
            border-color: rgba(255, 255, 255, 0.4) !important;
            transform: scale(1.1);
        }

        /* Bottom Exit Button */
        button:has(div p:contains("Exit Viewer")) {
            background-color: rgba(255, 255, 255, 0.03) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            color: #555 !important;
            border-radius: 30px !important;
            font-size: 11px !important;
            padding: 4px 20px !important;
        }
        
        button:has(div p:contains("Exit Viewer")):hover {
            background-color: #ff4b4b !important;
            color: white !important;
        }

        .page-info {
            color: #333;
            font-size: 10px;
            letter-spacing: 4px;
            text-align: center;
            margin-top: 5px;
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
        response = cloudinary.uploader.upload(
            file_bytes, public_id=filename.split('.')[0], 
            resource_type="raw", overwrite=True
        )
        return response['secure_url']
    except Exception: return None

def get_cloudinary_files():
    try:
        resources = cloudinary.api.resources(resource_type="raw", max_results=50)
        return resources.get('resources', [])
    except: return []

def rename_cloudinary_file(old_id, new_id):
    try:
        cloudinary.uploader.rename(old_id, new_id, resource_type="raw")
        return True
    except: return False

# --- 5. Sidebar ---
with st.sidebar:
    st.title("📂 Library")
    search_query = st.text_input("🔍 Search library...", "").strip().lower()
    
    st.markdown("<br>", unsafe_allow_html=True)
    all_files = get_cloudinary_files()
    if all_files:
        filtered = [f for f in all_files if search_query in f['public_id'].lower()]
        for f in filtered:
            label = f"▶️ {f['public_id']}" if f['public_id'] == st.session_state.current_filename else f"📄 {f['public_id']}"
            if st.button(label, key=f['public_id'], use_container_width=True):
                resp = requests.get(f['secure_url'])
                st.session_state.file_data = resp.content
                st.session_state.current_filename = f['public_id']
                st.session_state.page_num = 0
                st.rerun()
    
    if st.session_state.current_filename:
        st.markdown("---")
        new_name = st.text_input("Rename File", value=st.session_state.current_filename)
        if st.button("Apply"):
            if rename_cloudinary_file(st.session_state.current_filename, new_name):
                st.session_state.current_filename = new_name
                st.rerun()

# --- 6. Main Content Area ---
apply_pro_style()

if st.session_state.file_data is None:
    st.markdown("<div style='height: 25vh;'></div>", unsafe_allow_html=True)
    _, c2, _ = st.columns([1, 2, 1])
    with c2:
        st.title("Pro PDF Viewer")
        uploaded_file = st.file_uploader("Upload a PDF to sync", type=["pdf"])
        if uploaded_file:
            file_bytes = uploaded_file.read()
            if upload_to_cloudinary(file_bytes, uploaded_file.name):
                st.session_state.file_data = file_bytes
                st.session_state.current_filename = uploaded_file.name.split(".")[0]
                st.rerun()
else:
    # Invisible spacer for layout
    st.markdown("<div style='height: 1vh;'></div>", unsafe_allow_html=True)

    try:
        doc = fitz.open(stream=st.session_state.file_data, filetype="pdf")
        st.session_state.total_pages = len(doc)
        page = doc.load_page(st.session_state.page_num)
        # High resolution Matrix 3.0
        pix = page.get_pixmap(matrix=fitz.Matrix(3.0, 3.0)) 
        
        # NAVIGATION: [Side, Huge Middle, Side]
        nav_prev, main_area, nav_next = st.columns([0.8, 14.4, 0.8], vertical_alignment="center")

        with nav_prev:
            if st.button("〈", key="prev") and st.session_state.page_num > 0:
                st.session_state.page_num -= 1
                st.rerun()

        with main_area:
            st.image(pix.tobytes("png"), use_container_width=True)
            st.markdown(f"<div class='page-info'>{st.session_state.page_num + 1} / {st.session_state.total_pages}</div>", unsafe_allow_html=True)

        with nav_next:
            if st.button("〉", key="next") and st.session_state.page_num < st.session_state.total_pages - 1:
                st.session_state.page_num += 1
                st.rerun()
        
        # Centered Exit Button at very bottom
        _, exit_col, _ = st.columns([6, 2, 6])
        with exit_col:
            if st.button("✖ Exit Viewer", use_container_width=True):
                reset_state()
                st.rerun()

    except Exception as e:
        st.error(f"Render Error: {e}")
        if st.button("Reset"): reset_state()

    # Keyboard Controls
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
