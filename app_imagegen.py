from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import torch
import os
from diffusers import StableDiffusionXLPipeline, StableDiffusion3Pipeline
from huggingface_hub import login
from io import BytesIO
import uuid
import threading
import logging
import time
from collections import deque
import traceback 


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)


HF_TOKEN = os.getenv("HF_TOKEN")
MODEL_CACHE_DIR = "./model_cache"
OUTPUT_DIR = "./generated_images"
os.makedirs(OUTPUT_DIR, exist_ok=True)


task_statuses = {}
task_lock = threading.Lock()
MAX_TASKS_HISTORY = 100
task_history = deque(maxlen=MAX_TASKS_HISTORY)


def get_task_status(task_id):
    with task_lock:
        return task_statuses.get(task_id)

def update_task_status(task_id, status, progress=None, result_url=None, error=None):
    with task_lock:
        if task_id in task_statuses:
            task = task_statuses[task_id]
            task['status'] = status
            if progress is not None:
                task['progress'] = progress
            if result_url is not None:
                task['result_url'] = result_url
            if error is not None:
                task['error'] = error
            task['last_updated'] = time.time() 
        else:
            
             logger.warning(f"Attempted to update non-existent task: {task_id}")


def add_task(task_id):
    with task_lock:
        task_statuses[task_id] = {
            'task_id': task_id,
            'status': 'pending',
            'progress': 0.0, 
            'result_url': None,
            'error': None,
            'start_time': time.time(),
            'last_updated': time.time()
        }
        task_history.append(task_id)
        

def remove_task(task_id):
    with task_lock:
        task_statuses.pop(task_id, None)
        



loaded_models = {}
current_model = None

def clear_gpu_cache():
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        logger.info("Cleared GPU cache")
        

def load_model(model_type):
    """Dynamically load the requested model"""
    global current_model

    
    if current_model and current_model != model_type:
        logger.info(f"Unloading {current_model} model")
        # Use del to release references, then pop from dict
        if current_model in loaded_models:
             del loaded_models[current_model]
             loaded_models.pop(current_model, None)
        clear_gpu_cache()
        current_model = None

   
    if model_type in loaded_models:
        return loaded_models[model_type]

    try:
        logger.info(f"Loading {model_type} model...")

        if HF_TOKEN:
           
            try:
                login(token=HF_TOKEN)
            except Exception as e:
                 logger.warning(f"Hugging Face login failed: {e}")

        if model_type == "fast":
           
            local_file_path = os.path.join("sd_xl_base_1.0.safetensors")
            if os.path.exists(local_file_path):
                 model_path = local_file_path
                 from_single_file = True
            else:
                 
                 logger.warning(f"Local model file not found at {local_file_path}. Attempting to load from Hugging Face Hub.")
                 model_path = "stabilityai/stable-diffusion-xl-base-1.0"
                 from_single_file = False 

            if from_single_file:
                 pipe = StableDiffusionXLPipeline.from_single_file(
                    model_path,
                    torch_dtype=torch.float16,
                    use_safetensors=True,
                    cache_dir=MODEL_CACHE_DIR 
                 )
            else:
                 pipe = StableDiffusionXLPipeline.from_pretrained(
                    model_path,
                    torch_dtype=torch.float16,
                    use_safetensors=True, 
                    cache_dir=MODEL_CACHE_DIR 
                 )


            if torch.cuda.is_available():
                pipe = pipe.to("cuda")
            else:
                 
                 logger.warning("CUDA not available, loading Fast model on CPU. Generation will be slow.")
                 pipe.to("cpu")

        else:  # slow (Stable Diffusion 3.5)
            pipe = StableDiffusion3Pipeline.from_pretrained(
                "stabilityai/stable-diffusion-3.5-large",
                # Use float16 if bfloat16 causes issues or isn't supported well on your GPU
                torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32, # Use float32 on CPU
                cache_dir=MODEL_CACHE_DIR, 
            )
            pipe.enable_model_cpu_offload()
            #For Faster GPU processing. 
            
            #if torch.cuda.is_available():
                 #pipe.to("cuda")
                 # THIS LINE ENABLES CPU OFFLOADING:
                 #pipe.enable_model_cpu_offload() 
            #else:
                 #logger.warning("CUDA not available, loading Slow model on CPU. Generation will be *very* slow.")
                 #pipe.to("cpu") # Ensure it's on CPU


        loaded_models[model_type] = pipe
        current_model = model_type
        logger.info(f"{model_type} model loaded successfully")
        return pipe

    except Exception as e:
        logger.error(f"Failed to load {model_type} model: {str(e)}")
        
        loaded_models.pop(model_type, None)
        current_model = None
        clear_gpu_cache()
        raise 


def generate_task(task_id, prompt, mode):
    logger.info(f"Task {task_id}: Starting generation...")
    update_task_status(task_id, 'running', progress=0.0)

    try:
       d
        clear_gpu_cache()
        logger.debug(f"Task {task_id}: Cleared GPU cache before model load.")

        
        pipe = load_model(mode)

        
        params = {
            "prompt": prompt,
            
            "width": 768 if mode == 'fast' else 1024,
            "height": 768 if mode == 'fast' else 1024,
            "num_inference_steps": 20 if mode == 'fast' else 28,
            "guidance_scale": 7.5
        }

        logger.info(f"Task {task_id}: Generating with params: {params}")

        .
        image = pipe(**params).images[0]


       
        filename = f"{task_id}.png"
        filepath = os.path.join(OUTPUT_DIR, filename)
        image.save(filepath)

        
        update_task_status(task_id, 'completed', progress=1.0, result_url=f'/result/{task_id}')
        logger.info(f"Task {task_id}: Generation completed. Result saved to {filepath}")

    except torch.cuda.OutOfMemoryError:
        
        error_msg = "GPU memory exhausted. Please try a smaller image size or wait a few minutes."
        logger.error(f"Task {task_id}: {error_msg}")
        update_task_status(task_id, 'failed', error=error_msg)
    except Exception as e:
        
        error_msg = f"Generation failed: {str(e)}"
        logger.error(f"Task {task_id}: {error_msg}\n{traceback.format_exc()}")
        update_task_status(task_id, 'failed', error=str(e))
    finally:
       
        clear_gpu_cache()
        logger.debug(f"Task {task_id}: Cleared GPU cache in finally block.")
        
    
    

# --- Flask Routes ---

@app.route('/generate', methods=['POST'])
def generate_image():
    data = request.json
    prompt = data.get('prompt', '')
    mode = data.get('mode', 'fast') # Default to fast

    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400

    if mode not in ['fast', 'slow']:
        return jsonify({"error": "Invalid mode"}), 400

    task_id = str(uuid.uuid4())
    add_task(task_id)

    logger.info(f"Received generation request. Task ID: {task_id}, Mode: {mode}")

    thread = threading.Thread(target=generate_task, args=(task_id, prompt, mode))
    thread.start()

    
    return jsonify({"task_id": task_id, "status": "accepted"}), 202 # 202 Accepted
    

@app.route('/status/<task_id>', methods=['GET'])
def task_status(task_id):
    status = get_task_status(task_id)
    if status:
        return jsonify({
            "task_id": status['task_id'],
            "status": status['status'],
            "progress": status.get('progress', 0.0), 
            "error": status['error'],
            "result_url": status['result_url'] if status['status'] == 'completed' else None
        }), 200
    else:
        return jsonify({"error": "Task not found"}), 404

@app.route('/result/<task_id>', methods=['GET'])
def task_result(task_id):
    status = get_task_status(task_id)
    if status and status['status'] == 'completed' and status['result_url']:
        filename = f"{task_id}.png"
        filepath = os.path.join(OUTPUT_DIR, filename)

        if os.path.exists(filepath):
            logger.info(f"Sending result file for task {task_id}")
            return send_file(filepath, mimetype='image/png', as_attachment=True, download_name=filename)
        else:
             logger.error(f"Task {task_id} marked completed but file not found at {filepath}")
             return jsonify({"error": "Result file not found"}), 404
    elif status and status['status'] == 'failed':
        return jsonify({"error": status['error']}), 500 
    elif status: 
         return jsonify({"error": "Task not yet completed"}), 409 
    else:
        return jsonify({"error": "Task not found"}), 404



@app.route('/status', methods=['GET'])
def server_status():
    
    gpu_info = None
    try:
        if torch.cuda.is_available():
            gpu_info = {
                "total": torch.cuda.get_device_properties(0).total_memory,
                "reserved": torch.cuda.memory_reserved(0),
                "allocated": torch.cuda.memory_allocated(0),
                "free": torch.cuda.mem_get_info(0)[0] 
            }
    except Exception as e:
        logger.error(f"Failed to get GPU info: {e}")
        gpu_info = {"error": "Could not retrieve GPU information"}


   
    active_tasks = [id for id, status in task_statuses.items() if status['status'] in ['pending', 'running']]
    
    recent_completed_tasks = [id for id in task_history if task_statuses.get(id, {}).get('status') == 'completed']
    recent_failed_tasks = [id for id in task_history if task_statuses.get(id, {}).get('status') == 'failed']


    return jsonify({
        "current_model_loaded": current_model,
        "loaded_models": list(loaded_models.keys()),
        "gpu_memory": gpu_info,
        "active_tasks": active_tasks,
        "recent_completed_tasks": recent_completed_tasks,
        "recent_failed_tasks": recent_failed_tasks,
        "total_tasks_tracked": len(task_statuses)
    })


@app.route('/unload', methods=['POST'])
def unload_models():
    global loaded_models, current_model
    logger.info("Initiating model unload...")
    
    try:
        for model_type in list(loaded_models.keys()):
            logger.info(f"Unloading {model_type}...")
            del loaded_models[model_type]
            loaded_models.pop(model_type, None)
        loaded_models = {} 
        current_model = None
        clear_gpu_cache()
        logger.info("All models unloaded.")
        return jsonify({"status": "All models unloaded"})
    except Exception as e:
         logger.error(f"Error during model unload: {e}")
         return jsonify({"error": "Failed to unload models", "details": str(e)}), 500


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5000,
        threaded=True, 
        debug=os.getenv("FLASK_DEBUG", "false").lower() == "true",
       
    )
