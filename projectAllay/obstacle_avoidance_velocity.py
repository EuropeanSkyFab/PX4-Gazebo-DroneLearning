import asyncio
from mavsdk import System
from mavsdk.offboard import OffboardError, VelocityNedYaw


async def get_current_ned(drone):
    async for pos in drone.telemetry.position_velocity_ned():
        return pos.position.north_m, pos.position.east_m, pos.position.down_m


async def fly_to(drone, target_n, target_e, target_d, yaw, timeout=40.0, arrive_dist=0.5, max_speed=2.0):
    print("飞往 N=%.2f E=%.2f D=%.2f" % (target_n, target_e, target_d))
    start = asyncio.get_event_loop().time()
    last_print = 0

    while True:
        cur_n, cur_e, cur_d = await get_current_ned(drone)

        dn = target_n - cur_n
        de = target_e - cur_e
        dd = target_d - cur_d
        dist = (dn * dn + de * de + dd * dd) ** 0.5

        if dist < arrive_dist:
            print("  到达目标点")
            return True

        if dist < 1.0:
            speed = max_speed * dist
        else:
            speed = max_speed

        vn = dn / dist * speed
        ve = de / dist * speed
        vd = dd / dist * speed

        await drone.offboard.set_velocity_ned(
            VelocityNedYaw(vn, ve, vd, yaw)
        )

        now = asyncio.get_event_loop().time()
        if now - last_print > 1.0:
            print("  当前位置 N=%.2f E=%.2f D=%.2f  距目标 %.2f 米" % (cur_n, cur_e, cur_d, dist))
            last_print = now

        if now - start > timeout:
            print("  超时，跳过")
            return False

        await asyncio.sleep(0.1)


async def run():
    drone = System(port=50052)
    await drone.connect(system_address="udpin://0.0.0.0:14540")

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
    await drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, -1.0, 0.0))

    print("-- 启动 Offboard")
    try:
        await drone.offboard.start()
    except OffboardError as e:
        print("启动失败:", e._result.result)
        await drone.action.disarm()
        return

    print("-- 起飞到 3 米高")
    await fly_to(drone, 0.0, 0.0, -3.0, 0.0, timeout=20.0)

    print("-- 航点 1：东绕点")
    await fly_to(drone, 0.0, 2.77, -3.0, 0.0, timeout=20.0)

    print("-- 航点 2：北穿点")
    await fly_to(drone, 14.16, 2.77, -3.0, 0.0, timeout=40.0)

    print("-- 航点 3：终点上方")
    await fly_to(drone, 23.17, 1.59, -3.0, 0.0, timeout=40.0)

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