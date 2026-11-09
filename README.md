# Downard–Freestone Family Archive

Open `index.html` for the four family trees. The site also contains the People directory, historical Stories, Places and properties, Timeline, Document archive, Research notebook, About page, and Search.

The site is static and publishes from the root of `main` on GitHub Pages. It needs no server, database, or paid service.

To update the generated pages, edit the shared tree in `family-data.js`, the curated archive data in `archive-records.json`, the source catalog under `research/sources/`, or the cases under `research/verification/`. Run `python3 build-archive.py` with Node.js available, then review and commit the generated HTML and `archive-branches.js` together with their source changes.

The two original stories are edited directly under `stories/`. Their embedded scans are the preserved originals. The smaller JPEGs in the collection are browse previews. Research leads with missing scans, OCR, or issue details are labeled in the document archive.
