import os
import sys
from pathlib import Path
from gooey import Gooey, GooeyParser

# 尝试导入 pywin32 模块
try:
    import win32com.client
    # 导入 Word 相关的常量
    from win32com.client import constants as wdConstants
except ImportError:
    print("错误: 未安装 pywin32 库。请运行 'pip install pywin32' 进行安装。")
    sys.exit(1)

class WordToPdfConverter:
    """
    将指定目录下的所有Word文档 (.doc, .docx) 转换为PDF。
    """
    def __init__(self):
        self.word_app = None

    def _initialize_word(self):
        """初始化Word应用程序实例。"""
        try:
            self.word_app = win32com.client.Dispatch("Word.Application")
            self.word_app.Visible = False # 不显示Word窗口
            print("Word应用程序初始化成功。")
        except Exception as e:
            print(f"错误: 初始化Word应用程序失败。请确保已安装Microsoft Word。错误信息: {e}")
            self.word_app = None
            raise

    def _close_word(self):
        """关闭Word应用程序实例。"""
        if self.word_app:
            try:
                self.word_app.Quit()
                print("Word应用程序已关闭。")
            except Exception as e:
                print(f"错误: 关闭Word应用程序失败。错误信息: {e}")
            self.word_app = None

    def convert_directory(self, directory_path: str):
        """
        转换指定目录下的所有Word文档为PDF。

        Args:
            directory_path: 包含Word文档的目录路径。
        """
        if not Path(directory_path).is_dir():
            print(f"错误: '{directory_path}' 不是一个有效的目录。")
            return

        print(f"开始转换目录: {directory_path}")

        try:
            self._initialize_word()
            if not self.word_app:
                return # 初始化失败则退出

            for file_path in Path(directory_path).iterdir():
                if file_path.suffix.lower() in ['.doc', '.docx']:
                    print(f"发现Word文件: {file_path}")
                    try:
                        self._convert_file(str(file_path))
                    except Exception as e:
                        print(f"错误: 转换文件 '{file_path}' 失败。错误信息: {e}")
                else:
                    print(f"跳过非Word文件: {file_path}")

        except Exception as e:
            print(f"处理目录 '{directory_path}' 时发生错误: {e}")
        finally:
            self._close_word()
            print("转换过程结束。")


    def _convert_file(self, word_path: str):
        """
        将单个Word文档转换为PDF。

        Args:
            word_path: Word文档的完整路径。
        """
        if not self.word_app:
            print("错误: Word应用程序未初始化。无法转换文件。")
            return

        pdf_path = Path(word_path).with_suffix('.pdf')
        print(f"正在转换 '{word_path}' 到 '{pdf_path}'...")

        try:
            doc = self.word_app.Documents.Open(word_path)
            # WdExportFormat 列举值 (wdExportFormatPDF = 17)
            doc.ExportAsFixedFormat(str(pdf_path), wdConstants.wdExportFormatPDF)
            doc.Close()
            print(f"成功转换 '{Path(word_path).name}'。")
        except Exception as e:
            print(f"错误: 转换文件 '{word_path}' 失败。错误信息: {e}")
            # 尝试关闭文档，即使转换失败
            if 'doc' in locals() and doc:
                 try:
                     doc.Close()
                 except Exception as close_e:
                     print(f"错误: 关闭文档 '{word_path}' 失败。错误信息: {close_e}")
            raise # 重新抛出异常以便外部捕获

class PdfToWordConverter:
    """
    将指定目录下的所有PDF文档转换为Word文档 (.docx)。
    """
    def __init__(self):
        self.word_app = None

    def _initialize_word(self):
        """初始化Word应用程序实例。"""
        try:
            self.word_app = win32com.client.Dispatch("Word.Application")
            self.word_app.Visible = False # 不显示Word窗口
            print("Word应用程序初始化成功。")
        except Exception as e:
            print(f"错误: 初始化Word应用程序失败。请确保已安装Microsoft Word。错误信息: {e}")
            self.word_app = None
            raise

    def _close_word(self):
        """关闭Word应用程序实例。"""
        if self.word_app:
            try:
                self.word_app.Quit()
                print("Word应用程序已关闭。")
            except Exception as e:
                print(f"错误: 关闭Word应用程序失败。错误信息: {e}")
            self.word_app = None

    def convert_directory(self, directory_path: str):
        """
        转换指定目录下的所有PDF文档为Word文档。

        Args:
            directory_path: 包含PDF文档的目录路径。
        """
        if not Path(directory_path).is_dir():
            print(f"错误: '{directory_path}' 不是一个有效的目录。")
            return

        print(f"开始转换目录: {directory_path}")

        try:
            self._initialize_word()
            if not self.word_app:
                return # 初始化失败则退出

            for file_path in Path(directory_path).iterdir():
                if file_path.suffix.lower() == '.pdf':
                    print(f"发现PDF文件: {file_path}")
                    try:
                        self._convert_file(str(file_path))
                    except Exception as e:
                        print(f"错误: 转换文件 '{file_path}' 失败。错误信息: {e}")
                else:
                    print(f"跳过非PDF文件: {file_path}")

        except Exception as e:
            print(f"处理目录 '{directory_path}' 时发生错误: {e}")
        finally:
            self._close_word()
            print("转换过程结束。")

    def _convert_file(self, pdf_path: str):
        """
        将单个PDF文档转换为Word文档 (.docx)。

        Args:
            pdf_path: PDF文档的完整路径。
        """
        if not self.word_app:
            print("错误: Word应用程序未初始化。无法转换文件。")
            return

        word_path = Path(pdf_path).with_suffix('.docx')
        print(f"正在转换 '{pdf_path}' 到 '{word_path}'...")

        try:
            # 打开PDF文件，Word会尝试将其转换为可编辑格式
            doc = self.word_app.Documents.Open(
                pdf_path,
                ConfirmConversions=False, # 不弹出转换确认对话框
                ReadOnly=True,
                AddToRecentFiles=False,
                PasswordDocument="",
                PasswordTemplate="",
                Revert=False,
                WritePasswordDocument="",
                WritePasswordTemplate="",
                Format=wdConstants.wdOpenFormatAuto # 自动检测格式，包括PDF
            )
            # 保存为 .docx 格式
            doc.SaveAs(str(word_path), FileFormat=wdConstants.wdFormatDocumentDefault) # wdFormatDocumentDefault = 16 (.docx)
            doc.Close()
            print(f"成功转换 '{Path(pdf_path).name}'。")
        except Exception as e:
            print(f"错误: 转换文件 '{pdf_path}' 失败。错误信息: {e}")
            # 尝试关闭文档，即使转换失败
            if 'doc' in locals() and doc:
                 try:
                     doc.Close()
                 except Exception as close_e:
                     print(f"错误: 关闭文档 '{pdf_path}' 失败。错误信息: {close_e}")
            raise # 重新抛出异常以便外部捕获


@Gooey(
    program_name="文档转换工具",
    program_description="将指定目录下的Word文档转换为PDF，或将PDF转换为Word文档",
    default_size=(600, 400), # 保持增加后的窗口高度
    language='chinese', # 设置Gooey界面语言为中文
    layout='basic' # 保持默认布局
)
def main():
    parser = GooeyParser(description="选择转换类型和包含文档的目录")

    # 添加一个参数用于选择转换方向
    parser.add_argument(
        'conversion_type',
        metavar='选择转换方向',
        help='选择是将Word转为PDF还是将PDF转为Word',
        choices=['Word转PDF', 'PDF转Word'],
        default='Word转PDF', # 默认选择Word转PDF
        widget='Dropdown' # 改用下拉菜单显示
    )

    parser.add_argument(
        'directory',
        metavar='选择目录',
        help='选择要转换的文档所在的目录',
        widget='DirChooser' # 使用目录选择器
    )

    args = parser.parse_args()

    if args.directory:
        if args.conversion_type == 'Word转PDF':
            print("选择了 Word 转 PDF 转换。")
            converter = WordToPdfConverter()
            converter.convert_directory(args.directory)
        elif args.conversion_type == 'PDF转Word':
            print("选择了 PDF 转 Word 转换。")
            converter = PdfToWordConverter()
            converter.convert_directory(args.directory)
        else:
            print("未知的转换类型。")
    else:
        print("未选择目录。")

if __name__ == "__main__":
    main()