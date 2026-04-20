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
# Changed to 'expanded' so it's always there on first load
st.set_page_config(page_title="Pro PDF Viewer", layout="wide", initial_sidebar_state="expanded")

def apply_pro_style():
    st.markdown("""
        <style>
        /* Global Background */
        .stApp { background-color: #080a0c; }
        
        /* Hide Footer and 'Made with Streamlit' Menu but KEEP the Sidebar Toggle */
        footer { visibility: hidden !important; }
        #MainMenu { visibility: hidden !important; }
        header { background-color: rgba(0,0,0,0) !important; }

        /* Make Sidebar Toggle Button Visible and Professional */
        [data-testid="stSidebarCollapseButton"] {
            background-color: rgba(255,255,255,0.05) !important;
            border-radius: 8px !important;
            color: white !important;
            margin-left: 10px !important;
        }

        [data-testid="block-container"] { padding: 1rem 2rem !important; max-width: 100% !important; }
        
        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background-color: #0e1116 !important;
            border-right: 1px solid rgba(255,255,255,0.05);
            width: 300px !important;
        }

        /* Slide Image */
        [data-testid="stImage"] img {
            border-radius: 6px;
            box-shadow: 0 40px 100px rgba(0,0,0,0.7);
            border: 1px solid rgba(255,255,255,0.05);
            max-height: 75vh !important; 
            width: auto !important;
            margin: 0 auto;
            display: block;
        }

        /* Navigation Buttons */
        button:has(div p:contains("〈")), 
        button:has(div p:contains("〉")) {
            background-color: transparent !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 50% !important;
            width: 70px !important;
            height: 70px !important;
            color: #ffffff !important;
            font-size: 30px !important;
            transition: all 0.3s ease !important;
        }

        button:has(div p:contains("〈")):hover, 
        button:has(div p:contains("〉")):hover {
            background-color: rgba(255, 255, 255, 0.05) !important;
            border-color: rgba(255, 255, 255, 0.5) !important;
        }

        /* Bottom Exit Button */
        button:has(div p:contains("Exit Viewer")) {
            background-color: rgba(255, 255, 255, 0.03) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            color: #888 !important;
            border-radius: 20px !important;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        button:has(div p:contains("Exit Viewer")):hover {
            background-color: #ff4b4b !important;
            color: white !important;
        }

        .page-info {
            color: #444;
            font-size: 11px;
            letter-spacing: 2px;
            text-align: center;
            margin-top: 20px;
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

# --- 4. Cloudinary Functions ---
def upload_to_cloudinary(file_bytes, filename):
    try:
        response = cloudinary.uploader.upload(
            file_bytes, public_id=filename.split('.')[0], 
            resource_type="raw", overwrite=True
        )
        return response['secure_url']
    except Exception as e:
        st.error(f"Cloudinary Error: {e}")
        return None

def get_cloudinary_files():
    try:
        resources = cloudinary.api.resources(resource_type="raw")
        return resources.get('resources', [])
    except: return []

def rename_cloudinary_file(old_id, new_id):
    try:
        cloudinary.uploader.rename(old_id, new_id, resource_type="raw")
        return True
    except: return False

# --- 5. Sidebar (Controls) ---
with st.sidebar:
    st.title("📂 Cloud Library")
    st.caption("Select a file or upload a new one below")
    st.markdown("---")
    
    files = get_cloudinary_files()
    if not files:
        st.info("No files in cloud.")
    else:
        for f in files:
            if st.button(f"📄 {f['public_id']}", key=f['public_id'], use_container_width=True):
                with st.spinner("Downloading..."):
                    resp = requests.get(f['secure_url'])
                    st.session_state.file_data = resp.content
                    st.session_state.current_filename = f['public_id']
                    st.session_state.page_num = 0
                    st.rerun()
    
    if st.session_state.current_filename:
        st.markdown("---")
        st.subheader("Manage File")
        new_name = st.text_input("Rename to", value=st.session_state.current_filename)
        if st.button("Save Name"):
            if rename_cloudinary_file(st.session_state.current_filename, new_name):
                st.session_state.current_filename = new_name
                st.rerun()

# --- 6. Main Content Area ---
apply_pro_style()

if st.session_state.file_data is None:
    st.markdown("<div style='height: 20vh;'></div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.title("Pro PDF Viewer")
        st.markdown("Upload a PDF to start viewing. Existing files are in the **Sidebar Library** (left).")
        uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])
        if uploaded_file:
            with st.spinner("Uploading to Cloudinary..."):
                file_bytes = uploaded_file.read()
                if upload_to_cloudinary(file_bytes, uploaded_file.name):
                    st.session_state.file_data = file_bytes
                    st.session_state.current_filename = uploaded_file.name.split(".")[0]
                    st.rerun()
else:
    # FILENAME OVERLAY
    st.markdown(f"<div style='text-align:center; color:rgba(255,255,255,0.2); letter-spacing:5px; font-size:10px; margin-bottom:10px;'>{st.session_state.current_filename.upper()}</div>", unsafe_allow_html=True)

    try:
        doc = fitz.open(stream=st.session_state.file_data, filetype="pdf")
        st.session_state.total_pages = len(doc)
        page = doc.load_page(st.session_state.page_num)
        pix = page.get_pixmap(matrix=fitz.Matrix(2.5, 2.5)) 
        
        # Navigation
        nav_prev, main_area, nav_next = st.columns([2, 10, 2], vertical_alignment="center")

        with nav_prev:
            if st.button("〈", key="prev") and st.session_state.page_num > 0:
                st.session_state.page_num -= 1
                st.rerun()

        with main_area:
            st.image(pix.tobytes("png"), use_container_width=True)
            st.markdown(f"<div class='page-info'>PAGE {st.session_state.page_num + 1} / {st.session_state.total_pages}</div>", unsafe_allow_html=True)

        with nav_next:
            if st.button("〉", key="next") and st.session_state.page_num < st.session_state.total_pages - 1:
                st.session_state.page_num += 1
                st.rerun()
        
        # Centered Exit Button
        _, exit_col, _ = st.columns([5, 2, 5])
        with exit_col:
            if st.button("✖ Exit Viewer", use_container_width=True):
                reset_state()
                st.rerun()

    except Exception as e:
        st.error(f"Error: {e}")
        if st.button("Back"): reset_state()

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
