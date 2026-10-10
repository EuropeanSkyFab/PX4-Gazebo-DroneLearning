# PX4-Gazebo-DroneLearning

用于记录我使用 PX4 + Gazebo 仿真学习无人机控制的代码与踩坑文档。

## 目前跑通了什么
- **基础控制**：起飞、悬停、降落
- **初步掌握Mission模式**：`mission-mode.py` 生成 6 个随机航点并执行
- **Offboard 入门**：`offboard-positionned.py` 和 `offboard-velocityned.py` 已跑通基础位置/速度控制

## 项目结构
- `projectAlley/`：MAVSDK-Python 控制脚本
- `tech-notes/`：环境配置和踩坑记录（含 WSL 网络、Offboard 超时、PX4 端口连接失败等）
- `images/`：仿真运行截图

## 下一步计划
- 深入学习Offboard模式
- 尝试将手头的ESP32-S3部署为地面站
- 学习部署端侧AI
