# Jev Ultrafast Skill

[English](README.md) | [简体中文](README.zh-CN.md)

将 [browser-use/jev-ultrafast](https://github.com/browser-use/jev-ultrafast) 封装为可供 Codex 及其他支持 `SKILL.md` 的代理使用的浏览器自动化 Skill。本项目是社区封装，与 Browser Use 或 TypeSafe 没有官方隶属或背书关系。

Jev 负责选择浏览器操作和目标，Browser Harness 负责控制 Chrome。本仓库提供代理操作说明和带步数限制的执行脚本，不包含上游运行环境、模型权重、API Key 或浏览器用户数据。

## 安装 Skill

运行以下命令，然后选择你使用的代理：

```sh
npx skills add SherseaHe/jev-ultrafast-skill --skill jev-ultrafast
```

添加 `-g` 可全局安装。如果已经克隆本仓库，也可以在仓库根目录运行：

```sh
npx skills add . --skill jev-ultrafast
```

也可以将 `skills/jev-ultrafast` 复制到代理的 Skill 目录；Codex 的目录为 `~/.codex/skills/jev-ultrafast`。覆盖前请保留已有的自定义 Skill。

**安装 Skill 后，还需要配置独立的 Jev 运行环境。** Skill 本身不会包含或代填你的 API Key。

## 配置运行环境

需要 Git、uv、Python 3.12+（可由 uv 安装），以及受支持的本机 Chrome。本封装已在 macOS 和 Chrome 上实测，其他平台尚未验证。

以下命令将上游安装到独立目录，并固定到本封装验证过的版本：

```sh
JEV_RUNTIME="${JEV_ULTRAFAST_HOME:-$HOME/.local/share/jev-ultrafast}"
git clone https://github.com/browser-use/jev-ultrafast.git "$JEV_RUNTIME"
cd "$JEV_RUNTIME"
git checkout 1231850a0bf1a0c0341fe408ef1668dbbfdfac46
uv sync --locked --python 3.12
cp .env.example .env
chmod 600 .env
```

如果已经安装，请复用现有目录，先确认版本，不要覆盖已有 `.env` 或重置本地修改。使用其他路径时，将 `JEV_ULTRAFAST_HOME` 设置为该目录的绝对路径，并确保运行代理时能读取此环境变量。

在运行环境目录内编辑 `.env`：

```dotenv
TYPESAFE_API_KEY=
TYPESAFE_MODEL=jev-latest
TEXT_MODEL_API_KEY=
TEXT_MODEL_BASE_URL=https://openrouter.ai/api/v1
TEXT_MODEL=inception/mercury-2.5
TEXT_MODEL_REASONING=none
```

- 在 [TypeSafe 控制台](https://console.typesafe.ai/keys) 获取 Jev 使用的 Key，填写到 `TYPESAFE_API_KEY`。
- `TYPE_TEXT` 操作需要额外的文本生成模型；上面的示例使用 OpenRouter，需要单独的 `TEXT_MODEL_API_KEY`。只滚动、查看页面时无需文本生成。
- 示例模型名称及可用性可能变化，请以所选服务商的文档为准。
- `.env` 只放在运行环境目录中，不要提交到本 Skill 仓库。

在 Chrome 中打开 `chrome://inspect/#remote-debugging`，开启远程调试，并允许浏览器的连接请求。连接异常时，在运行环境目录执行：

```sh
uv run browser-harness --doctor
```

本机 Chrome 使用你的登录状态，无需登录 Browser Use Cloud。可参考 [Browser Harness 连接说明](https://github.com/browser-use/browser-harness/blob/main/install.md)。

如果需要上游可视化调试界面，在运行环境目录执行 `uv run jev`，再打开 `http://127.0.0.1:8766`。Skill 执行脚本不依赖这个界面。

## 使用方法

直接向代理描述任务，例如：

> 用 $jev-ultrafast 打开 https://01.me/，向下滚动，找到文章“当所有人都去卷 Coding，我在做什么？”。确认标题可见后停止。

代理会根据 [SKILL.md](skills/jev-ultrafast/SKILL.md) 调用脚本，执行多轮“观察 → 决策 → 操作”，并检查结果。

默认允许滚动、等待和停止。只有任务需要且已获得授权时，才启用 `CLICK`、`SELECT` 或 `TYPE_TEXT`。脚本支持：

| 参数 | 用途 |
| --- | --- |
| `--url` | 要打开的 HTTP(S) 网页 |
| `--goal` | 具体的自然语言任务目标 |
| `--max-steps` | 最多预测轮数，默认 20，范围 1–60 |
| `--allow-operation` | 额外允许的操作，可重复传入 |
| `--expect-text` | 检查最终可见区域是否包含指定文字 |
| `--expect-url` | 检查最终 URL 是否与指定值完全一致 |
| `--full-text` | 按需输出已渲染的 `document.body.innerText` |

输出为 JSON，包含状态、校验结果、URL、标题、耗时及操作名称。`verified: null` 表示没有提供独立校验条件；模型返回 `done` 并不等于任务已经得到验证。

## 行为与限制

- 默认最多执行 20 轮预测，页面失效后的重新预测也计入预算。
- 遇到未知执行错误时，不会自动重放操作，避免重复点击或提交。
- 运行结束（包括出错）时关闭本次创建的标签页，不保留标签页供后续接管。
- 分开报告初始化与执行耗时，不承诺所有任务都能加速。
- 默认观察当前可见区域，文本上限为 6,000 字符；可通过滚动读取更多内容。
- 全文输出需显式启用，不会自动加载分页或尚未加载的内容。单纯抓取文字不必增加 Jev 决策。
- 操作白名单只区分操作类型，不能区分普通点击与支付、删除等操作。需要操作前确认的阶段，应使用逐步检查与执行流程。
- 继承上游对 iframe、Shadow DOM、canvas、上传、弹出标签页及嵌套滚动等能力的限制。

API 调用可能产生费用。任务中的网页观察内容会发送给 TypeSafe，需要生成输入文字时，相应上下文会发送给配置的文本模型服务。测试结果仅代表已验证的页面和运行环境，不是通用可靠性保证。

## 开发与测试

在本仓库根目录运行：

```sh
python3 -m unittest discover -s tests -v
python3 skills/jev-ultrafast/scripts/run.py --help
```

测试为离线测试，不读取凭据、不连接浏览器，也不调用付费 API。实际浏览器执行需要通过上述 Python 3.12+ 的运行环境启动。已验证的上游版本为 `1231850a0bf1a0c0341fe408ef1668dbbfdfac46`。

## 开源许可

本封装使用 [MIT 许可证](LICENSE)。上游运行环境独立安装，保留其自身的 MIT 许可证和署名；本仓库没有复制上游源代码。
