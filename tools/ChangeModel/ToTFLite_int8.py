from pathlib import Path
import tensorflow as tf
import numpy as np # 导入 numpy
from sklearn.datasets import make_classification # 导入 make_classification
from sklearn.model_selection import train_test_split # 导入 train_test_split

current_dir = Path(__file__).parent
model_path = current_dir / 'model/simple_binary_dnn_model.keras'
print(f"模型路径: {model_path}")

# 重新生成用于代表性数据集的数据 (与 main.py 中一致)
X, y = make_classification(n_samples=1000, n_features=20, n_informative=10, n_redundant=10, n_classes=2, random_state=42)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = tf.keras.models.load_model(model_path)

# 创建 TFLite 转换器
converter = tf.lite.TFLiteConverter.from_keras_model(model)

# (可选) 应用优化，例如量化，这对于嵌入式设备非常重要
converter.optimizations = [tf.lite.Optimize.DEFAULT]
converter.target_spec.supported_types = [tf.int8] # 或者 tf.int8 | tf.uint8 | tf.float16

# 定义代表性数据集生成器
# 这个生成器函数必须返回一个迭代器，每次迭代产生一个输入数据的批次
def representative_data_gen():
  # 为了演示，我们只使用训练集的前100个样本作为代表性数据集
  # 修正：直接迭代前100个样本
  for input_value in X_train[:100].astype(np.float32):
    # yield 的数据必须是列表或元组，其中每个元素对应模型的一个输入
    yield [input_value.reshape(1, -1)] # 确保形状与模型输入层匹配

# 设置代表性数据集
converter.representative_dataset = representative_data_gen

tflite_model = converter.convert()

model_path = current_dir / 'model/int8_model.tflite'
with open(model_path, 'wb') as f:
    f.write(tflite_model)

print(f"模型已转换为 TFLite int8 格式并保存为 {model_path}")