"""
Helper script to push the local Git repository to GitHub using Dulwich or standard Git.
Works even if git.exe is not installed on system PATH.
"""

import sys
import getpass
from pathlib import Path
import dulwich.porcelain as git
from dulwich.repo import Repo

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def push_repo():
    print("=" * 65)
    print("🚀 GITHUB PUSH HELPER (MULTIMODAL ATTENDANCE AGENT)")
    print("=" * 65)

    repo_path = Path(".").resolve()
    repo = Repo(str(repo_path))

    print("\nBefore pushing, ensure you have created an empty repository on GitHub.")
    print("Example: https://github.com/your-username/multimodal-attendance-agent.git\n")

    remote_url = input("Enter your GitHub Repository HTTPS URL: ").strip()
    if not remote_url:
        print("❌ Error: Repository URL cannot be empty.")
        return

    # Check if authentication token is needed
    print("\nFor private or public repositories, GitHub requires a Personal Access Token (PAT)")
    print("Generate one at: https://github.com/settings/tokens (with 'repo' scope)")
    
    username = input("Enter your GitHub Username: ").strip()
    token = getpass.getpass("Enter your GitHub Personal Access Token (hidden): ").strip()

    if username and token:
        # Format authenticated URL
        if "@" not in remote_url and remote_url.startswith("https://"):
            auth_url = remote_url.replace("https://", f"https://{username}:{token}@")
        else:
            auth_url = remote_url
    else:
        auth_url = remote_url

    print(f"\nPushing 'main' branch to: {remote_url} ...")
    try:
        git.push(repo, auth_url, refspecs=[b"refs/heads/main:refs/heads/main"])
        print("\n🎉 SUCCESS! Your repository has been pushed to GitHub.")
        print(f"🔗 View it at: {remote_url.replace('.git', '')}")
    except Exception as e:
        print(f"\n❌ Push failed: {e}")
        print("\nTroubleshooting tips:")
        print("1. Check that your Personal Access Token has 'repo' permissions.")
        print("2. Ensure the remote repository on GitHub was created without initializing a README/License (so it is an empty repository).")
        print("3. Alternatively, if Git for Windows is installed, you can run:")
        print(f"   git remote add origin {remote_url}")
        print("   git push -u origin main")

if __name__ == "__main__":
    push_repo()
