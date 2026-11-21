# EC Language Lab — 校园服务器部署指南 (Server Deployment Guide)

本压缩包为 **Python 生产级服务端版本**，支持全校同学独立注册登录、个人词库云端存储、实时在线全校排行榜（统计已刷词汇题数、已掌握词数、已刷语法题数与正确率）以及全部 40 支 24fps 语法精讲视频。

---

## 方式一：Linux 服务器一键启动（推荐 Ubuntu / Debian / CentOS）

1. 上传并解压 `ec_server_release.zip` 到服务器（例如 `/opt/ec-studio`）：
   ```bash
   mkdir -p /opt/ec-studio && cd /opt/ec-studio
   unzip ec_server_release.zip
   chmod +x start_server.sh
   ```
2. 前台测试运行（默认监听 `5000` 端口）：
   ```bash
   ./start_server.sh
   ```
   浏览器访问 `http://你的服务器IP:5000`，检查 `/api/health` 返回 `{"status":"ok"}`。

3. 后台常驻运行（推荐 systemd）：
   创建 `/etc/systemd/system/ec-studio.service`：
   ```ini
   [Unit]
   Description=EC Language Lab School Server
   After=network.target

   [Service]
   User=root
   WorkingDirectory=/opt/ec-studio
   Environment="PORT=5000"
   Environment="DEBUG=False"
   ExecStart=/opt/ec-studio/venv/bin/gunicorn --workers 4 --threads 4 --bind 0.0.0.0:5000 wsgi:application
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```
   启用并启动：
   ```bash
   systemctl daemon-reload
   systemctl enable ec-studio
   systemctl start ec-studio
   systemctl status ec-studio
   ```

---

## 方式二：Docker 一键部署

```bash
unzip ec_server_release.zip -d ec-studio && cd ec-studio
docker compose up -d --build
```
数据库与密钥持久化保存在 `./data/` 目录，升级代码不会丢失学生账号和排行榜数据。

---

## 方式三：宝塔面板 (BaoTa) Python 项目部署

1. 将 `ec_server_release.zip` 上传并解压到 `/www/wwwroot/ec-studio`。
2. 打开宝塔 **网站 → Python项目 → 添加Python项目**：
   - **项目路径**：`/www/wwwroot/ec-studio`
   - **启动方式**：`gunicorn`
   - **启动文件/模块**：`wsgi:application`
   - **端口**：`5000`
   - **依赖文件**：勾选 `requirements.txt` 自动安装
3. 绑定你的学校域名，并在宝塔一键申请 SSL 证书开启 HTTPS。

---

## 方式四：Windows 服务器部署

解压后直接双击运行 `start_server.bat`（自动创建虚拟环境并通过 Waitress 生产服务器运行在 `5000` 端口）。

---

## Nginx 反向代理参考（绑定 80/443 域名）

```nginx
server {
    listen 80;
    server_name your-domain.com;

    client_max_body_size 20M;

    location /static/ {
        alias /opt/ec-studio/static/;
        expires 7d;
    }

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 数据备份提示

所有学生账号、个人词库、错词记录、语法练习次数与全校排行榜均保存在 `data/ec_words.db`（已启用 SQLite WAL 高并发模式），定时备份 `data/` 目录即可。
