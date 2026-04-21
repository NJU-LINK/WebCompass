# WebCompass Frontend

Academic project page for **WebCompass: A Unified Multimodal Benchmark and Evaluation Framework for Web Coding**.

Production deployment target:

- GitHub Pages (custom domain + project subpath)
- URL: `https://webcompass.ai/WebCompass/`
- Base path: `/WebCompass`

## Tech Stack

- Next.js (App Router)
- TypeScript
- Tailwind CSS
- shadcn/ui-style base components (`components/ui/*`)
- Framer Motion
- lucide-react
- Recharts

## Local Development

```bash
npm install
npm run dev
```

Local URL: `http://localhost:3000`

## Production Build (Static Export)

```bash
npm run build
```

This project uses Next.js static export (`output: "export"`) and generates deployable static files in `out/`.

## GitHub Pages Deployment

Deployment is automated by GitHub Actions:

- Workflow file: `.github/workflows/deploy.yml`
- Trigger: push to `main` or `master`
- Flow:
1. Install dependencies
2. Build static site
3. Upload Pages artifact (`out/`)
4. Deploy with `actions/deploy-pages`

After each push, the site updates at:
`https://webcompass.ai/WebCompass/`

## Figure-Source Consistency (LaTeX whitelist)

The frontend only renders figures that are referenced in LaTeX files under `../Paper/sec`.

- Extraction script: `scripts/extract-used-figures.mjs`
- Output whitelist: `data/usedFigures.json`

Run:

```bash
npm run sync:figures
npm run build
```

Figure rendering in `data/figures.ts` is filtered by this whitelist, and missing secondary assets are suppressed from the gallery.

## Deployment-specific Notes

- `next.config.js` applies static export + repo base path in production.
- Metadata and OG paths are generated with `/WebCompass` in production.
- Local `npm run dev` remains normal (no base path in development).

## Project Structure

```text
Frontend/
  .github/workflows/deploy.yml
  app/
  components/
  data/
  lib/
  public/
  scripts/
  styles/
```

