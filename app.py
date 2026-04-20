import streamlit as st
import fitz  # PyMuPDF
import os
import requests
import cloudinary
import cloudinary.uploader
import cloudinary.api
from cloudinary.exceptions import NotFound, BadRequest

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
st.set_page_config(page_title="BCH Media Vault", layout="wide", initial_sidebar_state="expanded")

def apply_pro_style():
    st.markdown("""
        <style>
        .stApp { background-color: #080A0C; }
        footer { visibility: hidden !important; }
        header { background-color: rgba(0,0,0,0) !important; }
        [data-testid="stSidebar"] { background-color: #0E1117 !important; border-right: 1px solid rgba(255,255,255,0.05); }
        
        /* Breadcrumb Sidebar */
        .breadcrumb-container {
            display: flex; align-items: center; padding: 12px;
            background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08);
            border-radius: 8px; margin-bottom: 15px;
        }

        /* Sidebar Buttons */
        .stButton button { border-radius: 8px !important; background-color: #1E2127 !important; border: 1px solid #2D3139 !important; color: #E0E0E0 !important; }
        .stButton button:hover { border-color: #4A90E2 !important; color: #4A90E2 !important; }
        
        button[key*="del_"] { color: #555 !important; border: none !important; background: transparent !important; }
        button[key*="del_"]:hover { color: #FF4B4B !important; background: rgba(255,75,75,0.1) !important; }

        /* --- MEDIA VIEWPORT CONTAINMENT --- */
        .media-container {
            display: flex;
            justify-content: center;
            align-items: center;
            width: 100%;
            height: calc(85vh - 60px); /* Strict height limit */
            margin: 0 auto;
            overflow: hidden;
        }

        .media-container img, .media-container video {
            max-width: 100% !important;
            max-height: 100% !important;
            object-fit: contain !important; /* Ensures the whole image/video is visible */
            border-radius: 8px;
            box-shadow: 0 40px 100px rgba(0,0,0,0.8);
            border: 1px solid rgba(255,255,255,0.05);
        }

        .sidebar-heading { color: #555; font-size: 0.7rem; font-weight: 800; text-transform: uppercase; letter-spacing: 1.5px; margin: 20px 0 10px 0; }
        .welcome-banner { background: rgba(74, 144, 226, 0.05); border: 1px solid rgba(74, 144, 226, 0.2); color: #4A90E2; padding: 30px; border-radius: 12px; text-align: center; margin-bottom: 30px; }
        </style>
    """, unsafe_allow_html=True)

# --- 3. State Management ---
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "current_path" not in st.session_state: st.session_state.current_path = ROOT_FOLDER
if "file_data" not in st.session_state: st.session_state.file_data = None
if "current_filename" not in st.session_state: st.session_state.current_filename = ""
if "current_type" not in st.session_state: st.session_state.current_type = ""
if "page_num" not in st.session_state: st.session_state.page_num = 0
if "virtual_folders" not in st.session_state: st.session_state.virtual_folders = set()

# --- 4. Cloudinary Engine ---

def get_items_in_path(path):
    folders, files = set(), []
    for vf in st.session_state.virtual_folders:
        if vf.rsplit('/', 1)[0] == path: folders.add(vf.split('/')[-1])

    try:
        sub_folders_res = cloudinary.api.subfolders(path)
        for folder in sub_folders_res.get('folders', []): folders.add(folder['name'])
    except: pass

    try:
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
            try: cloudinary.api.delete_resources_by_prefix(path + "/", resource_type=rt)
            except: pass
        try: cloudinary.api.delete_folder(path)
        except: pass
        if path in st.session_state.virtual_folders: st.session_state.virtual_folders.remove(path)
        return True
    except: return False

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
            st.rerun()
        else: st.error("Access Denied")

    st.markdown('<p class="sidebar-heading">Location</p>', unsafe_allow_html=True)
    path_parts = st.session_state.current_path.split('/')
    friendly_path = "Home" if len(path_parts) == 1 else "Home > " + " > ".join(path_parts[1:])
    st.markdown(f'<div class="breadcrumb-container"><span style="color:#4A90E2; font-size:0.85rem; font-weight:600;">📂 {friendly_path}</span></div>', unsafe_allow_html=True)
    
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

    st.markdown('<p class="sidebar-heading">Explorer</p>', unsafe_allow_html=True)
    folders, files = get_items_in_path(st.session_state.current_path)

    for f in folders:
        f_path = f"{st.session_state.current_path}/{f}"
        cf, df = st.columns([4, 1])
        with cf:
            if st.button(f"📁 {f}", key=f"folder_{f}", use_container_width=True):
                st.session_state.current_path = f_path
                st.rerun()
        with df:
            if st.session_state.authenticated:
                if st.button("🗑️", key=f"del_f_{f}"):
                    if delete_folder_recursive(f_path): st.rerun()

    for f in files:
        pid, name = f['public_id'], f['display_name']
        cf, df = st.columns([4, 1])
        with cf:
            active = pid == st.session_state.current_filename
            icon = "▶️" if active else "📄"
            if st.button(f"{icon} {name}", key=f"file_{pid}", use_container_width=True):
                resp = requests.get(f['secure_url'])
                st.session_state.file_data = resp.content
                st.session_state.current_filename = pid
                st.session_state.current_type = f['r_type']
                st.session_state.current_url = f['secure_url']
                st.session_state.page_num = 0
                st.rerun()
        with df:
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
        st.markdown(f'<div class="welcome-banner">📂 You are in <b>{display_name}</b> now.<br>{"This folder is empty. Upload below!" if not files and not folders else "Manage your content below."}</div>', unsafe_allow_html=True)
        
        if st.session_state.authenticated:
            if st.session_state.current_path == ROOT_FOLDER:
                with st.expander("📁 Create New Sub-folder"):
                    nf = st.text_input("Folder Name")
                    if st.button("Create"):
                        st.session_state.virtual_folders.add(f"{ROOT_FOLDER}/{nf}")
                        st.session_state.current_path = f"{ROOT_FOLDER}/{nf}"
                        st.rerun()
            with st.expander("📤 Upload Media"):
                un = st.text_input("Display Name")
                uf = st.file_uploader("Select File", type=["pdf", "png", "jpg", "mp4"])
                if st.button("Upload") and uf and un:
                    with st.spinner("Uploading..."):
                        url, rt = perform_upload(uf.read(), f"{un}.{uf.name.split('.')[-1]}", st.session_state.current_path)
                        st.session_state.current_filename = f"{st.session_state.current_path}/{un}"
                        st.session_state.current_type = rt
                        st.session_state.current_url = url
                        st.session_state.file_data = requests.get(url).content
                        st.rerun()
        else: st.info("🔐 Unlock Admin Mode in the sidebar to enable controls.")

else:
    # FILENAME DISPLAY
    clean_n = st.session_state.current_filename.split('/')[-1]
    st.markdown(f"<div style='text-align:center; color:#555; letter-spacing:5px; font-size:11px; margin: 15px 0;'>{clean_n.upper()}</div>", unsafe_allow_html=True)

    # --- RENDERER ---
    if st.session_state.current_type == "raw": # PDF
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
            st.markdown('<div class="media-container">', unsafe_allow_html=True)
            st.image(pix.tobytes("png"), use_container_width=False) # container width False helps manual CSS control
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown(f"<div style='text-align:center; color:#444; font-size:12px; margin-top:10px;'>{st.session_state.page_num+1} / {st.session_state.total_pages}</div>", unsafe_allow_html=True)
        with n2:
            if st.button("〉", key="n") and st.session_state.page_num < st.session_state.total_pages-1:
                st.session_state.page_num += 1
                st.rerun()
    
    elif st.session_state.current_type == "image":
        st.markdown('<div class="media-container">', unsafe_allow_html=True)
        st.image(st.session_state.file_data)
        st.markdown('</div>', unsafe_allow_html=True)
    
    elif st.session_state.current_type == "video":
        st.markdown('<div class="media-container">', unsafe_allow_html=True)
        st.video(st.session_state.current_url)
        st.markdown('</div>', unsafe_allow_html=True)

    # --- ACTION BUTTONS ---
    st.markdown("<br>", unsafe_allow_html=True)
    _, btn_col1, btn_col2, _ = st.columns([5, 2, 2, 5])
    
    with btn_col1:
        ext = st.session_state.current_url.split('.')[-1]
        st.download_button(
            label="Download",
            data=st.session_state.file_data,
            file_name=f"{clean_n}.{ext}",
            mime="application/octet-stream",
            use_container_width=True
        )
    
    with btn_col2:
        if st.button("Close", use_container_width=True):
            st.session_state.file_data = None
            st.rerun()
