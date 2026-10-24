# Website Cloner

A Python website asset cloner for saving HTML, CSS, JavaScript, fonts, and media for local inspection.

## Setup

This project uses Python 3.13 and `uv`.

```powershell
uv python install 3.13
uv venv .venv --python 3.13
.\.venv\Scripts\Activate.ps1
uv pip install -r requirements.txt
```

## Clone a site

Use a separate output directory for each site:

```powershell
python .\cloner.py "https://example.com" --output another_clone --delay 0
```

By default, the cloner downloads the starting page and its referenced assets. To also crawl same-domain navigation pages:

```powershell
python .\cloner.py "https://example.com" --output another_clone --delay 0 --follow-pages
```

Useful options:

- `--output NAME` sets the output directory.
- `--delay SECONDS` controls the delay between requests.
- `--depth NUMBER` limits recursive asset discovery.
- `--follow-pages` crawls same-domain links.
- `--no-robots` skips `robots.txt` checks when you have permission to do so.

## View a clone

Serve the clone over HTTP so browser scripts and SPA routes work:

```powershell
python .\local_server.py another_clone --port 8002
```

Open `http://localhost:8002` in your browser.

If the cloned site has a nested route, open it under the same local path. For example,
if the source URL was `https://example.com/products/item`, use:

```powershell
python .\local_server.py another_clone --port 8002
```

Then open `http://localhost:8002/example.com/products/item`.

## Standalone Feathery form

The Feathery form, its Node/MongoDB server, and its local environment
configuration have been moved into a separate working folder on this PC. The
Python cloner in this repository is independent of that running form. See the
standalone folder's `README.md` for startup and database details.

## Limitations

The cloner captures publicly downloadable frontend assets. Sites that depend on private APIs, authentication, server-side sessions, or protected runtime data may not work as complete offline copies. Use an official export or API for sites you own.

## Local Working Directories

The `binance_clone_playwright/` directory is used for local development and testing only. It is not tracked in version control (see `.gitignore`).

## Files

- `cloner.py` downloads and processes site assets.
- `local_server.py` serves clones and maps extensionless SPA routes to HTML files.
- `requirements.txt` lists Python dependencies.
