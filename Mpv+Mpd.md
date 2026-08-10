系统使用其他音频播放软件，如MPD。可能会发生抢占声卡的情况，这时候有两个选择
 ```taxt
1, 继续让他们抢占，前台优先。自行把不用的进程kill掉;
2, 开启混音模式，支持同时播放同时出声；
 ```
如选择混音模式请按一下指导操作：
### 第一步：在系统层定义一个名为 default（默认）的设备，让它强制指向你的 USB 声卡并开启软件混音（dmix）
 ```bash
nano /etc/asound.conf
 ```
清空里面的内容（如果有），粘贴以下 ALSA 全局混音配置：
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
        rate 48000      # 锁定标准采样率，防止因格式不匹配报错
    }
}

ctl.!default {
    type hw
    card 0
}
 ```
保存并退出（Ctrl+O 回车，Ctrl+X）。
### 第二步：配置MPD无脑输出给默认设备，不需要写复杂的设备名。
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
### 第三步：同样地，MPV也不需要任何复杂的设备路径。打开你的 MPV 配置文件：
 ```bash
nano /etc/mpv/mpv.conf
 ```
把里面的内容精简为：
 ```text
ao=alsa
 ```
保存退出。
