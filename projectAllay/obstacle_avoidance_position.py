import asyncio
from mavsdk import System
from mavsdk.offboard import OffboardError, PositionNedYaw

#获取当前位置
async def get_current_ned(drone):
    async for pos in drone.telemetry.position_velocity_ned():
        return pos.position.north_m, pos.position.east_m, pos.position.down_m


#传位置参数的函数
async def send_position_loop(drone, north, east, down, yaw, duration, hz=10):
    interval = 1.0 / hz
    end_time = asyncio.get_event_loop().time() + duration
    while asyncio.get_event_loop().time() < end_time:
        await drone.offboard.set_position_ned(
            PositionNedYaw(north, east, down, yaw)
        )
        await asyncio.sleep(interval)



async def goto_and_wait(drone, north, east, down, yaw, timeout=30.0):
    print("飞往 N=", north, "E=", east, "D=", down)
    start = asyncio.get_event_loop().time()
    while True:
        await drone.offboard.set_position_ned(
            PositionNedYaw(north, east, down, yaw)
        )
        await asyncio.sleep(0.1)

        cur_n, cur_e, cur_d = await get_current_ned(drone)
        dist = ((cur_n - north) ** 2 + (cur_e - east) ** 2 + (cur_d - down) ** 2) ** 0.5
        print("  当前位置 N=%.2f E=%.2f D=%.2f  距目标 %.2f 米" % (cur_n, cur_e, cur_d, dist))

        if dist < 0.5:
            print("  到达目标点")
            return True

        if asyncio.get_event_loop().time() - start > timeout:
            print("  超时，跳过")
            return False


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

    print("-- 发送初始 setpoint")
    await drone.offboard.set_position_ned(PositionNedYaw(0.0, 0.0, -1.0, 0.0))

    print("-- 启动 Offboard")
    try:
        await drone.offboard.start()
    except OffboardError as e:
        print("启动失败:", e._result.result)
        await drone.action.disarm()
        return

    print("-- 起飞到 3 米高")
    await goto_and_wait(drone, 0.0, 0.0, -3.0, 0.0, timeout=20.0)

    print("-- 航点 1：东绕点")
    await goto_and_wait(drone, 0.0, 2.77, -3.0, 0.0, timeout=20.0)

    print("-- 航点 2：北穿点")
    await goto_and_wait(drone, 14.16, 2.77, -3.0, 0.0, timeout=40.0)

    print("-- 航点 3：终点上方")
    await goto_and_wait(drone, 23.17, 1.59, -3.0, 0.0, timeout=40.0)

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