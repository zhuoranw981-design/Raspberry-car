import paho.mqtt.client as mqtt
import json
import asyncio
from datetime import datetime

class MQTTService:
    def __init__(self, config, data_processor, decision_engine):
        self.config = config
        self.data_processor = data_processor
        self.decision_engine = decision_engine
        self.client = None
        self.connected = False
        self.on_message_callback = None
        self.loop = None

    def set_event_loop(self, loop):
        self.loop = loop

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            print(f"✅ MQTT连接成功")
            self.client.subscribe(self.config.MQTT_TOPIC)
            self.client.subscribe(self.config.CAMERA_TOPIC)
        else:
            print(f"❌ MQTT连接失败，返回码: {rc}")

    def on_disconnect(self, client, userdata, rc):
        self.connected = False
        print("🔌 MQTT连接断开")

    def on_message(self, client, userdata, msg):
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            
            print(f"\n📥 收到MQTT消息: {topic}")

            if topic == self.config.MQTT_TOPIC:
                data = json.loads(payload)
                self.process_sensor_data(data)
                
                if self.on_message_callback and self.loop:
                    asyncio.run_coroutine_threadsafe(self.on_message_callback(data), self.loop)

            elif topic == self.config.CAMERA_TOPIC:
                if self.on_message_callback and self.loop:
                    asyncio.run_coroutine_threadsafe(self.on_message_callback({'type': 'camera', 'data': payload}), self.loop)

        except Exception as e:
            print(f"❌ MQTT消息处理错误: {e}")

    def process_sensor_data(self, data):
        """处理传感器数据"""
        if 'radar' in data:
            print(f"📡 雷达点数: {len(data['radar'])}")
            self.data_processor.process_radar_data(data['radar'])
            
        if 'ultrasonic' in data:
            print(f"🔊 超声波数据: {data['ultrasonic']}")
            self.data_processor.process_ultrasonic_data(data['ultrasonic'])
            
        if 'pose' in data:
            self.data_processor.process_pose_data(data['pose'])

        # 自动模式下进行决策
        if self.decision_engine.auto_mode:
            latest = self.data_processor.get_latest_data()
            radar_data = latest['radar']['data'] if (latest['radar'] and latest['radar'].get('data')) else []
            ultrasonic_data = latest['ultrasonic']['data'] if (latest['ultrasonic'] and latest['ultrasonic'].get('data')) else {}
            
            decision = self.decision_engine.get_decision(radar_data, ultrasonic_data, {})
            self.publish_command(decision)

    def publish_command(self, command):
        """发布命令到MQTT"""
        if self.connected and self.client:
            try:
                payload = json.dumps(command)
                self.client.publish(self.config.MQTT_COMMAND_TOPIC, payload)
                print(f"📤 发布命令: {command['action']} ({command['speed']}) - {command['reason']}")
            except Exception as e:
                print(f"❌ MQTT发布失败: {e}")

    def start(self):
        """启动MQTT服务"""
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        
        try:
            self.client.connect(self.config.MQTT_BROKER, self.config.MQTT_PORT, 60)
            self.client.loop_start()
            print("🚀 MQTT服务已启动")
        except Exception as e:
            print(f"❌ MQTT连接异常: {e}")

    def stop(self):
        """停止MQTT服务"""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            print("🛑 MQTT服务已停止")