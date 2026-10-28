# Wagtopia 宠物美容预约 Demo

基于 [Tech Dev Case](https://tlwc3yxhu0.feishu.cn/wiki/FR1Fw3ZM4io2YykWt8scRCean7e) 实现的移动端 H5 全栈演示。Python 标准库后端 + SQLite + 原生 HTML/CSS/JavaScript，无需登录，无第三方运行依赖。

## 第一步：启动

安装 Python 3.10 或更新版本，然后在项目目录执行：

```bash
python app.py
```

打开 http://127.0.0.1:8000 。前后端由同一个进程提供，无需分别启动或安装 npm 依赖；`requirements.txt` 仅记录无第三方依赖。Windows 若 `python` 命令不可用，可尝试 `py app.py` 或使用已安装 Python 的完整路径。

Windows 也可以在 PowerShell 中执行 `./start-demo.ps1`。脚本会依次寻找 Python Launcher、本机 Codex 自带 Python、系统 Python；可加 `-Port 8001` 更换端口。若系统策略阻止脚本执行，直接使用上面的 Python 命令即可。

可选参数：`python app.py --port 8001 --db data/demo.db`。默认只监听本机；如需同一局域网手机访问，使用 `--host 0.0.0.0`，再在手机浏览器打开电脑的局域网 IP 与端口，按系统提示放行本地网络。

数据库首次启动自动创建于 `data/wagtopia.db`，自动运行 `schema.sql` 和幂等的 `seed.sql`，重启保留已有预约。初始预约为空，所有姓名、电话均为虚构演示数据。

## 第二步：演示家长预约

1. 选择 Alice，再选择 Coco 或 Mochi。换成 Ben 后只会显示 Buddy，换成 Chloe 后只显示 Luna。
2. 选择 Wash（洗护）或 Grooming（美容）、美容师 Mia、任意日期的 10:00。
3. 点击确认预约。成功消息包含预约编号及开始、结束时间。所有服务固定 60 分钟，结束时间由后端计算。
4. 点击“查看美容师日程”，看到家长、狗狗、服务、日期与时间。

## 第三步：演示防重叠

使用同一日期、同一美容师 Mia：

| 新预约 | 已有 10:00–11:00 时的结果 |
| --- | --- |
| 10:00–11:00 | 409 拒绝 |
| 10:30–11:30 | 409 拒绝 |
| 09:30–10:30 | 409 拒绝 |
| 11:00–12:00 | 201 成功，允许相邻 |
| Leo 的 10:00–11:00 | 201 成功，不同美容师独立 |

冲突判断采用半开区间：`已有.start < 新.end AND 已有.end > 新.start`。API 在 `BEGIN IMMEDIATE` 事务中插入，SQLite INSERT/UPDATE 触发器进一步阻止数据库层重叠，避免并发请求同时写入冲突预约。外键和组合外键检查狗狗所属家长；数据库 CHECK 约束固定 60 分钟。

## 第四步：运行验证

```bash
python -m unittest -v test_app.py
```

测试在临时数据库启动真实 HTTP 服务，覆盖参考数据、成功预约、日程关联、持久化、重叠/相邻、不同美容师、跨日、无效输入、狗狗归属、六个并发请求和数据库触发器。不会改动演示数据库。

## API

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| GET | `/api/parents` | 家长列表 |
| GET | `/api/parents/{id}/dogs` | 某家长的狗狗 |
| GET | `/api/groomers` | 美容师列表 |
| GET | `/api/services` | 服务列表 |
| GET | `/api/groomers/{id}/bookings` | 美容师全部预约，按时间排序 |
| POST | `/api/bookings` | 创建预约 |

POST 请求示例：

```json
{"parent_id":1,"dog_id":1,"groomer_id":1,"service_id":2,"start_time":"2026-11-01T10:00"}
```

成功返回 HTTP 201 与 `booking_id`、`start_time`、`end_time`。错误返回 `{"error":"说明"}`；无效输入为 400，时间冲突为 409，数据库忙碌为 503。时间格式严格为 `YYYY-MM-DDTHH:mm`，统一按同一家门店当地时间解释，不包含时区换算。不存在的家长/美容师的列表子资源返回空数组。

## 数据结构与代码

`parents` 1:N `dogs`；`bookings` 引用 `parents`、`dogs`、`groomers` 和 `services`。完整字段、约束、索引和触发器见 `schema.sql`。

```text
app.py           后端、API、事务、静态资源服务
schema.sql       数据库表、外键、索引、防重叠触发器
seed.sql         3 位家长、4 只狗、3 位美容师、2 项服务
static/          响应式页面、样式、前端逻辑
test_app.py      HTTP 与数据库集成测试
screenshots/     预约页、日程页演示截图
```

## 范围与取舍

按题目要求，不实现登录、注册。仅限制美容师重叠；同一狗狗在不同美容师的重叠预约不额外限制。未设定营业时间、过去时间限制、取消/修改预约、价格和支付；支持任意合法分钟与跨日预约。页面防止重复点击，但网络重试没有幂等键，重复的相同时段请求会由防重叠规则拒绝。

Python `http.server` 适合本地演示，正式部署应更换生产级服务并增加身份校验、权限、HTTPS、请求限流、备份以及明确的时区策略。
