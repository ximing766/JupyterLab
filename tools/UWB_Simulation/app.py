import streamlit as st
import plotly.graph_objects as go
import numpy as np

# --------------------------
# 页面配置
# --------------------------
st.set_page_config(
    page_title="UWB 停车场门禁仿真",
    layout="wide",
)

# st.title("🚗 UWB 停车场门禁仿真")

# --------------------------
# 参数设置 (精简版)
# --------------------------
# 侧边栏只保留核心可调参数
# st.sidebar.header("UWB 布设参数")

# 核心可调参数
uwb_x = st.sidebar.slider("UWB 前后位置 (m)", -5.0, 5.0, 0.0, step=0.1, help="0为门平面，正值为门外，负值为门内")
uwb_y = st.sidebar.slider("UWB 左右位置 (m)", -3.0, 3.0, 0.0, step=0.1)
uwb_z = st.sidebar.slider("UWB 高度 (m)", 1.0, 4.0, 2.8, step=0.1)
trigger_radius = st.sidebar.slider("触发半径 (m)", 1.0, 15.0, 8.0, step=0.5)

# 固定参数 (隐藏)
gate_width = 5.0
gate_height = 3.5
car_speed_kmh = 15.0
car_y_offset = 1.0
phone_height = 1.2
trigger_delay = 200

# --------------------------
# 计算逻辑
# --------------------------
car_speed_ms = car_speed_kmh / 3.6

# 模拟车辆轨迹: 仅关注门前区域 (从 20m 到 0m)
# 既然用户说连接线不要超过门，那我们只模拟到门的位置即可
sim_x_start = 20.0
sim_x_end = 0.0  # 截止到门
sim_steps = 100
car_x = np.linspace(sim_x_start, sim_x_end, sim_steps)
car_y = np.full_like(car_x, car_y_offset)
car_z = np.full_like(car_x, phone_height)

# UWB 坐标
uwb_pos = np.array([uwb_x, uwb_y, uwb_z])
# 车辆坐标数组 (N, 3)
car_pos = np.stack([car_x, car_y, car_z], axis=1)

# 计算欧氏距离
distances = np.linalg.norm(car_pos - uwb_pos, axis=1)

# 判断是否触发
is_triggered = distances <= trigger_radius
trigger_indices = np.where(is_triggered)[0]

# 结果计算
if len(trigger_indices) > 0:
    first_trigger_idx = trigger_indices[0]
    first_trigger_x = car_x[first_trigger_idx]
    
    # 既然只模拟到门，且截止点就是0，那么触发时长应该是从首次触发到到达门的时间
    # 如果整个过程都在触发范围内，则时长 = (首次触发位置 - 0) / 速度
    dist_to_gate = first_trigger_x
    time_to_gate = dist_to_gate / car_speed_ms
    is_early_enough = time_to_gate > (trigger_delay / 1000.0)
    
    result_msg = "✅ 成功触发" if is_early_enough else "⚠️ 触发过晚"
else:
    first_trigger_x = None
    dist_to_gate = 0
    result_msg = "❌ 未触发"

# --------------------------
# 3D 绘图 (Plotly)
# --------------------------
fig = go.Figure()

# 1. 地面 (X: -5 to 20)
fig.add_trace(go.Mesh3d(
    x=[-5, -5, 20, 20],
    y=[-5, 5, 5, -5],
    z=[0, 0, 0, 0],
    color='lightgray',
    opacity=0.3,
    name='地面',
    hoverinfo='skip'
))

# 2. 大门门架 (固定)
w = gate_width / 2
h = gate_height
fig.add_trace(go.Scatter3d(
    x=[0, 0, 0, 0],
    y=[-w, -w, w, w],
    z=[0, h, h, 0],
    mode='lines',
    line=dict(color='black', width=6),
    name='大门',
    hoverinfo='skip'
))

# 3. UWB 模组 (实体小球)
# 使用 parametric surface 画一个小球
r_uwb = 0.2
# 增加网格密度，使其更圆
u = np.linspace(0, 2 * np.pi, 50)
v = np.linspace(0, np.pi, 50)
uwb_sphere_x = uwb_x + r_uwb * np.outer(np.cos(u), np.sin(v))
uwb_sphere_y = uwb_y + r_uwb * np.outer(np.sin(u), np.sin(v))
uwb_sphere_z = uwb_z + r_uwb * np.outer(np.ones(np.size(u)), np.cos(v))

fig.add_trace(go.Surface(
    x=uwb_sphere_x, y=uwb_sphere_y, z=uwb_sphere_z,
    opacity=1.0,
    colorscale=[[0, 'red'], [1, 'red']],
    showscale=False,
    name='UWB模组'
))

# 4. UWB 覆盖范围 (半透明大球)
# 增加网格密度
u = np.linspace(0, 2 * np.pi, 100)
v = np.linspace(0, np.pi, 50)
cov_x = uwb_x + trigger_radius * np.outer(np.cos(u), np.sin(v))
cov_y = uwb_y + trigger_radius * np.outer(np.sin(u), np.sin(v))
cov_z = uwb_z + trigger_radius * np.outer(np.ones(np.size(u)), np.cos(v))

fig.add_trace(go.Surface(
    x=cov_x, y=cov_y, z=cov_z,
    opacity=0.1,
    colorscale=[[0, 'blue'], [1, 'blue']],
    showscale=False,
    name='覆盖范围',
    hoverinfo='skip'
))

# 5. 车辆轨迹 (仅画到门)
# 未触发段 (灰色虚线)
fig.add_trace(go.Scatter3d(
    x=car_x, y=car_y, z=car_z,
    mode='lines',
    line=dict(color='gray', width=3, dash='dash'),
    name='行驶轨迹',
    hoverinfo='skip'
))

# 触发段 (绿色实线) - 叠加在轨迹上
if len(trigger_indices) > 0:
    fig.add_trace(go.Scatter3d(
        x=car_x[is_triggered], y=car_y[is_triggered], z=car_z[is_triggered],
        mode='lines',
        line=dict(color='green', width=5),
        name='有效触发段',
        hoverinfo='skip'
    ))

# 6. 首次触发点 & 连线
if first_trigger_x is not None:
    # 触发点
    fig.add_trace(go.Scatter3d(
        x=[first_trigger_x], y=[car_y_offset], z=[phone_height],
        mode='markers',
        marker=dict(size=5, color='orange'),
        name='首次触发点'
    ))
    
    # 连线: 触发点 -> UWB 模组
    fig.add_trace(go.Scatter3d(
        x=[first_trigger_x, uwb_x],
        y=[car_y_offset, uwb_y],
        z=[phone_height, uwb_z],
        mode='lines',
        line=dict(color='orange', width=5, dash='dot'),
        name='测距连线'
    ))

# 布局调整
fig.update_layout(
    scene=dict(
        aspectmode='data', # 强制保持数据比例一致 (x:y:z = 1:1:1)
        xaxis_title='X (前后)',
        yaxis_title='Y (左右)',
        zaxis_title='Z (高度)',
        # 移除强制的 range 设置，让 Plotly 根据 aspectmode='data' 自动计算
        # 这样才能保证球体是正球体，而不是被拉伸的椭球
    ),
    margin=dict(l=0, r=0, b=0, t=0),
    height=600,
    showlegend=True,
    legend=dict(x=0, y=1)
)

# --------------------------
# 界面布局 (左图右结果)
# --------------------------
col1, col2 = st.columns([3, 1])

with col1:
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # st.subheader("仿真结果")
    # st.info(f"状态: {result_msg}")
    
    if first_trigger_x is not None:
        st.metric("首次触发距离 (距门)", f"{first_trigger_x:.1f} m")
        st.metric("预留反应时间", f"{time_to_gate:.2f} s")
    else:
        st.write("未进入触发范围")
