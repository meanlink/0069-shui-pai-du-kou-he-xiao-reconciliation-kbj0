# 水牌 · 渡口核销对账

青屿渡运合作社的 8 名值班员在东、西两个检票闸为西沙渡和北湾渡核销月票。过去他们把排班表、闸口日志和异常纸单分开抄进表格，常重复计算双闸刷卡、把过午夜的航班归错营业日、漏掉纸单未处理。水牌对齐三个来源，将结算底表交给财务。

| 角色 | 页面和权限 |
|---|---|
| operator | 发班水牌、补记闸刷、提交复核 |
| reviewer | 确认过窗记录、驳回不适用月票、签署营业日 |
| viewer | 查阅全部页面及下载已冻结 CSV |

## 一个工作日

1. 07:35 排班水牌确认西沙渡 F-102 08:00 离岸，核定 30 人。
2. 07:41 东闸登记月票 M-071 的 GF-01；07:44 的西闸 GF-02 被归入重复。
3. 07:55 值班员将 07:35 的 GF-03 过窗流水提交复核，附纸本乘船单。
4. 09:00 北湾渡 F-211 的 GF-08 因月票于 10 月 31 日到期留待核查。
5. 次日 00:05 的 F-201 仍计入 11 月 19 日营业日；这班单独计 M-071。
6. 01:10 复核人员驳回 GF-08，补计 GF-03，F-102 月票核销从 2 变为 3。
7. 01:15 签署并下载 ferry-2026-11-19.csv，后台计算账单 SHA-256。

## 口径

营业日内读秒窗是离岸分钟减 20 至加 3，边界均包含。相同营业日、航线及有效期校验通过后，以每船班每票号为计数键；原始日志标记核销进入系统的顺序，透视按集合去重。分母为船班核定载客。计数超过核定载客或有待签复核时拒绝封账。源数据及计算结果在封账后冻结。

## 启动

```sh
cp -n .env.example .env
docker compose up -d --build --wait
docker compose exec backend python -m scripts.seed_demo
docker compose down -v --remove-orphans
```

访问由 .env 的 FRONTEND_PORT（前端）和 BACKEND_PORT（API）配置的本机地址。三个演示账号为 operator@demo.local、reviewer@demo.local、viewer@demo.local，默认密码 Demo2026!。DB_PORT 控制 PostgreSQL 本机映射。POSTGRES_PASSWORD、JWT_SECRET、DEMO_PASSWORD 建议在非本机演示时替换，SEED_DEMO 控制启动填充。

前端是 Nginx 与原生 HTML/CSS/ES modules，后端为 Python/FastAPI，数据库是 PostgreSQL，Redis 处理登录限频，worker 处理签账凭据。后端本地常规开发使用 backend/requirements.txt、DATABASE_URL、REDIS_URL、JWT_SECRET，运行 `uvicorn app:app --reload --port 8000`，worker 用 `python worker.py`。schema.sql 定义存储约束，backend/ferry 维护读秒、争议与封账，frontend/pier 是各工作台页面。横切枚举在 backend/core.py、frontend/base.js，闸机、核销、签审枚举在 backend/schema.sql、backend/ferry 的对应模型及 frontend/pier/words.js。MIT 许可证。

前端地址为 http://127.0.0.1:18463，API 为 http://127.0.0.1:19463，数据库本机映射端口为 17963。
