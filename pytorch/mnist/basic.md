# MNIST + PyTorch 入门指南（配套 main.py）

本文配套代码：
- e:\Work\Python\JupyterLab\pytorch\mnist\main.py

目标：
- 在 Windows PC 上训练一个 MNIST 分类模型（CNN）
- 自动下载 MNIST 数据集
- 保存 PyTorch 权重（.pt）
- 导出 ONNX（为 Jetson / TensorRT 做准备）

---

## 1. 你现在这份 main.py 在做什么？

整体流程可以理解为 7 步：

1) 定义模型结构（class Net）
2) 定义训练步骤（train）
3) 定义测试/评估步骤（test）
4) 选择设备（CPU / GPU）
5) 定义数据预处理（transform）
6) 下载并加载数据（datasets.MNIST + DataLoader）
7) 训练若干轮（epochs）→ 保存 .pt → 导出 .onnx

---

## 2. 核心概念速览

### 2.1 Tensor（张量）
PyTorch 的数据对象是 Tensor，可以理解为“带 GPU 支持的多维数组”。

- MNIST 单张图片形状是 `[1, 28, 28]`
  - 第一个 `1` 是通道数（灰度图）
- 一个 batch 的形状是 `[batch_size, 1, 28, 28]`

### 2.2 Module（模型）
模型写成 `nn.Module` 的子类，包含：
- `__init__()`：声明层（conv、fc、dropout）
- `forward()`：定义数据如何从输入流向输出（前向计算）

### 2.3 Loss（损失函数）
损失用于衡量预测和真实标签差距；训练就是让损失下降。

你这里用的是：
- `F.log_softmax(...)` + `F.nll_loss(...)`
这俩是配套使用的组合（对数概率 + 负对数似然）。

等价替代写法：
- 不用 `log_softmax`
- 直接输出 logits（未归一化分数）
- 用 `nn.CrossEntropyLoss()`（内部自带 softmax）

### 2.4 Optimizer（优化器）
优化器根据梯度更新模型参数（权重）：
- 典型步骤：`loss.backward()` → `optimizer.step()`

你这里用的是 `Adadelta`，属于自适应学习率优化器。

### 2.5 Scheduler（学习率调度器）
训练过程中动态调整学习率，常用来后期“更稳”收敛。
这里用：
- `StepLR(optimizer, step_size=1, gamma=0.7)`
含义是：每个 epoch 后把学习率乘以 `0.7`。

---

## 3. 逐段解释 main.py

### 3.1 设备选择（CPU / GPU）
代码逻辑是：

- `torch.cuda.is_available()`：检查系统是否能用 CUDA
- `device = torch.device("cuda" if use_cuda else "cpu")`：选择设备
- 后面把模型/数据都 `.to(device)` 放到同一设备上

你看到输出 `Using device: cpu` 说明当前没用到 GPU（或没装 CUDA 版 torch）。

---

### 3.2 数据预处理 transform

```python
transforms.ToTensor()
transforms.Normalize((0.1307,), (0.3081,))
```

- `ToTensor()`：
  - 把 PIL 图片 / numpy 转成 Tensor
  - 同时把像素从 `[0..255]` 归一化到 `[0..1]`

- `Normalize(mean, std)`：
  - 标准化：`(x - mean) / std`
  - 这里的均值/方差是 MNIST 常用的经验值

为什么要 Normalize？
- 训练更稳定、更快收敛（梯度尺度更统一）

---

### 3.3 下载与加载数据集

```python
datasets.MNIST('./data', train=True, download=True, transform=transform)
```

- 数据会被下载到 `./data` 目录（相对 main.py 运行目录）
- MNIST 原始格式是 IDX 二进制（不是一张张 png），这是正常的
- `download=True`：如果已经存在会跳过，不会重复下载

DataLoader 做了什么？
- 按 batch 取数据
- `shuffle=True`（你这里在 CUDA 情况下启用）会打乱数据顺序（更利于训练）

---

### 3.4 模型结构 Net（CNN）

你的模型大致是：

- Conv(1→32, 3x3) + ReLU
- Conv(32→64, 3x3) + ReLU
- MaxPool(2x2)
- Dropout(0.25)
- Flatten
- FC(9216→128) + ReLU
- Dropout(0.5)
- FC(128→10)
- log_softmax 输出 10 类的对数概率

为什么最后是 10？
- MNIST 标签是 0~9 十个类别

---

### 3.5 训练循环 train()

训练循环的固定模板就是：

1) `model.train()`：进入训练模式
2) 遍历 batch：
   - 把数据放到 device
   - 清梯度 `optimizer.zero_grad()`
   - 前向推理 `output = model(data)`
   - 算损失 `loss = ...`
   - 反向传播 `loss.backward()`
   - 参数更新 `optimizer.step()`

为什么需要 `model.train()`？
- Dropout 在训练时要随机丢弃神经元，增强泛化能力
- 在 eval 时 Dropout 要关闭，否则推理结果会随机变化

---

### 3.6 测试循环 test()

测试循环模板：

1) `model.eval()`：进入推理模式（关闭 Dropout 等）
2) `with torch.no_grad()`：关闭梯度计算（更快更省内存）
3) 遍历测试集：
   - forward
   - 累计 loss
   - 统计准确率

为什么测试集要 `no_grad()`？
- 测试不需要更新参数
- 关闭梯度能明显加速，并减少内存占用

---

### 3.7 保存 .pt 与导出 ONNX

#### 保存 .pt（权重）
```python
torch.save(model.state_dict(), "./mnist_model.pt")
```

这是推荐方式：只保存权重，不保存整个 Python 对象。

在 Jetson 上加载方式一般是：
- 写同样的 `Net()` 结构
- `model.load_state_dict(torch.load("mnist_model.pt", map_location=device))`

#### 导出 ONNX（给 TensorRT 用）
```python
torch.onnx.export(model, dummy_input, "./mnist_model.onnx", ...)
```

- dummy_input 用来“跑一遍 forward”，帮助导出图结构
- `dynamic_axes` 表示 batch 维度可变（TensorRT 也更通用）

你之前报错 `onnxscript` 缺失：
- 解决：安装依赖
  - `pip install onnx onnxscript`

---

## 4. 为什么 PyTorch 要手写训练 step？有没有更高层？

PyTorch 原生是偏底层的，手写 step 的好处：
- 训练过程完全可控
- 方便做自定义（多 loss、梯度裁剪、混合精度、自定义日志等）
- 导出/部署更透明

如果你想要 Keras 那种“高层训练”，可以用：
- PyTorch Lightning（非常常见）
- 或者自己封装 Trainer 类

但对于“训练→导出 ONNX→TensorRT”这种部署链路，原生写法往往更稳。

---

## 5. Windows 训练的 .pt 直接拷贝到 Jetson 可以吗？

结论：
- 拷贝 `.pt` 权重文件本身没问题
- 但 Jetson 上必须有同样的模型结构代码（Net），才能 load_state_dict
- 更推荐拷贝 `.onnx`（跨平台、与 TensorRT 直接对接）

---

## 6. Jetson + TensorRT 端侧部署推荐流程（概念版）

1) PC 训练得到：
- mnist_model.pt
- mnist_model.onnx

2) 把 mnist_model.onnx 拷到 Jetson

3) Jetson 上用 TensorRT 转 engine（示例）：
- trtexec --onnx=mnist_model.onnx --saveEngine=mnist_model.engine --fp16

4) Jetson 推理（两条路线）：
- Python + TensorRT API（更灵活）
- C++ + TensorRT API（性能更极致）

---

## 7. 常见问题排查

### 7.1 再次运行会不会重复下载？
不会。download=True 会先检查本地文件是否存在。

### 7.2 为什么 data 目录没有图片？
MNIST 官方就是 IDX 二进制格式，torchvision 会自动解析成 Tensor。

### 7.3 ONNX 导出失败（onnxscript 缺失）
安装：
- pip install onnx onnxscript

---

## 8. 下一步建议（你想做“全流程部署”）

建议你接下来做三件事：
1) main.py 增加 “导出前先 model.eval()”，让导出图更像推理状态
2) 写一个 infer.py：加载 .pt 做单张推理（验证权重文件可用）
3) Jetson 侧：转 TensorRT + 写推理脚本跑 1 张图验证一致性

如果你继续推进 Jetson 端的 TensorRT 全流程（含推理代码），我可以按你的 Jetson 型号/JetPack 版本把命令和代码一步步配齐。