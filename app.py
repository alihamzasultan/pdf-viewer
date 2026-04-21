import streamlit as st
import fitz  # PyMuPDF
import requests
import base64
import cloudinary
import cloudinary.uploader
import cloudinary.api
from datetime import datetime

# --- 1. Cloudinary Configuration ---
cloudinary.config(
    cloud_name="dg7joeqah",
    api_key="113129119585444",
    api_secret="v54z2aiNtORNanSQ1ulnkiRMabs",
    secure=True
)

ADMIN_PASSWORD = "Hello@123"
ROOT_FOLDER = "BCH-FILES"

# --- 2. Page Config ---
st.set_page_config(
    page_title="BCH | Enterprise Vault",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 3. Advanced Custom Styling ---
def apply_custom_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
        
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: #E0E0E2; }
        .stApp { background: radial-gradient(circle at top right, #1a1c23, #080a0c); }
        
        /* Sidebar Sticky Header */
        [data-testid="stSidebar"] [data-testid="stSidebarHeader"] {
            position: sticky; top: 0; z-index: 1000;
            background-color: #0f1116 !important;
            padding-bottom: 10px;
        }
        
        /* General Button Styling */
        .stButton button {
            border-radius: 10px !important;
            background: rgba(255, 255, 255, 0.03) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            transition: all 0.3s ease !important;
        }

        /* --- NAVIGATION BUTTONS (SIDE ARROWS) --- */
        /* Targets buttons inside the navigation columns */
        div[data-testid="column"] .nav-btn-container button {
            height: 60px !important;
            width: 60px !important;
            background-color: rgba(255, 255, 255, 0.05) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            color: white !important;
            font-size: 1.5rem !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            margin: 0 auto !important;
            border-radius: 12px !important;
        }
        
        div[data-testid="column"] .nav-btn-container button:hover {
            background-color: rgba(255, 255, 255, 0.15) !important;
            border-color: rgba(255, 255, 255, 0.3) !important;
            transform: scale(1.05);
        }

        /* Media Container */
        .media-card {
            background: #000;
            border-radius: 20px;
            overflow: hidden;
            border: 1px solid rgba(255,255,255,0.08);
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
            display: flex;
            justify-content: center;
            align-items: center;
        }

        .media-preview {
            max-width: 100%;
            max-height: 75vh;
            object-fit: contain;
        }

        .download-link {
            display: block; 
            background: #4A90E2; 
            color: white !important;
            text-decoration: none !important; 
            border-radius: 10px;
            padding: 12px 24px; 
            font-weight: 600; 
            text-align: center;
            transition: 0.3s;
        }
        .download-link:hover { background: #357ABD; transform: translateY(-2px); }
        
        /* Breadcrumbs */
        .breadcrumb {
            background: rgba(255,255,255,0.03);
            padding: 12px 20px;
            border-radius: 12px;
            border: 1px solid rgba(255,255,255,0.05);
            margin-bottom: 25px;
            display: flex; align-items: center; gap: 8px;
            font-size: 0.9rem;
        }
        </style>
    """, unsafe_allow_html=True)

# --- 4. Logic Functions ---
@st.cache_data(ttl=300)
def fetch_cloud_resources(path):
    folders, files = [], []
    try:
        sub_folders = cloudinary.api.subfolders(path).get('folders', [])
        folders = [f['name'] for f in sub_folders]
        for rt in ['image', 'video', 'raw']:
            res = cloudinary.api.resources(resource_type=rt, type="upload", prefix=path + "/", max_results=500)
            for item in res.get('resources', []):
                item_path = item['public_id'].rsplit('/', 1)[0]
                if item_path == path:
                    item['r_type'] = rt
                    item['display_name'] = item['public_id'].split('/')[-1]
                    files.append(item)
    except Exception as e:
        st.error(f"Connection Error: {e}")
    return sorted(folders), sorted(files, key=lambda x: x['display_name'])

def load_file(file_info, index):
    st.session_state.viewer_file = file_info
    st.session_state.viewer_index = index
    st.session_state.pdf_page = 0
    resp = requests.get(file_info['secure_url'])
    st.session_state.file_bytes = resp.content

def navigate_to(new_path):
    st.session_state.path = new_path
    st.session_state.viewer_file = None
    st.cache_data.clear()
    st.rerun()

# --- 5. Session State ---
if "auth" not in st.session_state: st.session_state.auth = False
if "path" not in st.session_state: st.session_state.path = ROOT_FOLDER
if "viewer_file" not in st.session_state: st.session_state.viewer_file = None

# --- 6. Sidebar ---
with st.sidebar:
    st.markdown("<h2 style='text-align:center; color:#4A90E2;'>BCH VAULT</h2>", unsafe_allow_html=True)
    if not st.session_state.auth:
        pwd = st.text_input("Access Key", type="password")
        if st.button("Authenticate", use_container_width=True):
            if pwd == ADMIN_PASSWORD:
                st.session_state.auth = True
                st.rerun()
    else:
        st.success("Admin Active")
        if st.button("Lock Vault", use_container_width=True):
            st.session_state.auth = False
            st.rerun()

    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🏠 Home", use_container_width=True): navigate_to(ROOT_FOLDER)
    with c2:
        if st.button("⬅️ Back", use_container_width=True):
            if st.session_state.path != ROOT_FOLDER:
                navigate_to(st.session_state.path.rsplit('/', 1)[0])

    folders, files = fetch_cloud_resources(st.session_state.path)
    st.markdown("<p style='font-size:0.7rem; color:#555;'>EXPLORER</p>", unsafe_allow_html=True)
    for f in folders:
        if st.button(f"📁 {f}", key=f"fldr_{f}", use_container_width=True):
            navigate_to(f"{st.session_state.path}/{f}")
    for i, f in enumerate(files):
        if st.button(f"📄 {f['display_name']}", key=f"file_{f['public_id']}", use_container_width=True):
            load_file(f, i)
            st.rerun()

# --- 7. Main UI ---
apply_custom_css()

# Breadcrumbs
parts = st.session_state.path.split('/')
breadcrumb_text = " • ".join(parts[1:]) if len(parts) > 1 else "Root"
st.markdown(f'<div class="breadcrumb"><span>Vault</span><span style="opacity:0.4">/</span><span>{breadcrumb_text}</span></div>', unsafe_allow_html=True)

if st.session_state.viewer_file:
    f = st.session_state.viewer_file
    
    # Close Button
    col_title, col_close = st.columns([0.85, 0.15])
    col_title.markdown(f"### {f['display_name']}")
    if col_close.button("✕ Close", use_container_width=True):
        st.session_state.viewer_file = None
        st.rerun()

    # --- THE STAGE (Navigation Buttons Centered) ---
    # Using vertical_alignment="center" to keep arrows in the middle of the image height
    v_prev, v_main, v_next = st.columns([1, 10, 1], vertical_alignment="center")

    with v_prev:
        st.markdown('<div class="nav-btn-container">', unsafe_allow_html=True)
        if st.button("❮", key="main_prev"):
            new_idx = (st.session_state.viewer_index - 1) % len(files)
            load_file(files[new_idx], new_idx)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with v_main:
        st.markdown('<div class="media-card">', unsafe_allow_html=True)
        if f['r_type'] == "image":
            img_b64 = base64.b64encode(st.session_state.file_bytes).decode()
            st.markdown(f'<img src="data:image/png;base64,{img_b64}" class="media-preview">', unsafe_allow_html=True)
        elif f['r_type'] == "video":
            st.video(f['secure_url'])
        elif f['display_name'].lower().endswith('.pdf'):
            try:
                doc = fitz.open(stream=st.session_state.file_bytes, filetype="pdf")
                page = doc.load_page(st.session_state.get('pdf_page', 0))
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                img_data = base64.b64encode(pix.tobytes("png")).decode()
                st.markdown(f'<img src="data:image/png;base64,{img_data}" class="media-preview">', unsafe_allow_html=True)
            except: st.info("Preview error")
        st.markdown('</div>', unsafe_allow_html=True)

    with v_next:
        st.markdown('<div class="nav-btn-container">', unsafe_allow_html=True)
        if st.button("❯", key="main_next"):
            new_idx = (st.session_state.viewer_index + 1) % len(files)
            load_file(files[new_idx], new_idx)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # Download and Delete
    st.markdown("<br>", unsafe_allow_html=True)
    foot1, foot2, foot3 = st.columns([2, 1, 2])
    with foot2:
        st.markdown(f'<a href="{f["secure_url"]}" target="_blank" class="download-link">Download File</a>', unsafe_allow_html=True)
        if st.session_state.auth:
            if st.button("🗑️ Delete Asset", use_container_width=True):
                cloudinary.uploader.destroy(f['public_id'], resource_type=f['r_type'])
                st.session_state.viewer_file = None
                st.cache_data.clear()
                st.rerun()

else:
    # Empty state / Folder View
    st.markdown("<div style='height: 10vh;'></div>", unsafe_allow_html=True)
    st.markdown(f"""
        <div style="background: rgba(74, 144, 226, 0.05); padding: 60px; border-radius: 20px; border: 1px dashed rgba(74, 144, 226, 0.3); text-align: center;">
            <h1 style="margin:0; font-weight:800;">Vault Explorer</h1>
            <p style="opacity:0.6;">Select an asset from the sidebar to begin.</p>
        </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.auth:
        st.markdown("<br>", unsafe_allow_html=True)
        m1, m2 = st.columns(2)
        with m1:
            with st.expander("📁 New Folder"):
                name = st.text_input("Folder Name")
                if st.button("Create") and name:
                    cloudinary.api.create_folder(f"{st.session_state.path}/{name}")
                    st.cache_data.clear()
                    st.rerun()
        with m2:
            with st.expander("📤 Upload Asset"):
                up = st.file_uploader("File")
                if st.button("Upload") and up:
                    ext = up.name.split('.')[-1].lower()
                    rtype = "image" if ext in ['jpg', 'jpeg', 'png'] else "video" if ext in ['mp4', 'mov'] else "raw"
                    cloudinary.uploader.upload(up, folder=st.session_state.path, public_id=up.name.rsplit('.', 1)[0] if rtype != "raw" else up.name, resource_type=rtype)
                    st.cache_data.clear()
                    st.rerun()

st.markdown(f'<div style="position: fixed; bottom: 10px; right: 20px; font-size: 0.7rem; opacity: 0.3;">Enterprise Media Manager | {datetime.now().year}</div>', unsafe_allow_html=True)
