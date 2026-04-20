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
        
        /* Navigation Breadcrumb */
        .breadcrumb-container {
            display: flex; align-items: center; padding: 12px;
            background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08);
            border-radius: 8px; margin-bottom: 15px;
        }

        /* Sidebar Buttons */
        .stButton button { border-radius: 8px !important; background-color: #1E2127 !important; border: 1px solid #2D3139 !important; color: #E0E0E0 !important; }
        .stButton button:hover { border-color: #4A90E2 !important; color: #4A90E2 !important; }
        
        /* Trash Icon */
        button[key*="del_"] { color: #555 !important; border: none !important; background: transparent !important; }
        button[key*="del_"]:hover { color: #FF4B4B !important; background: rgba(255,75,75,0.1) !important; }

        /* --- VIEWPORT FIX --- */
        .viewport-wrapper {
            display: flex; justify-content: center; align-items: center;
            width: 100%; height: 70vh; overflow: hidden; margin-top: 10px;
        }
        .viewport-wrapper img, .viewport-wrapper video {
            max-width: 100% !important; max-height: 100% !important;
            object-fit: contain !important; border-radius: 8px;
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
if "current_url" not in st.session_state: st.session_state.current_url = ""
if "page_num" not in st.session_state: st.session_state.page_num = 0
if "virtual_folders" not in st.session_state: st.session_state.virtual_folders = set()

# --- 4. Cloudinary Engine ---

def get_items_in_path(path):
    folders, files = set(), []
    for vf in st.session_state.virtual_folders:
        if vf.rsplit('/', 1)[0] == path: folders.add(vf.split('/')[-1])
    try:
        sub_folders_res = cloudinary.api.subfolders(path)
        for f in sub_folders_res.get('folders', []): folders.add(f['name'])
    except: pass
    try:
        for rt in ['image', 'video', 'raw']:
            res = cloudinary.api.resources(resource_type=rt, type="upload", prefix=path + "/", max_results=100)
            for item in res.get('resources', []):
                # Normalize path check
                if item['public_id'].rsplit('/', 1)[0] == path:
                    item['r_type'] = rt
                    item['display_name'] = item['public_id'].split('/')[-1]
                    files.append(item)
    except: pass
    return sorted(list(folders)), sorted(files, key=lambda x: x['display_name'])

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
    parts = st.session_state.current_path.split('/')
    friendly = "Home" if len(parts) == 1 else "Home > " + " > ".join(parts[1:])
    st.markdown(f'<div class="breadcrumb-container"><span style="color:#4A90E2; font-size:0.85rem; font-weight:600;">📂 {friendly}</span></div>', unsafe_allow_html=True)
    
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
        f_p = f"{st.session_state.current_path}/{f}"
        cf, df = st.columns([4, 1])
        with cf:
            if st.button(f"📁 {f}", key=f"folder_{f}", use_container_width=True):
                st.session_state.current_path = f_p
                st.rerun()
        with df:
            if st.session_state.authenticated:
                if st.button("🗑️", key=f"del_f_{f}"):
                    try:
                        for rt in ['image', 'video', 'raw']: cloudinary.api.delete_resources_by_prefix(f_p + "/", resource_type=rt)
                        cloudinary.api.delete_folder(f_p)
                        st.session_state.virtual_folders.discard(f_p)
                        st.rerun()
                    except: pass

    for f in files:
        pid, name = f['public_id'], f['display_name']
        cf, df = st.columns([4, 1])
        with cf:
            active = pid == st.session_state.current_filename
            icon = "▶️" if active else "📄"
            if st.button(f"{icon} {name}", key=f"file_{pid}", use_container_width=True):
                with st.spinner("Fetching..."):
                    resp = requests.get(f['secure_url'])
                    st.session_state.file_data = resp.content
                    st.session_state.current_filename = pid
                    st.session_state.current_type = f['r_type']
                    st.session_state.current_url = f['secure_url']
                    st.session_state.current_format = f.get('format', f['secure_url'].split('.')[-1])
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
        st.markdown(f'<div class="welcome-banner">📂 You are in <b>{curr_name}</b> now.<br>{"Folder empty. Upload below!" if not files and not folders else "Manage files below."}</div>', unsafe_allow_html=True)
        
        if st.session_state.authenticated:
            if st.session_state.current_path == ROOT_FOLDER:
                with st.expander("📁 Create New Sub-folder"):
                    nf = st.text_input("Folder Name")
                    if st.button("Create"):
                        new_p = f"{ROOT_FOLDER}/{nf}"
                        st.session_state.virtual_folders.add(new_p)
                        st.session_state.current_path = new_p
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
        else: st.info("🔐 Unlock Admin mode to manage content.")

else:
    # FILENAME
    clean_n = st.session_state.current_filename.split('/')[-1]
    st.markdown(f"<div style='text-align:center; color:#555; letter-spacing:5px; font-size:11px; margin: 15px 0;'>{clean_n.upper()}</div>", unsafe_allow_html=True)

    # RENDERER
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
            st.markdown('<div class="viewport-wrapper">', unsafe_allow_html=True)
            st.image(pix.tobytes("png"))
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown(f"<div style='text-align:center; color:#444; font-size:12px; margin-top:10px;'>{st.session_state.page_num+1} / {st.session_state.total_pages}</div>", unsafe_allow_html=True)
        with n2:
            if st.button("〉", key="n") and st.session_state.page_num < st.session_state.total_pages-1:
                st.session_state.page_num += 1
                st.rerun()
    
    elif st.session_state.current_type == "image":
        st.markdown('<div class="viewport-wrapper">', unsafe_allow_html=True)
        st.image(st.session_state.file_data)
        st.markdown('</div>', unsafe_allow_html=True)
    
    elif st.session_state.current_type == "video":
        st.markdown('<div class="viewport-wrapper">', unsafe_allow_html=True)
        st.video(st.session_state.current_url)
        st.markdown('</div>', unsafe_allow_html=True)

    # DOWNLOAD & CLOSE
    st.markdown("<br>", unsafe_allow_html=True)
    _, d_col, c_col, _ = st.columns([5, 2, 2, 5])
    with d_col:
        # We use st.session_state.current_format to ensure the download has the correct extension
        pass
    with c_col:
        if st.button("Close", use_container_width=True):
            st.session_state.file_data = None
            st.rerun()
