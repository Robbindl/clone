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

For the included Feathery capture, use:

```powershell
python .\local_server.py cloned_site --port 8001
```

Then open `http://localhost:8001/form.feathery.io/to/YAaOHQ`.

## Limitations

The cloner captures publicly downloadable frontend assets. Sites that depend on private APIs, authentication, server-side sessions, or protected runtime data may not work as complete offline copies. Use an official export or API for sites you own.

## Files

- `cloner.py` downloads and processes site assets.
- `local_server.py` serves clones and maps extensionless SPA routes to HTML files.
- `requirements.txt` lists Python dependencies.
