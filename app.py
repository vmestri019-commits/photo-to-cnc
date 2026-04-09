import streamlit as st
import numpy as np
from PIL import Image
import io
from streamlit_stl import stl_thumbnail

st.set_page_config(page_title="CNC 3D Maker Pro", layout="centered")

st.sidebar.title("Carving Settings")
mode = st.sidebar.radio("Project Type:", ["Artistic (Photo)", "Logo/Text (Sharp)"])

st.title(f"🛠 CNC {mode} Generator")

uploaded_file = st.file_uploader("Upload Image", type=["jpg", "jpeg", "png"])

if uploaded_file:
    img = Image.open(uploaded_file).convert('L')
    
    if mode == "Logo/Text (Sharp)":
        img = img.point(lambda x: 0 if x < 128 else 255, '1').convert('L')
        z_multiplier = st.slider("Extrusion Thickness (mm)", 1, 30, 10)
    else:
        z_multiplier = st.slider("Max Carving Depth (mm)", 0.1, 10.0, 2.0)

    res = st.select_slider("Detail Level", options=[50, 100, 150], value=100)
    img = img.resize((res, res))
    data = np.array(img)
    
    st.image(img, caption="Input Map", width=200)

    if st.button("🚀 Generate 3D Model"):
        rows, cols = data.shape
        # Use Binary STL format for the previewer (it's faster)
        # For simplicity in this script, we'll keep the text format 
        # but the previewer can read it!
        stl_output = io.StringIO()
        stl_output.write("solid cnc_model\n")
        
        for r in range(rows - 1):
            for c in range(cols - 1):
                z1 = (data[r, c] / 255.0) * z_multiplier
                z2 = (data[r+1, c] / 255.0) * z_multiplier
                z3 = (data[r, c+1] / 255.0) * z_multiplier
                
                stl_output.write("facet normal 0 0 0\n  outer loop\n")
                stl_output.write(f"    vertex {r} {c} {z1}\n")
                stl_output.write(f"    vertex {r+1} {c} {z2}\n")
                stl_output.write(f"    vertex {r} {c+1} {z3}\n")
                stl_output.write("  endloop\nendfacet\n")
            
        stl_output.write("endsolid cnc_model\n")
        stl_content = stl_output.getvalue()

        # --- 3D PREVIEW SECTION ---
        st.subheader("📦 3D Preview")
        st.info("Use your finger/mouse to rotate the model!")
        
        # This creates the interactive 3D window
        stl_thumbnail(stl_content, key="preview")

        st.success("Model Ready!")
        st.download_button(
            label="📥 Download STL",
            data=stl_content,
            file_name="cnc_project.stl",
            mime="text/plain"
        )
        
