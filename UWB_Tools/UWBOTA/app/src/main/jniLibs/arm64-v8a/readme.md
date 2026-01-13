# Android JNI 集成实现文档

本文档将 NDK 编译 C 库 (`librssi_dir.so`) 集成到 Android 项目，并通过 JNI 封装供上层 Kotlin/Java 代码调用。

## 1. 整体架构

整个调用链路如下：
`App` -> `JNI Wrapper (native-lib.cpp)` -> `librssi_dir.so`

*   **原始 C 库**: `librssi_dir.so` (预编译库，包含核心算法)
*   **JNI 封装层**: `libuwbota_jni.so` (由 `native-lib.cpp` 编译而来，作为桥梁)
*   **应用层**: `RssiDirNative.kt` (Kotlin 接口)

## 2. 文件目录结构

核心文件及其作用：

```text
app/src/main/
├── cpp/
│   ├── include/
│   │   └── rssi_dir.h          # 原始 C 库的头文件 (API 定义)
│   ├── native-lib.cpp          # JNI 实现代码 (C++ source)
│   └── CMakeLists.txt          # 构建脚本 (链接配置)
├── jniLibs/
│   └── arm64-v8a/
│       └── librssi_dir.so      # 预编译的原始 C 动态库
└── java/com/example/uwbota/
    └── RssiDirNative.kt        # Kotlin 层的调用接口
```

## 3. 实现步骤详解

### 第一步：导入预编译库 (Prebuilt Library)

将编译好的 `.so` 文件放置在 `jniLibs` 目录下对应的架构文件夹中（如 `arm64-v8a`），并将对应的头文件放入 `cpp/include`。

*   **库文件**: `app/src/main/jniLibs/arm64-v8a/librssi_dir.so`
*   **头文件**: `app/src/main/cpp/include/rssi_dir.h`

### 第二步：配置 CMake 构建脚本

在 `CMakeLists.txt` 中，我们需要做两件事：
1.  **导入**外部的 `librssi_dir.so`。
2.  **编译**我们自己的 `native-lib.cpp` 并**链接**到该库。



### 第三步：实现 JNI 封装层 (C++)

在 `native-lib.cpp` 中，我们需要引入头文件，并按照 JNI 的命名规范（`Java_包名_类名_方法名`）编写函数。这些函数负责接收 Java 参数，调用底层 C 函数，并返回结果。

### 第四步：定义 Kotlin 接口

在 Kotlin 层创建一个 `object`（单例），加载生成的 JNI 库，并声明 `external` 方法。

## 4. 运行时流程

1.  App 启动，访问 `RssiDirNative` 类。
2.  `init` 代码块执行，调用 `System.loadLibrary("uwbota_jni")`。
3.  Android 系统加载 `libuwbota_jni.so`。
4.  由于 `libuwbota_jni.so` 依赖于 `librssi_dir.so`（在 CMake 中链接），系统也会自动加载 `librssi_dir.so`。
5.  当调用 `RssiDirNative.estimateAngle()` 时，JNI 环境调用 `native-lib.cpp` 中的对应函数，最终执行核心算法。