import subprocess
import os

DOCS_DIR = "docs"
ARTIFACTS_DIR = os.path.join(DOCS_DIR, "_artifacts")
HTML_DIR = os.path.join(DOCS_DIR, "_book")

subprocess.run(["rm", "-rf", ARTIFACTS_DIR], check=True)
subprocess.run(["rm", "-rf", HTML_DIR], check=True)
subprocess.run(["quarto", "render", "docs", "--profile", "offline"], check=True)
subprocess.run(["quarto", "render", "docs", "--profile", "en"], check=True)
subprocess.run(["quarto", "render", "docs", "--profile", "zh"], check=True)