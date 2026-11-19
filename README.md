# Vice Panels

Vice Panels is an offline poster cover maker. Arrange local photos into a cinematic collage, tune each panel, and export a finished poster as PNG.

## Run it

Use Node 22 from this repository:

```sh
node serve.ts
```

Open `http://localhost:8080`. The app uses only local files; uploaded photos remain in the browser session.

## How a cover is made

Choose Classic (large left hero with four right panels), Hero Strip (large upper image with three images below), Duo (two tall panels), or Quad (four equal panels). Add photos with the file picker or drag them onto panels. Click a panel to select it; zoom and drag to reframe, and choose a panel grade or an overall grade.

The four grades are Vice Sunset (pink and orange warmth), Neon Night (cyan and magenta contrast), Palm Noir (hard monochrome contrast), and Golden Hour (warm gold haze). The optional cover finish adds halftone dots, grain, and a vignette. Title, subtitle band, and tagline are drawn into the canvas so they are part of every export. Export renders directly at 1080 × 1080, 1080 × 1350, or 1920 × 1080.

Sample photos live in `app/samples/`. `tools/make_sample.py` creates the original 1200 × 900 neon street sample using Python Pillow.

## Licence

The starter kit's licence is included at the repository root. The sample photographs and generated artwork are provided for this entry; the app uses system fonts and contains no Rockstar Games marks or artwork.
