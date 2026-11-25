"""Вставить ЛР3 в существующее меню MkDocs без перезаписи других разделов."""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
CONFIG = REPO_ROOT / "mkdocs.yml"
ITEM = "  - Лабораторная работа №3: lr3/report.md\n"


def main():
    if not CONFIG.is_file():
        raise SystemExit(f"Файл не найден: {CONFIG}")
    text = CONFIG.read_text(encoding="utf-8-sig")
    if "lr3/report.md" in text:
        print("ЛР3 уже добавлена в mkdocs.yml — без изменений")
        return
    lines = text.splitlines(keepends=True)
    nav_idx = next((i for i, s in enumerate(lines) if s.strip() == "nav:" and s.startswith("nav:")), None)
    if nav_idx is None:
        raise SystemExit("Нет блока nav: в mkdocs.yml; вставьте пункт меню вручную.")
    end = next((i for i in range(nav_idx + 1, len(lines))
                if lines[i].strip() and not lines[i][0].isspace()), len(lines))
    lines.insert(end, ITEM)
    CONFIG.write_text("".join(lines), encoding="utf-8")
    print("Добавлен пункт ЛР3 в меню MkDocs; остальные пункты сохранены")


if __name__ == "__main__":
    main()
