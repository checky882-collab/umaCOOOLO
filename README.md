# 特雷森学园 · GitHub 免费立绘外链仓库模板包

本角色卡已 **内置直连你的公开 GitHub 立绘仓库**：

- **内置默认仓库**：`https://github.com/checky882-collab/umaCOOOLO`（默认分支 `main`）
- **自动加速 CDN**：`https://cdn.jsdelivr.net/gh/checky882-collab/umaCOOOLO@main`
- **自动备用直链**：`https://raw.githubusercontent.com/checky882-collab/umaCOOOLO/main`

角色卡本体保持零图片体积、极速导入；开箱即优先走 **jsDelivr 国内高速 CDN** 加载你仓库里的立绘，仓库内尚未上传某角色图片时自动无缝降级到伴生服 / GameTora / wsrv.nl / 矢量代表色徽章，绝不裂图！

---

## 立即上传到 `checky882-collab/umaCOOOLO`（两种任选）

同目录下的 `characters/` 文件夹已为你准备好本地 54 张高清 `.webp` 与从 GameTora 拉取的其余实装角色立绘，直接上传即可生效！

### 方式 A：GitHub 网页一键拖拽上传（最简单）
1. 打开你的仓库网页：<https://github.com/checky882-collab/umaCOOOLO>
2. 点击 **`Add file` → `Upload files`**。
3. 把本目录的 **`characters` 整个文件夹** 直接拖进上传框（如一次文件过多，可分批每批 ~80 个文件拖入 `characters/` 目录）。
4. 在底部点击 **`Commit changes`** 推送至 `main` 分支。
5. 无需在酒馆里再做任何配置——角色卡默认已指向 `checky882-collab/umaCOOOLO`，刷新页面即可享受秒开高清立绘！

### 方式 B：命令行一次性全部推送（适合一次传齐数百张图）
在本目录（`github-art-repo-template/`）打开终端执行：
```bash
git clone https://github.com/checky882-collab/umaCOOOLO.git _repo_upload
xcopy /E /I /Y characters _repo_upload\characters
cd _repo_upload
git add characters
git commit -m "Add Uma Musume portraits"
git push origin main
```

---

## 如需更换为其他 GitHub 仓库或自定义图床

1. 在 SillyTavern 中打开本角色卡，点开**悬浮马蹄铁终端 →「立绘外链与图源」**（或在状态栏点击任意马娘 **ID 徽章** 弹出立绘灯箱，点击「配置 GitHub 立绘外链」）。
2. 粘贴任意格式的新地址保存即可立即覆盖默认仓库：
   - 仓库网址：`https://github.com/你的用户名/仓库名`
   - 极简缩写：`你的用户名/仓库名`
   - 指定分支/子目录：`https://github.com/你的用户名/仓库名/tree/main/characters`
   - 自定义图床前缀：`https://cdn.jsdelivr.net/gh/你的用户名/仓库名@main` 或任意 `https://...` 图床地址
3. 特殊指令：
   - 输入 `off` / `clear` 或留空保存 → **关闭 Tier 0 外链**，自动回退 Tier 1~4；
   - 输入 `default` / `reset` 保存 → **恢复内置默认仓库** `checky882-collab/umaCOOOLO`。

---

## 图片命名规范与多目录容错

路由器对每名角色按以下顺序自动探测（兼容 `.webp` 与 `.png`，放仓库根目录或 `characters/` 子目录均不会裂图）：

1. `{cdnBase}/{uma_id}_{variant}.webp`
2. `{cdnBase}/{uma_id}_{variant}.png`
3. `{cdnBase}/characters/{uma_id}_{variant}.webp`
4. `{cdnBase}/characters/{uma_id}_{variant}.png`
5. `{cdnBase}/{uma_id}.webp`（仅放一张单图也能通用！）
6. `{cdnBase}/{uma_id}.png`
7. `raw.githubusercontent.com` 同路径备链（GitHub 仓库自动附带）

### 三种服装变体（`variant`）
| 变体名 | 用途 | 文件名示例（东海帝王 `1003`） |
| --- | --- | --- |
| `racewear` | 决胜服（赛事阶段 / 灯箱决胜服预览） | `1003_racewear.webp` / `.png` |
| `uniform` | 特雷森校服（日常阶段 / 状态栏默认） | `1003_uniform.webp` / `.png` |
| `thumb` | 方形头像（状态栏头像 / 小队切换胶囊） | `1003_thumb.webp` / `.png` |

> 完整 172 名角色（含 145 名实装/登场赛马娘与 27 名传奇/学园 NPC）的 `cid`、`uma_id`、中文名与推荐文件名清单请查阅同目录 [`manifest_172.json`](./manifest_172.json)。

### 常见热门角色 ID 速查
| 角色名 | `uma_id` | 推荐文件名 |
| --- | --- | --- |
| 特别周 | `1001` | `1001_racewear.webp` / `1001_uniform.webp` / `1001_thumb.webp` |
| 无声铃鹿 | `1002` | `1002_racewear.webp` / `1002_uniform.webp` / `1002_thumb.webp` |
| 东海帝王 | `1003` | `1003_racewear.webp` / `1003_uniform.webp` / `1003_thumb.webp` |
| 小栗帽 | `1006` | `1006_racewear.webp` / `1006_uniform.webp` / `1006_thumb.webp` |
| 黄金船 | `1007` | `1007_racewear.webp` / `1007_uniform.webp` / `1007_thumb.webp` |
| 目白麦昆 | `1013` | `1013_racewear.webp` / `1013_uniform.webp` / `1013_thumb.webp` |
| 米浴 | `1030` | `1030_racewear.webp` / `1030_uniform.webp` / `1030_thumb.webp` |
| 北部玄驹 | `1068` | `1068_racewear.webp` / `1068_uniform.webp` / `1068_thumb.webp` |
| 黄金巨匠 | `1115` | `1115_racewear.webp` / `1115_uniform.webp` / `1115_thumb.webp` |
| 贵妇人 | `1116` | `1116_racewear.webp` / `1116_uniform.webp` / `1116_thumb.webp` |
| 周日宁静 | `400` | `400_racewear.webp` / `400_uniform.webp` / `400_thumb.webp` |

---

## 五级零体积外链容错架构

1. **Tier 0 · GitHub 外链图床**：默认直连 `checky882-collab/umaCOOOLO`（jsDelivr CDN + raw 备链，可随时覆盖或关闭）
2. **Tier 1 · 本地/局域网伴生服**：若本机或局域网运行伴生资源服（默认 `http://127.0.0.1:5173`）则自动读取
3. **Tier 2 · GameTora 官方高清图源**：直连 `chara_stand_{umaId}_{outfitId}.png` 与 `chr_icon_{umaId}.png`
4. **Tier 3 · wsrv.nl 加速代理**：国内直连不稳定时自动走 `wsrv.nl` WebP 压缩代理
5. **Tier 4 · 矢量代表色徽章**：完全断网时兜底生成零 `<filter>` 纯矢量 SVG 徽章，绝不裂图

---

## 脚本参数速览（`fetch_portraits_for_github.py`）

```bash
# 1. 仅复制本地已有 54 张高清 .webp 到 ./characters/（默认行为，不联网）
python fetch_portraits_for_github.py

# 2. 复制本地 54 张 + 礼貌并发从 GameTora 补全全部实装角色（支持断点续传）
python fetch_portraits_for_github.py --fetch-gametora --workers 8 --delay 0.15 --max-seconds 55

# 3. 仅补抓指定角色 ID（如 1004 丸善斯基、1024 重炮）
python fetch_portraits_for_github.py --fetch-gametora --ids 1004,1024
```
