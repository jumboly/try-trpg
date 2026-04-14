"""TryTRPG 機械処理ユーティリティ。

判定・度合判定・状態遷移・戦闘 1 攻撃解決を提供する。
ナラティブ（能力適用可否・描写）は Claude（GM）が担当する前提。

CLI:
    python3 TryTRPG.py judge --pl 1 --gm 0
    python3 TryTRPG.py damage --weapon --armor
    python3 TryTRPG.py attack --pl 1 --gm 0 --weapon
    python3 TryTRPG.py apply-damage --state 健常 --severity 重症
"""

from __future__ import annotations

import argparse
import json
import random
from typing import Literal

Severity = Literal["軽傷", "重症", "瀕死"]
State = Literal["健常", "軽傷", "重症1", "重症2", "瀕死", "気絶", "死亡"]

SEVERITY_VALUES: tuple[str, ...] = ("軽傷", "重症", "瀕死")
STATE_VALUES: tuple[str, ...] = ("健常", "軽傷", "重症1", "重症2", "瀕死", "気絶", "死亡")
ABILITY_MAX = 2  # 職業・趣味から +1d6 × 2 が上限


def _roll(n: int) -> list[int]:
    return [random.randint(1, 6) for _ in range(n)]


def judgement(pl_abilities: int = 0, gm_abilities: int = 0) -> dict:
    """通常判定。同値時は振り直し（能力なし 1d6 同士）まで内部で解決。

    Returns:
        {
            "rolls": [{"phase": "初回"|"振り直しN", "pl": [...], "gm": [...],
                       "pl_total": int, "gm_total": int, "result": "成功"|"失敗"|"同値"}],
            "result": "成功"|"失敗",
            "diff": int,           # 最終ロールの pl_total - gm_total（大成功/大失敗判定に使用）
            "grade": "大成功"|"成功"|"失敗"|"大失敗",
        }
    """
    # 上限超過は能力数のバリデーションで弾く（CLAUDE.md §4.4 最大 +2d6）
    if not (0 <= pl_abilities <= ABILITY_MAX) or not (0 <= gm_abilities <= ABILITY_MAX):
        raise ValueError(f"能力数は 0〜{ABILITY_MAX} の範囲で指定すること（pl={pl_abilities}, gm={gm_abilities}）")
    rolls = []
    pl_dice_count = 1 + pl_abilities
    gm_dice_count = 1 + gm_abilities
    phase_label = "初回"
    reroll_idx = 0
    while True:
        pl = _roll(pl_dice_count)
        gm = _roll(gm_dice_count)
        pl_total, gm_total = sum(pl), sum(gm)
        if pl_total > gm_total:
            outcome = "成功"
        elif pl_total < gm_total:
            outcome = "失敗"
        else:
            outcome = "同値"
        rolls.append({
            "phase": phase_label, "pl": pl, "gm": gm,
            "pl_total": pl_total, "gm_total": gm_total, "result": outcome,
        })
        if outcome != "同値":
            diff = pl_total - gm_total
            if diff >= 4:
                grade = "大成功"
            elif diff >= 1:
                grade = "成功"
            elif diff <= -4:
                grade = "大失敗"
            else:
                grade = "失敗"
            return {"rolls": rolls, "result": outcome, "diff": diff, "grade": grade}
        # 振り直し: 双方 1d6（能力剥奪）
        reroll_idx += 1
        phase_label = f"振り直し{reroll_idx}"
        pl_dice_count = gm_dice_count = 1


def damage_roll(weapon: bool = False, armor: bool = False, bonus: int = 0) -> dict:
    """度合判定。武器+1 / 防具-1、および大成功/大失敗由来の bonus を適用し、1〜6 にクリップ。

    bonus は CLAUDE.md §4.5 の「追加利得/代償」を戦闘の度合判定へ反映するための調整値。
    """
    raw = random.randint(1, 6)
    modifier = (1 if weapon else 0) - (1 if armor else 0) + bonus
    modified = max(1, min(6, raw + modifier))
    if modified <= 2:
        sev: Severity = "軽傷"
    elif modified <= 5:
        sev = "重症"
    else:
        sev = "瀕死"
    return {"raw": raw, "modifier": modifier, "modified": modified, "severity": sev}


def apply_damage(state: State, severity: Severity, knockout: bool = False) -> dict:
    """状態遷移。重症 2 回 → 瀕死、瀕死で被弾 → 死亡。気絶は瀕死被弾時に任意。"""
    if state not in STATE_VALUES:
        raise ValueError(f"state は {STATE_VALUES} のいずれか（received: {state!r}）")
    if severity not in SEVERITY_VALUES:
        raise ValueError(f"severity は {SEVERITY_VALUES} のいずれか（received: {severity!r}）")
    new = state
    note = ""

    if state == "死亡":
        return {"state": "死亡", "note": "既に死亡"}
    if state == "気絶":
        # 気絶中の被弾はルール明記なし → GM 裁量。ここでは瀕死扱いに戻して死亡判定
        if severity in ("軽傷", "重症", "瀕死"):
            new = "死亡"
            note = "気絶中の被弾、GM 裁量で死亡"
        return {"state": new, "note": note}

    if state == "瀕死":
        new = "死亡"
        note = "瀕死で被弾 → 死亡"
        return {"state": new, "note": note}

    if severity == "瀕死":
        new = "気絶" if knockout else "瀕死"
        note = "瀕死（任意で気絶）" if knockout else "瀕死"
    elif severity == "重症":
        if state in ("健常", "軽傷"):
            new = "重症1"
        elif state == "重症1":
            new = "重症2"
        elif state == "重症2":
            new = "瀕死"
            note = "重症 3 回目 → 瀕死へ進行"
    elif severity == "軽傷":
        if state == "健常":
            new = "軽傷"
        else:
            # 既に軽傷以上の場合、軽傷追加では悪化させない（ルール未記載、GM 裁量）
            note = "軽傷追加だが現状態より軽いため据え置き"

    return {"state": new, "note": note}


def combat_attack(
    attacker_abilities: int = 0,
    defender_abilities: int = 0,
    weapon: bool = False,
    armor: bool = False,
    defender_state: State = "健常",
    knockout_if_fatal: bool = False,
    auto_grade_bonus: bool = True,
) -> dict:
    """1 攻撃の解決。命中判定 → 命中なら度合判定 → 状態遷移。

    auto_grade_bonus=True の場合、命中判定が大成功なら度合判定 +1、大失敗は適用なし
    （回避として終了するため）。CLAUDE.md §4.5 の運用を自動化。
    """
    hit = judgement(pl_abilities=attacker_abilities, gm_abilities=defender_abilities)
    # 攻撃判定では「攻撃側 = PL 位置」として judgement を流用
    if hit["result"] != "成功":
        return {"hit": hit, "damage": None, "state_after": defender_state, "note": "回避"}
    bonus = 1 if (auto_grade_bonus and hit.get("grade") == "大成功") else 0
    dmg = damage_roll(weapon=weapon, armor=armor, bonus=bonus)
    after = apply_damage(defender_state, dmg["severity"], knockout=knockout_if_fatal)
    return {"hit": hit, "damage": dmg, "state_after": after["state"], "note": after["note"]}


def _cli():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    j = sub.add_parser("judge")
    j.add_argument("--pl", type=int, default=0, help="PL 側の能力数（0/1/2）")
    j.add_argument("--gm", type=int, default=0, help="GM 側の能力数（0/1/2）")

    d = sub.add_parser("damage")
    d.add_argument("--weapon", action="store_true")
    d.add_argument("--armor", action="store_true")
    d.add_argument("--bonus", type=int, default=0, help="大成功/大失敗由来の度合判定調整（+1/-1 等）")

    a = sub.add_parser("attack")
    a.add_argument("--pl", type=int, default=0)
    a.add_argument("--gm", type=int, default=0)
    a.add_argument("--weapon", action="store_true")
    a.add_argument("--armor", action="store_true")
    a.add_argument("--state", default="健常", choices=list(STATE_VALUES))
    a.add_argument("--knockout", action="store_true")
    a.add_argument("--no-auto-grade-bonus", action="store_true",
                   help="命中判定の大成功による度合判定 +1 を無効化")

    s = sub.add_parser("apply-damage")
    s.add_argument("--state", required=True, choices=list(STATE_VALUES))
    s.add_argument("--severity", required=True, choices=list(SEVERITY_VALUES))
    s.add_argument("--knockout", action="store_true")

    args = p.parse_args()
    if args.cmd == "judge":
        out = judgement(args.pl, args.gm)
    elif args.cmd == "damage":
        out = damage_roll(args.weapon, args.armor, args.bonus)
    elif args.cmd == "attack":
        out = combat_attack(args.pl, args.gm, args.weapon, args.armor, args.state,
                            args.knockout, auto_grade_bonus=not args.no_auto_grade_bonus)
    elif args.cmd == "apply-damage":
        out = apply_damage(args.state, args.severity, args.knockout)
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    _cli()
