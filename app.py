import streamlit as st
import fitz  # PyMuPDF
import os
import requests
import base64
import cloudinary
import cloudinary.uploader
import cloudinary.api
from cloudinary.exceptions import NotFound, BadRequest
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

# --- 3. Advanced Custom Styling (Modern Dark Theme) ---
def apply_custom_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
        
        /* Global Reset */
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: #E0E0E2; }
        .stApp { background: radial-gradient(circle at top right, #1a1c23, #080a0c); }
        
        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: rgba(15, 17, 22, 0.95) !important;
            border-right: 1px solid rgba(255,255,255,0.05);
            backdrop-filter: blur(10px);
        }
        
        /* Glassmorphism Cards */
        .stButton button {
            border-radius: 10px !important;
            background: rgba(255, 255, 255, 0.03) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            font-weight: 200 !important;
            text-align: left !important;
            padding: 10px 15px !important;
        }
        .stButton button:hover {
            background: rgba(74, 144, 226, 0.1) !important;
            border-color: #4A90E2 !important;
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        }

        /* Action Bar Buttons */
        .action-bar-btn button {
            text-align: center !important;
            justify-content: center !important;
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

        /* Preview Container */
        .media-card {
            background: #000;
            border-radius: 20px;
            overflow: hidden;
            border: 1px solid rgba(255,255,255,0.08);
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
            animation: fadeIn 0.6s ease-out;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .media-preview {
            max-width: 100%; border-radius: 8px;
        }

        /* Download Button CSS */
        .download-link {
            display: flex; align-items: center; justify-content: center;
            background: #4A90E2; color: white !important;
            text-decoration: none !important; border-radius: 10px;
            padding: 10px 20px; font-weight: 600; font-size: 14px;
            transition: 0.3s;
        }
        .download-link:hover { background: #357ABD; transform: scale(1.02); }

        /* Custom Scrollbar */
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 10px; }
        </style>
    """, unsafe_allow_html=True)

# --- 4. Cached Logic for Production Performance ---
@st.cache_data(ttl=600) # Cache directory listing for 10 mins
def fetch_cloud_resources(path):
    folders, files = [], []
    try:
        # Get Folders
        sub_folders = cloudinary.api.subfolders(path).get('folders', [])
        folders = [f['name'] for f in sub_folders]
        
        # Get Files (Aggregated search)
        for rt in ['image', 'video', 'raw']:
            res = cloudinary.api.resources(resource_type=rt, type="upload", prefix=path + "/", max_results=100)
            for item in res.get('resources', []):
                # Ensure we only get files in the current directory (not subdirectories)
                if item['public_id'].rsplit('/', 1)[0] == path:
                    item['r_type'] = rt
                    item['display_name'] = item['public_id'].split('/')[-1]
                    files.append(item)
    except Exception as e:
        st.error(f"Vault Connection Error: {e}")
    return sorted(folders), sorted(files, key=lambda x: x['display_name'])

def get_icon(name, r_type):
    ext = name.split('.')[-1].lower()
    icons = {'pdf': '📕', 'doc': '📝', 'docx': '📝', 'xls': '📈', 'xlsx': '📈', 'ppt': '📊', 'pptx': '📊'}
    if r_type == 'image': return "🖼️"
    if r_type == 'video': return "🎬"
    return icons.get(ext, "📄")

# --- 5. Session State Management ---
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
    # Pre-fetch content
    resp = requests.get(file_info['secure_url'])
    st.session_state.file_bytes = resp.content

# --- 6. Sidebar Implementation ---
with st.sidebar:
    st.markdown("<h2 style='text-align:center; color:#4A90E2;'>BCH VAULT</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; font-size:0.8rem; opacity:0.6; margin-bottom:30px;'>Enterprise Asset Management</p>", unsafe_allow_html=True)
    
    # Security Section
    if not st.session_state.auth:
        with st.expander("🔐 Unlock Vault", expanded=False):
            pwd = st.text_input("Access Key", type="password")
            if st.button("Authenticate", use_container_width=True):
                if pwd == ADMIN_PASSWORD:
                    st.session_state.auth = True
                    st.toast("Access Granted", icon="✅")
                    st.rerun()
                else: st.error("Invalid Key")
    else:
        st.success("Admin Access Active")
        if st.button("Lock Vault", use_container_width=True):
            st.session_state.auth = False
            st.rerun()

    st.divider()
    
    # Navigation Buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🏠 Home", use_container_width=True): navigate_to(ROOT_FOLDER)
    with col2:
        if st.button("⬅️ Back", use_container_width=True):
            if st.session_state.path != ROOT_FOLDER:
                navigate_to(st.session_state.path.rsplit('/', 1)[0])

    st.markdown("<p style='font-size:0.7rem; font-weight:800; color:#555; margin: 20px 0 10px 5px;'>EXPLORER</p>", unsafe_allow_html=True)
    
    folders, files = fetch_cloud_resources(st.session_state.path)
    
    # Folders List
    for f in folders:
        path_full = f"{st.session_state.path}/{f}"
        if st.button(f"📁 {f}", key=f"btn_{f}", use_container_width=True):
            navigate_to(path_full)
            
    # Files List
    for i, f in enumerate(files):
        icon = get_icon(f['display_name'], f['r_type'])
        if st.button(f"{icon} {f['display_name']}", key=f"file_{f['public_id']}", use_container_width=True):
            with st.spinner("Decrypting file..."):
                load_file(f, i)
                st.rerun()

# --- 7. Main Interface Logic ---
apply_custom_css()

# Breadcrumb Display
parts = st.session_state.path.split('/')
breadcrumb_text = " • ".join(parts[1:]) if len(parts) > 1 else "Root"
st.markdown(f'''
    <div class="breadcrumb">
        <span style="color:#4A90E2">Vault</span> 
        <span style="opacity:0.4">/</span> 
        <span>{breadcrumb_text}</span>
    </div>
''', unsafe_allow_html=True)

if st.session_state.viewer_file:
    # --- PREVIEW MODE ---
    f = st.session_state.viewer_file
    
    # Header for Preview
    c1, c2 = st.columns([0.8, 0.2])
    with c1:
        st.markdown(f"### {f['display_name']}")
    with c2:
        if st.button("✕ Close Preview", use_container_width=True):
            st.session_state.viewer_file = None
            st.rerun()

    # The Stage (Visualizer)
    with st.container():
        st.markdown('<div class="media-card">', unsafe_allow_html=True)
        
        # PDF Handler
        if f['r_type'] == "raw" and f['display_name'].lower().endswith('.pdf'):
            try:
                doc = fitz.open(stream=st.session_state.file_bytes, filetype="pdf")
                p1, pmain, p2 = st.columns([1, 8, 1])
                with pmain:
                    page = doc.load_page(st.session_state.pdf_page)
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                    img_data = base64.b64encode(pix.tobytes("png")).decode()
                    st.markdown(f'<div style="text-align:center; padding:20px;"><img src="data:image/png;base64,{img_data}" style="max-height:70vh; box-shadow: 0 0 20px rgba(0,0,0,0.5);"></div>', unsafe_allow_html=True)
                    st.markdown(f"<p style='text-align:center; opacity:0.5;'>Page {st.session_state.pdf_page+1} of {len(doc)}</p>", unsafe_allow_html=True)
                
                with p1:
                    st.markdown("<div style='height:30vh'></div>", unsafe_allow_html=True)
                    if st.button("❮", key="p_prev") and st.session_state.pdf_page > 0:
                        st.session_state.pdf_page -= 1
                        st.rerun()
                with p2:
                    st.markdown("<div style='height:30vh'></div>", unsafe_allow_html=True)
                    if st.button("❯", key="p_next") and st.session_state.pdf_page < len(doc) - 1:
                        st.session_state.pdf_page += 1
                        st.rerun()
            except:
                st.info("Preview not supported for this raw format.")
        
        # Image Handler
        elif f['r_type'] == "image":
            img_b64 = base64.b64encode(st.session_state.file_bytes).decode()
            st.markdown(f'<div style="text-align:center; padding:20px;"><img src="data:image/png;base64,{img_b64}" class="media-preview"></div>', unsafe_allow_html=True)
            
        # Video Handler
        elif f['r_type'] == "video":
            st.video(f['secure_url'])
        
        st.markdown('</div>', unsafe_allow_html=True)

    # Action Bar (Professional Footer)
    st.markdown("<br>", unsafe_allow_html=True)
    _, ab1, ab2, ab3, ab4, _ = st.columns([2, 1, 1, 1, 1, 2])
    
    with ab1:
        if st.button("←", use_container_width=True, key="nav_prev"):
            new_idx = (st.session_state.viewer_index - 1) % len(files)
            load_file(files[new_idx], new_idx)
            st.rerun()
            
    with ab2:
        st.markdown(f'<a href="{f["secure_url"]}" target="_blank" class="download-link">Download</a>', unsafe_allow_html=True)

    with ab3:
        if st.session_state.auth:
            if st.button("🗑️ Delete", use_container_width=True):
                cloudinary.uploader.destroy(f['public_id'], resource_type=f['r_type'])
                st.session_state.viewer_file = None
                st.cache_data.clear()
                st.rerun()

    with ab4:
        if st.button("→", use_container_width=True, key="nav_next"):
            new_idx = (st.session_state.viewer_index + 1) % len(files)
            load_file(files[new_idx], new_idx)
            st.rerun()

else:
    # --- FOLDER VIEW ---
    st.markdown("<div style='height: 5vh;'></div>", unsafe_allow_html=True)
    
    # Welcome Section
    st.markdown(f"""
        <div style="background: rgba(74, 144, 226, 0.05); padding: 40px; border-radius: 20px; border: 1px dashed rgba(74, 144, 226, 0.3); text-align: center;">
            <h1 style="margin:0; font-weight:800; letter-spacing:-1px;">Welcome to the Vault</h1>
            <p style="opacity:0.6;">Select a file from the sidebar to view or manage assets.</p>
        </div>
    """, unsafe_allow_html=True)

    if st.session_state.auth:
        st.markdown("<br><br>", unsafe_allow_html=True)
        m1, m2 = st.columns(2)
        
        with m1:
            with st.expander("📁 Create New Directory"):
                new_f = st.text_input("Directory Name")
                if st.button("Initialize Folder", use_container_width=True) and new_f:
                    cloudinary.api.create_folder(f"{st.session_state.path}/{new_f}")
                    st.cache_data.clear()
                    st.rerun()
                    
        with m2:
            with st.expander("📤 Upload New Assets"):
                up_name = st.text_input("Asset Label")
                up_file = st.file_uploader("Select File", type=['pdf', 'png', 'jpg', 'mp4', 'docx', 'xlsx'])
                if st.button("Upload to Cloud", use_container_width=True) and up_file and up_name:
                    with st.status("Uploading asset...", expanded=True) as status:
                        ext = up_file.name.split('.')[-1].lower()
                        rtype = "image" if ext in ['jpg', 'jpeg', 'png'] else "video" if ext in ['mp4', 'mov'] else "raw"
                        pub_id = f"{up_name}.{ext}" if rtype == "raw" else up_name
                        cloudinary.uploader.upload(up_file.read(), folder=st.session_state.path, public_id=pub_id, resource_type=rtype)
                        st.cache_data.clear()
                        status.update(label="Upload Complete!", state="complete")
                    st.rerun()
    else:
        st.markdown("""
            <div style="margin-top: 50px; text-align: center; opacity: 0.3;">
                <p>🔒 Admin panel hidden. Authenticate via sidebar for management tools.</p>
            </div>
        """, unsafe_allow_html=True)

# Footer
st.markdown(f"""
    <div style="position: fixed; bottom: 10px; right: 20px; font-size: 0.7rem; opacity: 0.3;">
        Enterprise Media Manager v2.1 | {datetime.now().year}
    </div>
""", unsafe_allow_html=True)
