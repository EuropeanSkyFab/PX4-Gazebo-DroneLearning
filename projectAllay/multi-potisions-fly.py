import asyncio
from mavsdk import System
import random

async def run():
    drone = System()
    await drone.connect(system_address="udp://:14540")

    # 等待连接
    print("等待无人机连接...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("无人机已连接")
            break

    # 等待 GPS 锁定
    print("等待 GPS 锁定...")
    async for health in drone.telemetry.health():
        if health.is_global_position_ok and health.is_home_position_ok:
            print("GPS 已就绪")
            break

    # 解锁并起飞
    print("-- 解锁")
    await drone.action.arm()
    print("-- 起飞")
    await drone.action.takeoff()
    await asyncio.sleep(5)  # 等待起飞完成

    # 获取起飞点坐标（作为返航点）
    home = None
    async for position in drone.telemetry.position():
        home = position
        break
    print(f"起飞点：纬度 {home.latitude_deg:.6f}，经度 {home.longitude_deg:.6f}")


    for i in range(6):  # 循环三次
        # 定义一个随机目标点（基于起飞点的偏移量）
        point = (home.latitude_deg + random.uniform(-0.0006, 0.0006), home.longitude_deg + random.uniform(-0.0006, 0.0006))
        # 飞到 A 点
        print(f"-- 飞往点 {i+1}")
        await drone.action.goto_location(
            point[0], point[1],
            10.0,   # 目标高度：10 米
            0.0     # 偏航角：0 度（正北）
        )
        await asyncio.sleep(8)  # 等待飞行完成

    # 返回起飞点
    print("-- 返航")
    await drone.action.goto_location(
        home.latitude_deg, home.longitude_deg,
        10.0,
        0.0
    )
    await asyncio.sleep(8)

    # 降落
    print("-- 降落")
    await drone.action.land()

    # 等待着陆
    async for in_air in drone.telemetry.in_air():
        if not in_air:
            print("已着陆")
            break

if __name__ == "__main__":
    asyncio.run(run())