<template>
  <div class="isovision-app">
    <div class="isovision-container">
      <router-link to="/" style="text-decoration: none; color: inherit;"><h1 class="title">IsoVision</h1></router-link>
      <p class="subtitle">Select a part of image and isolate it.</p>
      
      <div class="upload-container">
        <div 
          v-if="!originalImage"
          class="upload-box"
          @click="triggerFileInput"
        >
          <div class="upload-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="17 8 12 3 7 8"></polyline>
              <line x1="12" y1="3" x2="12" y2="15"></line>
            </svg>
          </div>
          <p>Click to upload an image</p>
        </div>
        
        <div v-else class="image-processing-container">
          <div class="image-selection-area">
            <img 
              ref="imageElement"
              :src="originalImage" 
              alt="Uploaded image"
              @load="imageLoaded"
              crossorigin="anonymous"
            />
            <canvas 
              ref="selectionCanvas"
              class="selection-canvas"
              @mousedown="startSelection"
              @mousemove="drawSelection"
              @mouseup="endSelection"
              @mouseleave="endSelection"
              @touchstart="handleTouchStart"
              @touchmove="handleTouchMove"
              @touchend="handleTouchEnd"
            ></canvas>
          </div>
          
          <div v-if="selectionMade" class="selection-actions">
            <button @click="confirmSelection" class="confirm-btn">
              <span v-if="!processing">Confirm Selection</span>
              <span v-else class="processing-text">Processing...</span>
            </button>
            <button @click="resetSelection" class="reset-btn">Reset</button>
          </div>
        </div>
        
        <input 
          type="file" 
          ref="fileInput"
          accept="image/*"
          @change="handleImageUpload"
          style="display: none;"
        />
      </div>
      
      <div v-if="resultImages.length > 0" class="results-container">
        <h2>Results</h2>
        <div class="results-grid">
          <div v-for="(image, index) in resultImages" :key="index" class="result-item">
            <img 
              :src="getImageUrl(image)" 
              :alt="`Result ${index + 1}`"
              @error="handleImageError(index)"
            />
            <a 
              :href="getImageUrl(image)" 
              :download="`isovision-result-${index + 1}.png`"
              class="download-btn"
            >
              Download
            </a>
          </div>
        </div>
      </div>

      <div v-if="error" class="error-message">
        {{ error }}
      </div>
      <div class="attribution">
          By Somendra Saini | 2025 | 0fRedesign.tech
        </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'IsoVision',
  data() {
    return {
      originalImage: null,
      selection: {
        startX: 0,
        startY: 0,
        endX: 0,
        endY: 0,
        isSelecting: false
      },
      selectionMade: false,
      processing: false,
      resultImages: [],
      imageDimensions: {
        width: 0,
        height: 0
      },
      error: null
    }
  },
  methods: {
    triggerFileInput() {
      try {
        // Wait for next tick to ensure DOM is ready
        this.$nextTick(() => {
          const fileInput = this.$refs.fileInput;
          if (fileInput && fileInput.click) {
            fileInput.click();
          } else {
            console.error('File input element not found');
            this.error = 'Failed to access file input. Please try again.';
          }
        });
      } catch (error) {
        console.error('Error triggering file input:', error);
        this.error = 'An error occurred while accessing the file input.';
      }
    },

    async handleImageUpload(event) {
      this.error = null;
      const file = event?.target?.files?.[0];
      if (!file) return;
      
      try {
        if (!file.type.match('image.*')) {
          throw new Error('Please select an image file (JPEG, PNG, etc.)');
        }
        
        // Clear previous state
        this.originalImage = await this.readFileAsDataURL(file);
        this.selectionMade = false;
        this.resultImages = [];
        this.error = null;
        
        // Load image dimensions
        await this.loadImageDimensions();
      } catch (error) {
        this.error = error.message || 'Failed to load image';
        console.error('Image upload error:', error);
      }
    },

    readFileAsDataURL(file) {
      return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = (e) => resolve(e.target.result);
        reader.onerror = () => reject(new Error('Failed to read file'));
        reader.readAsDataURL(file);
      });
    },

    loadImageDimensions() {
      return new Promise((resolve, reject) => {
        const img = new Image();
        img.onload = () => {
          this.imageDimensions = {
            width: img.width,
            height: img.height
          };
          resolve();
        };
        img.onerror = () => reject(new Error('Failed to load image dimensions'));
        img.src = this.originalImage;
      });
    },

    imageLoaded() {
      const img = this.$refs.imageElement;
      const canvas = this.$refs.selectionCanvas;
      
      if (img && canvas) {
        canvas.width = img.width;
        canvas.height = img.height;
      }
    },

    getImageElementRect() {
      const img = this.$refs.imageElement;
      if (!img) {
        throw new Error('Image element not found');
      }
      return img.getBoundingClientRect();
    },

    startSelection(e) {
      if (this.processing) return;
      
      try {
        const rect = this.getImageElementRect();
        const clientX = e.clientX ?? e.touches?.[0]?.clientX;
        const clientY = e.clientY ?? e.touches?.[0]?.clientY;
        
        if (typeof clientX !== 'number' || typeof clientY !== 'number') {
          throw new Error('Invalid coordinates');
        }

        this.selection = {
          startX: clientX - rect.left,
          startY: clientY - rect.top,
          endX: clientX - rect.left,
          endY: clientY - rect.top,
          isSelecting: true
        };
        this.selectionMade = false;
        this.drawSelectionBox();
      } catch (error) {
        console.error('Selection error:', error);
        this.error = 'Failed to start selection. Please try again.';
      }
    },

    drawSelection(e) {
      if (!this.selection.isSelecting) return;
      
      try {
        const rect = this.getImageElementRect();
        const clientX = e.clientX ?? e.touches?.[0]?.clientX;
        const clientY = e.clientY ?? e.touches?.[0]?.clientY;
        
        if (typeof clientX !== 'number' || typeof clientY !== 'number') {
          throw new Error('Invalid coordinates');
        }

        this.selection.endX = clientX - rect.left;
        this.selection.endY = clientY - rect.top;
        this.drawSelectionBox();
      } catch (error) {
        console.error('Drawing error:', error);
        this.endSelection();
      }
    },

    endSelection() {
      this.selection.isSelecting = false;
      
      const minSelectionSize = 10;
      if (Math.abs(this.selection.endX - this.selection.startX) > minSelectionSize && 
          Math.abs(this.selection.endY - this.selection.startY) > minSelectionSize) {
        this.selectionMade = true;
      }
    },

    handleTouchStart(e) {
      e.preventDefault();
      this.startSelection(e);
    },

    handleTouchMove(e) {
      e.preventDefault();
      this.drawSelection(e);
    },

    handleTouchEnd(e) {
      e.preventDefault();
      this.endSelection();
    },

    drawSelectionBox() {
      const canvas = this.$refs.selectionCanvas;
      if (!canvas) return;
      
      const ctx = canvas.getContext('2d');
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      const x = Math.min(this.selection.startX, this.selection.endX);
      const y = Math.min(this.selection.startY, this.selection.endY);
      const width = Math.abs(this.selection.endX - this.selection.startX);
      const height = Math.abs(this.selection.endY - this.selection.startY);
      
      ctx.strokeStyle = '#4285F4';
      ctx.lineWidth = 2;
      ctx.setLineDash([5, 5]);
      ctx.strokeRect(x, y, width, height);
      
      ctx.fillStyle = 'rgba(66, 133, 244, 0.2)';
      ctx.fillRect(x, y, width, height);
    },

    resetSelection() {
      const canvas = this.$refs.selectionCanvas;
      if (!canvas) return;
      
      const ctx = canvas.getContext('2d');
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      this.selection = {
        startX: 0,
        startY: 0,
        endX: 0,
        endY: 0,
        isSelecting: false
      };
      this.selectionMade = false;
    },

    async confirmSelection() {
  if (!this.selectionMade || this.processing) return;

  this.error = null;
  this.processing = true;

  try {
    const coordinates = this.getNormalizedCoordinates();
    const formData = new FormData();
    formData.append('image', await this.dataURLtoFile(this.originalImage, 'image.png'));
    formData.append('coordinates', JSON.stringify([coordinates]));

    const response = await fetch('https://isovision-backend.somendrasaini.com/process', {
      method: 'POST',
      body: formData,
      headers: {
        'Accept': 'application/json'
      }
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `Server error: ${response.status}`);
    }

    const data = await response.json();
    
    if (!data.images || data.images.length === 0) {
      throw new Error('No segmented images were returned');
    }

    this.resultImages = data.images;
  } catch (error) {
    console.error('Image processing error:', error);
    this.error = error.message || 'Failed to process image. Please try again.';
  } finally {
    this.processing = false;
  }
},

    getNormalizedCoordinates() {
      const img = this.$refs.imageElement;
      if (!img) return [[0, 0], [0, 0]];
      
      const scaleX = this.imageDimensions.width / img.width;
      const scaleY = this.imageDimensions.height / img.height;
      
      const x1 = Math.min(this.selection.startX, this.selection.endX) * scaleX;
      const y1 = Math.min(this.selection.startY, this.selection.endY) * scaleY;
      const x2 = Math.max(this.selection.startX, this.selection.endX) * scaleX;
      const y2 = Math.max(this.selection.startY, this.selection.endY) * scaleY;
      
      return [
        [Math.round(x1), Math.round(y1)],
        [Math.round(x2), Math.round(y2)]
      ];
    },

    dataURLtoFile(dataurl, filename) {
      const arr = dataurl.split(',');
      const mime = arr[0].match(/:(.*?);/)[1];
      const bstr = atob(arr[1]);
      let n = bstr.length;
      const u8arr = new Uint8Array(n);
      
      while (n--) {
        u8arr[n] = bstr.charCodeAt(n);
      }
      
      return new File([u8arr], filename, { type: mime });
    },

    getImageUrl(imagePath) {
      return `https://isovision-backend.somendrasaini.com/processed/${imagePath}`;
    },

    handleImageError(index) {
      console.error(`Failed to load image: ${this.resultImages[index]}`);
      this.resultImages.splice(index, 1);
      this.error = 'Failed to load one of the result images';
    }
  },
  mounted() {
    const canvas = this.$refs.selectionCanvas;
    if (canvas) {
      canvas.addEventListener('touchmove', (e) => {
        if (this.selection.isSelecting) {
          e.preventDefault();
        }
      }, { passive: false });
    }
  },
  beforeUnmount() {
    const canvas = this.$refs.selectionCanvas;
    if (canvas) {
      canvas.removeEventListener('touchmove', (e) => {
        if (this.selection.isSelecting) {
          e.preventDefault();
        }
      });
    }
  }
}
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Product+Sans:wght@400;500;700&display=swap');

/* Base Styles */
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html, body {
  height: 100%;
  background-color: #000;
  font-family: 'Product Sans', sans-serif;
  color: #fff;
  line-height: 1.6;
}

/* App Container */
.isovision-app {
  min-height: 100vh;
  width: 100vw;
  padding: 2rem;
  display: flex;
  justify-content: center;
  align-items: center;
}

.isovision-container {
  max-width: 1200px;
  width: 100%;
  margin: 0 auto;
  animation: fadeIn 0.5s ease-out;
}

/* Typography */
.title {
  font-size: 4rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  text-align: left;
  letter-spacing: -0.05em;
  background: linear-gradient(90deg, #4285F4, #34A853, #FBBC05, #EA4335);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  text-shadow: 0 2px 4px rgba(0,0,0,0.2);
  line-height: 1.2;
}

.subtitle {
  font-size: 1.25rem;
  opacity: 0.8;
  margin-bottom: 2rem;
  text-align: left;
  font-weight: 400;
  max-width: 600px;
}

/* Upload Container */
.upload-container {
  margin: 2rem 0;
  background-color: rgba(255, 255, 255, 0.02);
  border-radius: 16px;
  padding: 2rem;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  transition: all 0.3s ease;
}

.upload-box {
  border: 2px dashed rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  padding: 3rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background-color: rgba(255, 255, 255, 0.05);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
}

.upload-box:hover {
  border-color: #4285F4;
  background-color: rgba(66, 133, 244, 0.1);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(66, 133, 244, 0.2);
}

.upload-icon {
  margin-bottom: 1.5rem;
  transition: transform 0.3s ease;
}

.upload-box:hover .upload-icon {
  transform: scale(1.1);
}

.upload-box p {
  font-size: 1.1rem;
  color: rgba(255, 255, 255, 0.8);
  transition: color 0.3s ease;
}

.upload-box:hover p {
  color: #fff;
}

/* Image Processing Area */
.image-processing-container {
  position: relative;
  width: 100%;
  margin: 0 auto;
}

.image-selection-area {
  position: relative;
  display: inline-block;
  max-width: 100%;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.image-selection-area img {
  max-width: 100%;
  max-height: 70vh;
  display: block;
  border-radius: 8px;
  object-fit: contain;
}

.selection-canvas {
  position: absolute;
  top: 0;
  left: 0;
  cursor: crosshair;
  touch-action: none;
  -webkit-tap-highlight-color: transparent;
}

/* Selection Actions */
.selection-actions {
  margin-top: 1.5rem;
  display: flex;
  gap: 1rem;
  justify-content: center;
  flex-wrap: wrap;
}

button {
  font-family: 'Product Sans', sans-serif;
  padding: 1rem 2rem;
  border: none;
  border-radius: 24px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 200px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.confirm-btn {
  background-color: #34A853;
  color: white;
}

.confirm-btn:hover:not(:disabled) {
  background-color: #2d9248;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(52, 168, 83, 0.3);
}

.reset-btn {
  background-color: #EA4335;
  color: white;
}

.reset-btn:hover {
  background-color: #d33a2d;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(234, 67, 53, 0.3);
}

/* Processing Indicator */
.processing-indicator {
  margin-top: 1.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  color: #FBBC05;
  font-weight: 500;
}

.spinner {
  width: 24px;
  height: 24px;
  border: 3px solid rgba(251, 188, 5, 0.3);
  border-radius: 50%;
  border-top-color: #FBBC05;
  animation: spin 1s ease-in-out infinite;
}

.processing-text {
  display: inline-block;
  min-width: 120px;
  position: relative;
}

.processing-text::after {
  content: '...';
  position: absolute;
  animation: dots 1.5s steps(5, end) infinite;
}

/* Results Container */
.results-container {
  margin-top: 3rem;
  animation: fadeInUp 0.5s ease-out;
}

.results-container h2 {
  font-size: 2rem;
  margin-bottom: 1.5rem;
  color: #fff;
  font-weight: 600;
}

.results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 2rem;
  margin-top: 1.5rem;
}

.result-item {
  background-color: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.result-item:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
  border-color: rgba(255, 255, 255, 0.2);
}

.result-item img {
  width: 100%;
  height: 200px;
  object-fit: contain;
  display: block;
  background-color: rgba(0, 0, 0, 0.2);
}

.download-btn {
  display: block;
  text-align: center;
  padding: 0.85rem;
  background-color: #4285F4;
  color: white;
  text-decoration: none;
  font-weight: 500;
  transition: all 0.3s ease;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.download-btn:hover {
  background-color: #3367d6;
  letter-spacing: 0.5px;
}

/* Error Handling */
.error-message {
  margin-top: 1.5rem;
  padding: 1rem 1.5rem;
  background-color: rgba(234, 67, 53, 0.15);
  border-left: 4px solid #EA4335;
  color: #fff;
  border-radius: 8px;
  animation: shake 0.5s ease;
  font-weight: 500;
}

/* Animations */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes dots {
  0%, 20% { content: '.'; }
  40% { content: '..'; }
  60%, 100% { content: '...'; }
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  20%, 60% { transform: translateX(-5px); }
  40%, 80% { transform: translateX(5px); }
}

/* Responsive Design */
@media (max-width: 1024px) {
  .title {
    font-size: 3.25rem;
  }
  
  .subtitle {
    font-size: 1.1rem;
  }
  
  .upload-box {
    min-height: 250px;
    padding: 2rem;
  }
}

@media (max-width: 768px) {
  .isovision-app {
    padding: 1.5rem;
  }
  
  .title {
    font-size: 2.75rem;
    text-align: center;
  }
  
  .subtitle {
    text-align: center;
    margin-left: auto;
    margin-right: auto;
  }
  
  .upload-container {
    padding: 1.5rem;
  }
  
  .selection-actions {
    flex-direction: column;
    gap: 0.75rem;
  }
  
  button {
    width: 100%;
    padding: 1.25rem 2rem;
  }
  
  .results-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 480px) {
  .title {
    font-size: 2.25rem;
  }
  
  .upload-box {
    padding: 1.5rem;
  }
  
  .upload-box p {
    font-size: 1rem;
  }
  
  .results-container h2 {
    font-size: 1.75rem;
  }
}

/* Utility Classes */
.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.attribution {
  position: fixed;
  bottom: 20px;
  right: 20px;
  font-size: 0.8rem;
  opacity: 0.7;
  color: #888; /* Gray color */
  font-family: 'Product Sans', sans-serif;
  transition: opacity 0.3s ease;
  z-index: 10; /* Ensure it stays above other elements */
}

.attribution:hover {
  opacity: 1;
  color: #aaa; /* Slightly lighter gray on hover */
}

@media (max-width: 768px) {
  .attribution {
    font-size: 0.7rem;
    bottom: 15px;
    right: 15px;
    background: rgba(0,0,0,0.3); /* Semi-transparent background for mobile */
    padding: 4px 8px;
    border-radius: 4px;
    color: #ccc; /* Lighter gray for mobile */
  }
}
</style>