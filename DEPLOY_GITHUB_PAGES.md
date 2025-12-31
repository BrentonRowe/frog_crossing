# Deploy to iPad/iPhone via GitHub Pages (Web)

This game is written in Python/Pygame. To run on iPad/iPhone, the simplest route is to build a WebAssembly version and host it on GitHub Pages.

## 1) Install pygbag

From the project folder:

- `C:/Users/brent/AppData/Local/Microsoft/WindowsApps/python3.11.exe -m pip install -U pygbag`

## 2) Build the web version

- `C:/Users/brent/AppData/Local/Microsoft/WindowsApps/python3.11.exe -m pygbag frog_crossing.py`

This produces a folder like:

- `build/web/`

## 3) Publish on GitHub Pages

Quick option (recommended):

- Run `publish_pages.ps1` from the repo root to build + publish to Pages in one go.

You have two common options:

### Option A: Pages from `/docs`

1. Copy `build/web` to `docs`:
   - Delete any existing `docs/` folder
   - Copy the entire `build/web/` folder to `docs/`
2. Commit + push
3. In GitHub repo settings: **Settings → Pages → Build and deployment → Source: Deploy from a branch**
   - Branch: `main`
   - Folder: `/docs`

Your link will be:

- `https://BrentonRowe.github.io/<YOUR_REPO_NAME>/`

Example (repo: `frog_crossing`):

- `https://BrentonRowe.github.io/frog_crossing/`

### Option B: Pages from `gh-pages` branch

1. Use a GitHub Pages action or push `build/web` to `gh-pages`
2. Enable Pages for the `gh-pages` branch

## Notes for iOS

- iPhone/iPad requires HTTPS for web apps; GitHub Pages is HTTPS.
- Touch controls are built into the game.

## I can’t push for you

I can prepare files for GitHub Pages, but I can’t publish to your GitHub account without you pushing the repo.
