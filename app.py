# --- STREAMLIT UI ---
st.set_page_config(page_title="CNC Art Studio", layout="wide")
st.title("🎨 CNC Design Engine")

# 1. Settings Section (Always Visible)
st.write("### 🛠️ Step 1: Adjust Design Settings")
col_a, col_b, col_c, col_d = st.columns(4)

with col_a:
    style_choice = st.selectbox("Pattern Type", ["Vertical", "Crosshatch", "Circles", "Dots", "Spiral"])
with col_b:
    line_density = st.slider("Density", 4, 40, 12)
with col_c:
    line_weight = st.slider("Thickness", 0.1, 3.0, 1.0)
with col_d:
    img_contrast = st.slider("Contrast", 1.0, 3.0, 1.5)

st.markdown("---")

# 2. Upload Section
st.write("### 📸 Step 2: Upload Your Image")
uploaded_file = st.file_uploader("Choose a Portrait", type=["jpg", "png", "jpeg"])

if uploaded_file:
    image = Image.open(uploaded_file)
    img_np = np.array(image)
    
    # Execution
    with st.spinner("Generating Art..."):
        preview_img = generate_cnc_art(img_np, style_choice, line_density, line_weight, img_contrast)
        
        # Display Preview
        st.image(preview_img, caption=f"Resulting {style_choice} Pattern", use_container_width=True)

    # 3. Export Section
    st.write("### 💾 Step 3: Download Files")
    c1, c2 = st.columns(2)
    
    with c1:
        ret, tiff_buffer = cv2.imencode(".tif", preview_img)
        st.download_button("Download TIFF (Raster)", tiff_buffer.tobytes(), "cnc_art.tif", "image/tiff")
        
    with c2:
        dxf_data = create_dxf_data(img_np, style_choice, line_density, line_weight, img_contrast)
        st.download_button("Download DXF (Vector)", dxf_data, "cnc_art.dxf", "application/dxf")
else:
    st.info("Waiting for an image upload to show the preview...")
    
