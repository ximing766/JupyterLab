---
name: diagram-generator
description: Generates architecture, framework, or flow diagrams using Graphviz Python library. Invoke when user asks to draw diagrams or visualize system architecture.
---

# Graphviz Diagram Generator

## 描述
此技能用于根据用户描述，自动生成 Python 脚本并调用 Graphviz 库绘制各类架构图、流程图或框架图。

## 使用场景
当用户请求"画一个架构图"、"生成流程图"、"可视化这个系统"或明确要求使用 Graphviz 绘图时触发。

## 指令

1.  **分析需求**：
    *   理解用户想要绘制的图表类型（有向图 Digraph 或 无向图 Graph）。
    *   识别图中的关键节点（Nodes）、边（Edges）、子图/聚类（Subgraphs/Clusters）。
    *   确定图表的层级结构。

2.  **生成 Python 脚本**：
    *   创建一个新的 Python 脚本（例如 `draw_diagram.py`，或根据内容命名的文件）。
    *   **必须包含的代码规范**：
        *   导入库：`from graphviz import Digraph` (或 Graph)。
        *   **字体设置**：为了避免乱码和保证美观，必须将所有组件的字体设置为 `Helvetica` 或通用英文等宽字体。
            ```python
            dot.attr('node', fontname='Helvetica')
            dot.attr('edge', fontname='Helvetica')
            dot.attr('graph', fontname='Helvetica')
            ```
        *   **异常处理**：使用 `try-except` 块捕获渲染过程中的错误。
        *   **输出**：调用 `.render()` 方法生成图片（通常为 PNG），并设置 `cleanup=True` 清理中间文件。
        *   **打印结果**：脚本执行成功后，打印生成文件的绝对路径。

3.  **执行脚本**：
    *   使用 `RunCommand` 工具在 PowerShell 中执行生成的脚本：`python <script_name>`。
    *   **注意**：假设环境中已安装 `graphviz` 库和系统对应的 Graphviz 可执行文件。

4.  **验证与反馈**：
    *   检查脚本执行的输出。
    *   如果成功，告知用户图片生成的位置。
    *   如果失败（如缺少库或 Graphviz 未安装），尝试修复或提示用户。

## 示例代码结构

```python
from graphviz import Digraph
import os

def draw():
    dot = Digraph(comment='Diagram Title', format='png')
    dot.attr(rankdir='TB') # TB: Top-Bottom, LR: Left-Right
    
    # 关键：设置字体以支持英文和避免乱码
    dot.attr('node', fontname='Helvetica')
    dot.attr('edge', fontname='Helvetica')
    dot.attr('graph', fontname='Helvetica')

    # 定义节点和边
    dot.node('A', 'Node A')
    dot.node('B', 'Node B')
    dot.edge('A', 'B', label='Connection')

    try:
        output_path = dot.render('output_filename', directory='.', cleanup=True)
        print(f"Diagram generated at: {os.path.abspath(output_path)}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    draw()
```
