def create_dxf_data(img_array, style, spacing, weight, contrast):
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    
    img = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    img = cv2.convertScaleAbs(img, alpha=contrast, beta=0)
    h, w = img.shape
    scale = 0.1 # Adjust for real-world mm size

    if style == "Vertical":
        for x in range(0, w, spacing):
            points = []
            for y in range(0, h, 2): # Sampling every 2 pixels for smoothness
                b = img[y, x]
                # Calculate thickness/offset
                t = ((255 - b) / 255) * (spacing / 2) * weight
                if t > 0.5:
                    # We create a path that "wiggles" or widens
                    points.append((x * scale + (t*scale), (h-y) * scale))
            if len(points) > 1:
                msp.add_lwpolyline(points)

    elif style == "Circles":
        center = (w // 2, h // 2)
        max_r = int(math.sqrt(w**2 + h**2) / 2)
        for r in range(spacing, max_r, spacing):
            points = []
            steps = int(2 * math.pi * r / 2) # High precision sampling
            for i in range(steps + 1):
                angle = (i / steps) * 2 * math.pi
                px = center[0] + r * math.cos(angle)
                py = center[1] + r * math.sin(angle)
                
                if 0 <= int(px) < w and 0 <= int(py) < h:
                    b = img[int(py), int(px)]
                    # Instead of a circle at every point, we vary the radius slightly
                    # to create a "sculpted" vector line
                    t = ((255 - b) / 255) * (spacing / 4) * weight
                    adjusted_r = r + t
                    points.append(((center[0] + adjusted_r * math.cos(angle)) * scale, 
                                   (h - (center[1] + adjusted_r * math.sin(angle))) * scale))
            if len(points) > 1:
                msp.add_lwpolyline(points, dxfattribs={'closed': True})

    elif style == "Dots":
        for y in range(0, h, spacing):
            for x in range(0, w, spacing):
                b = img[y, x]
                r = ((255 - b) / 255) * (spacing / 2) * weight
                if r > 0.5:
                    msp.add_circle((x * scale, (h-y) * scale), radius=r * scale)

    out_str = io.StringIO()
    doc.write(out_str)
    return out_str.getvalue()
    
