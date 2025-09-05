import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.animation import FuncAnimation
import random
import math

# 设置matplotlib支持中文显示
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class GridMap:
    """栅格地图类"""
    def __init__(self, width, height, resolution=0.1):
        self.width = width  # 地图宽度（米）
        self.height = height  # 地图高度（米）
        self.resolution = resolution  # 栅格分辨率（米/像素）
        self.grid_width = int(width / resolution)
        self.grid_height = int(height / resolution)
        
        # 创建栅格地图，0表示自由空间，1表示障碍物
        self.grid = np.zeros((self.grid_height, self.grid_width))
        self._create_sample_map()
    
    def _create_sample_map(self):
        """创建示例地图"""
        # 添加边界墙
        self.grid[0, :] = 1  # 上边界
        self.grid[-1, :] = 1  # 下边界
        self.grid[:, 0] = 1  # 左边界
        self.grid[:, -1] = 1  # 右边界
        
        # 添加一些内部障碍物
        # 矩形障碍物1
        self.grid[20:40, 30:50] = 1
        # 矩形障碍物2
        self.grid[60:80, 70:90] = 1
        # L形障碍物
        self.grid[40:70, 120:140] = 1
        self.grid[50:90, 120:160] = 1
    
    def world_to_grid(self, x, y):
        """世界坐标转栅格坐标"""
        grid_x = int(x / self.resolution)
        grid_y = int(y / self.resolution)
        return grid_x, grid_y
    
    def grid_to_world(self, grid_x, grid_y):
        """栅格坐标转世界坐标"""
        x = grid_x * self.resolution
        y = grid_y * self.resolution
        return x, y
    
    def is_occupied(self, x, y):
        """检查世界坐标点是否被占用"""
        grid_x, grid_y = self.world_to_grid(x, y)
        if 0 <= grid_x < self.grid_width and 0 <= grid_y < self.grid_height:
            return self.grid[grid_y, grid_x] == 1
        return True  # 超出边界视为占用

class Particle:
    """粒子类"""
    def __init__(self, x, y, theta, weight=1.0):
        self.x = x  # x坐标
        self.y = y  # y坐标
        self.theta = theta  # 朝向角度
        self.weight = weight  # 权重

class ACML:
    """自适应蒙特卡洛定位算法"""
    def __init__(self, grid_map, num_particles=1000):
        self.grid_map = grid_map
        self.num_particles = num_particles
        self.particles = []
        self.estimated_pose = [0, 0, 0]  # [x, y, theta]
        
        # 噪声参数
        self.motion_noise_std = [0.1, 0.1, 0.05]  # [x, y, theta]的标准差
        self.sensor_noise_std = 0.2
        
        # 重采样参数
        self.resample_threshold = 0.5  # 有效粒子数阈值
        
        self._initialize_particles()
    
    def _initialize_particles(self):
        """初始化粒子群"""
        self.particles = []
        for _ in range(self.num_particles):
            # 在自由空间随机生成粒子
            while True:
                x = random.uniform(0, self.grid_map.width)
                y = random.uniform(0, self.grid_map.height)
                if not self.grid_map.is_occupied(x, y):
                    theta = random.uniform(0, 2 * math.pi)
                    self.particles.append(Particle(x, y, theta))
                    break
    
    def predict(self, control_input):
        """预测步骤：根据控制输入更新粒子位置"""
        dx, dy, dtheta = control_input
        
        for particle in self.particles:
            # 添加运动噪声
            noise_x = np.random.normal(0, self.motion_noise_std[0])
            noise_y = np.random.normal(0, self.motion_noise_std[1])
            noise_theta = np.random.normal(0, self.motion_noise_std[2])
            
            # 更新粒子位置
            particle.x += dx + noise_x
            particle.y += dy + noise_y
            particle.theta += dtheta + noise_theta
            
            # 角度归一化
            particle.theta = self._normalize_angle(particle.theta)
    
    def update(self, sensor_data):
        """更新步骤：根据传感器数据更新粒子权重"""
        total_weight = 0
        
        for particle in self.particles:
            # 计算粒子的似然度（这里简化为距离传感器模型）
            likelihood = self._calculate_likelihood(particle, sensor_data)
            particle.weight = likelihood
            total_weight += likelihood
        
        # 归一化权重
        if total_weight > 0:
            for particle in self.particles:
                particle.weight /= total_weight
        
        # 计算有效粒子数
        effective_particles = self._calculate_effective_particles()
        
        # 如果有效粒子数过低，进行重采样
        if effective_particles < self.resample_threshold * self.num_particles:
            self._resample()
    
    def _calculate_likelihood(self, particle, sensor_data):
        """计算粒子的似然度"""
        # 简化的传感器模型：假设sensor_data是机器人的真实位置
        true_x, true_y = sensor_data
        
        # 计算粒子与真实位置的距离
        distance = math.sqrt((particle.x - true_x)**2 + (particle.y - true_y)**2)
        
        # 使用高斯分布计算似然度
        likelihood = math.exp(-0.5 * (distance / self.sensor_noise_std)**2)
        
        # 如果粒子在障碍物中，权重设为很小的值
        if self.grid_map.is_occupied(particle.x, particle.y):
            likelihood *= 0.01
        
        return likelihood
    
    def _calculate_effective_particles(self):
        """计算有效粒子数"""
        sum_weights_squared = sum(p.weight**2 for p in self.particles)
        if sum_weights_squared == 0:
            return 0
        return 1.0 / sum_weights_squared
    
    def _resample(self):
        """重采样粒子"""
        # 使用轮盘赌算法重采样
        weights = [p.weight for p in self.particles]
        new_particles = []
        
        # 累积分布函数
        cumulative_weights = np.cumsum(weights)
        
        for _ in range(self.num_particles):
            r = random.uniform(0, cumulative_weights[-1])
            for i, cum_weight in enumerate(cumulative_weights):
                if r <= cum_weight:
                    # 复制选中的粒子并添加少量噪声
                    old_particle = self.particles[i]
                    new_particle = Particle(
                        old_particle.x + np.random.normal(0, 0.05),
                        old_particle.y + np.random.normal(0, 0.05),
                        old_particle.theta + np.random.normal(0, 0.02),
                        1.0 / self.num_particles
                    )
                    new_particles.append(new_particle)
                    break
        
        self.particles = new_particles
    
    def get_estimated_pose(self):
        """获取估计位姿（加权平均）"""
        if not self.particles:
            return self.estimated_pose
        
        total_weight = sum(p.weight for p in self.particles)
        if total_weight == 0:
            return self.estimated_pose
        
        # 计算加权平均位置
        weighted_x = sum(p.x * p.weight for p in self.particles) / total_weight
        weighted_y = sum(p.y * p.weight for p in self.particles) / total_weight
        
        # 计算加权平均角度（需要特殊处理）
        sin_sum = sum(math.sin(p.theta) * p.weight for p in self.particles) / total_weight
        cos_sum = sum(math.cos(p.theta) * p.weight for p in self.particles) / total_weight
        weighted_theta = math.atan2(sin_sum, cos_sum)
        
        self.estimated_pose = [weighted_x, weighted_y, weighted_theta]
        return self.estimated_pose
    
    def _normalize_angle(self, angle):
        """角度归一化到[-π, π]"""
        while angle > math.pi:
            angle -= 2 * math.pi
        while angle < -math.pi:
            angle += 2 * math.pi
        return angle
    
    def refresh_position(self, control_input, sensor_data):
        """刷新位置：ACML的核心更新流程"""
        # 1. 预测步骤：根据控制输入移动粒子
        self.predict(control_input)
        
        # 2. 更新步骤：根据传感器数据更新权重
        self.update(sensor_data)
        
        # 3. 估计当前位姿
        estimated_pose = self.get_estimated_pose()
        
        return estimated_pose

class ACMLVisualizer:
    """ACML可视化类"""
    def __init__(self, acml):
        self.acml = acml
        self.fig, self.ax = plt.subplots(figsize=(12, 8))
        self.particle_scatter = None
        self.robot_marker = None
        self.estimated_marker = None
        
    def setup_plot(self):
        """设置绘图"""
        # 显示栅格地图
        self.ax.imshow(self.acml.grid_map.grid, cmap='gray_r', 
                      extent=[0, self.acml.grid_map.width, 0, self.acml.grid_map.height],
                      origin='lower')
        
        self.ax.set_xlim(0, self.acml.grid_map.width)
        self.ax.set_ylim(0, self.acml.grid_map.height)
        self.ax.set_xlabel('X坐标 (米)')
        self.ax.set_ylabel('Y坐标 (米)')
        self.ax.set_title('ACML自适应蒙特卡洛定位算法演示 - 栅格地图')
        self.ax.grid(True, alpha=0.3)
        
        # 添加图例
        legend_elements = [
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='blue', 
                      markersize=8, label='粒子群'),
            plt.Line2D([0], [0], marker='s', color='w', markerfacecolor='red', 
                      markersize=10, label='机器人真实位置'),
            plt.Line2D([0], [0], marker='^', color='w', markerfacecolor='green', 
                      markersize=10, label='算法估计位置')
        ]
        self.ax.legend(handles=legend_elements, loc='upper right')
    
    def update_plot(self, true_position):
        """更新绘图"""
        # 清除之前的粒子
        if self.particle_scatter:
            self.particle_scatter.remove()
        if self.robot_marker:
            self.robot_marker.remove()
        if self.estimated_marker:
            self.estimated_marker.remove()
        
        # 绘制粒子
        particle_x = [p.x for p in self.acml.particles]
        particle_y = [p.y for p in self.acml.particles]
        particle_weights = [p.weight for p in self.acml.particles]
        
        # 根据权重调整粒子大小和透明度
        max_weight = max(particle_weights) if particle_weights else 1
        sizes = [max(1, w/max_weight * 50) for w in particle_weights]
        alphas = [max(0.1, w/max_weight) for w in particle_weights]
        
        self.particle_scatter = self.ax.scatter(particle_x, particle_y, 
                                              s=sizes, c='blue', alpha=0.6)
        
        # 绘制真实机器人位置
        self.robot_marker = self.ax.scatter(true_position[0], true_position[1], 
                                          s=100, c='red', marker='s', 
                                          label='真实位置')
        
        # 绘制估计位置
        estimated_pose = self.acml.get_estimated_pose()
        self.estimated_marker = self.ax.scatter(estimated_pose[0], estimated_pose[1], 
                                              s=100, c='green', marker='^', 
                                              label='估计位置')
        
        plt.draw()
        plt.pause(0.1)

def demo_acml():
    """ACML演示函数"""
    # 创建栅格地图
    grid_map = GridMap(width=20, height=10, resolution=0.1)
    
    # 创建ACML定位器
    acml = ACML(grid_map, num_particles=500)
    
    # 创建可视化器
    visualizer = ACMLVisualizer(acml)
    visualizer.setup_plot()
    
    # 模拟机器人运动
    true_position = [2.0, 2.0, 0.0]  # [x, y, theta]
    
    print("=== ACML自适应蒙特卡洛定位算法演示开始 ===")
    print("📍 绿色三角形：算法估计的机器人位置")
    print("🤖 红色方块：机器人真实位置")
    print("🔵 蓝色圆点：粒子群（圆点大小表示粒子权重）")
    print("⚠️  按Ctrl+C可随时停止演示")
    print("\n算法说明：ACML通过大量粒子模拟可能的机器人位置，")
    print("根据传感器数据不断调整粒子权重，最终收敛到真实位置。")
    
    try:
        for step in range(100):
            # 模拟控制输入（机器人运动）
            if step < 30:
                control_input = [0.1, 0.0, 0.0]  # 向右移动
            elif step < 60:
                control_input = [0.0, 0.1, 0.0]  # 向上移动
            else:
                control_input = [-0.05, 0.05, 0.02]  # 斜向移动并旋转
            
            # 更新真实位置
            true_position[0] += control_input[0]
            true_position[1] += control_input[1]
            true_position[2] += control_input[2]
            
            # 确保机器人不会撞墙
            true_position[0] = max(0.5, min(true_position[0], grid_map.width - 0.5))
            true_position[1] = max(0.5, min(true_position[1], grid_map.height - 0.5))
            
            # ACML位置刷新
            estimated_pose = acml.refresh_position(control_input, 
                                                 (true_position[0], true_position[1]))
            
            # 更新可视化
            visualizer.update_plot(true_position)
            
            # 打印定位误差
            error = math.sqrt((estimated_pose[0] - true_position[0])**2 + 
                            (estimated_pose[1] - true_position[1])**2)
            print(f"步骤 {step+1}: 定位误差 = {error:.3f}m")
            
    except KeyboardInterrupt:
        print("\n演示结束")
    
    plt.show()

if __name__ == "__main__":
    demo_acml()