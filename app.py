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
        
        /* Sidebar Navigation Buttons */
        .stButton button {
            border-radius: 8px !important;
            background: transparent !important;
            border: 1px solid transparent !important;
            text-align: left !important;
            color: #94a3b8 !important;
            transition: 0.2s all;
            padding: 8px 12px !important;
        }
        .stButton button:hover {
            background: #1e293b !important;
            color: #3b82f6 !important;
        }
        
        /* Centered Media Stage */
        .media-stage {
            display: flex;
            justify-content: center;
            align-items: center;
            background: #000000;
            border-radius: 20px;
            border: 1px solid #1e293b;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7);
            margin: auto;
            overflow: hidden;
            padding: 10px;
        }

        .img-preview {
            max-width: 100%;
            max-height: 75vh;
            object-fit: contain;
            display: block;
            margin: auto;
        }

        /* Responsive Navigation Arrows */
        div[data-testid="column"] .nav-btn button {
            width: 54px !important;
            height: 54px !important;
            background: rgba(30, 41, 59, 0.7) !important;
            border: 1px solid #334155 !important;
            border-radius: 12px !important;
            font-size: 1.5rem !important;
            color: white !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            margin: auto !important;
            backdrop-filter: blur(5px);
        }
        
        div[data-testid="column"] .nav-btn button:hover {
            background: #3b82f6 !important;
            border-color: #60a5fa !important;
            transform: scale(1.05);
        }

        /* Action Buttons */
        .action-btn {
            background: #3b82f6;
            color: white !important;
            padding: 10px 20px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 600;
            display: block;
            text-align: center;
            transition: 0.3s;
        }
        .action-btn:hover { background: #2563eb; transform: translateY(-2px); }

        /* Custom Scrollbar */
        ::-webkit-scrollbar { width: 5px; }
        ::-webkit-scrollbar-thumb { background: #334155; border-radius: 10px; }
        </style>
    """, unsafe_allow_html=True)

# --- 4. Logic Functions ---
@st.cache_data(ttl=300)
def fetch_vault(path):
    folders, files = [], []
    try:
        f_res = cloudinary.api.subfolders(path).get('folders', [])
        folders = [f['name'] for f in f_res]
        
        for r_type in ['image', 'video', 'raw']:
            res = cloudinary.api.resources(resource_type=r_type, type="upload", prefix=path + "/", max_results=500)
            for item in res.get('resources', []):
                # Only grab files in the current folder (not subfolders)
                if item['public_id'].rsplit('/', 1)[0] == path:
                    item['r_type'] = r_type
                    # We ensure 'name' is always available
                    item['name'] = item['public_id'].split('/')[-1]
                    files.append(item)
    except Exception as e:
        st.error(f"Cloud Error: {e}")
    return sorted(folders), sorted(files, key=lambda x: x['name'])

def rename_asset(old_id, new_name, r_type):
    try:
        folder = old_id.rsplit('/', 1)[0]
        # Preserve extension for 'raw' files like PDFs
        if r_type == 'raw' and '.' in old_id:
            ext = old_id.split('.')[-1]
            if not new_name.lower().endswith(f".{ext}".lower()):
                new_name = f"{new_name}.{ext}"
        
        new_id = f"{folder}/{new_name}"
        cloudinary.uploader.rename(old_id, new_id)
        st.cache_data.clear()
        return True, ""
    except Exception as e:
        return False, str(e)

def load_file(file_obj, index):
    st.session_state.viewer_file = file_obj
    st.session_state.viewer_index = index
    resp = requests.get(file_obj['secure_url'])
    st.session_state.file_bytes = resp.content

# --- 5. Session Initialization ---
if "path" not in st.session_state: st.session_state.path = ROOT_FOLDER
if "viewer_file" not in st.session_state: st.session_state.viewer_file = None
if "auth" not in st.session_state: st.session_state.auth = False

# --- 6. Sidebar Implementation ---
with st.sidebar:
    st.markdown("<h2 style='color:#3b82f6;'>BCH VAULT</h2>", unsafe_allow_html=True)
    
    # Auth Section
    if not st.session_state.auth:
        with st.expander("🔐 Admin Login"):
            p = st.text_input("Access Key", type="password")
            if st.button("Unlock Vault", use_container_width=True):
                if p == ADMIN_PASSWORD:
                    st.session_state.auth = True
                    st.rerun()
    else:
        st.success("Admin Access: ON")
        if st.button("Lock Vault", use_container_width=True):
            st.session_state.auth = False
            st.rerun()

    st.divider()
    
    # Navigation Buttons
    c1, c2 = st.columns(2)
    if c1.button("🏠 Home", use_container_width=True):
        st.session_state.path = ROOT_FOLDER
        st.session_state.viewer_file = None
        st.rerun()
    if c2.button("⬅️ Back", use_container_width=True):
        if st.session_state.path != ROOT_FOLDER:
            st.session_state.path = st.session_state.path.rsplit('/', 1)[0]
            st.session_state.viewer_file = None
            st.rerun()

    # Explorer
    folders, files = fetch_vault(st.session_state.path)
    
    st.markdown("<p style='font-size:0.7rem; color:#475569; font-weight:bold; margin-top:20px;'>FOLDERS</p>", unsafe_allow_html=True)
    for f in folders:
        if st.button(f"📁 {f}", key=f"f_{f}", use_container_width=True):
            st.session_state.path = f"{st.session_state.path}/{f}"
            st.session_state.viewer_file = None
            st.rerun()

    st.markdown("<p style='font-size:0.7rem; color:#475569; font-weight:bold; margin-top:20px;'>FILES</p>", unsafe_allow_html=True)
    for i, f in enumerate(files):
        # Professional fallback for name key
        display_name = f.get('name', f.get('display_name', 'Unnamed File'))
        if st.button(f"📄 {display_name}", key=f"file_{i}", use_container_width=True):
            load_file(f, i)
            st.rerun()

# --- 7. Main Area ---
apply_custom_css()

# Breadcrumb
st.markdown(f"<div style='color:#64748b; font-size:0.8rem; margin-bottom:15px;'>Vault / {' / '.join(st.session_state.path.split('/')[1:])}</div>", unsafe_allow_html=True)

if st.session_state.viewer_file:
    f = st.session_state.viewer_file
    # Safety get for the name
    current_name = f.get('name', f.get('display_name', 'Unnamed File'))

    # Header
    head_col, close_col = st.columns([0.85, 0.15])
    head_col.subheader(current_name)
    if close_col.button("✕ Close", use_container_width=True):
        st.session_state.viewer_file = None
        st.rerun()

    # --- THE CENTERED STAGE ---
    v_prev, v_mid, v_next = st.columns([1, 10, 1], vertical_alignment="center")

    with v_prev:
        st.markdown('<div class="nav-btn">', unsafe_allow_html=True)
        if st.button("❮", key="go_prev"):
            idx = (st.session_state.viewer_index - 1) % len(files)
            load_file(files[idx], idx)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with v_mid:
        st.markdown('<div class="media-stage">', unsafe_allow_html=True)
        if f['r_type'] == "image":
            b64 = base64.b64encode(st.session_state.file_bytes).decode()
            st.markdown(f'<img src="data:image/png;base64,{b64}" class="img-preview">', unsafe_allow_html=True)
        elif f['r_type'] == "video":
            st.video(f['secure_url'])
        elif current_name.lower().endswith('.pdf'):
            try:
                doc = fitz.open(stream=st.session_state.file_bytes, filetype="pdf")
                pix = doc[0].get_pixmap(matrix=fitz.Matrix(2,2))
                pdf_b64 = base64.b64encode(pix.tobytes("png")).decode()
                st.markdown(f'<img src="data:image/png;base64,{pdf_b64}" class="img-preview">', unsafe_allow_html=True)
            except: st.info("Preview not available for this PDF")
        st.markdown('</div>', unsafe_allow_html=True)

    with v_next:
        st.markdown('<div class="nav-btn">', unsafe_allow_html=True)
        if st.button("❯", key="go_next"):
            idx = (st.session_state.viewer_index + 1) % len(files)
            load_file(files[idx], idx)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # --- ACTION BAR ---
    st.markdown("<br>", unsafe_allow_html=True)
    a1, a2, a3 = st.columns([1, 1, 1])
    
    with a1:
        st.markdown(f'<a href="{f["secure_url"]}" target="_blank" class="action-btn">Download Original</a>', unsafe_allow_html=True)
    
    if st.session_state.auth:
        with a2:
            with st.popover("✏️ Rename Asset", use_container_width=True):
                new_title = st.text_input("New Name", value=current_name)
                if st.button("Update Filename", use_container_width=True):
                    success, err = rename_asset(f['public_id'], new_title, f['r_type'])
                    if success:
                        st.success("Renamed successfully!")
                        st.session_state.viewer_file = None
                        st.rerun()
                    else: st.error(err)
        with a3:
            if st.button("🗑️ Delete Permanently", use_container_width=True, type="primary"):
                cloudinary.uploader.destroy(f['public_id'], resource_type=f['r_type'])
                st.session_state.viewer_file = None
                st.cache_data.clear()
                st.rerun()

else:
    # Empty State
    st.markdown("<div style='height: 15vh;'></div>", unsafe_allow_html=True)
    st.markdown(f"""
        <div style='text-align:center; padding: 60px; border: 1px dashed #334155; border-radius: 24px; background: #0f172a;'>
            <h2 style='color:#3b82f6; font-weight:700;'>BCH Vault Explorer</h2>
            <p style='color:#64748b;'>Select a file from the sidebar to start previewing assets.</p>
        </div>
    """, unsafe_allow_html=True)

    if st.session_state.auth:
        st.markdown("<br>", unsafe_allow_html=True)
        col_u1, col_u2 = st.columns(2)
        with col_u1:
            with st.expander("📤 Upload File"):
                file = st.file_uploader("Select Asset")
                if st.button("Push to Cloud") and file:
                    ext = file.name.split('.')[-1].lower()
                    rtype = "image" if ext in ['jpg','png','jpeg','webp'] else "video" if ext in ['mp4','mov'] else "raw"
                    cloudinary.uploader.upload(file, folder=st.session_state.path, public_id=file.name.rsplit('.',1)[0] if rtype != 'raw' else file.name, resource_type=rtype)
                    st.cache_data.clear()
                    st.rerun()
        with col_u2:
            with st.expander("📁 New Directory"):
                dirname = st.text_input("Folder Name")
                if st.button("Create Folder") and dirname:
                    cloudinary.api.create_folder(f"{st.session_state.path}/{dirname}")
                    st.cache_data.clear()
                    st.rerun()

# Footer
st.markdown(f'<div style="position: fixed; bottom: 10px; right: 20px; font-size: 0.7rem; color: #475569;">BCH Vault v3.1 | {datetime.now().year}</div>', unsafe_allow_html=True)
