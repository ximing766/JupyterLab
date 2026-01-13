#!/bin/bash

# 检查是否安装了 docker
if ! command -v docker &> /dev/null; then
    echo "错误: 未找到 Docker。"
    echo "Python (Nuitka) 的跨平台编译（Standalone模式）必须在目标架构的系统上运行，"
    echo "或者使用 Docker + QEMU 模拟目标架构环境。"
    echo "单纯使用交叉编译工具链 (gcc-arm...) 无法正确打包 Python 解释器和依赖库。"
    echo "请安装 Docker 和 qemu-user-static:"
    echo "  sudo apt install docker.io qemu-user-static"
    exit 1
fi

# 启用 QEMU 模拟器以支持多架构构建
echo "正在启用 QEMU user static..."
docker run --rm --privileged multiarch/qemu-user-static --reset -p yes > /dev/null 2>&1

echo "--------------------------------------------------------"
echo "步骤 1/2: 构建 ARMv7 编译环境镜像..."
echo "--------------------------------------------------------"

# 构建针对 linux/arm/v7 平台的 Docker 镜像
docker build --platform linux/arm/v7 -t ota_tool_builder_arm -f Dockerfile.arm .

if [ $? -ne 0 ]; then
    echo "镜像构建失败!"
    exit 1
fi

echo "--------------------------------------------------------"
echo "步骤 2/2: 在 ARMv7 容器中运行 Nuitka 编译..."
echo "--------------------------------------------------------"

# 运行容器进行编译
# -v "$(pwd):/app": 将当前目录挂载到容器的 /app
# --platform linux/arm/v7: 指定容器运行架构为 ARMv7
docker run --rm --platform linux/arm/v7 \
    -v "$(pwd):/app" \
    ota_tool_builder_arm \
    python3 -m nuitka \
        --standalone \
        --onefile \
        --output-dir=output_linux_arm \
        --output-filename=ota_tool_cli_arm \
        --include-package=serial \
        --remove-output \
        --assume-yes-for-downloads \
        --python-flag=-OO \
        OTA_Flash_Tool_CLI.py

if [ $? -eq 0 ]; then
    echo "--------------------------------------------------------"
    echo "编译成功!"
    echo "ARM 可执行文件位置: output_linux_arm/ota_tool_cli_arm.bin"
    echo "注意: 请在目标 ARM 设备上运行测试。"
    echo "--------------------------------------------------------"
else
    echo "编译失败!"
fi
