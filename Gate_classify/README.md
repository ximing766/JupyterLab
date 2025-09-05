# 闸机状态识别系统

基于MobileNetV2的闸机开关状态识别系统，能够自动识别闸机的开门和关门状态。

## 项目特性

- 🎯 **高精度识别**: 基于深度学习的图像分类
- 🚀 **轻量级设计**: 适合边缘设备部署
- 📊 **训练可视化**: 支持训练过程监控
- 🔧 **简单易用**: 配置简单，易于使用

## 技术架构

### 模型设计
- **基础模型**: MobileNetV2 (ImageNet预训练)
- **输入尺寸**: 224x224x3
- **分类方式**: 二分类 (开门/关门)
- **训练策略**: 迁移学习，冻结基础模型层

### 图像处理
1. **尺寸调整**: 自动调整到224x224像素
2. **数据增强**: 旋转、平移、翻转等增强技术
3. **归一化**: 像素值归一化到[0,1]范围

## 数据集准备

### 数据集结构

```
dataset/
├── closed/          # 关门状态图像
│   ├── close1.jpg
│   ├── close2.jpg
│   └── ...
└── open/            # 开门状态图像
    ├── open1.jpg
    ├── open2.jpg
    └── ...
```

### 数据要求

- **数量**: 每类建议200张以上
- **格式**: JPG, PNG
- **质量**: 清晰，避免模糊
- **多样性**: 不同光照、角度条件

### 数据扩充

使用提供的数据扩充脚本可以从少量原始图片生成更多训练数据：

```bash
python data_augmentation.py
```

## 安装和使用

### 环境要求

- Python 3.8+
- 依赖包见 `pyproject.toml`

### 安装依赖

```bash
uv sync
```

### 使用方法

#### 1. 数据扩充（可选）

```bash
python data_augmentation.py
```

#### 2. 训练模型

```bash
python main.py
```

#### 3. 模型预测

```python
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
import numpy as np

# 加载模型
model = load_model('gate_classifier.h5')

# 预测图像
img = image.load_img('test.jpg', target_size=(224, 224))
img_array = image.img_to_array(img)
img_array = np.expand_dims(img_array, axis=0) / 255.0

prediction = model.predict(img_array)
print("开门" if prediction[0][0] > 0.5 else "关门")
```

## 性能优化

### 1. 模型优化

- **量化**: 使用TensorFlow Lite进行INT8量化
- **剪枝**: 移除不重要的连接以减少模型大小
- **知识蒸馏**: 使用更小的学生模型学习大模型知识

### 2. 推理优化

- **批处理**: 多图像批量推理提高吞吐量
- **预处理优化**: 使用OpenCV的优化函数
- **内存管理**: 及时释放不需要的变量

### 3. 硬件加速

- **GPU加速**: 使用CUDA或OpenCL
- **NPU加速**: 树莓派AI加速器
- **边缘TPU**: Google Coral加速器

## 故障排除

### 常见问题

1. **摄像头无法识别**
   ```bash
   # 检查摄像头连接
   libcamera-hello --list-cameras
   
   # 检查配置文件
   cat /boot/firmware/config.txt | grep camera
   ```

2. **内存不足**
   ```python
   # 减少批次大小
   config.batch_size = 16
   
   # 使用混合精度训练
   policy = tf.keras.mixed_precision.Policy('mixed_float16')
   tf.keras.mixed_precision.set_global_policy(policy)
   ```

3. **训练过慢**
   ```python
   # 使用更小的输入尺寸
   config.img_height = 160
   config.img_width = 160
   
   # 减少数据增强
   config.rotation_range = 10
   ```

4. **过拟合问题**
   ```python
   # 增加正则化
   config.dropout_rate = 0.3
   config.l2_regularization = 0.001
   
   # 增加数据增强
   config.rotation_range = 30
   config.zoom_range = 0.3
   ```

## 扩展功能

### 1. 多类别分类

```python
# 修改配置支持更多状态
config.num_classes = 4
config.class_names = ['closed', 'opening', 'open', 'closing']
```

### 2. 实时监控

```python
# 添加实时监控功能
def real_time_monitoring():
    while True:
        result = classifier.predict_from_camera()
        if result['confidence'] > 0.9:
            print(f"检测到状态变化: {result['class_name']}")
            # 触发相应动作
        time.sleep(0.1)
```

### 3. 数据记录

```python
# 添加预测结果记录
import sqlite3
from datetime import datetime

def log_prediction(result):
    conn = sqlite3.connect('gate_log.db')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO predictions (timestamp, class_name, confidence) VALUES (?, ?, ?)",
        (datetime.now(), result['class_name'], result['confidence'])
    )
    conn.commit()
    conn.close()
```

## 技术细节补充

### 未考虑的重要方面

1. **光照适应性**
   - 添加光照检测和自适应调整
   - 支持夜间红外模式
   - 动态白平衡调整

2. **边缘部署优化**
   - 模型量化和压缩
   - 推理延迟优化
   - 功耗管理

3. **系统集成**
   - 与门禁控制系统的接口
   - 网络通信协议
   - 远程监控和管理

4. **安全性考虑**
   - 防止对抗攻击
   - 数据加密传输
   - 访问权限控制

5. **可靠性保障**
   - 异常检测和恢复
   - 系统健康监控
   - 自动重启机制

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request来改进项目。

## 联系方式

如有问题或建议，请通过Issue联系。