# SHOWCASE_GUIDE

这个文档只服务演示版，不展开讲全部实现细节。

## 1. 最快启动命令

```bash
cd 03_core_algorithm
python -m src.cli --demo --scenario normal_lab --compact
```

这条命令会直接进入展示版终端界面，适合先看整体效果。

## 2. 推荐演示场景

### `normal_lab`

- 适合展示“系统正常求解 + 教学解释”
- 重点看 `Circuit State`、`Physical Reasoning Output`、`Showcase Interpretation`

### `ammeter_miswire`

- 适合展示“仪表误接 + 纠错建议”
- 重点看 `Diagnostic Signals` 和 `Teacher Actions`

### `short_risk`

- 适合展示“高风险场景 + 教师接管”
- 重点看 `Risk Level`、`Intervention`、`System Judgement`

### `teacher_handoff`

- 适合展示“连续错误后的人机边界”
- 重点看 `Intervention` 与 `Teacher Note`

## 3. 常用命令

列出演示场景：

```bash
python -m src.cli --list-scenarios
```

运行正常展示版：

```bash
python -m src.cli --demo --scenario normal_lab
```

运行单屏截图版：

```bash
python -m src.cli --demo --scenario short_risk --compact
```

导出 SVG、HTML 和 JSON：

```bash
python -m src.cli --demo --scenario short_risk --compact ^
  --export-svg artifacts/short_risk.svg ^
  --export-html artifacts/short_risk.html ^
  --export-json artifacts/short_risk.json
```

直接导出 PNG 截图：

```bash
python -m src.cli --demo --scenario short_risk --compact ^
  --export-png artifacts/short_risk.png
```

## 4. 演示时怎么讲

建议只讲三层：

1. 当前电路状态是什么
2. 系统为什么这样判断
3. 下一步应该继续引导学生，还是让教师接手

对应到界面：

- `Circuit State`: 当前系统对电路的结构判断
- `Physical Reasoning Output`: 节点电压和元件电流，说明不是纯规则判断
- `Diagnostic Signals`: 当前问题到底在哪里
- `Intervention`: 当前应该如何推进教学
- `Showcase Interpretation`: 适合直接口播的讲解文本

## 5. 推荐先截图的三个文件

- `artifacts/normal_lab.svg`
- `artifacts/short_risk.svg`
- `artifacts/teacher_handoff.svg`

如果要直接放 PPT，优先使用：

- `artifacts/normal_lab.png`
- `artifacts/short_risk.png`

## 6. DeepSeek 位置

当前演示版没有依赖 DeepSeek API。

现在的教学文案和展示数据来自：

- 内置 demo 场景元数据
- 求解器结果
- 诊断规则
- 演示文案模板

如果后续要接 DeepSeek，建议只替换：

- `system judgement`
- `pedagogical interpretation`
- `presentation script`

不要直接替换底层求解和诊断结果。
