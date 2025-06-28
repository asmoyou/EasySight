<script setup>
import {ref, defineProps, watch, defineEmits} from "vue";
import jessibucaPlayer from "./jessibucaPlayer.vue";
import { ElMessage } from 'element-plus'

const props = defineProps({
  video_url: {
    type: String,
    default: ''
  }
})

// 定义事件
const emit = defineEmits(['error', 'loaded'])

const video_url = ref(props.video_url);
const hasError = ref(false)

watch(() => props.video_url, (newVal) => {
  video_url.value = newVal;
  hasError.value = false // 重置错误状态
})

// 处理播放器错误
function handlePlayerError(error) {
  console.error('视频播放错误:', error)
  hasError.value = true
  emit('error', error)
}

// 处理播放器加载成功
function handlePlayerLoaded() {
  hasError.value = false
  emit('loaded')
}

const player_type = ref(''); // 视频类型

function checkVideoUrl(){
  // 如果video_url中含有rtsp/则判定为zlm的流，对url进行处理
  if(video_url.value.includes('/rtsp/')) {
    video_url.value = video_url.value.replace('http', 'ws');
    video_url.value = video_url.value.replace('.mp4', '.flv');
    video_url.value = video_url.value.replace('.ts', '.flv');
  }
  // 如果video_url的后缀为.mp4
  if(video_url.value.endsWith('.mp4')) {
    player_type.value = 'raw'
  }else if(video_url.value.endsWith('.flv')) {
    player_type.value = 'jessibuca';
  }else {
    player_type.value = 'jessibuca';
  }
}

onMounted(() => {
  checkVideoUrl();
})

onBeforeUnmount(() => {
  player_type.value = '';
  video_url.value = '';
})
</script>

<template>
  <div class="video-preview">
    <!-- 根据视频类型选择播放器 -->
    <div v-if="video_url.includes('/rtsp/') || video_url.endsWith('.flv')" class="jessibuca-player">
      <jessibuca-player 
        :video_url="video_url" 
        @error="handlePlayerError"
        @loaded="handlePlayerLoaded"
      />
    </div>
    <div v-else class="native-player">
      <video 
        :src="video_url" 
        controls 
        style="width: 100%; height: 100%; object-fit: contain;"
        @error="handlePlayerError"
        @loadeddata="handlePlayerLoaded"
      ></video>
    </div>
  </div>
</template>

<style scoped>
.video-preview{
  width: 100%;
  height: 100%;
  min-height: 20vh;
  background: lightgray;
  position: relative;
}
.video-player{
  width: 100%;
  height: 100%;
  object-fit: fill;
  position: absolute;
}
</style>
