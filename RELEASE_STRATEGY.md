# Git Branching & Release Strategy

## 1. Branch Architecture
* **`main`**: The strict production branch. Code here is ALWAYS deployable. No one pushes directly to `main`.
* **`develop`**: The active staging branch. All feature branches merge here for integration testing.
* **`feat/*`, `bugfix/*`**: Ephemeral branches created off `develop` for specific tasks.

## 2. Release Protocol
1. When `develop` is stable, a Pull Request is made to merge `develop` into `main`.
2. Once merged, a Git tag (e.g., `v1.0.0`) is created on `main`.
3. The tag is converted into an official **GitHub Release**.

## 3. The Rollback Procedure
If a bug reaches production, we do NOT write hotfixes directly on `main` in a panic. We roll back the deployment.

**To execute a rollback:**
1. **Infrastructure Level:** Re-deploy the Docker container associated with the previous stable GitHub Release tag (e.g., `docker pull our-registry/api:v0.4.0`).
2. **Code Level:** If the codebase needs to be reverted permanently, do not delete Git history. Use `git revert <broken_commit_hash>` on the `develop` branch, test it, and push a new release (e.g., `v1.0.1`) to roll forward safely.
