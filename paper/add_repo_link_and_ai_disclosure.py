from pathlib import Path
import subprocess

paper = Path("paper/paper.md")
text = paper.read_text(encoding="utf-8")

remote = subprocess.check_output(
    ["git", "remote", "get-url", "origin"],
    text=True
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

Generative AI tools, including OpenAI ChatGPT, were used to assist with software development workflow planning, code review support, validation-script drafting, artifact summarization, and manuscript drafting/editing. AI assistance was applied to code scaffolding, documentation wording, PowerShell workflow generation, and paper-section drafting.

All AI-assisted content was reviewed, modified, and validated by the author. The author made the primary design, architectural, econometric, validation, and interpretation decisions, executed the software and comparison workflows, inspected the generated artifacts, and remains responsible for the accuracy, originality, licensing compliance, and ethical/legal compliance of the submitted work.
"""

if "The source repository is available at" not in text:
    target = "# Availability and Reproducibility\n\n"
    if target not in text:
        raise ValueError("Availability heading not found.")
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
