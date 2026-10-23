"""Build a local three-arm inspection page; no upload, model call or user profile."""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / '.local/luna-v2'
ARMS = (('plain', '普通提示'), ('checklist', '完整清单'), ('ownvoice', 'OwnVoice'))


def escape(value):
    if not isinstance(value, str):
        value = json.dumps(value, ensure_ascii=False, indent=2)
    return html.escape(value)


def main():
    tasks = json.loads((ROOT / 'evals/luna_v2/cases.json').read_text())
    sections = []
    for phase in ('development', 'holdout'):
        for task in tasks[phase]:
            cards = []
            for arm, name in ARMS:
                identifier = f'luna-v2-{phase}-{task["id"]}-{arm}-' + ('revision' if task['domain'] == 'code' else 'initial')
                folder = LOCAL / 'runs' / identifier
                text = (folder / 'artifact.txt').read_text() if (folder / 'artifact.txt').exists() else '未完成'
                try:
                    output = json.loads(text)
                except ValueError:
                    output = None
                score_path = LOCAL / 'assessments' / (identifier + '.json')
                score = json.loads(score_path.read_text()) if score_path.exists() else {}
                if output and task['domain'] == 'code':
                    body = ''.join(f'<h4>{escape(filename)}</h4><pre>{escape(source)}</pre>' for filename, source in output.get('files', {}).items())
                else:
                    body = f'<pre>{escape((output or {}).get("artifact", (output or {}).get("draft", text)))}</pre>'
                cards.append(f'<article><h3>{name}</h3>{body}<details><summary>完整输出与原始探针</summary><pre>{escape(text)}</pre><pre>{escape(score)}</pre></details></article>')
            material = {key: value for key, value in task.items() if key not in {'oracle', 'source_map_oracle', 'tests', 'leakage_canaries', 'synthetic', 'public'}}
            sections.append(f'<section><h2>{phase} · {escape(task["id"])}</h2><details><summary>任务与风格样例</summary><pre>{escape(material)}</pre></details><div class="columns">{"".join(cards)}</div></section>')
    page = '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>OwnVoice Luna 三组对照</title><style>body{font:16px/1.6 system-ui;margin:24px;color:#172238;background:#f5f7fb}h1{font-size:24px}section{margin:32px 0}.columns{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}article{background:white;border:1px solid #ccd4df;border-radius:8px;padding:16px}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:13px/1.6 ui-monospace,monospace}summary{cursor:pointer}h3{margin-top:0}@media(max-width:1000px){.columns{grid-template-columns:1fr}}</style><h1>Luna 复杂任务：三组输出对照</h1><p>本地只读页面，无上传。开发与留出任务分开；OwnVoice 留出使用 0.1.2。文字严格探针包含已确认的格式约定问题，不能当作语义正确率。请同时核对任务、正文和结构化字段。</p>' + ''.join(sections) + '</html>'
    destination = LOCAL / 'compare.html'
    destination.write_text(page)
    print(destination)


if __name__ == '__main__':
    main()
