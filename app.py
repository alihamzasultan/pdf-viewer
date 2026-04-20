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
        
        /* Breadcrumb Styling */
        .breadcrumb-container {
            display: flex; align-items: center; padding: 12px;
            background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08);
            border-radius: 8px; margin-bottom: 15px;
        }

        /* Professional Sidebar Buttons */
        .stButton button { 
            border-radius: 8px !important; 
            background-color: #1E2127 !important;
            border: 1px solid #2D3139 !important;
            color: #E0E0E0 !important;
            transition: all 0.2s ease !important;
        }
        .stButton button:hover {
            border-color: #4A90E2 !important;
            color: #4A90E2 !important;
        }
        
        /* Trash Icon Styling */
        button[key*="del_"] { color: #555 !important; border: none !important; background: transparent !important; }
        button[key*="del_"]:hover { color: #FF4B4B !important; background: rgba(255,75,75,0.1) !important; }

        .sidebar-heading { color: #555; font-size: 0.7rem; font-weight: 800; text-transform: uppercase; letter-spacing: 1.5px; margin: 20px 0 10px 0; }
        .welcome-banner { background: rgba(74, 144, 226, 0.05); border: 1px solid rgba(74, 144, 226, 0.2); color: #4A90E2; padding: 30px; border-radius: 12px; text-align: center; margin-bottom: 30px; }
        .media-box img, .media-box video { border-radius: 8px; box-shadow: 0 40px 100px rgba(0,0,0,0.8); border: 1px solid rgba(255,255,255,0.05); max-height: 80vh !important; margin: 0 auto; display: block; }
        </style>
    """, unsafe_allow_html=True)

# --- 3. State Management ---
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "current_path" not in st.session_state: st.session_state.current_path = ROOT_FOLDER
if "file_data" not in st.session_state: st.session_state.file_data = None
if "current_filename" not in st.session_state: st.session_state.current_filename = ""
if "current_type" not in st.session_state: st.session_state.current_type = ""
if "page_num" not in st.session_state: st.session_state.page_num = 0
# Track folders created in this session that might be empty on Cloudinary
if "virtual_folders" not in st.session_state: st.session_state.virtual_folders = set()

# --- 4. Cloudinary Engine ---

def get_items_in_path(path):
    folders, files = set(), []
    
    # Add virtual folders that belong to this path
    for vf in st.session_state.virtual_folders:
        if vf.rsplit('/', 1)[0] == path:
            folders.add(vf.split('/')[-1])

    try:
        # Get actual folders from Cloudinary
        sub_folders_res = cloudinary.api.subfolders(path)
        for folder in sub_folders_res.get('folders', []):
            folders.add(folder['name'])
    except: pass
    
    try:
        # Get Files
        for rt in ['image', 'video', 'raw']:
            res = cloudinary.api.resources(resource_type=rt, type="upload", prefix=path + "/", max_results=100)
            for item in res.get('resources', []):
                if item['public_id'].rsplit('/', 1)[0] == path:
                    item['r_type'] = rt
                    item['display_name'] = item['public_id'].split('/')[-1]
                    files.append(item)
    except: pass
    
    return sorted(list(folders)), sorted(files, key=lambda x: x['display_name'])

def delete_folder_recursive(path):
    try:
        for rt in ['image', 'video', 'raw']:
            cloudinary.api.delete_resources_by_prefix(path + "/", resource_type=rt)
        cloudinary.api.delete_folder(path)
        # Remove from virtual tracker if present
        if path in st.session_state.virtual_folders:
            st.session_state.virtual_folders.remove(path)
        return True
    except Exception as e:
        # If it was only a virtual folder, just remove it from state
        if path in st.session_state.virtual_folders:
            st.session_state.virtual_folders.remove(path)
            return True
        st.error(f"Deletion failed: {e}")
        return False

def perform_upload(file_bytes, custom_name, folder_path):
    ext = custom_name.split('.')[-1].lower()
    r_type = "image" if ext in ['jpg', 'jpeg', 'png', 'webp'] else "video" if ext in ['mp4', 'mov'] else "raw"
    clean_id = custom_name.rsplit('.', 1)[0]
    resp = cloudinary.uploader.upload(file_bytes, folder=folder_path, public_id=clean_id, resource_type=r_type, overwrite=True)
    return resp['secure_url'], r_type

# --- 5. Sidebar UI ---
with st.sidebar:
    st.markdown("### 🔐 Admin")
    pwd = st.text_input("Password", type="password", placeholder="••••••••", label_visibility="collapsed")
    if st.button("Unlock Vault", use_container_width=True):
        if pwd == ADMIN_PASSWORD:
            st.session_state.authenticated = True
            st.toast("Access Granted", icon="🔓")
        else: st.error("Access Denied")

    st.markdown('<p class="sidebar-heading">Browse Location</p>', unsafe_allow_html=True)
    
    path_parts = st.session_state.current_path.split('/')
    friendly_path = "Home" if len(path_parts) == 1 else "Home > " + " > ".join(path_parts[1:])
    
    st.markdown(f'''
        <div class="breadcrumb-container">
            <span style="font-size:1.1rem; margin-right:8px;">📂</span>
            <span style="color:#4A90E2; font-size:0.85rem; font-weight:600;">{friendly_path}</span>
        </div>
    ''', unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("⬅️ Back", use_container_width=True):
            if st.session_state.current_path != ROOT_FOLDER:
                st.session_state.current_path = st.session_state.current_path.rsplit('/', 1)[0]
                st.rerun()
    with c2:
        if st.button("🏠 Home", use_container_width=True):
            st.session_state.current_path = ROOT_FOLDER
            st.rerun()

    st.markdown('<p class="sidebar-heading">Folders & Files</p>', unsafe_allow_html=True)
    folders, files = get_items_in_path(st.session_state.current_path)

    # Folders Section
    for f in folders:
        f_full_path = f"{st.session_state.current_path}/{f}"
        col_f, col_d_f = st.columns([4, 1])
        with col_f:
            if st.button(f"📁 {f}", key=f"folder_{f}", use_container_width=True):
                st.session_state.current_path = f_full_path
                st.rerun()
        with col_d_f:
            if st.session_state.authenticated:
                if st.button("🗑️", key=f"del_folder_{f}"):
                    if delete_folder_recursive(f_full_path):
                        st.rerun()

    # Files Section
    for f in files:
        pid = f['public_id']
        name = f['display_name']
        col_file, col_del = st.columns([4, 1])
        with col_file:
            icon = "▶️" if pid == st.session_state.current_filename else "📄"
            if st.button(f"{icon} {name}", key=f"file_{pid}", use_container_width=True):
                resp = requests.get(f['secure_url'])
                st.session_state.file_data = resp.content
                st.session_state.current_filename = pid
                st.session_state.current_type = f['r_type']
                st.session_state.current_url = f['secure_url']
                st.session_state.page_num = 0
                st.rerun()
        with col_del:
            if st.session_state.authenticated:
                if st.button("🗑️", key=f"del_file_{pid}"):
                    cloudinary.uploader.destroy(pid, resource_type=f['r_type'])
                    if st.session_state.current_filename == pid: st.session_state.file_data = None
                    st.rerun()

# --- 6. Main Area ---
apply_pro_style()

if st.session_state.file_data is None:
    st.markdown("<div style='height: 10vh;'></div>", unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        curr_name = st.session_state.current_path.split('/')[-1]
        display_name = "Root Library" if curr_name == ROOT_FOLDER else curr_name

        st.markdown(f"""
            <div class="welcome-banner">
                <span style="font-size:2.5rem; display:block; margin-bottom:10px;">📂</span>
                You are in <b>{display_name}</b> now.<br>
                {"This folder is empty. Upload your files below!" if not files and not folders else "Manage your folder content below."}
            </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.authenticated:
            # Folder creation ONLY at root
            if st.session_state.current_path == ROOT_FOLDER:
                with st.expander("📁 Create New Sub-folder"):
                    nf = st.text_input("Folder Name")
                    if st.button("Create"):
                        new_path = f"{ROOT_FOLDER}/{nf}"
                        st.session_state.virtual_folders.add(new_path)
                        st.session_state.current_path = new_path
                        st.rerun()
            
            with st.expander("📤 Upload to this Folder"):
                un = st.text_input("File Display Name")
                uf = st.file_uploader("Select Media", type=["pdf", "png", "jpg", "mp4"])
                if st.button("Confirm & Upload") and uf and un:
                    ext = uf.name.split('.')[-1]
                    with st.spinner("Syncing..."):
                        b = uf.read()
                        url, rt = perform_upload(b, f"{un}.{ext}", st.session_state.current_path)
                        st.session_state.file_data = b
                        st.session_state.current_filename = f"{st.session_state.current_path}/{un}"
                        st.session_state.current_type = rt
                        st.session_state.current_url = url
                        st.rerun()
        else:
            st.info("🔐 Unlock Admin Mode in the sidebar to enable controls.")
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
