import asyncio
from fastapi import FastAPI, WebSocket, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from config import Config
from services.data_processor import DataProcessor
from services.decision_engine import DecisionEngine
from services.mqtt_service import MQTTService
from datetime import datetime
from websockets.exceptions import ConnectionClosed

app = FastAPI(title="小车避障云端AI服务")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

config = Config()
data_processor = DataProcessor()
decision_engine = DecisionEngine(config)
mqtt_service = MQTTService(config, data_processor, decision_engine)

active_connections = set()
latest_camera_frame = None
latest_manual_command = None
mqtt_initialized = False

# 密码保护配置
CONTROL_PASSWORD = "123456"  # 默认密码，可修改
authenticated_clients = set()  # 已认证的客户端IP列表

@app.on_event("startup")
async def startup_event():
    global mqtt_initialized
    mqtt_service.start()
    mqtt_service.set_event_loop(asyncio.get_running_loop())
    mqtt_service.on_message_callback = broadcast_message
    mqtt_initialized = True
    print("🚀 小车避障云端AI服务启动成功")
    print(f"🔐 控制密码已设置")

@app.on_event("shutdown")
async def shutdown_event():
    mqtt_service.stop()

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    with open("static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/health")
async def health_check():
    return {"status": "healthy", "mqtt_connected": mqtt_service.connected}

@app.get("/latest")
async def get_latest_data():
    return {
        "timestamp": datetime.now().isoformat(),
        **data_processor.get_latest_data(),
        "last_command": latest_manual_command or decision_engine.get_last_command(),
        "mode_info": decision_engine.get_mode_info(),
        "camera": latest_camera_frame
    }

@app.post("/api/login")
async def login(request: Request):
    """密码验证接口"""
    try:
        data = await request.json()
        password = data.get('password', '')
        client_ip = request.client.host
        
        if password == CONTROL_PASSWORD:
            authenticated_clients.add(client_ip)
            print(f"🔐 客户端 {client_ip} 已认证")
            return JSONResponse(content={
                "success": True,
                "message": "认证成功"
            })
        else:
            print(f"❌ 客户端 {client_ip} 密码错误")
            return JSONResponse(content={
                "success": False,
                "message": "密码错误"
            })
    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)

@app.post("/api/command")
async def send_command(request: Request):
    """接收手机端命令（需要密码认证）"""
    global latest_manual_command
    
    # 检查认证状态
    client_ip = request.client.host
    if client_ip not in authenticated_clients:
        return JSONResponse(content={
            "success": False,
            "message": "请先登录"
        }, status_code=401)
    
    try:
        cmd = await request.json()
        print(f"📥 收到API命令: {cmd}")
        
        if 'auto_mode' in cmd:
            auto_mode = cmd['auto_mode']
            speed = cmd.get('speed', 20)
            safe_distance = cmd.get('safe_distance', 50)
            warning_distance = cmd.get('warning_distance', 100)
            
            decision = decision_engine.set_auto_mode(auto_mode, speed, safe_distance, warning_distance)
            latest_manual_command = None
            
            if mqtt_service.connected:
                mqtt_service.publish_command(decision)
            
            return JSONResponse(content={
                "success": True,
                "message": f"已{'启用' if auto_mode else '关闭'}自动避障模式",
                "speed": decision['speed'],
                "auto_mode": auto_mode
            })
        
        action = cmd.get('action', 'stop')
        speed = cmd.get('speed', 20)
        
        latest_manual_command = {
            'action': action,
            'speed': speed,
            'timestamp': datetime.now().isoformat(),
            'reason': '手动控制'
        }
        
        if mqtt_service.connected:
            mqtt_service.publish_command(latest_manual_command)
            print(f"📤 发送手动命令: {action} {speed}")
        
        return JSONResponse(content={
            "success": True,
            "message": f"命令已发送: {action}",
            "action": action,
            "speed": speed
        })
    
    except Exception as e:
        print(f"❌ 命令处理失败: {e}")
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)

@app.get("/api/mode")
async def get_mode():
    return decision_engine.get_mode_info()

async def broadcast_message(message):
    global latest_camera_frame
    
    if message.get('type') == 'camera':
        latest_camera_frame = message.get('data')
        return
    
    disconnected = []
    for connection in active_connections:
        try:
            await connection.send_json(message)
        except (ConnectionClosed, Exception):
            disconnected.append(connection)
    
    for conn in disconnected:
        active_connections.discard(conn)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.add(websocket)
    print(f"🔗 新连接，当前连接数: {len(active_connections)}")

    try:
        while True:
            mode_info = decision_engine.get_mode_info()
            
            if mode_info['auto_mode']:
                current_cmd = decision_engine.get_last_command()
            else:
                current_cmd = latest_manual_command or {
                    'action': 'stop',
                    'speed': 0,
                    'timestamp': datetime.now().isoformat(),
                    'reason': '等待命令'
                }
            
            latest_data = {
                "type": "sensor_data",
                "timestamp": datetime.now().isoformat(),
                **data_processor.get_latest_data(),
                "last_command": current_cmd,
                "mode_info": mode_info,
                "camera": latest_camera_frame
            }
            await websocket.send_json(latest_data)
            await asyncio.sleep(0.1)
            
    except ConnectionClosed:
        print("🔌 WebSocket连接正常关闭")
    except Exception as e:
        print(f"❌ WebSocket异常: {e}")
    finally:
        active_connections.discard(websocket)
        print(f"🔌 连接断开，当前连接数: {len(active_connections)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.API_HOST, port=config.API_PORT)