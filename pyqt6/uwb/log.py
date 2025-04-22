from rich.logging import RichHandler
import logging
from logging.handlers import RotatingFileHandler
import os

class Logger:
    def __init__(self, name="rich", log_level=logging.INFO, app_path=None):
        # 使用传入的应用路径或默认当前工作目录
        base_dir = app_path if app_path else os.getcwd()
        self.log_dir = os.path.join(base_dir, 'UWBLogs')
        self.loggers = {}
        os.makedirs(self.log_dir, exist_ok=True)

        # 创建二级文件夹
        self.text_log_dir = os.path.join(self.log_dir, 'text_logs')
        self.csv_log_dir = os.path.join(self.log_dir, 'csv_logs')
        os.makedirs(self.text_log_dir, exist_ok=True)
        os.makedirs(self.csv_log_dir, exist_ok=True)

        # 定义不同的日志格式
        self.text_format = "[%(asctime)s.%(msecs)03d] | %(message)s"
        self.csv_format = "%(message)s"

        # 日志格式化器
        self.text_formatter = logging.Formatter(
            fmt=self.text_format,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.csv_formatter = logging.Formatter(
            fmt=self.csv_format
        )

        # 基础配置（移除文件处理器，只保留控制台输出）
        logging.basicConfig(
            level=log_level,
            format=self.text_format,
            datefmt='%Y-%m-%d %H:%M:%S',
            handlers=[
                RichHandler(rich_tracebacks=True)
            ]
        )

        # 获取logger
        self.log = logging.getLogger(name)
        self.log.setLevel(log_level)

        # 添加控制台输出
        console_handler = RichHandler(rich_tracebacks=True)
        console_handler.setFormatter(self.text_formatter)  # 使用 text_formatter
        self.log.addHandler(console_handler)

        # 存储不同用途的logger
        self.loggers = {}

    def create_logger(self, name, filename, format_type='text'):
        """创建新的日志记录器
        format_type: 'text' 或 'csv'
        """
        logger = logging.getLogger(f"{self.log.name}.{name}")

        # 移除旧的处理器
        if name in self.loggers:
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)
        
        # 根据日志类型选择文件夹
        if format_type == 'csv':
            self.loggers[name] = {'logger': logger, 'type': 'csv'}
            log_path = os.path.join(self.csv_log_dir, filename)
            handler = RotatingFileHandler(
                log_path,
                maxBytes=10*1024*1024,
                backupCount=5,
                encoding='utf-8'
            )
            handler.setFormatter(self.csv_formatter)
            logger.addHandler(handler)
            self.loggers[name] = {'logger': logger, 'type': 'csv'}
        else:
            self.loggers[name] = {'logger': logger, 'type': 'text'}
            log_path = os.path.join(self.text_log_dir, filename)
            handler = RotatingFileHandler(
                log_path,
                maxBytes=10*1024*1024,
                backupCount=5,
                encoding='utf-8'
            )
            handler.setFormatter(self.text_formatter)
            logger.addHandler(handler)
            self.loggers[name] = {'logger': logger, 'type': 'text'}
        return logger

    def log_to(self, logger_name, level, message):
        """向指定的日志文件写入日志"""
        logger_info = self.loggers.get(logger_name)
        if logger_info is None:
            raise ValueError(f"Logger '{logger_name}' not found")
        
        logger = logger_info['logger']
        if logger_info['type'] == 'csv':
            # CSV 格式直接写入，不需要日志级别
            logger.info(message)
        else:
            # 文本格式根据级别写入
            if level == 'info':
                logger.info(message)
            elif level == 'warning':
                logger.warning(message)
            elif level == 'error':
                logger.error(message)
            elif level == 'debug':
                logger.debug(message)
            elif level == 'critical':
                logger.critical(message)

# 使用示例
if __name__ == "__main__":
    logger = Logger()
    
    # 创建不同格式的日志文件
    logger.create_logger("normal", "normal.log", "text")
    logger.create_logger("data", "data.csv", "csv")
    
    # 写入标准格式日志（需要指定日志级别）
    logger.log_to("normal", "info", "这是标准格式日志")
    logger.log_to("normal", "info", "这是标准格式日志")
    
    # 写入CSV格式数据（日志级别参数会被忽略）
    logger.log_to("data", "info", "123,456,789")

    logger.create_logger("normal", "normal_test.log", "text")
    logger.log_to("normal", "info", "这是标准格式日志")