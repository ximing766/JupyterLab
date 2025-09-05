#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据扩充脚本
用于扩充闸机图像数据集，从现有的20张图片扩充到200张
"""

import os
import numpy as np
from tensorflow.keras.preprocessing.image import ImageDataGenerator, load_img, img_to_array, array_to_img
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataAugmentor:
    def __init__(self, source_dir, target_dir, target_count=200):
        """
        初始化数据扩充器
        
        Args:
            source_dir: 源图片目录
            target_dir: 目标图片目录
            target_count: 目标图片数量
        """
        self.source_dir = Path(source_dir)
        self.target_dir = Path(target_dir)
        self.target_count = target_count
        
        # 创建目标目录
        self.target_dir.mkdir(parents=True, exist_ok=True)
        
        # 数据增强配置
        self.datagen = ImageDataGenerator(
            rotation_range=30,          # 旋转角度
            width_shift_range=0.3,      # 水平移动
            height_shift_range=0.3,     # 垂直移动
            shear_range=0.2,            # 剪切变换
            zoom_range=0.3,             # 缩放
            horizontal_flip=True,       # 水平翻转
            vertical_flip=False,        # 不进行垂直翻转（闸机通常不会上下颠倒）
            brightness_range=[0.7, 1.3], # 亮度调整
            fill_mode='nearest'         # 填充模式
        )
    
    def augment_images(self):
        """
        执行图像扩充
        """
        # 获取源图片列表
        source_images = list(self.source_dir.glob('*.jpg')) + list(self.source_dir.glob('*.png'))
        
        if not source_images:
            logger.error(f"在 {self.source_dir} 中没有找到图片文件")
            return
        
        logger.info(f"找到 {len(source_images)} 张源图片")
        logger.info(f"目标生成 {self.target_count} 张图片")
        
        # 先复制原始图片
        for i, img_path in enumerate(source_images):
            if i >= self.target_count:
                break
            
            # 读取并保存原始图片
            try:
                img = load_img(str(img_path))
                target_path = self.target_dir / f"{img_path.stem}_original{img_path.suffix}"
                img.save(str(target_path))
                logger.info(f"复制原始图片: {target_path.name}")
            except Exception as e:
                logger.error(f"复制图片 {img_path} 时出错: {e}")
        
        # 计算需要生成的增强图片数量
        remaining_count = self.target_count - len(source_images)
        
        if remaining_count <= 0:
            logger.info("原始图片数量已满足目标数量")
            return
        
        # 生成增强图片
        generated_count = 0
        
        while generated_count < remaining_count:
            for img_path in source_images:
                if generated_count >= remaining_count:
                    break
                
                try:
                    # 读取图片
                    img = load_img(str(img_path))
                    img_array = img_to_array(img)
                    
                    # 扩展维度以适应ImageDataGenerator
                    img_array = np.expand_dims(img_array, axis=0)
                    
                    # 生成增强图片
                    aug_iter = self.datagen.flow(
                        img_array,
                        batch_size=1,
                        save_to_dir=str(self.target_dir),
                        save_prefix=f"{img_path.stem}_aug",
                        save_format='jpg'
                    )
                    
                    # 生成一张增强图片
                    next(aug_iter)
                    generated_count += 1
                    
                    if generated_count % 20 == 0:
                        logger.info(f"已生成 {generated_count}/{remaining_count} 张增强图片")
                        
                except Exception as e:
                    logger.error(f"生成增强图片时出错: {e}")
                    continue
        
        logger.info(f"数据扩充完成！总共生成了 {self.target_count} 张图片")
    
    def clean_target_dir(self):
        """
        清理目标目录
        """
        if self.target_dir.exists():
            for file in self.target_dir.glob('*'):
                if file.is_file():
                    file.unlink()
            logger.info(f"已清理目标目录: {self.target_dir}")

def main():
    """
    主函数
    """
    dataset_path = Path("dataset")
    
    # 扩充closed类别
    logger.info("开始扩充 closed 类别图片...")
    closed_augmentor = DataAugmentor(
        source_dir=dataset_path / "closed",
        target_dir=dataset_path / "closed_augmented",
        target_count=200
    )
    closed_augmentor.augment_images()
    
    # 扩充open类别
    logger.info("开始扩充 open 类别图片...")
    open_augmentor = DataAugmentor(
        source_dir=dataset_path / "open",
        target_dir=dataset_path / "open_augmented",
        target_count=200
    )
    open_augmentor.augment_images()
    
    logger.info("所有数据扩充完成！")
    logger.info("请将扩充后的图片移动到对应的原始目录中：")
    logger.info("- dataset/closed_augmented/ -> dataset/closed/")
    logger.info("- dataset/open_augmented/ -> dataset/open/")

if __name__ == "__main__":
    main()