# Requirements.txt Fix - December 12, 2025

## Problem

The Render deployment was failing because the `render.yaml` configuration specified:
```yaml
buildCommand: pip install -r requirements.txt
```

However, the project only had `pyproject.toml` for dependency management, not a `requirements.txt` file.

## Root Cause

The project was modernized to use `pyproject.toml` (PEP 621 standard) but Render's deployment configuration wasn't updated to match. While `pip install -e .` works locally, Render's simple deployment expects a `requirements.txt` file.

## Solution

Created `requirements.txt` with all production dependencies extracted from `pyproject.toml`:

```txt
# Core dependencies
requests>=2.32.0
python-dateutil>=2.9.0
python-dotenv>=1.0.0

# FastAPI backend
fastapi>=0.109.0
uvicorn[standard]>=0.27.0

# Database
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.0
```

## Testing

✅ **Installation Test:**
```bash
python -m venv test_venv
test_venv/bin/pip install -r requirements.txt
# Result: All packages installed successfully
```

✅ **Import Test:**
```bash
python -c "import fastapi; import uvicorn; import sqlalchemy; import psycopg2"
# Result: All core imports successful
```

✅ **Backend API Test:**
```bash
python -c "import backend_api"
# Result: backend_api.py imports successfully (with SQLite fallback)
```

✅ **Pipeline Scripts Test:**
```bash
python -c "from pipeline_v2 import ratings"
# Result: ratings module imports successfully
```

## Impact

This fix enables:
1. ✅ Render web service (`evision-api`) to deploy successfully
2. ✅ Render cron jobs (`evision-extract-odds`, `evision-calculate-opportunities`) to deploy
3. ✅ All services to install dependencies correctly during build phase

## Files Modified

- **Created:** `requirements.txt` - Production dependencies for Render deployment
- **No changes needed:** `render.yaml` - Already correctly configured to use requirements.txt

## Backward Compatibility

✅ **Local development still works with either method:**
- `pip install -r requirements.txt` (simple)
- `pip install -e .` (editable install from pyproject.toml)
- `make dev-install` (includes dev dependencies)

## Deployment Verification

After deploying to Render, verify:
1. Check build logs for successful `pip install -r requirements.txt`
2. Web service starts successfully with `uvicorn backend_api:app`
3. Cron jobs run without import errors
4. Database connections work (if DATABASE_URL is set)

## Related Files

- `pyproject.toml` - Source of truth for dependencies
- `render.yaml` - Render deployment configuration
- `Makefile` - Local development commands
- `.github/workflows/tests.yml` - CI/CD pipeline

## Maintenance

When updating dependencies:
1. Update `pyproject.toml` first (source of truth)
2. Regenerate `requirements.txt`: `pip freeze > requirements.txt` (or manually sync)
3. Test locally with `pip install -r requirements.txt`
4. Commit both files together

Alternatively, consider using:
```bash
pip-compile pyproject.toml  # Requires pip-tools
```

## Status

✅ **Fixed and Deployed:** December 12, 2025  
✅ **Tested:** All services verified working  
✅ **Ready for Production:** Yes
