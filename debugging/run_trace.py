r"""Execute percent cells, preserving actual outputs in a notebook and local HTML report.

Run from project root: .\.venv\Scripts\python.exe -B debugging/run_trace.py
Only creates a new timestamped trace directory; production code/artifacts are read-only.
"""
from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime, timezone
from html import escape
from hashlib import sha256
from io import StringIO
from pathlib import Path
import inspect
import json
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = Path(__file__).with_name('trace_student_29485_20251.py')
OUT = ROOT / 'data/evaluation/recommendation_trace_pilot' / (
    'trace_29485_20251_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    protected = [*ROOT.joinpath('src').rglob('*.py'), *ROOT.joinpath('models').rglob('*.txt'),
                 *ROOT.joinpath('models').rglob('*.json'), *ROOT.joinpath('data/artifacts').glob('*')]
    before = {str(p): sha256(p.read_bytes()).hexdigest() for p in protected if p.is_file()}
    blocks = []
    for block in SCRIPT.read_text(encoding='utf-8').split('# %% ')[1:]:
        title, code = block.split('\n', 1)
        blocks.append((title.strip(), code.rstrip() + '\n'))
    notebook = {'cells': [], 'metadata': {'kernelspec': {'display_name': 'Academic Advisor .venv',
        'language': 'python', 'name': 'python3'}, 'language_info': {'name': 'python', 'version': sys.version.split()[0]}},
        'nbformat': 4, 'nbformat_minor': 5}
    namespace = {'__name__': '__main__', '_capture_trace': True, 'TRACE_OUTPUT': str(OUT)}
    panels = []
    failed = False
    for number, (title, code) in enumerate(blocks, 1):
        print(f'[{number}/{len(blocks)}] {title}', flush=True)
        notebook['cells'].append({'cell_type': 'markdown', 'id': f'title-{number}', 'metadata': {}, 'source': f'## {title}\n'})
        output = StringIO()
        namespace['_trace_displays'] = []
        error = None
        try:
            with redirect_stdout(output), redirect_stderr(output):
                exec(compile(code, str(SCRIPT) + f':cell-{number}', 'exec'), namespace)
        except Exception:
            error = traceback.format_exc()
            failed = True
        outputs = []
        printed = output.getvalue()
        if printed:
            outputs.append({'output_type': 'stream', 'name': 'stdout', 'text': printed})
        for table in namespace['_trace_displays']:
            outputs.append({'output_type': 'display_data', 'metadata': {}, 'data': {'text/html': table}})
        if error:
            outputs.append({'output_type': 'stream', 'name': 'stderr', 'text': error})
        notebook['cells'].append({'cell_type': 'code', 'id': f'code-{number}', 'metadata': {},
                                 'source': code, 'execution_count': number, 'outputs': outputs})
        tables = ''.join('<div class="table-wrap">' + t + '</div>' for t in namespace['_trace_displays'])
        function_names = {2: ['build_student_snapshot', 'add_student_history_features'],
            3: ['normalize_candidates', 'AcademicPlanRecommender.prepare_candidates'],
            4: ['enumerate_plan_indices', 'build_plan_rows'], 5: ['AcademicPlanRecommender.recommend'],
            6: ['AcademicPlanRecommender.score_rows', 'compute_plan_context_features'],
            7: ['load_local_inputs'], 9: ['summarize_scored_plans', 'rank_plans']}.get(number, [])
        production = []
        for idx, name in enumerate(function_names):
            obj = namespace[name.split('.')[0]]
            for attr in name.split('.')[1:]:
                obj = getattr(obj, attr)
            source_lines, start = inspect.getsourcelines(obj)
            path = str(Path(inspect.getfile(obj)).resolve())
            numbered = '\n'.join(f'{start+i:>3} {line.rstrip()}' for i, line in enumerate(source_lines))
            production.append(f'<details {"open" if idx == 0 else ""}><summary>{escape(name)}</summary>'
                f'<small dir="ltr">{escape(path)}:{start}</small><pre class="code"><code>{escape(numbered)}</code></pre></details>')
        executed = f'<details {"" if production else "open"}><summary>استدعاءات التتبّع والفحوص المنفّذة</summary><pre class="code"><code>{escape(code)}</code></pre></details>'
        panels.append(f'<section id="step-{number}" class="step" {"" if number == 1 else "hidden"}>'
            f'<h2>{escape(title)}</h2><div class="layout"><div><h3>الكود الذي نُفّذ</h3>'
            f'{"".join(production)}{executed}</div><div><h3>البيانات الناتجة</h3>'
            f'<pre class="output">{escape(printed)}</pre>{tables}'
            f'{("<pre class=error>" + escape(error) + "</pre>") if error else ""}</div></div></section>')
        if error:
            print(error)
            break
    scope = {'protected_file_count': len(before), 'unchanged': all(sha256(Path(p).read_bytes()).hexdigest() == h for p, h in before.items()),
             'sha256_before': before}
    (OUT / '10_production_scope_check.json').write_text(json.dumps(scope, indent=2), encoding='utf-8')
    if not scope['unchanged']:
        raise RuntimeError('Protected source or model files changed during this trace.')
    notebook_path = OUT / 'student_29485_20251.ipynb'
    notebook_path.write_text(json.dumps(notebook, ensure_ascii=False, indent=1), encoding='utf-8')
    nav = ''.join(f'<button type="button" data-step="{i}" aria-pressed="{str(i == 1).lower()}">{escape(t)}</button>'
                  for i, (t, _) in enumerate(blocks[:len(panels)], 1))
    html = '''<!doctype html><html lang="ar" dir="rtl"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>تتبّع الطالب 29485.111 — 20251</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#f7f8fb;color:#172335;font:16px/1.7 system-ui,Segoe UI,sans-serif}
header,main,nav,footer{max-width:1800px;margin:auto;padding:20px 28px}header{padding-bottom:4px}
h1{font-size:26px;margin:4px 0}h2{font-size:22px}h3{font-size:17px;color:#3b536c}
nav{display:flex;flex-wrap:wrap;gap:8px;padding-top:8px}button{font:inherit;padding:8px 12px;border:1px solid #c0cddd;border-radius:6px;background:#fff;color:#243d58;cursor:pointer}
button[aria-pressed=true]{background:#20466b;color:#fff}button:focus-visible,a:focus-visible{outline:3px solid #d3801b;outline-offset:3px}
.layout{display:grid;grid-template-columns:minmax(330px,.85fr) minmax(440px,1.35fr);gap:24px;align-items:start}
.layout>div{min-width:0}pre{margin:0 0 16px;padding:16px;border:1px solid #dce3eb;background:#fff;border-radius:6px;white-space:pre-wrap;overflow-wrap:anywhere}
details{margin-bottom:16px}summary{cursor:pointer;color:#20466b;padding:8px 0;overflow-wrap:anywhere}details small{display:block;overflow-wrap:anywhere}
.code{direction:ltr;text-align:left;font:13px/1.6 Consolas,monospace}.output{font:14px/1.9 system-ui;unicode-bidi:plaintext}
.table-wrap{overflow-x:auto;margin-bottom:20px;background:#fff;border:1px solid #dce3eb;border-radius:6px}
table{border-collapse:collapse;width:100%;font-size:13px;direction:ltr;text-align:left}th,td{padding:9px;border-bottom:1px solid #e1e7ef;vertical-align:top;white-space:nowrap}th{background:#eaf0f6;font-weight:600}
td{unicode-bidi:plaintext}tr:last-child td{border-bottom:0}a{color:#14588e}.error{color:#a01818}footer{color:#405269}small{color:#52657a}
@media(max-width:1000px){.layout{grid-template-columns:1fr}header,main,nav,footer{padding:14px}h1{font-size:22px}.code{font-size:12px}}
@media print{nav{display:none}.step[hidden]{display:block}.layout{display:block}.code{font-size:10px}.table-wrap{overflow:visible}table{font-size:9px}td,th{white-space:normal}}
</style><header><small>Academic Advisor · تتبّع تنفيذ فعلي</small><h1>الطالب 29485.111 · طب الأسنان · الفصل 20251</h1>
<p>15 مادة متاحة حسب الطلب · 12–18 ساعة · تاريخ المودل المجمد حتى 20243</p>
<p><strong>حالة التتبع: تشخيص للكود والبيانات.</strong> تشغيل procedure على 20251 مؤكد من المستخدم؛
صلاحية القائمة كأهلية تاريخية لبداية الفصل لم تُثبت. تفصيل اختلاف القائمة في المرحلة 8.</p>
<p>اتبع المراحل بالترتيب: الطلب ← حالة الطالب ← التاريخ ← الخطط ← التنبؤ ← التسجيل الفعلي ← التوصيات.
المقارنة بالتسجيل الفعلي تظهر في المرحلة 8 والتوصيات في المرحلة 9.</p>
<a href="student_29485_20251.ipynb">دفتر التنفيذ مع الكود والمخرجات</a></header><nav aria-label="مراحل التتبع">'''
    html += nav + '</nav><main aria-live="polite">' + ''.join(panels) + '''</main>
<footer>يمكن إعادة تشغيل دفتر التنفيذ باستخدام بيئة المشروع .venv. القيم المعروضة مأخوذة من التنفيذ، وليست أمثلة مصطنعة.</footer>
<script>
document.querySelectorAll('button[data-step]').forEach(button=>button.addEventListener('click',()=>{
document.querySelectorAll('.step').forEach(panel=>panel.hidden=panel.id!=='step-'+button.dataset.step);
document.querySelectorAll('button[data-step]').forEach(item=>item.setAttribute('aria-pressed',String(item===button)));
}));</script></html>'''
    (OUT / 'trace.html').write_text(html, encoding='utf-8')
    print('TRACE_OUTPUT=' + str(OUT), flush=True)
    return 1 if failed else 0


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    raise SystemExit(main())
