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

ADMIN_PASSWORD = "Hello@123"
ROOT_FOLDER = "BCH-FILES"

# --- 2. Page Config ---
st.set_page_config(page_title="BCH Cloud Explorer", layout="wide", initial_sidebar_state="expanded")

def apply_pro_style():
    st.markdown("""
        <style>
        .stApp { background-color: #080A0C; }
        footer { visibility: hidden !important; }
        header { background-color: rgba(0,0,0,0) !important; }
        [data-testid="stSidebar"] { background-color: #0E1117 !important; border-right: 1px solid rgba(255,255,255,0.05); }
        
        .sidebar-heading { color: #555; font-size: 0.7rem; font-weight: 800; text-transform: uppercase; letter-spacing: 1.5px; margin: 15px 0 5px 0; }
        
        /* Path Breadcrumb */
        .path-display { color: #4A90E2; font-family: monospace; font-size: 0.8rem; background: #1A1D24; padding: 8px 12px; border-radius: 4px; margin-bottom: 10px; border: 1px solid #2D323B; overflow: hidden; text-overflow: ellipsis; }

        /* Media Viewport */
        .media-box img, .media-box video { border-radius: 8px; box-shadow: 0 40px 100px rgba(0,0,0,0.8); border: 1px solid rgba(255,255,255,0.05); max-height: 82vh !important; margin: 0 auto; display: block; }
        
        .stButton button { border-radius: 6px !important; transition: all 0.2s ease; }
        
        /* Folder vs File Colors */
        button[key*="folder_"] { color: #F4D03F !important; text-align: left !important; border-color: rgba(244,208,63,0.2) !important; }
        button[key*="file_"] { color: #E6E6E6 !important; text-align: left !important; }
        </style>
    """, unsafe_allow_html=True)

# --- 3. State Management ---
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "current_path" not in st.session_state: st.session_state.current_path = ROOT_FOLDER
if "file_data" not in st.session_state: st.session_state.file_data = None
if "current_filename" not in st.session_state: st.session_state.current_filename = ""
if "current_type" not in st.session_state: st.session_state.current_type = ""
if "page_num" not in st.session_state: st.session_state.page_num = 0

# --- 4. Cloudinary Engine ---

def get_items_in_path(path):
    """Fetches subfolders and files for the given path using corrected API methods."""
    folders = []
    files = []
    try:
        # CORRECTED METHOD: subfolders (no underscore)
        sub_folders_res = cloudinary.api.subfolders(path)
        folders = [folder['name'] for folder in sub_folders_res.get('folders', [])]
        
        # Get Files in this specific folder
        for rt in ['image', 'video', 'raw']:
            res = cloudinary.api.resources(resource_type=rt, type="upload", prefix=path + "/", max_results=100)
            for item in res.get('resources', []):
                # Only show items directly in this directory
                if item['public_id'].rsplit('/', 1)[0] == path:
                    item['r_type'] = rt
                    item['display_name'] = item['public_id'].split('/')[-1]
                    files.append(item)
    except Exception as e:
        # Check if folder is just empty/new (Cloudinary throws error if folder doesn't 'exist' yet)
        if "not found" in str(e).lower():
            return [], []
        st.error(f"Sync Error: {e}")
    return sorted(folders), sorted(files, key=lambda x: x['display_name'])

def perform_upload(file_bytes, custom_name, folder_path):
    ext = custom_name.split('.')[-1].lower()
    r_type = "image" if ext in ['jpg', 'jpeg', 'png', 'webp'] else "video" if ext in ['mp4', 'mov'] else "raw"
    clean_id = custom_name.rsplit('.', 1)[0]
    
    resp = cloudinary.uploader.upload(
        file_bytes, 
        folder=folder_path, 
        public_id=clean_id, 
        resource_type=r_type, 
        overwrite=True
    )
    return resp['secure_url'], r_type

# --- 5. Sidebar UI ---
with st.sidebar:
    st.markdown("### 🛡️ Security")
    pwd = st.text_input("Password", type="password", placeholder="Enter Password", label_visibility="collapsed")
    if st.button("Unlock Admin Mode", use_container_width=True):
        if pwd == ADMIN_PASSWORD:
            st.session_state.authenticated = True
            st.toast("Admin Access Active", icon="🔓")
        else:
            st.session_state.authenticated = False
            st.error("Invalid Password")

    st.markdown('<p class="sidebar-heading">Current Location</p>', unsafe_allow_html=True)
    st.markdown(f'<div class="path-display">📂 {st.session_state.current_path}</div>', unsafe_allow_html=True)
    
    # Navigation
    c_back, c_home = st.columns(2)
    with c_back:
        if st.button("⬅️ Back", use_container_width=True):
            if st.session_state.current_path != ROOT_FOLDER:
                st.session_state.current_path = st.session_state.current_path.rsplit('/', 1)[0]
                st.rerun()
    with c_home:
        if st.button("🏠 Home", use_container_width=True):
            st.session_state.current_path = ROOT_FOLDER
            st.rerun()

    st.markdown('<p class="sidebar-heading">Explorer</p>', unsafe_allow_html=True)
    folders, files = get_items_in_path(st.session_state.current_path)

    # Folders
    for f in folders:
        if st.button(f"📁 {f}", key=f"folder_{f}", use_container_width=True):
            st.session_state.current_path += f"/{f}"
            st.rerun()

    # Files
    for f in files:
        pid = f['public_id']
        name = f['display_name']
        col_f, col_d = st.columns([4, 1])
        with col_f:
            active = pid == st.session_state.current_filename
            icon = "▶️" if active else "📄"
            if st.button(f"{icon} {name}", key=f"file_{pid}", use_container_width=True):
                with st.spinner(""):
                    resp = requests.get(f['secure_url'])
                    st.session_state.file_data = resp.content
                    st.session_state.current_filename = pid
                    st.session_state.current_type = f['r_type']
                    st.session_state.current_url = f['secure_url']
                    st.session_state.page_num = 0
                    st.rerun()
        with col_d:
            if st.session_state.authenticated:
                if st.button("🗑️", key=f"del_{pid}"):
                    cloudinary.uploader.destroy(pid, resource_type=f['r_type'])
                    if st.session_state.current_filename == pid: st.session_state.file_data = None
                    st.rerun()

# --- 6. Main Content Area ---
apply_pro_style()

if st.session_state.file_data is None:
    st.markdown("<div style='height: 15vh;'></div>", unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        st.title("BCH Cloud Vault")
        st.caption(f"Folder: {st.session_state.current_path}")
        
        if st.session_state.authenticated:
            with st.expander("➕ New Folder"):
                new_f = st.text_input("Sub-folder Name", placeholder="e.g. Project_Alpha")
                if st.button("Create Folder Context"):
                    # We append to path. Folder physically creates on first upload.
                    st.session_state.current_path += f"/{new_f}"
                    st.rerun()

            with st.expander("📤 Upload to this Folder"):
                up_name = st.text_input("Name this file", placeholder="e.g. final_presentation")
                up_file = st.file_uploader("Select Media", type=["pdf", "png", "jpg", "mp4"])
                if st.button("Upload Now") and up_file and up_name:
                    ext = up_file.name.split('.')[-1]
                    full_name = f"{up_name}.{ext}"
                    with st.spinner("Uploading..."):
                        b = up_file.read()
                        url, rt = perform_upload(b, full_name, st.session_state.current_path)
                        st.session_state.file_data = b
                        st.session_state.current_filename = f"{st.session_state.current_path}/{up_name}"
                        st.session_state.current_type = rt
                        st.session_state.current_url = url
                        st.rerun()
        else:
            st.info("💡 Enter Admin Password in the sidebar to manage this vault.")

else:
    # Viewer
    clean_n = st.session_state.current_filename.split('/')[-1]
    st.markdown(f"<div style='text-align:center; color:#555; letter-spacing:5px; font-size:11px; margin: 15px 0;'>{clean_n.upper()}</div>", unsafe_allow_html=True)

    if st.session_state.current_type == "raw":
        doc = fitz.open(stream=st.session_state.file_data, filetype="pdf")
        st.session_state.total_pages = len(doc)
        page = doc.load_page(st.session_state.page_num)
        pix = page.get_pixmap(matrix=fitz.Matrix(2.5, 2.5))
        
        n1, main, n2 = st.columns([1, 14, 1], vertical_alignment="center")
        with n1:
            if st.button("〈", key="p") and st.session_state.page_num > 0:
                st.session_state.page_num -= 1
                st.rerun()
        with main:
            st.image(pix.tobytes("png"), use_container_width=True)
            st.markdown(f"<div style='text-align:center; color:#444; font-size:12px; margin-top:10px;'>{st.session_state.page_num+1} / {st.session_state.total_pages}</div>", unsafe_allow_html=True)
        with n2:
            if st.button("〉", key="n") and st.session_state.page_num < st.session_state.total_pages-1:
                st.session_state.page_num += 1
                st.rerun()
    
    elif st.session_state.current_type == "image":
        st.markdown('<div class="media-box">', unsafe_allow_html=True)
        st.image(st.session_state.file_data, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    elif st.session_state.current_type == "video":
        st.markdown('<div class="media-box">', unsafe_allow_html=True)
        st.video(st.session_state.current_url)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    _, ex, _ = st.columns([6, 2, 6])
    if ex.button("✖ Close Viewer", use_container_width=True):
        st.session_state.file_data = None
        st.rerun()
