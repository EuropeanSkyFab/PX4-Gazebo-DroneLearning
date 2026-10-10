import asyncio
from mavsdk import System
from mavsdk.offboard import OffboardError, VelocityNedYaw


async def send_setpoint_loop(drone, north, east, down, yaw, duration, hz=10):
    """
    以固定频率持续发送 setpoint，持续 duration 秒。
    hz=10 表示每秒发 10 次。
    """
    interval = 1.0 / hz
    end_time = asyncio.get_event_loop().time() + duration
    while asyncio.get_event_loop().time() < end_time:
        await drone.offboard.set_velocity_ned(
            VelocityNedYaw(north, east, down, yaw)
        )
        await asyncio.sleep(interval)


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

    print("-- 发送初始 setpoint")
    await drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, -2.0, 0.0))

    print("-- 启动 Offboard 模式")
    try:
        await drone.offboard.start()
    except OffboardError as error:
        print(f"启动 Offboard 失败：{error._result.result}")
        await drone.action.disarm()
        return

    print("-- 阶段 1：持续发送 setpoint，上升 2 m/s，5 秒")
    await send_setpoint_loop(drone, 0.0, 0.0, -2.0, 0.0, duration=5.0)

    print("-- 阶段 2：悬停，持续发送，3 秒")
    await send_setpoint_loop(drone, 0.0, 0.0, 0.0, 0.0, duration=3.0)

    print("-- 阶段 3：向北飞 2 m/s，持续发送，5 秒")
    await send_setpoint_loop(drone, 2.0, 0.0, 0.0, 0.0, duration=5.0)

    print("-- 阶段 4：悬停，持续发送，3 秒")
    await send_setpoint_loop(drone, 0.0, 0.0, 0.0, 0.0, duration=3.0)

    print("-- 阶段 5：故意停止发送 setpoint，观察 5 秒")
    print("   （这 5 秒内不发任何 setpoint，看飞控怎么反应）")
    await asyncio.sleep(5)

    print("-- 阶段 6：尝试继续发 setpoint")
    try:
        await send_setpoint_loop(drone, 0.0, 0.0, 0.0, 0.0, duration=2.0)
        print("   还能继续发，说明还在 Offboard 模式")
    except Exception as e:
        print(f"   发送失败：{e}")
        print("   说明飞控已经退出 Offboard 模式")

    print("-- 检查当前飞行模式")
    async for mode in drone.telemetry.flight_mode():
        print(f"   当前模式：{mode}")
        break

    print("-- 停止 Offboard")
    try:
        await drone.offboard.stop()
    except OffboardError as e:
        print(f"   停止失败（可能已经不在 Offboard）：{e._result.result}")

    print("-- 降落")
    await drone.action.land()

    async for in_air in drone.telemetry.in_air():
        if not in_air:
            print("已着陆")
            break


if __name__ == "__main__":
    asyncio.run(run())