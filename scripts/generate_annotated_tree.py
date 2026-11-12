import os
from pathlib import Path

root = Path(__file__).resolve().parent.parent
out = root / 'aaos_tree_annotated.txt'

CODE_EXTS = {
    '.py', '.js', '.ts', '.tsx', '.jsx', '.java', '.go', '.c', '.cpp', '.h', '.rs',
    '.rb', '.php', '.swift', '.kt', '.kts', '.groovy', '.scala', '.ps1', '.sh',
    '.psm1', '.psd1', '.cs', '.fs', '.m', '.mm'
}


def has_code_in_path(p: Path) -> bool:
    if p.is_file():
        return p.suffix.lower() in CODE_EXTS
    for root_dir, dirs, files in os.walk(p):
        for f in files:
            if Path(f).suffix.lower() in CODE_EXTS:
                return True
    return False


def tree(dir_path: Path, prefix=''):
    entries = sorted(list(dir_path.iterdir()), key=lambda p: (not p.is_dir(), p.name.lower()))
    for i, path in enumerate(entries):
        name = path.name
        connector = '└── ' if i == len(entries)-1 else '├── '
        annotation = '(has code)' if has_code_in_path(path) else '(no code)'
        yield f"{prefix}{connector}{name} {annotation}"
        if path.is_dir():
            extension = '    ' if i == len(entries)-1 else '│   '
            yield from tree(path, prefix + extension)

with out.open('w', encoding='utf-8') as f:
    f.write(f"Annotated tree for: {root}\n\n")
    for line in tree(root):
        f.write(line + '\n')

print(f'Wrote annotated tree to: {out}')
