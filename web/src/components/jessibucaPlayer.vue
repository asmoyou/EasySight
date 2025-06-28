<script setup>
import {ref, onMounted, defineProps, watch, onBeforeUnmount, defineEmits} from "vue";
import { ElMessage } from 'element-plus'
import { VideoCamera } from '@element-plus/icons-vue'

// 定义 props 来接收外部传入的 video_url
const props = defineProps({
  video_url: {
    type: String,
    default: ''
  }
})

// 定义事件
const emit = defineEmits(['error', 'loaded'])

let jessibuca = null;
const video_url = ref(props.video_url);
const isLoading = ref(true)
const hasError = ref(false)
const errorMessage = ref('')

onMounted(() =>{
  initPlayer()
  playVideo()
})

onBeforeUnmount(() => {
  closePlayer()
})

function initPlayer(){
  try {
    jessibuca = new window.JessibucaPro(
        Object.assign({
          container: document.getElementById('jesscontainer'),
          decoder: '/js/decoder-pro.js',
          videoBuffer: 0.2,
          isResize: true, // 改为 true 以支持自适应
          text: "新航物联网",
          loadingText: "新航为您加载视频中...",
          useMSE: true,
          useSIMD: true,
          autoWasm: true,
          debug: false,
          showBandwidth: true,
          showPerformance: false,
          timeout: 15, // 减少超时时间
          heartTimeout: 10,
          heartTimeoutReplay: true,
          hotKey: true,
          controlAutoHide: true,
          operateBtns: {
            fullscreen: true,
            screenshot: true,
            play: true,
            audio: true,
            record: true,
            ptz: true,
            quality: true,
            performance: true,
          },
          qualityConfig: ['自动'],
          forceNoOffscreen: true,
          isNotMute: false,
        })
    )
    
    // 添加事件监听
    jessibuca.on('load', () => {
      console.log('视频加载成功')
      isLoading.value = false
      hasError.value = false
      emit('loaded')
    })
    
    jessibuca.on('error', (error) => {
      console.error('播放器错误:', error)
      isLoading.value = false
      hasError.value = true
      errorMessage.value = '视频播放失败'
      emit('error', error)
      ElMessage.error('视频播放失败，请检查网络连接或视频源')
    })
    
    jessibuca.on('timeout', () => {
      console.error('播放器超时')
      isLoading.value = false
      hasError.value = true
      errorMessage.value = '连接超时'
      emit('error', '连接超时')
      ElMessage.error('视频连接超时')
    })
    
  } catch (error) {
    console.error('初始化播放器失败:', error)
    hasError.value = true
    errorMessage.value = '播放器初始化失败'
    emit('error', error)
  }
}

function playVideo(){
  if(video_url.value && jessibuca){
    try {
      console.log("jesibuca play", video_url.value)
      jessibuca.play(video_url.value)
    } catch (error) {
      console.error('播放视频失败:', error)
      hasError.value = true
      errorMessage.value = '播放失败'
      emit('error', error)
    }
  }
}

function closePlayer(){
  try {
    if (jessibuca) {
      console.log("destroy jessibuca")
      jessibuca.destroy()
      jessibuca = null
    }
  } catch (error) {
    console.error('关闭播放器失败:', error)
  }
}

// 重试播放
function retryPlay() {
  hasError.value = false
  isLoading.value = true
  errorMessage.value = ''
  
  // 重新初始化播放器
  closePlayer()
  setTimeout(() => {
    initPlayer()
    playVideo()
  }, 500)
}
</script>

<template>
  <div class="jessibuca-container">
    <div 
      id="jesscontainer" 
      v-show="!hasError"
      class="video-container"
    ></div>
    
    <!-- 错误状态显示 -->
    <div v-if="hasError" class="error-container">
      <div class="error-content">
        <el-icon class="error-icon" size="48"><VideoCamera /></el-icon>
        <p class="error-message">{{ errorMessage }}</p>
        <el-button type="primary" @click="retryPlay">重试</el-button>
      </div>
    </div>
    
    <!-- 加载状态 -->
    <div v-if="isLoading && !hasError" class="loading-container" v-loading="isLoading" element-loading-text="正在加载视频...">
      <div class="loading-content">
        <el-icon class="loading-icon" size="32"><VideoCamera /></el-icon>
        <p>正在加载视频...</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.jessibuca-container {
  width: 100%;
  height: 100%;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #000;
  border-radius: 8px;
  overflow: hidden;
}

.video-container {
  width: 100%;
  height: 100%;
  background-image: url('/images/video-bg.png');
  background-size: contain;
  background-repeat: no-repeat;
  background-position: center;
  background-color: #000;
}

.error-container {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.8);
  color: white;
}

.error-content {
  text-align: center;
  padding: 20px;
}

.error-icon {
  color: #f56c6c;
  margin-bottom: 16px;
}

.error-message {
  margin: 16px 0;
  font-size: 16px;
  color: #fff;
}

.loading-container {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.8);
  color: white;
}

.loading-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.loading-icon {
  color: #409eff;
  margin-bottom: 16px;
  animation: pulse 2s infinite;
}

.loading-content p {
  margin: 0;
  font-size: 14px;
  color: white;
}

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.5; }
  100% { opacity: 1; }
}

/* 确保播放器容器保持合适的宽高比 */
.jessibuca-container {
  aspect-ratio: 16/9; /* 设置16:9的宽高比 */
  min-height: 300px;
  max-height: 500px;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .jessibuca-container {
    aspect-ratio: 4/3;
    min-height: 200px;
  }
}
</style>
