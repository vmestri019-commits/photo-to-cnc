import streamlit as st
import numpy as np
from PIL import Image
import io
from svgelements import SVG
from shapely.geometry import Polygon
import pandas as pd

st.set_page_config(page_title="CNC 3D Generator")

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("Settings")
mode = st.sidebar.radio("Choose Mode:", ["Artistic Photo (Heightmap)", "Clean Vector (Extrusion)"])

st.title(f"🛠 CNC {mode}")

if mode == "Artistic Photo (Heightmap)":
    uploaded_file = st.file_uploader("Upload Image (JPG/PNG)", type=["jpg", "jpeg", "png"])
    depth = st.slider("Carving Depth", 0.01, 0.5, 0.1)
    res = st.select_slider("Resolution", options=[50, 100, 150, 200], value=100)

    if uploaded_file:
        img = Image.open(uploaded_file).convert('L').resize((res, res))
        data = np.array(img)
        rows, cols = data.shape
        
        stl_buffer = io.StringIO()
        stl_buffer.write("solid photo_mesh\n")
        for r in range(rows - 1):
            for c in range(cols - 1):
                z1, z2, z3 = data[r, c]*depth, data[r+1, c]*depth, data[r, c+1]*depth
                stl_buffer.write(f"facet normal 0 0 0\n  outer loop\n")
                stl_buffer.write(f"    vertex {r} {c} {z1}\n")
                stl_buffer.write(f"    vertex {r+1} {c} {z2}\n")
                stl_buffer.write(f"    vertex {r} {c+1} {z3}\n")
                stl_buffer.write("  endloop\nendfacet\n")
        stl_buffer.write("endsolid photo_mesh\n")
        
        st.download_button("📥 Download Photo STL", stl_buffer.getvalue(), "photo_relief.stl")

elif mode == "Clean Vector (Extrusion)":
    st.info("This mode turns flat SVG shapes into solid 3D blocks.")
    uploaded_svg = st.file_uploader("Upload Vector (SVG)", type=["svg"])
    thickness = st.number_input("Extrusion Thickness (mm)", value=5.0)

    if uploaded_svg:
        # Simple Logic: Convert SVG paths to STL faces
        # Note: True 3D vector extrusion is complex, so we treat 
        # the SVG as a high-contrast mask for best results on mobile.
        st.warning("For best results, use simple black and white SVGs.")
        
        # We use a trick: Render the SVG to a high-res image then extrude
        # This is the most reliable way to handle vectors on a mobile-hosted app
        import base64
        svg_data = uploaded_svg.read().decode("utf-8")
        st.write("Previewing Vector...")
        st.image(uploaded_svg)
        
        # Triggering the same logic but with sharp 'cliff' edges
        img = Image.open(uploaded_svg).convert('L').resize((300, 300))
        data = np.array(img)
        # Force pixels to be either 0 or 255 (Sharp edges)
        data = np.where(data > 128, 255, 0)
        
        stl_buffer = io.StringIO()
        stl_buffer.write("solid vector_mesh\n")
        for r in range(data.shape[0] - 1):
            for c in range(data.shape[1] - 1):
                z = thickness if data[r,c] > 0 else 0
                stl_buffer.write(f"facet normal 0 0 0\n  outer loop\n")
                stl_buffer.write(f"    vertex {r} {c} {z}\n    vertex {r+1} {c} {z}\n    vertex {r} {c+1} {z}\n")
                stl_buffer.write("  endloop\nendfacet\n")
        stl_buffer.write("endsolid vector_mesh\n")
        
        st.download_button("📥 Download Vector STL", stl_buffer.getvalue(), "vector_3d.stl")
          
