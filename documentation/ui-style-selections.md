# UI Style Selections

Shopping pages can expose multiple UI styles without duplicating page logic. The page keeps one layout and switches CSS theme classes on the main container.

## How The Selector Works

In `ShopConfig`, configure:

```python
style_options=(
    "base",
    "minimalism",
    "liquid-glass",
    "velvet-noir",
    "champagne-gold",
    "neon-onyx",
    "bulma-default",
),
default_style="base",
```

The template renders a radio-style picker only when more than one style is available. Selecting an option changes the main container class:

```text
shop-main-container shop-theme-<style-name>
```

CSS files then scope overrides to that class.

## Asset Layout

Shared shopping styles live here:

```text
assets/shop/style.css
assets/shop/shop.css
assets/shop/styles/base.css
assets/shop/styles/minimalism.css
assets/shop/styles/liquid-glass.css
assets/shop/styles/velvet-noir.css
assets/shop/styles/champagne-gold.css
assets/shop/styles/neon-onyx.css
assets/shop/styles/bulma-default.css
```

`assets/shop/style.css` imports the shared base engine and all available theme variants. `assets/shop/shop.css` is the current shared shop stylesheet. `base.css` intentionally preserves the current look.

## Current Styles

`base`

- The current shared shopping UI.
- Dark casino palette with gold accent treatment.
- Best default for production because it preserves the existing visual language.

`minimalism`

- White-primary, simple, and software-product-like rather than event-poster-like.
- Warm white surfaces with subtle plum accents, simpler cards, footer, modal, and selector treatment.
- Good for admin-heavy or repeat-use pages where clarity matters more than event flair.

`liquid-glass`

- Frosted translucent surfaces with blur and shine.
- Modern premium kiosk/app feel.
- Good for luxury event screens, but test readability over bright backgrounds.

`velvet-noir`

- Recommended casino style.
- Red-black lounge atmosphere with gold accents.
- Good for VIP and premium table-game adjacent campaigns.

`champagne-gold`

- Recommended casino style.
- Warmer, brighter VIP event aesthetic.
- Good for rewards, luxury giveaway, and premium retail tie-ins.

`neon-onyx`

- Recommended casino style.
- Dark base with cyan and magenta highlights.
- Good for nightlife, gaming floor, electronic raffle, or high-energy events.


`bulma-default`

- Strips back the shared shopping visual enhancements as much as the current template markup allows.
- Uses Bulma-like defaults for buttons, inputs, cards, modal cards, and footer treatment.
- Good as a plain baseline when comparing custom themes or debugging layout behavior.
## Adding A New Style

1. Create a file:

```text
assets/shop/styles/<style-name>.css
```

Use lowercase kebab-case, for example `royal-sapphire.css`.

2. Import it from `assets/shop/style.css`.

```css
@import url("/assets/shop/styles/royal-sapphire.css");
```

3. Scope the CSS to the generated theme class.

```css
.shop-main-container.shop-theme-royal-sapphire {
    --shop-accent-1: #eef6ff;
    --shop-accent-2: #79aee8;
    --shop-accent-3: #2f5f9f;
    --shop-accent-4: #17345f;
    --shop-base-1: #172235;
    --shop-base-2: #101929;
    --shop-base-3: #08111f;
    --shop-base-4: #040912;
    --shop-border-accent: rgba(121, 174, 232, 0.42);
}

.shop-theme-royal-sapphire .shop-card {
    border-color: rgba(121, 174, 232, 0.38);
}
```

4. Add the style name to the page config.

```python
style_options=("base", "royal-sapphire")
```

## Design Guidelines

Prefer CSS custom properties first. Most color changes should be done by overriding `--shop-*` variables on `.shop-main-container.shop-theme-<name>`.

Keep styles readable. Item names, costs, TP balances, warning text, and modal actions must remain legible over the background image.

Avoid one-off layout changes inside a theme unless the page still works on mobile. Theme files should mostly change color, surface treatment, border, shadow, and button feel.

Use `base` as the fallback. If a theme is experimental, keep it in `style_options` after `base` so the current production look remains the default.

## Suggested Future Casino Styles

`royal-sapphire`

- Deep navy, sapphire, and pale gold.
- Feels premium and calmer than neon.
- Good for luxury hotel, resort, or premium membership campaigns.

`emerald-room`

- Emerald green, black lacquer, and brass.
- Classic casino table-game signal without becoming too loud.
- Good for baccarat, poker, or high-limit inspired events.

`crystal-palace`

- Cool silver, pearl, and subtle blue highlights.
- Fits high-end raffle or jewelry/luxury prize displays.
- Good when product photos should remain the visual focus.