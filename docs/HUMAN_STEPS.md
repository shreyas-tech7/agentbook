# Human steps

Only Shreyas can do these. Do them in order. Release commit: `RELEASE_SHA`.

## 1. Create the GitHub repo and push the bundle

The build had no GitHub access, so the code lives in a Git bundle.

1. Create a private repo named `agentbook` under `shreyas-tech7` at https://github.com/new. Add no README, license or .gitignore.
2. Clone the bundle and push every branch:

```bash
git clone /mnt/project-files/portfolio/bundles/agentbook.bundle agentbook
cd agentbook
git remote set-url origin https://github.com/shreyas-tech7/agentbook.git
git push origin --all
```

If you copied the bundle to your own computer, use that path in the first line.

## 2. Open a pull request and merge it

1. Open a pull request from `claude/build-agentbook` into `main`.
2. Read the diff. Start with `agentbook/patterns/tool_loop.py` and `docs/lessons/01-tool-loop.md`.
3. Check that the CI run on the pull request is green. If Actions is off, run `./init.sh` locally.
4. Merge with a merge commit, so the release commit stays in the history of `main`.

## 3. Tag the release candidate

```bash
git fetch origin
git tag -a v0.1.0-rc1 RELEASE_SHA -m "Release candidate 1"
git push origin v0.1.0-rc1
```

Or create a pre-release with the tag `v0.1.0-rc1` on the Releases page.

## 4. Run the secret scan once more

```bash
gitleaks git -v .
```

It must say "no leaks found". The build ran it on every commit.

## 5. Decide about `docs/build/BUILD_PROMPT.md`

It holds the full brief the agents followed. It names your GitHub account and the tools the build used. Decide whether it stays public. To remove it, delete the file in a new commit before step 6. It stays in the history, so remove it from history too if it must never be public.

## 6. Make the repo public

Settings, then General, then Change visibility. All history becomes public at that moment.

## 7. Turn on Pages

Settings, then Pages. Deploy from the `main` branch, folder `/docs`. The results page is `docs/index.html`.

## 8. Fill in the About box and the social preview

- Copy the description and topics from `docs/TOPICS.md` into the About box.
- Settings, then General, then Social preview. Upload `docs/social-preview.png`.

## 9. Pin the repo

Pin it on your profile, or list it in your profile README.

## 10. Record mode (optional)

1. Get a free API key from a provider with an OpenAI-compatible endpoint.
2. Set the three variables from `.env.example` in your shell. Never commit them.
3. Run `python scripts/record_demo.py`, then `python scripts/gen_readme.py`.
4. Commit `results/live/` and the README.

## 11. PyPI (optional)

The name `agentbook` was free on 2026-11-20. Publish with trusted publishing from a GitHub Actions workflow, only if you want the package on PyPI.
