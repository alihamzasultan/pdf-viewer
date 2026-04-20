import streamlit as st
import fitz  # PyMuPDF

st.set_page_config(page_title="PDF Pro Viewer", layout="wide", initial_sidebar_state="collapsed")

# --- Optimized CSS for Max Size ---
st.markdown("""
    <style>
    /* Fill the entire screen */
    .stApp { background-color: #0B0E11; }
    header, footer { visibility: hidden !important; }
    
    /* Remove all Streamlit default padding */
    [data-testid="block-container"] { 
        padding: 0rem !important; 
        max-width: 100% !important; 
    }

    /* Header Bar - Thinner */
    .header-bar {
        display: flex; justify-content: space-between; align-items: center;
        padding: 5px 20px; background: rgba(255,255,255,0.02);
        border-bottom: 1px solid rgba(255,255,255,0.05);
    }

    /* THE SLIDE IMAGE - MAX SIZE */
    [data-testid="stImage"] img {
        border-radius: 0px; 
        box-shadow: 0 0 50px rgba(0,0,0,1);
        /* Increase height to 92% of screen height */
        max-height: 92vh !important; 
        width: 100% !important;
        object-fit: contain;
        margin: 0 auto; 
        display: block;
    }

    /* Navigation Buttons - Larger and Floating style */
    button:has(div p:contains("〈")), button:has(div p:contains("〉")) {
        background-color: rgba(255, 255, 255, 0.02) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 50% !important; 
        width: 100px !important; 
        height: 100px !important;
        color: #ffffff !important; 
        font-size: 40px !important;
        transition: all 0.3s ease;
    }
    
    button:has(div p:contains("〈")):hover, button:has(div p:contains("〉")):hover {
        background-color: rgba(255, 255, 255, 0.08) !important;
        border-color: rgba(255, 255, 255, 0.3) !important;
        transform: scale(1.1);
    }

    /* Page Counter - Floating Minimalist */
    .page-info {
        position: absolute;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%);
        color: rgba(255,255,255,0.3); 
        font-family: sans-serif; 
        font-size: 14px;
        letter-spacing: 3px;
    }
    </style>
""", unsafe_allow_html=True)

if "page_num" not in st.session_state: st.session_state.page_num = 0
if "pdf_data" not in st.session_state: st.session_state.pdf_data = None

# UI
if st.session_state.pdf_data is None:
    st.markdown("<div style='height: 25vh;'></div>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 2, 1])
    with col2:
        st.title("PDF Viewer Pro")
        uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])
        if uploaded_file:
            st.session_state.pdf_data = uploaded_file.read()
            st.rerun()
else:
    # Header Bar
    st.markdown('<div class="header-bar">', unsafe_allow_html=True)
    if st.button("✖ Exit", key="close"):
        st.session_state.pdf_data = None
        st.session_state.page_num = 0
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # Render PDF with High Resolution (3.0 scale for clarity at large sizes)
    doc = fitz.open(stream=st.session_state.pdf_data, filetype="pdf")
    page = doc.load_page(st.session_state.page_num)
    pix = page.get_pixmap(matrix=fitz.Matrix(3.0, 3.0)) 
    
    # NEW COLUMN RATIO: [1, 18, 1] 
    # This makes the side columns tiny and the center column massive.
    col_prev, col_main, col_next = st.columns([1, 18, 1], vertical_alignment="center")
    
    with col_prev:
        if st.button("〈", key="prev") and st.session_state.page_num > 0:
            st.session_state.page_num -= 1
            st.rerun()
            
    with col_main:
        st.image(pix.tobytes("png"), use_container_width=True)
        st.markdown(f"<div class='page-info'>{st.session_state.page_num + 1} / {len(doc)}</div>", unsafe_allow_html=True)
        
    with col_next:
        if st.button("〉", key="next") and st.session_state.page_num < len(doc) - 1:
            st.session_state.page_num += 1
            st.rerun()

    # Keyboard JS
    st.components.v1.html("""
        <script>
        const doc = window.parent.document;
        doc.onkeydown = function(e) {
            if (e.key === 'ArrowLeft') doc.querySelectorAll('button p').forEach(p => { if(p.innerText.includes('〈')) p.click() });
            if (e.key === 'ArrowRight') doc.querySelectorAll('button p').forEach(p => { if(p.innerText.includes('〉')) p.click() });
        };
        </script>
    """, height=0)
