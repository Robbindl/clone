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

## Save form submissions to MongoDB

The cloned form is connected to `POST /api/submit`. The endpoint stores each
submission in the MongoDB `submissions` collection with the form route,
submitted data, page URL, and a server timestamp. Dynamic form fields are
stored under `data`, so new form steps do not require a schema change.
Changes and step navigation from one form session update the same record;
a new page load gets a new client submission ID and creates a new record.

Install the server dependencies:

```powershell
npm install
Copy-Item .env.example .env
```

Set `MONGODB_URI` in `.env`. The default local value is:

```text
mongodb://127.0.0.1:27017/cloned_site
```

For a separate Binance database, set `MONGODB_BINANCE_URI` as well. The local
default is `mongodb://127.0.0.1:27017/binance`.

Start the site and API together:

```powershell
npm start
```

Keep that PowerShell window open while using the form. If the browser has
remembered an older broken script, refresh the form with `Ctrl+F5` once.

Open `http://localhost:8002/form.feathery.io/to/YAaOHQ`. Check the API with
`http://localhost:8002/api/health`. View saved entries in MongoDB Compass or
with `mongosh`, using database `cloned_site` and collection `submissions`.

Use the Node/Express server above when testing submissions; `local_server.py`
only serves static files and does not provide the API.

The cloned form's phone-formatting JavaScript asset was repaired because the
downloaded copy contained an HTML error page instead of JavaScript. Without
that asset, the phone input stayed controlled at its placeholder value and
reported that the field was required.

## Limitations

The cloner captures publicly downloadable frontend assets. Sites that depend on private APIs, authentication, server-side sessions, or protected runtime data may not work as complete offline copies. Use an official export or API for sites you own.

## Local Working Directories

The `binance_clone_playwright/` directory is used for local development and testing only. It is not tracked in version control (see `.gitignore`).

## Files

- `cloner.py` downloads and processes site assets.
- `local_server.py` serves clones and maps extensionless SPA routes to HTML files.
- `requirements.txt` lists Python dependencies.
