# image_utils.py
import os
from PyQt6.QtGui import QPixmap, QIcon
# Assuming constants.py is in the same directory (Doubao/)
from .constants import PIC_FOLDER_NAME, ICON_FILE_NAME, BACKGROUND_IMAGE_FILES, CURRENT_BACKGROUND_IMAGE_INDEX

def get_image_path(filename: str) -> str:
    """Constructs the full path to an image file in the PIC directory."""
    # os.path.dirname(__file__) gives the directory of image_utils.py
    # PIC_FOLDER_NAME is relative to this script's directory
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, PIC_FOLDER_NAME, filename)

def load_pixmap(filename: str):
    """Loads a QPixmap from the PIC directory. Returns the QPixmap or None if failed."""
    path = get_image_path(filename)
    pixmap = QPixmap(path)
    if pixmap.isNull():
        print(f"图片加载失败: {path}")
        return None
    return pixmap

def get_app_icon() -> QIcon:
    """Loads the application icon using ICON_FILE_NAME from constants."""
    path = get_image_path(ICON_FILE_NAME)
    icon = QIcon(path)
    # It's good practice to check if icon loading failed, though QIcon doesn't have isNull() like QPixmap
    # We can check if the path exists or rely on Qt's internal handling for missing icons.
    # For simplicity, we'll assume QIcon handles it gracefully or the path is always valid.
    if not os.path.exists(path):
        print(f"应用图标文件不存在: {path}")
    return icon

def get_background_pixmap():
    """Loads the current background image pixmap based on the BACKGROUND_IMAGE_FILES list and current index in constants."""
    # Import constants here to ensure access to the global variable
    from . import constants

    # Get the current image filename
    current_image_file = constants.BACKGROUND_IMAGE_FILES[constants.CURRENT_BACKGROUND_IMAGE_INDEX]
    
    # Load and return the pixmap
    return load_pixmap(current_image_file)

def cycle_background_image_index():
    """Updates the index for the background image, cycling through the list."""
    from . import constants
    constants.CURRENT_BACKGROUND_IMAGE_INDEX = (constants.CURRENT_BACKGROUND_IMAGE_INDEX + 1) % len(constants.BACKGROUND_IMAGE_FILES)

    