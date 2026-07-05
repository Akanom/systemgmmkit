import subprocess
from pathlib import Path

paper = Path("paper/paper.md")

if not paper.exists():
    raise FileNotFoundError("paper/paper.md not found")

text = paper.read_text(encoding="utf-8")

remote = subprocess.check_output(
    ["git", "remote", "get-url", "origin"],
    text=True,
).strip()

if remote.startswith("git@github.com:"):
    repo_url = remote.replace("git@github.com:", "https://github.com/").replace(".git", "")
elif remote.endswith(".git"):
    repo_url = remote[:-4]
else:
    repo_url = remote

availability_insert = f"""
The source repository is available at `{repo_url}`. The cross-software comparison and validation artifacts are stored with the repository, including dynamic-GMM parity artifacts under `artifacts/parity/` and JOSS validation tables under `artifacts/joss/tables/`. These include the controlled Stata comparisons, the maintained `xtabond2` parity certificate, Python/R/Stata static comparison tables, performance benchmarks, and post-estimation / ML workflow audits.
"""

ai_section = """
# AI Usage Disclosure

Generative AI tools, including OpenAI ChatGPT, were used to assist with software-development workflow planning, code-review support, validation-script drafting, artifact summarization, PowerShell workflow generation, and manuscript drafting/editing.

AI assistance was applied to code scaffolding, validation and benchmark script drafting, documentation wording, artifact-summary preparation, and manuscript-section drafting. The author reviewed, modified, executed, and validated the AI-assisted outputs. The author made the primary econometric, architectural, design, validation, and interpretation decisions and remains responsible for the accuracy, originality, licensing compliance, and ethical/legal compliance of the submitted work.
"""

target = "# Availability and Reproducibility\n\n"

if "The source repository is available at" not in text:
    if target not in text:
        raise ValueError("Availability and Reproducibility heading not found")
    text = text.replace(target, target + availability_insert + "\n", 1)

if "# AI Usage Disclosure" not in text:
    if "# Acknowledgements" in text:
        text = text.replace("# Acknowledgements", ai_section + "\n# Acknowledgements", 1)
    elif "# References" in text:
        text = text.replace("# References", ai_section + "\n# References", 1)
    else:
        text = text.rstrip() + "\n\n" + ai_section + "\n"

paper.write_text(text, encoding="utf-8")

print("[DONE] Updated paper/paper.md")
print("Repository:", repo_url)
