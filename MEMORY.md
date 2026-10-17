# OrbitLab 项目记忆

最后更新：2026-10-17（Asia/Shanghai）

## 协作约定

- 每次完成代码修改后，同步更新本文件；具体规则见 `AGENTS.md`。
- 本文件用于跨会话延续项目上下文。代码和用户最新指令优先于历史记录。

## 当前项目

- OrbitLab 是使用 Python 与 Pygame 实现的二维天体轨道沙盒。
- 物理计算使用带软化项的牛顿 N 体模型和 Velocity Verlet 积分。
- 支持暂停、单步推进、时间倍速、视图缩放与平移、天体跟随、轨迹显示与预测、天体创建与编辑、碰撞合并、能量监测、场景保存与加载、中英文切换。
- 预设场景：Solar System、Binary Star、Earth-Moon、Figure-8。
- 运行中按 `N` 会自动暂停、提示 `Paused for single step` 并推进一个物理步；暂停时继续按 `N` 单步，按 Space 恢复运行。
- 天体数量大于 80 时清空并跳过预测；数量恢复到 80 或以下后，在下一次预测刷新时恢复计算。
- 用户指定的 GitHub 仓库：`git@github.com:zhFelix/OrbitLab.git`。本项目使用独立 Git 仓库，`origin` 指向该地址；提交分支为 `codex/orbitlab-refactor-cr123`。

## 文件与运行

- `orbitlab/main.py`：启动 `App`，保留原有 `main()` 和 KeyboardInterrupt 退出处理。
- `orbitlab/config.py`：`CONFIG`、滑块常量、`PROBE_TYPES`、`SCENE_LOCALIZED`、`TEXT`，以及 `BASE_DIR`、`PREFS_PATH`、`SCENE_PATH`。
- `orbitlab/bodies.py`：`Body`、四个场景工厂及 `SCENE_FACTORIES`。
- `orbitlab/physics.py`：完整 `Physics` 类。
- `orbitlab/camera.py`：完整 `Camera` 类，仅依赖 Pygame 和 future annotations。
- `orbitlab/app.py`：完整 `App` 类，包含所有应用状态、交互、UI 和渲染。
- 项目模块依赖严格单向：`main → app → {physics, camera, config, bodies}`，`physics → {bodies, config}`，`bodies → config`；不允许循环导入。
- 原单文件 `orbitlab.py` 已移除，避免遗留重复定义。
- `requirements.txt`：当前声明依赖 `pygame>=2.5`。
- `README.md`：安装、启动与交互操作说明。
- `orbitlab/prefs.json`：默认持久化界面与模拟偏好的位置。
- `orbitlab/scene.json`：默认保存场景快照的位置，不应将其天体列表视作默认预设。
- 安装依赖：`python -m pip install -r requirements.txt`。
- 启动：在项目根目录执行 `cd orbitlab`，然后 `python main.py`。
- 偏好、场景和截图的默认路径固定为 `Path(__file__).resolve().parent`（在 `config.py` 中定义，即 `orbitlab/` 目录），不受启动时工作目录影响；可从任意目录运行 `python /absolute/path/to/orbitlab/main.py`。
- 保存和加载方法仍接受显式 `path` 参数。根目录原有 JSON 文件未移动、未修改，也没有自动迁移到新的默认位置。

## 验证状态与待办

- 项目未引入测试依赖或常驻测试文件；拆分验证使用标准库临时脚本和已安装的 Pygame 2.6.1 / Python 3.10.12。
- 上一轮六模块拆分通过全部 16 个顶层定义的 AST 与源码逐字对照、原有注释完整性检查、六模块编译和指定依赖图检查；另在 SDL dummy 模式下通过 54 个状态、渲染和保存文件的对照检查点。
- 上一轮已在 `orbitlab/` 执行 `python main.py` 并通过 Ctrl+C 正常退出；UI 工具超时，原生窗口未完成可视化核验。
- 本轮 CR-1～CR-3 通过精确源码差异检查、六模块编译和依赖图检查；其余四个 Python 模块与修改前逐字节一致。
- 本轮 SDL dummy 验证通过：`N` 自动暂停且仅推进一步、再次单步和 Space 恢复；101/81 个天体不创建预测模拟，80/79 个天体在更新中恢复预测；无选中时清空预测。
- 本轮在临时副本和不同工作目录验证了默认文件路径、显式路径参数、四场景切换、天体质量编辑、存档往返、中英文切换、设置重启保持及渲染；另直接执行 `python /absolute/path/main.py`，注入 N/Ctrl+S/F12/退出事件，确认偏好、存档和截图均生成在脚本目录，退出码为 0。未修改用户的 JSON 或截图文件，未实测原生窗口帧率。
- 当前没有用户明确提出但尚未完成的功能需求。

## 最近变更

### 2026-10-17：首次 Git 提交

- 用户授权提交并推送当前项目。远程仓库初始为空，为本项目建立独立 Git 仓库。
- 提交包含六模块代码、CR-1～CR-3、项目说明、协作规则、项目记忆和原有根目录 JSON 文件。
- 新增 `.gitignore`，忽略 Python 缓存、macOS 元数据、截图和 `orbitlab/` 下生成的偏好及存档文件。
- 应用代码未额外修改，沿用上一轮已通过的验证；提交前检查暂存文件范围和补丁空白错误。推送结果以 Git 远程分支核验为准。

### 2026-10-17：CR-1～CR-3

- `orbitlab/app.py`：单步时自动暂停并显示指定提示；超过 80 个天体时提前结束预测；四个保存/加载方法及 F12 使用配置中的默认路径。
- `orbitlab/config.py`：添加标准库 `Path` 导入，以及 `BASE_DIR`、`PREFS_PATH`、`SCENE_PATH`。
- 仅按请求修改上述两份源文件；`main.py`、`bodies.py`、`physics.py`、`camera.py` 保持不变。
- `README.md` 同步单步行为、预测阈值及默认文件路径；本文件同步更新项目状态和验证结果。

### 2026-10-17：将单文件拆分为六个模块

- 按用户指定结构直接搬移代码，新增六个模块并移除原文件；完整保留 `App`，没有继续拆分 UI 或渲染。
- 仅增加必要导入和模块职责 docstring；保留原有类、函数、方法、常量值、字符串、注释和 docstring。原模块说明文本保留在 `main.py` docstring 内，因此其中的旧启动命令仅为原文保留；当前启动命令见上文及 README。
- 原有行为保持不变，包括 `step_once` 在未暂停时直接返回，以及删除主天体后的 `(primary)` 提示；未顺手修复其他逻辑。
- `README.md` 同步说明新结构、启动方式与当前工作目录的文件路径语义。
- 验证结果见上文；本次项目记忆已同步更新。

### 2026-10-17：建立项目记忆维护机制

- 根据用户要求新增 `AGENTS.md`，将“完成代码修改后同步更新项目记忆”写为项目协作规则。
- 新增本文件，记录已有项目概况、文件职责、运行方式与验证状态。
- 本次只添加项目文档，未修改应用代码；通过回读确认文件内容，未运行程序测试。
