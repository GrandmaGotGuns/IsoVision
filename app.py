import os
import json
import cv2
import numpy as np
import torch
from flask import Flask, request, jsonify, send_from_directory
from segment_anything import sam_model_registry, SamPredictor
from flask_cors import CORS
import shutil
from datetime import datetime  

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
PROCESSED_FOLDER = "processed"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)


MODEL_CHECKPOINT = "sam_model_vitb.pth"
MODEL_TYPE = "vit_b"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

def clear_processed_folder():
    """Clears all files in the processed folder"""
    for filename in os.listdir(PROCESSED_FOLDER):
        file_path = os.path.join(PROCESSED_FOLDER, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
                print("Processed folder cleared")
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f'Failed to delete {file_path}. Reason: {e}')

def generate_unique_filename():
    """Generates a unique filename using timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    return f"segmented_{timestamp}"

def segment_and_save(image_path, bounding_boxes):
    """
    Segments objects in an image based on bounding boxes using SAM.
    Saves each segmented object as a transparent PNG and returns filenames.
    """
   
    clear_processed_folder()

    # Load image
    image = cv2.imread(image_path)
    if image is None:
        return {"error": "Image loading failed"}

    
    sam = sam_model_registry[MODEL_TYPE](checkpoint=MODEL_CHECKPOINT)
    sam.to(DEVICE)
    predictor = SamPredictor(sam)
    predictor.set_image(image)

    segmented_images = []
    base_filename = generate_unique_filename()
    
    for i, bbox in enumerate(bounding_boxes):
        
        bbox = np.array(bbox, dtype=np.float32)
        
        
        masks, scores, _ = predictor.predict(box=bbox)

        
        for j, mask in enumerate(masks):
            
            binary_mask = (mask > 0).astype(np.uint8) * 255
            
            
            segmented = cv2.bitwise_and(image, image, mask=binary_mask)
            
            
            transparent = cv2.cvtColor(segmented, cv2.COLOR_BGR2BGRA)
            transparent[:, :, 3] = binary_mask

            
            filename = f"{base_filename}_{i}_{j}.png"
            save_path = os.path.join(PROCESSED_FOLDER, filename)
            cv2.imwrite(save_path, transparent)
            segmented_images.append(filename)

    return {"images": segmented_images}

@app.route("/process", methods=["POST"])
def process_image():
    """Endpoint for processing image with bounding boxes"""
    
    if "image" not in request.files or "coordinates" not in request.form:
        return jsonify({"error": "Image and coordinates are required"}), 400

    
    image_file = request.files["image"]
    if image_file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    image_path = os.path.join(UPLOAD_FOLDER, image_file.filename)
    image_file.save(image_path)

    
    try:
        bounding_boxes = json.loads(request.form["coordinates"])
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid coordinates format"}), 400

    
    try:
        results = segment_and_save(image_path, bounding_boxes)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/processed/<filename>")
def serve_processed_image(filename):
    """Endpoint to serve processed images with no-cache headers"""
    response = send_from_directory(PROCESSED_FOLDER, filename)
    
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
