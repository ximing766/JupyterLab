from pathlib import Path
import tensorflow as tf

current_dir = Path(__file__).parent
model_path = current_dir / 'model/simple_binary_dnn_model.keras'
print(f"模型路径: {model_path}")
model = tf.keras.models.load_model(model_path)

# 创建 TFLite 转换器
converter = tf.lite.TFLiteConverter.from_keras_model(model)

# (可选) 应用优化，例如量化，这对于嵌入式设备非常重要
converter.optimizations = [tf.lite.Optimize.DEFAULT]
converter.target_spec.supported_types = [tf.float16] # 或者 tf.int8 | tf.uint8 | tf.float16

tflite_model = converter.convert()

model_path = current_dir / 'model/float16_model.tflite'
with open(model_path, 'wb') as f:
    f.write(tflite_model)

print("模型已转换为 TFLite 格式并保存为 simple_binary_dnn_model.tflite")