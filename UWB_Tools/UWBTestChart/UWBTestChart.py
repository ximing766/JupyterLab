from pyecharts import options as opts
from pyecharts.charts import Pie
from pyecharts.commons.utils import JsCode
import os
import pandas as pd
from gooey import Gooey, GooeyParser

class UWBTestChart:
    def __init__(self, csv_path, height=0.8):
        self.df = pd.read_csv(csv_path)
        # Detect anchor column prefixes (supports 'M'/'S' and 'A1'/'A0')
        self.primary_prefix, self.secondary_prefix = self._detect_anchor_prefixes(self.df)
        self.df_08 = self.df[self.df['Height'] == 0.8].copy()
        self.df_15 = self.df[self.df['Height'] == 1.5].copy()
        self.nodes_data = self._init_nodes_data()
        df_selected = self.df_08 if height == 0.8 else self.df_15
        self.nodes_data = self._update_node_data(self.nodes_data, df_selected)

    def _get_color_by_value(self, value):
        if 0 <= value <= 10:
            return "#90BE6D"  # 绿色
        elif 10 < value <= 15:
            return "#F9C74F"  # 黄色
        return "#F94144"  # 红色

    def _init_nodes_data(self):
        return [
            # 第一行
            [2, "", "", 50, 50, "#FFFFFF", "#FFFFFF"],
            [5, "", "", 50, 50, "#FFFFFF", "#FFFFFF"],
            [8, "", "", 50, 50, "#FFFFFF", "#FFFFFF"],
            [11, "", "", 50, 50, "#FFFFFF", "#FFFFFF"],
            # 第二行
            [0, "", "", 50, 50, "#FFFFFF", "#FFFFFF"],
            [1, "", "", 50, 50, "#FFFFFF", "#FFFFFF"],
            [3, "", "", 50, 50, "#FFFFFF", "#FFFFFF"],
            [6, "", "", 50, 50, "#FFFFFF", "#FFFFFF"],
            [9, "", "", 50, 50, "#FFFFFF", "#FFFFFF"],
            [12, "", "", 50, 50, "#FFFFFF", "#FFFFFF"],
            [14, "", "", 50, 50, "#FFFFFF", "#FFFFFF"],
            # 第三行
            [4, "", "", 50, 50, "#FFFFFF", "#FFFFFF"],
            [7, "", "", 50, 50, "#FFFFFF", "#FFFFFF"],
            [10, "", "", 50, 50, "#FFFFFF", "#FFFFFF"],
            [13, "", "", 50, 50, "#FFFFFF", "#FFFFFF"],
        ]

    def _update_node_data(self, node_data, df):
        updated_nodes = []
        for node in node_data:
            point = node[0]
            if point in df['Point'].values:
                row = df[df['Point'] == point].iloc[0]
                # Use dynamic prefixes to support both old (M/S) and new (A1/A0) schemas
                m_res = abs(row[f"{self.primary_prefix}_Res"])
                s_res = abs(row[f"{self.secondary_prefix}_Res"])
                m_std = abs(row[f"{self.primary_prefix}_Std"])
                s_std = abs(row[f"{self.secondary_prefix}_Std"])
                m_rssi = row[f"{self.primary_prefix}_RSSI"]
                s_rssi = row[f"{self.secondary_prefix}_RSSI"]
                m_res_text = f"{m_res:.1f}±{m_std:.1f}cm"
                s_res_text = f"{s_res:.1f}±{s_std:.1f}cm"
                m_color = self._get_color_by_value(m_res + m_std)
                s_color = self._get_color_by_value(s_res + s_std)
                updated_nodes.append([
                    point, m_res_text, s_res_text,
                    m_rssi, s_rssi,
                    m_color, s_color
                ])
            else:
                updated_nodes.append(node)
        return updated_nodes

    def _detect_anchor_prefixes(self, df):
        """Detect anchor column prefixes in CSV (supports 'M'/'S' and 'A1'/'A0')."""
        cols = set(df.columns)
        primary = 'M' if 'M_Res' in cols else ('A1' if 'A1_Res' in cols else None)
        secondary = 'S' if 'S_Res' in cols else ('A0' if 'A0_Res' in cols else None)
        if not primary or not secondary:
            raise ValueError("CSV schema not recognized: expected M_/S_ or A1_/A0_ prefixed columns")
        return primary, secondary

    def _create_dual_circle(self, index, top_text, bottom_text, top_value, 
                          bottom_value, top_color, bottom_color):
        pie = Pie()
        # 外圈
        pie.add(
            series_name="",
            data_pair=[("上半部分", 50), ("下半部分", 50)],
            radius=["30%", "85%"],
            center=["50%", "50%"],
            start_angle=180,
            label_opts=opts.LabelOpts(
                position="inside",
                formatter=JsCode(
                    f"""function(params){{
                        return params.name === '上半部分' ? '\\n{top_text}' : '{bottom_text}\\n';
                    }}"""
                ),
                font_size=10,
                font_weight="bold",
                color="#FFFFFF",
                distance=25,
            ),
            tooltip_opts=opts.TooltipOpts(
                trigger="item",
                formatter=JsCode(
                    f"""function(params) {{
                        if (params.name === '上半部分') {{
                            return '主Anchor测量值：' + '{top_text}' + '<br/>RSSI：-{top_value}dBm';
                        }} else {{
                            return '从Anchor测量值：' + '{bottom_text}' + '<br/>RSSI：-{bottom_value}dBm';
                        }}
                    }}"""
                )
            )
        ).set_colors([top_color, bottom_color])
        
        # 中心圆
        pie.add(
            series_name="中心",
            data_pair=[("中心", 1)],
            radius=["0%", "25%"],
            center=["50%", "50%"],
            label_opts=opts.LabelOpts(
                position="center",
                formatter=f"{index}",
                font_size=18,
                font_weight="bold",
                color="#032c38"
            ),
            itemstyle_opts=opts.ItemStyleOpts(
                color="#87CEEB",
                border_radius=100
            ),
            tooltip_opts=opts.TooltipOpts(
                trigger="item",
                formatter=JsCode(
                    f"""function(params) {{
                        return '测试点：{index}';
                    }}"""
                )
            )
        )
        
        pie.set_global_opts(legend_opts=opts.LegendOpts(is_show=False))
        # pie.set_series_opts(tooltip_opts=opts.TooltipOpts(is_show=False))
        
        return pie

    def generate_html(self):
        js_charts = []
        chart_ids = []
        
        for data in self.nodes_data:
            index, top_text, bottom_text, top_value, bottom_value, top_color, bottom_color = data
            chart = self._create_dual_circle(
                index, top_text, bottom_text, top_value, bottom_value, top_color, bottom_color
            )
            chart_options = chart.dump_options()
            chart_id = chart.chart_id
            chart_ids.append((index, chart_id))
            
            js_charts.append(f"""
                var chart_{index} = echarts.init(document.getElementById('chart-{index}'));
                chart_{index}.setOption({chart_options});
                
                setTimeout(function() {{
                    chart_{index}.setOption({{
                        graphic: [
                            {{
                                type: 'text',
                                left: 'center',
                                top: '0%',
                                z: 100,
                                style: {{
                                    text: '-{top_value}dBm',
                                    fontSize: 10,
                                    fontWeight: 'bold',
                                    textShadow: '0 0 2px white'
                                }}
                            }},
                            {{
                                type: 'text',
                                left: 'center',
                                bottom: '0%',
                                z: 100,
                                style: {{
                                    text: '-{bottom_value}dBm',
                                    fontSize: 10,
                                    fontWeight: 'bold',
                                    textShadow: '0 0 2px white'
                                }}
                            }}
                        ]
                    }});
                }}, 100);
            """)
        
        with open(os.path.join(os.path.dirname(__file__), "uwb_layout_template.html"), "r", encoding="utf-8") as f:
            template = f.read()
            
        return template.replace("{{ CHARTS_SCRIPT }}", "\n".join(js_charts))

    def save_layout(self, output_name="uwb_layout.html"):
        output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), output_name)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(self.generate_html())
        print(f"布局已保存到: {output_path}")
        return output_path

@Gooey(
    program_name="UWB测试数据可视化工具",
    language='chinese',
    default_size=(600, 500),
    navigation='TABBED',
    show_success_modal=False,
)
def main():
    parser = GooeyParser(description="生成UWB测试数据可视化图表")
    
    parser.add_argument(
        "csv_file",
        metavar="CSV文件",
        help="选择包含UWB测试数据的CSV文件",
        widget="FileChooser",
        gooey_options={
            'wildcard': "CSV files (*.csv)|*.csv",
            'default_dir': './output'
        }
    )
    
    parser.add_argument(
        "--height",
        metavar="测试高度",
        choices=['0.8', '1.5'],
        default='0.8',
        help="选择测试高度(米)"
    )
    
    parser.add_argument(
        "--output_name",
        metavar="输出文件名",
        help="输出HTML文件名（可选）",
        default="uwb_layout.html"
    )

    args = parser.parse_args()
    
    # 创建图表
    height = float(args.height)
    chart = UWBTestChart(args.csv_file, height=height)
    
    # 生成输出文件名
    output_name = f"uwb_Test_{height}m.html" if args.output_name == "uwb_layout.html" else args.output_name
    
    # 保存布局
    output_path = chart.save_layout(output_name)
    
    # 自动打开生成的文件
    os.startfile(output_path)

if __name__ == "__main__":
    main()