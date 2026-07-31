# Development & Contribution Guide

Thank you for your interest in contributing to **FIT Activity Modifier**! This guide outlines our development workflow, coding standards, and branch management strategies to ensure code quality and project stability.

---

## 📌 Git Flow & Branch Strategy

To keep the production branch (`main`) stable and release-ready, all development follows a two-tier Git Flow architecture centered around the `development` branch:

```text
main (production-ready, protected)
 │
 └── development (active integration branch)
      │
      ├── feature/daily-batch-generator   ← New features
      ├── fix/csv-timestamp-overflow      ← Bug fixes
      ├── refactor/decouple-gui-logic     ← Refactoring
      └── docs/update-installation-guide  ← Docs only
```

```text
┌───────────────┐      ┌────────────────────┐      ┌─────────────────┐      ┌──────────────────┐      ┌──────────────┐      ┌─────────────┐
│ checkout      │ ──►  │ Create Feature     │ ──►  │ Local Dev &     │ ──►  │ Push to GitHub & │ ──►  │ Open PR to   │ ──►  │ Code Review │
│ development   │      │ Branch             │      │ Testing         │      │ Commit           │      │ development  │      │ & Merge     │
└───────────────┘      └────────────────────┘      └─────────────────┘      └──────────────────┘      └──────────────┘      └─────────────┘
```

---

## 🛠️ Step-by-Step Contribution Guide

### 1. Synchronize Local `development`
Always ensure your local `development` branch is up to date before creating a new working branch:
```bash
git checkout development
git pull origin development
```

---

### 2. Create a Feature Branch
Create a descriptive branch dedicated to the specific task or feature off `development`.

#### Branch Naming Conventions:
- `feature/` : New features or functional enhancements (e.g., `feature/daily-batch-generator`, `feature/strava-batch-upload`)
- `fix/`     : Bug fixes or issue resolutions (e.g., `fix/csv-timestamp-parser`)
- `docs/`    : Documentation updates or corrections (e.g., `docs/update-installation-guide`)
- `refactor/`: Code reorganization without changing external functionality (e.g., `refactor/decouple-gui-logic`)
- `chore/`   : Tooling, dependency, or configuration updates (e.g., `chore/add-gitignore-entry`)

```bash
git checkout -b feature/your-feature-name
```

---

### 3. Development & Local Testing
- Implement your changes in your code editor of choice.
- Test your changes locally to ensure CLI and GUI executions run cleanly without errors.
- Verify compatibility with existing `.fit` and `.csv` datasets (you can test against files in `examples/`).
- Run automated unit tests:
  ```bash
  python -m unittest discover -s tests -v
  ```

---

### 4. Commit Changes & Push
Use clear, concise, and structured commit messages adhering to the **Conventional Commits** specification:

- `feat:` A new feature.
- `fix:` A bug fix.
- `docs:` Documentation changes.
- `refactor:` Code changes that neither fix a bug nor add a feature.
- `test:` Adding or updating tests.
- `chore:` Tooling, packaging, or CI changes.

Example:
```bash
git add .
git commit -m "feat(creator): add daily batch generator and humanized HR algorithm"
git push -u origin feature/your-feature-name
```

---

### 5. Create a Pull Request (PR)
1. Open the repository on GitHub: [Dewangga027/FIT-Activity-Modifier](https://github.com/Dewangga027/FIT-Activity-Modifier).
2. Click **"Compare & pull request"**.
3. Set the target base branch to **`development`** (not `main`).
4. Provide a summary of changes, motivation, and verification steps.
5. Submit the Pull Request for code review and automated checks.

---

### 6. Clean Up Local Branches (Optional)
Once your Pull Request has been merged into `development`:
```bash
git checkout development
git pull origin development
git branch -d feature/your-feature-name
```

---

## 🎨 Coding Standards

- **Python Style:** Follow PEP 8 guidelines for formatting, variable naming, and 4-space indentation.
- **Packaging:** We use PEP 621 (`pyproject.toml`) for managing package metadata, dependencies, and entrypoints.
- **Documentation:** Update docstrings, `README.md`, and `CONTRIBUTING.md` whenever CLI flags, installation steps, or branch workflows change.
