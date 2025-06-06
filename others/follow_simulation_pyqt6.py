# -*- coding: utf-8 -*-
"""
距离跟随仿真应用 - PyQt6版本
在仅知道双方距离的情况下，B跟随随机移动的A

核心算法：
1. 使用历史位置信息预测A的移动方向
2. 基于距离变化率判断相对运动趋势
3. 采用梯度下降法优化B的移动方向
4. 结合惯性和阻尼系统提高跟随稳定性
"""

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
from PyQt6.QtCore import QTimer, Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect
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
        super().__init__(x, y, QColor(255, 107, 107))  # 现代红色
        self.direction = random.uniform(0, 2 * math.pi)
        self.speed = 2.0
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
    """跟随智能体B - 核心算法实现"""
    def __init__(self, x: float, y: float, target_distance: float):
        super().__init__(x, y, QColor(78, 205, 196))  # 现代青色
        self.target_distance = target_distance
        self.max_speed = 3.0
        self.distance_history: deque = deque(maxlen=10)  # 距离历史
        self.position_estimates: deque = deque(maxlen=5)  # A的位置估计历史
        self.last_successful_direction = 0.0  # 上次成功的移动方向
        self.inertia_factor = 0.3  # 惯性因子
        self.exploration_angle = 0.0  # 探索角度
        self.last_a_position = None  # 上次A的估计位置
        
    def estimate_target_position(self, distance_to_a: float, a_real_pos: Point = None) -> List[Point]:
        """基于距离估计A的可能位置（圆周上的点）"""
        possible_positions = []
        # 在以B为圆心，距离为半径的圆周上生成可能位置
        for angle in range(0, 360, 30):  # 每30度一个点
            rad = math.radians(angle)
            pos = Point(
                self.position.x + distance_to_a * math.cos(rad),
                self.position.y + distance_to_a * math.sin(rad)
            )
            possible_positions.append(pos)
        
        # 如果有真实A位置信息，选择最接近的估计位置
        if a_real_pos:
            best_pos = min(possible_positions, key=lambda p: p.distance_to(a_real_pos))
            self.position_estimates.append(best_pos)
            self.last_a_position = best_pos
        
        return possible_positions
    
    def predict_target_movement(self) -> Optional[Point]:
        """基于历史信息预测A的移动方向"""
        if len(self.position_estimates) < 2:
            return None
        
        # 计算A的平均移动向量
        movement_vectors = []
        for i in range(1, len(self.position_estimates)):
            if self.position_estimates[i] and self.position_estimates[i-1]:
                vector = self.position_estimates[i] - self.position_estimates[i-1]
                movement_vectors.append(vector)
        
        if not movement_vectors:
            return None
        
        # 计算平均移动向量
        avg_movement = Point(
            sum(v.x for v in movement_vectors) / len(movement_vectors),
            sum(v.y for v in movement_vectors) / len(movement_vectors)
        )
        
        return avg_movement
    
    def calculate_optimal_direction(self, distance_to_a: float, a_real_pos: Point) -> float:
        """计算最优移动方向 - 核心算法"""
        # 记录当前距离
        self.distance_history.append(distance_to_a)
        
        # 距离误差
        distance_error = distance_to_a - self.target_distance
        
        # 估计A的位置
        self.estimate_target_position(distance_to_a, a_real_pos)
        
        # 如果距离已经很接近目标，微调移动
        if abs(distance_error) < 8:
            if self.last_a_position:
                # 计算垂直于连线的方向，进行轨道调整
                to_a = Point(self.last_a_position.x - self.position.x, 
                           self.last_a_position.y - self.position.y)
                perpendicular = math.atan2(to_a.y, to_a.x) + math.pi/2
                return perpendicular
            return self.last_successful_direction
        
        # 方法1：直接朝向估计的A位置移动
        if self.last_a_position:
            if distance_error > 0:  # 距离太远，需要靠近
                direction_to_a = math.atan2(
                    self.last_a_position.y - self.position.y,
                    self.last_a_position.x - self.position.x
                )
                return direction_to_a
            else:  # 距离太近，需要远离
                direction_from_a = math.atan2(
                    self.position.y - self.last_a_position.y,
                    self.position.x - self.last_a_position.x
                )
                return direction_from_a
        
        # 方法2：基于距离变化率的方向调整
        if len(self.distance_history) >= 2:
            distance_change_rate = self.distance_history[-1] - self.distance_history[-2]
            
            # 如果距离在增加且当前距离大于目标距离，需要向A靠近
            if distance_change_rate > 0 and distance_error > 0:
                # 尝试多个方向，选择能最快减少距离的方向
                best_direction = self.last_successful_direction
                best_score = float('inf')
                
                for angle_offset in [-math.pi/3, -math.pi/6, 0, math.pi/6, math.pi/3]:
                    test_direction = self.last_successful_direction + angle_offset
                    
                    # 模拟移动后的位置
                    test_pos = Point(
                        self.position.x + self.max_speed * math.cos(test_direction),
                        self.position.y + self.max_speed * math.sin(test_direction)
                    )
                    
                    # 计算与目标距离的误差
                    if a_real_pos:
                        predicted_distance = test_pos.distance_to(a_real_pos)
                        error = abs(predicted_distance - self.target_distance)
                        if error < best_score:
                            best_score = error
                            best_direction = test_direction
                
                return best_direction
        
        # 方法3：基于预测的A的移动方向
        predicted_movement = self.predict_target_movement()
        if predicted_movement and self.last_a_position:
            # 预测A的下一个位置
            predicted_a_pos = self.last_a_position + predicted_movement
            
            if distance_error > 0:
                # 计算朝向预测位置的方向
                direction_to_predicted = math.atan2(
                    predicted_a_pos.y - self.position.y,
                    predicted_a_pos.x - self.position.x
                )
                return direction_to_predicted
        
        # 方法4：探索性移动
        self.exploration_angle += math.pi / 8  # 每次增加22.5度
        if self.exploration_angle > 2 * math.pi:
            self.exploration_angle = 0
        
        # 如果距离太远，向内移动；如果太近，向外移动
        if distance_error > 0:
            # 距离太远，需要靠近，使用探索角度
            return self.exploration_angle
        else:
            # 距离太近，需要远离，使用相反方向
            return self.exploration_angle + math.pi
    
    def move(self, distance_to_a: float, a_real_pos: Point, bounds: Tuple[int, int]):
        """基于距离信息移动"""
        # 计算最优移动方向
        optimal_direction = self.calculate_optimal_direction(distance_to_a, a_real_pos)
        
        # 应用惯性
        actual_direction = (
            self.inertia_factor * self.last_successful_direction +
            (1 - self.inertia_factor) * optimal_direction
        )
        
        # 计算移动速度（距离误差越大，速度越快）
        distance_error = abs(distance_to_a - self.target_distance)
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
        self.last_successful_direction = actual_direction
        
        self.update_trail()


class SimulationCanvas(QWidget):
    """仿真画布"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(800, 600)
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
            self.draw_trail(painter, self.agent_a.trail, QColor(255, 107, 107, 150), 3)
            self.draw_trail(painter, self.agent_b.trail, QColor(78, 205, 196, 150), 3)
        
        # 绘制目标距离圆圈
        if self.show_distance_circle:
            self.draw_target_circle(painter)
        
        # 绘制连接线
        self.draw_connection_line(painter)
        
        # 绘制智能体
        self.draw_agent(painter, self.agent_a, "A", 15)
        self.draw_agent(painter, self.agent_b, "B", 12)
    
    def draw_grid(self, painter: QPainter):
        """绘制网格背景"""
        pen = QPen(QColor(233, 236, 239), 1)
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
        painter.setPen(QPen(QColor(255, 255, 255), 3))
        painter.drawEllipse(x - size, y - size, size * 2, size * 2)
        
        # 绘制标签
        painter.setPen(QPen(QColor(255, 255, 255)))
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
        pen = QPen(QColor(108, 117, 125), 2)
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
        line_color = QColor(40, 167, 69) if abs(current_distance - self.agent_b.target_distance) < 10 else QColor(255, 193, 7)
        pen = QPen(line_color, 2)
        painter.setPen(pen)
        painter.drawLine(
            int(self.agent_a.position.x), int(self.agent_a.position.y),
            int(self.agent_b.position.x), int(self.agent_b.position.y)
        )

class ControlPanel(QWidget):
    """控制面板 - 可折叠"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(320)
        self.setStyleSheet("""
            QWidget {
                background-color: #F8F9FA;
                border: 1px solid #E9ECEF;
                border-radius: 8px;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #E9ECEF;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #FFFFFF;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                background-color: #F8F9FA;
            }
        """)
        
        self.is_collapsed = False
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        
        # 标题栏
        title_layout = QHBoxLayout()
        title_label = QLabel("🎛️ 控制面板")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px;")
        
        self.collapse_btn = QPushButton("◀")
        self.collapse_btn.setFixedSize(30, 30)
        self.collapse_btn.setStyleSheet("""
            QPushButton {
                border: 1px solid #E9ECEF;
                border-radius: 15px;
                background-color: #FFFFFF;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #F1F3F4;
            }
        """)
        self.collapse_btn.clicked.connect(self.toggle_collapse)
        
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(self.collapse_btn)
        layout.addLayout(title_layout)
        
        # 内容区域
        self.content_widget = QWidget()
        self.setup_content()
        layout.addWidget(self.content_widget)
        
        layout.addStretch()
    
    def setup_content(self):
        """设置内容区域"""
        layout = QVBoxLayout(self.content_widget)
        
        # 参数设置组
        param_group = QGroupBox("⚙️ 参数设置")
        param_layout = QGridLayout(param_group)
        
        # 目标距离
        param_layout.addWidget(QLabel("目标距离:"), 0, 0)
        self.target_distance_slider = QSlider(Qt.Orientation.Horizontal)
        self.target_distance_slider.setRange(50, 200)
        self.target_distance_slider.setValue(100)
        self.target_distance_label = QLabel("100")
        param_layout.addWidget(self.target_distance_slider, 0, 1)
        param_layout.addWidget(self.target_distance_label, 0, 2)
        
        # A的速度
        param_layout.addWidget(QLabel("A的速度:"), 1, 0)
        self.a_speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.a_speed_slider.setRange(5, 50)  # 0.5-5.0 * 10
        self.a_speed_slider.setValue(20)  # 2.0 * 10
        self.a_speed_label = QLabel("2.0")
        param_layout.addWidget(self.a_speed_slider, 1, 1)
        param_layout.addWidget(self.a_speed_label, 1, 2)
        
        # B的最大速度
        param_layout.addWidget(QLabel("B的最大速度:"), 2, 0)
        self.b_speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.b_speed_slider.setRange(10, 60)  # 1.0-6.0 * 10
        self.b_speed_slider.setValue(30)  # 3.0 * 10
        self.b_speed_label = QLabel("3.0")
        param_layout.addWidget(self.b_speed_slider, 2, 1)
        param_layout.addWidget(self.b_speed_label, 2, 2)
        
        # 惯性因子
        param_layout.addWidget(QLabel("惯性因子:"), 3, 0)
        self.inertia_slider = QSlider(Qt.Orientation.Horizontal)
        self.inertia_slider.setRange(0, 80)  # 0.0-0.8 * 100
        self.inertia_slider.setValue(30)  # 0.3 * 100
        self.inertia_label = QLabel("0.3")
        param_layout.addWidget(self.inertia_slider, 3, 1)
        param_layout.addWidget(self.inertia_label, 3, 2)
        
        layout.addWidget(param_group)
        
        # 显示选项组
        display_group = QGroupBox("👁️ 显示选项")
        display_layout = QVBoxLayout(display_group)
        
        self.show_trails_cb = QCheckBox("显示轨迹")
        self.show_trails_cb.setChecked(True)
        self.show_circle_cb = QCheckBox("显示目标距离圆")
        self.show_circle_cb.setChecked(True)
        self.show_grid_cb = QCheckBox("显示网格")
        self.show_grid_cb.setChecked(True)
        
        display_layout.addWidget(self.show_trails_cb)
        display_layout.addWidget(self.show_circle_cb)
        display_layout.addWidget(self.show_grid_cb)
        
        layout.addWidget(display_group)
        
        # 统计信息组
        stats_group = QGroupBox("📊 统计信息")
        stats_layout = QVBoxLayout(stats_group)
        
        self.stats_text = QTextEdit()
        self.stats_text.setMaximumHeight(125)
        self.stats_text.setStyleSheet("font-family: 'Consolas', monospace; font-size: 10px;")
        self.stats_text.setReadOnly(True)
        stats_layout.addWidget(self.stats_text)
        
        layout.addWidget(stats_group)
        
        # 算法说明组
        algo_group = QGroupBox("🧠 INFO")
        algo_layout = QVBoxLayout(algo_group)
        
        algo_text = QTextEdit()
        algo_text.setMaximumHeight(150)
        algo_text.setStyleSheet("font-size: 10px;")
        algo_text.setReadOnly(True)
        algo_text.setPlainText(
            "核心算法原理：\n\n"
            "1. 距离感知：B只能感知到与A的距离\n\n"
            "2. 方向推断：\n"
            "   • 基于距离变化率判断相对运动趋势\n"
            "   • 使用历史信息预测A的移动方向\n"
            "   • 采用多方向探索找到最优路径\n\n"
            "3. 运动控制：\n"
            "   • 距离误差越大，移动速度越快\n"
            "   • 应用惯性系统保持运动稳定性\n"
            "   • 边界检测防止越界\n\n"
            "4. 自适应学习：\n"
            "   • 记录成功的移动方向\n"
            "   • 根据跟随效果调整策略"
        )
        algo_layout.addWidget(algo_text)
        
        layout.addWidget(algo_group)
    
    def toggle_collapse(self):
        """切换折叠状态"""
        self.is_collapsed = not self.is_collapsed
        
        if self.is_collapsed:
            self.content_widget.hide()
            self.collapse_btn.setText("▶")
            self.setFixedWidth(60)
        else:
            self.content_widget.show()
            self.collapse_btn.setText("◀")
            self.setFixedWidth(320)
    
    def update_stats(self, step_count: int, avg_error: float, current_distance: float, agent_a: AgentA, agent_b: AgentB):
        """更新统计信息"""
        stats_info = (
            f"仿真步数: {step_count}\n"
            f"平均误差: {avg_error:.1f} px\n"
            f"距离误差: {abs(current_distance - agent_b.target_distance):.1f} px"
            f"当前距离: {current_distance:.1f} px\n"
            f"跟随精度: {max(0, 100 - avg_error):.1f}%\n"
            f"A位置: ({agent_a.position.x:.0f}, {agent_a.position.y:.0f})\n"
            f"B位置: ({agent_b.position.x:.0f}, {agent_b.position.y:.0f})\n"
        )
        self.stats_text.setPlainText(stats_info)


class BottomControlBar(QWidget):
    """底部控制栏"""
    start_pause_clicked = pyqtSignal()
    reset_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(60)
        self.setStyleSheet("""
            QWidget {
                background-color: #F1F3F4;
                border-top: 1px solid #E9ECEF;
            }
            QPushButton {
                background-color: #6C757D;
                color: white;
                border: none;
                border-radius: 20px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5A6268;
            }
            QPushButton:pressed {
                background-color: #495057;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)
        
        # 左侧按钮
        self.start_pause_btn = QPushButton("⏸️ 暂停")
        self.start_pause_btn.clicked.connect(self.start_pause_clicked.emit)
        
        self.reset_btn = QPushButton("🔄 重置")
        self.reset_btn.clicked.connect(self.reset_clicked.emit)
        
        layout.addWidget(self.start_pause_btn)
        layout.addWidget(self.reset_btn)
        layout.addStretch()
        
        # 右侧状态信息
        self.status_label = QLabel("🟢 仿真运行中")
        self.status_label.setStyleSheet("color: #28A745; font-weight: bold; background-color: transparent;")
        layout.addWidget(self.status_label)
    
    def update_status(self, is_running: bool):
        """更新状态"""
        if is_running:
            self.start_pause_btn.setText("⏸️ 暂停")
            self.status_label.setText("🟢 仿真运行中")
            self.status_label.setStyleSheet("color: #28A745; font-weight: bold; background-color: transparent;")
        else:
            self.start_pause_btn.setText("▶️ 开始")
            self.status_label.setText("🔴 仿真已暂停")
            self.status_label.setStyleSheet("color: #DC3545; font-weight: bold; background-color: transparent;")


class FollowSimulationApp(QMainWindow):
    """主应用程序"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("距离跟随仿真")
        self.setGeometry(100, 100, 1000, 700)
        
        # 仿真控制
        self.is_running = True
        self.step_count = 0
        self.distance_errors = deque(maxlen=100)
        
        self.setup_ui()
        self.setup_timer()
        self.connect_signals()
    
    def setup_ui(self):
        """设置UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 中间内容区域
        content_layout = QHBoxLayout()
        
        # 左侧画布区域
        canvas_container = QWidget()
        canvas_layout = QVBoxLayout(canvas_container)
        canvas_layout.setContentsMargins(10, 10, 10, 10)
        
        # 画布
        self.canvas = SimulationCanvas()
        canvas_layout.addWidget(self.canvas)
        
        content_layout.addWidget(canvas_container, 1)
        
        # 右侧控制面板
        self.control_panel = ControlPanel()
        content_layout.addWidget(self.control_panel)
        
        main_layout.addLayout(content_layout, 1)
        
        # 底部控制栏
        self.bottom_bar = BottomControlBar()
        main_layout.addWidget(self.bottom_bar)
    
    def setup_timer(self):
        """设置定时器"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_simulation)
        self.timer.start(50)  # 20 FPS
    
    def connect_signals(self):
        """连接信号"""
        # 底部控制栏
        self.bottom_bar.start_pause_clicked.connect(self.toggle_simulation)
        self.bottom_bar.reset_clicked.connect(self.reset_simulation)
        
        # 控制面板滑块
        self.control_panel.target_distance_slider.valueChanged.connect(self.update_target_distance)
        self.control_panel.a_speed_slider.valueChanged.connect(self.update_a_speed)
        self.control_panel.b_speed_slider.valueChanged.connect(self.update_b_speed)
        self.control_panel.inertia_slider.valueChanged.connect(self.update_inertia)
        
        # 显示选项
        self.control_panel.show_trails_cb.toggled.connect(self.toggle_trails)
        self.control_panel.show_circle_cb.toggled.connect(self.toggle_circle)
        self.control_panel.show_grid_cb.toggled.connect(self.toggle_grid)
    
    def update_simulation(self):
        """更新仿真"""
        if self.is_running:
            # 移动智能体
            self.canvas.agent_a.move((self.canvas.width(), self.canvas.height()))
            
            current_distance = self.canvas.agent_a.position.distance_to(self.canvas.agent_b.position)
            self.canvas.agent_b.move(current_distance, self.canvas.agent_a.position,
                                   (self.canvas.width(), self.canvas.height()))
            
            # 更新统计信息
            self.step_count += 1
            distance_error = abs(current_distance - self.canvas.agent_b.target_distance)
            self.distance_errors.append(distance_error)
            
            avg_error = sum(self.distance_errors) / len(self.distance_errors) if self.distance_errors else 0
            
            # 更新显示
            self.canvas.update()
            self.control_panel.update_stats(self.step_count, avg_error, current_distance, self.canvas.agent_a, self.canvas.agent_b)
    
    def toggle_simulation(self):
        """切换仿真状态"""
        self.is_running = not self.is_running
        self.bottom_bar.update_status(self.is_running)
    
    def reset_simulation(self):
        """重置仿真"""
        target_distance = self.control_panel.target_distance_slider.value()
        self.canvas.agent_a = AgentA(400, 300)
        self.canvas.agent_b = AgentB(300, 300, target_distance)
        self.step_count = 0
        self.distance_errors.clear()
        self.canvas.update()
    
    def update_target_distance(self, value):
        """更新目标距离"""
        self.control_panel.target_distance_label.setText(str(value))
        self.canvas.agent_b.target_distance = value
    
    def update_a_speed(self, value):
        """更新A的速度"""
        speed = value / 10.0
        self.control_panel.a_speed_label.setText(f"{speed:.1f}")
        self.canvas.agent_a.speed = speed
    
    def update_b_speed(self, value):
        """更新B的最大速度"""
        speed = value / 10.0
        self.control_panel.b_speed_label.setText(f"{speed:.1f}")
        self.canvas.agent_b.max_speed = speed
    
    def update_inertia(self, value):
        """更新惯性因子"""
        inertia = value / 100.0
        self.control_panel.inertia_label.setText(f"{inertia:.1f}")
        self.canvas.agent_b.inertia_factor = inertia
    
    def toggle_trails(self, checked):
        """切换轨迹显示"""
        self.canvas.show_trails = checked
    
    def toggle_circle(self, checked):
        """切换目标距离圆显示"""
        self.canvas.show_distance_circle = checked
    
    def toggle_grid(self, checked):
        """切换网格显示"""
        self.canvas.show_grid = checked


def main():
    app = QApplication(sys.argv)
    
    # 设置应用样式
    app.setStyleSheet("""
        QMainWindow {
            background-color: #F8F9FA;
        }
        QSlider::groove:horizontal {
            border: 1px solid #bbb;
            background: white;
            height: 10px;
            border-radius: 4px;
        }
        QSlider::sub-page:horizontal {
            background: qlineargradient(x1: 0, y1: 0,    x2: 0, y2: 1,
                stop: 0 #66e, stop: 1 #bbf);
            background: qlineargradient(x1: 0, y1: 0.2, x2: 1, y2: 1,
                stop: 0 #bbf, stop: 1 #55f);
            border: 1px solid #777;
            height: 10px;
            border-radius: 4px;
        }
        QSlider::add-page:horizontal {
            background: #fff;
            border: 1px solid #777;
            height: 10px;
            border-radius: 4px;
        }
        QSlider::handle:horizontal {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #eee, stop:1 #ccc);
            border: 1px solid #777;
            width: 18px;
            margin-top: -2px;
            margin-bottom: -2px;
            border-radius: 3px;
        }
        QSlider::handle:horizontal:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #fff, stop:1 #ddd);
            border: 1px solid #444;
            border-radius: 3px;
        }
    """)
    
    window = FollowSimulationApp()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()