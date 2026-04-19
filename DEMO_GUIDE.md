# DEMO_GUIDE

本指南用于答辩演示和 GitHub 展示，目标不是展示“完整系统”，而是展示“一个能跑通、能解释、能体现技术点的最小闭环原型”。

## 推荐演示顺序

建议按下面顺序演示，节奏最稳定：

1. 展示 `examples/series_ok.json`
2. 运行 CLI，展示正常求解结果
3. 展示 `examples/open_switch.json`
4. 运行 CLI，展示开路诊断与教学提示
5. 展示 `examples/short_risk.json`
6. 运行 CLI，展示短路风险与教师介入建议
7. 任选一个仪表错误案例，强调教学价值

## 推荐命令

```bash
cd 03_core_algorithm
python -m src.cli --input examples/series_ok.json
python -m src.cli --input examples/open_switch.json
python -m src.cli --input examples/short_risk.json
python -m src.cli --input examples/ammeter_parallel_error.json
pytest
```

## 每个样例的展示重点

### `series_ok.json`

- 展示最小输入格式
- 展示节点电压和支路电流
- 强调“这是基于 MNA 的真实数值求解，不只是字符串规则判断”

### `parallel_ok.json`

- 展示并联支路电压相同
- 展示支路电流不同
- 强调算法支持基础网络而不只是单一串联

### `open_switch.json`

- 展示断开的开关
- 展示开路诊断
- 展示启发式提示如何引导学生先判断回路是否闭合

### `short_risk.json`

- 展示电源两端被低阻旁路
- 展示短路风险标记为高优先级问题
- 展示教师介入建议，强调实验安全性

### `ammeter_parallel_error.json`

- 展示“电流表应该串联”的规则
- 展示错误定位到具体器件 ID
- 展示从错误检测到直接纠错建议的闭环

### `voltmeter_series_error.json`

- 展示“电压表应该并联”的规则
- 展示错误接法会导致回路几乎开路
- 强调“求解结果 + 教学解释”是同时给出的

## 推荐截图方案

建议准备 4 张图，信息密度高且容易讲：

### 图 1: 目录结构

截图 `03_core_algorithm/` 目录树：

- `src/`
- `examples/`
- `tests/`
- `README.md`
- `DEMO_GUIDE.md`

适合说明“项目结构清晰、可交付、可复现”。

### 图 2: 输入格式

打开 `examples/series_ok.json` 截图，建议框出：

- `components`
- `nodes`
- `params`
- `voltage_source`
- `resistor`
- `switch`

适合说明“我们设计了统一电路 JSON 表示”。

### 图 3: 正常求解输出

运行：

```bash
python -m src.cli --input examples/series_ok.json
```

截图时保留下面几段：

- `Solver Summary`
- `Node Voltages`
- `Element Measurements`

适合说明“核心算法可运行，并能给出可解释的物理量”。

### 图 4: 错误诊断与教学反馈

运行：

```bash
python -m src.cli --input examples/short_risk.json
```

或者：

```bash
python -m src.cli --input examples/ammeter_parallel_error.json
```

截图时保留：

- `Diagnostics`
- `HACP-style Feedback`

适合说明“系统不仅能算，还能做教学干预”。

## 讲解话术建议

可以用下面这套简短逻辑：

1. “我们没有重做完整 GUI，而是提炼出了核心算法和最小可运行 demo。”
2. “输入是统一电路 JSON，包含元件、节点连接和参数。”
3. “核心计算采用 MNA 进行直流求解，可以得到节点电压和元件电流。”
4. “在此基础上，我们增加了开路、短路风险和仪表接法异常的教学诊断。”
5. “最后输出 HACP 风格的教学反馈，形成从求解到纠错建议的闭环。”

## 答辩时如何截图用于展示

- 优先使用终端深色主题或 VS Code 集成终端，层次更清晰。
- 命令行窗口宽度保持在 100 到 120 列，避免换行破坏可读性。
- 一张截图只讲一个重点，不要把目录、JSON、输出全堆在同一张图里。
- 对于正常样例，保留“输入文件名 + 节点电压 + 元件电流”三块信息。
- 对于错误样例，保留“诊断码 + 中文说明 + 教学反馈”三块信息。
- 可以在 PowerPoint 中用红框标出 `OPEN_CIRCUIT`、`SHORT_RISK`、`AMMETER_PARALLEL` 等关键词。
- 建议至少准备“正常闭环”和“错误闭环”两组对照截图，便于突出系统价值。
