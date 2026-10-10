import asyncio
import time
from mavsdk import System
from mavsdk.offboard import OffboardError, VelocityNedYaw, PositionNedYaw


async def get_flight_mode(drone):
    async for mode in drone.telemetry.flight_mode():
        return mode


async def send_setpoint_loop(drone, north, east, down, yaw, duration, hz=10):
    interval = 1.0 / hz
    end_time = asyncio.get_event_loop().time() + duration
    count = 0
    while asyncio.get_event_loop().time() < end_time:
        await drone.offboard.set_velocity_ned(
            VelocityNedYaw(north, east, down, yaw)
        )
        count += 1
        print(f"   [发送 #{count}] n={north} e={east} d={down} yaw={yaw}")
        await asyncio.sleep(interval)


async def measure_timeout(drone, stop_duration):
    print(f"\n=== 测试：停发 {stop_duration} 秒 ===")

    # 重新进入 Offboard
    await drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, 0.0, 0.0))
    try:
        await drone.offboard.start()
    except OffboardError as e:
        print(f"   启动 Offboard 失败：{e._result.result}")
        return None

    await asyncio.sleep(0.3)
    mode = await get_flight_mode(drone)
    print(f"   启动后模式：{mode}")

    # 持续发 1 秒，让飞控稳定在 Offboard
    await send_setpoint_loop(drone, 0.0, 0.0, 0.0, 0.0, duration=1.0)

    # 停发
    print(f"   >>> 停止发送，开始等待 {stop_duration} 秒")
    t_start = time.time()
    await asyncio.sleep(stop_duration)
    t_elapsed = time.time() - t_start
    print(f"   >>> 等待结束（实际 {t_elapsed:.2f} 秒）")

    # 检查模式
    mode = await get_flight_mode(drone)
    print(f"   停发 {t_elapsed:.2f} 秒后模式：{mode}")

    still_offboard = ("OFFBOARD" in str(mode))

    # 退出 Offboard，准备下次测试
    try:
        await drone.offboard.stop()
    except OffboardError:
        pass
    await asyncio.sleep(1.0)

    return still_offboard


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

    # 先起飞到 3 米高（位置模式）
    print("-- 起飞到 3 米高")
    await drone.offboard.set_position_ned(PositionNedYaw(0.0, 0.0, -3.0, 0.0))
    try:
        await drone.offboard.start()
    except OffboardError as e:
        print(f"启动失败：{e._result.result}")
        await drone.action.disarm()
        return

    end_time = asyncio.get_event_loop().time() + 5.0
    while asyncio.get_event_loop().time() < end_time:
        await drone.offboard.set_position_ned(PositionNedYaw(0.0, 0.0, -3.0, 0.0))
        await asyncio.sleep(0.1)

    await drone.offboard.stop()
    await asyncio.sleep(1.0)

    # 测试
    test_durations = [2.0, 5.0, 10.0]

    results = []
    for d in test_durations:
        still = await measure_timeout(drone, d)
        if still is None:
            print("   测试中断")
            break
        results.append((d, still))

    # 结果汇总
    print("\n\n========== 结果汇总 ==========")
    print(f"{'停发时长(s)':<15}{'是否还在 Offboard':<20}")
    for d, still in results:
        print(f"{d:<15}{'是' if still else '否':<20}")

    print("\n-- 降落")
    await drone.action.land()

    async for in_air in drone.telemetry.in_air():
        if not in_air:
            print("已着陆")
            break


if __name__ == "__main__":
    asyncio.run(run())