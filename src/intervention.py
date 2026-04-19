"""HACP-style teaching intervention generator for the minimal demo."""

from __future__ import annotations

from .models import DiagnosticItem, TeachingFeedback


INTERVENTION_RULES = {
    "OPEN_CIRCUIT": {
        "hint": "先追踪电流路径：电流是否能从电源正极出发，再回到负极？",
        "fix": "优先检查开关是否断开，以及是否缺少返回电源负极的连接。",
        "teacher": "教师可现场画出最小闭合回路，对比开路前后电流读数变化。",
    },
    "SHORT_RISK": {
        "hint": "观察电源两端之间是否存在几乎不经过负载的低阻通路。",
        "fix": "移除直接跨接电源的导通支路，让电流先经过电阻等负载元件。",
        "teacher": "教师应立即介入，强调短路的安全风险与实验规范。",
    },
    "AMMETER_PARALLEL": {
        "hint": "回想电流表的任务是测流，它应该在支路里还是跨在元件两端？",
        "fix": "把电流表移到目标支路的串联位置，不要并联在负载两端。",
        "teacher": "教师可用一张串联/并联对比图快速纠正认知。",
    },
    "VOLTMETER_SERIES": {
        "hint": "电压表测的是两点电势差，因此应关注它连接的是哪两个端点。",
        "fix": "把电压表并接在被测元件两端，而不是插入主回路。",
        "teacher": "教师可示范把电压表从主回路挪到负载两端，比较读数变化。",
    },
    "INVALID_RESISTANCE": {
        "hint": "元件参数是否满足物理意义，例如电阻不能为零或负数。",
        "fix": "将电阻值改为正数，并优先使用课堂示例中的常见阻值。",
        "teacher": "教师可说明模型参数与真实器件标称值之间的关系。",
    },
    "INVALID_VOLTAGE": {
        "hint": "电源必须先给出明确电压，求解器才能计算整个网络。",
        "fix": "为电源补充数字化电压参数，例如 6V 或 12V。",
        "teacher": "教师可补充独立电压源在建模中的作用。",
    },
}


def build_teaching_feedback(diagnostics: list[DiagnosticItem]) -> TeachingFeedback:
    """Convert diagnostics into staged teaching feedback."""
    if not diagnostics:
        return TeachingFeedback(
            overall_level="normal",
            heuristic_hints=["当前电路结构正常，可以继续观察各节点电压和支路电流。"],
            direct_fixes=["无需纠错，可尝试修改参数观察串并联规律。"],
            teacher_actions=["教师可引导学生解释求解结果与欧姆定律的一致性。"],
        )

    heuristic_hints: list[str] = []
    direct_fixes: list[str] = []
    teacher_actions: list[str] = []

    highest_level = "light"
    for item in diagnostics:
        rule = INTERVENTION_RULES.get(item.code)
        if rule is not None:
            heuristic_hints.append(rule["hint"])
            direct_fixes.append(rule["fix"])
            teacher_actions.append(rule["teacher"])

        if item.severity == "error":
            highest_level = "high"
        elif item.severity == "warning" and highest_level != "high":
            highest_level = "medium"

    if not heuristic_hints:
        heuristic_hints.append("先从电源、负载、测量表三个角色重新梳理这条电路的功能。")
    if not direct_fixes:
        direct_fixes.append("按照电源-负载-回路闭合的顺序重新检查元件连接关系。")
    if not teacher_actions:
        teacher_actions.append("教师可结合正确样例与错误样例进行并排讲解。")

    return TeachingFeedback(
        overall_level=highest_level,
        heuristic_hints=_unique_preserve_order(heuristic_hints),
        direct_fixes=_unique_preserve_order(direct_fixes),
        teacher_actions=_unique_preserve_order(teacher_actions),
    )


def _unique_preserve_order(items: list[str]) -> list[str]:
    """Keep list order while removing duplicate intervention sentences."""
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result
