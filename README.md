## 项目说明
1. 在N1（或其他相似配置的盒子或路由器如京东云亚瑟，雅典娜等）上使用Lx-Music—headless自由播放网络音乐。
2. 项目调试使用的是蓝牙+USB声卡+放大器的一体化模块。
3. 建议使用USB声卡。如对音质有要求可使用烧友所谓的高品质小尾巴。
4. 调试是在LXC环境的虚拟机里，直接映射宿主机声卡。
5. 如果你没有安装声卡驱动，大概是不会出声的。安装过程大概/可能会安装USB声卡驱动。如果没有，你就自己安装一下吧。
   Debian / Ubuntu
 ```bash
   sudo apt update
   sudo apt install alsa-utils usbutils
 ```
   Openwrt
 ```bash
   opkg update
   opkg install kmod-sound-core kmod-usb-audio
   opkg install alsa-utils
 ```
6. 已分别在京东云亚瑟（openwrt下用LXC虚拟的debian和ubuntu）和魔百盒（armbian或openwrt下LXC虚拟的debian和ubuntu）测试通过。
7. 京东云亚瑟可能需要自行编译固件才装的上声卡驱动。如需要固件请与我联系。

## 安装注意 
1. 推荐 Debian 12 或 Ubuntu LTS 24 
2. 要用 root 用户
3. 墙内用户最好准备好梯子
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
## 无声问题解决
 安装后如果播放无声，可能是系统存在多个声卡，我们直接在系统全局层面上把 mpv 的默认输出锁死在你的 USB 声卡上。
 打开（或创建）系统全局的 mpv.conf 配置文件：
```bash
   mkdir -p /etc/mpv/
   nano /etc/mpv/mpv.conf
```
将以下三行配置完整复制并粘贴进去：
```text
   ao=alsa
   audio-device=alsa/plughw:CARD=Audio,DEV=0 #请使用aplay -l命令确认usb声卡位置。
   audio-channels=stereo
```
保存并退出（Ctrl+O 回车，Ctrl+X）。彻底杀掉之前残留的后台 mpv 进程（这步很重要，因为 alx 的 mpv 是守护进程，不杀掉不会读取新配置）：
```bash
  alx quit
  pkill -9 mpv
```
保存退出。之后重新放歌。
