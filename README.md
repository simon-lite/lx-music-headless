## 项目说明
1. 在N1（或其他相似配置的盒子或路由器如京东云亚瑟，雅典娜等）上使用Lx-Music—headless自由播放网络音乐。
2. 项目调试使用的是10块钱以内的蓝牙+USB声卡+放大器的一体化模块（又不是不能用）。
3. 建议使用USB声卡。如对音质有要求可使用烧友所谓的高品质小尾巴连接到音频播放器。
4. 调试是在LXC环境的虚拟机里，直接映射宿主机声卡。
5. 如果你没有安装声卡驱动，大概是不会出声的。安装过程大概/可能会安装USB声卡驱动。如果没有，你就自己安装一下吧。
 ```bash
   sudo apt install alsa-utils usbutils
 ```
6. 已分别在京东云亚瑟（openwrt下用LXC虚拟的debian和ubuntu）和魔百盒（armbian或openwrt下LXC虚拟的debian和ubuntu）测试通过。
7. 京东云亚瑟可能需要自行编译固件才装的上声卡驱动。如需要固件请与我联系。

## 安装注意 
1. 推荐 Debian 12 或 Ubuntu LTS 24 
2. 要用 root 用户
3. 国内用户最好准备好梯子
4. 默认登陆IP:8888
5. Armbian可用，如当前系统无法安装或无法使用，建议用LXC虚拟机内建Debian 12或 ubuntu 24

## 安装指令
   ```bash
   sudo apt install wget #通常都有，没有就装上。
   sudo wget https://raw.githubusercontent.com/simon-lite/lxmusic-headless/refs/heads/main/onekey && chmod +x onekey && ./onekey
 ```
## 脚本功能选择
 ```bash
================ ALXWEB 管理工具 ================
 1 安装
 2 启动
 3 重启
 4 停止
 5 卸载
 0 退出脚本
=================================================
请输入选项 [0——5]：
```
 
