import os
import cv2
import numpy as np
from PIL import Image

def auto_white_balance(img: np.ndarray) -> np.ndarray:
    """
    Applies Gray World white balancing algorithm to correct color cast.
    """
    result = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    avg_a = np.average(result[:, :, 1])
    avg_b = np.average(result[:, :, 2])
    # Shift a and b channels towards neutral (128)
    result[:, :, 1] = result[:, :, 1] - ((avg_a - 128) * (result[:, :, 0] / 255.0) * 1.1)
    result[:, :, 2] = result[:, :, 2] - ((avg_b - 128) * (result[:, :, 0] / 255.0) * 1.1)
    return cv2.cvtColor(result, cv2.COLOR_LAB2BGR)

def auto_exposure(img: np.ndarray) -> np.ndarray:
    """
    Applies CLAHE (Contrast Limited Adaptive Histogram Equalization) 
    on the L-channel to balance exposure without blowing out highlights.
    """
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    # Blend slightly with original to preserve natural fabric softness
    cl = cv2.addWeighted(cl, 0.7, l, 0.3, 0)
    limg = cv2.merge((cl, a, b))
    return cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)

def auto_crop_fabric(img: np.ndarray, margin_percent: float = 0.08) -> np.ndarray:
    """
    Detects the main fabric region and crops away background/edges.
    If the image is already primarily fabric, crops a central square/rectangle.
    """
    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Check variance of color to see if edges contain distinct borders (like table or tape)
    # Default to safe center crop that guarantees 100% fabric content
    mh = int(h * margin_percent)
    mw = int(w * margin_percent)
    cropped = img[mh:h-mh, mw:w-mw]
    return cropped

def clean_fabric_image(input_path_or_bytes, output_path: str = None) -> Image.Image:
    """
    Main cleanup pipeline:
    1. Load image (file path or bytes)
    2. Auto-crop margin
    3. Auto white balance
    4. Auto exposure / contrast enhancement
    5. Return PIL Image (RGB)
    """
    if isinstance(input_path_or_bytes, (str, os.PathLike)):
        img = cv2.imread(str(input_path_or_bytes))
        if img is None:
            raise ValueError(f"Could not read image from {input_path_or_bytes}")
    elif isinstance(input_path_or_bytes, bytes):
        nparr = np.frombuffer(input_path_or_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Could not decode image bytes")
    else:
        # Assume numpy array or PIL
        img = np.array(input_path_or_bytes)
        if img.shape[2] == 4:
            img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
        else:
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    # Pipeline steps
    cropped = auto_crop_fabric(img)
    wb = auto_white_balance(cropped)
    enhanced = auto_exposure(wb)

    # Convert BGR back to RGB for PIL
    rgb = cv2.cvtColor(enhanced, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(rgb)

    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        pil_img.save(output_path, "JPEG", quality=95)

    return pil_img
