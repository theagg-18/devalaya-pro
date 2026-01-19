---
description: How to release a new version of the Devalaya Billing System
---

# Release Process

1.  **Update Version**:
    *   Open `version.py`.
    *   Update `__version__` and `__version_info__`.
    *   Add a new entry to `VERSION_HISTORY` with the date and list of changes.

2.  **Commit Changes**:
    *   `git add version.py`
    *   `git commit -m "Bump version to X.Y.Z"`

3.  **Push Code**:
    *   `git push origin main`

4.  **Create Tag**:
    *   Create an annotated tag with the changelog.
    *   `git tag -a vX.Y.Z -m "Release vX.Y.Z\n\n- Change 1\n- Change 2..."`

5.  **Push Tag**:
    *   `git push origin vX.Y.Z`

6.  **Verify**:
    *   Check GitHub to ensure the tag and release notes appear.
