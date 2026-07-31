# Development & Contribution Guide

Thank you for your interest in contributing to **FIT Activity Modifier**! This guide outlines our development workflow, coding standards, and branch management strategies to ensure code quality and project stability.

---

## 📌 Git Flow & Development Workflow

To keep the `main` branch stable, robust, and release-ready, all new features, enhancements, and bug fixes must follow the industry-standard Git Flow process:

```text
┌──────────┐      ┌────────────────────┐      ┌─────────────────┐      ┌──────────────────┐      ┌──────────────┐      ┌─────────────┐
│  checkout│ ──►  │ Create Feature     │ ──►  │ Local Dev &     │ ──►  │ Push to GitHub & │ ──►  │ Open Pull    │ ──►  │ Code Review │
│  main    │      │ Branch             │      │ Testing         │      │ Commit (Conventions)│   │ Request (PR) │      │ & Merge     │
└──────────┘      └────────────────────┘      └─────────────────┘      └──────────────────┘      └──────────────┘      └─────────────┘
```

---

## 🛠️ Step-by-Step Contribution Steps

### 1. Synchronize Local `main`
Always ensure your local `main` branch is up to date before creating a new working branch:
```bash
git checkout main
git pull origin main
```

---

### 2. Create a Feature Branch
Create a descriptive branch dedicated to the specific task or feature you are working on.

#### Branch Naming Conventions:
- `feature/` : New features or functional enhancements (e.g., `feature/add-cadence-scaling`, `feature/strava-webhook-listener`)
- `fix/`     : Bug fixes or issue resolutions (e.g., `fix/csv-timestamp-parser`)
- `docs/`    : Documentation updates or corrections (e.g., `docs/update-installation-guide`)
- `refactor/`: Code reorganization without changing external functionality (e.g., `refactor/decouple-gui-logic`)

```bash
git checkout -b feature/your-feature-name
```

---

### 3. Development & Local Testing
- Implement your changes in your code editor of choice.
- Test your changes locally to ensure CLI and GUI executions run cleanly without errors.
- Verify compatibility with existing `.fit` and `.csv` datasets (you can test against files in `examples/`).

---

### 4. Commit Changes & Push
Use clear, concise, and structured commit messages adhering to the **Conventional Commits** specification:

- `feat:` A new feature.
- `fix:` A bug fix.
- `docs:` Documentation changes.
- `refactor:` Code changes that neither fix a bug nor add a feature.
- `test:` Adding or updating tests.
- `style:` Code style changes (formatting, missing semi-colons, etc.).

Example:
```bash
git add .
git commit -m "feat: add support for cadence metric adjustment"
git push -u origin feature/your-feature-name
```

---

### 5. Create a Pull Request (PR)
1. Open the repository on GitHub: [Dewangga027/FIT-Activity-Modifier](https://github.com/Dewangga027/FIT-Activity-Modifier).
2. Click the **"Compare & pull request"** banner.
3. Provide a brief summary of the proposed changes, motivation, and any testing steps.
4. Submit the Pull Request for review.

---

### 6. Clean Up Local Branches (Optional)
Once your Pull Request has been merged into `main`:
```bash
git checkout main
git pull origin main
git branch -d feature/your-feature-name
```

---

## 🎨 Coding Standards

- **Python Style:** Follow PEP 8 guidelines for formatting, variable naming, and indentation (4 spaces).
- **Packaging:** We use `pyproject.toml` for managing project metadata, dependencies, and CLI entry points.
- **Documentation:** Update relevant docstrings and the `README.md` if your changes introduce new parameters or flags.
