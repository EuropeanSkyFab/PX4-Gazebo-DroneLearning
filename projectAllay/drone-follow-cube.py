import asyncio
from mavsdk import System
from mavsdk.offboard import OffboardError, VelocityNedYaw

from cube import get_box_pose

#----------------------------- 获取方块位置&坐标转换 ------------------------------
cube_x, cube_y, cube_z = get_box_pose()
cube_n = cube_y
cube_e = cube_x
cube_d = -cube_z

async def run():
    drone = System(port=50052)
    await drone.connect(system_address="udp://:14540")

    print("等待无人机连接...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("无人机已连接")
            break

    print("等待 GPS 锁定...")
    async for health in drone.telemetry.health():
        if health.is_global_position_ok and health.is_home_position_ok:
            print("GPS 已就绪")
            break

    print("-- 解锁")
    await drone.action.arm()

    print("-- 发送初始 setpoint（起飞前必须先发一次）")
    await drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, -2.0, 0.0))

    print("-- 启动 Offboard 模式")
    try:
        await drone.offboard.start()
    except OffboardError as error:
        print(f"启动 Offboard 失败：{error._result.result}")
        print("-- 上锁")
        await drone.action.disarm()
        return

# ----------------------------- 控制主体------------------------------


    print("-- 上升 2 m/s，持续 5 秒（约升高 10 米）")
    await drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, -2.0, 0.0))
    await asyncio.sleep(5)

    print("-- 悬停 3 秒（速度归零）")
    await drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, 0.0, 0.0))
    await asyncio.sleep(3)
    
    
    while True:
        
        async for pos in drone.telemetry.position_velocity_ned():
            drone_n = pos.position.north_m
            drone_e = pos.position.east_m
            drone_d = pos.position.down_m
            break
            
        delta_n = cube_n - drone_n
        delta_e = cube_e - drone_e
        
        v_n = max(-2.0, min(delta_n * 0.5, 2.0))
        v_e = max(-2.0, min(delta_e * 0.5, 2.0))
        

        distance = (delta_n**2 + delta_e**2)**0.5
        if distance < 0.5:
            print("已接近方块，悬停")
            await drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, 0.0, 0.0))
            break
    
    
        # 持续发 setpoint
        await drone.offboard.set_velocity_ned(VelocityNedYaw(v_n, v_e, 0.0, 0.0))
        await asyncio.sleep(0.1)
    
# -------------------------------------------------------------------


    print("-- 停止 Offboard")
    await drone.offboard.stop()

    print("-- 降落")
    await drone.action.land()

    async for in_air in drone.telemetry.in_air():
        if not in_air:
            print("已着陆")
            break


if __name__ == "__main__":
    asyncio.run(run())