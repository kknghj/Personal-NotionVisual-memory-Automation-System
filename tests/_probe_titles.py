"""Temporary probe script — delete after capturing outputs."""
from __future__ import annotations

import sys

from app.data_loader import load_visual_candidates
from app.recommender import find_best_visual_candidate_match

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

c = load_visual_candidates()
titles = [
    "점심 메일 확인",
    "저녁 카톡 확인",
    "긴급 전화 문의",
    "과장님 전화 문의",
    "대표 메일 전달",
    "팀장 카톡 확인",
    "엑셀 자료 정리",
    "네이버폼 신청서 수정",
    "터미널 환경 설정 정리",
    "교육 신청 현황 엑셀 정리",
    "행사 자료 준비",
    "행사 엑셀 정리",
    "과장님 점심 카톡 일정 확인",
    "대표 행사 자료 준비",
    "긴급 회의자료 메일 전달",
    "일정 확인",
]
for t in titles:
    out = find_best_visual_candidate_match(t, c)
    if out:
        data, cid, matched, wp, spec, dom = out
        v = (data.get("visual") or {}).get("value", "")
        print(f"{t!r} -> {cid} emoji={v!r} matched={matched!r} wp={wp} spec={spec} dom={dom}")
    else:
        print(f"{t!r} -> None")
