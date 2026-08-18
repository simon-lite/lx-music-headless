#!/bin/bash
set -e

echo "=== 开始安装 upmpdcli (Debian 13 Trixie) ==="

# 1. 检查 root 权限
if [ "$(id -u)" -ne 0 ]; then
    echo "[错误] 请使用 root 权限或 sudo 运行此脚本！"
    exit 1
fi

# 2. 清理历史可能冲突的旧配置文件
echo "[1/5] 清理旧配置文件..."
rm -f /etc/apt/sources.list.d/upmpdcli*

# 3. 创建密钥目录并下载 GPG 密钥
echo "[2/5] 下载并导入 GPG 密钥..."
mkdir -p /usr/share/keyrings
wget -q -O /usr/share/keyrings/lesbonscomptes.gpg https://www.lesbonscomptes.com/pages/lesbonscomptes.gpg

if [ $? -eq 0 ] && [ -s /usr/share/keyrings/lesbonscomptes.gpg ]; then
    echo "✓ 密钥下载成功: /usr/share/keyrings/lesbonscomptes.gpg"
else
    echo "[错误] 密钥下载失败，请检查网络连接！"
    exit 1
fi

# 4. 检测 CPU 架构并配置软件源
echo "[3/5] 检测系统架构并配置软件源..."
ARCH=$(uname -m)

if [[ "$ARCH" == "aarch64" || "$ARCH" == "armv7l" || "$ARCH" == "armv6l" ]]; then
    echo "检测到 ARM 架构 ($ARCH)，下载 ARM 专用源配置..."
    wget -q -O /etc/apt/sources.list.d/upmpdcli.sources https://www.lesbonscomptes.com/upmpdcli/pages/upmpdcli-rtrixie.sources
else
    echo "检测到 x86/AMD64 架构 ($ARCH)，下载通用源配置..."
    wget -q -O /etc/apt/sources.list.d/upmpdcli.sources https://www.lesbonscomptes.com/upmpdcli/pages/upmpdcli-trixie.sources
fi

if [ $? -eq 0 ] && [ -s /etc/apt/sources.list.d/upmpdcli.sources ]; then
    echo "✓ 软件源配置成功: /etc/apt/sources.list.d/upmpdcli.sources"
else
    echo "[错误] 软件源下载失败！"
    exit 1
fi

# 5. 更新 APT 并安装 upmpdcli
echo "[4/5] 更新 APT 缓存..."
apt update

echo "[5/5] 安装 upmpdcli 及其推荐依赖..."
apt install -y upmpdcli

echo "=== 安装完成！ ==="
systemctl status upmpdcli --no-pager
