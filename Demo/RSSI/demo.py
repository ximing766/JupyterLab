import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from rssi_estimator import DirectionEstimator

class RSSIDemo:
    def __init__(self):
        self.anchors = {'A': np.array([-5.0, 0.0]), 'B': np.array([5.0, 0.0])}
        self.estimator = DirectionEstimator(D_AB=100.0)
        
        # Path: Circle with radius 80cm (1m) at y=150cm
        self.path_center, self.path_radius = np.array([0.0, 120.0]), 80.0
        
        # rssi_A: RSSI at reference distance d0 (100cm)
        self.rssi_A = -40 
        self.n = 2.0  # Path Loss Exponent
        
        self.history = {'ta': [], 'ea': [], 'td': [], 'ed': []}
        self.frame = 0

        # 2. Layout (Map Left, Charts Right)
        plt.style.use('seaborn-v0_8-whitegrid')
        self.fig = plt.figure(figsize=(10, 6))
        gs = self.fig.add_gridspec(2, 2, width_ratios=[3, 1])
        
        # 3. Map Setup
        self.ax_map = self.fig.add_subplot(gs[:, 0])
        self.ax_map.set_aspect('equal')
        # View window: X +/- 150cm, Y -20 to 300cm
        self.ax_map.set_xlim(-100, 100)
        self.ax_map.set_ylim(-20, 210)
        self.ax_map.set_title('Real-time Tracking (cm)', fontweight='bold')
        self.ax_map.set_xlabel('X (cm)')
        self.ax_map.set_ylabel('Y (cm)')
        
        # Draw Static Elements
        self.ax_map.scatter([-5.0, 5.0], [0, 0], c='#e74c3c', s=100, label='Anchors', zorder=5)
        self.ax_map.plot([-5.0, 5.0], [0, 0], c='#bdc3c7', ls='-')
        
        # Dynamic Elements
        self.tag, = self.ax_map.plot([], [], 'o', c='#3498db', ms=9, label='Tag', zorder=6)
        self.l_est, = self.ax_map.plot([], [], '--', c='#e67e22', lw=2, label='Est')
        self.l_true, = self.ax_map.plot([], [], ':', c='#2ecc71', lw=2, label='True')
        self.ax_map.legend(loc='upper right', fontsize='small', framealpha=0.9)

        # 4. Charts Setup
        self.ax_ang = self.fig.add_subplot(gs[0, 1])
        self.ax_dist = self.fig.add_subplot(gs[1, 1])
        
        self.ln_at, = self.ax_ang.plot([], [], c='#2ecc71', lw=1.5, label='True')
        self.ln_ae, = self.ax_ang.plot([], [], c='#e67e22', lw=1.5, label='Est')
        self.ax_ang.set_ylim(-90, 90); self.ax_ang.set_title('Angle (°)')
        self.ax_ang.legend(loc='upper right', fontsize='x-small')

        self.ln_dt, = self.ax_dist.plot([], [], c='#2ecc71', lw=1.5, label='True')
        self.ln_de, = self.ax_dist.plot([], [], c='#9b59b6', lw=1.5, label='Est')
        self.ax_dist.set_title('Distance (cm)')
        self.ax_dist.legend(loc='upper right', fontsize='x-small')

        # 5. Animation
        self.anim = FuncAnimation(self.fig, self.update, interval=30)

    def update(self, _):
        # A. Simulation Step
        ang = np.radians(self.frame % 360)
        pos = self.path_center + self.path_radius * np.array([np.cos(ang), np.sin(ang)])
        
        # B. RSSI Calculation (Model + Noise)
        # d is in cm. Model uses reference distance d0 = 100cm.
        da, db = np.linalg.norm(pos - self.anchors['A']), np.linalg.norm(pos - self.anchors['B'])
        
        # RSSI = A - 10*n*log10(d/d0)
        ra = self.rssi_A - 10 * self.n * np.log10(da/100.0) + np.random.normal(0, 0.5)
        rb = self.rssi_A - 10 * self.n * np.log10(db/100.0) + np.random.normal(0, 0.5)
        avg_rssi = (ra + rb) / 2
        
        # C. Estimation
        est_ang = self.estimator.estimate_angle(ra, rb, avg_rssi)
        # Distance Est: d = d0 * 10 ^ ((A - RSSI) / (10*n))
        est_dist = 100.0 * 10 ** ((self.rssi_A - avg_rssi) / (10 * self.n))
        
        # D. Ground Truth (0 deg is Y-axis)
        mp = (self.anchors['A'] + self.anchors['B']) / 2
        v = pos - mp
        true_ang = 90 - np.degrees(np.arctan2(v[1], v[0]))
        
        # E. Update Data
        avg_dist_true = (da + db) / 2
        for k, v in zip(['ta', 'ea', 'td', 'ed'], [true_ang, est_ang, avg_dist_true, est_dist]):
            self.history[k].append(v)
            if len(self.history[k]) > 100: self.history[k].pop(0)
            
        # F. Update Visuals
        self.tag.set_data([pos[0]], [pos[1]])
        er = np.radians(est_ang)
        # Draw est line length = est_dist
        self.l_est.set_data([mp[0], mp[0] + est_dist*np.sin(er)], [mp[1], mp[1] + est_dist*np.cos(er)])
        self.l_true.set_data([mp[0], pos[0]], [mp[1], pos[1]])
        
        x = range(len(self.history['ta']))
        self.ln_at.set_data(x, self.history['ta']); self.ln_ae.set_data(x, self.history['ea'])
        self.ln_dt.set_data(x, self.history['td']); self.ln_de.set_data(x, self.history['ed'])
        
        self.ax_ang.set_xlim(0, 100); self.ax_dist.set_xlim(0, 100)
        # Adjust Y limit for distance chart dynamically
        max_d = max(max(self.history['td']+[100]), max(self.history['ed']+[100]))
        self.ax_dist.set_ylim(0, max_d + 50)
        
        self.frame += 1

if __name__ == "__main__":
    RSSIDemo()
    plt.show()
