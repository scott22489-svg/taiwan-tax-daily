"""Build only public files into the Pages artifact."""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    archive = json.loads((ROOT / "data/articles.json").read_text(encoding="utf-8"))
    if not archive.get("articles"):
        raise RuntimeError("Refusing to publish an empty archive")
    destination = ROOT / "dist"
    destination.mkdir(exist_ok=True)
    for name in ("index.html", "style.css", "app.js", "favicon.svg"):
        shutil.copyfile(ROOT / "web" / name, destination / name)
    (destination / "data.json").write_text(json.dumps(archive, ensure_ascii=False), encoding="utf-8")
    (destination / ".nojekyll").touch()
    print(f"Built {len(archive['articles'])} articles into dist/")

if __name__ == "__main__":
    main()
