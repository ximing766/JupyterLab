# RSSI(d) = RSSI(d₀) – 10n·log₁₀(d / d₀)
# ΔRSSI = RSSI_B - RSSI_A ≈ 10n·log₁₀(d_A/d_B)
# 其中n是路径损耗指数（通常2-4）



# 查找表法
class DirectionEstimator:
    def __init__(self, D_AB=0.1):
        self.D_AB = D_AB
        
        # 预计算RSSI差与角度的对应关系
        # 通过实验校准获得
        self.rssi_diff_to_angle = {
            -20: -80,  # 强烈偏右
            -15: -60,
            -10: -40,
            -5:  -20,
            0:    0,   # 正前方
            5:    20,
            10:   40,
            15:   60,
            20:   80   # 强烈偏左
        }
    
    def estimate(self, rssi_a, rssi_b, avg_rssi=None):
        """
        使用查找表估算方向
        
        avg_rssi: 平均RSSI，用于考虑距离因素
        """
        # 计算RSSI差
        rssi_diff = rssi_b - rssi_a
        
        # 简单插值
        diffs = sorted(self.rssi_diff_to_angle.keys())
        
        if rssi_diff <= diffs[0]:
            return self.rssi_diff_to_angle[diffs[0]]
        elif rssi_diff >= diffs[-1]:
            return self.rssi_diff_to_angle[diffs[-1]]
        else:
            # 找到最近的差值
            for i in range(len(diffs)-1):
                if diffs[i] <= rssi_diff <= diffs[i+1]:
                    # 线性插值
                    ratio = (rssi_diff - diffs[i]) / (diffs[i+1] - diffs[i])
                    angle1 = self.rssi_diff_to_angle[diffs[i]]
                    angle2 = self.rssi_diff_to_angle[diffs[i+1]]
                    return angle1 + ratio * (angle2 - angle1)
        
        return 0  # 默认值