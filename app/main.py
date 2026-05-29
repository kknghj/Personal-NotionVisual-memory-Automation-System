from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from app.data_loader import load_sample_cases, load_visual_candidates
from app.models import RecommendRequest, RecommendResponse, Visual
from app.recommendation_logging import log_recommendation_execution
from app.recommender import find_best_visual_candidate_match, find_exact_title_match

app = FastAPI(title="Notion Icon Automation", version="0.1.0")

_sample_cases: list | None = None
_visual_candidates: dict | None = None


def get_sample_cases() -> list:
    global _sample_cases
    if _sample_cases is None:
        _sample_cases = load_sample_cases()
    return _sample_cases


def get_visual_candidates() -> dict:
    global _visual_candidates
    if _visual_candidates is None:
        _visual_candidates = load_visual_candidates()
    return _visual_candidates


_INDEX_HTML = """<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>아이콘 추천</title>
  <style>
    :root { font-family: system-ui, sans-serif; }
    body { max-width: 36rem; margin: 2rem auto; padding: 0 1rem; }
    label { display: block; margin-bottom: .35rem; font-weight: 600; }
    input[type="text"] { width: 100%; box-sizing: border-box; padding: .5rem .65rem; font-size: 1rem; }
    button { margin-top: .75rem; padding: .5rem 1rem; font-size: 1rem; cursor: pointer; }
    pre { background: #f4f4f5; padding: 1rem; overflow: auto; border-radius: 6px; margin-top: 1.25rem; }
    #summary { margin-top: 1.25rem; padding: 1rem; background: #ecfdf5; border-radius: 6px; border: 1px solid #a7f3d0; display: none; }
    #summary p { margin: 0; }
    #summary .reason { margin-top: .5rem; line-height: 1.45; }
    .hint { color: #71717a; font-size: .875rem; margin-top: 1.25rem; }
    .err { color: #b91c1c; }
  </style>
</head>
<body>
  <h1>노션 일정 제목 → visual 추천</h1>
  <p>
    ① <code>data/sample_cases.json</code> 제목 <strong>완전 일치</strong> 시 해당 visual·reason 사용.<br/>
    ② 없으면 <code>data/visual_candidates.json</code>의 <strong>meaning</strong> 키워드가 제목에 포함되는지 본 뒤,
    키워드 <strong>workflow_priority</strong> → <strong>interface dominance</strong> → <strong>workflow_resolution</strong> →
    제목에서의 위치 → 키워드 길이 순으로 후보를 고릅니다
    (점심·저녁 같은 시간 modifier, 과장님·대표·팀장 같은 person modifier가
    카톡·메일·전화 등 채널 anchor보다 앞서지 않도록 함).<br/>
    급여·수당·여비 등 <strong>subject</strong>만 있고 문서 workflow(공문·작성·검토 등)가 없을 때만 💰 후보가 경쟁합니다.<br/>
    <strong>교육청·교육신청서·보고서·회의자료·신청서·협의회</strong> 등 <strong>subject compound</strong> 안의 글자는
    「교육」「보고」「회의」「신청」만으로는 매칭·interface dominance에 쓰이지 않고,
    <strong>작성·수정·검토·확인·제출</strong> 등 실제 행동을 우선합니다.
  </p>
  <form id="f">
    <label for="title">일정 제목</label>
    <input id="title" name="title" type="text" placeholder="예: 출장 여비 입력" autocomplete="off" required/>
    <button type="submit">추천 요청</button>
  </form>
  <div id="summary" aria-live="polite"></div>
  <p style="margin-top:1.25rem;font-size:.875rem;color:#52525b"><strong>전체 JSON</strong></p>
  <pre id="out">응답이 여기에 표시됩니다.</pre>
  <p class="hint">API 문서: <a href="/docs">/docs</a></p>
  <script>
    const form = document.getElementById('f');
    const out = document.getElementById('out');
    const summary = document.getElementById('summary');

    function fillSummary(data) {
      summary.style.display = 'block';
      summary.replaceChildren();
      const v = data.visual || {};
      if (v.type === 'emoji') {
        const em = document.createElement('p');
        em.style.fontSize = '2rem';
        em.style.margin = '0 0 .35rem 0';
        em.textContent = v.value || '';
        summary.appendChild(em);
      } else {
        const p = document.createElement('p');
        p.appendChild(document.createTextNode('Notion icon '));
        const code = document.createElement('code');
        code.textContent = v.value || '';
        p.appendChild(code);
        if (v.color) {
          p.appendChild(document.createTextNode(' · 색상 '));
          const c = document.createElement('code');
          c.textContent = v.color;
          p.appendChild(c);
        }
        summary.appendChild(p);
      }
      const why = document.createElement('p');
      why.className = 'reason';
      const strong = document.createElement('strong');
      strong.textContent = '추천 이유: ';
      why.appendChild(strong);
      why.appendChild(document.createTextNode(data.reason || ''));
      summary.appendChild(why);
    }

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const title = document.getElementById('title').value;
      out.textContent = '요청 중…';
      out.className = '';
      summary.style.display = 'none';
      summary.replaceChildren();
      try {
        const res = await fetch('/recommend-icon', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ title })
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
          out.className = 'err';
          out.textContent = res.status + ' ' + res.statusText + '\\n' + JSON.stringify(data, null, 2);
          return;
        }
        fillSummary(data);
        out.textContent = JSON.stringify(data, null, 2);
      } catch (err) {
        out.className = 'err';
        out.textContent = String(err);
      }
    });
  </script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return _INDEX_HTML


@app.post("/recommend-icon", response_model=RecommendResponse)
def recommend_icon(body: RecommendRequest) -> RecommendResponse:
    case = find_exact_title_match(body.title, get_sample_cases())
    if case is not None:
        visual = case.get("visual")
        if not visual or not isinstance(visual, dict):
            raise HTTPException(
                status_code=500,
                detail="일치하는 케이스에 visual 필드가 없습니다.",
            )
        raw_reason = case.get("reason")
        reason = (
            raw_reason.strip()
            if isinstance(raw_reason, str) and raw_reason.strip()
            else "data/sample_cases.json의 제목과 정확히 일치하는 사례의 visual을 사용합니다."
        )
        wfs = case.get("workflow_resolution")
        if isinstance(wfs, int):
            reason = f"{reason} (기록된 workflow_resolution={wfs})"
        response = RecommendResponse(visual=Visual(**visual), reason=reason)
        log_recommendation_execution(body.title, case=case)
        return response

    visual_candidates = get_visual_candidates()
    cand = find_best_visual_candidate_match(body.title, visual_candidates)
    if cand is None:
        log_recommendation_execution(body.title, candidates=visual_candidates)
        raise HTTPException(
            status_code=404,
            detail="data/sample_cases 및 data/visual_candidates meaning 키워드와 일치하는 항목이 없습니다.",
        )

    data, cid, matched, wp, kres, idom = cand
    visual = data.get("visual")
    if not visual or not isinstance(visual, dict):
        raise HTTPException(
            status_code=500,
            detail="선택된 data/visual_candidates 항목에 visual 필드가 없습니다.",
        )
    reason = (
        "data/sample_cases에 같은 제목이 없어 data/visual_candidates로 매칭했습니다. "
        f"제목에 meaning「{matched}」가 포함되어 후보「{cid}」를 선택했습니다 "
        f"(정렬: interface_dominance={idom}, keyword_workflow_resolution={kres}, workflow_priority={wp})."
    )
    response = RecommendResponse(visual=Visual(**visual), reason=reason)
    log_recommendation_execution(
        body.title,
        catalog_match=cand,
        candidates=visual_candidates,
    )
    return response
