import streamlit as st
import fitz  # PyMuPDF
import os
import requests
import base64
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
        
        .breadcrumb-container {
            display: flex; align-items: center; padding: 12px;
            background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08);
            border-radius: 8px; margin-bottom: 15px;
        }

        .stButton button { border-radius: 8px !important; background-color: #1E2127 !important; border: 1px solid #2D3139 !important; color: #E0E0E0 !important; }
        .stButton button:hover { border-color: #4A90E2 !important; color: #4A90E2 !important; }
        
        /* --- CENTERED VIEWPORT FIX --- */
        .viewport-container {
            display: flex; justify-content: center; align-items: center;
            width: 100%; min-height: 60vh; margin-top: 20px;
        }
        .media-preview {
            max-width: 90% !important; max-height: 75vh !important;
            object-fit: contain !important; border-radius: 12px;
            box-shadow: 0 40px 100px rgba(0,0,0,0.8);
            border: 1px solid rgba(255,255,255,0.1);
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

# --- 4. Helper Functions ---
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
                if item['public_id'].rsplit('/', 1)[0] == path:
                    item['r_type'] = rt
                    item['display_name'] = item['public_id'].split('/')[-1]
                    files.append(item)
    except: pass
    return sorted(list(folders)), sorted(files, key=lambda x: x['display_name'])

def fetch_file_bytes(url):
    """Safely fetch bytes and verify it's not an error page."""
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            return response.content
        return None
    except:
        return None

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
                    data = fetch_file_bytes(f['secure_url'])
                    if data:
                        st.session_state.file_data = data
                        st.session_state.current_filename = pid
                        st.session_state.current_type = f['r_type']
                        st.session_state.current_url = f['secure_url']
                        st.session_state.current_format = f.get('format', f['secure_url'].split('.')[-1])
                        st.session_state.page_num = 0
                        st.rerun()
                    else:
                        st.error("Failed to load file.")
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
        st.markdown(f'<div class="welcome-banner">📂 You are in <b>{curr_name}</b> now.</div>', unsafe_allow_html=True)
        if st.session_state.authenticated:
            with st.expander("📤 Upload Media"):
                un = st.text_input("Display Name")
                uf = st.file_uploader("Select File", type=["pdf", "png", "jpg", "mp4"])
                if st.button("Upload") and uf and un:
                    with st.spinner("Uploading..."):
                        ext = uf.name.split('.')[-1]
                        r_type = "image" if ext.lower() in ['jpg', 'jpeg', 'png', 'webp'] else "video" if ext.lower() in ['mp4', 'mov'] else "raw"
                        resp = cloudinary.uploader.upload(uf.read(), folder=st.session_state.current_path, public_id=un, resource_type=r_type, overwrite=True)
                        st.session_state.file_data = requests.get(resp['secure_url']).content
                        st.session_state.current_filename = resp['public_id']
                        st.session_state.current_type = r_type
                        st.session_state.current_url = resp['secure_url']
                        st.rerun()

else:
    clean_n = st.session_state.current_filename.split('/')[-1]
    st.markdown(f"<div style='text-align:center; color:#555; letter-spacing:5px; font-size:11px; margin: 15px 0;'>{clean_n.upper()}</div>", unsafe_allow_html=True)

    # --- Renderers with Fixed Alignment ---
    if st.session_state.current_type == "raw": # PDF Renderer
        try:
            doc = fitz.open(stream=st.session_state.file_data, filetype="pdf")
            st.session_state.total_pages = len(doc)
            page = doc.load_page(st.session_state.page_num)
            pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
            img_b64 = base64.b64encode(pix.tobytes("png")).decode()
            
            n1, main, n2 = st.columns([1, 8, 1], vertical_alignment="center")
            with n1:
                if st.button("〈", key="p") and st.session_state.page_num > 0:
                    st.session_state.page_num -= 1
                    st.rerun()
            with main:
                st.markdown(f'<div class="viewport-container"><img src="data:image/png;base64,{img_b64}" class="media-preview"></div>', unsafe_allow_html=True)
                st.markdown(f"<div style='text-align:center; color:#444; font-size:12px; margin-top:10px;'>{st.session_state.page_num+1} / {st.session_state.total_pages}</div>", unsafe_allow_html=True)
            with n2:
                if st.button("〉", key="n") and st.session_state.page_num < st.session_state.total_pages-1:
                    st.session_state.page_num += 1
                    st.rerun()
        except:
            st.error("This PDF cannot be previewed.")

    elif st.session_state.current_type == "image":
        img_b64 = base64.b64encode(st.session_state.file_data).decode()
        st.markdown(f'<div class="viewport-container"><img src="data:image/image;base64,{img_b64}" class="media-preview"></div>', unsafe_allow_html=True)
    
    elif st.session_state.current_type == "video":
        st.markdown(f'<div class="viewport-container"><video controls class="media-preview"><source src="{st.session_state.current_url}"></video></div>', unsafe_allow_html=True)

    # --- Footer Actions ---
    st.markdown("<br>", unsafe_allow_html=True)
    _, d_col, c_col, _ = st.columns([5, 2, 2, 5])
    
    # Precise filename reconstruction
    ext = st.session_state.current_format.lower()
    disp_name = st.session_state.current_filename.split('/')[-1]
    dl_name = disp_name if disp_name.lower().endswith(f".{ext}") else f"{disp_name}.{ext}"

    with d_col:
        st.download_button(
            label="Download",
            data=st.session_state.file_data,
            file_name=dl_name,
            mime=f"application/octet-stream", # Forces binary download instead of text
            use_container_width=True
        )
    with c_col:
        if st.button("Close", use_container_width=True):
            st.session_state.file_data = None
            st.rerun()
