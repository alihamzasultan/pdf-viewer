import streamlit as st
import fitz  # PyMuPDF

# --- 1. Page Config ---
st.set_page_config(page_title="PDF Pro Viewer", layout="wide", initial_sidebar_state="collapsed")

def apply_ultra_style():
    st.markdown("""
        <style>
        .stApp { background-color: #0B0E11; }
        header, footer { visibility: hidden !important; }
        [data-testid="block-container"] { padding: 0rem !important; max-width: 100% !important; }
        
        .header-bar {
            display: flex; justify-content: space-between; align-items: center;
            padding: 10px 30px; background: rgba(255,255,255,0.03);
            border-bottom: 1px solid rgba(255,255,255,0.08);
        }

        [data-testid="stImage"] img {
            border-radius: 4px; box-shadow: 0 30px 60px rgba(0,0,0,0.9);
            border: 1px solid rgba(255,255,255,0.1);
            max-height: 88vh !important; width: auto !important; margin: 0 auto; display: block;
        }

        /* Navigation Buttons */
        button:has(div p:contains("〈")), button:has(div p:contains("〉")) {
            background-color: rgba(255, 255, 255, 0.04) !important;
            border: 1px solid rgba(255, 255, 255, 0.15) !important;
            border-radius: 50% !important; width: 80px !important; height: 80px !important;
            color: #ffffff !important; font-size: 30px !important;
            transition: all 0.3s ease; display: flex !important;
            align-items: center !important; justify-content: center !important;
        }
        button:has(div p:contains("〈")):hover, button:has(div p:contains("〉")):hover {
            background-color: rgba(255, 255, 255, 0.1) !important;
            transform: scale(1.1);
        }

        .page-info {
            color: #555; font-family: 'Inter', sans-serif; font-size: 12px;
            letter-spacing: 2px; text-align: center; margin-top: 15px; text-transform: uppercase;
        }
        </style>
    """, unsafe_allow_html=True)

# --- State Management ---
if "page_num" not in st.session_state: st.session_state.page_num = 0
if "pdf_data" not in st.session_state: st.session_state.pdf_data = None

def reset_state():
    st.session_state.pdf_data = None
    st.session_state.page_num = 0

# --- App Logic ---
if st.session_state.pdf_data is None:
    apply_ultra_style()
    st.markdown("<div style='height: 25vh;'></div>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 2, 1])
    with col2:
        st.title("PDF Viewer Pro")
        uploaded_file = st.file_uploader("Upload PDF Document", type=["pdf"])
        if uploaded_file:
            st.session_state.pdf_data = uploaded_file.read()
            st.rerun()
else:
    apply_ultra_style()
    
    # Simple Header
    st.markdown('<div class="header-bar">', unsafe_allow_html=True)
    h_col1, h_col2 = st.columns([1, 1])
    with h_col1:
        if st.button("✖ Close Document", key="close"): reset_state(); st.rerun()
    with h_col2:
        st.markdown("<div style='text-align:right; color:#444; font-size:12px;'>VIEWER MODE: FULLSCREEN</div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    try:
        # Open PDF from memory
        doc = fitz.open(stream=st.session_state.pdf_data, filetype="pdf")
        total_pages = len(doc)
        
        # Load Current Page
        page = doc.load_page(st.session_state.page_num)
        pix = page.get_pixmap(matrix=fitz.Matrix(2.5, 2.5)) # High Res
        img_bytes = pix.tobytes("png")

        # Navigation Layout
        _, nav_p, main, nav_n, _ = st.columns([1, 2, 10, 2, 1], vertical_alignment="center")
        
        with nav_p:
            if st.button("〈", key="prev") and st.session_state.page_num > 0:
                st.session_state.page_num -= 1
                st.rerun()
        
        with main:
            st.image(img_bytes, use_container_width=True)
            st.markdown(f"<div class='page-info'>{st.session_state.page_num + 1} / {total_pages}</div>", unsafe_allow_html=True)
        
        with nav_n:
            if st.button("〉", key="next") and st.session_state.page_num < total_pages - 1:
                st.session_state.page_num += 1
                st.rerun()

    except Exception as e:
        st.error(f"Error displaying PDF: {e}")
        if st.button("Reset"): reset_state()

    # Keyboard Controls (Arrow Keys)
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
