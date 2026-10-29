"""
Test runner for Step 2:
Runs cleanup.py and texture_map.py on the 4 sample fabric swatches across garment templates.
"""
import os
import time
import sys

ENGINE_DIR = "/Users/codekajugad/Desktop/vastrenix-fabric-engine"
sys.path.insert(0, ENGINE_DIR)

from app.processing.cleanup import clean_fabric_image
from app.processing.texture_map import drape_fabric_on_template

OUTPUT_DIR = os.path.join(ENGINE_DIR, "test_output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

SAMPLES = [
    ("royal_banarasi_silk.jpg", "saree"),
    ("maroon_floral_chanderi.jpg", "kurta"),
    ("emerald_cotton_linen.jpg", "shirt"),
    ("mustard_bandhani_print.jpg", "nehru_jacket"),
]

def run_tests():
    print("==================================================")
    print("RUNNING STEP 2 PIPELINE VALIDATION ON REAL SAMPLES")
    print("==================================================")
    
    results = []
    
    for swatch_name, template_name in SAMPLES:
        t0 = time.time()
        swatch_path = os.path.join(ENGINE_DIR, "test_samples", swatch_name)
        template_dir = os.path.join(ENGINE_DIR, "app", "templates", template_name)
        
        # 1. Cleanup
        cleaned_path = os.path.join(OUTPUT_DIR, f"cleaned_{swatch_name}")
        cleaned_fabric = clean_fabric_image(swatch_path, cleaned_path)
        
        # 2. Draping
        preview, thumbnail = drape_fabric_on_template(cleaned_fabric, template_dir, scale=0.7)
        
        preview_path = os.path.join(OUTPUT_DIR, f"preview_{template_name}_{swatch_name}")
        thumb_path = os.path.join(OUTPUT_DIR, f"thumb_{template_name}_{swatch_name}")
        
        preview.save(preview_path, "JPEG", quality=92)
        thumbnail.save(thumb_path, "JPEG", quality=90)
        
        elapsed_ms = int((time.time() - t0) * 1000)
        results.append({
            "fabric": swatch_name,
            "template": template_name,
            "preview_size": preview.size,
            "thumb_size": thumbnail.size,
            "time_ms": elapsed_ms,
            "preview_file": preview_path,
            "thumb_file": thumb_path
        })
        
        print(f"✓ Draped {swatch_name} -> {template_name.upper()} in {elapsed_ms}ms")
        print(f"    Preview: {preview_path} ({preview.size[0]}x{preview.size[1]})")
        print(f"    Thumbnail: {thumb_path} ({thumbnail.size[0]}x{thumbnail.size[1]})")

    print("\nAll pipeline tests completed successfully!")
    return results

if __name__ == "__main__":
    run_tests()
