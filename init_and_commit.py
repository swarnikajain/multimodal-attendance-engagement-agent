"""
Initialize Git repository and create initial commit using Dulwich.
"""

import sys
from pathlib import Path
import dulwich.porcelain as git
from dulwich.repo import Repo

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

workspace_path = Path(".").resolve()
print(f"Initializing Git repository at: {workspace_path}")

# 1. Initialize repo
repo = git.init(str(workspace_path))

# 2. Files to include
tracked_files = [
    ".gitignore",
    "README.md",
    "DEMO_SCRIPT.md",
    "LICENSE",
    "requirements.txt",
    "config.py",
    "app.py",
    "verify_all_features.py",
    ".streamlit/config.toml",
    "data/.gitkeep",
    "data/exports/.gitkeep",
    "data/temp_uploads/.gitkeep",
    "sample_data/README.md",
    "sample_data/sample_classroom_10s.mp4",
    "sample_data/sample_classroom_10s.wav",
    "modules/__init__.py",
    "modules/video_processor.py",
    "modules/face_detector.py",
    "modules/tracking.py",
    "modules/attendance.py",
    "modules/audio_processor.py",
    "modules/engagement.py",
    "modules/recommendation_engine.py",
    "modules/analytics.py",
    "modules/database.py",
    "modules/report_generator.py",
    "modules/privacy.py",
    "modules/demo_data.py",
    "modules/ui_common.py",
    "pages/1_Dashboard.py",
    "pages/2_Participants.py",
    "pages/3_Session_Analysis.py",
    "pages/4_Reports.py",
    "pages/5_Settings.py",
    "tests/test_attendance.py",
    "tests/test_database.py",
    "tests/test_engagement.py",
    "tests/test_recommendations.py"
]

print("Staging files...")
for f in tracked_files:
    f_path = Path(f)
    if f_path.exists():
        git.add(repo, str(f))

# 3. Commit
author = b"Student Developer <student@futureskillsprime.edu>"
commit_msg = b"feat: initial commit of Multimodal Attendance & Engagement Agent\n\nComplete platform for automated attendance, observational engagement proxy analysis, and explainable pedagogical recommendations."

commit_sha = git.commit(
    repo,
    message=commit_msg,
    author=author,
    committer=author
)

# 4. Set branch to main
try:
    repo.refs[b"refs/heads/main"] = commit_sha
    repo.refs.set_symbolic_ref(b"HEAD", b"refs/heads/main")
except Exception as e:
    print(f"Branch note: {e}")

print(f"Successfully created initial commit on branch 'main'!")
print(f"Commit SHA: {commit_sha.decode('ascii')}")

# Print status summary
status = git.status(repo)
print(f"Staged files: {len(tracked_files)}")
