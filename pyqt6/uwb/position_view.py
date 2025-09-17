from PyQt6.QtCore import Qt, QPoint, QTimer, QRectF, QPointF
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import (
    QFont, QColor, QPainter, QPen,
    QLinearGradient, QPixmap
)
from user_manager import MultiUserManager, UserData


class PositionView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scale            = 2
        self.origin_offset_y  = -200
        self.main_window      = parent  # 保存主窗口引用
        self.display_scale    = 1.0     # 显示缩放因子，用于扩展模式
        
        # 创建静态内容缓存
        self.static_content   = None
        
        # 多用户管理器
        self.user_manager = MultiUserManager(max_users=10)
        
        # 动画定时器 - 用于平滑移动动画
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_animations)
        self.animation_timer.setInterval(15)  # BM: SET FPS
        
        # 兼容性属性 - 为了保持与现有代码的兼容性
        self.current_position = None
        self.last_position = None
        
    def set_display_scale(self, scale):
        """设置显示缩放因子"""
        self.display_scale = scale
        self.static_content = None  # 清除缓存，强制重绘
        self.update()
        
    def update_animations(self):   #XXX 定时器会不断检测是否还需要update重绘
        """Update user position animations"""
        has_active_animations = self.user_manager.update_animations()
        
        if has_active_animations:
            # Continue animation
            self.update()  # Trigger repaint
        else:
            # No active animations, stop timer
            self.animation_timer.stop()
        
    def draw_static_content(self, painter, center_x, center_y):
        # 获取动态长度值并应用显示缩放
        red_height = int(self.main_window.red_length * self.scale * self.display_scale) if self.main_window.red_length != 0 else int(100 * self.display_scale)
        blue_height = int(self.main_window.blue_length * self.display_scale) if self.main_window.blue_length != 0 else int(300 * self.display_scale)
        print(f'red_height: {red_height}, blue_height: {blue_height}, display_scale: {self.display_scale}')
        
        # 应用缩放的区域宽度
        area_width = int(200 * self.display_scale)
        area_half_width = int(100 * self.display_scale)
        
        # 红色感应区（从原点开始向下）
        red_gradient = QLinearGradient(center_x, center_y, center_x, center_y + red_height)
        red_gradient.setColorAt(0, QColor(255, 0, 0, 70))  # 增加红色透明度
        red_gradient.setColorAt(1, QColor(255, 0, 0, 80))
        painter.setBrush(red_gradient)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(int(center_x - area_half_width), int(center_y), area_width, red_height)
        
        # 蓝色区域（紧接红色区域，不重叠）
        blue_start_y = center_y + red_height
        blue_rect_height = blue_height - red_height if blue_height > red_height else blue_height
        blue_gradient = QLinearGradient(center_x, blue_start_y, center_x, blue_start_y + blue_rect_height)
        blue_gradient.setColorAt(0, QColor(0, 140, 255, 100))  # 增加蓝色透明度和饱和度
        blue_gradient.setColorAt(1, QColor(0, 140, 255, 70))
        painter.setBrush(blue_gradient)
        painter.drawRect(int(center_x - area_half_width), int(blue_start_y), area_width, blue_rect_height)
        
        # 应用缩放的闸机尺寸
        gate_width = int(20 * self.display_scale)
        gate_height = int(80 * self.display_scale)
        gate_half_height = int(40 * self.display_scale)
        
        # 绘制闸机（左侧）
        painter.setPen(QPen(QColor("#333333"), int(2 * self.display_scale)))
        painter.setBrush(QColor("#444444"))
        painter.drawRect(int(center_x - area_half_width), int(center_y - gate_half_height), gate_width, gate_height)
        # 闸机装饰
        painter.setPen(QPen(QColor("#666666"), max(1, int(1 * self.display_scale))))
        decoration_offset = int(5 * self.display_scale)
        decoration_spacing = int(30 * self.display_scale)
        painter.drawLine(int(center_x - area_half_width + decoration_offset), int(center_y - decoration_spacing), 
                        int(center_x - area_half_width + gate_width - decoration_offset), int(center_y - decoration_spacing))
        painter.drawLine(int(center_x - area_half_width + decoration_offset), int(center_y), 
                        int(center_x - area_half_width + gate_width - decoration_offset), int(center_y))
        painter.drawLine(int(center_x - area_half_width + decoration_offset), int(center_y + decoration_spacing), 
                        int(center_x - area_half_width + gate_width - decoration_offset), int(center_y + decoration_spacing))
        
        # 绘制闸机（右侧）
        right_gate_x = int(center_x + area_half_width - gate_width)
        painter.setPen(QPen(QColor("#333333"), int(2 * self.display_scale)))
        painter.setBrush(QColor("#444444"))
        painter.drawRect(right_gate_x, int(center_y - gate_half_height), gate_width, gate_height)
        # 闸机装饰
        painter.setPen(QPen(QColor("#666666"), max(1, int(1 * self.display_scale))))
        painter.drawLine(int(right_gate_x + decoration_offset), int(center_y - decoration_spacing), 
                        int(right_gate_x + gate_width - decoration_offset), int(center_y - decoration_spacing))
        painter.drawLine(int(right_gate_x + decoration_offset), int(center_y), 
                        int(right_gate_x + gate_width - decoration_offset), int(center_y))
        painter.drawLine(int(right_gate_x + decoration_offset), int(center_y + decoration_spacing), 
                        int(right_gate_x + gate_width - decoration_offset), int(center_y + decoration_spacing))
        
        # 绘制坐标轴
        painter.setPen(QPen(QColor("#666666"), max(1, int(1 * self.display_scale))))
        painter.drawLine(0, int(center_y), self.width(), int(center_y))
        painter.drawLine(int(center_x), 0, int(center_x), self.height())
        
        # 绘制原点（红色）
        origin_size = int(4 * self.display_scale)
        origin_half_size = int(2 * self.display_scale)
        painter.setPen(QPen(QColor("#FF0000"), int(2 * self.display_scale)))
        painter.setBrush(QColor("#FF0000"))
        painter.drawEllipse(int(center_x) - origin_half_size, int(center_y) - origin_half_size, origin_size, origin_size)
        
    def create_static_content(self):
        """创建静态内容缓存"""
        self.static_content = QPixmap(self.size())
        self.static_content.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(self.static_content)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 获取窗口中心
        center_x = self.width() / 2
        center_y = self.height() / 2 + self.origin_offset_y
        
        # 绘制静态内容
        self.draw_static_content(painter, center_x, center_y)
        painter.end()
        
    def update_position(self, x, y, mac="default"):
        #XXX 用户大幅度或中幅度移动 position_changed=TRUE
        position_changed = self.user_manager.update_user_position(mac, x, y)  
        
        # 更新兼容性属性（使用第一个用户或默认用户的位置）
        if mac == "default" or len(self.user_manager.users) == 1:
            if mac in self.user_manager.users:
                user = self.user_manager.users[mac]
                self.last_position = self.current_position
                self.current_position = (user.current_position[0], user.current_position[1])
        
        # 根据位置变化类型决定处理方式
        if position_changed:
            # Check if any user is animating to decide whether to start animation timer
            has_animations = any(user.is_animating for user in self.user_manager.users.values())
            
            if has_animations and not self.animation_timer.isActive():
                # Start animation timer only if there are animations
                self.animation_timer.start()
            
            # Always trigger redraw for position changes
            self.update()
    
    def update_multi_user_positions(self, user_positions):  # BM: 更新用户位置
        any_position_changed = False
        
        if isinstance(user_positions, dict):
            # Handle dictionary input
            for mac, (x, y) in user_positions.items():
                if self.user_manager.update_user_position(mac, x, y):
                    any_position_changed = True
        else:
            # Handle list of tuples input
            for mac, x, y in user_positions:
                if self.user_manager.update_user_position(mac, x, y):
                    any_position_changed = True
        
        # Update compatibility attributes with first user
        users = self.user_manager.get_all_users()
        if users:
            first_user = users[0]
            self.last_position = self.current_position
            self.current_position = (first_user.current_position[0], first_user.current_position[1])
        
        # Only trigger redraw and animation if any position changed significantly
        if any_position_changed:
            # Check if any user is animating to decide whether to start animation timer
            has_animations = any(user.is_animating for user in self.user_manager.users.values())
            
            if has_animations and not self.animation_timer.isActive():
                # Start animation timer only if there are animations
                self.animation_timer.start()
            
            # Always trigger redraw for position changes
            self.update()
        
    def refresh_areas(self):
        """刷新红蓝区域，当长度值变化时调用"""
        self.static_content = None  # 清除缓存
        self.update()  # 触发重绘
        
    def paintEvent(self, event):   # BM: 绘制用户位置
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 如果静态内容不存在或窗口大小改变，重新创建
        if self.static_content is None or \
           self.static_content.size() != self.size():
            self.create_static_content()
        
        # 绘制静态内容
        painter.drawPixmap(0, 0, self.static_content)
        
        # 获取窗口中心（用于动态内容）
        center_x = self.width() / 2
        center_y = self.height() / 2 + self.origin_offset_y
        
        # 获取所有用户
        users = self.user_manager.get_all_users()
        
        # 如果没有用户数据，到此结束
        if not users:
            return
        
        # 绘制用户信息（去掉黑色底纹）
        info_y = 0
        for i, user in enumerate(users):
            x, y, z = user.current_position
            user_color = self.user_manager.get_user_color(user.mac)
            
            # 构建用户信息文本，包含坐标、卡号和余额
            coord_text = f"{user.mac[-4:]} : ({int(x)}, {int(y)})"
            
            # 添加卡号和余额信息
            if user.card_no is not None:
                coord_text += f" | {user.card_no[-8:]}"
            if user.balance is not None:
                coord_text += f" | ¥{user.balance:.2f}"
            
            # 绘制用户颜色指示器
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(*user_color, 255))
            painter.drawEllipse(15, info_y + 3, 8, 8)
            
            # 绘制文本（无背景）
            painter.setPen(QPen(QColor("#ffffff"), 1))
            painter.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            painter.drawText(28, info_y + 13, coord_text)
            
            info_y += 25  # 下一行
        
        # 绘制所有用户的位置和轨迹
        for user in users:
            x, y, z = user.current_position
            # 应用显示缩放到位置计算
            screen_x = center_x + x * self.scale * self.display_scale
            screen_y = center_y + y * self.scale * self.display_scale
            user_color = self.user_manager.get_user_color(user.mac)
            
            # 绘制轨迹（如果有上一个位置）
            if user.last_position:
                last_x, last_y, _ = user.last_position
                last_screen_x = center_x + last_x * self.scale * self.display_scale
                last_screen_y = center_y + last_y * self.scale * self.display_scale
                
                # 使用用户特定颜色绘制轨迹
                gradient = QLinearGradient(last_screen_x, last_screen_y, screen_x, screen_y)
                gradient.setColorAt(0, QColor(*user_color, 50))   # 起点颜色（较淡）
                gradient.setColorAt(1, QColor(*user_color, 180))  # 终点颜色（较深）
                
                pen = QPen()
                pen.setBrush(gradient)
                pen.setWidth(int(4 * self.display_scale))
                painter.setPen(pen)
                painter.drawLine(int(last_screen_x), int(last_screen_y), 
                               int(screen_x), int(screen_y))
            
            # 绘制当前位置点
            point_size = int(12 * self.display_scale)
            point_half_size = int(6 * self.display_scale)
            painter.setPen(QPen(QColor(*user_color), int(2 * self.display_scale)))
            painter.setBrush(QColor(*user_color, 255))
            painter.drawEllipse(int(screen_x) - point_half_size, int(screen_y) - point_half_size, point_size, point_size)
            
            # 绘制用户MAC标识（在点正下方）
            painter.setPen(QPen(QColor("#ffffff"), max(1, int(1 * self.display_scale))))
            font_size = max(6, int(8 * self.display_scale))
            painter.setFont(QFont("Segoe UI", font_size, QFont.Weight.Bold))
            # 计算文本宽度以居中显示
            text_width = painter.fontMetrics().horizontalAdvance(user.mac[-4:])
            text_offset = int(20 * self.display_scale)
            painter.drawText(int(screen_x) - text_width // 2, int(screen_y) + text_offset, user.mac[-4:])
        
        # 标记所有用户数据为已处理
        for user in users:
            user.mark_processed()