<template>
  <div class="ai-unified-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">
          <el-icon><Box /></el-icon>
          AI算法与模型管理
        </h1>
        <p class="page-description">统一管理AI算法包和模型文件，支持插件化上传和版本控制</p>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="showUploadDialog = true">
          <el-icon><Upload /></el-icon>
          上传算法包
        </el-button>
        <el-button type="success" @click="openAddModelDialog">
          <el-icon><Plus /></el-icon>
          添加模型
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <el-row :gutter="16">
        <el-col :span="4">
          <div class="stat-card" :class="{ 'zero-value': stats.total_algorithms === 0 }">
            <div class="stat-icon algorithms">
              <el-icon><Cpu /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">
                {{ stats.total_algorithms }}
                <span v-if="stats.total_algorithms === 0" class="zero-hint">暂无数据</span>
              </div>
              <div class="stat-label">算法总数</div>
            </div>
          </div>
        </el-col>
        <el-col :span="4">
          <div class="stat-card" :class="{ 'zero-value': stats.total_models === 0 }">
            <div class="stat-icon models">
              <el-icon><Box /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">
                {{ stats.total_models }}
                <span v-if="stats.total_models === 0" class="zero-hint">暂无数据</span>
              </div>
              <div class="stat-label">模型总数</div>
            </div>
          </div>
        </el-col>

        <el-col :span="4">
          <div class="stat-card" :class="{ 'zero-value': stats.total_size === 0 }">
            <div class="stat-icon storage">
              <el-icon><FolderOpened /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">
                {{ stats.total_size === 0 ? '0 B' : formatFileSize(stats.total_size) }}
                <span v-if="stats.total_size === 0" class="zero-hint">暂无占用</span>
              </div>
              <div class="stat-label">存储占用</div>
            </div>
          </div>
        </el-col>
        <el-col :span="4">
          <div class="stat-card" :class="{ 'zero-value': stats.avg_accuracy === 0 }">
            <div class="stat-icon performance">
              <el-icon><TrendCharts /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">
                {{ stats.avg_accuracy === 0 ? '0.0%' : (stats.avg_accuracy * 100).toFixed(1) + '%' }}
                <span v-if="stats.avg_accuracy === 0" class="zero-hint">暂无数据</span>
              </div>
              <div class="stat-label">平均准确率</div>
            </div>
          </div>
        </el-col>

      </el-row>
    </div>

    <!-- 搜索和筛选 -->
    <div class="search-filters">
      <el-row :gutter="16">
        <el-col :span="6">
          <el-input
            v-model="searchQuery"
            placeholder="搜索算法或模型名称"
            clearable
            @input="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
        <el-col :span="3">
          <el-select
            v-model="filterType"
            placeholder="算法类型"
            clearable
            @change="handleFilter"
          >
            <el-option label="目标检测" value="object_detection" />
            <el-option label="人脸识别" value="face_recognition" />
            <el-option label="行为分析" value="behavior_analysis" />
            <el-option label="车辆检测" value="vehicle_detection" />
            <el-option label="入侵检测" value="intrusion_detection" />
            <el-option label="火焰检测" value="fire_detection" />
            <el-option label="烟雾检测" value="smoke_detection" />
            <el-option label="人群分析" value="crowd_analysis" />
            <el-option label="异常行为" value="abnormal_behavior" />
            <el-option label="自定义" value="custom" />
          </el-select>
        </el-col>
        <el-col :span="3">
          <el-select
            v-model="filterStatus"
            placeholder="状态"
            clearable
            @change="handleFilter"
          >
            <el-option label="活跃" :value="true" />
            <el-option label="非活跃" :value="false" />
          </el-select>
        </el-col>
        <el-col :span="3">
          <el-select
            v-model="viewMode"
            placeholder="视图模式"
            @change="handleViewModeChange"
          >
            <el-option label="算法视图" value="algorithms" />
            <el-option label="模型视图" value="models" />
          </el-select>
        </el-col>
        <el-col :span="9">
          <div class="filter-actions">
            <el-button @click="resetFilters">重置</el-button>
            <el-button type="primary" @click="loadData">搜索</el-button>
            <el-button type="warning" @click="batchOperation" :disabled="selectedItems.length === 0">
              批量操作
            </el-button>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 算法视图 -->
    <div v-if="viewMode === 'algorithms'" class="algorithms-view">
      <!-- 空状态 -->
      <div v-if="!loading && algorithms.length === 0" class="empty-state">
        <div class="empty-icon">
          <el-icon size="64"><Cpu /></el-icon>
        </div>
        <div class="empty-title">暂无算法数据</div>
        <div class="empty-description">您还没有上传任何算法包，点击下方按钮开始上传</div>
        <div class="empty-actions">
          <el-button type="primary" @click="showUploadDialog = true">
            <el-icon><Upload /></el-icon>
            上传算法包
          </el-button>
        </div>
      </div>
      
      <div v-else class="algorithms-grid">
        <el-row :gutter="24">
          <el-col :span="8" v-for="algorithm in algorithms" :key="algorithm.id">
            <div class="algorithm-card" @click="selectAlgorithm(algorithm)" :class="{ selected: selectedAlgorithm?.id === algorithm.id }">
              <div class="card-header">
                <div class="algorithm-info">
                  <h3 class="algorithm-name">{{ algorithm.name }}</h3>
                  <div class="algorithm-meta">
                    <el-tag size="small" :type="getAlgorithmTypeColor(algorithm.algorithm_type)">
                      {{ getAlgorithmTypeLabel(algorithm.algorithm_type) }}
                    </el-tag>
                    <span class="version">v{{ algorithm.version }}</span>
                  </div>
                </div>
                <div class="card-actions">
                  <el-dropdown @command="handleAlgorithmAction">
                    <el-button type="text" size="small">
                      <el-icon><MoreFilled /></el-icon>
                    </el-button>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item :command="{ action: 'view', data: algorithm }">查看详情</el-dropdown-item>
                        <el-dropdown-item :command="{ action: 'edit', data: algorithm }">编辑</el-dropdown-item>
                        <el-dropdown-item :command="{ action: 'copy', data: algorithm }">复制</el-dropdown-item>
                        <el-dropdown-item :command="{ action: 'delete', data: algorithm }" divided class="danger-item">删除</el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                </div>
              </div>
              
              <div class="card-content">
                <p class="algorithm-description">{{ algorithm.description || '暂无描述' }}</p>
                
                <div class="algorithm-stats">
                  <div class="stat-item">
                    <span class="stat-label">模型数量</span>
                    <span class="stat-value">{{ algorithm.models?.length || 0 }}</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-label">服务数量</span>
                    <span class="stat-value">{{ algorithm.services?.length || 0 }}</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-label">使用次数</span>
                    <span class="stat-value">{{ algorithm.usage_count || 0 }}</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-label">创建时间</span>
                    <span class="stat-value">{{ formatDate(algorithm.created_at) }}</span>
                  </div>
                </div>
                
                <div class="algorithm-tags" v-if="algorithm.tags && algorithm.tags.length">
                  <el-tag v-for="tag in algorithm.tags" :key="tag" size="small" class="tag-item">
                    {{ tag }}
                  </el-tag>
                </div>
              </div>
              
              <div class="card-footer">
                <div class="status-indicator">
                  <el-switch
                    v-model="algorithm.is_active"
                    @change="toggleAlgorithmStatus(algorithm)"
                    :disabled="loading"
                  />
                  <span class="status-text">{{ algorithm.is_active ? '已启用' : '已停用' }}</span>
                </div>
                
                <div class="performance-metrics" v-if="algorithm.performance_metrics">
                  <div class="metric-item" v-if="algorithm.performance_metrics.accuracy">
                    <el-icon><TrendCharts /></el-icon>
                    <span>{{ (algorithm.performance_metrics.accuracy * 100).toFixed(1) }}%</span>
                  </div>
                </div>
              </div>
            </div>
          </el-col>
        </el-row>
      </div>
      
      <!-- 算法详情面板 -->
      <div v-if="selectedAlgorithm" class="detail-panel">
        <div class="panel-header">
          <h3>{{ selectedAlgorithm.name }} - 关联模型</h3>
          <el-button type="primary" size="small" @click="addModelToAlgorithm">
            <el-icon><Plus /></el-icon>
            添加模型
          </el-button>
        </div>
        
        <div class="models-list">
          <el-table :data="selectedAlgorithm.models" stripe>
            <el-table-column prop="name" label="模型名称" />
            <el-table-column prop="version" label="版本" width="100" />
            <el-table-column prop="model_type" label="类型" width="120">
              <template #default="{ row }">
                <el-tag size="small" :type="getModelTypeColor(row.model_type)">
                  {{ getModelTypeLabel(row.model_type) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="file_size" label="大小" width="100">
              <template #default="{ row }">
                {{ formatFileSize(row.file_size) }}
              </template>
            </el-table-column>
            <el-table-column label="状态" width="80">
              <template #default="{ row }">
                <el-switch v-model="row.is_active" @change="toggleModelStatus(row)" />
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150">
              <template #default="{ row }">
                <el-button type="primary" size="small" @click="viewModel(row)">查看</el-button>
                <el-button type="warning" size="small" @click="editModel(row)">编辑</el-button>
                <el-button type="danger" size="small" @click="deleteModel(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </div>

    <!-- 模型视图 -->
    <div v-if="viewMode === 'models'" class="models-view">
      <!-- 空状态 -->
      <div v-if="!loading && models.length === 0" class="empty-state">
        <div class="empty-icon">
          <el-icon size="64"><Box /></el-icon>
        </div>
        <div class="empty-title">暂无模型数据</div>
        <div class="empty-description">您还没有上传任何模型文件，请先上传算法包或单独添加模型</div>
        <div class="empty-actions">
          <el-button type="primary" @click="openAddModelDialog">
            <el-icon><Plus /></el-icon>
            添加模型
          </el-button>
          <el-button @click="showUploadDialog = true">
            <el-icon><Upload /></el-icon>
            上传算法包
          </el-button>
        </div>
      </div>
      
      <el-table v-else :data="models" v-loading="loading" stripe @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="55" />
        <el-table-column prop="name" label="模型名称" min-width="200">
          <template #default="{ row }">
            <div class="model-info">
              <div class="model-name">
                <strong>{{ row.name }}</strong>
                <el-tag size="small" :type="getModelTypeColor(row.model_type)">
                  {{ getModelTypeLabel(row.model_type) }}
                </el-tag>
              </div>
              <div class="model-meta">
                <span class="version">v{{ row.version }}</span>
                <span class="file-size">{{ formatFileSize(row.file_size) }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="algorithm" label="关联算法" min-width="150">
          <template #default="{ row }">
            <div class="algorithm-info" v-if="row.algorithm_name">
              <div class="algorithm-name">{{ row.algorithm_name }}</div>
              <div class="algorithm-type">{{ getAlgorithmTypeLabel(row.algorithm_type || 'custom') }}</div>
            </div>
            <span v-else class="no-algorithm">未关联</span>
          </template>
        </el-table-column>
        <el-table-column label="性能指标" min-width="200">
          <template #default="{ row }">
            <div class="performance-metrics" v-if="row.performance_metrics && Object.keys(row.performance_metrics).length">
              <div class="metric-item" v-if="row.performance_metrics.accuracy">
                <span class="metric-label">准确率</span>
                <span class="metric-value">{{ row.performance_metrics.accuracy.toFixed(1) }}%</span>
              </div>
              <div class="metric-item" v-if="row.performance_metrics.validation_accuracy">
                <span class="metric-label">验证准确率</span>
                <span class="metric-value">{{ row.performance_metrics.validation_accuracy.toFixed(1) }}%</span>
              </div>
              <div class="metric-item" v-if="row.performance_metrics.inference_time">
                <span class="metric-label">推理时间</span>
                <span class="metric-value">{{ row.performance_metrics.inference_time }}ms</span>
              </div>

            </div>
            <span v-else class="no-metrics">暂无数据</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-switch v-model="row.is_active" @change="toggleModelStatus(row)" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button type="primary" size="small" @click="viewModel(row)">查看</el-button>
              <el-button type="warning" size="small" @click="editModel(row)">编辑</el-button>
              <el-button type="danger" size="small" @click="deleteModel(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>



    <!-- 分页 -->
    <div class="pagination-container">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>

    <!-- 算法包上传对话框 -->
    <el-dialog
      v-model="showUploadDialog"
      title="上传算法包"
      width="800px"
      :close-on-click-modal="false"
    >
      <div class="upload-container">
        <el-steps :active="uploadStep" align-center>
          <el-step title="选择文件" description="上传算法包文件" />
          <el-step title="解析配置" description="解析算法配置信息" />
          <el-step title="确认信息" description="确认算法信息" />
          <el-step title="完成安装" description="安装算法包" />
        </el-steps>
        
        <!-- 步骤1: 文件上传 -->
        <div v-if="uploadStep === 0" class="upload-step">
          <!-- 示例算法包展示 -->
          <div class="example-packages">
            <h4>示例算法包</h4>
            <p class="example-description">参考以下示例算法包的结构和配置，快速开发您的算法插件</p>
            
            <div class="example-list">
              <div class="example-item">
                <div class="example-header">
                  <div class="example-info">
                    <h5>人脸检测算法包</h5>
                    <div class="example-meta">
                      <el-tag size="small" type="primary">face_recognition</el-tag>
                      <span class="version">v1.0.0</span>
                    </div>
                  </div>
                  <div class="example-actions">
                    <el-button size="small" @click="downloadExamplePackage">下载示例</el-button>
                    <el-button size="small" type="primary" @click="showExampleDetails">查看详情</el-button>
                  </div>
                </div>
                <p class="example-desc">基于深度学习的人脸检测算法，支持实时检测和识别，包含完整的配置文件和说明文档</p>
                <div class="example-features">
                  <el-tag size="small" effect="plain">实时检测</el-tag>
                  <el-tag size="small" effect="plain">关键点定位</el-tag>
                  <el-tag size="small" effect="plain">置信度评估</el-tag>
                  <el-tag size="small" effect="plain">可配置参数</el-tag>
                </div>
              </div>
            </div>
          </div>
          
          <el-divider>或上传您的算法包</el-divider>
          
          <el-upload
            ref="uploadRef"
            class="upload-dragger"
            drag
            :auto-upload="false"
            :on-change="handleFileChange"
            :before-upload="beforeUpload"
            accept=".zip,.tar.gz,.tar"
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">
              将算法包文件拖到此处，或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                支持 .zip, .tar.gz, .tar 格式的算法包文件，大小不超过 500MB
              </div>
            </template>
          </el-upload>
          
          <div v-if="uploadFile" class="file-info">
            <h4>选中的文件:</h4>
            <div class="file-item">
              <el-icon><Document /></el-icon>
              <span class="file-name">{{ uploadFile.name }}</span>
              <span class="file-size">{{ formatFileSize(uploadFile.size) }}</span>
            </div>
          </div>
        </div>
        
        <!-- 步骤2: 解析配置 -->
        <div v-if="uploadStep === 1" class="parse-step">
          <div class="parse-progress">
            <el-progress :percentage="parseProgress" :status="parseStatus" />
            <p class="parse-text">{{ parseText }}</p>
          </div>
        </div>
        
        <!-- 步骤3: 确认信息 -->
        <div v-if="uploadStep === 2" class="confirm-step">
          <el-form :model="algorithmInfo" label-width="120px">
            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="算法名称">
                  <el-input v-model="algorithmInfo.name" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="版本">
                  <el-input v-model="algorithmInfo.version" />
                </el-form-item>
              </el-col>
            </el-row>
            
            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="算法类型">
                  <el-select v-model="algorithmInfo.algorithm_type" placeholder="选择算法类型">
                    <el-option label="目标检测" value="object_detection" />
                    <el-option label="人脸识别" value="face_recognition" />
                    <el-option label="行为分析" value="behavior_analysis" />
                    <el-option label="车辆检测" value="vehicle_detection" />
                    <el-option label="入侵检测" value="intrusion_detection" />
                    <el-option label="火焰检测" value="fire_detection" />
                    <el-option label="烟雾检测" value="smoke_detection" />
                    <el-option label="人群分析" value="crowd_analysis" />
                    <el-option label="异常行为" value="abnormal_behavior" />
                    <el-option label="自定义" value="custom" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="状态">
                  <el-select v-model="algorithmInfo.status">
                    <el-option label="开发中" value="development" />
                    <el-option label="测试中" value="testing" />
                    <el-option label="生产就绪" value="production" />
                    <el-option label="已弃用" value="deprecated" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
            
            <el-form-item label="描述">
              <el-input v-model="algorithmInfo.description" type="textarea" :rows="3" />
            </el-form-item>
            
            <el-form-item label="标签">
              <el-select v-model="algorithmInfo.tags" multiple filterable allow-create placeholder="添加标签">
                <el-option v-for="tag in commonTags" :key="tag" :label="tag" :value="tag" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="支持平台">
              <el-checkbox-group v-model="algorithmInfo.supported_platforms">
                <el-checkbox label="linux">Linux</el-checkbox>
                <el-checkbox label="windows">Windows</el-checkbox>
                <el-checkbox label="macos">macOS</el-checkbox>
                <el-checkbox label="docker">Docker</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
          </el-form>
          
          <div class="package-info">
            <h4>包信息:</h4>
            <el-descriptions :column="2" border>
              <el-descriptions-item label="包大小">{{ formatFileSize(packageInfo.size) }}</el-descriptions-item>
              <el-descriptions-item label="文件数量">{{ packageInfo.file_count }}</el-descriptions-item>
              <el-descriptions-item label="依赖数量">{{ packageInfo.dependencies?.length || 0 }}</el-descriptions-item>
              <el-descriptions-item label="模型数量">{{ packageInfo.models?.length || 0 }}</el-descriptions-item>
            </el-descriptions>
          </div>
        </div>
        
        <!-- 步骤4: 安装进度 -->
        <div v-if="uploadStep === 3" class="install-step">
          <div class="install-progress">
            <el-progress :percentage="installProgress" :status="installStatus" />
            <p class="install-text">{{ installText }}</p>
          </div>
          
          <div v-if="installLogs.length" class="install-logs">
            <h4>安装日志:</h4>
            <div class="log-container">
              <div v-for="(log, index) in installLogs" :key="index" class="log-item" :class="log.level">
                <span class="log-time">{{ log.time }}</span>
                <span class="log-message">{{ log.message }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showUploadDialog = false" :disabled="uploading">取消</el-button>
          <el-button v-if="uploadStep > 0" @click="prevStep" :disabled="uploading">上一步</el-button>
          <el-button v-if="uploadStep < 3" type="primary" @click="nextStep" :disabled="!canNextStep" :loading="uploading">
            下一步
          </el-button>
          <el-button v-if="uploadStep === 3" type="success" @click="finishInstall" :disabled="installStatus !== 'success'">
            完成
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 模型添加/编辑对话框 -->
    <el-dialog
      v-model="showModelDialog"
      :title="editingModel ? '编辑模型' : '添加模型'"
      width="700px"
      :close-on-click-modal="false"
    >
      <el-form ref="modelFormRef" :model="modelForm" :rules="modelRules" label-width="120px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="模型名称" prop="name">
              <el-input v-model="modelForm.name" placeholder="请输入模型名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="模型版本" prop="version">
              <el-input v-model="modelForm.version" placeholder="如: 1.0.0" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="模型类型" prop="model_type">
              <el-select v-model="modelForm.model_type" placeholder="选择模型类型">
                <el-option label="PyTorch" value="pytorch" />
                <el-option label="TensorFlow" value="tensorflow" />
                <el-option label="ONNX" value="onnx" />
                <el-option label="OpenVINO" value="openvino" />
                <el-option label="TensorRT" value="tensorrt" />
                <el-option label="其他" value="other" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="关联算法" prop="algorithm_id">
              <el-select v-model="modelForm.algorithm_id" placeholder="选择算法" clearable>
                <el-option
                  v-for="algorithm in algorithms"
                  :key="algorithm.id"
                  :label="algorithm.name"
                  :value="algorithm.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="模型描述">
          <el-input v-model="modelForm.description" type="textarea" :rows="3" placeholder="请输入模型描述" />
        </el-form-item>
        
        <el-form-item label="模型文件" prop="file_path">
          <el-upload
            ref="modelUploadRef"
            class="model-upload"
            :auto-upload="false"
            :on-change="handleModelFileChange"
            :before-upload="beforeModelUpload"
            accept=".pth,.pt,.onnx,.pb,.tflite,.bin,.xml"
          >
            <el-button type="primary">
              <el-icon><Upload /></el-icon>
              选择模型文件
            </el-button>
            <template #tip>
              <div class="el-upload__tip">
                支持 PyTorch (.pth, .pt), ONNX (.onnx), TensorFlow (.pb), TensorFlow Lite (.tflite), OpenVINO (.bin, .xml) 等格式
              </div>
            </template>
          </el-upload>
          
          <div v-if="modelFile" class="file-info">
            <div class="file-item">
              <el-icon><Document /></el-icon>
              <span class="file-name">{{ modelFile.name }}</span>
              <span class="file-size">{{ formatFileSize(modelFile.size) }}</span>
            </div>
          </div>
        </el-form-item>
        
        <el-form-item label="性能指标">
          <el-row :gutter="16">
            <el-col :span="12">
              <el-input
                v-model.number="modelForm.performance_metrics.accuracy"
                placeholder="95"
                type="number"
                step="0.1"
                min="0"
                max="100"
              >
                <template #prepend>训练准确率</template>
                <template #append>%</template>
              </el-input>
            </el-col>
            <el-col :span="12">
              <el-input
                v-model.number="modelForm.performance_metrics.validation_accuracy"
                placeholder="92"
                type="number"
                step="0.1"
                min="0"
                max="100"
              >
                <template #prepend>验证准确率</template>
                <template #append>%</template>
              </el-input>
            </el-col>
          </el-row>
          <el-row :gutter="16" style="margin-top: 16px;">
            <el-col :span="24">
              <el-input
                v-model.number="modelForm.performance_metrics.inference_time"
                placeholder="50"
                type="number"
                min="0"
                style="max-width: 400px;"
              >
                <template #prepend>推理时间</template>
                <template #append>ms</template>
              </el-input>
            </el-col>
          </el-row>
        </el-form-item>
        
        <el-form-item label="标签">
          <el-select v-model="modelForm.tags" multiple filterable allow-create placeholder="添加标签">
            <el-option v-for="tag in commonTags" :key="tag" :label="tag" :value="tag" />
          </el-select>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showModelDialog = false">取消</el-button>
          <el-button type="primary" @click="saveModel" :loading="saving">
            {{ editingModel ? '更新' : '创建' }}
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 示例算法包详情对话框 -->
    <el-dialog
      v-model="showExampleDialog"
      title="示例算法包详情"
      width="900px"
      :close-on-click-modal="false"
    >
      <div class="example-details">
        <el-tabs v-model="activeTab">
          <el-tab-pane label="基本信息" name="info">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="算法名称">人脸检测算法</el-descriptions-item>
              <el-descriptions-item label="版本">v1.0.0</el-descriptions-item>
              <el-descriptions-item label="类型">face_recognition</el-descriptions-item>
              <el-descriptions-item label="作者">EasySight Team</el-descriptions-item>
              <el-descriptions-item label="许可证">MIT</el-descriptions-item>
              <el-descriptions-item label="支持平台">Linux, Windows, macOS</el-descriptions-item>
            </el-descriptions>
            
            <h4 style="margin-top: 20px;">功能特性</h4>
            <ul>
              <li>实时人脸检测</li>
              <li>人脸边界框定位</li>
              <li>人脸关键点检测</li>
              <li>置信度评估</li>
              <li>可配置参数</li>
            </ul>
            
            <h4>性能指标</h4>
            <el-descriptions :column="2" border>
              <el-descriptions-item label="准确率">95%</el-descriptions-item>
              <el-descriptions-item label="推理时间">~50ms (CPU)</el-descriptions-item>
              <el-descriptions-item label="内存占用">~512MB</el-descriptions-item>
              <el-descriptions-item label="GPU要求">否</el-descriptions-item>
            </el-descriptions>
          </el-tab-pane>
          
          <el-tab-pane label="配置参数" name="config">
            <el-table :data="exampleConfigParams" border>
              <el-table-column prop="name" label="参数名" width="180" />
              <el-table-column prop="type" label="类型" width="100" />
              <el-table-column prop="default" label="默认值" width="120" />
              <el-table-column prop="description" label="描述" />
            </el-table>
          </el-tab-pane>
          
          <el-tab-pane label="文件结构" name="structure">
            <div class="file-structure">
              <pre>{{ exampleFileStructure }}</pre>
            </div>
          </el-tab-pane>
          
          <el-tab-pane label="使用说明" name="usage">
            <div class="usage-guide">
              <h4>安装步骤</h4>
              <ol>
                <li>下载示例算法包ZIP文件</li>
                <li>在EasySight管理界面中选择"AI统一管理"</li>
                <li>点击"上传算法包"按钮</li>
                <li>选择下载的ZIP文件</li>
                <li>系统将自动解析并安装算法包</li>
              </ol>
              
              <h4>开发指南</h4>
              <p>基于此示例开发您自己的算法包时，请确保包含以下必需文件：</p>
              <ul>
                <li><code>algorithm.json</code> - 算法配置文件</li>
                <li><code>main.py</code> - 算法主程序</li>
                <li><code>README.md</code> - 说明文档</li>
                <li><code>requirements.txt</code> - 依赖列表</li>
              </ul>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showExampleDialog = false">关闭</el-button>
          <el-button type="primary" @click="downloadExamplePackage">下载示例包</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 模型详情对话框 -->
    <el-dialog
      v-model="showModelDetailDialog"
      title="模型详情"
      width="800px"
      :close-on-click-modal="false"
    >
      <div v-if="viewingModel" class="model-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="模型名称">
            <span class="model-name">{{ viewingModel.name }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="模型版本">
            <el-tag type="info">v{{ viewingModel.version }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="模型类型">
            <el-tag :type="getModelTypeColor(viewingModel.model_type)">
              {{ getModelTypeLabel(viewingModel.model_type) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="viewingModel.is_active ? 'success' : 'danger'">
              {{ viewingModel.is_active ? '激活' : '停用' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="文件路径">
            <span class="file-path">{{ viewingModel.file_path || '未指定' }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="文件大小">
            <span>{{ formatFileSize(viewingModel.file_size || 0) }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">
            <span>{{ formatDate(viewingModel.created_at) }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="更新时间">
            <span>{{ formatDate(viewingModel.updated_at) }}</span>
          </el-descriptions-item>
        </el-descriptions>

        <div class="model-description" v-if="viewingModel.description">
          <h4>模型描述</h4>
          <p>{{ viewingModel.description }}</p>
        </div>

        <div class="performance-metrics" v-if="viewingModel.performance_metrics && Object.keys(viewingModel.performance_metrics).length">
          <h4>性能指标</h4>
          <el-row :gutter="16">
            <el-col :span="8" v-if="viewingModel.performance_metrics.accuracy">
              <div class="metric-card">
                <div class="metric-label">训练准确率</div>
                <div class="metric-value">{{ viewingModel.performance_metrics.accuracy.toFixed(2) }}%</div>
              </div>
            </el-col>
            <el-col :span="8" v-if="viewingModel.performance_metrics.validation_accuracy">
              <div class="metric-card">
                <div class="metric-label">验证准确率</div>
                <div class="metric-value">{{ viewingModel.performance_metrics.validation_accuracy.toFixed(2) }}%</div>
              </div>
            </el-col>
            <el-col :span="8" v-if="viewingModel.performance_metrics.inference_time">
              <div class="metric-card">
                <div class="metric-label">推理时间</div>
                <div class="metric-value">{{ viewingModel.performance_metrics.inference_time }}ms</div>
              </div>
            </el-col>

          </el-row>
        </div>

        <div class="model-formats" v-if="(viewingModel.input_format && Object.keys(viewingModel.input_format).length) || (viewingModel.output_format && Object.keys(viewingModel.output_format).length)">
          <h4>输入输出格式</h4>
          <el-row :gutter="16">
            <el-col :span="12" v-if="viewingModel.input_format && Object.keys(viewingModel.input_format).length">
              <div class="format-card">
                <h5>输入格式</h5>
                <pre class="format-json">{{ JSON.stringify(viewingModel.input_format, null, 2) }}</pre>
              </div>
            </el-col>
            <el-col :span="12" v-if="viewingModel.output_format && Object.keys(viewingModel.output_format).length">
              <div class="format-card">
                <h5>输出格式</h5>
                <pre class="format-json">{{ JSON.stringify(viewingModel.output_format, null, 2) }}</pre>
              </div>
            </el-col>
          </el-row>
        </div>

        <div class="model-tags" v-if="viewingModel.tags && viewingModel.tags.length">
          <h4>标签</h4>
          <div class="tags-container">
            <el-tag v-for="tag in viewingModel.tags" :key="tag" class="tag-item">
              {{ tag }}
            </el-tag>
          </div>
        </div>
      </div>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showModelDetailDialog = false">关闭</el-button>
          <el-button type="warning" @click="editModel(viewingModel!); showModelDetailDialog = false">编辑</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules, UploadFile } from 'element-plus'
import {
  Box,
  Plus,
  Search,
  Check,
  FolderOpened,
  TrendCharts,
  Upload,
  UploadFilled,
  Document,
  Cpu,
  DataAnalysis,
  MoreFilled
} from '@element-plus/icons-vue'
import { aiApi } from '@/api/ai'
import type {
  AIAlgorithm,
  AIModel,
  AIAlgorithmCreate,
  AIModelCreate,
  AIModelUpdate
} from '@/types/ai'

// 响应式数据
const loading = ref(false)
const saving = ref(false)
const uploading = ref(false)
const algorithms = ref<AIAlgorithm[]>([])
const models = ref<AIModel[]>([])

const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const selectedItems = ref<any[]>([])
const selectedAlgorithm = ref<AIAlgorithm | null>(null)

// 统计数据
const stats = ref({
  total_algorithms: 0,
  total_models: 0,
  total_size: 0,
  avg_accuracy: 0
})

// 搜索和筛选
const searchQuery = ref('')
const filterType = ref('')
const filterStatus = ref<boolean | undefined>(undefined)
const viewMode = ref('algorithms')

// 对话框
const showUploadDialog = ref(false)
const showModelDialog = ref(false)
const showModelDetailDialog = ref(false)
const showExampleDialog = ref(false)
const editingModel = ref<AIModel | null>(null)
const viewingModel = ref<AIModel | null>(null)
const modelFormRef = ref<FormInstance>()
const activeTab = ref('info')

// 上传相关
const uploadStep = ref(0)
const uploadFile = ref<File | null>(null)
const modelFile = ref<File | null>(null)
const parseProgress = ref(0)
const parseStatus = ref<'success' | 'exception' | 'warning' | ''>('')
const parseText = ref('')
const installProgress = ref(0)
const installStatus = ref<'success' | 'exception' | 'warning' | ''>('')
const installText = ref('')
const installLogs = ref<Array<{ time: string; level: string; message: string }>>([])

// 算法信息
const algorithmInfo = reactive<AIAlgorithmCreate>({
  name: '',
  algorithm_type: 'custom',
  version: '',
  description: '',
  file_path: '',
  config_schema: {},
  supported_platforms: [],
  resource_requirements: {},
  performance_metrics: {},
  tags: [],
  status: 'development',
  is_active: true
})

// 包信息
const packageInfo = ref({
  size: 0,
  file_count: 0,
  dependencies: [],
  models: []
})

// 模型表单
const modelForm = reactive<AIModelCreate>({
  name: '',
  model_type: 'pytorch',
  version: '',
  description: '',
  file_path: '',
  file_size: 0,
  algorithm_id: undefined,
  input_format: {},
  output_format: {},
  performance_metrics: {
    accuracy: undefined,
    validation_accuracy: undefined,
    inference_time: undefined
  },
  tags: [],
  is_active: true
})

// 表单验证规则
const modelRules: FormRules = {
  name: [
    { required: true, message: '请输入模型名称', trigger: 'blur' },
    { min: 2, max: 100, message: '长度在 2 到 100 个字符', trigger: 'blur' }
  ],
  model_type: [
    { required: true, message: '请选择模型类型', trigger: 'change' }
  ],
  version: [
    { required: true, message: '请输入模型版本', trigger: 'blur' },
    { pattern: /^\d+\.\d+\.\d+$/, message: '版本格式应为 x.y.z', trigger: 'blur' }
  ],
  algorithm_id: [
    { required: true, message: '请选择关联算法', trigger: 'change' }
  ],
  file_path: [
    { required: true, message: '请选择模型文件', trigger: 'blur' }
  ]
}

// 常用标签
const commonTags = [
  '高精度', '轻量级', '实时推理', '边缘计算', 'GPU优化',
  '量化模型', '预训练', '微调', '多尺度', '鲁棒性'
]

// 示例算法包数据
const exampleConfigParams = ref([
  {
    name: 'confidence_threshold',
    type: 'number',
    default: '0.5',
    description: '置信度阈值，低于此值的检测结果将被过滤'
  },
  {
    name: 'max_faces',
    type: 'integer',
    default: '10',
    description: '单张图像中最大检测人脸数量'
  },
  {
    name: 'input_size',
    type: 'array',
    default: '[640, 480]',
    description: '输入图像的处理尺寸 [width, height]'
  }
])

const exampleFileStructure = ref(`face-detection-algorithm/
├── algorithm.json          # 算法配置文件
├── main.py                # 算法主程序
├── README.md              # 说明文档
├── requirements.txt       # 依赖列表
├── models/
│   ├── face_detection.pth # 人脸检测模型
│   └── face_recognition.pth # 人脸识别模型
├── utils/
│   ├── __init__.py
│   ├── detector.py        # 检测器实现
│   └── preprocessor.py    # 图像预处理
└── tests/
    ├── test_algorithm.py  # 单元测试
    └── sample_images/     # 测试图像`)

// 计算属性
const canNextStep = computed(() => {
  switch (uploadStep.value) {
    case 0:
      return !!uploadFile.value
    case 1:
      return parseStatus.value === 'success'
    case 2:
      return algorithmInfo.name && algorithmInfo.version && algorithmInfo.algorithm_type
    default:
      return false
  }
})

// 方法
const loadData = async () => {
  switch (viewMode.value) {
    case 'algorithms':
      await loadAlgorithms()
      break
    case 'models':
      await loadModels()
      break
  }
}

const loadAlgorithms = async () => {
  try {
    loading.value = true
    const params = {
      page: currentPage.value,
      page_size: pageSize.value,
      search: searchQuery.value || undefined,
      algorithm_type: filterType.value || undefined,
      is_active: filterStatus.value
    }
    
    const response = await aiApi.getAlgorithms(params)
    algorithms.value = response.data || []
    total.value = response.total || 0
  } catch (error) {
    console.error('加载算法列表失败:', error)
    ElMessage.error('加载算法列表失败')
  } finally {
    loading.value = false
  }
}

const loadModels = async () => {
  try {
    loading.value = true
    const params = {
      page: currentPage.value,
      page_size: pageSize.value,
      search: searchQuery.value || undefined,
      model_type: filterType.value || undefined,
      is_active: filterStatus.value
    }
    
    const response = await aiApi.getModels(params)
    models.value = response.data || []
    total.value = response.total || 0
  } catch (error) {
    console.error('加载模型列表失败:', error)
    ElMessage.error('加载模型列表失败')
  } finally {
    loading.value = false
  }
}



const loadStats = async () => {
  try {
    const response = await aiApi.getStats()
    stats.value = {
      total_algorithms: response.total_algorithms || 0,
      total_models: response.total_models || 0,
      total_size: response.total_model_size || 0,
      avg_accuracy: response.avg_model_accuracy || 0
    }
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

const handleSearch = () => {
  currentPage.value = 1
  loadData()
}

const handleFilter = () => {
  currentPage.value = 1
  loadData()
}

const resetFilters = () => {
  searchQuery.value = ''
  filterType.value = ''
  filterStatus.value = undefined
  currentPage.value = 1
  loadData()
}

const handleViewModeChange = () => {
  currentPage.value = 1
  selectedItems.value = []
  selectedAlgorithm.value = null
  loadData()
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  loadData()
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
  loadData()
}

const handleSelectionChange = (selection: any[]) => {
  selectedItems.value = selection
}

const selectAlgorithm = async (algorithm: AIAlgorithm) => {
  selectedAlgorithm.value = algorithm
  // 加载算法关联的模型
  try {
    const response = await aiApi.getModels({ algorithm_id: algorithm.id, page_size: 100 })
    algorithm.models = response.data || []
  } catch (error) {
    console.error('加载算法模型失败:', error)
  }
}

const handleAlgorithmAction = async (command: { action: string; data: AIAlgorithm }) => {
  const { action, data } = command
  switch (action) {
    case 'view':
      // TODO: 实现查看详情
      break
    case 'edit':
      // TODO: 实现编辑算法
      break
    case 'copy':
      // TODO: 实现复制算法
      break
    case 'delete':
      await deleteAlgorithm(data)
      break
  }
}

const deleteAlgorithm = async (algorithm: AIAlgorithm) => {
  try {
    await ElMessageBox.confirm(
      '确定要删除这个算法吗？删除后无法恢复。',
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await aiApi.deleteAlgorithm(algorithm.id)
    ElMessage.success('删除成功')
    loadAlgorithms()
    loadStats()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除算法失败:', error)
      ElMessage.error('删除算法失败')
    }
  }
}

const toggleAlgorithmStatus = async (algorithm: AIAlgorithm) => {
  try {
    await aiApi.updateAlgorithm(algorithm.id, { is_active: algorithm.is_active })
    ElMessage.success(`算法已${algorithm.is_active ? '启用' : '停用'}`)
    loadStats()
  } catch (error) {
    console.error('更新算法状态失败:', error)
    ElMessage.error('更新算法状态失败')
    algorithm.is_active = !algorithm.is_active
  }
}

const toggleModelStatus = async (model: AIModel) => {
  try {
    const updateData: AIModelUpdate = { is_active: model.is_active }
    await aiApi.updateModel(model.id, updateData)
    ElMessage.success(`模型已${model.is_active ? '激活' : '停用'}`)
    loadStats()
  } catch (error) {
    console.error('更新模型状态失败:', error)
    ElMessage.error('更新模型状态失败')
    model.is_active = !model.is_active
  }
}

const openAddModelDialog = async () => {
  // 确保算法列表已加载
  if (algorithms.value.length === 0) {
    await loadAlgorithms()
  }
  showModelDialog.value = true
}

const addModelToAlgorithm = () => {
  if (selectedAlgorithm.value) {
    modelForm.algorithm_id = selectedAlgorithm.value.id
  }
  showModelDialog.value = true
}

const viewModel = (model: AIModel) => {
  viewingModel.value = model
  showModelDetailDialog.value = true
}

const editModel = (model: AIModel) => {
  editingModel.value = model
  Object.assign(modelForm, {
    name: model.name,
    model_type: model.model_type,
    version: model.version,
    description: model.description,
    file_path: model.file_path,
    file_size: model.file_size,
    algorithm_id: model.algorithm_id,
    input_format: model.input_format,
    output_format: model.output_format,
    performance_metrics: {
      accuracy: model.performance_metrics?.accuracy,
      validation_accuracy: model.performance_metrics?.validation_accuracy,
      inference_time: model.performance_metrics?.inference_time
    },
    tags: model.tags,
    is_active: model.is_active
  })
  showModelDialog.value = true
}

const deleteModel = async (model: AIModel) => {
  try {
    await ElMessageBox.confirm(
      '确定要删除这个模型吗？删除后无法恢复。',
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await aiApi.deleteModel(model.id)
    ElMessage.success('删除成功')
    loadData()
    loadStats()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除模型失败:', error)
      ElMessage.error('删除模型失败')
    }
  }
}

const saveModel = async () => {
  try {
    await modelFormRef.value?.validate()
    
    saving.value = true
    
    if (editingModel.value) {
      const updateData: AIModelUpdate = {
        name: modelForm.name,
        model_type: modelForm.model_type,
        version: modelForm.version,
        description: modelForm.description,
        algorithm_id: modelForm.algorithm_id,
        input_format: modelForm.input_format,
        output_format: modelForm.output_format,
        performance_metrics: {
          accuracy: modelForm.performance_metrics.accuracy,
          validation_accuracy: modelForm.performance_metrics.validation_accuracy,
          inference_time: modelForm.performance_metrics.inference_time
        },
        tags: modelForm.tags,
        is_active: modelForm.is_active
      }
      await aiApi.updateModel(editingModel.value.id, updateData)
      ElMessage.success('模型更新成功')
    } else {
      // 如果有模型文件，先上传文件
      if (modelFile.value) {
        try {
          const uploadResult = await aiApi.uploadModelFile(modelFile.value)
          // 更新模型表单中的文件路径
          modelForm.file_path = uploadResult.file_path
          modelForm.file_size = uploadResult.file_size
        } catch (uploadError) {
          console.error('模型文件上传失败:', uploadError)
          ElMessage.error('模型文件上传失败')
          return
        }
      }
      
      await aiApi.createModel(modelForm)
      ElMessage.success('模型创建成功')
    }
    
    showModelDialog.value = false
    resetModelForm()
    loadData()
    loadStats()
  } catch (error) {
    console.error('保存模型失败:', error)
    ElMessage.error('保存模型失败')
  } finally {
    saving.value = false
  }
}

const resetModelForm = () => {
  editingModel.value = null
  Object.assign(modelForm, {
    name: '',
    model_type: 'pytorch',
    version: '',
    description: '',
    file_path: '',
    file_size: 0,
    algorithm_id: undefined,
    input_format: {},
    output_format: {},
    performance_metrics: {
      accuracy: undefined,
      validation_accuracy: undefined,
      inference_time: undefined
    },
    tags: [],
    is_active: true
  })
  modelFile.value = null
  modelFormRef.value?.resetFields()
}

// 示例算法包相关方法
const showExampleDetails = () => {
  showExampleDialog.value = true
  activeTab.value = 'info'
}

const downloadExamplePackage = () => {
  try {
    // 创建下载链接，使用端口3000
    const link = document.createElement('a')
    link.href = 'http://localhost:3000/example-algorithm-package.zip'
    link.download = 'face-detection-algorithm-v1.0.0.zip'
    link.target = '_blank'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    ElMessage.success('示例算法包下载已开始')
  } catch (error) {
    console.error('下载失败:', error)
    ElMessage.error('下载失败，请稍后重试')
  }
}

// 文件上传相关方法
const handleFileChange = (file: UploadFile) => {
  uploadFile.value = file.raw || null
}

const beforeUpload = (file: File) => {
  const isValidType = ['application/zip', 'application/x-tar', 'application/gzip'].includes(file.type) ||
    file.name.endsWith('.zip') || file.name.endsWith('.tar.gz') || file.name.endsWith('.tar')
  
  if (!isValidType) {
    ElMessage.error('只支持 .zip, .tar.gz, .tar 格式的文件')
    return false
  }
  
  const isLt500M = file.size / 1024 / 1024 < 500
  if (!isLt500M) {
    ElMessage.error('文件大小不能超过 500MB')
    return false
  }
  
  return false // 阻止自动上传
}

const handleModelFileChange = (file: UploadFile) => {
  modelFile.value = file.raw || null
  if (modelFile.value) {
    modelForm.file_path = modelFile.value.name
    modelForm.file_size = modelFile.value.size
  }
}

const beforeModelUpload = (file: File) => {
  const validExtensions = ['.pth', '.pt', '.onnx', '.pb', '.tflite', '.bin', '.xml']
  const isValidType = validExtensions.some(ext => file.name.toLowerCase().endsWith(ext))
  
  if (!isValidType) {
    ElMessage.error('不支持的模型文件格式')
    return false
  }
  
  const isLt1G = file.size / 1024 / 1024 < 1024
  if (!isLt1G) {
    ElMessage.error('模型文件大小不能超过 1GB')
    return false
  }
  
  return false // 阻止自动上传
}

const nextStep = async () => {
  if (uploadStep.value === 0) {
    // 开始解析文件
    uploadStep.value = 1
    await parseAlgorithmPackage()
  } else if (uploadStep.value === 1) {
    uploadStep.value = 2
  } else if (uploadStep.value === 2) {
    uploadStep.value = 3
    await installAlgorithmPackage()
  }
}

const prevStep = () => {
  if (uploadStep.value > 0) {
    uploadStep.value--
  }
}

const parseAlgorithmPackage = async () => {
  try {
    parseProgress.value = 0
    parseStatus.value = ''
    parseText.value = '正在解析算法包...'
    
    // 模拟解析过程
    const steps = [
      { progress: 20, text: '正在读取包文件...' },
      { progress: 40, text: '正在解析配置文件...' },
      { progress: 60, text: '正在验证依赖关系...' },
      { progress: 80, text: '正在检查模型文件...' },
      { progress: 100, text: '解析完成' }
    ]
    
    for (const step of steps) {
      await new Promise(resolve => setTimeout(resolve, 500))
      parseProgress.value = step.progress
      parseText.value = step.text
    }
    
    parseStatus.value = 'success'
    
    // 模拟解析结果
    algorithmInfo.name = uploadFile.value?.name.replace(/\.(zip|tar\.gz|tar)$/, '') || ''
    algorithmInfo.version = '1.0.0'
    packageInfo.value = {
      size: uploadFile.value?.size || 0,
      file_count: 25,
      dependencies: ['numpy', 'opencv-python', 'torch'],
      models: ['model.pth', 'config.json']
    }
  } catch (error) {
    parseStatus.value = 'exception'
    parseText.value = '解析失败'
    console.error('解析算法包失败:', error)
  }
}

const installAlgorithmPackage = async () => {
  try {
    if (!uploadFile.value) {
      throw new Error('请先选择算法包文件')
    }
    
    installProgress.value = 0
    installStatus.value = ''
    installText.value = '正在安装算法包...'
    installLogs.value = []
    
    // 第一步：上传文件到MinIO
    installProgress.value = 10
    installText.value = '正在上传文件...'
    installLogs.value.push({
      time: new Date().toLocaleTimeString(),
      level: 'info',
      message: '开始上传算法包文件到MinIO'
    })
    
    const uploadResult = await aiApi.uploadAlgorithmFile(uploadFile.value, (progress) => {
      installProgress.value = 10 + (progress * 0.6) // 上传占60%进度
    })
    
    installLogs.value.push({
      time: new Date().toLocaleTimeString(),
      level: 'info',
      message: `文件上传成功: ${uploadResult.file_path}`
    })
    
    // 第二步：解析算法包信息
    installProgress.value = 70
    installText.value = '正在解析算法包...'
    installLogs.value.push({
      time: new Date().toLocaleTimeString(),
      level: 'info',
      message: '正在解析算法包配置信息'
    })
    
    // 更新算法信息中的文件路径
    algorithmInfo.file_path = uploadResult.file_path
    
    await new Promise(resolve => setTimeout(resolve, 500))
    
    // 第三步：创建算法记录
    installProgress.value = 90
    installText.value = '正在注册算法...'
    installLogs.value.push({
      time: new Date().toLocaleTimeString(),
      level: 'info',
      message: '正在注册算法到系统'
    })
    
    await aiApi.createAlgorithm(algorithmInfo)
    
    // 完成
    installProgress.value = 100
    installText.value = '安装完成'
    installStatus.value = 'success'
    installLogs.value.push({
      time: new Date().toLocaleTimeString(),
      level: 'info',
      message: '算法包安装成功'
    })
    
  } catch (error) {
    installStatus.value = 'exception'
    installText.value = '安装失败'
    installLogs.value.push({
      time: new Date().toLocaleTimeString(),
      level: 'error',
      message: '算法包安装失败: ' + (error as Error).message
    })
    console.error('安装算法包失败:', error)
  }
}

const finishInstall = () => {
  showUploadDialog.value = false
  uploadStep.value = 0
  uploadFile.value = null
  loadData()
  loadStats()
}

const batchOperation = () => {
  ElMessage.info('批量操作功能待实现')
}



// 工具函数
const getAlgorithmTypeLabel = (type: string) => {
  const typeMap: Record<string, string> = {
    object_detection: '目标检测',
    face_recognition: '人脸识别',
    behavior_analysis: '行为分析',
    vehicle_detection: '车辆检测',
    intrusion_detection: '入侵检测',
    fire_detection: '火焰检测',
    smoke_detection: '烟雾检测',
    crowd_analysis: '人群分析',
    abnormal_behavior: '异常行为',
    custom: '自定义'
  }
  return typeMap[type] || type
}

const getAlgorithmTypeColor = (type: string) => {
  const colorMap: Record<string, string> = {
    object_detection: 'primary',
    face_recognition: 'success',
    behavior_analysis: 'warning',
    vehicle_detection: 'info',
    intrusion_detection: 'danger',
    fire_detection: 'danger',
    smoke_detection: 'warning',
    crowd_analysis: 'info',
    abnormal_behavior: 'warning',
    custom: ''
  }
  return colorMap[type] || ''
}

const getModelTypeLabel = (type: string) => {
  const typeMap: Record<string, string> = {
    pytorch: 'PyTorch',
    tensorflow: 'TensorFlow',
    onnx: 'ONNX',
    openvino: 'OpenVINO',
    tensorrt: 'TensorRT',
    other: '其他'
  }
  return typeMap[type] || type
}

const getModelTypeColor = (type: string) => {
  const colorMap: Record<string, string> = {
    pytorch: 'warning',
    tensorflow: 'success',
    onnx: 'primary',
    openvino: 'info',
    tensorrt: 'danger',
    other: ''
  }
  return colorMap[type] || ''
}



const formatFileSize = (bytes: number) => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatDate = (date: string) => {
  return new Date(date).toLocaleDateString('zh-CN')
}

const formatDateTime = (date: string) => {
  return new Date(date).toLocaleString('zh-CN')
}

// 生命周期
onMounted(() => {
  loadData()
  loadStats()
})
</script>

<style scoped>
@import '@/styles/stat-cards.scss';

.ai-unified-container {
  padding: 24px;
  background: #f5f5f5;
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  padding: 24px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.header-left {
  flex: 1;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
  color: #1f2937;
}

.page-description {
  margin: 0;
  color: #6b7280;
  font-size: 14px;
}

.header-right {
  display: flex;
  gap: 12px;
}

/* 空状态样式 */
.empty-state {
  text-align: center;
  padding: 80px 20px;
  background: #fafafa;
  border-radius: 8px;
  border: 1px dashed #d1d5db;
}

.empty-icon {
  margin-bottom: 16px;
  color: #d1d5db;
}

.empty-title {
  font-size: 18px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 8px;
}

.empty-description {
  font-size: 14px;
  color: #6b7280;
  margin-bottom: 24px;
  line-height: 1.5;
}

.empty-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
  flex-wrap: wrap;
}

.stat-label {
  font-size: 14px;
  color: #6b7280;
  font-weight: 500;
}

.search-filters {
  margin-bottom: 24px;
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.filter-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.algorithms-view {
  display: flex;
  gap: 24px;
}

.algorithms-grid {
  flex: 1;
}

.algorithm-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  margin-bottom: 24px;
  transition: all 0.3s ease;
  border: 1px solid #e5e7eb;
  cursor: pointer;
}

.algorithm-card:hover {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.algorithm-card.selected {
  border-color: #3b82f6;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 20px 20px 0 20px;
}

.algorithm-info {
  flex: 1;
}

.algorithm-name {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  line-height: 1.4;
}

.algorithm-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.version {
  font-size: 12px;
  color: #6b7280;
  background: #f3f4f6;
  padding: 2px 8px;
  border-radius: 4px;
}

.card-actions {
  margin-left: 12px;
}

.card-content {
  padding: 16px 20px;
}

.algorithm-description {
  margin: 0 0 16px 0;
  color: #6b7280;
  font-size: 14px;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.algorithm-stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 16px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-label {
  font-size: 12px;
  color: #9ca3af;
  font-weight: 500;
}

.stat-value {
  font-size: 14px;
  color: #374151;
  font-weight: 600;
}

.algorithm-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tag-item {
  font-size: 12px;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px 20px 20px;
  border-top: 1px solid #f3f4f6;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-text {
  font-size: 14px;
  color: #6b7280;
}

.performance-metrics {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.metric-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 2px 8px;
  background: #f8f9fa;
  border-radius: 4px;
  font-size: 12px;
}

.metric-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #059669;
  background: #ecfdf5;
  padding: 4px 8px;
  border-radius: 4px;
}

.detail-panel {
  width: 400px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 20px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.models-list {
  max-height: 400px;
  overflow-y: auto;
}

.models-view,
.services-view {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-bottom: 24px;
}

.model-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.model-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.model-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #6b7280;
}

.file-size {
  background: #e5e7eb;
  padding: 2px 6px;
  border-radius: 4px;
}

.algorithm-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.algorithm-name {
  font-weight: 600;
  color: #1f2937;
}

.algorithm-type {
  font-size: 12px;
  color: #6b7280;
}

.no-algorithm {
  color: #9ca3af;
  font-style: italic;
}

.metric-label {
  color: #6b7280;
}

.metric-value {
  font-weight: 600;
  color: #1f2937;
}

.no-metrics {
  color: #9ca3af;
  font-style: italic;
}

.pagination-container {
  display: flex;
  justify-content: center;
  padding: 24px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.upload-container {
  padding: 20px 0;
}

.upload-step {
  text-align: center;
  padding: 40px 0;
}

.upload-dragger {
  width: 100%;
}

.file-info {
  margin-top: 20px;
  text-align: left;
}

.file-info h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  background: #f9fafb;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
}

.file-name {
  flex: 1;
  font-size: 14px;
  color: #374151;
}

.file-size {
  font-size: 12px;
  color: #6b7280;
  background: #e5e7eb;
  padding: 2px 6px;
  border-radius: 4px;
}

.parse-step,
.install-step {
  padding: 40px 0;
  text-align: center;
}

.parse-progress,
.install-progress {
  margin-bottom: 20px;
}

.parse-text,
.install-text {
  margin: 16px 0 0 0;
  font-size: 14px;
  color: #6b7280;
}

.confirm-step {
  padding: 20px 0;
}

.package-info {
  margin-top: 20px;
}

.package-info h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
}

.install-logs {
  margin-top: 20px;
  text-align: left;
}

.install-logs h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
}

.log-container {
  max-height: 200px;
  overflow-y: auto;
  background: #1f2937;
  border-radius: 6px;
  padding: 12px;
}

.log-item {
  display: flex;
  gap: 8px;
  margin-bottom: 4px;
  font-size: 12px;
  font-family: monospace;
}

.log-item.info {
  color: #10b981;
}

.log-item.error {
  color: #ef4444;
}

.log-item.warning {
  color: #f59e0b;
}

.log-time {
  color: #6b7280;
  min-width: 80px;
}

.log-message {
  flex: 1;
}

.model-upload {
  width: 100%;
}

/* 示例算法包样式 */
.example-packages {
  margin-bottom: 24px;
  text-align: left;
}

.example-packages h4 {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.example-description {
  margin: 0 0 16px 0;
  font-size: 14px;
  color: #6b7280;
}

.example-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.example-item {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
  background: #f9fafb;
  transition: all 0.2s;
}

.example-item:hover {
  border-color: #3b82f6;
  background: #eff6ff;
}

.example-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
}

.example-info h5 {
  margin: 0 0 4px 0;
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
}

.example-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.example-meta .version {
  font-size: 12px;
  color: #6b7280;
  background: #e5e7eb;
  padding: 2px 6px;
  border-radius: 4px;
}

.example-actions {
  display: flex;
  gap: 8px;
}

.example-desc {
  margin: 0 0 12px 0;
  font-size: 13px;
  color: #4b5563;
  line-height: 1.5;
}

.example-features {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

/* 示例详情对话框样式 */
.example-details {
  padding: 0;
}

.example-details h4 {
  margin: 20px 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
}

.example-details ul {
  margin: 8px 0;
  padding-left: 20px;
}

.example-details li {
  margin-bottom: 4px;
  font-size: 14px;
  color: #4b5563;
}

.file-structure {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 16px;
}

.file-structure pre {
  margin: 0;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.5;
  color: #374151;
  white-space: pre;
  overflow-x: auto;
}

.usage-guide {
  line-height: 1.6;
}

.usage-guide h4 {
  margin: 20px 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
}

.usage-guide ol {
  margin: 8px 0;
  padding-left: 20px;
}

.usage-guide li {
  margin-bottom: 6px;
  font-size: 14px;
  color: #4b5563;
}

.usage-guide p {
  margin: 8px 0;
  font-size: 14px;
  color: #4b5563;
}

.usage-guide code {
  background: #f3f4f6;
  padding: 2px 4px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  color: #1f2937;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .algorithms-view {
    flex-direction: column;
  }
  
  .detail-panel {
    width: 100%;
  }
  
  .algorithms-grid .el-col {
    width: 50%;
  }
}

@media (max-width: 768px) {
  .algorithms-grid .el-col {
    width: 100%;
  }
  
  .page-header {
    flex-direction: column;
    gap: 16px;
  }
  
  .search-filters .el-row {
    flex-direction: column;
  }
  
  .search-filters .el-col {
    width: 100%;
    margin-bottom: 12px;
  }
  
  .stats-cards .el-col {
    width: 50%;
    margin-bottom: 16px;
  }
}

/* 模型详情对话框样式 */
.model-detail {
  padding: 0;
}

.model-detail h4 {
  margin: 24px 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  border-bottom: 1px solid #e5e7eb;
  padding-bottom: 8px;
}

.model-name {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.file-path {
  font-family: 'Courier New', monospace;
  font-size: 13px;
  color: #6b7280;
  background: #f3f4f6;
  padding: 2px 6px;
  border-radius: 4px;
}

.model-description {
  margin-top: 20px;
}

.model-description p {
  margin: 8px 0 0 0;
  font-size: 14px;
  color: #4b5563;
  line-height: 1.6;
}

.performance-metrics {
  margin-top: 20px;
}

.metric-card {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
  text-align: center;
}

.metric-label {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 8px;
  font-weight: 500;
}

.metric-value {
  font-size: 20px;
  font-weight: 700;
  color: #1f2937;
}

.model-formats {
  margin-top: 20px;
}

.format-card {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
}

.format-card h5 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
}

.format-json {
  margin: 0;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.4;
  color: #374151;
  background: #ffffff;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  padding: 12px;
  overflow-x: auto;
  max-height: 200px;
  overflow-y: auto;
}

.model-tags {
  margin-top: 20px;
}

.tags-container {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}

.tag-item {
  margin: 0;
}

/* 操作按钮样式 */
.action-buttons {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: nowrap;
}

.action-buttons .el-button {
  margin: 0;
  min-width: 60px;
}

/* 删除按钮危险样式 */
.el-dropdown-menu .danger-item {
  color: #f56c6c !important;
}

.el-dropdown-menu .danger-item:hover {
  background-color: #fef0f0 !important;
  color: #f56c6c !important;
}

.el-dropdown-menu .danger-item .el-icon {
  color: #f56c6c !important;
}

.el-dropdown-menu .danger-item span {
  color: #f56c6c !important;
}
</style>