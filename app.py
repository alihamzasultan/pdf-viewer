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
st.set_page_config(page_title="BCH Secure Vault", layout="wide", initial_sidebar_state="expanded")

def apply_pro_style():
    st.markdown("""
        <style>
        .stApp { background-color: #050708; }
        footer { visibility: hidden !important; }
        header { background-color: rgba(0,0,0,0) !important; }
        [data-testid="stSidebarCollapseButton"] { background-color: rgba(255,255,255,0.05) !important; color: white !important; }
        [data-testid="block-container"] { padding: 0rem 1rem !important; max-width: 100% !important; }
        section[data-testid="stSidebar"] { background-color: #0e1116 !important; border-right: 1px solid rgba(255,255,255,0.05); }

        /* Media Container */
        .media-box img, .media-box video {
            border-radius: 4px;
            box-shadow: 0 50px 100px rgba(0,0,0,0.9);
            border: 1px solid rgba(255,255,255,0.08);
            max-height: 88vh !important;
            width: auto !important;
            margin: 0 auto;
            display: block;
        }

        /* Nav Buttons */
        button:has(div p:contains("〈")), button:has(div p:contains("〉")) {
            background-color: transparent !important;
            border: 1px solid rgba(255, 255, 255, 0.05) !important;
            border-radius: 50% !important;
            width: 60px !important; height: 60px !important;
            color: #ffffff !important; font-size: 28px !important;
        }

        .page-info { color: #444; font-size: 10px; letter-spacing: 4px; text-align: center; margin-top: 5px; }
        
        /* Sidebar Button Styling */
        .stButton button { border-radius: 4px !important; }
        </style>
    """, unsafe_allow_html=True)

# --- 3. State Management ---
if "page_num" not in st.session_state: st.session_state.page_num = 0
if "file_data" not in st.session_state: st.session_state.file_data = None
if "current_filename" not in st.session_state: st.session_state.current_filename = ""
if "current_type" not in st.session_state: st.session_state.current_type = ""
if "authenticated" not in st.session_state: st.session_state.authenticated = False

def reset_state():
    st.session_state.file_data = None
    st.session_state.page_num = 0
    st.session_state.current_filename = ""

# --- 4. Cloudinary Helpers (Folder Aware) ---
def get_resource_type(filename):
    ext = filename.split('.')[-1].lower()
    if ext in ['jpg', 'jpeg', 'png', 'webp']: return "image"
    if ext in ['mp4', 'mov', 'avi']: return "video"
    return "raw" 

def upload_to_cloudinary(file_bytes, filename):
    try:
        r_type = get_resource_type(filename)
        # We specify the folder here
        response = cloudinary.uploader.upload(
            file_bytes, 
            public_id=filename.split('.')[0], 
            folder=FOLDER_NAME,
            resource_type=r_type, 
            overwrite=True
        )
        return response['secure_url'], r_type
    except Exception as e:
        st.error(f"Upload Failed: {e}")
        return None, None

def delete_from_cloudinary(public_id, r_type):
    try:
        # public_id here includes the folder name (e.g. BCH-FILES/filename)
        cloudinary.uploader.destroy(public_id, resource_type=r_type)
        return True
    except Exception as e:
        st.error(f"Delete Failed: {e}")
        return False

def get_folder_files():
    files = []
    try:
        for r_type in ['image', 'video', 'raw']:
            # We filter specifically by prefix to target the BCH-FILES folder
            res = cloudinary.api.resources(
                resource_type=r_type, 
                type="upload", 
                prefix=f"{FOLDER_NAME}/",
                max_results=100
            )
            for item in res.get('resources', []):
                item['r_type'] = r_type
                # display_name is the filename without the folder prefix
                item['display_name'] = item['public_id'].replace(f"{FOLDER_NAME}/", "")
                files.append(item)
    except: pass
    return files

# --- 5. Sidebar ---
with st.sidebar:
    st.title("📁 BCH Library")
    
    # Password Auth
    pwd = st.text_input("Enter Admin Password", type="password")
    if pwd == ADMIN_PASSWORD:
        st.session_state.authenticated = True
    else:
        st.session_state.authenticated = False

    st.markdown("---")
    search_query = st.text_input("🔍 Search folder...", "").lower()
    
    all_files = get_folder_files()
    if not all_files:
        st.caption("No files found in BCH-FILES folder.")
    
    for f in all_files:
        pid = f['public_id']
        display = f['display_name']
        rtype = f['r_type']
        
        if search_query in display.lower():
            col_file, col_del = st.columns([4, 1])
            with col_file:
                icon = "▶️" if pid == st.session_state.current_filename else "📄"
                if st.button(f"{icon} {display}", key=f"btn_{pid}", use_container_width=True):
                    with st.spinner("Loading..."):
                        resp = requests.get(f['secure_url'])
                        st.session_state.file_data = resp.content
                        st.session_state.current_filename = pid
                        st.session_state.current_type = rtype
                        st.session_state.page_num = 0
                        st.session_state.current_url = f['secure_url']
                        st.rerun()
            with col_del:
                if st.session_state.authenticated:
                    if st.button("🗑️", key=f"del_{pid}"):
                        if delete_from_cloudinary(pid, rtype):
                            if st.session_state.current_filename == pid: reset_state()
                            st.rerun()

# --- 6. Main Content Area ---
apply_pro_style()

if st.session_state.file_data is None:
    st.markdown("<div style='height: 25vh;'></div>", unsafe_allow_html=True)
    _, c2, _ = st.columns([1, 2, 1])
    with c2:
        st.title("BCH Media Vault")
        st.caption(f"Storage Folder: {FOLDER_NAME}")
        if st.session_state.authenticated:
            uploaded_file = st.file_uploader("Upload to BCH-FILES", type=["pdf", "png", "jpg", "jpeg", "mp4"])
            if uploaded_file:
                with st.spinner("Uploading..."):
                    file_bytes = uploaded_file.read()
                    url, r_type = upload_to_cloudinary(file_bytes, uploaded_file.name)
                    if url:
                        st.session_state.file_data = file_bytes
                        st.session_state.current_filename = f"{FOLDER_NAME}/{uploaded_file.name.split('.')[0]}"
                        st.session_state.current_type = r_type
                        st.session_state.current_url = url
                        st.rerun()
        else:
            st.warning("Admin Password Required for Upload/Delete")

else:
    # Display the clean filename at the top
    clean_name = st.session_state.current_filename.replace(f"{FOLDER_NAME}/", "")
    st.markdown(f"<div style='text-align:center; color:rgba(255,255,255,0.2); letter-spacing:5px; font-size:10px; margin-top:10px;'>{clean_name.upper()}</div>", unsafe_allow_html=True)

    try:
        # PDF
        if st.session_state.current_type == "raw":
            doc = fitz.open(stream=st.session_state.file_data, filetype="pdf")
            st.session_state.total_pages = len(doc)
            page = doc.load_page(st.session_state.page_num)
            pix = page.get_pixmap(matrix=fitz.Matrix(3.0, 3.0)) 
            
            nav_prev, main_area, nav_next = st.columns([1, 14, 1], vertical_alignment="center")
            with nav_prev:
                if st.button("〈", key="prev") and st.session_state.page_num > 0:
                    st.session_state.page_num -= 1
                    st.rerun()
            with main_area:
                st.markdown('<div class="media-box">', unsafe_allow_html=True)
                st.image(pix.tobytes("png"), use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown(f"<div class='page-info'>{st.session_state.page_num + 1} / {st.session_state.total_pages}</div>", unsafe_allow_html=True)
            with nav_next:
                if st.button("〉", key="next") and st.session_state.page_num < st.session_state.total_pages - 1:
                    st.session_state.page_num += 1
                    st.rerun()

        # IMAGE
        elif st.session_state.current_type == "image":
            st.markdown('<div class="media-box">', unsafe_allow_html=True)
            st.image(st.session_state.file_data, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # VIDEO
        elif st.session_state.current_type == "video":
            st.markdown('<div class="media-box">', unsafe_allow_html=True)
            st.video(st.session_state.current_url)
            st.markdown('</div>', unsafe_allow_html=True)

        # Exit
        st.markdown("<br>", unsafe_allow_html=True)
        _, exit_col, _ = st.columns([6, 2, 6])
        with exit_col:
            if st.button("✖ Close Viewer", use_container_width=True):
                reset_state()
                st.rerun()

    except Exception as e:
        st.error(f"Error: {e}")
        if st.button("Reset"): reset_state()

    # Keyboard logic
    if st.session_state.current_type == "raw":
        st.components.v1.html("""
            <script>
            const doc = window.parent.document;
            doc.onkeydown = function(e) {
                if (e.key === 'ArrowLeft') {
                    const btn = Array.from(doc.querySelectorAll('button')).find(el => el.innerText.includes('〈'));
                    if(btn) btn.click();
                } else if (e.key === 'ArrowRight') {
                    const btn = Array.from(doc.querySelectorAll('button')).find(el => el.innerText.includes('〉'));
                    if(btn) btn.click();
                }
            };
            </script>
        """, height=0)
