<template>
  <div class="genvision-app">
    <div class="genvision-container">
      <router-link to="/" style="text-decoration: none; color: inherit;"><h1 class="title">IsoVision</h1></router-link>
      <p class="subtitle">Generate stunning images from text prompts</p>

      <div class="prompt-container">
        <div class="prompt-box">
          <textarea
            v-model="prompt"
            placeholder="Enter your prompt (at least 3 words)..."
            @input="validatePrompt"
            :disabled="processing || taskId"
          ></textarea>
          <p v-if="error" class="error-message">{{ error }}</p>
        </div>

        <div class="mode-selection">
          <div
            class="mode-option"
            @click="selectMode('fast')"
            :class="{ active: mode === 'fast', disabled: processing || taskId }"
            :disabled="processing || taskId"
          >
            <h3>Fast</h3>
            <p>Quick results with basic quality</p>
          </div>

          <div
            class="mode-option"
            @click="selectMode('slow')"
            :class="{ active: mode === 'slow', disabled: processing || taskId }"
            :disabled="processing || taskId"
          >
            <h3>Slow</h3>
            <p>Higher quality with longer wait</p>
          </div>
        </div>

        <button
          class="generate-btn"
          :disabled="!isValid || processing || !mode"
          @click="startGeneration"
        >
          <span v-if="!processing">Generate Images</span>
          <span v-else-if="taskStatus === 'pending'" class="processing-text">Starting...</span>
          <span v-else-if="taskStatus === 'running'" class="processing-text">Generating...</span>
          <span v-else-if="taskStatus === 'completed'">Completed!</span>
          <span v-else-if="taskStatus === 'failed'">Failed</span>
          <span v-else class="processing-text">Processing...</span> </button>
      </div>

      <div v-if="showModeInfo" class="mode-info-modal">
        <div class="modal-content">
          <h3>{{ modeInfo.title }}</h3>
          <p>{{ modeInfo.description }}</p>
          <button @click="confirmMode">Proceed</button>
          <button @click="cancelMode" class="cancel-btn">Cancel</button>
        </div>
      </div>

      <div v-if="processing && !showModeInfo" class="processing-modal">
        <div class="modal-content">
          <h3>{{ taskStatus === 'pending' ? 'Starting Task...' : taskStatus === 'running' ? 'Generating Image...' : 'Processing...' }}</h3>
          <p v-if="taskStatus === 'running'">Please wait while your image is being generated. This might take some time.</p>
           <p v-if="taskStatus === 'failed'" class="error-message">Error: {{ error || 'An unknown error occurred.' }}</p>
           <button v-if="taskStatus === 'failed'" @click="resetState">Try Again</button>
        </div>
      </div>


      <div v-if="resultImages.length > 0" class="results-container">
        <h2>Generated Results</h2>
        <div class="results-grid">
          <div v-for="(image, index) in resultImages" :key="index" class="result-item">
            <img :src="image" :alt="`Generated image ${index + 1}`" />
            <a :href="image" :download="`isovision-result-${taskId || 'unknown'}-${index + 1}.png`" class="download-btn">
              Download
            </a>
          </div>
        </div>
      </div>
      <div class="attribution">
        By Somendra Saini | 2025 | 0fRedesign.tech
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'GenVision',
  data() {
    return {
      prompt: '',
      mode: null,
      isValid: false,
      error: '',
      processing: false, 
      showModeInfo: false,
      resultImages: [],
      modeInfo: {
        title: '',
        description: ''
      },
      
      taskId: null,
      taskStatus: null, 
      taskProgress: 0, // 0.0 to 1.0
      pollingTimer: null,
      pollingInterval: 3000, // Poll every 3 seconds
    }
  },
  methods: {
    validatePrompt() {
      const words = this.prompt.trim().split(/\s+/).filter(word => word.length > 0)
      if (words.length < 3) {
        this.error = 'Please enter at least 3 words'
        this.isValid = false
      } else {
        this.error = ''
        this.isValid = true
      }
    },
    selectMode(mode) {
      if (this.processing || this.taskId) return;

      this.mode = mode
      this.showModeInfo = true

      if (mode === 'fast') {
        this.modeInfo = {
          title: 'Fast Generation Mode',
          description: 'Results will be generated quickly but might lack some detail and refinement. Uses SDXL 1.0.'
        }
      } else {
        this.modeInfo = {
          title: 'Slow Generation Mode',
          description: 'Using a more advanced model for better quality results. This will take more time and significant resources (GPU memory). Uses Stable Diffusion 3.5 Large.'
        }
      }
      this.error = ''; 
    },
    confirmMode() {
      this.showModeInfo = false
    },
    cancelMode() {
      this.showModeInfo = false
      this.mode = null 
    },
    async startGeneration() {
      if (!this.isValid || this.processing || !this.mode) return;

      this.processing = true;
      this.taskStatus = null; 
      this.taskProgress = 0;
      this.resultImages = []; 
      this.error = ''; 
      this.taskId = null; 

      try {
        const response = await fetch('https://isovision-ai.somendrasaini.com/generate', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            prompt: this.prompt,
            mode: this.mode
          }),
           signal: AbortSignal.timeout(10000) 
        });

        if (!response.ok) {
           
          const errorText = await response.text();
          let errorMessage = `HTTP error! status: ${response.status}`;
          try {
             const errorJson = JSON.parse(errorText);
             errorMessage = errorJson.error || errorMessage;
          } catch {
             errorMessage = `${errorMessage} - ${errorText}`;
          }
          throw new Error(errorMessage);
        }

        const data = await response.json();
        this.taskId = data.task_id;
        this.taskStatus = 'pending'; 
        console.info(`Generation task started with ID: ${this.taskId}`); 

        
        this.startPolling();

      } catch (error) {
        console.error('Failed to start generation task:', error); 
        this.error = 'Failed to start generation: ' + error.message;
        this.processing = false;
        this.taskId = null;
        this.taskStatus = 'failed'; 
      }
    },

    startPolling() {
        if (!this.taskId) return;

      
        this.stopPolling();

        this.pollingTimer = setInterval(async () => {
            try {
                 
                 const controller = new AbortController();
                 const timeoutId = setTimeout(() => controller.abort(), 5000); // Timeout each poll after 5s

                const response = await fetch(`https://isovision-ai.somendrasaini.com/status/${this.taskId}`, {
                     signal: controller.signal
                });

                clearTimeout(timeoutId); 

                if (!response.ok) {
                     const errorText = await response.text();
                     let errorMessage = `Polling error: HTTP status ${response.status}`;
                     try {
                        const errorJson = JSON.parse(errorText);
                        errorMessage = errorJson.error || errorMessage;
                     } catch {
                        errorMessage = `${errorMessage} - ${errorText}`;
                     }
                     throw new Error(errorMessage);
                }

                const statusData = await response.json();
                this.taskStatus = statusData.status;
                this.taskProgress = statusData.progress || 0; 
                this.error = statusData.error || ''; 

                console.debug(`Polling status for ${this.taskId}: ${this.taskStatus}`); 

                if (this.taskStatus === 'completed') {
                    this.stopPolling();
                    console.info(`Task ${this.taskId} completed. Fetching result.`); 
                    await this.fetchResult(this.taskId); 
                    this.processing = false; 
                } else if (this.taskStatus === 'failed') {
                    this.stopPolling();
                    console.error(`Task ${this.taskId} failed: ${this.error}`); 
                    this.processing = false; 
                }

            } catch (error) {
                console.error(`Polling failed for task ${this.taskId}:`, error); 
                this.stopPolling();
                 if (error.name === 'AbortError') {
                     this.error = 'Polling timed out. Server might be slow to respond.';
                 } else {
                     this.error = 'Error while polling task status: ' + error.message;
                 }
                this.taskStatus = 'failed'; 
                this.processing = false;
            }
        }, this.pollingInterval);
    },

    stopPolling() {
      if (this.pollingTimer) {
        clearInterval(this.pollingTimer);
        this.pollingTimer = null;
        console.debug(`Stopped polling for task ${this.taskId}`); 
      }
    },

    async fetchResult(taskId) {
        try {
             
             const controller = new AbortController();
             const timeoutId = setTimeout(() => controller.abort(), 60000); 
            const response = await fetch(`https://isovision-ai.somendrasaini.com/result/${taskId}`, {
                 signal: controller.signal
            });

             clearTimeout(timeoutId); 

            if (!response.ok) {
                 const errorText = await response.text();
                 let errorMessage = `Failed to fetch result: HTTP status ${response.status}`;
                 try {
                    const errorJson = JSON.parse(errorText);
                    errorMessage = errorJson.error || errorMessage;
                 } catch {
                    errorMessage = `${errorMessage} - ${errorText}`;
                 }
                throw new Error(errorMessage);
            }

            const blob = await response.blob();
            const imageUrl = URL.createObjectURL(blob);
            this.resultImages = [imageUrl]; 

            console.info(`Successfully fetched result for task ${taskId}`); 

        } catch (error) {
            console.error(`Failed to fetch result for task ${taskId}:`, error); 
            if (error.name === 'AbortError') {
                this.error = 'Fetching result timed out.';
            } else {
                 this.error = 'Failed to retrieve image result: ' + error.message;
            }
            this.taskStatus = 'failed'; 
        }
    },

    resetState() {
        this.prompt = '';
        this.mode = null;
        this.isValid = false;
        this.error = '';
        this.processing = false;
        this.showModeInfo = false;
        this.resultImages = [];
        this.taskId = null;
        this.taskStatus = null;
        this.taskProgress = 0;
        this.stopPolling(); 
    }
  },
  watch: {
      taskStatus(/* newValue, oldValue */) { 
      }
  },
  beforeUnmount() {
    this.stopPolling();
    this.resultImages.forEach(url => URL.revokeObjectURL(url));
  }
}
</script>

<style>

@import url('https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Product+Sans:wght@400;500;700&display=swap');

.genvision-app {
  min-height: 100vh;
  width: 100vw;
  padding: 2rem;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  background-color: #000;
  color: #fff;
  box-sizing: border-box; 
}

.genvision-container {
  max-width: 1200px;
  width: 100%;
  margin: 0 auto;
  animation: fadeIn 0.5s ease-out;
}

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
  font-family: 'Product Sans', sans-serif;
}

.subtitle {
  font-size: 1.25rem;
  opacity: 0.8;
  margin-bottom: 2rem;
  text-align: left;
  font-weight: 400;
  max-width: 600px;
  font-family: 'Product Sans', sans-serif;
}

.prompt-container {
  margin: 2rem 0;
  background-color: rgba(255, 255, 255, 0.02);
  border-radius: 16px;
  padding: 2rem;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.prompt-box {
  margin-bottom: 2rem;
}

.prompt-box textarea {
  width: 100%;
  min-height: 150px;
  padding: 1rem;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background-color: rgba(255, 255, 255, 0.05);
  color: white;
  font-size: 1rem;
  font-family: 'Product Sans', sans-serif;
  resize: vertical;
  transition: border-color 0.3s ease;
}

.prompt-box textarea:focus {
  outline: none;
  border-color: #4285F4;
}
.prompt-box textarea:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.error-message {
  margin-top: 0.5rem;
  color: #EA4335;
  font-size: 0.9rem;
  font-family: 'Product Sans', sans-serif;
}

.mode-selection {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
}

.mode-option {
  flex: 1;
  padding: 1.5rem;
  border-radius: 12px;
  background-color: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  cursor: pointer;
  transition: all 0.3s ease;
}

.mode-option:hover:not(.disabled) {
  background-color: rgba(255, 255, 255, 0.1);
  transform: translateY(-2px);
}

.mode-option.active {
  background-color: rgba(66, 133, 244, 0.2);
  border-color: #4285F4;
}

.mode-option.disabled {
    opacity: 0.6;
    cursor: not-allowed;
}

.mode-option h3 {
  font-size: 1.25rem;
  margin-bottom: 0.5rem;
  font-family: 'Instrument Sans', sans-serif;
  font-weight: 700;
}

.mode-option p {
  font-size: 0.9rem;
  opacity: 0.8;
  font-family: 'Product Sans', sans-serif;
}

.generate-btn {
  width: 100%;
  padding: 1.25rem;
  border-radius: 12px;
  border: none;
  background-color: #4285F4;
  color: white;
  font-size: 1.1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  font-family: 'Product Sans', sans-serif;
}

.generate-btn:hover:not(:disabled) {
  background-color: #3367d6;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(66, 133, 244, 0.3);
}

.generate-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.processing-text {
  display: inline-block;
  position: relative;
}

.processing-text::after {
  content: '...';
  position: absolute;
  animation: dots 1.5s steps(5, end) infinite;
}


.mode-info-modal, .processing-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  backdrop-filter: blur(5px);
}

.modal-content {
  background-color: rgba(30, 30, 30, 0.95);
  padding: 2rem;
  border-radius: 16px;
  max-width: 500px;
  width: 90%;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.1);
  text-align: center; 
}

.modal-content h3 {
  font-size: 1.5rem;
  margin-bottom: 1rem;
  font-family: 'Instrument Sans', sans-serif;
  font-weight: 700;
}

.modal-content p {
  margin-bottom: 2rem;
  font-family: 'Product Sans', sans-serif;
  line-height: 1.6;
}
.modal-content .error-message {
    color: #EA4335;
    margin-top: 1rem;
    margin-bottom: 0;
}


.modal-content button {
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  border: none;
  background-color: #34A853;
  color: white;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  font-family: 'Product Sans', sans-serif;
  margin: 0.5rem;
}

.modal-content button:hover {
  background-color: #2d9248;
  transform: translateY(-2px);
}

.modal-content .cancel-btn {
  background-color: #EA4335;
}

.modal-content .cancel-btn:hover {
  background-color: #d33a2d;
}


.results-container {
  margin-top: 3rem;
  animation: fadeInUp 0.5s ease-out;
}

.results-container h2 {
  font-size: 2rem;
  margin-bottom: 1.5rem;
  color: #fff;
  font-weight: 600;
  font-family: 'Product Sans', sans-serif;
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
  object-fit: cover;
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
  font-family: 'Product Sans', sans-serif;
}

.download-btn:hover {
  background-color: #3367d6;
  letter-spacing: 0.5px;
}

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

@keyframes dots {
  0%, 20% { content: '.'; }
  40% { content: '..'; }
  60%, 100% { content: '...'; }
}

@media (max-width: 768px) {
  .title {
    font-size: 2.5rem;
  }

  .subtitle {
    font-size: 1.1rem;
  }

  .mode-selection {
    flex-direction: column;
  }

  .results-grid {
    grid-template-columns: 1fr;
  }
    .modal-content button {
        width: calc(100% - 1rem); 
        margin: 0.5rem 0.5rem;
    }
}

.attribution {
  position: fixed;
  bottom: 20px;
  right: 20px;
  font-size: 0.8rem;
  opacity: 0.7;
  color: #888; 
  font-family: 'Product Sans', sans-serif;
  transition: opacity 0.3s ease;
  z-index: 10; 
}

.attribution:hover {
  opacity: 1;
  color: #aaa;
}

@media (max-width: 768px) {
  .attribution {
    font-size: 0.7rem;
    bottom: 15px;
    right: 15px;
    background: rgba(0,0,0,0.3); 
    padding: 4px 8px;
    border-radius: 4px;
    color: #ccc; 
  }
}


</style>
