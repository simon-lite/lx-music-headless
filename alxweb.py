import subprocess
import re
import json
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# 指定歌曲下载绝对路径
DOWNLOAD_DIR = "/mnt/sda1/alxdl"

# 全局变量
CURRENT_SEARCH_RESULTS = []  # 保存当前搜索结果的歌曲对象列表
PLAY_QUEUE = []              # 保存当前播放队列的歌曲对象列表
CURRENT_PLAYING_ID = None    # 当前正在播放的歌曲 ID

def play_from_queue_node(song_id):
    """
    根据右侧队列中被触发的歌曲，向后台 alx 发送当前歌曲及后续所有歌曲的 ID，
    利用 alx 的原生多 ID 队列机制实现顺次自动播放。
    """
    global CURRENT_PLAYING_ID, PLAY_QUEUE
    if not PLAY_QUEUE:
        return
    
    start_idx = 0
    for idx, song in enumerate(PLAY_QUEUE):
        if song['id'] == song_id:
            start_idx = idx
            break
            
    ordered_ids = [song['id'] for song in PLAY_QUEUE[start_idx:]]
    
    if ordered_ids:
        subprocess.run(["alx", "stop"])
        cmd = ["alx", "play"] + ordered_ids
        print(f"[Player] 执行原生切歌队列命令: {cmd}")
        subprocess.Popen(cmd)
        CURRENT_PLAYING_ID = song_id

def clean_ansi(text):
    """去除终端输出中的 ANSI 颜色和样式控制代码"""
    return re.sub(r'(?:\x1B[@-_][0-?]*[ -/]*[@-~])', '', text)

def get_alx_state():
    """执行 alx now --json 并解析 JSON 格式的当前播放状态与进度"""
    state_data = {
        "status": "Stopped ■",
        "title": "暂无播放曲目",
        "progress_text": "00:00 / 00:00",
        "progress_percent": 0,
        "duration": 0,
        "position": 0
    }
    try:
        res = subprocess.run(["alx", "now", "--json"], capture_output=True, text=True, timeout=1)
        if res.returncode == 0 and res.stdout.strip():
            data = json.loads(res.stdout)
            
            raw_status = data.get("status", "stopped").lower()
            if raw_status == "playing":
                state_data["status"] = "Playing ▶"
            elif raw_status == "paused":
                state_data["status"] = "Paused ⏸"
            else:
                state_data["status"] = "Stopped ■"

            if raw_status in ["playing", "paused"] and "song" in data and data["song"]:
                song = data["song"]
                name = song.get("name", "未知曲目")
                singer = song.get("singer", "未知歌手")
                source = song.get("source", "")
                
                state_data["title"] = f"{name} - {singer} [{source}]" if source else f"{name} - {singer}"
                
                current_sec = int(data.get("position", 0))
                total_sec = int(data.get("duration", 0))
                
                state_data["duration"] = total_sec
                state_data["position"] = current_sec

                c_min, c_sec = divmod(current_sec, 60)
                t_min, t_sec = divmod(total_sec, 60)
                state_data["progress_text"] = f"{c_min:02d}:{c_sec:02d} / {t_min:02d}:{t_sec:02d}"
                
                if total_sec > 0:
                    state_data["progress_percent"] = min(100, int((current_sec / total_sec) * 100))
    except Exception as e:
        print(f"[State Error] 解析 JSON 状态失败: {e}")
    return state_data

BASE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>HIFI音乐遥控器</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: #121212; color: #fff; text-align: center; padding: 15px; margin: 0; }
        
        .container { max-width: 1000px; margin: 0 auto; padding-top: 190px; position: relative; z-index: 1; }
        
        /* 顶部锁定面板 */
        .top-sticky-panel { position: fixed; top: 0; left: 0; right: 0; background: #121212; border-bottom: 2px solid #282828; padding: 12px 15px; z-index: 9999; box-shadow: 0 4px 15px rgba(0,0,0,0.6); pointer-events: auto; }
        .top-sticky-wrapper { max-width: 1000px; margin: 0 auto; }
        
        .status-card { background: #181818; border: 1px solid #282828; border-radius: 12px; padding: 10px 15px; margin-bottom: 8px; text-align: left; display: flex; flex-direction: column; gap: 5px; }
        .status-meta { display: flex; justify-content: space-between; align-items: center; font-size: 13px; color: #b3b3b3; }
        .status-title { font-size: 15px; font-weight: bold; color: #1db954; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        
        /* 交互式滑动进度条 */
        .progress-bar-container { width: 100%; margin-top: 4px; display: flex; align-items: center; }
        .progress-slider {
            -webkit-appearance: none;
            appearance: none;
            width: 100%;
            height: 6px;
            border-radius: 3px;
            background: linear-gradient(to right, #1db954 0%, #333 0%);
            outline: none;
            cursor: pointer;
            transition: background 0.1s ease;
        }
        .progress-slider::-webkit-slider-thumb {
            -webkit-appearance: none;
            appearance: none;
            width: 14px;
            height: 14px;
            border-radius: 50%;
            background: #fff;
            cursor: pointer;
            box-shadow: 0 0 5px rgba(0,0,0,0.5);
            transition: transform 0.1s ease;
        }
        .progress-slider::-webkit-slider-thumb:hover {
            transform: scale(1.25);
            background: #1db954;
        }
        .progress-slider::-moz-range-thumb {
            width: 14px;
            height: 14px;
            border-radius: 50%;
            background: #fff;
            cursor: pointer;
            border: none;
        }

        /* 双栏布局 */
        .main-layout { display: flex; justify-content: space-between; margin-top: 0; gap: 20px; text-align: left; }
        .column { flex: 1; background: #181818; padding: 15px; border-radius: 12px; border: 1px solid #282828; height: calc(100vh - 220px); max-height: 650px; display: flex; flex-direction: column; box-sizing: border-box; overflow: hidden; }
        
        .column-header-box { display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #282828; padding-bottom: 10px; margin-bottom: 10px; height: 38px; flex-shrink: 0; box-sizing: border-box; position: sticky; top: 0; background: #181818; z-index: 10; }
        .column-header-box h3 { margin: 0; color: #b3b3b3; font-size: 18px; }
        
        .search-box-inline { display: flex; width: 65%; max-width: 300px; background: #282828; border-radius: 20px; overflow: hidden; }
        .search-box-inline input { flex: 1; padding: 8px 12px; border: none; background: transparent; color: white; font-size: 14px; outline: none; }
        .search-box-inline button { background: #1db954; color: white; border: none; padding: 0 14px; font-size: 13px; font-weight: bold; cursor: pointer; }
        .search-box-inline button:active { opacity: 0.8; }
        
        #search-list, #play-queue-list { flex: 1; overflow-y: auto; padding-right: 4px; }
        #search-list::-webkit-scrollbar, #play-queue-list::-webkit-scrollbar { width: 5px; }
        #search-list::-webkit-scrollbar-thumb, #play-queue-list::-webkit-scrollbar-thumb { background: #333; border-radius: 10px; }
        #search-list::-webkit-scrollbar-thumb:hover, #play-queue-list::-webkit-scrollbar-thumb:hover { background: #1db954; }
        
        .song-item { display: flex; align-items: center; background: #222; margin: 8px 0; border-radius: 8px; border: 1px solid #333; width: 100%; box-sizing: border-box; overflow: hidden; }
        .song-item.active { border-color: #1db954; background: #1e291e; }
        .song-btn { flex: 1; text-align: left; background: transparent; padding: 10px 0 10px 12px; border: none; cursor: pointer; color: #fff; display: flex; align-items: center; justify-content: space-between; overflow: hidden; }
        .song-info { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; margin-right: 5px; }
        .song-title { font-size: 14px; font-weight: bold; color: #fff; margin-bottom: 2px; display: block; }
        .song-artist { font-size: 11px; color: #b3b3b3; display: block; }
        
        .action-btn { background: #333; border: none; padding: 12px 14px; font-size: 14px; font-weight: bold; cursor: pointer; height: 100%; box-sizing: border-box; }
        .action-btn.add-btn { color: #1db954; font-size: 12px; border-left: 1px solid #333; width: 100px; text-align: center; }
        .action-btn.dl-btn { color: #00bfff; border-left: 1px solid #333; font-size: 15px; }
        .action-btn.del-btn { color: #ff5b5b; border-left: 1px solid #333; font-size: 15px; }
        .action-btn:active { background: #444; }
        
        .all-clear-btn { background: #ff5b5b; color: #fff; border: none; padding: 6px 12px; font-size: 12px; font-weight: bold; border-radius: 15px; cursor: pointer; transition: opacity 0.2s; }
        .all-clear-btn:active { opacity: 0.8; }
        
        .all-dl-btn { background: #00bfff; color: #fff; border: none; padding: 6px 12px; font-size: 12px; font-weight: bold; border-radius: 15px; cursor: pointer; }
        .all-dl-btn:active { opacity: 0.8; }

        .source-btn { background: #282828; color: #1db954; border: 1px solid #1db954; border-radius: 6px; padding: 3px 8px; font-size: 12px; font-weight: bold; cursor: pointer; transition: all 0.2s ease; white-space: nowrap; }
        .source-btn:hover { background: #1db954; color: #fff; }

        .control-panel { display: flex; justify-content: space-between; flex-wrap: wrap; margin-top: 5px; }
        .ctrl-btn { width: 23%; padding: 12px 5px; font-size: 14px; background: #333; border: none; color: white; border-radius: 10px; cursor: pointer; font-weight: bold; }
        .vol-btn { width: 31%; padding: 12px 5px; font-size: 14px; background: #282828; border: 1px solid #444; color: #1db954; border-radius: 10px; margin-top: 6px; cursor: pointer; font-weight: bold; }
        .stop-btn { width: 31%; padding: 12px 5px; font-size: 14px; background: #282828; border: 1px solid #ff5b5b; color: #ff5b5b; border-radius: 10px; margin-top: 6px; cursor: pointer; font-weight: bold; }
        .ctrl-btn:active, .vol-btn:active, .stop-btn:active { background: #444; transform: scale(0.98); }
        
        .toast { display: none; position: fixed; bottom: 40px; left: 50%; transform: translateX(-50%); background: rgba(29, 185, 84, 0.9); color: #fff; padding: 10px 20px; border-radius: 20px; font-size: 14px; z-index: 99999; }
        
        @media (max-width: 768px) {
            .container { padding-top: 210px; }
            .main-layout { flex-direction: column; }
            .column { height: 380px; max-height: 380px; margin-bottom: 15px; }
        }
    </style>
</head>
<body>
    <div class="top-sticky-panel">
        <div class="top-sticky-wrapper">
            <div class="status-card">
                <div class="status-title" id="player-song-title">正在载入状态...</div>
                <div class="status-meta">
                    <span id="player-status">状态: --</span>
                    <span id="player-time">00:00 / 00:00</span>
                </div>
                <div class="progress-bar-container">
                    <input type="range" class="progress-slider" id="player-progress-range" min="0" max="100" value="0" step="0.1"
                           oninput="onSeekInput(this.value)" onchange="onSeekChange(this.value)">
                </div>
            </div>
            <div class="control-panel">
                <button class="ctrl-btn" onclick="sendCmd('prev')">⏮ 上一首</button>
                <button class="ctrl-btn" onclick="sendCmd('pause')">⏸ 暂停</button>
                <button class="ctrl-btn" onclick="sendCmd('resume')">▶ 播放</button>
                <button class="ctrl-btn" onclick="sendCmd('next')">⏭ 下一首</button>
                <button class="vol-btn" onclick="sendCmd('volume -10')">🔉 音量 -</button>
                <button class="stop-btn" onclick="quitPlayer()">⏹ 停止</button>
                <button class="vol-btn" onclick="sendCmd('volume +10')">🔊 音量 +</button>
            </div>
        </div>
    </div>

    <div class="container">
        <div class="main-layout">
            <div class="column">
                <div class="column-header-box">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <button class="source-btn" onclick="promptAddSource()" title="添加自定义音源">源</button>
                        <h3>🔍 搜索结果</h3>
                    </div>
                    <form action="/search" method="get" class="search-box-inline">
                        <input type="text" name="q" placeholder="歌名/歌手..." value="{{ query }}" required>
                        <button type="submit">搜索</button>
                    </form>
                </div>
                <div id="search-list">
                    {% if songs %}
                        {% for song in songs %}
                            <div class="song-item">
                                <div class="song-btn">
                                    <div class="song-info">
                                        <span class="song-title">{{ song.idx }}. {{ song.title }}</span>
                                        <span class="song-artist">🎤 {{ song.artist }} [{{ song.platform }}]</span>
                                    </div>
                                </div>
                                <button class="action-btn add-btn" onclick="addToQueue('{{ song.id }}', '{{ song.title | replace("'", "\\'") }}', '{{ song.artist | replace("'", "\\'") }}')">加入播放表</button>
                            </div>
                        {% endfor %}
                    {% elif has_searched %}
                        <p style="color: #aaa; text-align: center; margin: 20px 0;">❌ 未找到相关歌曲。</p>
                    {% endif %}
                </div>
            </div>
            
            <div class="column">
                <div class="column-header-box">
                    <h3>📅 播放队列</h3>
                    <div style="display: flex; gap: 8px;">
                        <button class="all-clear-btn" onclick="clearQueue()">全部清除</button>
                        <button class="all-dl-btn" onclick="downloadAllQueue()">全部下载</button>
                    </div>
                </div>
                <div id="play-queue-list"></div>
            </div>
        </div>
    </div>
    <div id="toast" class="toast"></div>

    <script>
        let isRefreshPaused = false; 
        let isSeeking = false;        // 标记用户是否正处于拖拽 seek 状态
        let currentDuration = 0;      // 记录当前歌曲总秒数

        document.addEventListener("DOMContentLoaded", function() {
            updateQueueView();
            setInterval(updateQueueView, 2000);
        });

        // 拖拽过程中的实时预览
        function onSeekInput(percent) {
            isSeeking = true;
            const rangeInput = document.getElementById("player-progress-range");
            rangeInput.style.background = `linear-gradient(to right, #1db954 ${percent}%, #333 ${percent}%)`;
            
            if (currentDuration > 0) {
                const seekSec = Math.floor((percent / 100) * currentDuration);
                const curMin = Math.floor(seekSec / 60);
                const curSec = seekSec % 60;
                const totMin = Math.floor(currentDuration / 60);
                const totSec = currentDuration % 60;
                
                const curStr = curMin + ":" + (curSec < 10 ? "0" : "") + curSec;
                const totStr = totMin + ":" + (totSec < 10 ? "0" : "") + totSec;
                
                document.getElementById("player-time").innerText = `${curStr} / ${totStr}`;
            }
        }

        // 拖拽松开后正式提交命令
        function onSeekChange(percent) {
            if (currentDuration <= 0) {
                isSeeking = false;
                return;
            }
            const seekSec = Math.floor((percent / 100) * currentDuration);
            const curMin = Math.floor(seekSec / 60);
            const curSec = seekSec % 60;
            const timeStr = curMin + ":" + (curSec < 10 ? "0" : "") + curSec;
            
            showToast("⏩ 跳转至: " + timeStr);
            sendCmd('seek ' + timeStr);
            
            // 延时 1.5 秒解锁轮询，避免跳转瞬间轮询覆盖进度条
            setTimeout(function() {
                isSeeking = false;
            }, 1500);
        }

        function quitPlayer() {
            isRefreshPaused = true;
            
            document.getElementById("player-song-title").innerText = "暂无播放曲目";
            document.getElementById("player-status").innerText = "状态: Stopped ■";
            document.getElementById("player-time").innerText = "00:00 / 00:00";
            
            const rangeInput = document.getElementById("player-progress-range");
            rangeInput.value = 0;
            rangeInput.style.background = `linear-gradient(to right, #1db954 0%, #333 0%)`;
            currentDuration = 0;
            
            showToast("⏹ 播放关机。加入歌曲或点击播放列表内歌曲会自动恢复");
            sendCmd('quit');

            setTimeout(function() {
                isRefreshPaused = false;
            }, 3000);
        }

        function promptAddSource() {
            var url = prompt("请输入音源文件地址 (URL):");
            if (url && url.trim() !== "") {
                showToast("⏳ 正在导入自定义音源...");
                fetch('/add_source?url=' + encodeURIComponent(url.trim()))
                    .then(res => res.json())
                    .then(data => {
                        showToast(data.msg);
                    })
                    .catch(err => {
                        showToast("❌ 请求异常: " + err);
                    });
            }
        }

        function addToQueue(id, title, artist) {
            fetch(`/add_to_queue?id=${id}&title=${encodeURIComponent(title)}&artist=${encodeURIComponent(artist)}`)
                .then(res => res.json())
                .then(data => {
                    showToast(data.msg);
                    handleUiRefresh(data);
                });
        }

        function playQueueSong(id) {
            fetch(`/play_queue_id?id=${id}`)
                .then(res => res.json())
                .then(data => {
                    showToast("正在播放: " + data.title);
                    handleUiRefresh(data);
                });
        }

        function updateQueueView() {
            if (isRefreshPaused) return;
            fetch('/get_queue')
                .then(res => res.json())
                .then(data => {
                    if (!isRefreshPaused) handleUiRefresh(data);
                });
        }

        function handleUiRefresh(data) {
            renderQueue(data.queue, data.current_id);
            if (data.state) {
                currentDuration = data.state.duration || 0;
                document.getElementById("player-song-title").innerText = data.state.title;
                document.getElementById("player-status").innerText = "状态: " + data.state.status;
                
                if (!isSeeking) {
                    document.getElementById("player-time").innerText = data.state.progress_text;
                    const rangeInput = document.getElementById("player-progress-range");
                    const percent = data.state.progress_percent || 0;
                    rangeInput.value = percent;
                    rangeInput.style.background = `linear-gradient(to right, #1db954 ${percent}%, #333 ${percent}%)`;
                }
            }
        }

        function renderQueue(queue, currentId) {
            const container = document.getElementById("play-queue-list");
            if (!queue || queue.length === 0) {
                container.innerHTML = '<p style="color: #aaa; text-align: center; margin: 20px 0;">队列为空，请从左侧添加歌曲。</p>';
                return;
            }
            
            let html = "";
            queue.forEach((song, index) => {
                const isActive = song.id === currentId ? "active" : "";
                const icon = song.id === currentId ? "▶ " : "";
                html += `
                    <div class="song-item ${isActive}">
                        <button class="song-btn" onclick="playQueueSong('${song.id}')">
                            <div class="song-info">
                                <span class="song-title">${index + 1}. ${icon}${song.title}</span>
                                <span class="song-artist">🎤 ${song.artist}</span>
                            </div>
                        </button>
                        <button class="action-btn dl-btn" onclick="downloadSong('${song.id}', '${song.title.replace(/'/g, "\\'")}')">⬇</button>
                        <button class="action-btn del-btn" onclick="removeFromQueue('${song.id}')">×</button>
                    </div>
                `;
            });
            container.innerHTML = html;
        }

        function removeFromQueue(id) {
            fetch(`/remove_from_queue?id=${id}`)
                .then(res => res.json())
                .then(data => { handleUiRefresh(data); });
        }

        function clearQueue() {
            if (confirm("确定要清空播放队列吗？")) {
                fetch('/clear_queue')
                    .then(res => res.json())
                    .then(data => {
                        showToast("🗑️ 播放队列已清空");
                        handleUiRefresh(data);
                    });
            }
        }

        function downloadSong(id, title) {
            showToast("正在后台下载: " + title);
            fetch('/download_id?id=' + id)
                .then(res => res.text())
                .then(data => {
                    if(data === "OK") { showToast("📥 已触发后台极速下载..."); } 
                    else { showToast("❌ 下载请求失败"); }
                });
        }

        function downloadAllQueue() {
            showToast("🚀 已触发队列全部歌曲后台下载...");
            fetch('/download_all')
                .then(res => res.text())
                .then(data => {
                    if(data === "OK") { showToast("📥 队列全部歌曲已交付后台下载！"); }
                    else { showToast("❌ 下载请求未成功"); }
                });
        }

        function sendCmd(cmdStr) {
            fetch('/cmd?c=' + encodeURIComponent(cmdStr))
                .then(res => res.text())
                .then(() => { setTimeout(updateQueueView, 300); });
        }

        function showToast(msg) {
            var t = document.getElementById("toast");
            t.innerText = msg;
            t.style.display = "block";
            setTimeout(function(){ t.style.display = "none"; }, 3000);
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(BASE_HTML, query="", songs=[], has_searched=False)

@app.route('/add_source')
def add_source():
    url = request.args.get('url', '').strip()
    if not url:
        return jsonify({"status": "error", "msg": "❌ 音源地址不能为空"})
    
    try:
        res = subprocess.run(["alx", "source", "add", url], capture_output=True, text=True, timeout=15)
        output = clean_ansi(res.stdout + res.stderr)
        
        if "successfully" in output.lower() or "✓" in output:
            return jsonify({"status": "ok", "msg": "✓ 自定义音源导入成功！"})
        else:
            err_line = output.strip().split('\n')[-1] if output.strip() else "导入失败"
            return jsonify({"status": "error", "msg": f"❌ {err_line}"})
    except Exception as e:
        return jsonify({"status": "error", "msg": f"❌ 执行出错: {e}"})

@app.route('/search')
def search():
    global CURRENT_SEARCH_RESULTS
    query = request.args.get('q', '')
    songs = []
    CURRENT_SEARCH_RESULTS = []

    if query:
        result = subprocess.run(["alx", "search", query], capture_output=True, text=True)
        lines = clean_ansi(result.stdout).split('\n')
        for line in lines:
            if any(k in line for k in ["╭", "├", "╰", "Index"]) or not line.strip():
                continue
            if line.startswith("│") and line.endswith("│"):
                parts = [p.strip() for p in line.split("│")]
                if len(parts) >= 8 and parts[1].isdigit():
                    song_data = {
                        "idx": parts[1],
                        "id": parts[2],
                        "title": parts[3],
                        "artist": parts[4],
                        "album": parts[5],
                        "platform": parts[7]
                    }
                    songs.append(song_data)
                    CURRENT_SEARCH_RESULTS.append(song_data)
    return render_template_string(BASE_HTML, query=query, songs=songs, has_searched=True)

@app.route('/get_queue')
def get_queue():
    return jsonify({
        "queue": PLAY_QUEUE, 
        "current_id": CURRENT_PLAYING_ID, 
        "state": get_alx_state()
    })

@app.route('/add_to_queue')
def add_to_queue():
    global PLAY_QUEUE, CURRENT_PLAYING_ID
    song_id = request.args.get('id', '')
    title = request.args.get('title', '')
    artist = request.args.get('artist', '')
    
    if not song_id:
        return jsonify({"queue": PLAY_QUEUE, "current_id": CURRENT_PLAYING_ID, "msg": "无效ID"})

    exists = any(song['id'] == song_id for song in PLAY_QUEUE)
    if not exists:
        PLAY_QUEUE.append({"id": song_id, "title": title, "artist": artist})

    if len(PLAY_QUEUE) == 1 or CURRENT_PLAYING_ID is None:
        play_from_queue_node(song_id)
        msg = f"🎵 立即播放: {title}"
    else:
        msg = f"➕ 已追加至队列尾部"

    return jsonify({
        "queue": PLAY_QUEUE, 
        "current_id": CURRENT_PLAYING_ID, 
        "state": get_alx_state(), 
        "msg": msg
    })

@app.route('/play_queue_id')
def play_queue_id():
    global PLAY_QUEUE, CURRENT_PLAYING_ID
    song_id = request.args.get('id', '')
    title = ""
    if song_id:
        for song in PLAY_QUEUE:
            if song['id'] == song_id:
                title = song['title']
                break
        play_from_queue_node(song_id)
    return jsonify({
        "queue": PLAY_QUEUE, 
        "current_id": CURRENT_PLAYING_ID, 
        "state": get_alx_state(), 
        "title": title
    })

@app.route('/remove_from_queue')
def remove_from_queue():
    global PLAY_QUEUE, CURRENT_PLAYING_ID
    song_id = request.args.get('id', '')
    if song_id:
        PLAY_QUEUE = [song for song in PLAY_QUEUE if song['id'] != song_id]
        if CURRENT_PLAYING_ID == song_id:
            subprocess.run(["alx", "stop"])
            CURRENT_PLAYING_ID = None
    return jsonify({
        "queue": PLAY_QUEUE, 
        "current_id": CURRENT_PLAYING_ID, 
        "state": get_alx_state()
    })

@app.route('/clear_queue')
def clear_queue():
    global PLAY_QUEUE, CURRENT_PLAYING_ID
    PLAY_QUEUE = []
    CURRENT_PLAYING_ID = None
    subprocess.run(["alx", "stop"])
    return jsonify({
        "queue": PLAY_QUEUE, 
        "current_id": CURRENT_PLAYING_ID, 
        "state": get_alx_state()
    })

@app.route('/download_id')
def download_id():
    song_id = request.args.get('id', '')
    if song_id:
        subprocess.run(["alx", "config", "set", "download.output_dir", DOWNLOAD_DIR])
        cmd = ["alx", "download", "add", song_id]
        print(f"[Web] 执行单曲下载至 {DOWNLOAD_DIR}: {cmd}")
        subprocess.Popen(cmd)
        return "OK"
    return "FAILED"

@app.route('/download_all')
def download_all():
    global PLAY_QUEUE
    if not PLAY_QUEUE:
        return "FAILED"
    subprocess.run(["alx", "config", "set", "download.output_dir", DOWNLOAD_DIR])
    for song in PLAY_QUEUE:
        cmd = ["alx", "download", "add", song['id']]
        print(f"[Web] 执行批量下载至 {DOWNLOAD_DIR}: {cmd}")
        subprocess.Popen(cmd)
    return "OK"

@app.route('/cmd')
def cmd():
    global CURRENT_PLAYING_ID, PLAY_QUEUE
    c = request.args.get('c', '')
    if c:
        cmd_parts = c.split()
        
        if len(cmd_parts) >= 1 and cmd_parts[0] == "quit":
            CURRENT_PLAYING_ID = None
            args = ["alx", "quit"]
        
        elif len(cmd_parts) >= 2 and cmd_parts[0] == "seek":
            args = ["alx", "seek", cmd_parts[1]]

        elif len(cmd_parts) >= 1 and cmd_parts[0] == "next" and PLAY_QUEUE:
            for idx, song in enumerate(PLAY_QUEUE):
                if song['id'] == CURRENT_PLAYING_ID and idx + 1 < len(PLAY_QUEUE):
                    play_from_queue_node(PLAY_QUEUE[idx + 1]['id'])
                    return "OK"
            subprocess.run(["alx", "next"])
            return "OK"

        elif len(cmd_parts) >= 1 and cmd_parts[0] == "prev" and PLAY_QUEUE:
            for idx, song in enumerate(PLAY_QUEUE):
                if song['id'] == CURRENT_PLAYING_ID and idx - 1 >= 0:
                    play_from_queue_node(PLAY_QUEUE[idx - 1]['id'])
                    return "OK"
            subprocess.run(["alx", "prev"])
            return "OK"

        elif len(cmd_parts) >= 2 and cmd_parts[0] == "volume":
            vol_val = cmd_parts[1]
            if vol_val.startswith("-"):
                args = ["alx", "volume", "--", vol_val]
            else:
                args = ["alx", "volume", vol_val]

        elif len(cmd_parts) >= 2 and cmd_parts[0] == "download":
            if cmd_parts[1] != "add":
                args = ["alx", "download", "add"] + cmd_parts[1:]
            else:
                args = ["alx"] + cmd_parts

        else:
            args = ["alx"] + cmd_parts
            
        print(f"[Web] 执行底层控制命令: {args}")
        subprocess.run(args)
    return "OK"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888)
