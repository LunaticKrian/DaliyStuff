"""极简成本估算（USD）。仅 GLM / Claude 系粗估，后续可接入真实价目。

单位：每 1k token 的 USD 价格 (input, output, cache_read, cache_write)。
"""
_PRICING = {
    # 更具体的前缀放前面（startswith 顺序匹配）
    "glm-5":   (0.002,  0.006, 0.001, 0.002),
    "glm-4.6": (0.001,  0.002, 0.0005, 0.001),
    "glm":     (0.001,  0.002, 0.0005, 0.001),
    "claude":  (0.003,  0.015, 0.0003, 0.00375),
}
_DEFAULT = (0.001, 0.002, 0.0005, 0.001)


def estimate_cost(
    model: str, input_tokens: int, output_tokens: int,
    cache_read: int = 0, cache_write: int = 0,
) -> float:
    m = (model or "").lower()
    rate = _DEFAULT
    for prefix, r in _PRICING.items():
        if m.startswith(prefix):
            rate = r
            break
    ip, op, cr, cw = rate
    cost = (
        (input_tokens / 1000) * ip
        + (output_tokens / 1000) * op
        + (cache_read / 1000) * cr
        + (cache_write / 1000) * cw
    )
    return round(cost, 6)
