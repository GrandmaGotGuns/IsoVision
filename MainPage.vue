<template>
    <div class="main-page">
      <div class="container">
        <h1 class="title">IsoVision</h1>
        <p class="subtitle">Transform your visual content with AI-powered image segmentation and generation</p>
        
        <div class="description">
          <p>IsoVision offers cutting-edge AI tools to enhance your creative workflow. Segment precise parts of images or generate entirely new visuals from text prompts.</p>
        </div>
        
        <div class="options-container" v-if="imagesLoaded">
          <router-link to="/segment" class="option-card" @mouseenter="animateCard(0)" @mouseleave="resetCard(0)">
            <div class="card-bg" :style="{ backgroundImage: `url(${cardImages[0]})` }" ref="bg1"></div>
            <div class="card-overlay"></div>
            <div class="card-content">
              <h2>Segment Images</h2>
              <p class="card-description">Precisely isolate elements from your images with AI</p>
              <div class="arrow-container">
                <svg ref="arrow1" class="arrow" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2">
                  <path d="M5 12h14M12 5l7 7-7 7"/>
                </svg>
              </div>
            </div>
          </router-link>
          
          <router-link to="/generate" class="option-card" @mouseenter="animateCard(1)" @mouseleave="resetCard(1)">
            <div class="card-bg" :style="{ backgroundImage: `url(${cardImages[1]})` }" ref="bg2"></div>
            <div class="card-overlay"></div>
            <div class="card-content">
              <h2>Generate Images</h2>
              <p class="card-description">Create stunning visuals from text prompts with our AI</p>
              <div class="arrow-container">
                <svg ref="arrow2" class="arrow" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2">
                  <path d="M5 12h14M12 5l7 7-7 7"/>
                </svg>
              </div>
            </div>
          </router-link>
        </div>

        <div class="attribution">
          By Somendra Saini | 2025 | 0fRedesign.tech
        </div>


      </div>
    </div>
  </template>
  
  <script>
  import { gsap } from 'gsap'
  
  export default {
    name: 'MainPage',
    data() {
      return {
        cardImages: [
          'https://images.unsplash.com/photo-1656593445333-2c3b00db2964',
          'https://images.unsplash.com/photo-1614683361837-963af4039d58'
        ],
        imagesLoaded: false
      }
    },
    mounted() {
      // Preload images
      this.preloadImages().then(() => {
        this.imagesLoaded = true
        this.initAnimations()
      }).catch(error => {
        console.error('Error preloading images:', error)
        this.initAnimations()
      })
    },
    methods: {
      preloadImages() {
        return Promise.all(
          this.cardImages.map(url => {
            return new Promise((resolve, reject) => {
              const img = new Image()
              img.src = url
              img.onload = resolve
              img.onerror = reject
            })
          })
        )
      },
      initAnimations() {
        gsap.from('.title', { 
          duration: 0.8, 
          y: -50, 
          opacity: 0, 
          ease: 'power3.out' 
        })
        gsap.from('.subtitle', { 
          duration: 0.8, 
          y: -30, 
          opacity: 0, 
          ease: 'power3.out', 
          delay: 0.2 
        })
        gsap.from('.description', { 
          duration: 0.8, 
          x: -30, 
          opacity: 0, 
          ease: 'power3.out', 
          delay: 0.4 
        })
        gsap.from('.option-card', { 
          duration: 0.8, 
          y: 50, 
          opacity: 0, 
          stagger: 0.1,
          ease: 'power3.out', 
          delay: 0.6 
        })
      },
      animateCard(index) {
        const arrow = index === 0 ? this.$refs.arrow1 : this.$refs.arrow2
        const bg = index === 0 ? this.$refs.bg1 : this.$refs.bg2
        
        gsap.to(arrow, {
          x: 10,
          duration: 0.3,
          ease: 'power2.out'
        })
        
        gsap.to(bg, {
          scale: 1.1,
          duration: 0.5,
          ease: 'power2.out'
        })
        
        gsap.to(`.option-card:nth-child(${index + 1}) .card-overlay`, {
          opacity: 0.2,
          duration: 0.3
        })
      },
      resetCard(index) {
        const arrow = index === 0 ? this.$refs.arrow1 : this.$refs.arrow2
        const bg = index === 0 ? this.$refs.bg1 : this.$refs.bg2
        
        gsap.to(arrow, {
          x: 0,
          duration: 0.3,
          ease: 'power2.out'
        })
        
        gsap.to(bg, {
          scale: 1,
          duration: 0.5,
          ease: 'power2.out'
        })
        
        gsap.to(`.option-card:nth-child(${index + 1}) .card-overlay`, {
          opacity: 0.5,
          duration: 0.3
        })
      }
    }
  }
  </script>
  
  <style>
  @import url('https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@700&display=swap');
  @import url('https://fonts.googleapis.com/css2?family=Product+Sans:wght@400;500;700&display=swap');
  
  .main-page {
    min-height: 100vh;
    width: 100vw;
    padding: 4rem 2rem;
    display: flex;
    justify-content: center;
    align-items: center;
    background-color: #000;
    color: #fff;
    background-image: radial-gradient(circle at 25% 25%, rgba(66, 133, 244, 0.1) 0%, transparent 50%),
                      radial-gradient(circle at 75% 75%, rgba(234, 67, 53, 0.1) 0%, transparent 50%);
  }
  
  .container {
    max-width: 1200px;
    width: 100%;
    margin: 0 auto;
    padding: 0 2rem;
  }
  
  .title {
    font-size: 4.5rem;
    font-weight: 700;
    margin-bottom: 1rem;
    text-align: left;
    letter-spacing: -0.05em;
    background: linear-gradient(90deg, #4285F4, #34A853, #FBBC05, #EA4335);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    text-shadow: 0 2px 10px rgba(0,0,0,0.3);
    line-height: 1.1;
    font-family: 'Product Sans', sans-serif;
  }
  
  .subtitle {
    font-size: 1.5rem;
    opacity: 0.9;
    margin-bottom: 2rem;
    text-align: left;
    font-weight: 400;
    max-width: 700px;
    font-family: 'Product Sans', sans-serif;
    line-height: 1.4;
  }
  
  .description {
    max-width: 700px;
    margin: 3rem 0;
    padding: 0;
    font-size: 1.2rem;
    line-height: 1.7;
    text-align: left;
    font-family: 'Product Sans', sans-serif;
    opacity: 0.85;
  }
  
  .options-container {
    display: flex;
    justify-content: flex-start;
    gap: 2rem;
    margin-top: 3rem;
    flex-wrap: wrap;
  }
  
  .option-card {
    position: relative;
    width: 380px;
    height: 240px;
    border-radius: 16px;
    overflow: hidden;
    text-decoration: none;
    transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
    cursor: pointer;
    box-shadow: 0 10px 30px -5px rgba(0, 0, 0, 0.3);
  }
  
  .option-card:hover {
    transform: translateY(-8px);
    box-shadow: 0 15px 40px -5px rgba(0, 0, 0, 0.4);
  }
  
  .card-bg {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-size: cover;
    background-position: center;
    transition: transform 0.5s cubic-bezier(0.16, 1, 0.3, 1);
    z-index: 1;
  }
  
  .card-overlay {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(2px);
    z-index: 2;
    transition: opacity 0.3s ease;
  }
  
  .card-content {
    position: relative;
    z-index: 3;
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: flex-end;
    align-items: flex-start;
    padding: 2rem;
    color: white;
    text-align: left;
  }
  
  .card-content h2 {
    font-size: 2rem;
    margin-bottom: 0.5rem;
    font-family: 'Instrument Sans', sans-serif;
    font-weight: 700;
    text-shadow: 0 2px 4px rgba(0,0,0,0.3);
  }
  
  .card-description {
    font-size: 1rem;
    opacity: 0.9;
    margin-bottom: 1.5rem;
    font-family: 'Product Sans', sans-serif;
    max-width: 80%;
    line-height: 1.5;
    text-shadow: 0 1px 2px rgba(0,0,0,0.3);
  }
  
  .arrow-container {
    display: flex;
    justify-content: flex-start;
    width: 100%;
  }
  
  .arrow {
    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  }
  
  @media (max-width: 1024px) {
    .title {
      font-size: 3.5rem;
    }
    
    .subtitle {
      font-size: 1.3rem;
    }
    
    .option-card {
      width: 100%;
      max-width: 100%;
    }
  }
  
  @media (max-width: 768px) {
    .main-page {
      padding: 2rem 1.5rem;
    }
    
    .title {
      font-size: 2.8rem;
    }
    
    .subtitle {
      font-size: 1.2rem;
    }
    
    .description {
      font-size: 1.1rem;
    }
    
    .options-container {
      flex-direction: column;
      gap: 1.5rem;
    }
  }
  
  @media (max-width: 480px) {
    .title {
      font-size: 2.2rem;
    }
    
    .subtitle {
      font-size: 1.1rem;
    }
    
    .description {
      font-size: 1rem;
    }
    
    .card-content h2 {
      font-size: 1.7rem;
    }
    
    .card-description {
      font-size: 0.9rem;
    }
  
    

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