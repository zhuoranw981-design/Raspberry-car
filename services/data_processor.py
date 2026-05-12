from datetime import datetime

class DataProcessor:
    def __init__(self):
        self.radar_data = {'timestamp': None, 'data': None}
        self.ultrasonic_data = {'timestamp': None, 'data': None}
        self.pose_data = {'timestamp': None, 'data': None}
    
    def process_radar_data(self, radar_data):
        self.radar_data = {
            'timestamp': datetime.now().isoformat(),
            'data': radar_data
        }
    
    def process_ultrasonic_data(self, ultrasonic_data):
        self.ultrasonic_data = {
            'timestamp': datetime.now().isoformat(),
            'data': ultrasonic_data
        }
    
    def process_pose_data(self, pose_data):
        self.pose_data = {
            'timestamp': datetime.now().isoformat(),
            'data': pose_data
        }
    
    def get_latest_data(self):
        return {
            'radar': self.radar_data,
            'ultrasonic': self.ultrasonic_data,
            'pose': self.pose_data
        }