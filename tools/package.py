"""Package only the public reproducibility files; do not archive the working folder."""

from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    ".gitignore",
    ".python-version",
    ".node-version",
    "pyproject.toml",
    "package.json",
    "package-lock.json",
    "requirements-plot.txt",
    "tools/package.py",
    "tools/compare_results.py",
    "tools/build_fixtures.py",
    "tools/paper_statistics.py",
    "tools/plot_curves.py",
]
DOCUMENTS = ["README.md", "README.ja.md", "METHOD.md", "METHOD.ja.md", "THIRD_PARTY.md"]
DIRECTORIES = ["expectation_lab", "tests", "docs", ".github/workflows"]


def public_files():
    selected = [ROOT / name for name in FILES]
    selected += [ROOT / name for name in DOCUMENTS]
    for directory in DIRECTORIES:
        selected.extend(
            path
            for path in (ROOT / directory).rglob("*")
            if path.is_file()
            and not {"__pycache__", ".pytest_cache", ".cache"}.intersection(path.parts)
            and path.suffix not in (".pyc", ".pyo")
            and path.name != ".DS_Store"
        )
    return sorted(set(selected))


if __name__ == "__main__":
    destination = ROOT.parent / (ROOT.name + ".zip")
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in public_files():
            archive.write(path, ROOT.name + "/" + str(path.relative_to(ROOT)))
    print(destination)
