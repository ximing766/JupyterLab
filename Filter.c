typedef struct {
    float x[2];   // State: [0]=distance(m), [1]=velocity(m/s)
    float P[2][2]; // Error Covariance
    float Q[2][2]; // Process Noise
    float R;       // Measurement Noise (Adaptive)
    int64_t last_ts; // Last timestamp (ms)
} AEKF_State;

#define AEKF_R_BASE     4.0f   // 基础测量噪声 (dB^2)
#define AEKF_GATE_DB    7.0f  // 异常值门限 (dB)        XXX
#define MIN_DIST_M      0.1f   // 最小距离限制
#define MAX_DT_SEC      1.0f   // 最大时间间隔限制

void AEKF_init(AEKF_State *kf, float initial_dist, int64_t now) {
    if (initial_dist < MIN_DIST_M) initial_dist = MIN_DIST_M;
    
    kf->x[0] = initial_dist;
    kf->x[1] = 0.0f; // 初始速度假设为0
    
    // 初始化协方差矩阵 P
    kf->P[0][0] = 0.5f; kf->P[0][1] = 0.0f;
    kf->P[1][0] = 0.0f; kf->P[1][1] = 1.0f;
    
    kf->last_ts = now;
    kf->R = AEKF_R_BASE;
}

float AEKF_filter(AEKF_State *kf, float rssi, int64_t now) {
    // 1. 计算时间差 dt
    float dt = (float)(now - kf->last_ts) / 1000.0f;
    if (dt <= 0.001f) dt = 0.001f;
    if (dt > MAX_DT_SEC) dt = MAX_DT_SEC; // 防止长时间无数据导致发散
    kf->last_ts = now;

    // 2. 状态预测 (Prediction)
    // 模型: 恒定速度 (Constant Velocity)
    // x_k = x_{k-1} + v_{k-1} * dt
    float x_pred_dist = kf->x[0] + kf->x[1] * dt;
    float x_pred_vel  = kf->x[1];
    
    if (x_pred_dist < MIN_DIST_M) x_pred_dist = MIN_DIST_M;

    // 3. 协方差预测 (Covariance Prediction)
    // Q: 离散白噪声加速模型 (Discrete White Noise Acceleration)
    // BM Q值
    float q_scale = 5.0f; // 从 0.5f 增加到 5.0f 以提高响应速度
    float dt2 = dt * dt;
    float dt3 = dt2 * dt;
    float dt4 = dt3 * dt;
    
    float Q[2][2];
    Q[0][0] = q_scale * dt4 * 0.25f; Q[0][1] = q_scale * dt3 * 0.5f;
    Q[1][0] = Q[0][1];               Q[1][1] = q_scale * dt2;

    // P_pred = F * P * F^T + Q
    // F = [[1, dt], [0, 1]]
    float P00 = kf->P[0][0], P01 = kf->P[0][1], P10 = kf->P[1][0], P11 = kf->P[1][1];
    
    float FP00 = P00 + P10 * dt;
    float FP01 = P01 + P11 * dt;
    float FP10 = P10;
    float FP11 = P11;
    
    float P_pred[2][2];
    P_pred[0][0] = FP00 + FP01 * dt + Q[0][0];
    P_pred[0][1] = FP01 + Q[0][1];
    P_pred[1][0] = FP10 + FP11 * dt + Q[1][0];
    P_pred[1][1] = FP11 + Q[1][1];

    // 4. 测量预测 (Measurement Prediction)
    // h(x) = A - 10*n*log10(d)
    float rssi_pred = g_dist_params.rssi_d0 - 10.0f * g_dist_params.n_value * log10f(x_pred_dist);

    // 5. 异常值处理 (Outlier Handling)
    float clean_rssi = handle_outlier(rssi, rssi_pred);
    float innovation = clean_rssi - rssi_pred;

    // 自适应测量噪声 R
    // 如果残差依然很大(说明确实在快速移动或环境变了)，适当增大R以保持平滑，或者减小R以快速跟随?
    // 策略: 保持适中的 R，依靠 Kalman Gain 自动平衡
    kf->R = AEKF_R_BASE;

    // 6. 计算雅可比矩阵 H (Jacobian)
    // H = [dH/dd, dH/dv] = [-C/d, 0]
    // C = 10 * n / ln(10)
    float C = 10.0f * g_dist_params.n_value * 0.43429448f; // log10(e) = 0.4343
    // Derivative of -10*n*log10(d) = -10*n * (1/(d*ln10)) = -C/d
    float H_jac = -(10.0f * g_dist_params.n_value) / (x_pred_dist * 2.302585f);
    
    // 7. 更新步骤 (Update)
    // S = H P H^T + R
    // H = [H_jac, 0]
    float HP00 = H_jac * P_pred[0][0];
    float HP01 = H_jac * P_pred[0][1];
    
    float S = HP00 * H_jac + kf->R;
    
    // K = P H^T / S
    float K[2];
    K[0] = HP00 / S;
    K[1] = (P_pred[1][0] * H_jac) / S; // P_pred是对称的, P10=P01? 不一定完全对称计算误差
    
    // 更新状态
    kf->x[0] = x_pred_dist + K[0] * innovation;
    kf->x[1] = x_pred_vel + K[1] * innovation;
    
    if (kf->x[0] < MIN_DIST_M) kf->x[0] = MIN_DIST_M;

    // 更新协方差
    // P = (I - K H) P_pred
    // I - KH = [[1 - K0 H, 0], [-K1 H, 1]]
    float IKH00 = 1.0f - K[0] * H_jac;
    float IKH10 = -K[1] * H_jac;
    
    kf->P[0][0] = IKH00 * P_pred[0][0]; // + 0 * P10
    kf->P[0][1] = IKH00 * P_pred[0][1];
    kf->P[1][0] = IKH10 * P_pred[0][0] + P_pred[1][0];
    kf->P[1][1] = IKH10 * P_pred[0][1] + P_pred[1][1];

    // 返回基于最优估计距离计算出的平滑 RSSI
    return g_dist_params.rssi_d0 - 10.0f * g_dist_params.n_value * log10f(kf->x[0]);
}
