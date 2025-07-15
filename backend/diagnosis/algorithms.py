import cv2
import numpy as np
from typing import Dict, Any, Tuple, List
import time
from enum import Enum
from models.diagnosis import DiagnosisType, DiagnosisStatus

class DiagnosisAlgorithm:
    """诊断算法基类"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
    def diagnose(self, image: np.ndarray) -> Dict[str, Any]:
        """执行诊断"""
        raise NotImplementedError
        
    def get_threshold(self, key: str, default: float) -> float:
        """获取阈值配置"""
        return self.config.get('thresholds', {}).get(key, default)

class BrightnessAlgorithm(DiagnosisAlgorithm):
    """亮度检测算法"""
    
    def diagnose(self, image: np.ndarray) -> Dict[str, Any]:
        start_time = time.time()
        
        # 转换为灰度图
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        # 计算平均亮度
        mean_brightness = np.mean(gray)
        
        # 获取阈值
        min_threshold = self.get_threshold('brightness_min', 30)
        max_threshold = self.get_threshold('brightness_max', 220)
        optimal_brightness = (min_threshold + max_threshold) / 2  # 最佳亮度值
        
        # 计算标准化评分 (0-100)
        if mean_brightness < min_threshold:
            # 过低：线性映射到0-60分
            score = max(0, (mean_brightness / min_threshold) * 60)
            status = DiagnosisStatus.ERROR
            message = f"亮度过低: {mean_brightness:.1f} < {min_threshold} (评分: {score:.1f})"
        elif mean_brightness > max_threshold:
            # 过高：线性映射到0-60分
            excess = mean_brightness - max_threshold
            max_excess = 255 - max_threshold  # 最大可能的超出值
            score = max(0, 60 - (excess / max_excess) * 60)
            status = DiagnosisStatus.ERROR
            message = f"亮度过高: {mean_brightness:.1f} > {max_threshold} (评分: {score:.1f})"
        else:
            # 正常范围：根据距离最佳值的偏差计算60-100分
            distance_from_optimal = abs(mean_brightness - optimal_brightness)
            max_distance = (max_threshold - min_threshold) / 2
            score = 100 - (distance_from_optimal / max_distance) * 40
            score = max(60, min(100, score))  # 确保在60-100范围内
            
            if score >= 90:
                status = DiagnosisStatus.NORMAL
                message = f"亮度优秀: {mean_brightness:.1f} (评分: {score:.1f})"
            elif score >= 75:
                status = DiagnosisStatus.NORMAL
                message = f"亮度良好: {mean_brightness:.1f} (评分: {score:.1f})"
            else:
                status = DiagnosisStatus.WARNING
                message = f"亮度一般: {mean_brightness:.1f} (评分: {score:.1f})"
            
        processing_time = (time.time() - start_time) * 1000
        
        return {
            'status': status,
            'score': float(score),
            'threshold': {'min': min_threshold, 'max': max_threshold},
            'message': message,
            'processing_time': processing_time,
            'metrics': {
                'mean_brightness': float(mean_brightness),
                'std_brightness': float(np.std(gray)),
                'raw_score': float(mean_brightness),  # 保留原始亮度值
                'normalized_score': float(score)  # 标准化后的评分
            }
        }

class ClarityAlgorithm(DiagnosisAlgorithm):
    """清晰度检测算法"""
    
    def diagnose(self, image: np.ndarray) -> Dict[str, Any]:
        start_time = time.time()
        
        # 转换为灰度图
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        # 使用Laplacian算子计算清晰度
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        clarity_score = np.var(laplacian)
        
        # 获取阈值
        min_threshold = self.get_threshold('clarity_min', 100)
        excellent_threshold = self.get_threshold('clarity_excellent', 500)  # 优秀清晰度阈值
        
        # 计算标准化评分 (0-100)
        if clarity_score < min_threshold:
            # 模糊：线性映射到0-60分
            score = max(0, (clarity_score / min_threshold) * 60)
            status = DiagnosisStatus.WARNING
            message = f"图像模糊: {clarity_score:.1f} < {min_threshold} (评分: {score:.1f})"
        elif clarity_score >= excellent_threshold:
            # 优秀清晰度：95-100分
            score = min(100, 95 + (clarity_score - excellent_threshold) / excellent_threshold * 5)
            status = DiagnosisStatus.NORMAL
            message = f"图像非常清晰: {clarity_score:.1f} (评分: {score:.1f})"
        else:
            # 正常范围：线性映射到60-95分
            score = 60 + ((clarity_score - min_threshold) / (excellent_threshold - min_threshold)) * 35
            score = max(60, min(95, score))
            
            if score >= 85:
                status = DiagnosisStatus.NORMAL
                message = f"图像清晰: {clarity_score:.1f} (评分: {score:.1f})"
            elif score >= 70:
                status = DiagnosisStatus.NORMAL
                message = f"图像较清晰: {clarity_score:.1f} (评分: {score:.1f})"
            else:
                status = DiagnosisStatus.WARNING
                message = f"图像清晰度一般: {clarity_score:.1f} (评分: {score:.1f})"
            
        processing_time = (time.time() - start_time) * 1000
        
        return {
            'status': status,
            'score': float(score),
            'threshold': min_threshold,
            'message': message,
            'processing_time': processing_time,
            'metrics': {
                'clarity_score': float(clarity_score),
                'laplacian_var': float(clarity_score),
                'raw_score': float(clarity_score),  # 保留原始清晰度值
                'normalized_score': float(score)  # 标准化后的评分
            }
        }

class BlueScreenAlgorithm(DiagnosisAlgorithm):
    """蓝屏检测算法"""
    
    def diagnose(self, image: np.ndarray) -> Dict[str, Any]:
        start_time = time.time()
        
        # 转换为HSV色彩空间
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # 定义蓝色范围
        lower_blue = np.array([100, 50, 50])
        upper_blue = np.array([130, 255, 255])
        
        # 创建蓝色掩码
        mask = cv2.inRange(hsv, lower_blue, upper_blue)
        blue_ratio = np.sum(mask > 0) / (image.shape[0] * image.shape[1])
        
        # 获取阈值
        threshold = self.get_threshold('blue_screen_ratio', 0.8)
        
        # 计算评分：正常情况接近100分，异常情况接近0分
        # 评分 = 100 - (蓝色比例 / 阈值) * 100
        # 当蓝色比例接近0时，评分接近100（正常）
        # 当蓝色比例达到阈值时，评分接近0（异常）
        if blue_ratio <= threshold:
            # 正常情况：线性映射到60-100分
            score = 100 - (blue_ratio / threshold) * 40
        else:
            # 异常情况：映射到0-60分
            excess_ratio = min(blue_ratio - threshold, threshold)  # 限制最大超出量
            score = 60 - (excess_ratio / threshold) * 60
        
        # 确保分数在0-100范围内
        score = max(0, min(100, score))
        
        # 判断状态
        if blue_ratio > threshold:
            status = DiagnosisStatus.CRITICAL
            message = f"检测到蓝屏: {blue_ratio:.2%} > {threshold:.2%} (评分: {score:.1f})"
        elif blue_ratio > threshold * 0.5:  # 添加警告阈值
            status = DiagnosisStatus.WARNING
            message = f"蓝色区域较多: {blue_ratio:.2%} (评分: {score:.1f})"
        else:
            status = DiagnosisStatus.NORMAL
            message = f"画面正常: {blue_ratio:.2%} (评分: {score:.1f})"
            
        processing_time = (time.time() - start_time) * 1000
        
        return {
            'status': status,
            'score': float(score),
            'threshold': threshold,
            'message': message,
            'processing_time': processing_time,
            'metrics': {
                'blue_ratio': float(blue_ratio),
                'blue_pixels': int(np.sum(mask > 0)),
                'raw_score': float(blue_ratio),  # 保留原始比例值
                'normalized_score': float(score)  # 标准化后的评分
            }
        }

class NoiseAlgorithm(DiagnosisAlgorithm):
    """噪声检测算法"""
    
    def diagnose(self, image: np.ndarray) -> Dict[str, Any]:
        start_time = time.time()
        
        # 转换为灰度图
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        # 使用高斯滤波去噪
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # 计算噪声水平（原图与去噪图的差异）
        noise = cv2.absdiff(gray, blurred)
        noise_level = np.mean(noise)
        
        # 获取阈值
        max_threshold = self.get_threshold('noise_max', 15)
        excellent_threshold = self.get_threshold('noise_excellent', 3)  # 优秀噪声水平阈值
        
        # 计算标准化评分 (0-100)，噪声越低分数越高
        if noise_level <= excellent_threshold:
            # 优秀：95-100分
            score = min(100, 100 - (noise_level / excellent_threshold) * 5)
            status = DiagnosisStatus.NORMAL
            message = f"噪声极低: {noise_level:.1f} (评分: {score:.1f})"
        elif noise_level <= max_threshold:
            # 正常范围：线性映射到60-95分
            score = 95 - ((noise_level - excellent_threshold) / (max_threshold - excellent_threshold)) * 35
            score = max(60, min(95, score))
            
            if score >= 85:
                status = DiagnosisStatus.NORMAL
                message = f"噪声很低: {noise_level:.1f} (评分: {score:.1f})"
            elif score >= 70:
                status = DiagnosisStatus.NORMAL
                message = f"噪声较低: {noise_level:.1f} (评分: {score:.1f})"
            else:
                status = DiagnosisStatus.WARNING
                message = f"噪声一般: {noise_level:.1f} (评分: {score:.1f})"
        else:
            # 噪声过高：线性映射到0-60分
            excess = noise_level - max_threshold
            max_excess = 50 - max_threshold  # 假设最大噪声水平为50
            score = max(0, 60 - (excess / max_excess) * 60)
            status = DiagnosisStatus.WARNING
            message = f"噪声过高: {noise_level:.1f} > {max_threshold} (评分: {score:.1f})"
            
        processing_time = (time.time() - start_time) * 1000
        
        return {
            'status': status,
            'score': float(score),
            'threshold': max_threshold,
            'message': message,
            'processing_time': processing_time,
            'metrics': {
                'noise_level': float(noise_level),
                'noise_std': float(np.std(noise)),
                'raw_score': float(noise_level),  # 保留原始噪声水平
                'normalized_score': float(score)  # 标准化后的评分
            }
        }

class ContrastAlgorithm(DiagnosisAlgorithm):
    """对比度检测算法"""
    
    def diagnose(self, image: np.ndarray) -> Dict[str, Any]:
        start_time = time.time()
        
        # 转换为灰度图
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        # 计算对比度（标准差）
        contrast = np.std(gray)
        
        # 获取阈值
        min_threshold = self.get_threshold('contrast_min', 20)
        excellent_threshold = self.get_threshold('contrast_excellent', 60)  # 优秀对比度阈值
        
        # 计算标准化评分 (0-100)
        if contrast < min_threshold:
            # 对比度过低：线性映射到0-60分
            score = max(0, (contrast / min_threshold) * 60)
            status = DiagnosisStatus.WARNING
            message = f"对比度过低: {contrast:.1f} < {min_threshold} (评分: {score:.1f})"
        elif contrast >= excellent_threshold:
            # 优秀对比度：95-100分
            score = min(100, 95 + (contrast - excellent_threshold) / excellent_threshold * 5)
            status = DiagnosisStatus.NORMAL
            message = f"对比度优秀: {contrast:.1f} (评分: {score:.1f})"
        else:
            # 正常范围：线性映射到60-95分
            score = 60 + ((contrast - min_threshold) / (excellent_threshold - min_threshold)) * 35
            score = max(60, min(95, score))
            
            if score >= 85:
                status = DiagnosisStatus.NORMAL
                message = f"对比度良好: {contrast:.1f} (评分: {score:.1f})"
            elif score >= 70:
                status = DiagnosisStatus.NORMAL
                message = f"对比度正常: {contrast:.1f} (评分: {score:.1f})"
            else:
                status = DiagnosisStatus.WARNING
                message = f"对比度一般: {contrast:.1f} (评分: {score:.1f})"
            
        processing_time = (time.time() - start_time) * 1000
        
        return {
            'status': status,
            'score': float(score),
            'threshold': min_threshold,
            'message': message,
            'processing_time': processing_time,
            'metrics': {
                'contrast': float(contrast),
                'min_value': int(np.min(gray)),
                'max_value': int(np.max(gray)),
                'raw_score': float(contrast),  # 保留原始对比度值
                'normalized_score': float(score)  # 标准化后的评分
            }
        }

class ShakeAlgorithm(DiagnosisAlgorithm):
    """抖动检测算法"""
    
    def diagnose(self, image: np.ndarray) -> Dict[str, Any]:
        start_time = time.time()
        
        # 转换为灰度图
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        # 使用边缘检测计算图像锐度
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / (image.shape[0] * image.shape[1])
        
        # 计算图像梯度方差（抖动会导致边缘模糊）
        grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
        gradient_variance = np.var(gradient_magnitude)
        
        # 综合评估抖动程度
        shake_score = edge_density * gradient_variance / 1000  # 归一化
        
        # 获取阈值
        min_threshold = self.get_threshold('shake_min', 0.5)
        excellent_threshold = self.get_threshold('shake_excellent', 2.0)
        
        # 计算标准化评分 (0-100)
        if shake_score < min_threshold:
            # 抖动严重：0-60分
            score = max(0, (shake_score / min_threshold) * 60)
            status = DiagnosisStatus.WARNING
            message = f"检测到严重抖动: {shake_score:.2f} (评分: {score:.1f})"
        elif shake_score >= excellent_threshold:
            # 图像稳定：95-100分
            score = min(100, 95 + min((shake_score - excellent_threshold) / excellent_threshold, 1) * 5)
            status = DiagnosisStatus.NORMAL
            message = f"图像非常稳定: {shake_score:.2f} (评分: {score:.1f})"
        else:
            # 正常范围：60-95分
            score = 60 + ((shake_score - min_threshold) / (excellent_threshold - min_threshold)) * 35
            score = max(60, min(95, score))
            
            if score >= 85:
                status = DiagnosisStatus.NORMAL
                message = f"图像稳定: {shake_score:.2f} (评分: {score:.1f})"
            else:
                status = DiagnosisStatus.WARNING
                message = f"轻微抖动: {shake_score:.2f} (评分: {score:.1f})"
            
        processing_time = (time.time() - start_time) * 1000
        
        return {
            'status': status,
            'score': float(score),
            'threshold': min_threshold,
            'message': message,
            'processing_time': processing_time,
            'metrics': {
                'shake_score': float(shake_score),
                'edge_density': float(edge_density),
                'gradient_variance': float(gradient_variance),
                'raw_score': float(shake_score),
                'normalized_score': float(score)
            }
        }

class FreezeAlgorithm(DiagnosisAlgorithm):
    """冻结检测算法"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.previous_frame = None
        
    def diagnose(self, image: np.ndarray) -> Dict[str, Any]:
        start_time = time.time()
        
        # 转换为灰度图
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        if self.previous_frame is None:
            self.previous_frame = gray
            # 首次检测，假设正常
            return {
                'status': DiagnosisStatus.NORMAL,
                'score': 100.0,
                'threshold': 0.01,
                'message': '首次检测，画面正常',
                'processing_time': (time.time() - start_time) * 1000,
                'metrics': {
                    'frame_diff': 0.0,
                    'raw_score': 0.0,
                    'normalized_score': 100.0
                }
            }
            
        # 计算帧间差异
        frame_diff = cv2.absdiff(gray, self.previous_frame)
        diff_ratio = np.mean(frame_diff) / 255.0
        
        # 更新前一帧
        self.previous_frame = gray
        
        # 获取阈值
        freeze_threshold = self.get_threshold('freeze_threshold', 0.01)
        normal_threshold = self.get_threshold('freeze_normal', 0.05)
        
        # 计算标准化评分 (0-100)
        if diff_ratio < freeze_threshold:
            # 可能冻结：0-60分
            score = max(0, (diff_ratio / freeze_threshold) * 60)
            status = DiagnosisStatus.WARNING
            message = f"疑似画面冻结: 变化率 {diff_ratio:.3f} < {freeze_threshold:.3f} (评分: {score:.1f})"
        elif diff_ratio >= normal_threshold:
            # 画面正常变化：95-100分
            score = min(100, 95 + min((diff_ratio - normal_threshold) / normal_threshold, 1) * 5)
            status = DiagnosisStatus.NORMAL
            message = f"画面变化正常: 变化率 {diff_ratio:.3f} (评分: {score:.1f})"
        else:
            # 轻微变化：60-95分
            score = 60 + ((diff_ratio - freeze_threshold) / (normal_threshold - freeze_threshold)) * 35
            score = max(60, min(95, score))
            status = DiagnosisStatus.NORMAL
            message = f"画面轻微变化: 变化率 {diff_ratio:.3f} (评分: {score:.1f})"
            
        processing_time = (time.time() - start_time) * 1000
        
        return {
            'status': status,
            'score': float(score),
            'threshold': freeze_threshold,
            'message': message,
            'processing_time': processing_time,
            'metrics': {
                'frame_diff': float(diff_ratio),
                'mean_diff': float(np.mean(frame_diff)),
                'raw_score': float(diff_ratio),
                'normalized_score': float(score)
            }
        }

class ColorCastAlgorithm(DiagnosisAlgorithm):
    """偏色检测算法"""
    
    def diagnose(self, image: np.ndarray) -> Dict[str, Any]:
        start_time = time.time()
        
        # 计算各通道的平均值
        if len(image.shape) == 3:
            b_mean = np.mean(image[:, :, 0])
            g_mean = np.mean(image[:, :, 1])
            r_mean = np.mean(image[:, :, 2])
        else:
            # 灰度图，无偏色
            return {
                'status': DiagnosisStatus.NORMAL,
                'score': 100.0,
                'threshold': 20,
                'message': '灰度图像，无偏色问题',
                'processing_time': (time.time() - start_time) * 1000,
                'metrics': {
                    'color_cast_score': 0.0,
                    'raw_score': 0.0,
                    'normalized_score': 100.0
                }
            }
            
        # 计算颜色偏差
        total_mean = (r_mean + g_mean + b_mean) / 3
        r_deviation = abs(r_mean - total_mean)
        g_deviation = abs(g_mean - total_mean)
        b_deviation = abs(b_mean - total_mean)
        
        max_deviation = max(r_deviation, g_deviation, b_deviation)
        
        # 获取阈值
        threshold = self.get_threshold('color_cast_threshold', 20)
        severe_threshold = self.get_threshold('color_cast_severe', 50)
        
        # 计算标准化评分 (0-100)
        if max_deviation >= severe_threshold:
            # 严重偏色：0-40分
            score = max(0, 40 - ((max_deviation - severe_threshold) / severe_threshold) * 40)
            status = DiagnosisStatus.ERROR
            message = f"严重偏色: 最大偏差 {max_deviation:.1f} (评分: {score:.1f})"
        elif max_deviation >= threshold:
            # 轻微偏色：40-60分
            score = 60 - ((max_deviation - threshold) / (severe_threshold - threshold)) * 20
            status = DiagnosisStatus.WARNING
            message = f"轻微偏色: 最大偏差 {max_deviation:.1f} (评分: {score:.1f})"
        else:
            # 颜色正常：60-100分
            score = 100 - (max_deviation / threshold) * 40
            score = max(60, min(100, score))
            status = DiagnosisStatus.NORMAL
            message = f"颜色正常: 最大偏差 {max_deviation:.1f} (评分: {score:.1f})"
            
        processing_time = (time.time() - start_time) * 1000
        
        return {
            'status': status,
            'score': float(score),
            'threshold': threshold,
            'message': message,
            'processing_time': processing_time,
            'metrics': {
                'max_deviation': float(max_deviation),
                'r_mean': float(r_mean),
                'g_mean': float(g_mean),
                'b_mean': float(b_mean),
                'raw_score': float(max_deviation),
                'normalized_score': float(score)
            }
        }

class OcclusionAlgorithm(DiagnosisAlgorithm):
    """遮挡检测算法"""
    
    def diagnose(self, image: np.ndarray) -> Dict[str, Any]:
        start_time = time.time()
        
        # 转换为灰度图
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        # 检测极暗区域（可能的遮挡）
        dark_threshold = self.get_threshold('occlusion_dark_threshold', 30)
        dark_mask = gray < dark_threshold
        dark_ratio = np.sum(dark_mask) / (image.shape[0] * image.shape[1])
        
        # 检测边缘密度（遮挡会导致边缘减少）
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / (image.shape[0] * image.shape[1])
        
        # 综合评估遮挡程度
        occlusion_score = dark_ratio * 0.7 + (1 - edge_density) * 0.3
        
        # 获取阈值
        threshold = self.get_threshold('occlusion_threshold', 0.3)
        severe_threshold = self.get_threshold('occlusion_severe', 0.6)
        
        # 计算标准化评分 (0-100)
        if occlusion_score >= severe_threshold:
            # 严重遮挡：0-40分
            score = max(0, 40 - ((occlusion_score - severe_threshold) / (1 - severe_threshold)) * 40)
            status = DiagnosisStatus.CRITICAL
            message = f"严重遮挡: 遮挡评分 {occlusion_score:.2f} (评分: {score:.1f})"
        elif occlusion_score >= threshold:
            # 轻微遮挡：40-60分
            score = 60 - ((occlusion_score - threshold) / (severe_threshold - threshold)) * 20
            status = DiagnosisStatus.WARNING
            message = f"轻微遮挡: 遮挡评分 {occlusion_score:.2f} (评分: {score:.1f})"
        else:
            # 无遮挡：60-100分
            score = 100 - (occlusion_score / threshold) * 40
            score = max(60, min(100, score))
            status = DiagnosisStatus.NORMAL
            message = f"无遮挡: 遮挡评分 {occlusion_score:.2f} (评分: {score:.1f})"
            
        processing_time = (time.time() - start_time) * 1000
        
        return {
            'status': status,
            'score': float(score),
            'threshold': threshold,
            'message': message,
            'processing_time': processing_time,
            'metrics': {
                'occlusion_score': float(occlusion_score),
                'dark_ratio': float(dark_ratio),
                'edge_density': float(edge_density),
                'raw_score': float(occlusion_score),
                'normalized_score': float(score)
            }
        }

class MosaicAlgorithm(DiagnosisAlgorithm):
    """马赛克检测算法"""
    
    def diagnose(self, image: np.ndarray) -> Dict[str, Any]:
        start_time = time.time()
        
        # 转换为灰度图
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        # 检测块状结构（马赛克特征）
        # 使用形态学操作检测规则的块状结构
        kernel = np.ones((8, 8), np.uint8)
        opened = cv2.morphologyEx(gray, cv2.MORPH_OPEN, kernel)
        closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel)
        
        # 计算处理前后的差异
        diff = cv2.absdiff(gray, closed)
        mosaic_score = np.mean(diff) / 255.0
        
        # 检测边缘的规律性（马赛克会产生规律的边缘）
        edges = cv2.Canny(gray, 50, 150)
        
        # 使用霍夫变换检测直线（马赛克会产生很多直线）
        lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=50)
        line_count = len(lines) if lines is not None else 0
        line_density = line_count / (image.shape[0] * image.shape[1] / 10000)  # 归一化
        
        # 综合评估马赛克程度
        combined_score = mosaic_score * 0.6 + min(line_density / 10, 1) * 0.4
        
        # 获取阈值
        threshold = self.get_threshold('mosaic_threshold', 0.2)
        severe_threshold = self.get_threshold('mosaic_severe', 0.5)
        
        # 计算标准化评分 (0-100)
        if combined_score >= severe_threshold:
            # 严重马赛克：0-40分
            score = max(0, 40 - ((combined_score - severe_threshold) / (1 - severe_threshold)) * 40)
            status = DiagnosisStatus.CRITICAL
            message = f"严重马赛克: 马赛克评分 {combined_score:.2f} (评分: {score:.1f})"
        elif combined_score >= threshold:
            # 轻微马赛克：40-60分
            score = 60 - ((combined_score - threshold) / (severe_threshold - threshold)) * 20
            status = DiagnosisStatus.WARNING
            message = f"轻微马赛克: 马赛克评分 {combined_score:.2f} (评分: {score:.1f})"
        else:
            # 无马赛克：60-100分
            score = 100 - (combined_score / threshold) * 40
            score = max(60, min(100, score))
            status = DiagnosisStatus.NORMAL
            message = f"无马赛克: 马赛克评分 {combined_score:.2f} (评分: {score:.1f})"
            
        processing_time = (time.time() - start_time) * 1000
        
        return {
            'status': status,
            'score': float(score),
            'threshold': threshold,
            'message': message,
            'processing_time': processing_time,
            'metrics': {
                'mosaic_score': float(combined_score),
                'diff_score': float(mosaic_score),
                'line_count': int(line_count),
                'line_density': float(line_density),
                'raw_score': float(combined_score),
                'normalized_score': float(score)
            }
        }

class FlowerScreenAlgorithm(DiagnosisAlgorithm):
    """花屏检测算法"""
    
    def diagnose(self, image: np.ndarray) -> Dict[str, Any]:
        start_time = time.time()
        
        # 计算图像的颜色分布异常
        if len(image.shape) == 3:
            # 计算各通道的直方图
            hist_b = cv2.calcHist([image], [0], None, [256], [0, 256])
            hist_g = cv2.calcHist([image], [1], None, [256], [0, 256])
            hist_r = cv2.calcHist([image], [2], None, [256], [0, 256])
            
            # 计算直方图的方差（花屏会导致颜色分布异常）
            var_b = np.var(hist_b)
            var_g = np.var(hist_g)
            var_r = np.var(hist_r)
            color_variance = (var_b + var_g + var_r) / 3
        else:
            # 灰度图
            hist = cv2.calcHist([image], [0], None, [256], [0, 256])
            color_variance = np.var(hist)
            
        # 检测异常像素点（极值像素）
        if len(image.shape) == 3:
            # 检测饱和像素
            saturated_pixels = np.sum((image == 0) | (image == 255))
            total_pixels = image.shape[0] * image.shape[1] * image.shape[2]
        else:
            saturated_pixels = np.sum((image == 0) | (image == 255))
            total_pixels = image.shape[0] * image.shape[1]
            
        saturation_ratio = saturated_pixels / total_pixels
        
        # 检测噪声模式（花屏通常伴随特定的噪声模式）
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        # 使用高频滤波检测异常模式
        kernel = np.array([[-1, -1, -1], [-1, 8, -1], [-1, -1, -1]])
        filtered = cv2.filter2D(gray, -1, kernel)
        noise_level = np.std(filtered)
        
        # 综合评估花屏程度
        flower_score = (color_variance / 100000) * 0.4 + saturation_ratio * 0.3 + (noise_level / 100) * 0.3
        
        # 获取阈值
        threshold = self.get_threshold('flower_screen_threshold', 0.3)
        severe_threshold = self.get_threshold('flower_screen_severe', 0.6)
        
        # 计算标准化评分 (0-100)
        if flower_score >= severe_threshold:
            # 严重花屏：0-40分
            score = max(0, 40 - ((flower_score - severe_threshold) / (1 - severe_threshold)) * 40)
            status = DiagnosisStatus.CRITICAL
            message = f"严重花屏: 花屏评分 {flower_score:.2f} (评分: {score:.1f})"
        elif flower_score >= threshold:
            # 轻微花屏：40-60分
            score = 60 - ((flower_score - threshold) / (severe_threshold - threshold)) * 20
            status = DiagnosisStatus.WARNING
            message = f"轻微花屏: 花屏评分 {flower_score:.2f} (评分: {score:.1f})"
        else:
            # 无花屏：60-100分
            score = 100 - (flower_score / threshold) * 40
            score = max(60, min(100, score))
            status = DiagnosisStatus.NORMAL
            message = f"无花屏: 花屏评分 {flower_score:.2f} (评分: {score:.1f})"
            
        processing_time = (time.time() - start_time) * 1000
        
        return {
            'status': status,
            'score': float(score),
            'threshold': threshold,
            'message': message,
            'processing_time': processing_time,
            'metrics': {
                'flower_score': float(flower_score),
                'color_variance': float(color_variance),
                'saturation_ratio': float(saturation_ratio),
                'noise_level': float(noise_level),
                'raw_score': float(flower_score),
                'normalized_score': float(score)
            }
        }

class SignalLossAlgorithm(DiagnosisAlgorithm):
    """信号丢失检测算法"""
    
    def diagnose(self, image: np.ndarray) -> Dict[str, Any]:
        start_time = time.time()
        
        # 转换为灰度图
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        # 检测全黑或全白区域（信号丢失的典型特征）
        black_pixels = np.sum(gray < 10)
        white_pixels = np.sum(gray > 245)
        total_pixels = gray.shape[0] * gray.shape[1]
        
        black_ratio = black_pixels / total_pixels
        white_ratio = white_pixels / total_pixels
        extreme_ratio = black_ratio + white_ratio
        
        # 检测图像方差（信号丢失会导致方差极低）
        image_variance = np.var(gray)
        
        # 检测边缘密度（信号丢失会导致边缘极少）
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / total_pixels
        
        # 综合评估信号丢失程度
        signal_loss_score = extreme_ratio * 0.5 + (1 - min(image_variance / 1000, 1)) * 0.3 + (1 - edge_density * 10) * 0.2
        
        # 获取阈值
        threshold = self.get_threshold('signal_loss_threshold', 0.3)
        severe_threshold = self.get_threshold('signal_loss_severe', 0.7)
        
        # 计算标准化评分 (0-100)
        if signal_loss_score >= severe_threshold:
            # 严重信号丢失：0-40分
            score = max(0, 40 - ((signal_loss_score - severe_threshold) / (1 - severe_threshold)) * 40)
            status = DiagnosisStatus.CRITICAL
            message = f"严重信号丢失: 信号评分 {signal_loss_score:.2f} (评分: {score:.1f})"
        elif signal_loss_score >= threshold:
            # 轻微信号问题：40-60分
            score = 60 - ((signal_loss_score - threshold) / (severe_threshold - threshold)) * 20
            status = DiagnosisStatus.WARNING
            message = f"信号不稳定: 信号评分 {signal_loss_score:.2f} (评分: {score:.1f})"
        else:
            # 信号正常：60-100分
            score = 100 - (signal_loss_score / threshold) * 40
            score = max(60, min(100, score))
            status = DiagnosisStatus.NORMAL
            message = f"信号正常: 信号评分 {signal_loss_score:.2f} (评分: {score:.1f})"
            
        processing_time = (time.time() - start_time) * 1000
        
        return {
            'status': status,
            'score': float(score),
            'threshold': threshold,
            'message': message,
            'processing_time': processing_time,
            'metrics': {
                'signal_loss_score': float(signal_loss_score),
                'extreme_ratio': float(extreme_ratio),
                'image_variance': float(image_variance),
                'edge_density': float(edge_density),
                'raw_score': float(signal_loss_score),
                'normalized_score': float(score)
            }
        }

class LensDirtyAlgorithm(DiagnosisAlgorithm):
    """镜头脏污检测算法"""
    
    def diagnose(self, image: np.ndarray) -> Dict[str, Any]:
        start_time = time.time()
        
        # 转换为灰度图
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        # 检测模糊区域（脏污会导致局部模糊）
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        blur_map = np.abs(laplacian)
        
        # 计算模糊区域的分布
        blur_threshold = np.percentile(blur_map, 20)  # 最模糊的20%区域
        blur_mask = blur_map < blur_threshold
        blur_ratio = np.sum(blur_mask) / (gray.shape[0] * gray.shape[1])
        
        # 检测亮度不均匀性（脏污会导致亮度分布不均）
        # 使用高斯滤波平滑图像，然后计算与原图的差异
        smoothed = cv2.GaussianBlur(gray, (21, 21), 0)
        brightness_diff = cv2.absdiff(gray, smoothed)
        brightness_variance = np.var(brightness_diff)
        
        # 检测圆形或椭圆形污渍（典型的脏污形状）
        # 使用霍夫圆检测
        circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1, 20,
                                  param1=50, param2=30, minRadius=5, maxRadius=50)
        circle_count = len(circles[0]) if circles is not None else 0
        
        # 综合评估脏污程度
        dirty_score = blur_ratio * 0.4 + (brightness_variance / 1000) * 0.4 + min(circle_count / 10, 1) * 0.2
        
        # 获取阈值
        threshold = self.get_threshold('lens_dirty_threshold', 0.3)
        severe_threshold = self.get_threshold('lens_dirty_severe', 0.6)
        
        # 计算标准化评分 (0-100)
        if dirty_score >= severe_threshold:
            # 严重脏污：0-40分
            score = max(0, 40 - ((dirty_score - severe_threshold) / (1 - severe_threshold)) * 40)
            status = DiagnosisStatus.WARNING
            message = f"镜头严重脏污: 脏污评分 {dirty_score:.2f} (评分: {score:.1f})"
        elif dirty_score >= threshold:
            # 轻微脏污：40-60分
            score = 60 - ((dirty_score - threshold) / (severe_threshold - threshold)) * 20
            status = DiagnosisStatus.WARNING
            message = f"镜头轻微脏污: 脏污评分 {dirty_score:.2f} (评分: {score:.1f})"
        else:
            # 镜头清洁：60-100分
            score = 100 - (dirty_score / threshold) * 40
            score = max(60, min(100, score))
            status = DiagnosisStatus.NORMAL
            message = f"镜头清洁: 脏污评分 {dirty_score:.2f} (评分: {score:.1f})"
            
        processing_time = (time.time() - start_time) * 1000
        
        return {
            'status': status,
            'score': float(score),
            'threshold': threshold,
            'message': message,
            'processing_time': processing_time,
            'metrics': {
                'dirty_score': float(dirty_score),
                'blur_ratio': float(blur_ratio),
                'brightness_variance': float(brightness_variance),
                'circle_count': int(circle_count),
                'raw_score': float(dirty_score),
                'normalized_score': float(score)
            }
        }

class FocusBlurAlgorithm(DiagnosisAlgorithm):
    """焦点模糊检测算法"""
    
    def diagnose(self, image: np.ndarray) -> Dict[str, Any]:
        start_time = time.time()
        
        # 转换为灰度图
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        # 使用多种方法检测焦点模糊
        
        # 1. Laplacian方差（经典的模糊检测方法）
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        laplacian_var = np.var(laplacian)
        
        # 2. Sobel梯度幅值
        grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
        gradient_mean = np.mean(gradient_magnitude)
        
        # 3. 高频成分分析
        f_transform = np.fft.fft2(gray)
        f_shift = np.fft.fftshift(f_transform)
        magnitude_spectrum = np.abs(f_shift)
        
        # 计算高频能量比例
        h, w = gray.shape
        center_h, center_w = h // 2, w // 2
        high_freq_mask = np.zeros((h, w))
        high_freq_mask[center_h-h//4:center_h+h//4, center_w-w//4:center_w+w//4] = 1
        high_freq_energy = np.sum(magnitude_spectrum * (1 - high_freq_mask))
        total_energy = np.sum(magnitude_spectrum)
        high_freq_ratio = high_freq_energy / total_energy if total_energy > 0 else 0
        
        # 综合评估焦点清晰度
        focus_score = (laplacian_var / 1000) * 0.4 + (gradient_mean / 100) * 0.4 + high_freq_ratio * 0.2
        
        # 获取阈值
        min_threshold = self.get_threshold('focus_blur_min', 0.5)
        excellent_threshold = self.get_threshold('focus_blur_excellent', 2.0)
        
        # 计算标准化评分 (0-100)
        if focus_score < min_threshold:
            # 严重失焦：0-60分
            score = max(0, (focus_score / min_threshold) * 60)
            status = DiagnosisStatus.WARNING
            message = f"严重失焦模糊: 焦点评分 {focus_score:.2f} (评分: {score:.1f})"
        elif focus_score >= excellent_threshold:
            # 焦点清晰：95-100分
            score = min(100, 95 + min((focus_score - excellent_threshold) / excellent_threshold, 1) * 5)
            status = DiagnosisStatus.NORMAL
            message = f"焦点非常清晰: 焦点评分 {focus_score:.2f} (评分: {score:.1f})"
        else:
            # 正常范围：60-95分
            score = 60 + ((focus_score - min_threshold) / (excellent_threshold - min_threshold)) * 35
            score = max(60, min(95, score))
            
            if score >= 85:
                status = DiagnosisStatus.NORMAL
                message = f"焦点清晰: 焦点评分 {focus_score:.2f} (评分: {score:.1f})"
            else:
                status = DiagnosisStatus.WARNING
                message = f"轻微失焦: 焦点评分 {focus_score:.2f} (评分: {score:.1f})"
            
        processing_time = (time.time() - start_time) * 1000
        
        return {
            'status': status,
            'score': float(score),
            'threshold': min_threshold,
            'message': message,
            'processing_time': processing_time,
            'metrics': {
                'focus_score': float(focus_score),
                'laplacian_var': float(laplacian_var),
                'gradient_mean': float(gradient_mean),
                'high_freq_ratio': float(high_freq_ratio),
                'raw_score': float(focus_score),
                'normalized_score': float(score)
            }
        }

# 算法注册表
ALGORITHM_REGISTRY = {
    DiagnosisType.BRIGHTNESS: BrightnessAlgorithm,
    DiagnosisType.CLARITY: ClarityAlgorithm,
    DiagnosisType.BLUE_SCREEN: BlueScreenAlgorithm,
    DiagnosisType.NOISE: NoiseAlgorithm,
    DiagnosisType.CONTRAST: ContrastAlgorithm,
    DiagnosisType.SHAKE: ShakeAlgorithm,
    DiagnosisType.FREEZE: FreezeAlgorithm,
    DiagnosisType.COLOR_CAST: ColorCastAlgorithm,
    DiagnosisType.OCCLUSION: OcclusionAlgorithm,
    DiagnosisType.MOSAIC: MosaicAlgorithm,
    DiagnosisType.FLOWER_SCREEN: FlowerScreenAlgorithm,
    DiagnosisType.SIGNAL_LOSS: SignalLossAlgorithm,
    DiagnosisType.LENS_DIRTY: LensDirtyAlgorithm,
    DiagnosisType.FOCUS_BLUR: FocusBlurAlgorithm,
}

def get_algorithm(diagnosis_type: DiagnosisType, config: Dict[str, Any] = None) -> DiagnosisAlgorithm:
    """获取诊断算法实例"""
    algorithm_class = ALGORITHM_REGISTRY.get(diagnosis_type)
    if not algorithm_class:
        raise ValueError(f"不支持的诊断类型: {diagnosis_type}")
    return algorithm_class(config)