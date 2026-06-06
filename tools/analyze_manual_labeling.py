"""P5-B Manual Labeling Aggregator.

Reads completed manual labels from ``reports/p5b_active_gap_labeling.csv`` and
produces priority-ranked backlogs for candidate / metadata / boundary work.
Does not modify recommendation logic or catalog data.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DEFAULT_INPUT = Path("reports/p5b_active_gap_labeling.csv")

REQUIRED_COLUMNS = (
    "id",
    "title",
    "recommended_visual",
    "final_visual",
    "current_taxonomy",
    "inferred_gap_type",
    "current_engine_visual",
    "current_engine_candidate_id",
    "current_engine_workflow",
    "resolved_by_current_engine",
    "active_gap",
    "still_no_candidate",
    "source_type_manual",
    "cause_type_manual",
    "action_hint_manual",
    "generalizable_manual",
    "note",
)

MANUAL_COLUMNS = (
    "source_type_manual",
    "cause_type_manual",
    "action_hint_manual",
    "generalizable_manual",
)

ALLOWED_SOURCE_TYPES = frozenset(
    {
        "workflow_mismatch",
        "visual_mismatch",
        "boundary_ambiguity",
        "candidate_gap",
        "metadata_gap",
        "personal_preference",
        "no_candidate",
        "unclear",
    }
)

ALLOWED_CAUSE_TYPES = frozenset(
    {
        "action_not_captured",
        "object_priority",
        "object_vs_channel",
        "interface_ignored",
        "catalog_gap",
        "metadata_missing",
        "visual_wrong_recall",
        "status_marker",
        "context_vs_action",
        "personal_association",
        "needs_more_data",
    }
)

ALLOWED_ACTION_HINTS = frozenset(
    {
        "add_candidate",
        "update_metadata",
        "adjust_boundary",
        "adjust_scoring",
        "suppress_overfit",
        "keep_as_preference",
        "needs_more_data",
    }
)

ALLOWED_GENERALIZABLE = frozenset({"yes", "no", "review"})

DEFER_ACTION_HINTS = frozenset(
    {"needs_more_data", "keep_as_preference", "suppress_overfit"}
)

BOUNDARY_CAUSE_TYPES = frozenset(
    {"object_vs_channel", "context_vs_action", "interface_ignored"}
)


def _parse_bool(value: str | None) -> bool:
    return str(value or "").strip().lower() == "true"


def _md_cell(text: str | None) -> str:
    return str(text or "").replace("|", "\\|").replace("\n", " ")


def _counter_dict(counter: Counter[str]) -> dict[str, int]:
    return dict(sorted(counter.items(), key=lambda item: (-item[1], item[0])))


@dataclass
class LabelRow:
    raw: dict[str, str]

    @property
    def id(self) -> str:
        return str(self.raw.get("id", "")).strip()

    @property
    def title(self) -> str:
        return str(self.raw.get("title", "")).strip()

    @property
    def active_gap(self) -> bool:
        return _parse_bool(self.raw.get("active_gap"))

    @property
    def still_no_candidate(self) -> bool:
        return _parse_bool(self.raw.get("still_no_candidate"))

    @property
    def source_type_manual(self) -> str:
        return str(self.raw.get("source_type_manual", "")).strip()

    @property
    def cause_type_manual(self) -> str:
        return str(self.raw.get("cause_type_manual", "")).strip()

    @property
    def action_hint_manual(self) -> str:
        return str(self.raw.get("action_hint_manual", "")).strip()

    @property
    def generalizable_manual(self) -> str:
        return str(self.raw.get("generalizable_manual", "")).strip()

    @property
    def note(self) -> str:
        return str(self.raw.get("note", "")).strip()

    def manual_fields_filled(self) -> bool:
        return all(str(self.raw.get(col, "")).strip() for col in MANUAL_COLUMNS)

    def priority_score(self) -> int:
        score = 0
        gen = self.generalizable_manual
        if gen == "yes":
            score += 3
        elif gen == "review":
            score += 1
        if self.active_gap:
            score += 2
        if self.still_no_candidate:
            score += 2
        action = self.action_hint_manual
        cause = self.cause_type_manual
        if action == "add_candidate" and cause == "catalog_gap":
            score += 2
        if action == "adjust_boundary" and cause in BOUNDARY_CAUSE_TYPES:
            score += 2
        if action == "update_metadata":
            score += 1
        if self.source_type_manual == "personal_preference":
            score -= 2
        if action == "needs_more_data":
            score -= 1
        return score

    def priority_label(self) -> str:
        score = self.priority_score()
        if score >= 7:
            return "high"
        if score >= 4:
            return "medium"
        return "low"

    def sort_key(self) -> tuple[int, int, int, int, str]:
        gen_rank = {"yes": 0, "review": 1, "no": 2}.get(self.generalizable_manual, 3)
        still_rank = 0 if self.still_no_candidate else 1
        add_rank = 0 if self.action_hint_manual == "add_candidate" else 1
        return (-self.priority_score(), gen_rank, still_rank, add_rank, self.id.zfill(6))


def load_labeling_csv(path: Path) -> list[LabelRow]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"{path} has no header row")
        missing = [col for col in REQUIRED_COLUMNS if col not in reader.fieldnames]
        if missing:
            raise ValueError(f"{path} missing required columns: {', '.join(missing)}")
        return [LabelRow(dict(row)) for row in reader]


def _collect_unknown_values(rows: list[LabelRow]) -> dict[str, list[str]]:
    unknown: dict[str, set[str]] = {
        "source_type_manual": set(),
        "cause_type_manual": set(),
        "action_hint_manual": set(),
        "generalizable_manual": set(),
    }
    allowed_map = {
        "source_type_manual": ALLOWED_SOURCE_TYPES,
        "cause_type_manual": ALLOWED_CAUSE_TYPES,
        "action_hint_manual": ALLOWED_ACTION_HINTS,
        "generalizable_manual": ALLOWED_GENERALIZABLE,
    }
    for row in rows:
        for col, allowed in allowed_map.items():
            value = str(row.raw.get(col, "")).strip()
            if value and value not in allowed:
                unknown[col].add(value)
    return {key: sorted(values) for key, values in unknown.items() if values}


def _in_bucket(row: LabelRow, action: str) -> bool:
    return (
        row.action_hint_manual == action
        and row.generalizable_manual in ("yes", "review")
    )


def _in_defer_bucket(row: LabelRow) -> bool:
    return (
        row.action_hint_manual in DEFER_ACTION_HINTS
        or row.generalizable_manual == "no"
    )


def _sorted_bucket(rows: list[LabelRow]) -> list[LabelRow]:
    return sorted(rows, key=lambda row: row.sort_key())


def suggest_candidate_direction(row: LabelRow) -> str:
    text = f"{row.title} {row.raw.get('final_visual', '')} {row.note}".lower()
    patterns: list[tuple[tuple[str, ...], str]] = [
        (("기차", "ktx", "🚄", "열차"), "train_reservation / KTX / 🚄"),
        (("비행기", "✈", "항공", "ticket airplane"), "travel_ticket / flight / ✈️"),
        (("숙소", "호텔", "🏨", "숙박"), "lodging_reservation / hotel / 🏨"),
        (("조직도", "network", "연락처"), "organization_chart / network"),
        (("게시", "누리집", "social media", "게시글"), "web_posting / social media post"),
        (("대피", "비상", "소집", "훈련", "🚨", "탈출"), "evacuation_training / emergency / 🚨"),
        (("방문점검", "현장점검", "점검 실시", "clipboard", "💼"), "site_visit_inspection / clipboard or suitcase"),
        (("브레인스토", "아이디어", "🧠"), "brainstorming / lightbulb or brain"),
        (("커피", "차 픽업", "음료", "coffee"), "beverage_pickup / coffee cup"),
        (("홍보물", "시안", "photo landscape"), "promo_material_review / photo landscape"),
        (("질의", "질문", "speech bubble", "말풍선"), "q_and_a / speech bubbles"),
        (("체크리스트", "준비 사항", "checkmark list"), "event_checklist / checkmark list"),
        (("수신자", "user squares"), "document_recipient / user squares"),
        (("수당", "공문"), "allowance_request / document edit"),
        (("마감", "종료일", "calendar", "표창"), "deadline_status / day calendar"),
        (("실적", "취합", "📊"), "performance_aggregation / chart or document"),
    ]
    for keywords, direction in patterns:
        if any(kw in text for kw in keywords):
            return direction
    return "needs_manual_candidate_design"


def suggest_metadata_direction(row: LabelRow) -> str:
    cid = str(row.raw.get("current_engine_candidate_id", "")).strip()
    title = row.title.lower()
    note = row.note.lower()
    text = f"{title} {note} {cid}"

    if "회의" in text and ("people meeting" in text or "meeting" in cid):
        return "internal_meeting should prefer people meeting over handshake"
    if "간식" in text or "snack" in cid or "food_preparation" in cid:
        return "snack/food candidate should not overmatch fruit snack logistics"
    if "업로드" in text or "folder" in cid:
        return "upload keywords should prefer folder-arrow-up over generic folder"
    if "발송" in text or "송부" in text or "distribution" in cid:
        return "document send/dispatch should prefer document-arrow-right over generic paper"
    if "보도자료" in text:
        return "press release review should prefer newspaper over generic document"
    if "세금계산서" in text or "영수증" in text or "receipt" in text:
        return "tax invoice review should prefer receipt over generic document"
    if "매트리스" in text or "침대" in text:
        return "physical item inspection should prefer bed/mattress visual over document"
    if "영상" in text:
        return "video submission should prefer camera/video over document edit"
    return f"{cid or 'candidate'} metadata should align with final visual preference"


def suggest_boundary_question(row: LabelRow) -> str:
    cause = row.cause_type_manual
    title = row.title
    if cause == "context_vs_action":
        if "오찬" in title or "식사" in title:
            return "회의라는 맥락보다 오찬/식사 장소 선정 행위가 우선되어야 하는가?"
        if "출장" in title:
            return "교육/현장 맥락보다 출장(이동) 행위가 우선되어야 하는가?"
        return f"맥락({title})보다 실제 행동이 workflow/visual 선택을 주도해야 하는가?"
    if cause == "object_vs_channel":
        return "공문/자료라는 대상보다 전화·메일·메신저 전달 채널이 우선되어야 하는가?"
    if cause == "interface_ignored":
        return "수당/여비/접수 확인 등 돈·문서 관련 대상보다 행정 내부 시스템 처리 행위가 우선되어야 하는가?"
    if cause == "action_not_captured":
        if "점검" in title or "방문" in title:
            return "방문점검/현장점검은 room_cleaning과 분리되어야 하는가?"
        if "간식" in title:
            return "간식 구매/전달 행위는 document workflow와 분리되어야 하는가?"
        return f"{title}에서 실제 행동이 현재 workflow보다 우선되어야 하는가?"
    return f"{title}: semantic boundary between context/object and user-preferred visual?"


def suggest_test_case(row: LabelRow) -> str:
    title = row.title
    templates = {
        "context_vs_action": f"{title} → action (meal/travel) beats meeting context",
        "object_vs_channel": f"{title} → channel (phone/email) beats document object",
        "interface_ignored": f"{title} → admin system (💻) beats salary/document object",
        "action_not_captured": f"{title} → field visit/action beats room_cleaning workflow",
    }
    return templates.get(
        row.cause_type_manual,
        f"{title} boundary: {row.raw.get('final_visual', '')} over {row.raw.get('current_engine_workflow', '')}",
    )


@dataclass
class AnalysisResult:
    rows: list[LabelRow]
    overall: dict[str, int]
    distributions: dict[str, dict[str, int]]
    unknown_manual_values: dict[str, list[str]]
    buckets: dict[str, list[LabelRow]] = field(default_factory=dict)
    recommended_fixes: list[dict[str, Any]] = field(default_factory=list)


def analyze(rows: list[LabelRow]) -> AnalysisResult:
    missing_manual = [row for row in rows if not row.manual_fields_filled()]
    active_gap_missing = [
        row for row in rows if row.active_gap and not row.manual_fields_filled()
    ]

    overall = {
        "total_rows": len(rows),
        "active_gap_rows": sum(1 for row in rows if row.active_gap),
        "still_no_candidate_rows": sum(1 for row in rows if row.still_no_candidate),
        "completed_manual_rows": len(rows) - len(missing_manual),
        "missing_manual_rows": len(missing_manual),
        "generalizable_yes_count": sum(1 for row in rows if row.generalizable_manual == "yes"),
        "generalizable_review_count": sum(
            1 for row in rows if row.generalizable_manual == "review"
        ),
        "generalizable_no_count": sum(1 for row in rows if row.generalizable_manual == "no"),
        "active_gap_missing_manual_rows": len(active_gap_missing),
    }

    distributions = {
        "source_type_manual": _counter_dict(
            Counter(row.source_type_manual for row in rows if row.source_type_manual)
        ),
        "cause_type_manual": _counter_dict(
            Counter(row.cause_type_manual for row in rows if row.cause_type_manual)
        ),
        "action_hint_manual": _counter_dict(
            Counter(row.action_hint_manual for row in rows if row.action_hint_manual)
        ),
        "generalizable_manual": _counter_dict(
            Counter(row.generalizable_manual for row in rows if row.generalizable_manual)
        ),
    }

    add_candidate = _sorted_bucket([row for row in rows if _in_bucket(row, "add_candidate")])
    update_metadata = _sorted_bucket(
        [row for row in rows if _in_bucket(row, "update_metadata")]
    )
    adjust_boundary = _sorted_bucket(
        [row for row in rows if _in_bucket(row, "adjust_boundary")]
    )
    defer = _sorted_bucket([row for row in rows if _in_defer_bucket(row)])

    buckets = {
        "add_candidate": add_candidate,
        "update_metadata": update_metadata,
        "adjust_boundary": adjust_boundary,
        "defer": defer,
    }

    return AnalysisResult(
        rows=rows,
        overall=overall,
        distributions=distributions,
        unknown_manual_values=_collect_unknown_values(rows),
        buckets=buckets,
        recommended_fixes=build_recommended_fixes(rows, buckets),
    )


def build_recommended_fixes(
    rows: list[LabelRow],
    buckets: dict[str, list[LabelRow]],
) -> list[dict[str, Any]]:
    fixes: list[dict[str, Any]] = []

    travel_ids = [
        row.id
        for row in buckets["add_candidate"]
        if row.generalizable_manual == "yes"
        and any(
            kw in f"{row.title} {row.note}".lower()
            for kw in ("기차", "ktx", "비행기", "숙소", "예매", "항공", "호텔", "열차")
        )
    ]
    if travel_ids:
        fixes.append(
            {
                "title": "Travel reservation candidates 추가 (🚄, ✈️, 🏨)",
                "ids": travel_ids,
                "action_type": "add_candidate",
                "expected_effect": "출장·교통·숙박 예매 업무에서 still_no_candidate 및 visual mismatch 해소",
                "regression_risk": "low",
                "tests": "기차표/KTX/비행기/숙소 예매 boundary test + ranking snapshot",
            }
        )

    emergency_ids = [
        row.id
        for row in buckets["add_candidate"]
        if row.generalizable_manual == "yes"
        and any(kw in f"{row.title} {row.note}" for kw in ("대피", "비상", "소집"))
    ]
    if emergency_ids:
        fixes.append(
            {
                "title": "Emergency drill / evacuation candidate 추가 (🚨, person running)",
                "ids": emergency_ids,
                "action_type": "add_candidate",
                "expected_effect": "비상훈련·대피 업무가 room_cleaning/training_session과 분리",
                "regression_risk": "low-medium",
                "tests": "민방위/비상소집 boundary test",
            }
        )

    org_ids = [
        row.id
        for row in buckets["add_candidate"]
        if "조직도" in row.title or "network" in row.raw.get("final_visual", "").lower()
    ]
    if org_ids:
        fixes.append(
            {
                "title": "Organization chart / network candidate 추가",
                "ids": org_ids,
                "action_type": "add_candidate",
                "expected_effect": "조직도·연락처 정비 업무에서 phone_call 오매칭 방지",
                "regression_risk": "low",
                "tests": "조직도/연락처 정비 title ranking test",
            }
        )

    web_ids = [
        row.id
        for row in buckets["add_candidate"]
        if any(kw in row.title for kw in ("게시", "누리집", "새소식"))
    ]
    if web_ids:
        fixes.append(
            {
                "title": "Web posting / social media post candidate 추가",
                "ids": web_ids,
                "action_type": "add_candidate",
                "expected_effect": "온라인 게시 예약 업무 visual recall 개선",
                "regression_risk": "low",
                "tests": "게시글 예약 title test",
            }
        )

    boundary_channel = [
        row
        for row in buckets["adjust_boundary"]
        if row.generalizable_manual == "yes"
        and row.cause_type_manual == "object_vs_channel"
    ][:2]
    if boundary_channel:
        fixes.append(
            {
                "title": "Document vs communication channel boundary 조정",
                "ids": [row.id for row in boundary_channel],
                "action_type": "adjust_boundary",
                "expected_effect": "공문/자료 전달·요청 업무에서 채널(📧📞💬) 우선",
                "regression_risk": "medium-high",
                "tests": "semantic boundary workflow + document→channel regression suite",
            }
        )

    boundary_system = [
        row
        for row in buckets["adjust_boundary"]
        if row.generalizable_manual == "yes"
        and row.cause_type_manual == "interface_ignored"
    ][:1]
    if boundary_system:
        fixes.append(
            {
                "title": "Admin system (💻) vs salary/document object boundary 조정",
                "ids": [row.id for row in boundary_system],
                "action_type": "adjust_boundary",
                "expected_effect": "행정 시스템 등록·지급 업무에서 💻 우선",
                "regression_risk": "medium",
                "tests": "여비등록/수당지급/정보공개 boundary test",
            }
        )

    metadata_yes = [
        row for row in buckets["update_metadata"] if row.generalizable_manual == "yes"
    ][:2]
    for row in metadata_yes:
        fixes.append(
            {
                "title": f"Metadata: {suggest_metadata_direction(row)}",
                "ids": [row.id],
                "action_type": "update_metadata",
                "expected_effect": f"{row.title}에서 final visual 선호 반영",
                "regression_risk": "low",
                "tests": f"metadata snapshot for id={row.id}",
            }
        )

    site_visit = [
        row
        for row in buckets["add_candidate"]
        if "점검" in row.title and row.generalizable_manual == "yes"
    ]
    if site_visit and len(fixes) < 5:
        fixes.append(
            {
                "title": "Site visit / field inspection candidate 추가 (💼, 📋)",
                "ids": [row.id for row in site_visit],
                "action_type": "add_candidate",
                "expected_effect": "현장점검·방문점검이 room_cleaning과 분리",
                "regression_risk": "low-medium",
                "tests": "센터 방문점검 boundary + candidate test",
            }
        )

    row_by_id = {row.id: row for row in rows}
    yes_first = sorted(
        fixes,
        key=lambda fix: (
            0
            if any(row_by_id.get(i, LabelRow({})).generalizable_manual == "yes" for i in fix["ids"])
            else 1,
            0 if fix["action_type"] == "add_candidate" else 1,
            0 if fix["regression_risk"].startswith("low") else 1,
        ),
    )

    boundary_count = 0
    selected: list[dict[str, Any]] = []
    for fix in yes_first:
        if fix["action_type"] == "adjust_boundary":
            if boundary_count >= 2:
                continue
            boundary_count += 1
        selected.append(fix)
        if len(selected) >= 5:
            break
    return selected[:5] if len(selected) >= 3 else selected


def analyze_to_json(result: AnalysisResult) -> dict[str, Any]:
    def row_payload(row: LabelRow) -> dict[str, Any]:
        return {
            "id": row.id,
            "title": row.title,
            "priority_score": row.priority_score(),
            "priority_label": row.priority_label(),
            "source_type_manual": row.source_type_manual,
            "cause_type_manual": row.cause_type_manual,
            "action_hint_manual": row.action_hint_manual,
            "generalizable_manual": row.generalizable_manual,
            "active_gap": row.active_gap,
            "still_no_candidate": row.still_no_candidate,
        }

    return {
        "overall": result.overall,
        "distributions": result.distributions,
        "unknown_manual_values": result.unknown_manual_values,
        "action_buckets": {
            name: [row_payload(row) for row in rows]
            for name, rows in result.buckets.items()
        },
        "recommended_fixes": result.recommended_fixes,
    }


def _distribution_table(distribution: dict[str, int]) -> list[str]:
    lines = ["| value | count |", "| --- | ---: |"]
    if not distribution:
        lines.append("| (none) | 0 |")
    else:
        for value, count in distribution.items():
            lines.append(f"| {value} | {count} |")
    return lines


def _bucket_summary_table(buckets: dict[str, list[LabelRow]]) -> list[str]:
    lines = ["| bucket | count |", "| --- | ---: |"]
    for name, rows in buckets.items():
        lines.append(f"| {name} | {len(rows)} |")
    return lines


def _top_targets_table(rows: list[LabelRow], extra_col: str, extra_fn) -> list[str]:
    if not rows:
        return ["- (none)"]
    header = (
        f"| priority | score | id | title | {extra_col} | generalizable |"
    )
    sep = "| --- | ---: | --- | --- | --- | --- |"
    lines = [header, sep]
    for row in rows[:10]:
        lines.append(
            f"| {row.priority_label()} | {row.priority_score()} | {row.id} | "
            f"{_md_cell(row.title)} | {_md_cell(extra_fn(row))} | {row.generalizable_manual} |"
        )
    return lines


def format_summary_markdown(result: AnalysisResult) -> str:
    overall = result.overall
    lines: list[str] = [
        "# P5-B Manual Labeling Summary",
        "",
        "> Aggregated from manual labels in `reports/p5b_active_gap_labeling.csv`. "
        "Analysis-only — does not modify catalog or engine.",
        "",
        "## 1. Overall",
        "",
        f"- total_rows: {overall['total_rows']}",
        f"- active_gap_rows: {overall['active_gap_rows']}",
        f"- still_no_candidate_rows: {overall['still_no_candidate_rows']}",
        f"- completed_manual_rows: {overall['completed_manual_rows']}",
        f"- missing_manual_rows: {overall['missing_manual_rows']}",
        f"- active_gap with missing manual: {overall['active_gap_missing_manual_rows']}",
        f"- generalizable_yes: {overall['generalizable_yes_count']}",
        f"- generalizable_review: {overall['generalizable_review_count']}",
        f"- generalizable_no: {overall['generalizable_no_count']}",
        "",
    ]

    if result.unknown_manual_values:
        lines.extend(["### unknown_manual_values", ""])
        for col, values in result.unknown_manual_values.items():
            lines.append(f"- `{col}`: {', '.join(f'`{v}`' for v in values)}")
        lines.append("")

    lines.extend(["## 2. Manual Label Distribution", ""])
    for col in (
        "source_type_manual",
        "cause_type_manual",
        "action_hint_manual",
        "generalizable_manual",
    ):
        lines.extend([f"### {col}", ""])
        lines.extend(_distribution_table(result.distributions[col]))
        lines.append("")

    lines.extend(["## 3. Action Bucket Summary", ""])
    lines.extend(_bucket_summary_table(result.buckets))
    lines.append("")

    lines.extend(["## 4. Top Add Candidate Targets", ""])
    lines.extend(
        _top_targets_table(
            result.buckets["add_candidate"],
            "suggested_direction",
            suggest_candidate_direction,
        )
    )
    lines.append("")

    lines.extend(["## 5. Top Metadata Update Targets", ""])
    lines.extend(
        _top_targets_table(
            result.buckets["update_metadata"],
            "suggested_direction",
            suggest_metadata_direction,
        )
    )
    lines.append("")

    lines.extend(["## 6. Top Boundary Adjustment Targets", ""])
    lines.extend(
        _top_targets_table(
            result.buckets["adjust_boundary"],
            "boundary_question",
            suggest_boundary_question,
        )
    )
    lines.append("")

    lines.extend(["## 7. Deferred / Preference-only Cases", ""])
    defer = result.buckets["defer"]
    if defer:
        lines.extend(
            [
                "| id | title | action_hint | generalizable | source_type |",
                "| --- | --- | --- | --- | --- |",
            ]
        )
        for row in defer:
            lines.append(
                f"| {row.id} | {_md_cell(row.title)} | {row.action_hint_manual} | "
                f"{row.generalizable_manual} | {row.source_type_manual} |"
            )
    else:
        lines.append("- (none)")
    lines.append("")

    lines.extend(["## 8. Recommended Next 3~5 Fixes", ""])
    for index, fix in enumerate(result.recommended_fixes, start=1):
        lines.append(f"### {index}. {fix['title']}")
        lines.append(f"- 관련 사례 id: {', '.join(fix['ids'])}")
        lines.append(f"- 수정 유형: {fix['action_type']}")
        lines.append(f"- 기대 효과: {fix['expected_effect']}")
        lines.append(f"- regression 위험: {fix['regression_risk']}")
        lines.append(f"- 필요한 테스트: {fix['tests']}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def export_candidate_backlog(result: AnalysisResult) -> str:
    lines = [
        "# P5-B Candidate Backlog",
        "",
        "> `action_hint_manual=add_candidate` and `generalizable_manual in (yes, review)`",
        "",
        "| priority | score | id | title | final_visual | engine_visual | source | cause | note | suggested_direction |",
        "| --- | ---: | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in result.buckets["add_candidate"]:
        lines.append(
            "| {priority} | {score} | {id} | {title} | {final} | {engine} | {src} | {cause} | {note} | {direction} |".format(
                priority=row.priority_label(),
                score=row.priority_score(),
                id=row.id,
                title=_md_cell(row.title),
                final=_md_cell(str(row.raw.get("final_visual", ""))),
                engine=_md_cell(str(row.raw.get("current_engine_visual", ""))),
                src=row.source_type_manual,
                cause=row.cause_type_manual,
                note=_md_cell(row.note),
                direction=_md_cell(suggest_candidate_direction(row)),
            )
        )
    if not result.buckets["add_candidate"]:
        lines.append("| — | — | — | (none) | | | | | | |")
    return "\n".join(lines).rstrip() + "\n"


def export_metadata_backlog(result: AnalysisResult) -> str:
    lines = [
        "# P5-B Metadata Backlog",
        "",
        "> `action_hint_manual=update_metadata` and `generalizable_manual in (yes, review)`",
        "",
        "| priority | score | id | title | recommended | final | candidate_id | workflow | source | cause | note | suggested_direction |",
        "| --- | ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in result.buckets["update_metadata"]:
        lines.append(
            "| {priority} | {score} | {id} | {title} | {rec} | {final} | {cid} | {wf} | {src} | {cause} | {note} | {direction} |".format(
                priority=row.priority_label(),
                score=row.priority_score(),
                id=row.id,
                title=_md_cell(row.title),
                rec=_md_cell(str(row.raw.get("recommended_visual", ""))),
                final=_md_cell(str(row.raw.get("final_visual", ""))),
                cid=_md_cell(str(row.raw.get("current_engine_candidate_id", ""))),
                wf=_md_cell(str(row.raw.get("current_engine_workflow", ""))),
                src=row.source_type_manual,
                cause=row.cause_type_manual,
                note=_md_cell(row.note),
                direction=_md_cell(suggest_metadata_direction(row)),
            )
        )
    if not result.buckets["update_metadata"]:
        lines.append("| — | — | — | (none) | | | | | | | | |")
    return "\n".join(lines).rstrip() + "\n"


def export_boundary_backlog(result: AnalysisResult) -> str:
    lines = [
        "# P5-B Boundary Backlog",
        "",
        "> `action_hint_manual=adjust_boundary` and `generalizable_manual in (yes, review)`",
        "",
        "| priority | score | id | title | recommended | final | workflow | source | cause | note | boundary_question | suggested_test_case |",
        "| --- | ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in result.buckets["adjust_boundary"]:
        lines.append(
            "| {priority} | {score} | {id} | {title} | {rec} | {final} | {wf} | {src} | {cause} | {note} | {question} | {test} |".format(
                priority=row.priority_label(),
                score=row.priority_score(),
                id=row.id,
                title=_md_cell(row.title),
                rec=_md_cell(str(row.raw.get("recommended_visual", ""))),
                final=_md_cell(str(row.raw.get("final_visual", ""))),
                wf=_md_cell(str(row.raw.get("current_engine_workflow", ""))),
                src=row.source_type_manual,
                cause=row.cause_type_manual,
                note=_md_cell(row.note),
                question=_md_cell(suggest_boundary_question(row)),
                test=_md_cell(suggest_test_case(row)),
            )
        )
    if not result.buckets["adjust_boundary"]:
        lines.append("| — | — | — | (none) | | | | | | | | |")
    return "\n".join(lines).rstrip() + "\n"


def _configure_stdout() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")


def main() -> None:
    _configure_stdout()
    parser = argparse.ArgumentParser(
        description="Aggregate P5-B manual labeling CSV into priority backlogs."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"Manual labeling CSV (default: {DEFAULT_INPUT})",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON summary to stdout")
    parser.add_argument(
        "--export-md",
        type=Path,
        metavar="PATH",
        help="Write full summary markdown (e.g. reports/p5b_manual_labeling_summary.md)",
    )
    parser.add_argument(
        "--export-candidates-md",
        type=Path,
        metavar="PATH",
        help="Write candidate backlog markdown",
    )
    parser.add_argument(
        "--export-metadata-md",
        type=Path,
        metavar="PATH",
        help="Write metadata backlog markdown",
    )
    parser.add_argument(
        "--export-boundary-md",
        type=Path,
        metavar="PATH",
        help="Write boundary backlog markdown",
    )
    args = parser.parse_args()

    rows = load_labeling_csv(args.input)
    result = analyze(rows)

    if args.export_md:
        args.export_md.parent.mkdir(parents=True, exist_ok=True)
        args.export_md.write_text(format_summary_markdown(result), encoding="utf-8")
    if args.export_candidates_md:
        args.export_candidates_md.parent.mkdir(parents=True, exist_ok=True)
        args.export_candidates_md.write_text(export_candidate_backlog(result), encoding="utf-8")
    if args.export_metadata_md:
        args.export_metadata_md.parent.mkdir(parents=True, exist_ok=True)
        args.export_metadata_md.write_text(export_metadata_backlog(result), encoding="utf-8")
    if args.export_boundary_md:
        args.export_boundary_md.parent.mkdir(parents=True, exist_ok=True)
        args.export_boundary_md.write_text(export_boundary_backlog(result), encoding="utf-8")

    if args.json:
        print(json.dumps(analyze_to_json(result), ensure_ascii=False, indent=2))
    elif not any(
        [args.export_md, args.export_candidates_md, args.export_metadata_md, args.export_boundary_md]
    ):
        print(format_summary_markdown(result), end="")


if __name__ == "__main__":
    main()
