# 小车避障云端AI系统 - 完整部署报告

## 项目概述

本项目是一个基于云端AI的智能小车避障系统，通过实时接收小车的传感器数据（雷达、超声波、姿态传感器），在云端进行智能决策，实现自动避障功能。系统采用MQTT协议进行数据传输，FastAPI提供Web服务，支持WebSocket实时数据推送。

**项目名称**: 小车避障云端AI服务  
**版本**: v1.0  
**部署日期**: 2026-05-12  
**部署环境**: Linux/Windows混合环境

---

## 一、系统架构

### 1.1 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      云端AI服务器                            │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  MQTT服务    │───▶│  数据处理    │───▶│  决策引擎    │  │
│  │ (数据接收)   │    │  (DataProcessor)│  │ (DecisionEngine)│ │
│  └──────────────┘    └──────────────┘    └──────┬───────┘  │
│                                                     │         │
│  ┌──────────────┐    ┌──────────────┐    ┌───────▼───────┐  │
│  │  FastAPI     │◀───│  WebSocket   │◀───│  控制指令生成  │  │
│  │ (Web服务)    │    │ (实时推送)   │    │               │  │
│  └──────────────┘    └──────────────┘    └───────────────┘  │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────┐    ┌──────────────┐                      │
│  │  Web前端     │    │  REST API    │                      │
│  │ (监控界面)   │    │ (控制接口)   │                      │
│  └──────────────┘    └──────────────┘                      │
└─────────────────────────────────────────────────────────────┘
                          ▲
                          │ MQTT
                          │
┌─────────────────────────┴─────────────────────────────────┐
│                    小车终端                                │
├─────────────────────────────────────────────────────────────┤
│  雷达模块  │ 超声波模块  │ 姿态传感器  │ 摄像头  │ 执行机构 │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 技术栈

| 组件 | 技术 | 版本 | 用途 |
|------|------|------|------|
| Web框架 | FastAPI | - | 提供REST API和WebSocket服务 |
| 异步运行时 | Uvicorn | - | ASGI服务器 |
| 消息队列 | MQTT (paho-mqtt) | 1.6.1 | 传感器数据接收和命令下发 |
| 前端 | HTML/CSS/JavaScript | - | Web监控界面 |
| 数据处理 | Python标准库 | 3.9+ | 传感器数据清洗和融合 |
| 决策算法 | 自定义算法 | - | 智能避障决策 |

### 1.3 核心模块说明

#### 1.3.1 主应用模块 (app.py)
- **功能**: 系统入口，提供Web服务和API接口
- **主要接口**:
  - `GET /`: Web前端界面
  - `GET /health`: 健康检查
  - `GET /latest`: 获取最新传感器数据
  - `POST /api/login`: 密码认证
  - `POST /api/command`: 接收控制命令
  - `GET /api/mode`: 获取当前模式
  - `WebSocket /ws`: 实时数据推送

#### 1.3.2 决策引擎模块 (services/decision_engine.py)
- **功能**: 智能避障决策核心
- **主要方法**:
  - `set_auto_mode()`: 设置自动避障模式
  - `set_manual_command()`: 设置手动控制命令
  - `get_decision()`: 基于传感器数据生成决策
- **决策逻辑**:
  - 前方270度雷达检测
  - 左中右三区域障碍物分析
  - 超声波辅助检测（更高优先级）
  - 紧急停车、减速、转向躲避三种策略

#### 1.3.3 MQTT服务模块 (services/mqtt_service.py)
- **功能**: MQTT消息收发
- **订阅主题**: 
  - 传感器数据主题
  - 摄像头数据主题
- **发布主题**: 控制命令主题

---

## 二、部署环境

### 2.1 硬件要求

| 资源 | 最低配置 | 推荐配置 |
|------|---------|---------|
| CPU | 双核 | 四核及以上 |
| 内存 | 2GB | 4GB及以上 |
| 存储 | 10GB | 20GB及以上 |
| 网络 | 100Mbps | 1Gbps |

### 2.2 软件要求

| 软件 | 版本要求 | 用途 |
|------|---------|------|
| 操作系统 | Linux (Ubuntu 20.04+) / Windows 10+ | 运行环境 |
| Python | 3.9+ | 开发语言 |
| MQTT Broker | Mosquitto 2.0+ | 消息队列 |
| Web浏览器 | Chrome 90+ / Edge 90+ | 前端访问 |

### 2.3 网络端口

| 端口 | 协议 | 用途 |
|------|------|------|
| 8000 | HTTP/WS | Web服务和WebSocket |
| 1883 | MQTT | MQTT消息传输 |
| 8086 | HTTP | InfluxDB（可选） |

---

## 三、部署步骤

### 3.1 环境准备

#### 3.1.1 Linux环境部署

```bash
# 1. 更新系统
sudo apt update && sudo apt upgrade -y

# 2. 安装Python和虚拟环境工具
sudo apt install -y python3 python3-pip python3-venv

# 3. 安装MQTT Broker
sudo apt install -y mosquitto mosquitto-clients

# 4. 启动MQTT服务
sudo systemctl enable mosquitto
sudo systemctl start mosquitto
```

#### 3.1.2 Windows环境部署

```powershell
# 1. 安装Python 3.9+
# 从 https://www.python.org/downloads/ 下载并安装

# 2. 安装MQTT Broker
# 从 https://mosquitto.org/download/ 下载并安装

# 3. 启动MQTT服务（默认端口1883）
# Mosquitto会自动作为Windows服务运行
```

### 3.2 项目部署

#### 3.2.1 创建项目目录

```bash
# Linux
mkdir -p ~/car-cloud-service
cd ~/car-cloud-service

# Windows
mkdir C:\Users\YourName\car-cloud-service
cd C:\Users\YourName\car-cloud-service
```

#### 3.2.2 创建虚拟环境

```bash
# Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

#### 3.2.3 安装依赖

```bash
pip install fastapi uvicorn paho-mqtt python-multipart
```

### 3.3 配置文件

#### 3.3.1 创建配置文件 config.py

```python
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
```

#### 3.3.2 创建数据处理服务 services/data_processor.py

```python
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
```

### 3.4 启动服务

#### 3.4.1 直接启动（开发环境）

```bash
# Linux
cd ~/car-cloud-service
source venv/bin/activate
python app.py

# Windows
cd C:\Users\YourName\car-cloud-service
venv\Scripts\activate
python app.py
```

#### 3.4.2 后台启动（生产环境）

```bash
# Linux - 使用nohup
nohup python app.py > app.log 2>&1 &

# 查看日志
tail -f app.log

# 停止服务
ps aux | grep app.py
kill <PID>
```

#### 3.4.3 使用systemd管理（Linux）

创建服务文件 `/etc/systemd/system/car-cloud.service`:

```ini
[Unit]
Description=Car Cloud AI Service
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/home/your_username/car-cloud-service
Environment="PATH=/home/your_username/car-cloud-service/venv/bin"
ExecStart=/home/your_username/car-cloud-service/venv/bin/python app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务:

```bash
sudo systemctl daemon-reload
sudo systemctl enable car-cloud
sudo systemctl start car-cloud
sudo systemctl status car-cloud
```

---

## 四、系统配置

### 4.1 安全配置

#### 4.1.1 修改控制密码

编辑 `app.py` 文件:

```python
CONTROL_PASSWORD = "your_secure_password"  # 修改为强密码
```

#### 4.1.2 MQTT认证（可选）

编辑 Mosquitto 配置文件 `/etc/mosquitto/mosquitto.conf`:

```conf
listener 1883
allow_anonymous false
password_file /etc/mosquitto/passwd
```

创建密码文件:

```bash
sudo mosquitto_passwd -c /etc/mosquitto/passwd car_user
sudo systemctl restart mosquitto
```

### 4.2 避障参数调优

在 `services/decision_engine.py` 中调整:

```python
self.safe_distance = 50      # 安全距离（厘米）
self.warning_distance = 100   # 警告距离（厘米）
self.auto_speed = 20         # 自动模式速度
```

### 4.3 网络配置

#### 4.3.1 防火墙配置

```bash
# Ubuntu/Debian
sudo ufw allow 8000/tcp
sudo ufw allow 1883/tcp
sudo ufw enable

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --permanent --add-port=1883/tcp
sudo firewall-cmd --reload
```

#### 4.3.2 外网访问

使用反向代理（Nginx）:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

---

## 五、数据协议

### 5.1 小车端发送数据格式

#### 5.1.1 传感器数据

```json
{
    "radar": [
        {"angle": -45, "distance": 120},
        {"angle": -30, "distance": 85},
        {"angle": 0, "distance": 60},
        {"angle": 30, "distance": 95},
        {"angle": 45, "distance": 110}
    ],
    "ultrasonic": {
        "front": 55,
        "left": 120,
        "right": 80,
        "back": 200,
        "min_distance": 55
    },
    "pose": {
        "acc_x": 0.15,
        "acc_y": 0.02,
        "acc_z": 9.78,
        "gyro_x": 0.01,
        "gyro_y": 0.005,
        "gyro_z": 0.02
    },
    "timestamp": "2026-05-12T10:30:00.000Z"
}
```

#### 5.1.2 摄像头数据

- **主题**: `car/camera`
- **格式**: Base64编码的JPEG图像

### 5.2 云端返回数据格式

#### 5.2.1 控制命令

```json
{
    "action": "forward",
    "speed": 20,
    "timestamp": "2026-05-12T10:30:00.500Z",
    "reason": "安全"
}
```

**动作类型**:
- `forward`: 前进
- `backward`: 后退
- `left`: 左转
- `right`: 右转
- `stop`: 停止

#### 5.2.2 WebSocket实时数据

```json
{
    "type": "sensor_data",
    "timestamp": "2026-05-12T10:30:00.500Z",
    "radar": {
        "timestamp": "2026-05-12T10:30:00.000Z",
        "data": [...]
    },
    "ultrasonic": {
        "timestamp": "2026-05-12T10:30:00.000Z",
        "data": {...}
    },
    "pose": {
        "timestamp": "2026-05-12T10:30:00.000Z",
        "data": {...}
    },
    "last_command": {
        "action": "forward",
        "speed": 20,
        "timestamp": "2026-05-12T10:30:00.500Z",
        "reason": "安全"
    },
    "mode_info": {
        "auto_mode": true,
        "auto_speed": 20,
        "safe_distance": 50,
        "warning_distance": 100
    },
    "camera": "base64_encoded_image_data"
}
```

---

## 六、功能测试

### 6.1 健康检查

```bash
curl http://localhost:8000/health
```

预期输出:
```json
{
    "status": "healthy",
    "mqtt_connected": true
}
```

### 6.2 密码认证测试

```bash
curl -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{"password": "123456"}'
```

### 6.3 手动控制测试

```bash
curl -X POST http://localhost:8000/api/command \
  -H "Content-Type: application/json" \
  -d '{"action": "forward", "speed": 30}'
```

### 6.4 自动避障模式测试

```bash
curl -X POST http://localhost:8000/api/command \
  -H "Content-Type: application/json" \
  -d '{
    "auto_mode": true,
    "speed": 20,
    "safe_distance": 50,
    "warning_distance": 100
  }'
```

### 6.5 MQTT消息测试

```bash
# 订阅控制命令
mosquitto_sub -h localhost -t car/command -v

# 发送传感器数据
mosquitto_pub -h localhost -t car/sensors -m '{
    "radar": [{"angle": 0, "distance": 60}],
    "ultrasonic": {"front": 55, "min_distance": 55},
    "pose": {"acc_x": 0.1, "acc_y": 0.02, "acc_z": 9.8}
}'
```

---

## 七、监控与维护

### 7.1 日志查看

```bash
# 查看应用日志
tail -f app.log

# 查看MQTT日志
sudo journalctl -u mosquitto -f

# 查看系统服务状态
sudo systemctl status car-cloud
```

### 7.2 性能监控

```bash
# 检查CPU和内存使用
top

# 检查网络连接
netstat -tunlp | grep 8000

# 检查MQTT连接
mosquitto_sub -h localhost -t '$SYS/broker/clients/active' -v
```

### 7.3 故障排查

#### 7.3.1 服务无法启动

```bash
# 检查端口占用
sudo lsof -i :8000
sudo lsof -i :1883

# 检查Python环境
python --version
pip list
```

#### 7.3.2 MQTT连接失败

```bash
# 检查MQTT服务状态
sudo systemctl status mosquitto

# 测试MQTT连接
mosquitto_sub -h localhost -t test -v
```

#### 7.3.3 WebSocket连接断开

- 检查网络连接
- 查看浏览器控制台错误
- 检查防火墙设置

---

## 八、备份与恢复

### 8.1 配置文件备份

```bash
# 备份配置
tar -czf car-cloud-backup-$(date +%Y%m%d).tar.gz \
    ~/car-cloud-service/config.py \
    ~/car-cloud-service/app.py \
    ~/car-cloud-service/services/
```

### 8.2 数据备份（如使用数据库）

```bash
# 备份InfluxDB数据
influx backup /path/to/backup

# 备份Redis数据
redis-cli SAVE
cp /var/lib/redis/dump.rdb /backup/
```

### 8.3 恢复流程

```bash
# 1. 停止服务
sudo systemctl stop car-cloud

# 2. 解压备份
tar -xzf car-cloud-backup-20260512.tar.gz

# 3. 恢复配置文件
cp -r car-cloud-service/* ~/car-cloud-service/

# 4. 重启服务
sudo systemctl start car-cloud
```

---

## 九、安全建议

### 9.1 密码安全

- 使用强密码（至少12位，包含大小写字母、数字、特殊字符）
- 定期更换密码
- 不要在代码中硬编码密码

### 9.2 网络安全

- 使用HTTPS（配置SSL证书）
- 限制访问IP（防火墙规则）
- 启用MQTT认证

### 9.3 系统安全

- 定期更新系统和依赖包
- 使用非root用户运行服务
- 定期检查日志，发现异常行为

---

## 十、常见问题

### Q1: 如何修改控制密码？

A: 编辑 `app.py` 文件中的 `CONTROL_PASSWORD` 变量。

### Q2: 如何调整避障灵敏度？

A: 修改 `services/decision_engine.py` 中的 `safe_distance` 和 `warning_distance` 参数。

### Q3: 如何查看实时传感器数据？

A: 访问 Web 界面 `http://localhost:8000`，或使用 WebSocket 客户端连接 `/ws`。

### Q4: 如何让服务开机自启？

A: 使用 systemd 服务（参考3.4.3节）。

### Q5: 如何从外网访问？

A: 配置端口转发或使用反向代理（参考4.3.2节）。

---

## 十一、附录

### 11.1 文件结构

```
car-cloud-service/
├── app.py                    # 主应用入口
├── config.py                 # 配置文件
├── requirements.txt          # Python依赖
├── services/                 # 服务模块
│   ├── data_processor.py     # 数据处理
│   ├── decision_engine.py    # 决策引擎
│   └── mqtt_service.py       # MQTT服务
├── static/                   # 静态文件
│   └── index.html           # Web前端
├── logs/                     # 日志目录
└── venv/                     # 虚拟环境
```

### 11.2 依赖包列表

```
fastapi==0.104.1
uvicorn==0.24.0
paho-mqtt==1.6.1
python-multipart==0.0.6
```

### 11.3 相关资源

- FastAPI文档: https://fastapi.tiangolo.com/
- MQTT协议: https://mqtt.org/
- Mosquitto文档: https://mosquitto.org/documentation/

---

## 十二、部署总结

### 12.1 部署检查清单

- [ ] 系统环境准备完成
- [ ] Python虚拟环境创建
- [ ] 依赖包安装完成
- [ ] 配置文件创建并配置
- [ ] MQTT服务运行正常
- [ ] 主应用启动成功
- [ ] Web界面可访问
- [ ] 密码认证功能正常
- [ ] MQTT消息收发正常
- [ ] 自动避障功能测试通过
- [ ] 日志记录正常
- [ ] 备份策略制定

### 12.2 部署后建议

1. **监控**: 设置监控告警，及时发现服务异常
2. **日志**: 定期检查日志，分析系统运行状况
3. **备份**: 定期备份配置和数据
4. **更新**: 关注依赖包安全更新，及时升级
5. **优化**: 根据实际使用情况，优化避障参数


**部署报告完成日期**: 2026-05-12  
**文档版本**: v1.0  
**部署人员**: [王卓然]
