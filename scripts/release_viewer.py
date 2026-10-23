"""Local artifact comparison for the frozen 0.2 evaluation; never uploads data."""
import html
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
LOCAL=ROOT/'.local/release-v02'


def esc(value):return html.escape(value if isinstance(value,str) else json.dumps(value,ensure_ascii=False,indent=2))


def main():
    tasks=json.loads((ROOT/'evals/release_v02/cases.json').read_text());sections=[]
    for phase,cases in tasks.items():
        for task in cases:
            for style in ((0,) if phase=='development' else (0,1)):
                columns=[]
                for arm,title in (('plain','普通提示'),('checklist','完整清单'),('ownvoice','OwnVoice')):
                    name=f'ownvoice-v02-{phase}-{task["id"]}-s{style}-{arm}-revision'
                    folder=LOCAL/'runs'/name
                    text=(folder/'artifact.txt').read_text() if (folder/'artifact.txt').exists() else '未完成'
                    try:value=json.loads(text)
                    except ValueError:value={}
                    if task['domain']=='code':
                        body=''.join('<h4>'+esc(key)+'</h4><pre>'+esc(source)+'</pre>' for key,source in value.get('files',{}).items())
                    else:body='<pre>'+esc(value.get('artifact',text))+'</pre>'
                    score_path=LOCAL/'assessments'/(name+'.json')
                    score=json.loads(score_path.read_text()) if score_path.exists() else {}
                    columns.append('<article><h3>'+title+'</h3><p>已声明检查：'+('通过' if score.get('passed') else '未通过／未完成')+'</p>'+body+
                                   '<details><summary>完整输出和检查</summary><pre>'+esc(text)+'</pre><pre>'+esc(score)+'</pre></details></article>')
                packet={k:v for k,v in task.items() if k not in {'style_sets','tests','public','constraints','synthetic'}}
                sections.append('<section data-phase="'+phase+'"><h2>'+esc(phase+' / '+task['id']+' / 样例组 '+str(style+1))+'</h2>'+\
                                '<details><summary>风格样例</summary><pre>'+esc(task['style_sets'][style])+'</pre></details>'+\
                                '<details><summary>任务材料与输出契约</summary><pre>'+esc(packet)+'</pre></details><div class="grid">'+''.join(columns)+'</div></section>')
    page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>OwnVoice 0.2 对照</title><style>
body{margin:24px;background:#f4f6fa;color:#172238;font:16px/1.6 system-ui}h1{font-size:24px}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}article{background:white;border:1px solid #ccd4df;border-radius:8px;padding:16px}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:13px/1.6 ui-monospace,monospace}section{margin:32px 0}summary{cursor:pointer}@media(max-width:1000px){.grid{grid-template-columns:1fr}}
</style><h1>OwnVoice 0.2：相同任务与不同样例的三组对照</h1><p>本地只读，无上传。检查通过仅覆盖已声明的结构、事实或有限行为；风格匹配与正文来源复核另行报告。原始数据均为合成案例。</p>'''+''.join(sections)+'</html>'
    destination=LOCAL/'compare.html';destination.write_text(page);print(destination)


if __name__=='__main__':main()
