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
FOLDER_NAME = "BCH-FILES"

# --- 2. Page Config ---
st.set_page_config(page_title="BCH Library Pro", layout="wide", initial_sidebar_state="expanded")

def apply_pro_style():
    st.markdown("""
        <style>
        /* Global App Styling */
        .stApp { background-color: #080A0C; }
        footer { visibility: hidden !important; }
        header { background-color: rgba(0,0,0,0) !important; }
        
        /* Sidebar Professional Overhaul */
        [data-testid="stSidebar"] {
            background-color: #0E1117 !important;
            border-right: 1px solid rgba(255,255,255,0.05);
        }
        
        .sidebar-heading {
            color: #888;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            margin-bottom: 10px;
            margin-top: 20px;
        }

        /* Input Boxes */
        .stTextInput input {
            background-color: #1A1D24 !important;
            border: 1px solid #2D323B !important;
            color: #E6E6E6 !important;
            border-radius: 6px !important;
        }

        /* Professional Buttons */
        .stButton button {
            border-radius: 6px !important;
            border: 1px solid #2D323B !important;
            background-color: #1A1D24 !important;
            color: #E6E6E6 !important;
            transition: all 0.2s ease;
        }
        
        .stButton button:hover {
            border-color: #4A90E2 !important;
            color: #4A90E2 !important;
            background-color: #1E2530 !important;
        }

        /* Active File Highlight */
        button[key*="btn_active"] {
            border-color: #4A90E2 !important;
            color: #4A90E2 !important;
        }

        /* Delete Button - Red Hover */
        button[key*="del_"]:hover {
            border-color: #FF4B4B !important;
            color: #FF4B4B !important;
        }

        /* Media Viewport */
        .media-box img, .media-box video {
            border-radius: 8px;
            box-shadow: 0 40px 100px rgba(0,0,0,0.8);
            border: 1px solid rgba(255,255,255,0.05);
            max-height: 85vh !important;
            margin: 0 auto;
            display: block;
        }

        /* Navigation Arrows */
        button:has(div p:contains("〈")), button:has(div p:contains("〉")) {
            width: 50px !important; height: 50px !important;
            border-radius: 50% !important;
            font-size: 24px !important;
        }
        </style>
    """, unsafe_allow_html=True)

# --- 3. State Management ---
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "page_num" not in st.session_state: st.session_state.page_num = 0
if "file_data" not in st.session_state: st.session_state.file_data = None
if "current_filename" not in st.session_state: st.session_state.current_filename = ""
if "current_type" not in st.session_state: st.session_state.current_type = ""

# --- 4. Logic Functions ---
def get_resource_type(filename):
    ext = filename.split('.')[-1].lower()
    if ext in ['jpg', 'jpeg', 'png', 'webp']: return "image"
    if ext in ['mp4', 'mov', 'avi']: return "video"
    return "raw"

def upload_file(file_bytes, filename):
    r_type = get_resource_type(filename)
    resp = cloudinary.uploader.upload(file_bytes, folder=FOLDER_NAME, public_id=filename.split('.')[0], resource_type=r_type, overwrite=True)
    return resp['secure_url'], r_type

def delete_file(public_id, r_type):
    cloudinary.uploader.destroy(public_id, resource_type=r_type)
    return True

def fetch_files():
    files = []
    try:
        for rt in ['image', 'video', 'raw']:
            res = cloudinary.api.resources(resource_type=rt, type="upload", prefix=f"{FOLDER_NAME}/", max_results=100)
            for item in res.get('resources', []):
                item['r_type'] = rt
                item['display_name'] = item['public_id'].replace(f"{FOLDER_NAME}/", "")
                files.append(item)
    except: pass
    return files

# --- 5. Sidebar UI ---
with st.sidebar:
    st.markdown('<p class="sidebar-heading">Security</p>', unsafe_allow_html=True)
    pwd_input = st.text_input("Password", type="password", placeholder="Enter Admin Password", label_visibility="collapsed")
    if st.button("Unlock Admin Mode", use_container_width=True):
        if pwd_input == ADMIN_PASSWORD:
            st.session_state.authenticated = True
            st.toast("Admin mode unlocked", icon="🔓")
        else:
            st.session_state.authenticated = False
            st.error("Invalid Password")
    
    if st.session_state.authenticated:
        st.caption("✅ Admin Authorized")

    st.markdown('<p class="sidebar-heading">Explorer</p>', unsafe_allow_html=True)
    search = st.text_input("Search", placeholder="🔍 Search folder...", label_visibility="collapsed").lower()
    
    st.markdown('<p class="sidebar-heading">BCH-FILES Library</p>', unsafe_allow_html=True)
    lib_files = fetch_files()
    
    for f in lib_files:
        pid = f['public_id']
        name = f['display_name']
        if search in name.lower():
            c1, c2 = st.columns([4, 1])
            with c1:
                is_active = pid == st.session_state.current_filename
                btn_key = f"btn_active_{pid}" if is_active else f"btn_{pid}"
                icon = "▶️" if is_active else "📄"
                if st.button(f"{icon} {name}", key=btn_key, use_container_width=True):
                    with st.spinner(""):
                        resp = requests.get(f['secure_url'])
                        st.session_state.file_data = resp.content
                        st.session_state.current_filename = pid
                        st.session_state.current_type = f['r_type']
                        st.session_state.current_url = f['secure_url']
                        st.session_state.page_num = 0
                        st.rerun()
            with c2:
                if st.session_state.authenticated:
                    if st.button("🗑️", key=f"del_{pid}", help="Delete from cloud"):
                        if delete_file(pid, f['r_type']):
                            if st.session_state.current_filename == pid:
                                st.session_state.file_data = None
                            st.rerun()

# --- 6. Main Area ---
apply_pro_style()

if st.session_state.file_data is None:
    st.markdown("<div style='height: 25vh;'></div>", unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        st.title("BCH Media Vault")
        st.markdown("Select a file from the sidebar or upload a new one.")
        if st.session_state.authenticated:
            up = st.file_uploader("Drop file here", type=["pdf", "png", "jpg", "mp4"])
            if up:
                with st.spinner("Processing..."):
                    b = up.read()
                    url, rt = upload_file(b, up.name)
                    st.session_state.file_data = b
                    st.session_state.current_filename = f"{FOLDER_NAME}/{up.name.split('.')[0]}"
                    st.session_state.current_type = rt
                    st.session_state.current_url = url
                    st.rerun()
        else:
            st.info("💡 Enter the admin password in the sidebar to enable uploads.")
else:
    # Title display
    clean_n = st.session_state.current_filename.split('/')[-1]
    st.markdown(f"<div style='text-align:center; color:#555; letter-spacing:5px; font-size:11px; margin: 15px 0;'>{clean_n.upper()}</div>", unsafe_allow_html=True)

    # Viewer
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
            st.image(pix.tobytes("png"), use_container_width=True)
            st.markdown(f"<div style='text-align:center; color:#444; font-size:12px; margin-top:10px;'>{st.session_state.page_num+1} / {st.session_state.total_pages}</div>", unsafe_allow_html=True)
        with n2:
            if st.button("〉", key="n") and st.session_state.page_num < st.session_state.total_pages-1:
                st.session_state.page_num += 1
                st.rerun()
    
    elif st.session_state.current_type == "image":
        st.image(st.session_state.file_data, use_container_width=True)
    
    elif st.session_state.current_type == "video":
        st.video(st.session_state.current_url)

    # Exit
    st.markdown("<br>", unsafe_allow_html=True)
    _, ex, _ = st.columns([6, 2, 6])
    if ex.button("✖ Close Viewer", use_container_width=True):
        st.session_state.file_data = None
        st.rerun()
