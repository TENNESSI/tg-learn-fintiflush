FIGURES = ["triangle", "parallelogram", "rhombus", "trapezoid"]


def empty_stats() -> dict[str, dict[str, int]]:
    return {figure: {"correct": 0, "wrong": 0} for figure in FIGURES}


user_sessions: dict[int, dict] = {}
