import asyncio
from mavsdk import System

async def run():
    # 1. 创建无人机对象，连接到仿真端口 14540
    drone = System()
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

    print("-- 起飞")
    await drone.action.takeoff()

    # 悬停 5 秒
    await asyncio.sleep(5)

    print("-- 降落")
    await drone.action.land()

    # 等待降落完成
    async for in_air in drone.telemetry.in_air():
        if not in_air:
            print("已着陆")
            break

if __name__ == "__main__":
    asyncio.run(run())