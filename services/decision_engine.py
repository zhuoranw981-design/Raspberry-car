from datetime import datetime

class DecisionEngine:
    def __init__(self, config):
        self.config = config
        self.last_command = {
            'action': 'stop', 
            'speed': 0, 
            'timestamp': datetime.now().isoformat(),
            'reason': '初始状态'
        }
        self.auto_mode = False
        self.auto_speed = 20
        self.safe_distance = 50    # 安全距离（厘米）
        self.warning_distance = 100 # 警告距离（厘米）
        self.last_manual_time = None
        
    def set_auto_mode(self, enabled, speed=None, safe_distance=None, warning_distance=None):
        """设置自动避障模式"""
        self.auto_mode = enabled
        if speed is not None:
            self.auto_speed = speed
        if safe_distance is not None:
            self.safe_distance = safe_distance
        if warning_distance is not None:
            self.warning_distance = warning_distance
            
        if enabled:
            self.last_command = {
                'action': 'forward',
                'speed': self.auto_speed,
                'timestamp': datetime.now().isoformat(),
                'reason': '自动避障模式已启用'
            }
        else:
            self.last_command = {
                'action': 'stop',
                'speed': 0,
                'timestamp': datetime.now().isoformat(),
                'reason': '已切换为手动模式'
            }
        
        return self.last_command

    def set_manual_command(self, action, speed):
        """设置手动命令"""
        self.last_manual_time = datetime.now()
        self.last_command = {
            'action': action,
            'speed': speed,
            'timestamp': datetime.now().isoformat(),
            'reason': '手动控制'
        }
        return self.last_command

    def get_decision(self, radar_obstacles, ultrasonic_data, pose_data):
        """优化后的自动避障算法"""
        if not self.auto_mode:
            return self.last_command

        decision = {
            'action': 'forward',
            'speed': self.auto_speed,
            'reason': '安全',
            'timestamp': datetime.now().isoformat()
        }

        # 🔍 扩大检测角度范围：前方270度（-135度到135度）
        if radar_obstacles and len(radar_obstacles) > 0:
            # 检测前方270度范围
            front_obstacles = [
                obs for obs in radar_obstacles 
                if obs.get('angle', 0) >= -135 and obs.get('angle', 0) <= 135
            ]
            
            if front_obstacles:
                # 📐 按角度分区检测
                left_obstacles = [obs for obs in front_obstacles if obs['angle'] < -45]
                center_obstacles = [obs for obs in front_obstacles if -45 <= obs['angle'] <= 45]
                right_obstacles = [obs for obs in front_obstacles if obs['angle'] > 45]
                
                # 计算各区域最近距离
                left_dist = min([obs['distance'] for obs in left_obstacles]) if left_obstacles else float('inf')
                center_dist = min([obs['distance'] for obs in center_obstacles]) if center_obstacles else float('inf')
                right_dist = min([obs['distance'] for obs in right_obstacles]) if right_obstacles else float('inf')
                
                print(f"📡 雷达检测: 左={left_dist:.1f}cm 中={center_dist:.1f}cm 右={right_dist:.1f}cm")
                
                # 🚨 紧急停车条件：正前方近距离障碍物
                if center_dist < self.safe_distance:
                    decision['action'] = 'stop'
                    decision['speed'] = 0
                    decision['reason'] = f'🚨 正前方障碍物距离 {center_dist:.1f}cm，紧急停车'
                    
                # 🚧 减速条件：前方中等距离障碍物
                elif center_dist < self.warning_distance:
                    decision['speed'] = int(self.auto_speed * 0.3)  # 减速到30%
                    decision['reason'] = f'⚠️ 前方障碍物距离 {center_dist:.1f}cm，减速行驶'
                    
                # 🔄 转向躲避：侧面障碍物更近时
                elif left_dist < right_dist and left_dist < self.warning_distance:
                    decision['action'] = 'right'
                    decision['speed'] = int(self.auto_speed * 0.5)
                    decision['reason'] = f'↻ 左侧有障碍物({left_dist:.1f}cm)，向右躲避'
                    
                elif right_dist < left_dist and right_dist < self.warning_distance:
                    decision['action'] = 'left'
                    decision['speed'] = int(self.auto_speed * 0.5)
                    decision['reason'] = f'↺ 右侧有障碍物({right_dist:.1f}cm)，向左躲避'

        # 📢 超声波辅助检测（更高优先级）
        if ultrasonic_data and ultrasonic_data.get('min_distance', 0) > 0:
            us_min = ultrasonic_data['min_distance']
            print(f"🔊 超声波检测: {us_min}cm")
            
            if us_min < self.safe_distance * 0.8:  # 更灵敏的超声波检测
                decision['action'] = 'stop'
                decision['speed'] = 0
                decision['reason'] = f'🔊 超声波检测到障碍物距离 {us_min}cm，紧急停车'
            elif us_min < self.warning_distance:
                if decision['speed'] > self.auto_speed * 0.3:
                    decision['speed'] = int(self.auto_speed * 0.3)
                    decision['reason'] = f'🔊 超声波检测到障碍物，减速至 {decision["speed"]}'

        self.last_command = decision
        return decision

    def get_last_command(self):
        return self.last_command

    def get_mode_info(self):
        return {
            'auto_mode': self.auto_mode,
            'auto_speed': self.auto_speed,
            'safe_distance': self.safe_distance,
            'warning_distance': self.warning_distance
        }