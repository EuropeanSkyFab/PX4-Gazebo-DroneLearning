import asyncio
from mavsdk import System
from mavsdk.offboard import OffboardError, VelocityNedYaw


async def run():
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

    print("-- 上升 2 m/s，持续 5 秒（约升高 10 米）")
    await drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, -2.0, 0.0))
    await asyncio.sleep(5)

    print("-- 悬停 3 秒（速度归零）")
    await drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, 0.0, 0.0))
    await asyncio.sleep(3)

    print("-- 向北飞 3 m/s，持续 5 秒（约向北 15 米）")
    await drone.offboard.set_velocity_ned(VelocityNedYaw(3.0, 0.0, 0.0, 0.0))
    await asyncio.sleep(5)

    print("-- 悬停 3 秒")
    await drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, 0.0, 0.0))
    await asyncio.sleep(3)

    print("-- 向东南飞，北 2 m/s、东 2 m/s，持续 5 秒")
    await drone.offboard.set_velocity_ned(VelocityNedYaw(2.0, 2.0, 0.0, 0.0))
    await asyncio.sleep(5)

    print("-- 悬停 3 秒")
    await drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, 0.0, 0.0))
    await asyncio.sleep(3)

    print("-- 原地转向朝西（yaw = 270）")
    await drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, 0.0, 270.0))
    await asyncio.sleep(3)

    print("-- 以 1 m/s 下降，持续 5 秒")
    await drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, 1.0, 270.0))
    await asyncio.sleep(5)

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