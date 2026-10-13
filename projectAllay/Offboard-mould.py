import asyncio
from mavsdk import System
from mavsdk.offboard import OffboardError, VelocityNedYaw


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