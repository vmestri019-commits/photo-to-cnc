def generate_preview(img_array, style, spacing, weight, contrast):
    # 1. Standardize image and boost contrast
    img = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    img = cv2.convertScaleAbs(img, alpha=contrast, beta=0)
    h, w = img.shape
    
    # Create white canvas
    output = np.full((h, w), 255, dtype=np.uint8)
    center = (w // 2, h // 2)

    # --- Start of Logic Chain ---
    if style == "Vertical" or style == "Crosshatch":
        for x in range(0, w, spacing):
            col = img[:, min(x, w-1)]
            thicknesses = ((255 - col) / 255) * (spacing / 2) * weight
            for y in range(h):
                t = int(thicknesses[y])
                if t > 0:
                    output[y, max(0, x-t):min(w, x+t)] = 0
                    
        # If Crosshatch, we don't stop; we add horizontal lines too
        if style == "Crosshatch":
            for y in range(0, h, spacing):
                row = img[y, :]
                thicknesses = ((255 - row) / 255) * (spacing / 2) * weight
                for x in range(w):
                    t = int(thicknesses[x])
                    if t > 0:
                        output[max(0, y-t):min(h, y+t), x] = 0

    elif style == "Circles":
        max_r = int(math.sqrt(w**2 + h**2) / 2)
        for r in range(0, max_r, spacing):
            sample_y = max(0, center[1] - r)
            brightness = img[sample_y, center[0]]
            t = int(((255 - brightness) / 255) * (spacing / 2) * weight)
            if t > 0:
                cv2.circle(output, center, r, 0, max(1, t))

    elif style == "Dots":
        for y in range(0, h, spacing):
            for x in range(0, w, spacing):
                brightness = img[y, x]
                r = int(((255 - brightness) / 255) * (spacing / 2) * weight)
                if r > 0:
                    cv2.circle(output, (x, y), r, 0, -1)

    elif style == "Spiral":
        max_r = int(math.sqrt(w**2 + h**2) / 2)
        b = spacing / (2 * math.pi)
        angle = 0.0
        while True:
            r = b * angle
            if r > max_r: break
            x_pos = int(center[0] + r * math.cos(angle))
            y_pos = int(center[1] + r * math.sin(angle))
            if 0 <= x_pos < w and 0 <= y_pos < h:
                brightness = img[y_pos, x_pos]
                t = int(((255 - brightness) / 255) * (spacing / 2) * weight)
                if t > 0:
                    cv2.circle(output, (x_pos, y_pos), t, 0, -1)
            angle += 0.1 / (r/spacing + 1) # Smooth increment

    return output
                           
