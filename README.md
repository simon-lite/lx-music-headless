在N1（或其他相似配置的盒子）上使用Lx-Music—headless。

## 安装注意 
1. 推荐 Debian 12 或 Ubuntu LTS 24 
2. 要用 root 用户
3. 国内用户最好准备好梯子
4. 默认登陆IP:8888
Armbian可用，如当前系统无法安装或无法使用，建议用LXC虚拟机内建Debian 12或 ubuntu 24。
## 安装指令
   ```bash
   sudo apt install wget #通常都有，没有就装上。
   sudo wget https://raw.githubusercontent.com/simon-lite/lxmusic-headless/refs/heads/main/onekey && chmod +x onekey && ./onekey
 ```
