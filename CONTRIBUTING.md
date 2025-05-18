Thank you for your interest in contributing to **Sisimpur**! We welcome contributions of all kinds: code, documentation, tests, bug reports, feature requests, and ideas. By participating, you help make Sisimpur better for everyone.

---

## Table of Contents

1. [Code of Conduct](#1-code-of-conduct)
2. [Project Structure](#2-project-structure)
3. [Getting Started](#3-getting-started)
4. [Reporting Issues](#4-reporting-issues)
5. [Contributing Code](#5-contributing-code)

   * [Frontend Contributions](#51-frontend-contributions)
   * [Backend & Core](#52-backend--core)
   * [AI Brain Module](#53-ai-brain-module)
6. [Writing Documentation](#6-writing-documentation)
7. [Testing](#7-testing)
8. [Style and Formatting](#8-style-and-formatting)
9. [Continuous Integration](#9-continuous-integration)
10. [License](#10-license)

---

## 1. Code of Conduct

Please read and adhere to our [Code of Conduct](CODE_OF_CONDUCT.md). We expect everyone to be respectful, supportive, and collaborative.

## 2. Project Structure

```
udbhabon-sisimpur/
├── README.md
├── CONTRIBUTING.md
├── LICENSE
├── manage.py
├── requirements.txt
├── apps/
│   ├── authentication/   # Django auth app
│   └── frontend/         # Django frontend app
├── core/                 # Django project settings
├── frontend/             # Static HTML prototypes (Home_01.html, Home_02.html)
├── sisimpur-brain/       # AI Brain module (main.py)
└── static/               # CSS & JS assets
```

## 3. Getting Started

1. **Fork** the repository.
2. **Clone** your fork:

   ```bash
   git clone https://github.com/<your-username>/udbhabon-sisimpur.git
   cd udbhabon-sisimpur
   ```
3. **Install** dependencies:

   ```bash
   pip install -r requirements.txt
   ```
4. **Virtual Environment** (optional but recommended):

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
5. **Run** the development server:

   ```bash
   python manage.py runserver
   ```

## 4. Reporting Issues

1. Search existing issues to avoid duplicates.
2. Open a new issue with a clear title and description.
3. Use our templates in `.github/ISSUE_TEMPLATE/` for bug reports or feature requests.

## 5. Contributing Code

### 5.1 Frontend Contributions

The **frontend** directory contains static prototypes, while `apps/frontend` holds the Django templates and views.

* **Static HTML & CSS/JS**: Work in the `frontend/` folder for standalone pages.
* **Django Frontend App**: Modify `apps/frontend/templates/`, `views.py`, and related routes.

#### Toast Notification System

Sisimpur includes a global toast notification system for displaying feedback to users:

**File Structure:**
- `apps/frontend/templates/includes/toast.html`: Contains the toast container and CSS
- `static/js/toast_new.js`: Contains the JavaScript for creating and managing toast notifications

**Usage in Views:**
```python
from django.contrib import messages

# Different types of messages
messages.success(request, 'Operation completed successfully!', extra_tags='Success')
messages.error(request, 'An error occurred.', extra_tags='Error')
messages.warning(request, 'Warning: This action cannot be undone.', extra_tags='Warning')
messages.info(request, 'Your session will expire in 10 minutes.', extra_tags='Info')
```

**Usage in JavaScript:**
```javascript
// Show a toast notification directly from JavaScript
if (typeof window.showToast === 'function') {
    window.showToast('success', 'Success', 'Operation completed successfully!');
    window.showToast('error', 'Error', 'An error occurred.');
    window.showToast('warning', 'Warning', 'This action cannot be undone.');
    window.showToast('info', 'Info', 'Your session will expire in 10 minutes.');
}
```

**Toast Types:**
- `success`: Green color, check icon
- `error`: Red color, exclamation icon
- `warning`: Orange color, bell icon
- `info`: Blue color, info icon

**Testing:**
- Visit `/toast-test/` to see a demonstration of all toast types
- Each toast automatically disappears after 5 seconds
- Toasts can be manually dismissed by clicking the × button

Create feature branches:

```bash
git checkout -b feature/frontend-new-component
```

### 5.2 Backend & Core

For changes to Django settings, models, or URL routing, work within `core/` and `apps/authentication`:

* **Core settings**: `core/settings.py`, `core/urls.py`.
* **Authentication**: `apps/authentication/` for user-related features.

Branch naming example:

```bash
git checkout -b fix/auth-model-validation
```

### 5.3 AI Brain Module

The AI logic lives in `sisimpur-brain/main.py`. For enhancements, bug fixes, or new analysis pipelines:

```bash
git checkout -b feature/brain-enhance-parser
```

> **Note**: Ensure any third-party model dependencies are added to `requirements.txt`.

#### Pull Request Workflow

1. Commit changes with clear messages: `Add FAQ endpoint (#123)`.
2. Push branch: `git push origin feature/xyz`.
3. Open a PR against `main` including:

   * Summary of changes
   * Related issues
   * Testing instructions
4. Request reviews via GitHub reviewers.

## 6. Writing Documentation

* Document new features in `docs/` or inline via docstrings.
* Update `README.md` for installation or usage changes.
* Keep markdown clear and concise.

## 7. Testing

* Run existing tests: `pytest` or `python manage.py test`.
* Add tests for new code paths.

## 8. Style and Formatting

* Python: follow PEP8, use `black .` and `flake8 .`.
* JavaScript/CSS: maintain existing project style.

## 9. Continuous Integration

All PRs trigger GitHub Actions:

* Linting
* Tests
* Build checks

Ensure your branch passes CI before merging.

## 10. License

By contributing, you agree your work will be licensed under the [MIT License](LICENSE).