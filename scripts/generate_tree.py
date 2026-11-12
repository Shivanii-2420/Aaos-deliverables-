import os
from pathlib import Path

root = Path(__file__).resolve().parent.parent
out = root / 'aaos_tree.txt'

def tree(dir_path, prefix=''):
    entries = sorted(os.listdir(dir_path))
    for i, name in enumerate(entries):
        path = os.path.join(dir_path, name)
        connector = '└── ' if i == len(entries)-1 else '├── '
        yield f"{prefix}{connector}{name}"
        if os.path.isdir(path):
            extension = '    ' if i == len(entries)-1 else '│   '
            yield from tree(path, prefix + extension)

with out.open('w', encoding='utf-8') as f:
    f.write(f"Tree for: {root}\n\n")
    for line in tree(str(root)):
        f.write(line + '\n')

print(f'Wrote tree to: {out}')
