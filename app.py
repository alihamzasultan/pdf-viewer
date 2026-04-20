import streamlit as st
import fitz  # PyMuPDF
import aspose.slides as slides
import os

# --- 1. Page Config ---
st.set_page_config(page_title="Pro Slide Viewer", layout="wide", initial_sidebar_state="collapsed")

def apply_ultra_style():
    st.markdown("""
        <style>
        /* 1. Global Reset & Dark Theme */
        .stApp { background-color: #0B0E11; }
        header, footer { visibility: hidden !important; }
        [data-testid="block-container"] { padding: 0rem !important; max-width: 100% !important; }

        /* 2. Top Header Bar (Slimmer for more slide space) */
        .header-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 30px;
            background: rgba(255,255,255,0.03);
            border-bottom: 1px solid rgba(255,255,255,0.08);
        }

        /* 3. INCREASED SLIDE SIZE */
        [data-testid="stImage"] img {
            border-radius: 4px;
            box-shadow: 0 30px 60px rgba(0,0,0,0.9);
            border: 1px solid rgba(255,255,255,0.1);
            /* This allows the slide to take up almost the full height */
            max-height: 100vh !important; 
            width: 100% !important;
            margin: 0 auto;
            display: block;
        }

        /* 4. BIGGER PROFESSIONAL BUTTONS */
        button:has(div p:contains("〈")), 
        button:has(div p:contains("〉")) {
            background-color: rgba(255, 255, 255, 0.04) !important;
            border: 1px solid rgba(255, 255, 255, 0.15) !important;
            border-radius: 50% !important;
            /* Dimensions increased from 64px to 90px */
            width: 90px !important;
            height: 90px !important;
            color: #ffffff !important;
            /* Font size increased */
            font-size: 40px !important;
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3) !important;
        }

        button:has(div p:contains("〈")):hover, 
        button:has(div p:contains("〉")):hover {
            background-color: rgba(255, 255, 255, 0.15) !important;
            border-color: rgba(255, 255, 255, 0.6) !important;
            transform: scale(1.15);
            box-shadow: 0 0 30px rgba(255,255,255,0.15) !important;
        }

        /* Adjusting the "Close & Exit" to stay elegant but small */
        button:has(div p:contains("Close & Exit")) {
            background-color: #1a1d21 !important;
            border: 1px solid rgba(255,255,255,0.2) !important;
            color: #bbb !important;
            padding: 5px 20px !important;
        }

        /* 5. Minimalist Page Counter */
        .page-info {
            color: #444;
            font-family: 'Inter', sans-serif;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 2px;
            text-align: center;
            margin-top: 10px;
            text-transform: uppercase;
        }
        </style>
    """, unsafe_allow_html=True)

# --- 2. State Management ---
if "page_num" not in st.session_state: st.session_state.page_num = 0
if "file_data" not in st.session_state: st.session_state.file_data = None

def reset_state():
    st.session_state.file_data = None
    st.session_state.page_num = 0
    if os.path.exists("temp_ppt.pptx"): os.remove("temp_ppt.pptx")

# --- 3. View Logic ---
if st.session_state.file_data is None:
    apply_ultra_style()
    st.markdown("<div style='height: 25vh;'></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("Presentation Viewer Pro")
        uploaded_file = st.file_uploader("Upload Presentation (PDF/PPTX)", type=["pdf", "pptx"])
        if uploaded_file:
            st.session_state.file_data = uploaded_file.read()
            st.session_state.file_ext = uploaded_file.name.split(".")[-1].lower()
            st.rerun()
else:
    apply_ultra_style()
    
    # Sleek Header
    st.markdown('<div class="header-bar">', unsafe_allow_html=True)
    h_col1, h_col2 = st.columns([1, 1])
    with h_col1:
        if st.button("✖ Close & Exit", key="close_btn"):
            reset_state()
            st.rerun()
    with h_col2:
        st.markdown(f"<div style='text-align:right; color:#444; font-size:12px;'>MODE: FULLSCREEN VIEW — {st.session_state.file_ext.upper()}</div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Rendering logic
    img_bytes = None
    try:
        if st.session_state.file_ext == "pdf":
            doc = fitz.open(stream=st.session_state.file_data, filetype="pdf")
            st.session_state.total_pages = len(doc)
            page = doc.load_page(st.session_state.page_num)
            pix = page.get_pixmap(matrix=fitz.Matrix(3.0, 3.0)) # Super High Res for large view
            img_bytes = pix.tobytes("png")
        else:
            with open("temp_ppt.pptx", "wb") as f: f.write(st.session_state.file_data)
            with slides.Presentation("temp_ppt.pptx") as pres:
                st.session_state.total_pages = len(pres.slides)
                slide = pres.slides[st.session_state.page_num]
                img_path = f"tmp_{st.session_state.page_num}.png"
                slide.get_image(3.0, 3.0).save(img_path) # 3.0 Scale for sharpness
                with open(img_path, "rb") as f: img_bytes = f.read()
                os.remove(img_path)

        # MAIN LAYOUT
        # Changed to [1, 14, 1] to make the slide column as wide as possible
        nav_prev, main_area, nav_next = st.columns([1, 14, 1], vertical_alignment="center")

        with nav_prev:
            if st.button("〈", key="nav_prev_btn") and st.session_state.page_num > 0:
                st.session_state.page_num -= 1
                st.rerun()

        with main_area:
            if img_bytes:
                # use_container_width=True allows it to fill the massive 14-unit column
                st.image(img_bytes, use_container_width=True)
                st.markdown(f"<div class='page-info'>{st.session_state.page_num + 1} / {st.session_state.total_pages}</div>", unsafe_allow_html=True)

        with nav_next:
            if st.button("〉", key="nav_next_btn") and st.session_state.page_num < st.session_state.total_pages - 1:
                st.session_state.page_num += 1
                st.rerun()

    except Exception as e:
        st.error(f"Render Error: {e}")
        if st.button("Reset View"): reset_state()

    # Keyboard logic
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