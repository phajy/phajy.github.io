# phajy.github.io

Personal academic website for [Professor Andrew Young](https://phajy.github.io), built with [Quarto](https://quarto.org/) and published to GitHub Pages.

There is also a [Wiki](https://github.com/phajy/phajy.github.io/wiki) with notes on relativistic accretion discs and related software. Collaborators can edit the wiki — ask if you’d like access.

## Local development

```bash
python scripts/prepare_site.py   # people partials + ORCID publications
quarto preview
```

## Content you usually edit

| Path | Purpose |
| --- | --- |
| `index.qmd` | Home / hero |
| `about.qmd` | Biography and contact |
| `data/people.yml` | Current and former group members |
| `news/*/index.qmd` | News posts |
| `styles.scss` | Site look and feel |

Publications are generated from ORCID (`0000-0003-3626-9151`) into `_partials/publications-list.md`, with a cached copy in `data/orcid-works.json`.

## Publishing

GitHub Actions (`.github/workflows/publish.yml`) renders the site and publishes to the `gh-pages` branch on every push to `main`, and weekly to refresh ORCID.

**One-time GitHub settings:** under *Settings → Pages*, set the source to **Deploy from a branch**, branch **`gh-pages`** / root. Also grant the Actions workflow **Read and write** permissions under *Settings → Actions → General*.

A monthly workflow opens a checklist issue so the people list and news stay current.
