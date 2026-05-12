import os

class Config:
    # API配置
    API_HOST = os.getenv('API_HOST', '0.0.0.0')
    API_PORT = int(os.getenv('API_PORT', 8000))
    
    # MQTT配置
    MQTT_BROKER = os.getenv('MQTT_BROKER', 'localhost')
    MQTT_PORT = int(os.getenv('MQTT_PORT', 1883))
    MQTT_TOPIC = 'car/sensors'
    MQTT_COMMAND_TOPIC = 'car/command'
    CAMERA_TOPIC = 'car/camera'
    
    # 安全配置
    CONTROL_PASSWORD = os.getenv('CONTROL_PASSWORD', '123456')