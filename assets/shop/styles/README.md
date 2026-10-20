# Shop Style Variants

`/assets/shop/style.css` is the shared entrypoint used by shopping pages that set `assets_folder="shop"`.

- `base.css` preserves the existing shared `shop.css` look.
- Add a new variant as `styles/<name>.css`.
- Scope overrides to `.shop-main-container.shop-theme-<name>` or `.shop-theme-<name> ...`.
- Add the same `<name>` to `ShopConfig(style_options=...)` in the page module.

Recommended casino-fit variants included here:

- `velvet-noir`: premium red-black lounge with gold accents.
- `champagne-gold`: brighter VIP event feel with warm gold surfaces.
- `neon-onyx`: nightlife/casino-floor energy with cyan and magenta highlights.
- ulma-default: plain Bulma-like baseline with custom shop visuals reset where possible.
