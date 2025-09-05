#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
门禁闸机状态识别系统
使用MobileNetV2进行迁移学习的二分类任务
"""

import os
import cv2
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping
import matplotlib.pyplot as plt
import matplotlib
# 设置matplotlib中文字体支持
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False
import json
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GateClassifierConfig:
    """门禁闸机分类器配置类"""
    
    def __init__(self):
        # 基本配置
        self.dataset_path = "dataset"
        self.img_height = 224
        self.img_width = 224
        self.input_shape = (224, 224, 3)
        self.batch_size = 32
        self.epochs = 50
        self.validation_split = 0.15  # 减少验证集比例，增加训练数据
        
        # 学习率配置
        self.learning_rate = 0.0005  # 降低学习率，提高稳定性
        
        # 类别配置
        self.num_classes = 2
        self.class_names = ['closed', 'open']
        
        # 模型保存
        self.model_save_path = "models"
        self.checkpoint_path = os.path.join(self.model_save_path, "best_model.h5")
        
    def load_config(self, filepath):
        """从JSON文件加载配置"""
        with open(filepath, 'r', encoding='utf-8') as f:
            config_dict = json.load(f)
        for k, v in config_dict.items():
            if hasattr(self, k):
                setattr(self, k, v)

class GateClassifier:
    """门禁闸机状态分类器"""
    
    def __init__(self, config):
        self.config = config
        self.model = None
        self.history = None
        
        # 创建必要的目录
        os.makedirs(self.config.model_save_path, exist_ok=True)
        
    def create_model(self):
        """创建模型 - 冻结基础模型，只训练分类头"""
        
        # 创建基础模型
        base_model = MobileNetV2(
            input_shape=self.config.input_shape,
            include_top=False,
            weights='imagenet'
        )
        
        base_model.trainable = True

        # 然后冻结前面的层（例如前100层）
        for layer in base_model.layers[:100]:
            layer.trainable = False
        
        # 构建完整模型
        inputs = keras.Input(shape=self.config.input_shape)
        x = keras.applications.mobilenet_v2.preprocess_input(inputs)
        x = base_model(x, training=True)
        x = layers.GlobalAveragePooling2D()(x)
        x = layers.Dropout(0.2)(x)
        
        # 输出层
        if self.config.num_classes == 2:
            outputs = layers.Dense(1, activation='sigmoid')(x)
            loss = 'binary_crossentropy'
        else:
            outputs = layers.Dense(self.config.num_classes, activation='softmax')(x)
            loss = 'categorical_crossentropy'
        
        self.model = keras.Model(inputs, outputs)
        
        # 编译模型
        self.model.compile(
            optimizer=Adam(learning_rate=self.config.learning_rate),
            loss=loss,
            metrics=['accuracy']
        )
        
        logger.info("模型创建完成")
        logger.info(f"模型参数总数: {self.model.count_params():,}")
        
        return self.model
    
    def prepare_data(self):
        """准备训练数据"""
        
        # 训练数据增强 - 增加更多变换提高泛化能力
        train_datagen = ImageDataGenerator(
            rescale=1./255,
            rotation_range=25,  # 增加旋转范围
            width_shift_range=0.25,  # 增加水平移动
            height_shift_range=0.25,  # 增加垂直移动
            shear_range=0.2,  # 添加剪切变换
            zoom_range=0.2,  # 添加缩放变换
            horizontal_flip=True,
            brightness_range=[0.8, 1.2],  # 添加亮度变化
            fill_mode='nearest',  # 填充模式
            validation_split=self.config.validation_split
        )
        
        # 验证数据（仅重缩放）
        val_datagen = ImageDataGenerator(
            rescale=1./255,
            validation_split=self.config.validation_split
        )
        
        # 训练数据生成器
        train_generator = train_datagen.flow_from_directory(
            self.config.dataset_path,
            target_size=(self.config.img_height, self.config.img_width),
            batch_size=self.config.batch_size,
            class_mode='binary' if self.config.num_classes == 2 else 'categorical',
            subset='training',
            shuffle=True
        )
        
        # 验证数据生成器
        val_generator = val_datagen.flow_from_directory(
            self.config.dataset_path,
            target_size=(self.config.img_height, self.config.img_width),
            batch_size=self.config.batch_size,
            class_mode='binary' if self.config.num_classes == 2 else 'categorical',
            subset='validation',
            shuffle=False
        )
        
        return train_generator, val_generator
    
    def train(self, train_generator, val_generator):
        """训练模型"""
        
        logger.info("开始训练模型...")
        
        # 回调函数
        callbacks = [
            ModelCheckpoint(
                filepath=self.config.checkpoint_path,
                monitor='val_loss',  # 监控验证损失而非准确率
                save_best_only=True,
                verbose=1,
                mode='min'  # 损失越小越好
            ),
            EarlyStopping(
                monitor='val_loss',  # 监控验证损失
                patience=15,  # 增加patience，避免过早停止
                restore_best_weights=True,
                verbose=1,
                mode='min',
                min_delta=0.001  # 最小改善阈值
            )
        ]
        
        # 训练模型
        self.history = self.model.fit(
            train_generator,
            epochs=self.config.epochs,
            validation_data=val_generator,
            callbacks=callbacks,
            verbose=1
        )
        
        logger.info("模型训练完成")
        return self.history
    
    def predict_image(self, image_path):
        """预测单张图像"""
        
        # 加载和预处理图像
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"无法加载图像: {image_path}")
        
        # 预处理
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = cv2.resize(image, (self.config.img_width, self.config.img_height))
        image = image.astype(np.float32) / 255.0
        image_batch = np.expand_dims(image, axis=0)
        
        # 预测
        prediction = self.model.predict(image_batch)
        
        if self.config.num_classes == 2:
            confidence = float(prediction[0][0])
            predicted_class = 1 if confidence > 0.5 else 0
            class_name = self.config.class_names[predicted_class]
        else:
            predicted_class = np.argmax(prediction[0])
            confidence = float(prediction[0][predicted_class])
            class_name = self.config.class_names[predicted_class]
        
        return {
            'class_name': class_name,
            'class_index': predicted_class,
            'confidence': confidence
        }
    
    def save_model(self, filepath=None):
        """保存模型"""
        if filepath is None:
            filepath = os.path.join(
                self.config.model_save_path, 
                f"gate_classifier_{datetime.now().strftime('%Y%m%d_%H%M%S')}.h5"
            )
        
        self.model.save(filepath)
        logger.info(f"模型已保存到: {filepath}")
        return filepath
    
    def load_model(self, filepath):
        """加载模型"""
        self.model = keras.models.load_model(filepath)
        logger.info(f"模型已从 {filepath} 加载")
        return self.model
    
    def plot_training_history(self, save_path=None):
        """绘制训练历史"""
        if self.history is None:
            logger.warning("没有训练历史可绘制")
            return
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
        
        # 准确率
        ax1.plot(self.history.history['accuracy'], label='训练准确率')
        ax1.plot(self.history.history['val_accuracy'], label='验证准确率')
        ax1.set_title('模型准确率')
        ax1.set_xlabel('Epoch')
        ax1.set_ylabel('准确率')
        ax1.legend()
        
        # 损失
        ax2.plot(self.history.history['loss'], label='训练损失')
        ax2.plot(self.history.history['val_loss'], label='验证损失')
        ax2.set_title('模型损失')
        ax2.set_xlabel('Epoch')
        ax2.set_ylabel('损失')
        ax2.legend()
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"训练历史图表已保存到: {save_path}")
        
        plt.show()

def create_dataset_structure():
    """创建数据集目录结构"""
    
    dataset_dirs = [
        "dataset/closed",  # 关门状态图像
        "dataset/open",    # 开门状态图像
    ]
    
    for dir_path in dataset_dirs:
        os.makedirs(dir_path, exist_ok=True)
        logger.info(f"创建目录: {dir_path}")
    
    logger.info("数据集目录结构创建完成")
    logger.info("请将图像文件放入对应的目录中：")
    logger.info("- 关门状态图像 -> dataset/closed/")
    logger.info("- 开门状态图像 -> dataset/open/")

def main():
    """主函数"""
    
    # 创建配置
    config = GateClassifierConfig()
    
    # 如果存在配置文件，加载配置
    config_file = "config.json"
    if os.path.exists(config_file):
        config.load_config(config_file)
        logger.info(f"已加载配置文件: {config_file}")
    
    # 创建分类器
    classifier = GateClassifier(config)
    
    # 检查数据集
    if not os.path.exists(config.dataset_path):
        logger.info("数据集目录不存在，创建目录结构...")
        create_dataset_structure()
        logger.info("请添加训练图像后重新运行")
        return
    
    # 创建模型
    classifier.create_model()
    
    # 准备数据
    train_generator, val_generator = classifier.prepare_data()
    
    logger.info(f"训练样本数: {train_generator.samples}")
    logger.info(f"验证样本数: {val_generator.samples}")
    logger.info(f"类别: {train_generator.class_indices}")
    
    # 训练模型
    classifier.train(train_generator, val_generator)
    
    # 保存模型
    model_path = classifier.save_model()
    
    # 绘制训练历史
    classifier.plot_training_history("training_history.png")
    
    logger.info("训练完成！")
    logger.info("=" * 60)
    logger.info("模型文件说明:")
    logger.info(f"1. 最佳模型 (best_model.h5): {config.checkpoint_path}")
    logger.info("   - 基于验证集损失最低的epoch保存")
    logger.info("   - 推荐用于实际预测")
    logger.info(f"2. 最终模型 (时间戳命名): {model_path}")
    logger.info("   - 训练结束时的模型状态")
    logger.info("   - 可能存在过拟合")
    logger.info("=" * 60)
    
    # 输出训练结果分析
    if classifier.history:
        final_train_acc = classifier.history.history['accuracy'][-1]
        final_val_acc = classifier.history.history['val_accuracy'][-1]
        best_val_acc = max(classifier.history.history['val_accuracy'])
        
        logger.info("训练结果分析:")
        logger.info(f"最终训练准确率: {final_train_acc:.4f}")
        logger.info(f"最终验证准确率: {final_val_acc:.4f}")
        logger.info(f"最佳验证准确率: {best_val_acc:.4f}")
        
        if final_train_acc - final_val_acc > 0.2:
            logger.warning("检测到过拟合！建议:")
            logger.warning("1. 增加数据增强")
            logger.warning("2. 添加更多训练数据")
            logger.warning("3. 增加Dropout比例")
        
        if best_val_acc < 0.8:
            logger.warning("验证准确率较低，可能原因:")
            logger.warning("1. 数据集质量问题 - 检查标注是否正确")
            logger.warning("2. 数据集太小 - 当前约440张图片可能不足")
            logger.warning("3. 类别不平衡 - 检查两类样本数量")
            logger.warning("4. 图片质量差异大 - 统一拍摄条件")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()