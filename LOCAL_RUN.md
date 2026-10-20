# Local Run Guide

This project is a multi-page Dash app. For local development, use [`app_dev.py`](app_dev.py) or [`run_local.bat`](run_local.bat). The dev entrypoint runs with SSL so secure session cookies work during login.

## 1. Start from this workspace

Open a terminal in this folder:

```bat
l:\Strategic Marketing\Database Admin\ETL\Applications\reports
```

## 2. Create the conda environment

```bat
setup_conda_env.bat
```

Or run conda directly:

```bat
"C:\Users\rinzai.terrado\Anaconda3\Scripts\conda.exe" env create -f environment.yaml
```

If the environment already exists, update it instead:

```bat
"C:\Users\rinzai.terrado\Anaconda3\Scripts\conda.exe" env update -n reports-local -f environment.yaml --prune
```

## 3. Run locally

```bat
run_local.bat
```

Then open:

```text
https://127.0.0.1:8050
```

To use a different port:

```bat
set PORT=8051
run_local.bat
```

## If Python is not on PATH

This machine currently resolves [`python`](LOCAL_RUN.md) to the Windows Store alias instead of a real interpreter. [`run_local.bat`](run_local.bat) uses the conda environment Python directly:

```bat
C:\Users\rinzai.terrado\Anaconda3\envs\reports-local\python.exe
```

If your environment is in a different Anaconda location, override it:

```bat
set PYTHON_EXE=C:\Users\rinzai.terrado\Anaconda3\envs\reports-local\python.exe
run_local.bat
```

Replace the example path with the interpreter path shown by VS Code if needed.

You can also disable the Windows Store alias in Windows:

```text
Settings > Apps > Advanced app settings > App execution aliases > turn off python.exe and python3.exe
```

## Notes

- [`app_dev.py`](app_dev.py) runs with SSL and debug enabled.
- [`app.py`](app.py) is the server-style entrypoint and expects SSL certificates from a UNC share.
- Some pages rely on internal network paths and the internal [`okada`](agent/operations.md) package. If startup fails during page import, confirm your VPN/network share access first.
- The combined patron/comms page is in [`pages/whitelist.py`](pages/whitelist.py), with helper functions in [`pages/patrondb_etl/patrondb_etl.py`](pages/patrondb_etl/patrondb_etl.py).
