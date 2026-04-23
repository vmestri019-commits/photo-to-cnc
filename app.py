import streamlit as st
import cv2
import numpy as np
from PIL import Image
import ezdxf
import io
import math

# 1. Page Config (Must be first line of Streamlit code)
st.set_page_config(page_title="CNC Vector Studio", layout="wide")

# --- 2. ENGINE ---
def generate_art(img, style, spacing, weight):
    h, w = img.shape
    canvas = np.full((h, w), 255, dtype=np.uint8)
    center = (w // 2, h // 2)

    if style == "Vertical":
        for x in range(0, w, spacing):
            for y in range(0, h, 2):
                b = img[y, x]
                t = int(((255 - b) / 255) * (spacing / 2) * weight)
                if t > 0:
                    cv2.line(canvas, (x, y), (x + t, y), 0, 1)

    elif style == "Spiral":
        max_r = int(math.sqrt(w**2 + h**2) / 2)
        b_spiral = spacing / (2 * math.pi)
        angle = 0.0
        while angle < (max_r / b_spiral) * 1.2:
            r = b_spiral * angle
            x, y = int(center[0] + r * math.cos(angle)), int(center[1] + r * math.sin(angle))
            if 0 <= x < w and 0 <= y < h:
                t = int(((255 - img[y, x]) / 255) * (spacing / 3) * weight)
                if t > 0: cv2.circle(canvas, (x, y), t, 0, -1)
            angle += 0.1

    elif style == "Circles":
        max_r = int(math.sqrt(w**2 + h**2) / 2)
        for r in range(spacing, max_r, spacing):
            steps = int(2 * math.pi * r / 4)
            for i in range(steps):
                angle = (i / steps) * 2 * math.pi
                x, y = int(center[0] + r * math.cos(angle)), int(center[1] + r * math.sin(angle))
                if 0 <= x < w and 0 <= y < h:
                    t = int(((255 - img[y, x]) / 255) * (spacing / 3) * weight)
                    if t > 0: cv2.circle(canvas, (x, y), t, 0, -1)

    elif style == "Dots":
        for y in range(0, h, spacing):
            for x in range(0, w, spacing):
                r = int(((255 - img[y, x]) / 255) * (spacing / 2) * weight)
                if r > 0: cv2.circle(canvas, (x, y), r, 0, -1)
    return canvas

# --- 3. MAIN UI ---
st.title("🎨 CNC Art Master Engine")
st.write("If you don't see settings, wait for the page to finish loading.")

# Settings Container (Top of Page)
st.write("### ⚙️ Step 1: Design Settings")
c1, c2, c3, c4 = st.columns(4)
with c1: style_choice = st.selectbox("Pattern", ["Vertical", "Spiral", "Circles", "Dots"])
with c2: space = st.slider("Density (Spacing)", 5, 50, 15)
with c3: thick = st.slider("Weight", 0.1, 3.0, 1.2)
with c4: cont = st.slider("Contrast", 1.0, 3.0, 1.5)

st.markdown("---")

# Upload Section
st.write("### 📸 Step 2: Upload Image")
uploaded_file = st.file_uploader("Upload a photo", type=["jpg", "png", "jpeg"])

if uploaded_file:
    # Load and Resize for browser performance
    raw_pil = Image.open(uploaded_file).convert('L')
    raw_pil.thumbnail((800, 800)) 
    img_np = np.array(raw_pil)
    img_np = cv2.convertScaleAbs(img_np, alpha=cont, beta=0)

    # Preview Column
    col_pre, col_res = st.columns(2)
    with col_pre:
        st.image(img_np, caption="Adjusted Source", use_container_width=True)
    
    # Process Button
    if st.button("🚀 CLICK HERE TO GENERATE DESIGN"):
        with st.spinner("Calculating smooth paths..."):
            result = generate_art(img_np, style_choice, space, thick)
            with col_res:
                st.image(result, caption=f"CNC {style_choice} Ready", use_container_width=True)

            # Export
            st.write("### 📥 Step 3: Download Files")
            d1, d2 = st.columns(2)
            with d1:
                _, png = cv2.imencode(".png", result)
                st.download_button("Download HD PNG", png.tobytes(), "cnc_design.png", "image/png")
            with d2:
                # Optimized DXF for this specific style
                doc = ezdxf.new()
                msp = doc.modelspace()
                if style_choice == "Dots":
                    for y in range(0, img_np.shape[0], space):
                        for x in range(0, img_np.shape[1], space):
                            r = ((255 - img_np[y, x])/255) * (space/2) * thick
                            if r > 1: msp.add_circle((x*0.1, -y*0.1), r*0.1)
                dxf_io = io.StringIO()
                doc.write(dxf_io)
                st.download_button("Download DXF Vector", dxf_io.getvalue(), "cnc_design.dxf", "application/dxf")
else:
    st.info("Upload an image to unlock the generator button.")
                    
