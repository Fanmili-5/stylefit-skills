"""Write task facts and original sources by blind pair ID, without revealing methods."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    tasks = {task['id']: task for task in json.loads((ROOT / 'evals/tasks.json').read_text())['main']}
    pairs = json.loads((ROOT / '.local/blind-mapping.json').read_text())
    lines = ['# 盲评任务参考', '', '仅含任务约束和改写前原文，不包含方法名称或左右答案映射。', '']
    for pair in pairs:
        task = tasks[pair['task']]
        lines.extend(['## ' + pair['id'], '', task['packet'], ''])
        if task.get('source'):
            lines.extend(['改写前原文：', '', '```' + ('python' if task['domain'] == 'code' else 'text'),
                          task['source'], '```', ''])
        if task.get('protected'):
            lines.extend(['必须保留的信息：' + ', '.join(task['protected']), ''])
    path = ROOT / '.local/blind-task-reference.md'
    path.write_text('\n'.join(lines))
    print(str(path))


if __name__ == '__main__':
    main()
