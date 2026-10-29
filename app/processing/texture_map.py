import os
import numpy as np
from PIL import Image, ImageOps, ImageFilter

def tile_texture(texture_img: Image.Image, target_size: tuple, scale: float = 1.0) -> Image.Image:
    """
    Tiles the fabric texture to fill the target size (width, height).
    Optional scaling factor to simulate fine or coarse fabric weave.
    """
    target_w, target_h = target_size
    orig_w, orig_h = texture_img.size
    
    # Scale swatch appropriately (e.g. 200px-400px repeat)
    base_repeat_w = max(180, int(orig_w * scale))
    base_repeat_h = max(180, int(orig_h * scale))
    
    resized_swatch = texture_img.resize((base_repeat_w, base_repeat_h), Image.Resampling.LANCZOS)
    sw_w, sw_h = resized_swatch.size

    tiled = Image.new("RGB", (target_w, target_h))
    for y in range(0, target_h, sw_h):
        for x in range(0, target_w, sw_w):
            tiled.paste(resized_swatch, (x, y))
            
    return tiled

def multiply_blend(base_np: np.ndarray, blend_np: np.ndarray) -> np.ndarray:
    """
    Multiplies base image with shading overlay (values 0-255).
    Formula: (base * blend) / 255.0
    """
    return ((base_np.astype(np.float32) * blend_np.astype(np.float32)) / 255.0).astype(np.uint8)

def overlay_blend(base_np: np.ndarray, blend_np: np.ndarray) -> np.ndarray:
    """
    Standard Photoshop-style Overlay blend mode.
    """
    base = base_np.astype(np.float32) / 255.0
    blend = blend_np.astype(np.float32) / 255.0
    
    low = 2.0 * base * blend
    high = 1.0 - 2.0 * (1.0 - base) * (1.0 - blend)
    
    result = np.where(base < 0.5, low, high)
    return np.clip(result * 255.0, 0, 255).astype(np.uint8)

def drape_fabric_on_template(fabric_img: Image.Image, template_dir: str, scale: float = 0.8) -> tuple:
    """
    Core 2D compositing drape engine:
    1. Loads template mask, shading overlay, and optional outline/accents.
    2. Tiles fabric across canvas.
    3. Multiplies fabric with fold/shadow overlay.
    4. Applies silhouette alpha mask.
    5. Places garment onto a studio background with soft ambient drop shadow.
    6. Returns (preview_pil, thumbnail_pil).
    """
    mask_path = os.path.join(template_dir, "silhouette_mask.png")
    shading_path = os.path.join(template_dir, "shading_overlay.png")
    accent_path = os.path.join(template_dir, "accent_overlay.png")

    if not os.path.exists(mask_path):
        raise FileNotFoundError(f"Missing silhouette mask: {mask_path}")
    if not os.path.exists(shading_path):
        raise FileNotFoundError(f"Missing shading overlay: {shading_path}")

    mask_img = Image.open(mask_path).convert("L")
    canvas_w, canvas_h = mask_img.size

    # 1. Tile fabric to canvas size
    tiled_fabric = tile_texture(fabric_img, (canvas_w, canvas_h), scale=scale)
    fabric_np = np.array(tiled_fabric)

    # 2. Load shading layer
    shading_img = Image.open(shading_path).convert("RGBA")
    # Separate shading into RGB luminance and alpha
    shading_rgb = shading_img.convert("RGB")
    shading_np = np.array(shading_rgb)

    # 3. Composite fabric with realistic shading
    # Using balanced multiply blend for natural cloth shadows and highlights
    draped_np = multiply_blend(fabric_np, shading_np)
    draped_img = Image.fromarray(draped_np, "RGB")

    # 4. Optional accent overlay (collar lines, buttons, hem piping)
    if os.path.exists(accent_path):
        accent_img = Image.open(accent_path).convert("RGBA")
        draped_img.paste(accent_img, (0, 0), accent_img)

    # 5. Build studio presentation canvas
    # Soft neutral studio background (#F5F5F7)
    bg_color = (245, 245, 248)
    final_canvas = Image.new("RGBA", (canvas_w, canvas_h), (*bg_color, 255))

    # Add soft garment drop shadow for depth
    shadow_mask = mask_img.filter(ImageFilter.GaussianBlur(radius=18))
    shadow_layer = Image.new("RGBA", (canvas_w, canvas_h), (30, 30, 45, 0))
    # Fill shadow with subtle opacity (alpha 40)
    shadow_alpha = (np.array(shadow_mask).astype(np.float32) * 0.16).astype(np.uint8)
    shadow_layer.putalpha(Image.fromarray(shadow_alpha, "L"))
    # Offset shadow slightly downward
    final_canvas.paste(shadow_layer, (0, 10), shadow_layer)

    # Paste masked draped garment
    garment_rgba = draped_img.convert("RGBA")
    garment_rgba.putalpha(mask_img)
    final_canvas.paste(garment_rgba, (0, 0), garment_rgba)

    preview_img = final_canvas.convert("RGB")

    # 6. Generate square thumbnail crop (focusing on garment chest / core)
    # Target 360x360 thumbnail
    crop_w = int(canvas_w * 0.65)
    crop_h = crop_w
    crop_x = int((canvas_w - crop_w) / 2)
    crop_y = int(canvas_h * 0.18)  # Chest / collar area focus
    
    thumb_crop = preview_img.crop((crop_x, crop_y, crop_x + crop_w, crop_y + crop_h))
    thumbnail_img = thumb_crop.resize((360, 360), Image.Resampling.LANCZOS)

    return preview_img, thumbnail_img
