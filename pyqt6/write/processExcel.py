import xlwings as xw
import os

class ExcelDataAnalyzer:
    def __init__(self):
        self.app = xw.App(visible=True, add_book=False)
        self.wb = None
        self.ws = None
        self.total_rows = 0

    def open_file(self, file_path):
        """打开CSV/Excel文件"""
        if self.wb:
            self.wb.close()
        self.wb = self.app.books.open(file_path)
        self.ws = self.wb.sheets.active
        self.total_rows = self.ws.range('A1').end('down').row

    def create_chart(self, column_letter, name):
        """创建美化的折线图"""
        data_range = f'{column_letter}2:{column_letter}{self.total_rows}'  # 跳过表头
        chart_col = chr(65 + self.ws.range('A1').end('right').column + 3)
        chart_count = len(self.ws.charts)
        
        chart = self.ws.charts.add()
        chart.set_source_data(self.ws.range(data_range))
        chart.chart_type = 'line'
        
        # 设置图表位置和大小
        chart.left = self.ws.range(f'{chart_col}1').left
        chart.top = chart_count * 300
        chart.width = 600
        chart.height = 280
        
        # 美化样式
        chart.api[1].ChartArea.Format.Fill.ForeColor.RGB = 0xFFFFFF  # 白色背景
        chart.api[1].PlotArea.Format.Fill.ForeColor.RGB = 0xF8F8F8  # 浅灰色绘图区
        
        # 设置标题
        chart.api[1].HasTitle = True
        title = chart.api[1].ChartTitle
        title.Text = name
        title.Font.Size = 14
        title.Font.Bold = True
        title.Font.Color = 0x404040  # 深灰色
        
        # 设置坐标轴
        for axis in [chart.api[1].Axes(1), chart.api[1].Axes(2)]:
            axis.HasMajorGridlines = True
            axis.MajorGridlines.Format.Line.ForeColor.RGB = 0xE0E0E0  # 浅灰网格
            axis.Format.Line.ForeColor.RGB = 0x404040  # 深灰轴线
            axis.TickLabels.Font.Size = 9
            
        # 设置数据系列
        series = chart.api[1].SeriesCollection(1)
        series.Format.Line.Weight = 2.5  # 线条粗细
        series.Format.Line.ForeColor.RGB = 0x4472C4  # 蓝色线条
        series.MarkerStyle = 8  # 圆形标记
        series.MarkerSize = 5
        series.Format.Fill.ForeColor.RGB = 0xFFFFFF  # 白色填充
        
        return chart

    def save_close(self, save_path=None):
        if save_path:
            self.wb.save(save_path)
        self.wb.close()
        self.app.quit()

if __name__ == "__main__":
    analyzer = ExcelDataAnalyzer()
    analyzer.open_file(r'e:\Work\UWB\Code\UwbCOMCode\tools\UwbCOM_Log_2025-03-31-17-55-12.csv')
    
    analyzer.create_chart('F', "主站距离变化趋势")
    analyzer.create_chart('G', "从站距离变化趋势")
    
    # analyzer.save_close('UWB_analysis.xlsx')