import pygame
import sys
import math
import os
import requests
from PIL import Image
from enum import Enum
from typing import List, Tuple, Optional
import threading
import time

# 游戏常量
WIDTH = 1200
HEIGHT = 800
FPS = 60
GRID_SIZE = 40
MAP_WIDTH = WIDTH // GRID_SIZE
MAP_HEIGHT = HEIGHT // GRID_SIZE

# 颜色定义
COLORS = {
    'BLACK': (0, 0, 0),
    'WHITE': (255, 255, 255),
    'GREEN': (0, 255, 0),
    'RED': (255, 0, 0),
    'BLUE': (0, 0, 255),
    'YELLOW': (255, 255, 0),
    'GRAY': (128, 128, 128),
    'LIGHT_GRAY': (200, 200, 200),
    'DARK_GREEN': (0, 128, 0),
    'DARK_RED': (128, 0, 0),
    'DARK_BLUE': (0, 0, 128),
    'ORANGE': (255, 165, 0)
}

class TerrainType(Enum):
    PLAINS = 1
    FOREST = 2
    MOUNTAIN = 3
    WATER = 4
    CITY = 5

class Player(Enum):
    NEUTRAL = 0
    PLAYER1 = 1
    PLAYER2 = 2
    PLAYER3 = 3

class RealMapLoader:
    """真实地图瓦片加载器"""
    
    def __init__(self, cache_dir="map_cache"):
        self.cache_dir = cache_dir
        self.tile_size = 256
        self.user_agent = "WarStrategyGame/1.0"
        self.base_url = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
        
        # 创建缓存目录
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
    
    def deg2num(self, lat_deg, lon_deg, zoom):
        """将经纬度转换为瓦片坐标"""
        lat_rad = math.radians(lat_deg)
        n = 2.0 ** zoom
        xtile = int((lon_deg + 180.0) / 360.0 * n)
        ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
        return (xtile, ytile)
    
    def num2deg(self, xtile, ytile, zoom):
        """将瓦片坐标转换为经纬度"""
        n = 2.0 ** zoom
        lon_deg = xtile / n * 360.0 - 180.0
        lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
        lat_deg = math.degrees(lat_rad)
        return (lat_deg, lon_deg)
    
    def get_tile_filename(self, x, y, z):
        """获取瓦片缓存文件名"""
        return os.path.join(self.cache_dir, f"tile_{z}_{x}_{y}.png")
    
    def download_tile(self, x, y, z):
        """下载单个瓦片"""
        filename = self.get_tile_filename(x, y, z)
        
        # 如果文件已存在，直接返回
        if os.path.exists(filename):
            return filename
        
        try:
            url = self.base_url.format(x=x, y=y, z=z)
            headers = {'User-Agent': self.user_agent}
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            with open(filename, 'wb') as f:
                f.write(response.content)
            
            print(f"下载瓦片: {filename}")
            return filename
            
        except Exception as e:
            print(f"下载瓦片失败 {x},{y},{z}: {e}")
            return None
    
    def load_map_area(self, center_lat, center_lon, zoom, width_tiles, height_tiles):
        """加载指定区域的地图瓦片"""
        center_x, center_y = self.deg2num(center_lat, center_lon, zoom)
        
        # 计算需要下载的瓦片范围
        start_x = center_x - width_tiles // 2
        end_x = center_x + width_tiles // 2
        start_y = center_y - height_tiles // 2
        end_y = center_y + height_tiles // 2
        
        tiles = []
        for y in range(start_y, end_y + 1):
            row = []
            for x in range(start_x, end_x + 1):
                filename = self.download_tile(x, y, zoom)
                if filename:
                    row.append(filename)
                else:
                    row.append(None)
            tiles.append(row)
        
        return tiles
    
    def create_map_surface(self, tiles):
        """将瓦片组合成一个pygame surface"""
        if not tiles or not tiles[0]:
            return None
        
        rows = len(tiles)
        cols = len(tiles[0])
        
        # 创建合成图像
        total_width = cols * self.tile_size
        total_height = rows * self.tile_size
        
        combined_image = Image.new('RGB', (total_width, total_height))
        
        for row_idx, row in enumerate(tiles):
            for col_idx, tile_file in enumerate(row):
                if tile_file and os.path.exists(tile_file):
                    try:
                        tile_image = Image.open(tile_file)
                        x_offset = col_idx * self.tile_size
                        y_offset = row_idx * self.tile_size
                        combined_image.paste(tile_image, (x_offset, y_offset))
                    except Exception as e:
                        print(f"加载瓦片图像失败 {tile_file}: {e}")
        
        # 转换为pygame surface
        mode = combined_image.mode
        size = combined_image.size
        data = combined_image.tobytes()
        
        surface = pygame.image.fromstring(data, size, mode)
        return surface

class Territory:
    def __init__(self, x: int, y: int, terrain_type: TerrainType):
        self.x = x
        self.y = y
        self.terrain_type = terrain_type
        self.owner = Player.NEUTRAL
        self.troops = 1
        self.selected = False
        self.highlighted = False
        
    def get_color(self, use_real_map=False):
        """根据所有者和地形类型返回颜色"""
        if self.selected:
            return COLORS['YELLOW']
        elif self.highlighted:
            return COLORS['ORANGE']
        elif self.owner == Player.PLAYER1:
            return COLORS['BLUE'] if not use_real_map else (*COLORS['BLUE'], 128)  # 半透明
        elif self.owner == Player.PLAYER2:
            return COLORS['RED'] if not use_real_map else (*COLORS['RED'], 128)   # 半透明
        elif self.owner == Player.PLAYER3:
            return COLORS['GREEN'] if not use_real_map else (*COLORS['GREEN'], 128) # 半透明
        else:
            if use_real_map:
                return None  # 中性区域在真实地图模式下不显示颜色
            # 中性区域根据地形类型显示
            terrain_colors = {
                TerrainType.PLAINS: COLORS['LIGHT_GRAY'],
                TerrainType.FOREST: COLORS['DARK_GREEN'],
                TerrainType.MOUNTAIN: COLORS['GRAY'],
                TerrainType.WATER: COLORS['DARK_BLUE'],
                TerrainType.CITY: COLORS['WHITE']
            }
            return terrain_colors.get(self.terrain_type, COLORS['LIGHT_GRAY'])
    
    def can_attack_from(self, other_territory) -> bool:
        """检查是否可以从另一个区域攻击此区域"""
        # 相邻区域才能攻击
        dx = abs(self.x - other_territory.x)
        dy = abs(self.y - other_territory.y)
        return (dx <= 1 and dy <= 1) and (dx + dy > 0)
    
    def get_defense_bonus(self) -> float:
        """根据地形类型获取防御加成"""
        bonuses = {
            TerrainType.PLAINS: 1.0,
            TerrainType.FOREST: 1.2,
            TerrainType.MOUNTAIN: 1.5,
            TerrainType.WATER: 0.8,
            TerrainType.CITY: 1.3
        }
        return bonuses.get(self.terrain_type, 1.0)

class GameMap:
    def __init__(self, use_real_map=True):
        self.territories = []
        self.real_map_surface = None
        self.map_loader = None
        self.use_real_map = use_real_map
        
        if use_real_map:
            self.map_loader = RealMapLoader()
            self.load_real_map_background()
        
        self.generate_map()
    
    def load_real_map_background(self):
        """加载真实地图背景"""
        try:
            # 使用北京作为中心点 (39.9042, 116.4074)
            # 可以根据需要修改为其他城市
            center_lat = 39.9042
            center_lon = 116.4074
            zoom = 10  # 缩放级别，可以调整
            
            # 计算需要的瓦片数量来覆盖游戏窗口
            tiles_width = (WIDTH // 256) + 2
            tiles_height = (HEIGHT // 256) + 2
            
            print(f"正在加载真实地图: 中心({center_lat}, {center_lon}), 缩放级别{zoom}")
            
            # 在后台线程中加载地图
            def load_map_thread():
                tiles = self.map_loader.load_map_area(
                    center_lat, center_lon, zoom, tiles_width, tiles_height
                )
                self.real_map_surface = self.map_loader.create_map_surface(tiles)
                if self.real_map_surface:
                    # 缩放地图以适应游戏窗口
                    self.real_map_surface = pygame.transform.scale(
                        self.real_map_surface, (WIDTH, HEIGHT)
                    )
                    print("真实地图加载完成")
                else:
                    print("真实地图加载失败")
            
            # 启动后台加载线程
            thread = threading.Thread(target=load_map_thread)
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            print(f"加载真实地图背景失败: {e}")
    
    def generate_map(self):
        """生成游戏地图"""
        # 尝试加载真实地图，如果失败则使用默认地图
        if not self.load_real_map():
            self.load_default_map()
    
    def load_real_map(self):
        """加载真实地图数据"""
        try:
            # 尝试从文件加载地图
            import os
            map_file = "real_map.txt"
            if os.path.exists(map_file):
                with open(map_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for y, line in enumerate(lines[:MAP_HEIGHT]):
                        row = []
                        for x, char in enumerate(line.strip()[:MAP_WIDTH]):
                            terrain = self.char_to_terrain(char)
                            territory = Territory(x, y, terrain)
                            self.setup_initial_ownership(territory, x, y)
                            row.append(territory)
                        # 如果行不够长，用平原填充
                        while len(row) < MAP_WIDTH:
                            territory = Territory(len(row), y, TerrainType.PLAINS)
                            self.setup_initial_ownership(territory, len(row), y)
                            row.append(territory)
                        self.territories.append(row)
                    
                    # 如果行数不够，用平原填充
                    while len(self.territories) < MAP_HEIGHT:
                        row = []
                        y = len(self.territories)
                        for x in range(MAP_WIDTH):
                            territory = Territory(x, y, TerrainType.PLAINS)
                            self.setup_initial_ownership(territory, x, y)
                            row.append(territory)
                        self.territories.append(row)
                    return True
            else:
                # 创建一个示例真实地图文件
                self.create_sample_real_map(map_file)
                return self.load_real_map()  # 递归调用加载刚创建的文件
        except Exception as e:
            print(f"加载真实地图失败: {e}")
            return False
    
    def create_sample_real_map(self, filename):
        """创建一个示例真实地图文件（基于中国地形特征）"""
        # 创建一个简化的中国地形图
        map_data = [
            "WWWWWWWWWWWWWWWWWWWWWWWWWWWWWW",  # 北部边界（水域）
            "WMMMMMMMMMMMMMMMMMMMMMMMMMMMFW",  # 北部山脉
            "WMMFFFFFFFFFFFFFFFFFFFFFFFFFW",  # 东北森林
            "WMMFFFFFPPPPPPPPPPPPPPPPFFFFW",  # 华北平原
            "WMMFFFFFPPPPCCPPPPPPPPPPFFFFW",  # 华北平原（城市）
            "WMMFFFFFPPPPPPPPPPPPPPPPFFFFW",
            "WMMFFFFFPPPPPPPPPPPPPPPPFFFFW",
            "WMMMMFFFPPPPPPPPPPPPPPPPFFFFW",
            "WMMMMFFFPPPPCCPPPPPPPPPPFFFFW",  # 中部城市
            "WMMMMFFFPPPPPPPPPPPPPPPPFFFFW",
            "WMMMMFFFPPPPPPPPPPPPPPPPFFFFW",
            "WMMMMFFFPPPPPPPPPPPPPPPPFFFFW",
            "WMMMMFFFPPPPCCPPPPPPPPPPFFFFW",  # 南部城市
            "WMMMMFFFPPPPPPPPPPPPPPPPFFFFW",
            "WMMMMFFFPPPPPPPPPPPPPPPPFFFFW",
            "WMMMMFFFPPPPPPPPPPPPPPPPFFFFW",
            "WMMMMFFFPPPPPPPPPPPPPPPPFFFFW",
            "WMMMMFFFPPPPPPPPPPPPPPPPFFFFW",
            "WMMMMFFFPPPPPPPPPPPPPPPPFFFFW",
            "WWWWWWWWWWWWWWWWWWWWWWWWWWWWWW",  # 南部边界（水域）
        ]
        
        with open(filename, 'w', encoding='utf-8') as f:
            for line in map_data:
                f.write(line + '\n')
    
    def char_to_terrain(self, char):
        """将字符转换为地形类型"""
        terrain_map = {
            'P': TerrainType.PLAINS,   # 平原
            'F': TerrainType.FOREST,   # 森林
            'M': TerrainType.MOUNTAIN, # 山地
            'W': TerrainType.WATER,    # 水域
            'C': TerrainType.CITY,     # 城市
        }
        return terrain_map.get(char.upper(), TerrainType.PLAINS)
    
    def setup_initial_ownership(self, territory, x, y):
        """设置初始区域所有权"""
        import random
        
        # 设置初始玩家区域（左上角和右下角）
        if x < 3 and y < 3:
            territory.owner = Player.PLAYER1
            territory.troops = random.randint(2, 5)
        elif x > MAP_WIDTH - 4 and y > MAP_HEIGHT - 4:
            territory.owner = Player.PLAYER2
            territory.troops = random.randint(2, 5)
    
    def load_default_map(self):
        """加载默认随机地图（备用方案）"""
        import random
        
        for y in range(MAP_HEIGHT):
            row = []
            for x in range(MAP_WIDTH):
                # 随机生成地形类型
                terrain_roll = random.random()
                if terrain_roll < 0.4:
                    terrain = TerrainType.PLAINS
                elif terrain_roll < 0.6:
                    terrain = TerrainType.FOREST
                elif terrain_roll < 0.75:
                    terrain = TerrainType.MOUNTAIN
                elif terrain_roll < 0.9:
                    terrain = TerrainType.WATER
                else:
                    terrain = TerrainType.CITY
                
                territory = Territory(x, y, terrain)
                self.setup_initial_ownership(territory, x, y)
                row.append(territory)
            self.territories.append(row)
    
    def get_territory(self, x: int, y: int) -> Optional[Territory]:
        """获取指定坐标的区域"""
        if 0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT:
            return self.territories[y][x]
        return None
    
    def get_adjacent_territories(self, territory: Territory) -> List[Territory]:
        """获取相邻区域"""
        adjacent = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                adj_territory = self.get_territory(territory.x + dx, territory.y + dy)
                if adj_territory:
                    adjacent.append(adj_territory)
        return adjacent

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("战争策略游戏")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 16)
        
        self.game_map = GameMap()
        self.current_player = Player.PLAYER1
        self.selected_territory = None
        self.game_phase = "select"  # select, attack, move
        
    def handle_events(self):
        """处理游戏事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左键点击
                    self.handle_mouse_click(event.pos)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.end_turn()
                elif event.key == pygame.K_ESCAPE:
                    self.clear_selection()
                elif event.key == pygame.K_m:
                    self.toggle_map_mode()
        return True
    
    def handle_mouse_click(self, pos: Tuple[int, int]):
        """处理鼠标点击"""
        grid_x = pos[0] // GRID_SIZE
        grid_y = pos[1] // GRID_SIZE
        
        clicked_territory = self.game_map.get_territory(grid_x, grid_y)
        if not clicked_territory:
            return
        
        if self.game_phase == "select":
            if clicked_territory.owner == self.current_player:
                self.select_territory(clicked_territory)
        elif self.game_phase == "attack":
            if self.selected_territory and clicked_territory != self.selected_territory:
                if clicked_territory.owner != self.current_player:
                    self.attack_territory(self.selected_territory, clicked_territory)
    
    def select_territory(self, territory: Territory):
        """选择区域"""
        self.clear_selection()
        self.selected_territory = territory
        territory.selected = True
        self.game_phase = "attack"
        
        # 高亮可攻击的区域
        for adj_territory in self.game_map.get_adjacent_territories(territory):
            if adj_territory.owner != self.current_player:
                adj_territory.highlighted = True
    
    def clear_selection(self):
        """清除选择"""
        if self.selected_territory:
            self.selected_territory.selected = False
        self.selected_territory = None
        self.game_phase = "select"
        
        # 清除高亮
        for row in self.game_map.territories:
            for territory in row:
                territory.highlighted = False
    
    def attack_territory(self, attacker: Territory, defender: Territory):
        """攻击区域"""
        if not defender.can_attack_from(attacker):
            return
        
        if attacker.troops <= 1:
            return  # 至少保留1个兵力
        
        # 计算战斗结果
        import random
        
        attack_power = (attacker.troops - 1) * random.uniform(0.8, 1.2)
        defense_power = defender.troops * defender.get_defense_bonus() * random.uniform(0.8, 1.2)
        
        if attack_power > defense_power:
            # 攻击成功
            defender.owner = attacker.owner
            defender.troops = attacker.troops - 1
            attacker.troops = 1
            print(f"攻击成功！占领了({defender.x}, {defender.y})")
        else:
            # 攻击失败
            attacker.troops = max(1, attacker.troops - 1)
            defender.troops = max(1, defender.troops - 1)
            print(f"攻击失败！")
        
        self.clear_selection()
    
    def end_turn(self):
        """结束回合"""
        self.clear_selection()
        
        # 切换玩家
        if self.current_player == Player.PLAYER1:
            self.current_player = Player.PLAYER2
        else:
            self.current_player = Player.PLAYER1
        
        # 增加兵力（简单的资源系统）
        self.add_reinforcements()
    
    def toggle_map_mode(self):
        """切换地图模式"""
        self.game_map.use_real_map = not self.game_map.use_real_map
        
        if self.game_map.use_real_map and not self.game_map.real_map_surface:
            # 如果切换到真实地图模式但还没有加载，则开始加载
            if not self.game_map.map_loader:
                self.game_map.map_loader = RealMapLoader()
            self.game_map.load_real_map_background()
            print("切换到真实地图模式 - 正在加载...")
        elif self.game_map.use_real_map:
            print("切换到真实地图模式")
        else:
            print("切换到传统地图模式")
    
    def add_reinforcements(self):
        """为当前玩家添加增援"""
        import random
        
        player_territories = []
        for row in self.game_map.territories:
            for territory in row:
                if territory.owner == self.current_player:
                    player_territories.append(territory)
        
        # 每3个区域获得1个增援
        reinforcements = max(1, len(player_territories) // 3)
        
        for _ in range(reinforcements):
            if player_territories:
                territory = random.choice(player_territories)
                territory.troops += 1
    
    def draw(self):
        """绘制游戏画面"""
        self.screen.fill(COLORS['BLACK'])
        
        # 绘制真实地图背景（如果可用）
        if self.game_map.use_real_map and self.game_map.real_map_surface:
            self.screen.blit(self.game_map.real_map_surface, (0, 0))
        
        # 绘制地图区域
        for row in self.game_map.territories:
            for territory in row:
                rect = pygame.Rect(
                    territory.x * GRID_SIZE,
                    territory.y * GRID_SIZE,
                    GRID_SIZE,
                    GRID_SIZE
                )
                
                # 获取区域颜色
                color = territory.get_color(self.game_map.use_real_map)
                
                if color is not None:
                    if len(color) == 4:  # 半透明颜色
                        # 创建半透明surface
                        temp_surface = pygame.Surface((GRID_SIZE, GRID_SIZE), pygame.SRCALPHA)
                        temp_surface.fill(color)
                        self.screen.blit(temp_surface, rect.topleft)
                    else:
                        # 普通颜色
                        pygame.draw.rect(self.screen, color, rect)
                
                # 绘制边框（在真实地图模式下使用更细的边框）
                border_width = 1 if not self.game_map.use_real_map else 1
                border_color = COLORS['BLACK'] if not self.game_map.use_real_map else COLORS['WHITE']
                pygame.draw.rect(self.screen, border_color, rect, border_width)
                
                # 绘制兵力数量
                if territory.troops > 0:
                    text_color = COLORS['BLACK'] if not self.game_map.use_real_map else COLORS['WHITE']
                    text = self.small_font.render(str(territory.troops), True, text_color)
                    text_rect = text.get_rect(center=rect.center)
                    
                    # 在真实地图模式下为文字添加背景
                    if self.game_map.use_real_map:
                        bg_rect = text_rect.inflate(4, 2)
                        pygame.draw.rect(self.screen, (0, 0, 0, 180), bg_rect)
                    
                    self.screen.blit(text, text_rect)
        
        # 绘制UI信息
        self.draw_ui()
        
        pygame.display.flip()
    
    def draw_ui(self):
        """绘制用户界面"""
        # 当前玩家信息
        player_text = f"当前玩家: {self.current_player.name}"
        text_surface = self.font.render(player_text, True, COLORS['WHITE'])
        self.screen.blit(text_surface, (10, 10))
        
        # 游戏阶段信息
        phase_text = f"阶段: {self.game_phase}"
        text_surface = self.font.render(phase_text, True, COLORS['WHITE'])
        self.screen.blit(text_surface, (10, 40))
        
        # 控制说明
        controls = [
            "左键: 选择/攻击区域",
            "空格: 结束回合",
            "ESC: 取消选择",
            "M: 切换地图模式"
        ]
        
        for i, control in enumerate(controls):
            text_surface = self.small_font.render(control, True, COLORS['WHITE'])
            self.screen.blit(text_surface, (10, HEIGHT - 60 + i * 20))
    
    def run(self):
        """运行游戏主循环"""
        running = True
        while running:
            running = self.handle_events()
            self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

def main():
    """主函数"""
    game = Game()
    game.run()

if __name__ == "__main__":
    main()
