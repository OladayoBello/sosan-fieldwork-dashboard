# SOSAN Fieldwork Dashboard

A live-updating page showing submission progress by enumerator and by
community/LGA. It never shows individual answers, only counts. Set up once,
then it refreshes itself automatically.

## How it works

1. A small Python script logs into your KoboToolbox account and calculates
   summary counts (never raw answers) from the SOSAN form.
2. It writes those counts to `data/summary.json`.
3. A GitHub Action runs that script once a day (and any time you trigger it
   manually), and commits the updated file.
4. `index.html` is a plain webpage that reads `data/summary.json` and shows
   it as numbers and charts. GitHub Pages serves this file publicly, but
   since it only ever contains counts, no respondent data is exposed.

## One-time setup

### 1. Create the repository

Create a new GitHub repository and upload everything in this folder,
keeping the same folder structure (including the `.github` folder, which
is hidden by default in your file explorer, but must be included).

### 2. Get your Kobo API token

1. Log into KoboToolbox in a browser.
2. Go to **Account Settings** \u2192 **Security**.
3. Copy your API token (or generate one if you don't have one yet).
4. Keep this private \u2014 do not paste it into any file in the repository.

### 3. Find your project's asset UID

1. Open the SOSAN project on the Kobo website.
2. Look at the URL. It will look like:
   `https://kf.kobotoolbox.org/#/forms/aXXXXXXXXXXXXXXXXXXXXXX/summary`
3. The code after `forms/` is your asset UID.

### 4. Add both as GitHub secrets

In your new repository:

1. Go to **Settings** \u2192 **Secrets and variables** \u2192 **Actions**.
2. Click **New repository secret**.
3. Add one named `KOBO_API_TOKEN` with your token as the value.
4. Add another named `KOBO_ASSET_UID` with your project's asset UID.

These stay private to the repository and are never visible on the public
page or in any file.

### 5. Turn on GitHub Pages

1. Go to **Settings** \u2192 **Pages**.
2. Under **Source**, choose **Deploy from a branch**.
3. Choose the `main` branch and the `/ (root)` folder.
4. Save. GitHub will give you a URL, usually
   `https://<your-username>.github.io/<repository-name>/`.

### 6. Run it for the first time

You don't need to wait for the daily schedule the first time:

1. Go to the **Actions** tab in your repository.
2. Click **Refresh Kobo summary data** in the left sidebar.
3. Click **Run workflow** \u2192 **Run workflow**.
4. Wait about a minute, then refresh your GitHub Pages URL. Figures should
   appear.

## Changing what it shows

- **How often it refreshes**: edit the `cron` line in
  `.github/workflows/update-data.yml`. It's currently set to run once a day
  at 06:00 UTC.
- **Which fields it summarizes**: edit the constants near the top of
  `scripts/fetch_kobo_summary.py` (`ENUMERATOR_FIELD`, `LGA_FIELD`, etc.) if
  any field names in the form change.

## If something looks wrong

- **Page says "No data yet"**: the Action hasn't successfully run yet, or
  `data/summary.json` wasn't committed. Check the Actions tab for errors.
- **Action fails with an authentication error**: double check the
  `KOBO_API_TOKEN` and `KOBO_ASSET_UID` secrets are correct and haven't
  expired.
- **Numbers look off**: check that the field names in
  `fetch_kobo_summary.py` still match the actual current form (they may
  need updating if the form was restructured).
