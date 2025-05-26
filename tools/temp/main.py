import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.datasets import make_classification
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
import os

# 1. 生成简单数据集
# 使用 make_classification 生成一个包含1000个样本，20个特征（其中10个是信息特征），2个类别的数据集
X, y = make_classification(n_samples=1000, n_features=20, n_informative=10, n_redundant=10, n_classes=2, random_state=42)

# 2. 划分训练集和测试集
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 3. 构建简单的DNN模型
# 模型包含一个输入层，一个隐藏层和一个输出层
model = Sequential([
    Dense(32, activation='relu', input_shape=(X_train.shape[1],)), # 输入层和隐藏层
    Dense(1, activation='sigmoid') # 输出层，二分类使用sigmoid激活函数
])

# 4. 编译模型
# 使用Adam优化器，二分类使用binary_crossentropy损失函数，评估指标为准确率
model.compile(optimizer='adam',
              loss='binary_crossentropy',
              metrics=['accuracy'])

# 打印模型结构和参数量
model.summary()

# 5. 训练模型
print("\n开始训练模型...")
history = model.fit(X_train, y_train, epochs=10, batch_size=32, validation_split=0.1, verbose=1)
print("模型训练完成。")

# 6. 评估模型
loss, accuracy = model.evaluate(X_test, y_test, verbose=0)
print(f"\n测试集损失 (Loss): {loss:.4f}")
print(f"测试集准确率 (Accuracy): {accuracy:.4f}")

# 7. 进行预测 (可选)
# 预测测试集的前5个样本
predictions = model.predict(X_test[:5])
print("\n前5个测试样本的预测结果 (概率):")
print(predictions.flatten())
# 将概率转换为类别 (大于0.5为类别1，否则为类别0)
predicted_classes = (predictions > 0.5).astype("int32")
print("前5个测试样本的预测类别:")
print(predicted_classes.flatten())
print("前5个测试样本的真实类别:")
print(y_test[:5])


# 8. 保存模型
model_save_path = './simple_binary_dnn_model.keras' # 添加 .keras 扩展名
# 确保保存路径存在
os.makedirs(os.path.dirname(model_save_path), exist_ok=True) # 修改为检查目录是否存在
model.save(model_save_path)
print(f"\n模型已保存到: {model_save_path}")

# 如何加载模型 (示例，实际运行时不需要这部分)
# loaded_model = tf.keras.models.load_model(model_save_path)
# print("\n模型加载成功！")
# loaded_loss, loaded_accuracy = loaded_model.evaluate(X_test, y_test, verbose=0)
# print(f"加载模型在测试集上的准确率: {loaded_accuracy:.4f}")