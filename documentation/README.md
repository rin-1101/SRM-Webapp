# Reports App Documentation

This folder explains reusable app templates and UI style selections used by the Dash reports app.

Start here:

- [Shopping Template](shopping-template.md): how `pages/templates/shopping.py` is configured and reused by pages like `pages/BDEAG.py`.
- [UI Style Selections](ui-style-selections.md): how selectable themes under `assets/shop/` work, what each style is for, and how to add another style.

Key paths:

- `pages/templates/`: reusable page templates.
- `pages/BDEAG.py`: BD Earn and Get shopping page example.
- `assets/shop/style.css`: shared style entrypoint for shopping pages.
- `assets/shop/styles/`: selectable UI variants.
- `utils/paths.py`: route constants.
- `config/pages.yaml`: page names and access roles.