# EasySight

> 通用分布式智能安防平台

## 📖 项目简介

本项目致力于建设一个通用的分布式智能安防平台，提供商业项目所需的所有基础能力。在此基础上，开发者可以专注于业务算法的开发，从而快速实现自己的业务需求，减少重复造轮子的时间，提高开发效率，进一步推动AI技术的落地发展。

## 🏗️ 技术架构

- **前端**: Vue 3 + Element Plus
- **构建工具**: Vite 6.x
- **包管理**: Yarn

- **后端**: Python 3 + fastapi
- **数据库**: postgre + redis
- **对象数据库**: minio

- **部署架构**: docker容器化

## ✨ 功能特性
### 页面设计风格
1. 简洁优雅 (Clean & Elegant)：避免冗余装饰，界面元素清晰。
2. 空间感与深度层次 (Spatial Awareness & Depth)： 通过毛玻璃效果 (Vibrancy)、阴影、视差等模拟物理空间层次，帮助用户理解界面结构。
3. 高度一致性 (Consistency)：遵循统一的设计语言，降低学习成本。
4. 用户友好性 (User-Friendly) & 可访问性 (Accessibility)： 设计核心目标，确保尽可能多的用户能轻松舒适地使用。
5. 自然元素融入 (Nature-Inspired)： 从壁纸到色彩渐变，常借鉴自然界的柔和光影和形态，增加亲和力。
6. 精致细节 (Refined Details)： 设计的标志，体现在流畅的动画、恰到好处的微交互和精准的像素级打磨上。
7. 人文关怀 (Human-Centered) & 愉悦感 (Delightful)： 设计不仅是功能性的，更关注用户的情感体验，力求操作流畅、反馈舒适，带来愉悦感。
8. 高效 (Efficient) & 无干扰 (Unobtrusive)： 界面设计服务于内容和工作，避免喧宾夺主，让用户专注于任务。
9. 现代简约 (Modern & Minimalist) & 温暖亲和 (Warm & Approachable)： 结合了科技感的简洁与人性化的温暖（如圆角、柔和色彩），不显冰冷。

### 色调准则
1. 基础中性色 (Foundation Neutrals)：
    白色/浅灰 (White/Light Gray)： 这是浅色模式 (Light Mode) 的绝对主角。界面背景、窗口、侧边栏等大面积区域通常使用非常纯净、明亮的白色或极浅的灰色 ( #F5F5F7, #F2F2F2, #FFFFFF)，营造干净、开阔、现代的感觉。
    深灰/深空灰 (Dark Gray/Space Gray)： 这是深色模式 (Dark Mode) 的核心。不是纯黑 (#000000)，而是采用不同层级的深灰色 ( #1E1E1E, #2C2C2E, #3A3A3C)，模拟深邃但仍有细节的空间感，减少视觉疲劳，更具沉浸感。苹果称之为"深空灰"色调。
2. 标志性强调色 (Signature Accent Color)：
    动态系统蓝 (Dynamic System Blue)： 最重要、最标志性的强调色。它用于：
    按钮高亮/选中状态 (如对话框的"确定"按钮)
    链接文字 (默认蓝色下划线)
    选中文本的背景色
    菜单栏高亮项
    进度条 (部分样式)
    系统控件焦点状态
    关键特性： 这个蓝色不是固定不变的！它是动态的，会根据当前壁纸的主色调进行微妙的自动调整，使其更和谐地融入整体环境。其基础范围通常在 #007AFF 到 #0A84FF 之间，但实际显示会有变化。这是苹果"适应性设计"理念的体现。
3. 辅助中性色与状态色 (Auxiliary & Status Colors)：
    中灰色 (Medium Gray)： 用于分割线 (Dividers)、边框 (Borders)、非活跃控件、图标背景等 ( #C6C6C8, #D8D8D8)。
    深灰色 (Darker Gray)： 用于深色模式下的文字、图标，或浅色模式下的次要文字 ( #8E8E93, #636366)。
    系统红/绿/黄/橙 (System Status Colors)： 用于明确的状态指示，使用非常克制：
    红 ( #FF453A): 关闭按钮 (窗口左上角)、删除操作、严重错误警告。
    黄 ( #FFD60A): 最小化按钮 (窗口左上角)、一般警告。
    绿 ( #30D158): 全屏按钮 (窗口左上角)、成功状态、可用状态。
    橙 ( #FF9F0A): 偶尔用于需要注意但非错误的状态（比黄色使用更少）。
4. 半透明与模糊效果 (Vibrancy & Blur)：
    虽然不是单一颜色，但毛玻璃效果 (Vibrancy) 是 macOS 配色的关键组成部分。侧边栏、菜单、通知中心等元素使用半透明背景并叠加实时的背景模糊。这使得背景的颜色和光线能"透"过来，动态地影响前景元素的色调，创造出空间感和深度感，同时让界面色彩与用户环境（壁纸）无缝融合。

### 设计功能
- 基础板块
-- 🚧 用户管理：含页面权限与数据权限控制
-- 🚧 支持多语言切换[中文、英文]
- 🚧 摄像头管理
-- 🚧 设备接入：增删改设备，编辑内容包括摄像头编码、名称、视频源地址、媒体代理[下拉选择], 属性信息[自定义属性标签与数值]等。
-- 🚧 视频预览: 多屏播放可以同时查看多路视频的实时视频, 支持1,4,9,16分屏
-- 🚧 电子地图: 可以显示设备点位信息
- 🚧 AI应用中心
-- 🚧 算法市场：上传AI算法，包括算法名称、算法描述、算法版本、算法作者、算法类型、算法文件、算法配置
-- 🚧 AI服务配置：针对已有的摄像头，配置对应点位启用的AI算法，包括生效时间，算法参数，区域绘制，告警配置等
- 🚧 事件告警中心 
-- 🚧告警事件：展示所有的事件告警信息，包括事件类型，事件时间，事件位置，事件描述对应的图片、视频等。
- 🚧 系统配置
-- 🚧版本信息：展示系统版本信息，包括版本号，更新时间等
-- 🚧存储配置：配置数据留存天数。
-- 🚧流媒体管理：增删改查流媒体节点的信息，包含节点名称、节点IP、节点端口、密钥、在线状态等。
-- 🚧消息中心配置：配置消息中的IP地址，端口，以及上报的事件类型等。
- 🚧 智能诊断
-- 诊断任务：对点位视频配置诊断任务，包含亮度检测、蓝屏检查、清晰度检查、抖动检查、冻结检测、偏色检测、遮挡检测、噪声检测、对比度检测、马赛克检测、花屏检测等
-- 诊断告警：缩略图展示告警类型、时间，以及对应的设备点位信息
- 📋 多租户

备注：🚧 开发任务，📋 计划任务

## 🚀 快速开始

### 环境要求
- Node.js >= 16.0.0 
- Yarn >= 1.22.0
- Python >= 3.8
- 推荐安装 Docker & Docker Compose（用于一键启动依赖服务）

---

### 1. 启动基础服务（可选，推荐使用 Docker）

```bash
# 在项目根目录下启动数据库、缓存、对象存储等基础服务
docker-compose up -d
```

---

### 2. 前端项目

#### 安装依赖

```bash
# 进入 web 目录
cd web

# 安装前端依赖
yarn install
```

#### 启动开发服务器

```bash
yarn dev
```

#### 构建生产版本

```bash
yarn build

# 预览构建结果
yarn preview
```

---

### 3. 后端项目

#### 安装依赖

```bash
# 进入 backend 目录
cd backend

# 使用虚拟化环境
## 创建
python -m venv .venv
## 激活
.venv/Scripts\activate

# 安装后端依赖（如 requirements.txt 存在）
pip install -r requirements.txt
```

#### 启动开发服务器

```bash
# 以 FastAPI + Uvicorn 为例
uvicorn main:app --reload
```

> 请根据实际后端入口文件名（如 main.py、app.py）和依赖文件名（如 requirements.txt、pyproject.toml）调整命令。

---

### 4. 生产部署

- 推荐将前后端分别打包为 Docker 镜像，并扩展 docker-compose.yaml，统一容器化部署。
- 可参考基础服务的写法，添加 web 和 backend 服务。

---

## 📁 项目结构


## 生产部署
使用docker镜像打包前后端服务，整体服务以容器化微服务架构部署，支持docker-compose脚本一键启动。

## 🤝 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 📞 联系我们

如有问题或建议，请通过以下方式联系我们：

- 提交 Issue
- 发送邮件
- 加入讨论群

---

⭐ 如果这个项目对你有帮助，请给我们一个星标！
