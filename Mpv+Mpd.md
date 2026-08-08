## 第一步：创建全局 ALSA 混音配置我们在系统层定义一个名为 default（默认）的设备，让它强制指向你的 USB 声卡并开启软件混音（dmix）。用 nano 创建或覆盖全局配置文件：'
 ```bash
nano /etc/asound.conf
 ```
清空里面的内容（如果有的话），粘贴以下标准 ALSA 全局混音配置：
 ```text
pcm.!default {
    type plug
    slave.pcm "dmixer"
}

pcm.dmixer {
    type dmix
    ipc_key 1024
    ipc_perm 0666       # 极其关键：赋予 0666 权限，允许 root 和普通用户同时访问
    slave {
        pcm "hw:0,0"    # 你的 USB 声卡 (card 0, device 0)
        period_time 0
        period_size 1024
        buffer_size 4096
        rate 44100      # 锁定标准采样率，防止因格式不匹配报错
    }
}

ctl.!default {
    type hw
    card 0
}
 ```
保存并退出（Ctrl+O 回车，Ctrl+X）。
## 第二步：既然系统全局默认设备已经配好了，MPD 只需要无脑输出给 default 即可，不需要写复杂的设备名。
打开 MPD 配置文件：
 ```bash
nano /etc/mpd.conf
 ```
将 audio_output 修改为最干净的 ALSA 基础配置：
 ```text
audio_output {
        type            "alsa"
        name            "USB Audio"
        device          "default"       # 关键：直接走刚才配好的 default 混音器
        mixer_type      "software"
}
 ```
保存退出，并重启 MPD 服务：
 ```bash
systemctl restart mpd
 ```
## 第三步：MPV 也不需要任何复杂的设备路径了。打开你的 MPV 配置文件：
 ```bash
nano /etc/mpv/mpv.conf
 ```
把里面的内容精简为：
 ```text
ao=alsa
 ```
保存退出。
