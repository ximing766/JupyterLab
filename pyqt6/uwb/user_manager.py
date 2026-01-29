from typing import Tuple, Optional, List
import time
import math


class SimpleKalmanFilter:
    """
    Simple 1D Kalman Filter implementation
    """
    def __init__(self, R=1.0, Q=0.1):
        self.R = R  # Measurement noise covariance (measurement uncertainty)
        self.Q = Q  # Process noise covariance (prediction uncertainty)
        self.P = 1.0  # Estimation error covariance
        self.x = None # State estimate
        
    def update(self, measurement):
        # Initialize if first measurement
        if self.x is None:
            self.x = measurement
            self.P = 1.0
            return self.x
            
        # Prediction update
        # Assuming constant state model for position (velocity is process noise)
        self.P = self.P + self.Q
        
        # Measurement update
        K = self.P / (self.P + self.R)  # Kalman Gain
        self.x = self.x + K * (measurement - self.x)
        self.P = (1 - K) * self.P
        
        return self.x
        
    def reset(self):
        self.x = None
        self.P = 1.0


class PositionFilter:
    def __init__(self, history_max_size: int = 5, max_jump_distance: float = 50.0):
        self.history_max_size = history_max_size
        self.max_jump_distance = max_jump_distance
        self.position_history: List[Tuple[float, float]] = []
        self.last_position: Optional[Tuple[float, float]] = None
        
        # Initialize Kalman filters for X and Y coordinates
        # R=10.0 (high measurement noise for UWB), Q=0.5 (users move relatively smoothly)
        self.kf_x = SimpleKalmanFilter(R=5.0, Q=0.5)
        self.kf_y = SimpleKalmanFilter(R=5.0, Q=0.5)
        
    def filter_position(self, x: float, y: float) -> Tuple[float, float]:
        # If this is the first position, accept it directly
        if self.last_position is None:
            self.last_position = (x, y)
            self.position_history.append((x, y))
            self.kf_x.update(x)
            self.kf_y.update(y)
            return (x, y)
            
        # Calculate distance from last position (raw data)
        last_x, last_y = self.last_position
        distance = ((x - last_x) ** 2 + (y - last_y) ** 2) ** 0.5
        
        # Outlier detection - limit movement if distance is too large
        if distance > self.max_jump_distance:
            # Limit movement distance while preserving direction
            if distance > 0:
                direction_x = (x - last_x) / distance
                direction_y = (y - last_y) / distance
                x = last_x + direction_x * self.max_jump_distance
                y = last_y + direction_y * self.max_jump_distance
        
        # Apply Kalman Filter
        filtered_x = self.kf_x.update(x)
        filtered_y = self.kf_y.update(y)
        
        # Add current position to history
        self.position_history.append((filtered_x, filtered_y))
        
        # Maintain history size limit
        if len(self.position_history) > self.history_max_size:
            self.position_history.pop(0)
        
        # Update last position
        self.last_position = (filtered_x, filtered_y)
        
        return (filtered_x, filtered_y)
    
    def reset(self):
        """Reset filter state"""
        self.position_history.clear()
        self.last_position = None
        self.kf_x.reset()
        self.kf_y.reset()


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
        self.animation_duration: float = 0.25  # Default 250ms
        self.is_animating: bool = False
        
        # Stationary state tracking
        self.is_stationary: bool = False
        self.stationary_start_time: float = 0.0
        
    def update_position(self, x: float, y: float, z: float = 0.0) -> bool:
        current_time = time.time()
        
        # Calculate dynamic animation duration based on update interval
        # Use smoothed update interval to avoid jitter
        time_diff = current_time - self.last_update_time
        if time_diff > 0.05 and time_diff < 2.0:  # Valid interval (50ms - 2s)
             # Slightly larger than interval to ensure smooth transition (1.2x -> 1.1x)
             # Reduced multiplier for snappier response
            self.animation_duration = time_diff * 1.1
            
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
            if distance < 5.0:  # Small movement - stationary with feedback
                # Update timestamp but keep position fixed to avoid jitter
                self.last_update_time = current_time
                self.has_new_data = True # Trigger redraw for feedback effect
                
                if not self.is_stationary:
                    self.is_stationary = True
                    self.stationary_start_time = current_time
                
                return False
            elif distance > 5.0:  # Large movement - start animation 
                # Start interpolation animation
                self.animation_start_position = self.current_position
                self.target_position = new_target
                self.animation_start_time = current_time
                self.is_animating = True
                self.last_update_time = current_time
                self.has_new_data = True
                self.is_stationary = False
                return True
            else:  # Medium movement (3.0 - 10.0) - direct update
                # Should not be reached given logic above, but kept for safety
                self.current_position = new_target
                self.last_update_time = current_time
                self.has_new_data = True
                self.is_stationary = False
                return True
        else:
            # First position, set directly
            self.current_position = new_target
            self.last_update_time = current_time
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
        
        # Apply easing function for smoother animation
        # Changed from Cubic to Quadratic for smoother continuous movement
        eased_progress = 1 - (1 - progress) ** 2
        
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