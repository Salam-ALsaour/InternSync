# InternSync – Wireframe Sources

These files are the sources of the clickable wireframes in Claude Design: [InternSync Wireframes](https://claude.ai/artifact/GUCAYYDPvkkBiwntVfJWJA).

- Each `*.dc.html` file is one screen (artboard); `canvas.json` holds their layout on the canvas.
- The files render fully only inside the canvas; open the link above to view or click through them.
- The canvas is the place to edit. After a change there, copy the changed files here so the repository stays in step.
- `png/` holds static images of the main screens with their default tweaks, used as Figures 4.1 – 4.10 of the SRS. They are made by `render_wf.js` (Node.js with `puppeteer` and an installed Chrome), which evaluates the canvas markup (`sc-if`, `sc-for`, `{{ }}`) outside the canvas. From this folder: `node render_wf.js . png Register Main …` (screen names without `.dc.html`).

The mapping of screens to SRS Table 4.1 and the design system are in Section 8 of the [design document](../InternSync_Design.md).
