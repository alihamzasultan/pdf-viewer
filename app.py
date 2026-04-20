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

# --- 2. Page Config ---
st.set_page_config(page_title="Ultra Media Vault", layout="wide", initial_sidebar_state="expanded")

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
            border-radius: 6px;
            box-shadow: 0 50px 100px rgba(0,0,0,0.9);
            border: 1px solid rgba(255,255,255,0.08);
            max-height: 85vh !important;
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
        
        /* Delete Button Style */
        .stButton button[kind="secondary"] {
            color: #ff4b4b !important;
            border-color: rgba(255,75,75,0.2) !important;
            background: transparent !important;
        }

        .page-info { color: #444; font-size: 10px; letter-spacing: 4px; text-align: center; margin-top: 5px; }
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

# --- 4. Cloudinary Helpers ---
def get_resource_type(filename):
    ext = filename.split('.')[-1].lower()
    if ext in ['jpg', 'jpeg', 'png', 'webp']: return "image"
    if ext in ['mp4', 'mov', 'avi']: return "video"
    return "raw" # PDF and others

def upload_to_cloudinary(file_bytes, filename):
    try:
        r_type = get_resource_type(filename)
        response = cloudinary.uploader.upload(
            file_bytes, public_id=filename.split('.')[0], 
            resource_type=r_type, overwrite=True
        )
        return response['secure_url'], r_type
    except Exception as e:
        st.error(f"Upload Failed: {e}")
        return None, None

def delete_from_cloudinary(public_id, r_type):
    try:
        cloudinary.uploader.destroy(public_id, resource_type=r_type)
        return True
    except Exception as e:
        st.error(f"Delete Failed: {e}")
        return False

def get_all_files():
    files = []
    try:
        for r_type in ['image', 'video', 'raw']:
            res = cloudinary.api.resources(resource_type=r_type, max_results=50)
            for item in res.get('resources', []):
                item['r_type'] = r_type
                files.append(item)
    except: pass
    return files

# --- 5. Sidebar ---
with st.sidebar:
    st.title("🛡️ Secure Vault")
    
    # Password Auth
    pwd = st.text_input("Admin Password", type="password")
    if pwd == ADMIN_PASSWORD:
        st.session_state.authenticated = True
        st.success("Admin Access Granted")
    else:
        st.session_state.authenticated = False
        if pwd: st.error("Wrong Password")

    st.markdown("---")
    search_query = st.text_input("🔍 Search Library", "").lower()
    
    all_files = get_all_files()
    for f in all_files:
        pid = f['public_id']
        rtype = f['r_type']
        if search_query in pid.lower():
            col_file, col_del = st.columns([4, 1])
            with col_file:
                label = f"▶️ {pid}" if pid == st.session_state.current_filename else f"📄 {pid}"
                if st.button(label, key=f"btn_{pid}", use_container_width=True):
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
                            st.toast(f"Deleted {pid}")
                            if st.session_state.current_filename == pid: reset_state()
                            st.rerun()

# --- 6. Main Content Area ---
apply_pro_style()

if st.session_state.file_data is None:
    st.markdown("<div style='height: 20vh;'></div>", unsafe_allow_html=True)
    _, c2, _ = st.columns([1, 2, 1])
    with c2:
        st.title("Pro Media Viewer")
        if st.session_state.authenticated:
            uploaded_file = st.file_uploader("Upload (PDF, Image, Video)", type=["pdf", "png", "jpg", "jpeg", "mp4"])
            if uploaded_file:
                with st.spinner("Uploading to Cloud..."):
                    file_bytes = uploaded_file.read()
                    url, r_type = upload_to_cloudinary(file_bytes, uploaded_file.name)
                    if url:
                        st.session_state.file_data = file_bytes
                        st.session_state.current_filename = uploaded_file.name.split(".")[0]
                        st.session_state.current_type = r_type
                        st.session_state.current_url = url
                        st.rerun()
        else:
            st.warning("Please enter Admin Password in sidebar to upload files.")

else:
    # FILENAME HEADER
    st.markdown(f"<div style='text-align:center; color:rgba(255,255,255,0.2); letter-spacing:5px; font-size:10px; margin-top:10px;'>{st.session_state.current_filename.upper()}</div>", unsafe_allow_html=True)

    try:
        # --- PDF VIEWER ---
        if st.session_state.current_type == "raw":
            doc = fitz.open(stream=st.session_state.file_data, filetype="pdf")
            st.session_state.total_pages = len(doc)
            page = doc.load_page(st.session_state.page_num)
            pix = page.get_pixmap(matrix=fitz.Matrix(3.0, 3.0)) 
            
            nav_prev, main_area, nav_next = st.columns([1, 12, 1], vertical_alignment="center")
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

        # --- IMAGE VIEWER ---
        elif st.session_state.current_type == "image":
            st.markdown('<div class="media-box">', unsafe_allow_html=True)
            st.image(st.session_state.file_data, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # --- VIDEO VIEWER ---
        elif st.session_state.current_type == "video":
            st.markdown('<div class="media-box">', unsafe_allow_html=True)
            st.video(st.session_state.current_url)
            st.markdown('</div>', unsafe_allow_html=True)

        # Exit Button
        st.markdown("<br>", unsafe_allow_html=True)
        _, exit_col, _ = st.columns([6, 2, 6])
        with exit_col:
            if st.button("✖ Close Viewer", use_container_width=True):
                reset_state()
                st.rerun()

    except Exception as e:
        st.error(f"Render Error: {e}")
        if st.button("Reset"): reset_state()

    # Keyboard Controls (PDF only)
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
