# -*- coding: utf-8 -*-

# 目标函数：minimize |distance_to_A - target_distance|
# 变量分析：
# - AgentB位置 (x_B, y_B) - 可控变量
# - AgentA位置 (x_A, y_A) - 随机变化，不可控

import sys
import math
import random
import time
from typing import Tuple, List, Optional
from dataclasses import dataclass
from collections import deque

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QFrame, QLabel, QPushButton, QSlider, QCheckBox, QTextEdit,
    QGroupBox, QGridLayout, QSplitter, QSizePolicy, QSpacerItem
)
from PyQt6.QtCore import QTimer, Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect, QPoint
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPainterPath


@dataclass
class Point:
    """二维点类"""
    x: float
    y: float
    
    def distance_to(self, other: 'Point') -> float:
        """计算到另一点的距离"""
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)
    
    def __add__(self, other: 'Point') -> 'Point':
        return Point(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other: 'Point') -> 'Point':
        return Point(self.x - other.x, self.y - other.y)
    
    def __mul__(self, scalar: float) -> 'Point':
        return Point(self.x * scalar, self.y * scalar)


class Agent:
    """智能体基类"""
    def __init__(self, x: float, y: float, color: QColor):
        self.position = Point(x, y)
        self.velocity = Point(0, 0)
        self.color = color
        self.trail: deque = deque(maxlen=50)  # 轨迹记录
        self.trail.append(Point(x, y))
    
    def update_trail(self):
        """更新轨迹"""
        self.trail.append(Point(self.position.x, self.position.y))


class AgentA(Agent):
    """随机移动的智能体A"""
    def __init__(self, x: float, y: float):
        super().__init__(x, y, QColor(255, 182, 193))  # 浅粉色
        self.direction = random.uniform(0, 2 * math.pi)
        self.speed = 3.0
        self.direction_change_prob = 0.05  # 方向改变概率
        self.max_direction_change = math.pi / 6  # 最大方向改变角度
    
    def move(self, bounds: Tuple[int, int]):
        """随机移动"""
        # 随机改变方向
        if random.random() < self.direction_change_prob:
            self.direction += random.uniform(-self.max_direction_change, self.max_direction_change)
        
        # 计算新位置
        new_x = self.position.x + self.speed * math.cos(self.direction)
        new_y = self.position.y + self.speed * math.sin(self.direction)
        
        # 边界检测和反弹
        if new_x <= 15 or new_x >= bounds[0] - 15:
            self.direction = math.pi - self.direction
            new_x = max(15, min(bounds[0] - 15, new_x))
        
        if new_y <= 15 or new_y >= bounds[1] - 15:
            self.direction = -self.direction
            new_y = max(15, min(bounds[1] - 15, new_y))
        
        self.position.x = new_x
        self.position.y = new_y
        self.update_trail()


class AgentB(Agent):
    def __init__(self, x: float, y: float, target_distance: float):
        super().__init__(x, y, QColor(173, 216, 230))  # 浅蓝色
        self.target_distance = target_distance
        self.max_speed = 3.0
        self.distance_history: deque = deque(maxlen=10)  # 距离历史
        self.last_successful_direction = random.uniform(0, 2 * math.pi)  # 初始随机方向
        self.inertia_factor = 0.3  # 惯性因子
        self.last_distance_error = 0.0  # 上次距离误差
        
        # 角度显示属性
        self.optimal_direction_degrees = 0.0
        self.actual_direction_degrees = 0.0
        
        # 算法有效性统计
        self.total_moves = 0
        self.effective_moves = 0
        self.distance_errors = deque(maxlen=100)  # 记录最近100次的距离误差
        self.adjustment_angle = math.pi / 2  # 可调整的角度，默认90度
        
    def calculate_optimal_direction(self, distance_to_a: float) -> float:
        """仅基于距离计算最优移动方向"""
        # 记录当前距离
        self.distance_history.append(distance_to_a)
        
        # 距离误差
        distance_error = distance_to_a - self.target_distance

        # 基于距离变化率的策略
        if len(self.distance_history) >= 2:
            distance_change_rate = self.distance_history[-1] - self.distance_history[-2]
            
            # 梯度方向为负
            if (distance_error > 0 and distance_change_rate > 0) or (distance_error < 0 and distance_change_rate < 0):
                direction_adjustment = self.adjustment_angle  # 使用可调整的角度
                return self.last_successful_direction + direction_adjustment
            
            # 梯度方向为正，继续当前策略
            elif (distance_error > 0 and distance_change_rate < 0) or (distance_error < 0 and distance_change_rate > 0):
                return self.last_successful_direction
        
        # 如果没有足够的历史数据或其他情况，使用当前方向
        return self.last_successful_direction
    
    def move(self, distance_to_a: float, bounds: Tuple[int, int], agent_a_pos=None):
        """仅基于距离信息移动"""
        # 计算距离误差
        distance_error = abs(distance_to_a - self.target_distance)
        
        # 记录距离误差用于统计
        self.distance_errors.append(distance_error)
        
        # 如果距离误差很小，停止移动
        if distance_error < 8:
            return
        
        # 计算最优移动方向
        optimal_direction = self.calculate_optimal_direction(distance_to_a)
        
        # 应用惯性 若向正确方向移动: optimal_direction = actual_direction
        actual_direction = (
            self.inertia_factor * self.last_successful_direction +
            (1 - self.inertia_factor) * optimal_direction
        )
        
        # 保存角度值用于显示（转换为度数）
        self.optimal_direction_degrees = math.degrees(optimal_direction) % 360
        self.actual_direction_degrees = math.degrees(actual_direction) % 360
        
        # 计算移动速度（距离误差越大，速度越快）
        speed_factor = min(1.0, distance_error / 30.0)  # 归一化速度因子
        actual_speed = self.max_speed * (0.4 + 0.6 * speed_factor)  # 最小40%速度
        
        # 计算新位置
        new_x = self.position.x + actual_speed * math.cos(actual_direction)
        new_y = self.position.y + actual_speed * math.sin(actual_direction)
        
        # 边界检测
        new_x = max(15, min(bounds[0] - 15, new_x))
        new_y = max(15, min(bounds[1] - 15, new_y))
        
        self.position.x = new_x
        self.position.y = new_y
        
        self.total_moves += 1
        # 简化的有效性判断：如果距离误差在减小趋势中认为有效
        if len(self.distance_errors) >= 2 and self.distance_errors[-1] < self.distance_errors[-2]:
            self.effective_moves += 1
        
        # 记录距离误差用于平均值计算
        new_distance_error = abs(distance_to_a - self.target_distance)
        self.distance_errors.append(new_distance_error)
        
        # 更新成功方向（这里我们假设移动是成功的，实际应用中可能需要验证）
        self.last_successful_direction = actual_direction
        
        self.update_trail()
    
    def get_effectiveness_ratio(self) -> float:
        """获取有效移动占比"""
        if self.total_moves == 0:
            return 0.0
        return self.effective_moves / self.total_moves
    
    def get_average_distance_error(self) -> float:
        """获取平均距离误差"""
        if len(self.distance_errors) == 0:
            return 0.0
        return sum(self.distance_errors) / len(self.distance_errors)
    
    def reset_statistics(self):
        """重置统计数据"""
        self.total_moves = 0
        self.effective_moves = 0
        self.distance_errors.clear()
    
    def set_adjustment_angle(self, degrees: int):
        """设置调整角度（度数）"""
        self.adjustment_angle = math.radians(degrees)

class SimulationCanvas(QWidget):
    """仿真画布"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(600, 500)
        self.setStyleSheet("background-color: #F8F9FA; border: 1px solid #DEE2E6;")
        
        self.agent_a = AgentA(400, 300)
        self.agent_b = AgentB(300, 300, 100)  # 目标距离100像素
        self.show_trails = True
        self.show_distance_circle = True
        self.show_grid = True
        
    def mousePressEvent(self, event):
        """点击重置A的位置"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.agent_a.position.x = event.position().x()
            self.agent_a.position.y = event.position().y()
            self.agent_a.trail.clear()
            self.agent_a.trail.append(Point(event.position().x(), event.position().y()))
            self.update()
    
    def paintEvent(self, event):
        """绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 绘制网格
        if self.show_grid:
            self.draw_grid(painter)
        
        # 绘制轨迹
        if self.show_trails:
            self.draw_trail(painter, self.agent_a.trail, QColor(255, 182, 193, 150), 3)
            self.draw_trail(painter, self.agent_b.trail, QColor(173, 216, 230, 150), 3)
        
        # 绘制目标距离圆圈
        if self.show_distance_circle:
            self.draw_target_circle(painter)
        
        # 绘制连接线
        self.draw_connection_line(painter)
        
        # 绘制智能体
        self.draw_agent(painter, self.agent_a, "A", 15)
        self.draw_agent(painter, self.agent_b, "B", 12)
        
        # 绘制角度信息
        self.draw_angle_info(painter)
        
        # 距离信息已移至控制面板
    
    def draw_grid(self, painter: QPainter):
        """绘制网格背景"""
        pen = QPen(QColor(230, 243, 255), 1)
        painter.setPen(pen)
        
        width = self.width()
        height = self.height()
        
        # 绘制网格线
        for i in range(0, width, 50):
            painter.drawLine(i, 0, i, height)
        for i in range(0, height, 50):
            painter.drawLine(0, i, width, i)
    
    def draw_agent(self, painter: QPainter, agent: Agent, label: str, size: int):
        """绘制智能体"""
        x, y = int(agent.position.x), int(agent.position.y)
        
        # 绘制阴影
        shadow_brush = QBrush(QColor(0, 0, 0, 50))
        painter.setBrush(shadow_brush)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(x - size + 2, y - size + 2, size * 2, size * 2)
        
        # 绘制主体
        painter.setBrush(QBrush(agent.color))
        painter.setPen(QPen(QColor(70, 130, 180), 3))
        painter.drawEllipse(x - size, y - size, size * 2, size * 2)
        
        # 绘制标签
        painter.setPen(QPen(QColor(47, 79, 79)))
        painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        painter.drawText(x - 5, y + 5, label)
    
    def draw_trail(self, painter: QPainter, trail: deque, color: QColor, width: int):
        """绘制轨迹"""
        if len(trail) < 2:
            return
        
        path = QPainterPath()
        first_point = trail[0]
        path.moveTo(first_point.x, first_point.y)
        
        for point in list(trail)[1:]:
            path.lineTo(point.x, point.y)
        
        # 绘制轨迹阴影
        shadow_pen = QPen(QColor(0, 0, 0, 30), width + 1)
        shadow_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(shadow_pen)
        painter.drawPath(path)
        
        # 绘制主轨迹
        pen = QPen(color, width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawPath(path)
    
    def draw_target_circle(self, painter: QPainter):
        """绘制目标距离圆圈"""
        x, y = int(self.agent_b.position.x), int(self.agent_b.position.y)
        r = int(self.agent_b.target_distance)
        
        # 绘制圆圈阴影
        shadow_pen = QPen(QColor(0, 0, 0, 50), 2)
        painter.setPen(shadow_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(x - r + 2, y - r + 2, r * 2, r * 2)
        
        # 绘制目标圆圈
        pen = QPen(QColor(176, 196, 222), 2)
        pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.drawEllipse(x - r, y - r, r * 2, r * 2)
    
    def draw_connection_line(self, painter: QPainter):
        """绘制连接线"""
        current_distance = self.agent_a.position.distance_to(self.agent_b.position)
        
        # 连接线阴影
        shadow_pen = QPen(QColor(0, 0, 0, 50), 2)
        painter.setPen(shadow_pen)
        painter.drawLine(
            int(self.agent_a.position.x + 1), int(self.agent_a.position.y + 1),
            int(self.agent_b.position.x + 1), int(self.agent_b.position.y + 1)
        )
        
        # 连接线
        line_color = QColor(144, 238, 144) if abs(current_distance - self.agent_b.target_distance) < 10 else QColor(255, 218, 185)
        pen = QPen(line_color, 2)
        painter.setPen(pen)
        painter.drawLine(
            int(self.agent_a.position.x), int(self.agent_a.position.y),
            int(self.agent_b.position.x), int(self.agent_b.position.y)
        )
    
    def draw_angle_info(self, painter: QPainter):
        """绘制角度信息"""
        # 获取AgentB的位置
        b_x, b_y = int(self.agent_b.position.x), int(self.agent_b.position.y)
        
        # 绘制最优方向箭头（绿色）
        optimal_rad = math.radians(self.agent_b.optimal_direction_degrees)
        arrow_length = 40
        optimal_end_x = b_x + arrow_length * math.cos(optimal_rad)
        optimal_end_y = b_y + arrow_length * math.sin(optimal_rad)
        
        # 绘制最优方向箭头
        pen = QPen(QColor(0, 200, 0), 3)
        painter.setPen(pen)
        painter.drawLine(b_x, b_y, int(optimal_end_x), int(optimal_end_y))
        
        # 绘制箭头头部
        self.draw_arrow_head(painter, b_x, b_y, optimal_end_x, optimal_end_y, QColor(0, 200, 0))
        
        # 绘制实际方向箭头（红色）
        actual_rad = math.radians(self.agent_b.actual_direction_degrees)
        actual_end_x = b_x + arrow_length * math.cos(actual_rad)
        actual_end_y = b_y + arrow_length * math.sin(actual_rad)
        
        # 绘制实际方向箭头
        pen = QPen(QColor(200, 0, 0), 3)
        painter.setPen(pen)
        painter.drawLine(b_x, b_y, int(actual_end_x), int(actual_end_y))
        
        # 绘制箭头头部
        self.draw_arrow_head(painter, b_x, b_y, actual_end_x, actual_end_y, QColor(200, 0, 0))
        
        # 绘制角度文本信息
        painter.setPen(QPen(QColor(50, 50, 50)))
        painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        
        # 角度文本 - 固定在左上角
        angle_text_x = 10
        angle_text_y = 30
        
        # 绘制背景矩形
        # text_width = 130
        # text_height = 40
        # painter.fillRect(angle_text_x - 5, angle_text_y - 20, text_width, text_height, QColor(240, 240, 240, 200))
        # painter.setPen(QPen(QColor(180, 180, 180)))
        # painter.drawRect(angle_text_x - 5, angle_text_y - 20, text_width, text_height)
        
        # 绘制角度文本 - 统一使用黑色字体
        painter.setPen(QPen(QColor(50, 50, 50)))
        painter.drawText(angle_text_x, angle_text_y, f"最优: {self.agent_b.optimal_direction_degrees:.1f}°")
        painter.drawText(angle_text_x, angle_text_y + 15, f"实际: {self.agent_b.actual_direction_degrees:.1f}°")
    
    def draw_arrow_head(self, painter: QPainter, start_x: float, start_y: float, end_x: float, end_y: float, color: QColor):
        """绘制箭头头部"""
        # 计算箭头方向
        dx = end_x - start_x
        dy = end_y - start_y
        length = math.sqrt(dx*dx + dy*dy)
        
        if length == 0:
            return
            
        # 单位向量
        ux = dx / length
        uy = dy / length
        
        # 箭头头部大小
        head_length = 8
        head_width = 4
        
        # 计算箭头头部的三个点
        head_x = end_x - head_length * ux
        head_y = end_y - head_length * uy
        
        # 垂直向量
        perp_x = -uy * head_width
        perp_y = ux * head_width
        
        # 箭头头部的三个点
        points = [
            QPoint(int(end_x), int(end_y)),
            QPoint(int(head_x + perp_x), int(head_y + perp_y)),
            QPoint(int(head_x - perp_x), int(head_y - perp_y))
        ]
        
        # 绘制箭头头部
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(color, 2))
        painter.drawPolygon(points)
    
    def get_distance_info(self):
        """获取距离信息"""
        current_distance = self.agent_a.position.distance_to(self.agent_b.position)
        distance_error = abs(current_distance - self.agent_b.target_distance)
        return current_distance, distance_error


class ControlPanel(QWidget):
    """控制面板"""
    panel_toggled = pyqtSignal(bool)  # 面板切换信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(320)
        self.collapsed = False
        self.effectiveness_history = {}  # 存储不同角度的有效性历史
        self.setStyleSheet("""
            QWidget {
                background-color: #FFFFFF;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #FFFFFF;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                background-color: #FFFFFF;
                color: #666666;
            }
            QLabel {
                color: #2F4F4F;
            }
        """)
        
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        
        # 主内容区域
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        
        # 距离信息组
        distance_group = QGroupBox("📊 距离信息")
        distance_layout = QGridLayout(distance_group)
        
        self.current_distance_label = QLabel("当前距离: --")
        self.target_distance_display = QLabel("目标距离: --")
        self.distance_error_label = QLabel("距离误差: --")
        
        distance_layout.addWidget(self.current_distance_label, 0, 0)
        distance_layout.addWidget(self.target_distance_display, 1, 0)
        distance_layout.addWidget(self.distance_error_label, 2, 0)
        
        self.content_layout.addWidget(distance_group)
        
        # 创建可折叠的信息块（包含参数设置）
        self.create_collapsible_groups()
        
        # 控制按钮组
        control_group = QGroupBox("🎮 控制")
        control_layout = QVBoxLayout(control_group)
        
        # 创建水平布局用于放置开始和停止按钮
        button_row = QHBoxLayout()
        
        self.start_btn = QPushButton("▶️ 开始")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #98FB98;
                color: #2F4F4F;
                border: 1px solid #90EE90;
                border-radius: 6px;
                padding: 8px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #90EE90;
            }
        """)
        
        self.stop_btn = QPushButton("⏸️ 停止")
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFB6C1;
                color: #8B0000;
                border: 1px solid #FFA0B4;
                border-radius: 6px;
                padding: 8px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #FFA0B4;
            }
        """)
        
        # 将按钮添加到水平布局
        button_row.addWidget(self.start_btn)
        button_row.addWidget(self.stop_btn)
        
        # 将水平布局添加到控制布局
        control_layout.addLayout(button_row)
        
        self.content_layout.addWidget(control_group)
        
        self.content_layout.addStretch()
        
        layout.addWidget(self.content_widget)
        
        # 初始化历史记录显示
        self.history_text.setPlainText("暂无记录，点击'记录当前有效性'开始记录")
    
    def create_collapsible_groups(self):
        """创建可折叠的信息块组"""
        from PyQt6.QtWidgets import QTextEdit
        
        # 算法有效性信息组（默认展开）
        effectiveness_group = self.create_collapsible_group("📈 算法有效性", collapsed=False)
        effectiveness_layout = QGridLayout()
        
        self.effective_ratio_label = QLabel("有效移动占比: --")
        self.avg_error_label = QLabel("平均距离误差: --")
        
        # 重置统计按钮
        self.reset_stats_btn = QPushButton("重置统计")
        self.reset_stats_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFE4B5;
                color: #8B4513;
                border: 1px solid #DEB887;
                border-radius: 4px;
                padding: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F5DEB3;
            }
        """)
        
        effectiveness_layout.addWidget(self.effective_ratio_label, 0, 0, 1, 2)
        effectiveness_layout.addWidget(self.avg_error_label, 1, 0, 1, 2)
        effectiveness_layout.addWidget(self.reset_stats_btn, 2, 0, 1, 2)
        
        effectiveness_group['content'].setLayout(effectiveness_layout)
        self.content_layout.addWidget(effectiveness_group['widget'])
        
        # 历史有效性记录组
        history_group = self.create_collapsible_group("📊 历史记录", collapsed=False)
        history_layout = QVBoxLayout()
        
        self.history_text = QTextEdit()
        self.history_text.setMaximumHeight(120)
        self.history_text.setReadOnly(True)
        self.history_text.setStyleSheet("""
            QTextEdit {
                background-color: #F8F9FA;
                border: 1px solid #DEE2E6;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
                font-size: 10px;
            }
        """)
        
        # 记录当前设置按钮
        self.record_btn = QPushButton("Record")
        self.record_btn.setStyleSheet("""
            QPushButton {
                background-color: #E6F3FF;
                color: #2F4F4F;
                border: 1px solid #B0C4DE;
                border-radius: 4px;
                padding: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #D1E7FF;
            }
        """)
        
        # 清除记录按钮
        self.clear_history_btn = QPushButton("Clear")
        self.clear_history_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFE6E6;
                color: #8B0000;
                border: 1px solid #FFB6C1;
                border-radius: 4px;
                padding: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FFD1D1;
            }
        """)
        
        history_layout.addWidget(self.history_text)
        
        # 按钮水平布局
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.record_btn)
        button_layout.addWidget(self.clear_history_btn)
        
        # 创建按钮容器
        button_widget = QWidget()
        button_widget.setLayout(button_layout)
        history_layout.addWidget(button_widget)
        
        history_group['content'].setLayout(history_layout)
        self.content_layout.addWidget(history_group['widget'])
        
        # 参数设置组
        param_group = self.create_collapsible_group("⚙️ 参数设置", collapsed=True)
        param_layout = QGridLayout()
        
        # 标签样式
        label_style = """
            QLabel {
                color: #2F4F4F;
                font-weight: bold;
                font-size: 11px;
                padding: 3px;
                background-color: #F0F8FF;
                border-radius: 4px;
                border-left: 3px solid #4682B4;
            }
        """
        
        # 值标签样式
        value_label_style = """
            QLabel {
                color: #2F4F4F;
                font-weight: bold;
                background-color: #E6F3FF;
                border-radius: 4px;
                padding: 3px 6px;
                min-width: 30px;
                text-align: center;
            }
        """
        
        # 目标距离
        distance_label = QLabel("目标距离:")
        distance_label.setStyleSheet(label_style)
        param_layout.addWidget(distance_label, 0, 0)
        self.distance_slider = QSlider(Qt.Orientation.Horizontal)
        self.distance_slider.setRange(50, 200)  # 50-200像素
        self.distance_slider.setValue(100)  # 默认100像素
        self.distance_label = QLabel("100")
        self.distance_label.setStyleSheet(value_label_style)
        param_layout.addWidget(self.distance_slider, 0, 1)
        param_layout.addWidget(self.distance_label, 0, 2)
        
        # B最大速度
        speed_label = QLabel("最大速度:")
        speed_label.setStyleSheet(label_style)
        param_layout.addWidget(speed_label, 1, 0)
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(1, 10)  # 1-10像素/帧
        self.speed_slider.setValue(3)  # 默认3像素/帧
        self.speed_label = QLabel("3")
        self.speed_label.setStyleSheet(value_label_style)
        param_layout.addWidget(self.speed_slider, 1, 1)
        param_layout.addWidget(self.speed_label, 1, 2)
        
        # 惯性因子
        inertia_label = QLabel("惯性因子:")
        inertia_label.setStyleSheet(label_style)
        param_layout.addWidget(inertia_label, 2, 0)
        self.inertia_slider = QSlider(Qt.Orientation.Horizontal)
        self.inertia_slider.setRange(0, 80)  # 0.0-0.8 * 100
        self.inertia_slider.setValue(30)  # 0.3 * 100
        self.inertia_label = QLabel("0.3")
        self.inertia_label.setStyleSheet(value_label_style)
        param_layout.addWidget(self.inertia_slider, 2, 1)
        param_layout.addWidget(self.inertia_label, 2, 2)
        
        # 调整角度选择
        angle_label = QLabel("调整角度:")
        angle_label.setStyleSheet(label_style)
        param_layout.addWidget(angle_label, 3, 0)
        from PyQt6.QtWidgets import QComboBox
        self.angle_combo = QComboBox()
        self.angle_combo.addItems(["30°", "60°", "90°", "120°", "150°", "180°"])
        self.angle_combo.setCurrentText("90°")  # 默认90度
        
        # 美化下拉框样式
        combo_style = """
            QComboBox {
                background-color: #FFFFFF;
                border: 2px solid #B0C4DE;
                border-radius: 6px;
                padding: 5px 10px;
                font-weight: bold;
                color: #2F4F4F;
                min-height: 20px;
            }
            QComboBox:hover {
                border-color: #4682B4;
                background-color: #F0F8FF;
            }
            QComboBox:focus {
                border-color: #4169E1;
                background-color: #E6F3FF;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 25px;
                border-left-width: 1px;
                border-left-color: #B0C4DE;
                border-left-style: solid;
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
                background-color: #E6F3FF;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #4682B4;
                width: 0;
                height: 0;
            }
            QComboBox QAbstractItemView {
                border: 2px solid #B0C4DE;
                border-radius: 6px;
                background-color: #FFFFFF;
                selection-background-color: #E6F3FF;
                selection-color: #2F4F4F;
                padding: 2px;
            }
            QComboBox QAbstractItemView::item {
                height: 25px;
                padding: 3px 8px;
                border-radius: 3px;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #D1E7FF;
            }
        """
        self.angle_combo.setStyleSheet(combo_style)
        param_layout.addWidget(self.angle_combo, 3, 1, 1, 2)
        
        # 更新帧率
        fps_label = QLabel("更新帧率:")
        fps_label.setStyleSheet(label_style)
        param_layout.addWidget(fps_label, 4, 0)
        self.fps_slider = QSlider(Qt.Orientation.Horizontal)
        self.fps_slider.setRange(1, 20)  # 1-20 FPS
        self.fps_slider.setValue(20)
        self.fps_label = QLabel("20")
        self.fps_label.setStyleSheet(value_label_style)
        param_layout.addWidget(self.fps_slider, 4, 1)
        param_layout.addWidget(self.fps_label, 4, 2)
        
        param_group['content'].setLayout(param_layout)
        self.content_layout.addWidget(param_group['widget'])
        
        # 显示选项组（默认折叠）
        display_group = self.create_collapsible_group("👁️ 显示选项", collapsed=True)
        display_layout = QVBoxLayout()
        
        self.show_trails_cb = QCheckBox("显示轨迹")
        self.show_trails_cb.setChecked(True)
        self.show_distance_circle_cb = QCheckBox("显示目标距离圆圈")
        self.show_distance_circle_cb.setChecked(True)
        self.show_grid_cb = QCheckBox("显示网格")
        self.show_grid_cb.setChecked(True)
        
        display_layout.addWidget(self.show_trails_cb)
        display_layout.addWidget(self.show_distance_circle_cb)
        display_layout.addWidget(self.show_grid_cb)
        
        display_group['content'].setLayout(display_layout)
        self.content_layout.addWidget(display_group['widget'])
    
    def create_collapsible_group(self, title, collapsed=False):
        """创建可折叠的组件"""
        # 主容器
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 标题按钮
        title_btn = QPushButton(f"{'▼' if not collapsed else '▶'} {title}")
        title_btn.setStyleSheet("""
            QPushButton {
                background-color: #F0F0F0;
                border: 1px solid #D0D0D0;
                border-radius: 4px;
                padding: 8px;
                text-align: left;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #E8E8E8;
            }
        """)
        
        # 内容容器
        content_widget = QWidget()
        content_widget.setStyleSheet("""
            QWidget {
                border: 1px solid #D0D0D0;
                border-top: none;
                border-radius: 0px 0px 4px 4px;
                background-color: white;
                padding: 5px;
            }
        """)
        
        if collapsed:
            content_widget.hide()
        
        # 连接折叠/展开功能
        def toggle_content():
            if content_widget.isVisible():
                content_widget.hide()
                title_btn.setText(f"▶ {title}")
            else:
                content_widget.show()
                title_btn.setText(f"▼ {title}")
            
            # 调整窗口大小
            QTimer.singleShot(50, self.adjust_window_size)
        
        title_btn.clicked.connect(toggle_content)
        
        main_layout.addWidget(title_btn)
        main_layout.addWidget(content_widget)
        
        return {
            'widget': main_widget,
            'content': content_widget,
            'title_btn': title_btn
        }
    
    def adjust_window_size(self):
        """调整窗口大小以适应内容"""
        try:
            # 获取主窗口
            main_window = self.window()
            if main_window:
                # 计算所需的最小高度
                self.adjustSize()
                main_window.adjustSize()
                
                # 确保窗口不会太小
                min_width = 900
                min_height = 600
                current_size = main_window.size()
                
                new_width = max(min_width, current_size.width())
                new_height = max(min_height, current_size.height())
                
                main_window.resize(new_width, new_height)
        except Exception as e:
            print(f"调整窗口大小时出错: {e}")
    
    def update_distance_info(self, current_distance, distance_error, target_distance):
        """更新距离信息显示"""
        self.current_distance_label.setText(f"当前距离: {current_distance:.1f}")
        self.target_distance_display.setText(f"目标距离: {target_distance:.1f}")
        self.distance_error_label.setText(f"距离误差: {distance_error:.1f}")
        
        # 更新有效性显示
        self.update_effectiveness_display()
    
    def update_effectiveness_display(self):
        """更新有效性显示"""
        try:
            # 通过父窗口获取canvas
            parent_window = self.parent()
            while parent_window and not hasattr(parent_window, 'canvas'):
                parent_window = parent_window.parent()
            
            if parent_window and hasattr(parent_window, 'canvas'):
                agent_b = parent_window.canvas.agent_b
                effectiveness = agent_b.get_effectiveness_ratio()
                avg_error = agent_b.get_average_distance_error()
                
                self.effective_ratio_label.setText(f"有效移动占比: {effectiveness:.1%}")
                self.avg_error_label.setText(f"平均距离误差: {avg_error:.1f}")
                
                # 根据有效性设置颜色
                if effectiveness > 0.7:
                    ratio_color = "color: #228B22;"  # 绿色
                elif effectiveness > 0.5:
                    ratio_color = "color: #FF8C00;"  # 橙色
                else:
                    ratio_color = "color: #DC143C;"  # 红色
                
                self.effective_ratio_label.setStyleSheet(ratio_color)
            else:
                # 如果无法获取数据，显示默认值
                self.effective_ratio_label.setText("有效移动占比: --")
                self.avg_error_label.setText("平均距离误差: --")
        except Exception as e:
            print(f"更新有效性显示时出错: {e}")
            self.effective_ratio_label.setText("有效移动占比: --")
            self.avg_error_label.setText("平均距离误差: --")


class MainWindow(QMainWindow):
    """主窗口"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("跟随仿真-距离方案")
        self.setGeometry(100, 100, 800, 600)
        
        # 设置样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #FFFFFF;
            }
        """)
        
        self.setup_ui()
        self.setup_timer()
        self.connect_signals()
        
        # 初始化距离信息显示
        self.update_distance_display()
    
    def on_panel_toggled(self, collapsed):
        """处理控制面板收起/展开事件"""
        if collapsed:
            # 面板收起时，画布扩展
            self.canvas.setMinimumWidth(self.width() - 80)  # 留出收起面板的空间
        else:
            # 面板展开时，恢复画布最小宽度
            self.canvas.setMinimumWidth(600)
        
    def setup_ui(self):
        """设置UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        self.main_layout = QHBoxLayout(central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)
        
        # 仿真画布
        self.canvas = SimulationCanvas()
        self.main_layout.addWidget(self.canvas)
        
        # 控制面板
        self.control_panel = ControlPanel()
        self.control_panel.panel_toggled.connect(self.on_panel_toggled)
        self.main_layout.addWidget(self.control_panel)
        
    def setup_timer(self):
        """设置定时器"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_simulation)
        self.fps = 4  # 默认4 FPS
        self.timer.setInterval(int(1000 / self.fps))  # 计算间隔时间
        
    def connect_signals(self):
        """连接信号"""
        # 参数滑块
        self.control_panel.distance_slider.valueChanged.connect(self.update_target_distance)
        self.control_panel.speed_slider.valueChanged.connect(self.update_max_speed)
        self.control_panel.inertia_slider.valueChanged.connect(self.update_inertia)
        self.control_panel.fps_slider.valueChanged.connect(self.update_fps)
        self.control_panel.angle_combo.currentTextChanged.connect(self.update_adjustment_angle)
        self.control_panel.reset_stats_btn.clicked.connect(self.reset_statistics)
        self.control_panel.record_btn.clicked.connect(self.record_effectiveness)
        
        # 显示选项
        self.control_panel.show_trails_cb.toggled.connect(self.toggle_trails)
        self.control_panel.show_distance_circle_cb.toggled.connect(self.toggle_distance_circle)
        self.control_panel.show_grid_cb.toggled.connect(self.toggle_grid)
        
        # 控制按钮
        self.control_panel.start_btn.clicked.connect(self.toggle_simulation)
        self.control_panel.reset_stats_btn.clicked.connect(self.reset_simulation)
        self.control_panel.clear_history_btn.clicked.connect(self.clear_history)
        
    def update_target_distance(self, value):
        """更新目标距离"""
        self.canvas.agent_b.target_distance = value
        self.control_panel.target_distance_label.setText(str(value))
        
    def update_max_speed(self, value):
        """更新B的最大速度"""
        speed = value
        self.canvas.agent_b.max_speed = speed
        self.control_panel.speed_label.setText(f"{speed}")
        
    def update_inertia(self, value):
        """更新惯性因子"""
        inertia = value / 100.0
        self.canvas.agent_b.inertia_factor = inertia
        self.control_panel.inertia_label.setText(f"{inertia:.2f}")
    
    def update_adjustment_angle(self, text):
        """更新调整角度"""
        angle_value = int(text.replace('°', ''))
        self.canvas.agent_b.set_adjustment_angle(angle_value)
    
    def reset_statistics(self):
        """重置统计数据"""
        self.canvas.agent_b.reset_statistics()
        self.control_panel.update_effectiveness_display()
    
    def record_effectiveness(self):
        """记录当前有效性到历史"""
        agent_b = self.canvas.agent_b
        current_angle = self.control_panel.angle_combo.currentText()
        effectiveness = agent_b.get_effectiveness_ratio()
        avg_error = agent_b.get_average_distance_error()
        
        # 记录到历史
        timestamp = time.strftime("%H:%M:%S")
        record = f"[{timestamp}] {current_angle}: 有效率={effectiveness:.2%}, 误差={avg_error:.1f}"
        
        # 更新历史记录显示
        current_text = self.control_panel.history_text.toPlainText()
        if current_text and current_text != "暂无记录，点击'记录当前有效性'开始记录":
            new_text = record + "\n" + current_text
        else:
            new_text = record
        
        # 限制历史记录行数
        lines = new_text.split('\n')
        if len(lines) > 10:
            lines = lines[:10]
            new_text = '\n'.join(lines)
        
        self.control_panel.history_text.setPlainText(new_text)
        
        # 存储到历史字典
        if current_angle not in self.control_panel.effectiveness_history:
            self.control_panel.effectiveness_history[current_angle] = []
        self.control_panel.effectiveness_history[current_angle].append({
            'timestamp': timestamp,
            'effectiveness': effectiveness,
            'avg_error': avg_error
        })
    
    def clear_history(self):
        """清除历史记录"""
        # 清空历史记录文本显示
        self.control_panel.history_text.setPlainText("暂无记录，点击'记录当前有效性'开始记录")
        
        # 清空历史记录字典
        self.control_panel.effectiveness_history.clear()
    
    def update_fps(self, value):
        """更新帧率"""
        self.fps = value
        self.control_panel.fps_label.setText(f"{value}")
        # 如果定时器正在运行，重新设置间隔
        if hasattr(self, 'timer') and self.timer.isActive():
            self.timer.setInterval(int(1000 / self.fps))
        
    def toggle_trails(self, checked):
        """切换轨迹显示"""
        self.canvas.show_trails = checked
        
    def toggle_distance_circle(self, checked):
        """切换距离圆圈显示"""
        self.canvas.show_distance_circle = checked
        
    def toggle_grid(self, checked):
        """切换网格显示"""
        self.canvas.show_grid = checked
        
    def toggle_simulation(self):
        """切换仿真状态"""
        if self.timer.isActive():
            self.timer.stop()
            self.control_panel.start_btn.setText("▶️ 开始仿真")
            self.control_panel.start_btn.setStyleSheet("""
                QPushButton {
                    background-color: #98FB98;
                    color: #2F4F4F;
                    border: none;
                    padding: 10px;
                    border-radius: 5px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #90EE90;
                }
            """)
        else:
            self.timer.start()
            self.control_panel.start_btn.setText("⏸️ 暂停仿真")
            self.control_panel.start_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FFB6C1;
                    color: #2F4F4F;
                    border: none;
                    padding: 10px;
                    border-radius: 5px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #FFA0B4;
                }
            """)
            
    def reset_simulation(self):
        """重置仿真"""
        # 重置位置
        self.canvas.agent_a.position = Point(400, 300)
        self.canvas.agent_b.position = Point(300, 300)
        
        # 清空轨迹
        self.canvas.agent_a.trail.clear()
        self.canvas.agent_b.trail.clear()
        self.canvas.agent_a.trail.append(Point(400, 300))
        self.canvas.agent_b.trail.append(Point(300, 300))
        
        # 重置B的状态
        self.canvas.agent_b.distance_history.clear()
        self.canvas.agent_b.last_successful_direction = 0.0
        self.canvas.agent_b.reset_statistics()
        
        # 重置A的方向
        self.canvas.agent_a.direction = random.uniform(0, 2 * math.pi)
        
        self.canvas.update()
        
    def update_simulation(self):
        """更新仿真"""
        bounds = (self.canvas.width(), self.canvas.height())
        
        # 移动A
        self.canvas.agent_a.move(bounds)
        
        # 计算距离（B只能获取这个信息）
        distance_to_a = self.canvas.agent_a.position.distance_to(self.canvas.agent_b.position)
        
        # 移动B（仅基于距离）
        self.canvas.agent_b.move(distance_to_a, bounds, self.canvas.agent_a.position)
        
        # 更新距离信息显示
        self.update_distance_display()
        
        # 更新画布
        self.canvas.update()
    
    def update_distance_display(self):
        """更新距离信息显示"""
        current_distance, distance_error = self.canvas.get_distance_info()
        self.control_panel.update_distance_info(
            current_distance, 
            distance_error, 
            self.canvas.agent_b.target_distance
        )


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用样式
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()