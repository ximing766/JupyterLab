import random
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QSplitter # Presumed existing, add if not
from PyQt6.QtCore import QPointF, QTimer, Qt, QRectF      # Add QPointF, QTimer, Qt, QRectF
from PyQt6.QtGui import QPainter, QColor

class Particle:
    def __init__(self, bounds_rect):
        self.bounds = bounds_rect
        self.reset()

    def reset(self):
        self.pos = QPointF(random.uniform(0, self.bounds.width()),
                           random.uniform(0, self.bounds.height()))
        # Particles tend to float upwards
        self.vel = QPointF(random.uniform(-0.5, 0.5), random.uniform(-0.8, -1.8))
        self.color = QColor(random.randint(100, 200), 
                            random.randint(100, 200), 
                            random.randint(200, 255), 
                            random.randint(30, 120)) # Alpha for transparency
        self.size = random.uniform(1.5, 4.5)

    def update(self):
        self.pos += self.vel
        # If particle goes out of bounds, reset it
        if not self.bounds.contains(self.pos):
            # Reset to a position along the bottom edge, moving upwards
            self.pos = QPointF(random.uniform(0, self.bounds.width()), self.bounds.height() -1)
            self.vel = QPointF(random.uniform(-0.5, 0.5), random.uniform(-0.8, -1.8))


class ParticleEffectWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background: transparent;")
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        self.particles = []
        self.num_particles = 75

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_particles_and_repaint)
        
        self._particles_initialized = False

    def _initialize_particles(self):
        if self.width() > 0 and self.height() > 0:
            bounds = QRectF(0, 0, self.width(), self.height())
            self.particles = [Particle(bounds) for _ in range(self.num_particles)]
            self._particles_initialized = True

    def start_animation(self):
        if not self.isVisible():
            return
        if not self._particles_initialized and self.width() > 0 and self.height() > 0:
            self._initialize_particles()
        
        if self._particles_initialized and not self.timer.isActive():
            self.timer.start(30) # Approx 33 FPS

    def stop_animation(self):
        self.timer.stop()

    def update_particles_and_repaint(self):
        if not self.isVisible() or not self._particles_initialized:
            self.stop_animation()
            return
        for p in self.particles:
            p.update()
        self.update() 

    def paintEvent(self, event):
        if not self._particles_initialized:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        for p in self.particles:
            painter.setBrush(p.color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(p.pos, p.size, p.size)
        super().paintEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.width() > 0 and self.height() > 0:
            new_bounds = QRectF(0, 0, self.width(), self.height())
            if not self._particles_initialized:
                self._initialize_particles()
            else:
                for p in self.particles:
                    p.bounds = new_bounds
                    if not new_bounds.contains(p.pos): # If resize made particle out of bounds
                        p.reset() # Or p.pos = QPointF(random.uniform(0, new_bounds.width()), ...)
            
            if self.isVisible() and not self.timer.isActive():
                self.start_animation()
        self.update()

    def showEvent(self, event):
        super().showEvent(event)
        self.start_animation()

    def hideEvent(self, event):
        super().hideEvent(event)
        self.stop_animation()

class BasePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background:transparent;")

        self.particle_effect = ParticleEffectWidget(self) # 创建粒子效果控件作为 BasePage 的子控件
        
        # 确保粒子效果控件在 BasePage 子控件堆叠顺序的最底层，作为背景
        self.particle_effect.lower()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # 当 BasePage 大小改变时，调整粒子效果控件的大小以填充整个 BasePage
        if hasattr(self, 'particle_effect'): # 确保 particle_effect 已创建
             self.particle_effect.setGeometry(self.rect())

    def showEvent(self, event):
        super().showEvent(event)
        # 当 BasePage 显示时，启动粒子动画
        if hasattr(self, 'particle_effect'):
            self.particle_effect.start_animation()

    def hideEvent(self, event):
        super().hideEvent(event)
        # 当 BasePage 隐藏时，停止粒子动画
        if hasattr(self, 'particle_effect'):
            self.particle_effect.stop_animation()
            
    # 可选: 为子页面提供启用/禁用粒子效果的方法
    def set_particles_enabled(self, enabled):
        if hasattr(self, 'particle_effect'):
            if enabled:
                self.particle_effect.show() # 会触发其 showEvent -> start_animation
            else:
                self.particle_effect.hide() # 会触发其 hideEvent -> stop_animation