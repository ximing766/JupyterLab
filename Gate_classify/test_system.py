#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
门禁闸机状态识别系统测试脚本
用于验证系统各个组件的功能
"""

import os
import sys
import cv2
import numpy as np
import tensorflow as tf
from main import GateClassifier, GateClassifierConfig
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_basic_dependencies():
    """测试基本依赖"""
    logger.info("测试基本依赖...")
    try:
        logger.info(f"Python版本: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
        logger.info(f"TensorFlow版本: {tf.__version__}")
        logger.info(f"OpenCV版本: {cv2.__version__}")
        logger.info(f"GPU可用: {len(tf.config.list_physical_devices('GPU')) > 0}")
        logger.info("✓ 基本依赖正常")
        return True
    except Exception as e:
        logger.error(f"✗ 基本依赖有问题: {e}")
        return False

def test_model_creation():
    """测试模型创建"""
    logger.info("测试模型创建...")
    try:
        config = GateClassifierConfig()
        classifier = GateClassifier(config)
        
        # 创建模型
        model = classifier.create_model()
        
        # 验证模型
        if model is not None:
            logger.info(f"✓ 模型创建成功")
            logger.info(f"✓ 模型参数数量: {model.count_params():,}")
            
            # 检查基础模型是否冻结
            base_model = model.layers[2]  # MobileNetV2基础模型
            if not base_model.trainable:
                logger.info("✓ 基础模型已正确冻结")
            else:
                logger.warning("⚠️ 基础模型未冻结")
            
            return True
        else:
            logger.error("✗ 模型创建失败")
            return False
    except Exception as e:
        logger.error(f"✗ 模型创建出错: {e}")
        return False

def test_model_prediction():
    """测试模型预测功能"""
    logger.info("测试模型预测功能...")
    try:
        config = GateClassifierConfig()
        classifier = GateClassifier(config)
        
        # 创建模型
        model = classifier.create_model()
        
        # 创建测试数据
        test_input = np.random.random((1, config.img_height, config.img_width, 3))
        
        # 测试预测
        prediction = model.predict(test_input, verbose=0)
        
        if prediction is not None:
            logger.info(f"✓ 模型预测正常")
            logger.info(f"✓ 预测输出形状: {prediction.shape}")
            logger.info(f"✓ 预测值: {prediction[0][0]:.3f}")
            return True
        else:
            logger.error("✗ 模型预测失败")
            return False
    except Exception as e:
        logger.error(f"✗ 模型预测出错: {e}")
        return False

def test_dataset_structure():
    """测试数据集结构"""
    logger.info("测试数据集结构...")
    try:
        config = GateClassifierConfig()
        
        # 检查数据集目录
        if os.path.exists(config.dataset_path):
            logger.info(f"✓ 数据集目录存在: {config.dataset_path}")
            
            # 检查子目录
            subdirs = [d for d in os.listdir(config.dataset_path) 
                      if os.path.isdir(os.path.join(config.dataset_path, d))]
            
            if len(subdirs) >= 2:
                logger.info(f"✓ 找到类别目录: {subdirs}")
                
                # 统计每个类别的图像数量
                total_images = 0
                for subdir in subdirs:
                    subdir_path = os.path.join(config.dataset_path, subdir)
                    image_files = [f for f in os.listdir(subdir_path) 
                                 if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
                    logger.info(f"  {subdir}: {len(image_files)} 张图像")
                    total_images += len(image_files)
                
                if total_images > 0:
                    logger.info(f"✓ 总计 {total_images} 张图像")
                    return True
                else:
                    logger.warning("⚠️ 数据集为空")
                    return False
            else:
                logger.warning(f"✗ 类别目录不足: {subdirs}")
                return False
        else:
            logger.warning(f"✗ 数据集目录不存在: {config.dataset_path}")
            return False
    except Exception as e:
        logger.error(f"✗ 数据集结构检查出错: {e}")
        return False

def test_image_prediction():
    """测试图像预测（如果有数据集）"""
    logger.info("测试图像预测...")
    try:
        config = GateClassifierConfig()
        
        # 查找测试图像
        test_image = None
        if os.path.exists(config.dataset_path):
            for root, dirs, files in os.walk(config.dataset_path):
                for file in files:
                    if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                        test_image = os.path.join(root, file)
                        break
                if test_image:
                    break
        
        if test_image:
            classifier = GateClassifier(config)
            classifier.create_model()
            
            # 测试预测
            result = classifier.predict_image(test_image)
            
            logger.info(f"✓ 图像预测成功")
            logger.info(f"  图像: {os.path.basename(test_image)}")
            logger.info(f"  预测类别: {result['class_name']}")
            logger.info(f"  置信度: {result['confidence']:.3f}")
            return True
        else:
            logger.info("⚠️ 未找到测试图像，跳过此测试")
            return True
    except Exception as e:
        logger.error(f"✗ 图像预测出错: {e}")
        return False

def main():
    """主函数"""
    logger.info("\n" + "="*50)
    logger.info("门禁闸机状态识别系统测试")
    logger.info("="*50)
    
    tests = [
        ("基本依赖", test_basic_dependencies),
        ("模型创建", test_model_creation),
        ("模型预测", test_model_prediction),
        ("数据集结构", test_dataset_structure),
        ("图像预测", test_image_prediction),
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n运行测试: {test_name}")
        logger.info("-" * 30)
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"测试 {test_name} 出现异常: {e}")
            results.append((test_name, False))
    
    # 汇总结果
    logger.info("\n" + "="*50)
    logger.info("测试结果汇总")
    logger.info("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        logger.info(f"{test_name:<15} {status}")
        if result:
            passed += 1
    
    logger.info("-" * 50)
    logger.info(f"总计: {passed}/{total} 项测试通过")
    
    if passed == total:
        logger.info("🎉 所有测试通过！系统准备就绪。")
        logger.info("\n下一步操作:")
        logger.info("1. 准备数据集 - 将图像放入dataset/closed和dataset/open目录")
        logger.info("2. 运行训练 - python main.py")
    else:
        logger.warning(f"⚠️ 有 {total - passed} 项测试失败，请检查相关配置。")
    
    return passed == total

if __name__ == "__main__":
    main()