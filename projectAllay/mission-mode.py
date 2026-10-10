import asyncio
from mavsdk import System
from mavsdk.mission import MissionItem, MissionPlan
import random
import math

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

    # 获取起飞点坐标
    home = None
    async for position in drone.telemetry.position():
        home = position
        break
    print(f"起飞点：纬度 {home.latitude_deg:.6f}，经度 {home.longitude_deg:.6f}")

    # 定义三个航点（基于起飞点的微小偏移）
    mission_items = []
    for i in range(6):
        angle = 2 * math.pi * i / 6
        lat = home.latitude_deg + 0.0006 * math.cos(angle)
        lon = home.longitude_deg + 0.0006 * math.sin(angle) / math.cos(math.radians(home.latitude_deg))
        mission_items.append(MissionItem(
            latitude_deg=lat,
            longitude_deg=lon,
            relative_altitude_m=10.0,
            speed_m_s=10.0,
            is_fly_through=True,
            gimbal_pitch_deg=float('nan'),
            gimbal_yaw_deg=float('nan'),
            camera_action=MissionItem.CameraAction.NONE,
            loiter_time_s=float('nan'),
            camera_photo_interval_s=float('nan'),
            acceptance_radius_m=float('nan'),
            yaw_deg=float('nan'),
            camera_photo_distance_m=float('nan'),
            vehicle_action=MissionItem.VehicleAction.NONE
        ))

    mission_plan = MissionPlan(mission_items)

    # 上传任务
    print("-- 上传任务")
    await drone.mission.upload_mission(mission_plan)

    # 解锁并起飞
    print("-- 解锁")
    await drone.action.arm()
    print("-- 起飞")
    await drone.action.takeoff()
    await asyncio.sleep(5)

    # 启动任务
    print("-- 启动任务")
    await drone.mission.start_mission()

    # 监听任务进度
    async for progress in drone.mission.mission_progress():
        print(f"任务进度：{progress.current}/{progress.total}")
        if progress.current == progress.total:
            print("任务完成")
            break

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

    async for in_air in drone.telemetry.in_air():
        if not in_air:
            print("已着陆")
            break

if __name__ == "__main__":
    asyncio.run(run())