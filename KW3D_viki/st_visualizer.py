import sys
import os
import threading
import time
import serial
import xlwt
import pandas as pd
import streamlit as st
from streamlit.runtime.scriptrunner import add_script_run_ctx
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from KW3D_viki import read_and_write_data, UWB_COM, UWB_BAUDRATE
# import motor_modbus_rtu_0308 as inst
# def turntable_rotate_3D(degreeAzi):
#     inst.write(degreeAzi)
#     inst.query("*OPC?")

# streamlit run st_visualizer.py


# --- 页面配置 ---
st.set_page_config(page_title="UWB 实时数据分析", layout="wide")
# st.title("UWB数据观测")

# 初始化 Session State
if "df_data" not in st.session_state:
    st.session_state.df_data = pd.DataFrame(columns=["Azimuth", "PDOA_Fst", "AoA_Azi", "Distance", "RSSI", "AoA_Ele", "Pdoa_Sec"])
if "is_running" not in st.session_state:
    st.session_state.is_running = False

# --- 侧边栏配置 ---
# st.sidebar.header("采集参数配置")
set_count = st.sidebar.number_input("每个位置采集数量", value=20, min_value=1)
start_angle = st.sidebar.slider("起始角度", -90, 90, -60)
end_angle = st.sidebar.slider("结束角度", -90, 90, 60)
step = st.sidebar.number_input("步长", value=6)

def data_callback(point):
    new_row = pd.DataFrame([point])
    # 限制 DataFrame 长度为最近 100 条数据，防止 X 轴无限扩张
    st.session_state.df_data = pd.concat([st.session_state.df_data, new_row], ignore_index=True).iloc[-100:]

def render_charts(data):
    if data.empty:
        st.info("等待数据接入...")
        return

    latest = data.iloc[-1]
    chart_height = 200
    
    # 第一行
    c1, c2 = st.columns(2)
    with c1:
        st.metric("距离", f"{latest['Distance']:.1f} cm")
        st.line_chart(data[["Distance"]], height=chart_height, width='stretch', color="#29b5e8")
    with c2:
        st.metric("PDOA1", f"{latest['PDOA_Fst']:.2f}")
        st.line_chart(data[["PDOA_Fst"]], height=chart_height, width='stretch', color="#1c83e1")
        
    # 第二行
    c3, c4 = st.columns(2)
    with c3:
        st.metric("AoA Azi", f"{latest['AoA_Azi']:.1f} °")
        st.line_chart(data[["AoA_Azi"]], height=chart_height, width='stretch', color="#77c405")
    with c4:
        st.metric("RSSI", f"{latest['RSSI']:.1f} dBm")
        st.line_chart(data[["RSSI"]], height=chart_height, width='stretch', color="#fca50a")

    # 第三行
    c5, c6 = st.columns(2)
    with c5:
        st.metric("AoA Ele", f"{latest['AoA_Ele']:.1f} °")
        st.line_chart(data[["AoA_Ele"]], height=chart_height, width='stretch', color="#9e31e2")
    with c6:
        st.metric("PDOA2", f"{latest['Pdoa_Sec']:.2f}")
        st.line_chart(data[["Pdoa_Sec"]], height=chart_height, width='stretch', color="#ff4b4b")

def run_collection():
    try:
        # 1. 初始化 Excel 表头
        head = [
            "Azimuth", "PDOA_Fst", "AoA_Azi", "Distance", "RSSI", "AoA_Ele", "Pdoa_Sec",
            "PointCount", "Azimuth", "PDOA_Fst", "AoA_Azi", "Distance", "RSSI", "AoA_Ele", "Pdoa_Sec"
        ]
        
        workbook = xlwt.Workbook("utf-8")
        sheet = workbook.add_sheet("data")
        for i in range(len(head)):
            sheet.write(0, i, head[i])

        print("转台归位...")
        print("已到初始位置")

        # 2. 打开 UWB 串口
        ser = serial.Serial(UWB_COM, UWB_BAUDRATE, timeout=2)
        print(f"✅ UWB串口打开成功：{UWB_COM} @ {UWB_BAUDRATE}")
        
        test_num = (end_angle - start_angle) // step
        current_start = start_angle
        
        for i in range(test_num + 1):
            if not st.session_state.is_running: break

            # turntable_rotate_3D(angle)
            angle = current_start
            print(f"\n🎯 已转到角度：{angle}°")

            time.sleep(1)
            ser.reset_input_buffer()
            if hasattr(ser, 'hex_buffer'):
                ser.hex_buffer = ""
            
            print("🔍 开始采集数据...")
            read_and_write_data(set_count, angle, i, ser, sheet, workbook, callback=data_callback)
            current_start += step
            
        # 最终保存+关闭串口
        workbook.save("G5-A1-RIGHT天线&魅族手机-姿态1-0°-2.5m_CH9.xls")
        ser.close()
        print("\n🏁 测试全部完成，文件已保存！")
    except Exception as e:
        print(f"采集出错: {e}")
    finally:
        st.session_state.is_running = False

# --- 控制按钮 ---
col1, col2 = st.sidebar.columns(2)
if col1.button("开始采集", disabled=st.session_state.is_running):
    st.session_state.df_data = pd.DataFrame(columns=["Azimuth", "PDOA_Fst", "AoA_Azi", "Distance", "RSSI", "AoA_Ele", "Pdoa_Sec"])
    st.session_state.is_running = True
    thread = threading.Thread(target=run_collection, daemon=True)
    # 将当前 Streamlit 的上下文添加到新线程中，这样新线程就可以使用 st.session_state 了
    add_script_run_ctx(thread)
    thread.start()
    st.rerun()

if col2.button("停止采集", disabled=not st.session_state.is_running):
    st.session_state.is_running = False
    st.rerun()

if st.sidebar.button("清空数据", disabled=st.session_state.is_running):
    st.session_state.df_data = pd.DataFrame(columns=["Azimuth", "PDOA_Fst", "AoA_Azi", "Distance", "RSSI", "AoA_Ele", "Pdoa_Sec"])
    st.rerun()

# --- 图表展示区 ---
chart_placeholder = st.empty()

if st.session_state.is_running:
    with chart_placeholder.container():
        render_charts(st.session_state.df_data)
    
    time.sleep(0.5) # 每 0.5 秒刷新一次 UI
    st.rerun()
else:
    # 非运行状态下的最后一次显示
    render_charts(st.session_state.df_data)