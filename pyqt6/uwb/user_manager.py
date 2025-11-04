from typing import Tuple, Optional, List
import time


class PositionFilter:
    def __init__(self, history_max_size: int = 5, max_jump_distance: float = 50.0, 
                 smoothing_factor: float = 0.5):

        self.history_max_size = history_max_size
        self.max_jump_distance = max_jump_distance
        self.smoothing_factor = smoothing_factor
        self.position_history: List[Tuple[float, float]] = []
        self.last_position: Optional[Tuple[float, float]] = None
        
    def filter_position(self, x: float, y: float) -> Tuple[float, float]:
        # If this is the first position, accept it directly
        if self.last_position is None:
            self.last_position = (x, y)
            self.position_history.append((x, y))
            return (x, y)
            
        # Calculate distance from last position
        last_x, last_y = self.last_position
        distance = ((x - last_x) ** 2 + (y - last_y) ** 2) ** 0.5
        
        # Outlier detection - limit movement if distance is too large
        if distance > self.max_jump_distance:
            # print(f"Outlier detected: distance {distance:.1f} exceeds threshold {self.max_jump_distance}")
            
            # Limit movement distance while preserving direction
            if distance > 0:
                direction_x = (x - last_x) / distance
                direction_y = (y - last_y) / distance
                x = last_x + direction_x * self.max_jump_distance
                y = last_y + direction_y * self.max_jump_distance
        
        # Add current position to history
        self.position_history.append((x, y))
        
        # Maintain history size limit
        if len(self.position_history) > self.history_max_size:
            self.position_history.pop(0)
        
        # Apply moving average filtering
        if len(self.position_history) > 1:
            # Calculate average of historical positions
            avg_x = sum(pos[0] for pos in self.position_history) / len(self.position_history)
            avg_y = sum(pos[1] for pos in self.position_history) / len(self.position_history)
            
            # Apply smoothing factor - interpolate between current measurement and average
            filtered_x = x * self.smoothing_factor + avg_x * (1 - self.smoothing_factor)
            filtered_y = y * self.smoothing_factor + avg_y * (1 - self.smoothing_factor)
        else:
            filtered_x, filtered_y = x, y
        
        # Update last position
        self.last_position = (filtered_x, filtered_y)
        
        return (filtered_x, filtered_y)
    
    def reset(self):
        """Reset filter state"""
        self.position_history.clear()
        self.last_position = None


class UserData:
    def __init__(self, mac: str, x: float = 0.0, y: float = 0.0, z: float = 0.0):
        self.mac = mac
        self.current_position = (x, y, z)
        self.last_position: Optional[Tuple[float, float, float]] = None
        self.filter = PositionFilter()
        self.last_update_time = time.time()
        self.has_new_data = False
        
        # Card information
        self.card_no: Optional[str] = None
        self.balance: Optional[float] = None
        
        # Interpolation animation properties
        self.target_position: Optional[Tuple[float, float, float]] = None
        self.animation_start_position: Optional[Tuple[float, float, float]] = None
        self.animation_start_time: float = 0.0
        self.animation_duration: float = 0.25  # BM: 250ms animation duration
        self.is_animating: bool = False
        
    def update_position(self, x: float, y: float, z: float = 0.0) -> bool:
        # Apply filtering to 2D coordinates
        filtered_x, filtered_y = self.filter.filter_position(x, y)
        
        # Store previous position
        self.last_position = self.current_position
        
        # Set target position for animation
        new_target = (filtered_x, filtered_y, z)
        
        # Check if position changed significantly (threshold: 1 unit)
        # Three-level movement detection
        if self.last_position:
            distance = ((filtered_x - self.last_position[0]) ** 2 + 
                       (filtered_y - self.last_position[1]) ** 2) ** 0.5
            # BM: 用户移动3级处理机制
            if distance < 5.0:  # Small movement - ignore
                return False
            elif distance > 5.0:  # Large movement - start animation 
                # Start interpolation animation
                self.animation_start_position = self.current_position
                self.target_position = new_target
                self.animation_start_time = time.time()
                self.is_animating = True
                self.last_update_time = time.time()
                self.has_new_data = True
                return True
            else:  # Medium movement (3.0 - 10.0) - direct update
                # Medium movement, update directly without animation
                self.current_position = new_target
                self.last_update_time = time.time()
                self.has_new_data = True
                return True
        else:
            # First position, set directly
            self.current_position = new_target
            self.last_update_time = time.time()
            self.has_new_data = True
            return True
    
    def update_animation(self) -> bool:
        """Update interpolation animation, returns True if animation is still active"""
        if not self.is_animating or not self.target_position or not self.animation_start_position:
            return False
            
        current_time = time.time()
        elapsed_time = current_time - self.animation_start_time
        
        if elapsed_time >= self.animation_duration:
            # Animation completed
            self.current_position = self.target_position
            self.is_animating = False
            self.target_position = None
            self.animation_start_position = None
            return False
        
        # Calculate interpolation progress (0.0 to 1.0)
        progress = elapsed_time / self.animation_duration
        
        # Apply easing function for smoother animation (ease-out)
        eased_progress = 1 - (1 - progress) ** 3
        
        # Interpolate between start and target positions
        start_x, start_y, start_z = self.animation_start_position
        target_x, target_y, target_z = self.target_position
        
        current_x = start_x + (target_x - start_x) * eased_progress
        current_y = start_y + (target_y - start_y) * eased_progress
        current_z = start_z + (target_z - start_z) * eased_progress
        
        self.current_position = (current_x, current_y, current_z)
        return True
    
    def get_screen_position(self, center_x: float, center_y: float, scale: float) -> Tuple[float, float]:
        """Convert world coordinates to screen coordinates"""
        x, y, _ = self.current_position
        screen_x = center_x + x * scale
        screen_y = center_y + y * scale
        return (screen_x, screen_y)
    
    def update_card_info(self, card_no: Optional[str] = None, balance: Optional[float] = None):
        """Update card number and balance information"""
        if card_no is not None:
            self.card_no = str(card_no)
        if balance is not None:
            self.balance = balance
    
    def mark_processed(self):
        """Mark that this user's data has been processed"""
        self.has_new_data = False


class MultiUserManager:
    def __init__(self, max_users: int = 10):
        self.max_users = max_users
        self.users: dict[str, UserData] = {}  # MAC -> UserData mapping
        self.user_colors = [
            (255, 100, 100),  # Red
            (100, 255, 100),  # Green
            (100, 100, 255),  # Blue
            (255, 255, 100),  # Yellow
            (255, 100, 255),  # Magenta
            (100, 255, 255),  # Cyan
            (255, 150, 100),  # Orange
            (150, 100, 255),  # Purple
            (100, 255, 150),  # Light Green
            (255, 100, 150),  # Pink
        ]
    
    def update_user_position(self, mac: str, x: float, y: float, z: float = 0.0) -> bool:
        # Check if user exists
        if mac not in self.users:
            # Check if we can add new user
            if len(self.users) >= self.max_users:
                print(f"Maximum users ({self.max_users}) reached, ignoring new user {mac}")
                return False
            
            # Add new user
            self.users[mac] = UserData(mac, x, y, z)
            print(f"Added new user: {mac}")
            return True
        
        # Update existing user
        return self.users[mac].update_position(x, y, z)
    
    def update_user_card_info(self, mac: str, card_no: Optional[str] = None, balance: Optional[float] = None):
        """Update user card information"""
        if mac in self.users:
            self.users[mac].update_card_info(card_no, balance)
    
    def get_users_with_updates(self) -> List[UserData]:
        """Get list of users that have new data to process"""
        return [user for user in self.users.values() if user.has_new_data]
    
    def get_all_users(self) -> List[UserData]:
        """Get list of all users"""
        return list(self.users.values())
    
    def get_user_color(self, mac: str) -> Tuple[int, int, int]:
        """Get color for a specific user based on their MAC"""
        if mac not in self.users:
            return (180, 120, 220)  # Default color
        
        # Use hash of MAC to get consistent color index
        color_index = hash(mac) % len(self.user_colors)
        return self.user_colors[color_index]
    
    def remove_inactive_users(self, timeout_seconds: float = 30.0):
        """Remove users that haven't been updated recently"""
        current_time = time.time()
        inactive_users = []
        
        for mac, user in self.users.items():
            if current_time - user.last_update_time > timeout_seconds:
                inactive_users.append(mac)
        
        for mac in inactive_users:
            del self.users[mac]
            print(f"Removed inactive user: {mac}")
    
    def update_animations(self) -> bool:
        """Update animations for all users, returns True if any user is still animating"""
        has_active_animations = False
        for user in self.users.values():
            if user.update_animation():
                has_active_animations = True
                user.has_new_data = True  # Mark for redraw
        return has_active_animations
    
    def clear_all_users(self):
        """Clear all users"""
        self.users.clear()