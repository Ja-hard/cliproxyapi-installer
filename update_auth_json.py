#!/usr/bin/env python3
import glob
import json
import os

# ========== 可配置区域 ==========
SCAN_DIR = "/home/rachel/cliproxyapi/auth"
DRY_RUN = False
USER_AGENT = "codex-cli/0.114.0"

# 默认 priority
DEFAULT_PRIORITY = 0

# 文件名命中规则。按顺序匹配，命中后使用对应 priority。
FILENAME_PRIORITY_RULES = {
    "plus": 20,
}

# email 白名单模式。支持 fnmatch 风格通配符，命中后会直接覆盖为 WHITELIST_PRIORITY。
EMAIL_WHITELIST = [
    # "*@gmail.com",
    "gmail.com",
    "foxmail.com",
    "qq.com",
]
WHITELIST_PRIORITY = -1


def match_email_whitelist(email):
    normalized_email = str(email).strip().lower()
    for pattern in EMAIL_WHITELIST:
        normalized_pattern = str(pattern).strip().lower()
        if normalized_pattern and normalized_pattern in normalized_email:
            return pattern

    return None


def get_priority_rule(path, data):
    basename = os.path.basename(path).lower()
    email = str(data.get("email", "")).strip().lower()

    # plus 相关文件优先级最高，覆盖设置最大 priority=20
    for keyword, priority in FILENAME_PRIORITY_RULES.items():
        if keyword.lower() in basename:
            return priority, "plus"

    # 白名单优先级次之，覆盖设置最小 priority=-1
    matched_pattern = match_email_whitelist(email)
    if email and matched_pattern:
        return WHITELIST_PRIORITY, "whitelist"


    return DEFAULT_PRIORITY, "default"


def update_file(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    changed = False

    target_priority, matched_rule = get_priority_rule(path, data)
    should_update_priority = matched_rule != "default" or "priority" not in data
    if should_update_priority and data.get("priority") != target_priority:
        data["priority"] = target_priority
        changed = True

    headers = {"User-Agent": USER_AGENT}
    if data.get("headers") != headers:
        data["headers"] = headers
        changed = True

    if not changed:
        return False, target_priority, matched_rule

    if not DRY_RUN:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            f.write("\n")

    return True, target_priority, matched_rule


def main():
    pattern = os.path.join(SCAN_DIR, "*.json")
    files = sorted(glob.glob(pattern))

    if not files:
        print(f"未找到 JSON 文件: {pattern}")
        return

    updated = 0
    plus_matched = 0
    whitelist_matched = 0
    for path in files:
        basename = os.path.basename(path)
        changed, target_priority, matched_rule = update_file(path)

        if matched_rule == "plus":
            plus_matched += 1
        elif matched_rule == "whitelist":
            whitelist_matched += 1

        if changed:
            updated += 1
            prefix = "[预览] " if DRY_RUN else ""
            print(f"{prefix}{basename}: priority={target_priority}")

    print(f"\n合计: {len(files)} 个文件, {updated} 个已更新")
    print(f"匹配 Plus: {plus_matched}")
    print(f"匹配白名单邮箱: {whitelist_matched}")
    if DRY_RUN:
        print("(dry-run 模式，未实际写入)")


if __name__ == "__main__":
    main()
