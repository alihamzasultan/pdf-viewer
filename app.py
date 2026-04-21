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
    page_title="BCH Vault | Enterprise Asset Manager",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 3. Custom CSS (Professional Dark Theme) ---
def apply_custom_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        /* Global UI */
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: #f0f0f0; }
        .stApp { background-color: #0e1117; }
        
        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: #05070a !important;
            border-right: 1px solid #1e2128;
        }
        
        [data-testid="stSidebarNav"] { display: none; } /* Hide default nav */

        /* Sidebar Buttons */
        .stButton button {
            border-radius: 8px !important;
            background: transparent !important;
            border: 1px solid transparent !important;
            text-align: left !important;
            color: #94a3b8 !important;
            transition: 0.2s all;
        }
        .stButton button:hover {
            background: #1e293b !important;
            color: #3b82f6 !important;
        }
        
        /* Active File Highlight (Simulated) */
        .active-file button {
            background: rgba(59, 130, 246, 0.1) !important;
            border: 1px solid #3b82f6 !important;
            color: #3b82f6 !important;
        }

        /* Center Stage Layout */
        .media-container {
            display: flex;
            justify-content: center;
            align-items: center;
            background: #000000;
            border-radius: 16px;
            border: 1px solid #1e293b;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
            margin: auto;
            overflow: hidden;
            min-height: 400px;
        }

        .img-fluid {
            max-width: 100%;
            max-height: 80vh;
            object-fit: contain;
        }

        /* Navigation Arrows */
        div[data-testid="column"] .nav-btn button {
            width: 50px !important;
            height: 50px !important;
            background: #1e293b !important;
            border: 1px solid #334155 !important;
            border-radius: 12px !important;
            font-size: 1.2rem !important;
            padding: 0 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            color: white !important;
            margin: auto !important;
        }
        
        div[data-testid="column"] .nav-btn button:hover {
            background: #3b82f6 !important;
            border-color: #60a5fa !important;
        }

        /* Breadcrumb */
        .breadcrumb {
            font-size: 0.85rem;
            color: #64748b;
            margin-bottom: 20px;
            display: flex;
            gap: 10px;
        }

        /* Rename/Download Action Bar */
        .action-link {
            background: #3b82f6;
            color: white !important;
            padding: 10px 20px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 600;
            display: inline-block;
            text-align: center;
        }
        </style>
    """, unsafe_allow_html=True)

# --- 4. Cloudinary Helpers ---
@st.cache_data(ttl=300)
def fetch_vault_contents(path):
    folders, files = [], []
    try:
        f_data = cloudinary.api.subfolders(path).get('folders', [])
        folders = [f['name'] for f in f_data]
        
        for r_type in ['image', 'video', 'raw']:
            res = cloudinary.api.resources(resource_type=r_type, type="upload", prefix=path + "/", max_results=500)
            for item in res.get('resources', []):
                # Ensure the file is directly in the current folder
                if item['public_id'].rsplit('/', 1)[0] == path:
                    item['r_type'] = r_type
                    item['name'] = item['public_id'].split('/')[-1]
                    files.append(item)
    except Exception as e:
        st.error(f"Cloud Connection Error: {e}")
    return sorted(folders), sorted(files, key=lambda x: x['name'])

def rename_asset(old_public_id, new_name, resource_type):
    try:
        folder_path = old_public_id.rsplit('/', 1)[0]
        # Keep extension for raw files
        if resource_type == 'raw' and '.' in old_public_id:
            ext = old_public_id.split('.')[-1]
            if not new_name.endswith(f".{ext}"):
                new_name = f"{new_name}.{ext}"
        
        new_public_id = f"{folder_path}/{new_name}"
        cloudinary.uploader.rename(old_public_id, new_public_id)
        st.cache_data.clear()
        return True, new_public_id
    except Exception as e:
        return False, str(e)

# --- 5. Navigation Logic ---
if "path" not in st.session_state: st.session_state.path = ROOT_FOLDER
if "viewer_file" not in st.session_state: st.session_state.viewer_file = None
if "auth" not in st.session_state: st.session_state.auth = False

def change_folder(new_path):
    st.session_state.path = new_path
    st.session_state.viewer_file = None
    st.cache_data.clear()

def view_file(file_obj, index):
    st.session_state.viewer_file = file_obj
    st.session_state.viewer_index = index
    # Pre-load bytes for PDFs/Images
    resp = requests.get(file_obj['secure_url'])
    st.session_state.file_bytes = resp.content

# --- 6. Sidebar Implementation ---
with st.sidebar:
    st.markdown("<h1 style='color:#3b82f6; font-size:1.5rem;'>BCH VAULT</h1>", unsafe_allow_html=True)
    
    # Auth
    if not st.session_state.auth:
        with st.expander("🔐 Admin Access"):
            p = st.text_input("Key", type="password")
            if st.button("Unlock"):
                if p == ADMIN_PASSWORD:
                    st.session_state.auth = True
                    st.rerun()
    else:
        st.caption("🟢 Administrator Mode")
        if st.button("Logout"): 
            st.session_state.auth = False
            st.rerun()

    st.divider()
    
    # Navigation
    nav1, nav2 = st.columns(2)
    if nav1.button("🏠 Home", use_container_width=True): change_folder(ROOT_FOLDER); st.rerun()
    if nav2.button("⬅️ Up", use_container_width=True):
        if st.session_state.path != ROOT_FOLDER:
            change_folder(st.session_state.path.rsplit('/', 1)[0])
            st.rerun()

    # Explorer
    folders, files = fetch_vault_contents(st.session_state.path)
    
    st.markdown("<br><p style='font-size:0.7rem; color:#475569; font-weight:700;'>DIRECTORIES</p>", unsafe_allow_html=True)
    for f in folders:
        if st.button(f"📁 {f}", key=f"f_{f}", use_container_width=True):
            change_folder(f"{st.session_state.path}/{f}")
            st.rerun()

    st.markdown("<br><p style='font-size:0.7rem; color:#475569; font-weight:700;'>ASSETS</p>", unsafe_allow_html=True)
    for i, f in enumerate(files):
        is_active = st.session_state.viewer_file and st.session_state.viewer_file['public_id'] == f['public_id']
        style_class = "active-file" if is_active else ""
        st.markdown(f'<div class="{style_class}">', unsafe_allow_html=True)
        if st.button(f"📄 {f['name']}", key=f"file_{i}", use_container_width=True):
            view_file(f, i)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# --- 7. Main Content Area ---
apply_custom_css()

# Breadcrumb UI
p_parts = st.session_state.path.split('/')
b_path = " / ".join(p_parts[1:]) if len(p_parts) > 1 else "Root"
st.markdown(f'<div class="breadcrumb"><span>Vault</span> <span>/</span> <span>{b_path}</span></div>', unsafe_allow_html=True)

if st.session_state.viewer_file:
    f = st.session_state.viewer_file
    
    # Viewer Header
    h1, h2 = st.columns([0.8, 0.2])
    h1.subheader(f['name'])
    if h2.button("✕ Close Viewer", use_container_width=True):
        st.session_state.viewer_file = None
        st.rerun()

    # --- CENTERING STAGE ---
    # We use vertical_alignment="center" to keep arrows in the middle regardless of image height
    v_prev, v_content, v_next = st.columns([1, 12, 1], vertical_alignment="center")

    with v_prev:
        st.markdown('<div class="nav-btn">', unsafe_allow_html=True)
        if st.button("❮", key="prev_btn"):
            idx = (st.session_state.viewer_index - 1) % len(files)
            view_file(files[idx], idx)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with v_content:
        st.markdown('<div class="media-container">', unsafe_allow_html=True)
        if f['r_type'] == "image":
            b64 = base64.b64encode(st.session_state.file_bytes).decode()
            st.markdown(f'<img src="data:image/png;base64,{b64}" class="img-fluid">', unsafe_allow_html=True)
        elif f['r_type'] == "video":
            st.video(f['secure_url'])
        elif f['name'].lower().endswith('.pdf'):
            try:
                pdf_doc = fitz.open(stream=st.session_state.file_bytes, filetype="pdf")
                page = pdf_doc.load_page(0) # Preview first page
                pix = page.get_pixmap(matrix=fitz.Matrix(2,2))
                pdf_b64 = base64.b64encode(pix.tobytes("png")).decode()
                st.markdown(f'<img src="data:image/png;base64,{pdf_b64}" class="img-fluid">', unsafe_allow_html=True)
            except: st.warning("PDF Preview Failed")
        st.markdown('</div>', unsafe_allow_html=True)

    with v_next:
        st.markdown('<div class="nav-btn">', unsafe_allow_html=True)
        if st.button("❯", key="next_btn"):
            idx = (st.session_state.viewer_index + 1) % len(files)
            view_file(files[idx], idx)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # --- ACTION BAR ---
    st.markdown("<br>", unsafe_allow_html=True)
    a1, a2, a3 = st.columns([1, 1, 1])
    
    with a1:
        st.markdown(f'<a href="{f["secure_url"]}" target="_blank" class="action-link" style="width:100%">Download Original</a>', unsafe_allow_html=True)
    
    if st.session_state.auth:
        with a2:
            with st.popover("✏️ Rename Asset", use_container_width=True):
                new_n = st.text_input("New Filename", value=f['name'])
                if st.button("Confirm Rename"):
                    success, msg = rename_asset(f['public_id'], new_n, f['r_type'])
                    if success:
                        st.success("Renamed!")
                        st.session_state.viewer_file = None
                        st.rerun()
                    else: st.error(msg)
        with a3:
            if st.button("🗑️ Delete Permanently", use_container_width=True, type="primary"):
                cloudinary.uploader.destroy(f['public_id'], resource_type=f['r_type'])
                st.session_state.viewer_file = None
                st.cache_data.clear()
                st.rerun()

else:
    # --- FOLDER LANDING VIEW ---
    st.markdown("<div style='height: 15vh;'></div>", unsafe_allow_html=True)
    st.markdown(f"""
        <div style='text-align:center; padding: 50px; border: 1px dashed #334155; border-radius: 20px; background: #0f172a;'>
            <h2 style='color:#3b82f6;'>Vault Explorer Active</h2>
            <p style='color:#64748b;'>Select an asset from the sidebar to preview or manage files.</p>
            <code style='color:#94a3b8;'>Path: {st.session_state.path}</code>
        </div>
    """, unsafe_allow_html=True)

    if st.session_state.auth:
        st.markdown("<br>", unsafe_allow_html=True)
        col_up1, col_up2 = st.columns(2)
        with col_up1:
            with st.expander("📤 Upload New Asset"):
                up = st.file_uploader("Choose file")
                if st.button("Upload to Cloud") and up:
                    ext = up.name.split('.')[-1].lower()
                    rt = "image" if ext in ['jpg','jpeg','png','webp'] else "video" if ext in ['mp4','mov'] else "raw"
                    cloudinary.uploader.upload(up, folder=st.session_state.path, public_id=up.name.rsplit('.',1)[0] if rt != "raw" else up.name, resource_type=rt)
                    st.cache_data.clear()
                    st.rerun()
        with col_up2:
            with st.expander("📁 Create Sub-Directory"):
                fn = st.text_input("Directory Name")
                if st.button("Initialize Folder") and fn:
                    cloudinary.api.create_folder(f"{st.session_state.path}/{fn}")
                    st.cache_data.clear()
                    st.rerun()

st.markdown(f'<div style="position: fixed; bottom: 10px; right: 20px; font-size: 0.7rem; color: #475569;">BCH Vault v3.0 | {datetime.now().year}</div>', unsafe_allow_html=True)
