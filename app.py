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

# --- 2. Professional Page Config ---
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
        
        [data-testid="stSidebar"] {
            background-color: rgba(15, 17, 22, 0.95) !important;
            border-right: 1px solid rgba(255,255,255,0.05);
            backdrop-filter: blur(10px);
        }
        
        /* Buttons */
        .stButton button {
            border-radius: 10px !important;
            background: rgba(255, 255, 255, 0.03) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            transition: all 0.3s ease !important;
            text-align: left !important;
            padding: 10px 15px !important;
        }
        .stButton button:hover {
            background: rgba(74, 144, 226, 0.1) !important;
            border-color: #4A90E2 !important;
            transform: translateY(-2px);
        }

        /* Nav Arrows (Side Buttons) */
        .nav-col {
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100%;
        }
        
        .side-nav-btn button {
            height: 100px !important;
            width: 100% !important;
            font-size: 2rem !important;
            text-align: center !important;
            background: rgba(255,255,255,0.02) !important;
        }

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

        /* Media Container */
        .media-card {
            background: #000;
            border-radius: 20px;
            overflow: hidden;
            border: 1px solid rgba(255,255,255,0.08);
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
            margin: auto;
        }

        .media-preview {
            max-width: 100%;
            max-height: 70vh;
            object-fit: contain;
            display: block;
            margin: 0 auto;
        }

        .download-link {
            display: block; 
            background: #4A90E2; 
            color: white !important;
            text-decoration: none !important; 
            border-radius: 10px;
            padding: 12px; 
            font-weight: 600; 
            text-align: center;
            margin-top: 10px;
        }
        </style>
    """, unsafe_allow_html=True)

# --- 4. Core Logic ---
@st.cache_data(ttl=300)
def fetch_cloud_resources(path):
    folders, files = [], []
    try:
        # Get Folders
        sub_folders = cloudinary.api.subfolders(path).get('folders', [])
        folders = [f['name'] for f in sub_folders]
        
        # Get Files
        for rt in ['image', 'video', 'raw']:
            # We use prefix to filter by current folder
            res = cloudinary.api.resources(resource_type=rt, type="upload", prefix=path + "/", max_results=500)
            for item in res.get('resources', []):
                # Critical Fix: Ensure the file is directly in THIS folder, not a subfolder
                # Cloudinary public_id is "folder/subfolder/file"
                item_path = item['public_id'].rsplit('/', 1)[0]
                if item_path == path:
                    item['r_type'] = rt
                    item['display_name'] = item['public_id'].split('/')[-1]
                    files.append(item)
    except Exception as e:
        st.error(f"Vault Connection Error: {e}")
    return sorted(folders), sorted(files, key=lambda x: x['display_name'])

def get_icon(name, r_type):
    ext = name.split('.')[-1].lower()
    icons = {'pdf': '📕', 'doc': '📝', 'docx': '📝', 'xls': '📈', 'xlsx': '📈'}
    if r_type == 'image': return "🖼️"
    if r_type == 'video': return "🎬"
    return icons.get(ext, "📄")

# --- 5. Session Management ---
if "auth" not in st.session_state: st.session_state.auth = False
if "path" not in st.session_state: st.session_state.path = ROOT_FOLDER
if "viewer_file" not in st.session_state: st.session_state.viewer_file = None
if "pdf_page" not in st.session_state: st.session_state.pdf_page = 0

def navigate_to(new_path):
    st.session_state.path = new_path
    st.session_state.viewer_file = None
    st.cache_data.clear()
    st.rerun()

def load_file(file_info, index):
    st.session_state.viewer_file = file_info
    st.session_state.viewer_index = index
    st.session_state.pdf_page = 0
    resp = requests.get(file_info['secure_url'])
    st.session_state.file_bytes = resp.content

# --- 6. Sidebar ---
with st.sidebar:
    st.markdown("<h2 style='text-align:center; color:#4A90E2;'>BCH VAULT</h2>", unsafe_allow_html=True)
    
    if not st.session_state.auth:
        with st.expander("🔐 Unlock Vault"):
            pwd = st.text_input("Access Key", type="password")
            if st.button("Authenticate", use_container_width=True):
                if pwd == ADMIN_PASSWORD:
                    st.session_state.auth = True
                    st.rerun()
                else: st.error("Invalid Key")
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

    st.markdown("<p style='font-size:0.7rem; font-weight:800; color:#555; margin-top:20px;'>EXPLORER</p>", unsafe_allow_html=True)
    
    folders, files = fetch_cloud_resources(st.session_state.path)
    
    for f in folders:
        if st.button(f"📁 {f}", key=f"fldr_{f}", use_container_width=True):
            navigate_to(f"{st.session_state.path}/{f}")
            
    for i, f in enumerate(files):
        icon = get_icon(f['display_name'], f['r_type'])
        if st.button(f"{icon} {f['display_name']}", key=f"file_{f['public_id']}", use_container_width=True):
            load_file(f, i)
            st.rerun()

# --- 7. Main UI ---
apply_custom_css()

# Breadcrumbs
parts = st.session_state.path.split('/')
breadcrumb_text = " • ".join(parts[1:]) if len(parts) > 1 else "Root"
st.markdown(f'<div class="breadcrumb"><span style="color:#4A90E2">Vault</span><span style="opacity:0.4">/</span><span>{breadcrumb_text}</span></div>', unsafe_allow_html=True)

if st.session_state.viewer_file:
    f = st.session_state.viewer_file
    
    # Title and Close
    head1, head2 = st.columns([0.8, 0.2])
    head1.markdown(f"### {f['display_name']}")
    if head2.button("✕ Close Viewer", use_container_width=True):
        st.session_state.viewer_file = None
        st.rerun()

    # --- VIEWER STAGE (Side Buttons Layout) ---
    v_prev, v_main, v_next = st.columns([1, 8, 1])

    with v_prev:
        st.markdown('<div class="nav-col">', unsafe_allow_html=True)
        if st.button("❮", key="main_prev", use_container_width=True):
            new_idx = (st.session_state.viewer_index - 1) % len(files)
            load_file(files[new_idx], new_idx)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with v_main:
        st.markdown('<div class="media-card">', unsafe_allow_html=True)
        
        # PDF
        if f['r_type'] == "raw" and f['display_name'].lower().endswith('.pdf'):
            try:
                doc = fitz.open(stream=st.session_state.file_bytes, filetype="pdf")
                page = doc.load_page(st.session_state.pdf_page)
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                img_data = base64.b64encode(pix.tobytes("png")).decode()
                st.markdown(f'<div style="text-align:center; padding:20px;"><img src="data:image/png;base64,{img_data}" style="max-height:65vh; width:auto;"></div>', unsafe_allow_html=True)
                
                # PDF Internal Nav
                p1, p2, p3 = st.columns([1,2,1])
                if p1.button("← Page", use_container_width=True) and st.session_state.pdf_page > 0:
                    st.session_state.pdf_page -= 1
                    st.rerun()
                p2.markdown(f"<p style='text-align:center;'>{st.session_state.pdf_page+1} / {len(doc)}</p>", unsafe_allow_html=True)
                if p3.button("Page →", use_container_width=True) and st.session_state.pdf_page < len(doc)-1:
                    st.session_state.pdf_page += 1
                    st.rerun()
            except: st.info("Preview unavailable for this format.")
        
        # Images
        elif f['r_type'] == "image":
            img_b64 = base64.b64encode(st.session_state.file_bytes).decode()
            st.markdown(f'<img src="data:image/png;base64,{img_b64}" class="media-preview">', unsafe_allow_html=True)
            
        # Video
        elif f['r_type'] == "video":
            st.video(f['secure_url'])
        
        st.markdown('</div>', unsafe_allow_html=True)

    with v_next:
        st.markdown('<div class="nav-col">', unsafe_allow_html=True)
        if st.button("❯", key="main_next", use_container_width=True):
            new_idx = (st.session_state.viewer_index + 1) % len(files)
            load_file(files[new_idx], new_idx)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # Actions
    act1, act2, act3 = st.columns([3, 1, 3])
    with act2:
        st.markdown(f'<a href="{f["secure_url"]}" target="_blank" class="download-link">Download File</a>', unsafe_allow_html=True)
        if st.session_state.auth:
            if st.button("🗑️ Delete Asset", use_container_width=True):
                cloudinary.uploader.destroy(f['public_id'], resource_type=f['r_type'])
                st.session_state.viewer_file = None
                st.cache_data.clear()
                st.rerun()

else:
    # --- FOLDER VIEW ---
    st.markdown("<div style='height: 5vh;'></div>", unsafe_allow_html=True)
    st.markdown(f"""
        <div style="background: rgba(74, 144, 226, 0.05); padding: 60px; border-radius: 20px; border: 1px dashed rgba(74, 144, 226, 0.3); text-align: center;">
            <h1 style="margin:0; font-weight:800;">Vault Explorer</h1>
            <p style="opacity:0.6;">Directory: {st.session_state.path}</p>
        </div>
    """, unsafe_allow_html=True)

    if st.session_state.auth:
        st.markdown("<br>", unsafe_allow_html=True)
        m1, m2 = st.columns(2)
        with m1:
            with st.expander("📁 Create Folder"):
                new_f = st.text_input("Name")
                if st.button("Create", use_container_width=True) and new_f:
                    cloudinary.api.create_folder(f"{st.session_state.path}/{new_f}")
                    st.cache_data.clear()
                    st.rerun()
        with m2:
            with st.expander("📤 Upload File"):
                up_file = st.file_uploader("Select File")
                if st.button("Upload", use_container_width=True) and up_file:
                    ext = up_file.name.split('.')[-1].lower()
                    rtype = "image" if ext in ['jpg', 'jpeg', 'png'] else "video" if ext in ['mp4', 'mov'] else "raw"
                    # Important: Use full path in public_id
                    cloudinary.uploader.upload(
                        up_file, 
                        folder=st.session_state.path, 
                        public_id=up_file.name.rsplit('.', 1)[0] if rtype != "raw" else up_file.name,
                        resource_type=rtype
                    )
                    st.cache_data.clear()
                    st.toast("Uploaded Successfully")
                    st.rerun()

# Footer
st.markdown(f'<div style="position: fixed; bottom: 10px; right: 20px; font-size: 0.7rem; opacity: 0.3;">Enterprise Media Manager | {datetime.now().year}</div>', unsafe_allow_html=True)
