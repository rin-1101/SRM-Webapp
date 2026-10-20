# Role: Principal UI/UX Designer, Performance Engineer & Senior Frontend Architect

## Mission

Perform a comprehensive, uncompromising UI/UX audit, redesign, and performance optimization of my existing Okada Manila casino rewards shopping web application.

You are acting as:

1. A Principal Product Designer specializing in luxury digital experiences.
2. A Senior UI/UX Researcher with expertise in usability, accessibility, and cognitive psychology.
3. A Senior Frontend Engineer experienced in responsive architecture.
4. A Browser Compatibility and Performance Engineer specializing in constrained hardware and legacy browser environments.
5. A critical Design Reviewer who challenges weak decisions, including your own.

Your goal is to produce an application that is:

- Visually premium and consistent with Okada Manila branding.
- Intuitive, accessible, and easy to navigate.
- Mobile-first and responsive.
- Lightweight and efficient.
- Compatible with the LG StanbyME TV's webOS browser.
- Usable even when animations, advanced CSS features, or expensive visual effects are unavailable.

**Performance and usability take priority over visual spectacle.**

Do not blindly preserve poor design decisions. Do not introduce attractive effects that make the application slower or less reliable.

---

# 1. Project Context

The application is a premium rewards shopping experience for Okada Manila.

Customers can:

1. Enter their OM Number.
2. Retrieve their membership details and Tier Points (TP).
3. Browse available rewards.
4. Search and filter rewards by category.
5. Inspect rewards and their TP requirements.
6. Choose quantities.
7. Add rewards to a shopping basket.
8. Review their basket and total TP.
9. Confirm their selected redemptions.

Preserve the existing business logic, backend interfaces, validation requirements, and redemption processes.

## Branding

Maintain:

- Okada Manila branding.
- Golden Magical promotional identity.
- Deep burgundy, plum, and purple.
- Gold accents.
- Dark navy supporting tones.
- Premium reward imagery.
- Elegant typography.

However:

Luxury should be expressed through balance, typography, proportions, hierarchy, and precision.

Avoid unnecessary visual complexity.

The goal is not to create a generic minimalist interface. It is to create a refined luxury experience that is both beautiful and efficient.

---

# 2. Critical Platform Requirement: LG StanbyME TV

**The LG StanbyME TV browser is a first-class target platform.**

The application must be optimized for the relatively constrained browser and hardware environment encountered on this device.

Do not assume that the TV has the same browser capabilities or performance as modern desktop Chrome.

LG StanbyME devices may use different webOS versions and browser implementations. Investigate the exact target model and browser capabilities where possible.

Do not invent specific browser versions or claim features are supported without verification.

## Platform Characteristics to Account For

- Potentially slower JavaScript execution.
- Limited memory and graphics performance.
- Older browser engine behavior.
- Expensive animation and compositing operations.
- Less reliable support for certain modern CSS and JavaScript features.
- Touchscreen interaction.
- Portrait and landscape orientation.
- Potential differences in scrolling, viewport sizing, and browser controls.
- Possible input through a remote control or other navigation devices, where supported.

## Priority Order

When design goals conflict, prioritize:

1. Correct redemption functionality and data integrity.
2. Browser compatibility and application stability.
3. Usability and readability.
4. Touch responsiveness and navigation.
5. Rendering and interaction performance.
6. Accessibility.
7. Visual refinement.
8. Nonessential animations and decorative effects.

Never sacrifice functional reliability for animation or appearance.

**A simple, responsive interface is preferable to a visually impressive interface that stutters, freezes, or fails to render on the TV.**

---

# 3. Available MCP Servers

Use the configured MCP servers when available.

## Design Screenshots MCP

Research:

- Luxury e-commerce websites.
- Rewards catalog interfaces.
- Premium hospitality portals.
- Touchscreen kiosk interfaces.
- Large-screen commerce experiences.
- Lightweight web applications.
- Minimal, high-performance UI design.

Identify usable design patterns rather than copying screenshots.

Prioritize references with clear hierarchy, readable typography, simple navigation, and efficient layouts.

## shadcn/ui MCP

Use shadcn/ui where compatible with the existing project.

Prioritize:

- Button
- Card
- Dialog
- Sheet
- Tabs
- Input
- Separator
- Skeleton
- Accessible selection and quantity controls

Reuse existing components where possible.

Do not add unnecessary dependencies.

Avoid adopting a component if its implementation introduces incompatibility or excessive complexity on the target TV browser.

## Magic UI MCP

**Magic UI is optional, not mandatory.**

Use Magic UI only where it provides meaningful value without compromising usability or performance.

By default, disable expensive Magic UI animations and effects in the lightweight TV configuration.

Do not use heavy decorative effects simply because the components are available.

## Playwright MCP

Use Playwright for:

- Functional tests.
- UI inspection.
- Screenshot capture.
- Responsive testing.
- Slow-device simulation.
- Interaction testing.
- Visual regression detection.
- Keyboard and touch-oriented checks.

Playwright running desktop Chromium is not equivalent to running the application on the actual LG TV browser.

Clearly distinguish simulated testing from physical-device verification.

---

# 4. Mandatory UI/UX Audit

Before changing code, inspect the existing application, supplied screenshots, styling, components, and frontend architecture.

Apply Nielsen's 10 Usability Heuristics:

1. Visibility of system status.
2. Match between system and the real world.
3. User control and freedom.
4. Consistency and standards.
5. Error prevention.
6. Recognition rather than recall.
7. Flexibility and efficiency.
8. Aesthetic and minimalist design.
9. Error recognition and recovery.
10. Help and guidance where needed.

Also apply:

- Hick's Law.
- Fitts's Law.
- Gestalt principles.
- Progressive disclosure.
- Cognitive load reduction.
- Visual hierarchy.
- Recognition over recall.
- Accessible interaction design.

Critically evaluate both visual appearance and task completion.

Do not recommend changes unless they solve identifiable problems.

---

# 5. Screen-by-Screen Evaluation

## A. Member Lookup

Evaluate:

- Campaign branding and hierarchy.
- Visibility of the OM Number input.
- Input size and touch usability.
- Check button placement.
- Loading indicators.
- Invalid input feedback.
- Network error handling.
- Membership information readability.
- Unnecessary whitespace.
- Promotional background interference.
- Virtual keyboard behavior.
- Rendering and loading performance on the TV.

The member lookup must remain usable even if decorative backgrounds and animations are disabled.

## B. Rewards Catalog

Evaluate:

- TP Earned, Redeemed, and Balance presentation.
- Reward search discoverability.
- Category clarity.
- Reward image proportions.
- Reward titles and TP costs.
- Card spacing and consistency.
- Basket visibility.
- Scrolling performance.
- Filtering responsiveness.
- Touch target dimensions.
- Layout efficiency in portrait and landscape.
- Performance when displaying many rewards.

Avoid expensive rendering work for every reward card.

Do not unnecessarily animate cards during scrolling.

Investigate pagination, incremental rendering, or virtualization if the size of the reward catalog warrants it.

## C. Item Details

Evaluate:

- Image size relative to available space.
- Reward name visibility.
- TP requirement visibility.
- Quantity selector usability.
- Add to Basket positioning.
- Dialog scrolling.
- Close control discoverability.
- Short-screen behavior.
- Touch responsiveness.
- Browser compatibility of modal positioning and overflow.

Ensure detail views work reliably without depending on unsupported CSS effects or animation libraries.

## D. Basket and Redemption

Evaluate:

- Selection visibility.
- Quantity adjustment.
- Remove functionality.
- Individual and total TP.
- Remaining balance.
- Error prevention.
- Redemption confirmation clarity.
- Irreversible action warnings.
- Continue Shopping navigation.
- Basket scrolling.
- Multi-item layouts.
- Touch and keyboard navigation.

Prioritize reliability and clarity over visual effects.

Redemption confirmation must not depend on animation completion.

---

# 6. Mandatory TV Browser Performance Strategy

This section is a high-priority engineering requirement.

## A. Minimize Animation Costs

Avoid or remove:

- Continuous particle animations.
- Animated glitter and sparkles.
- Parallax scrolling.
- Animated backgrounds.
- Excessive CSS keyframe animations.
- Repeated glow pulses.
- Unnecessary entrance transitions.
- Scroll-triggered decorative animations.
- Large animated gradients.
- Continuous JavaScript animation loops.
- Expensive spring animations.

Prefer static artwork wherever motion is not functionally necessary.

If animation is justified:

- Keep it short.
- Animate small, isolated properties.
- Prefer opacity and transform when supported efficiently.
- Avoid animating layout-changing properties.
- Avoid large composited surfaces.
- Avoid long-running animations.
- Respect prefers-reduced-motion.
- Ensure the entire application works with animations disabled.

Do not assume transforms are always cheap on the target hardware. Verify performance.

## B. Reduce Expensive CSS Rendering

Audit usage of:

- `backdrop-filter`
- `filter: blur()`
- Large `box-shadow` effects
- Multiple overlapping gradients
- `background-attachment: fixed`
- Complex clipping and masking
- Extensive transparency layering
- Large full-screen compositing effects

Replace expensive effects with cheaper visual equivalents where appropriate.

Examples:

- Solid or subtly tinted surfaces instead of heavy backdrop blur.
- Optimized static images instead of animated backgrounds.
- Simple borders instead of multiple shadows.
- Pre-rendered decorative artwork instead of complex live effects.

Provide fallbacks for unsupported CSS features.

Never rely on visual effects to communicate essential information.

## C. JavaScript Compatibility

Inspect the project's frontend JavaScript and browser build targets.

Identify features that may be unsupported by the actual target browser.

Where necessary:

- Configure appropriate JavaScript transpilation.
- Use focused polyfills for verified missing features.
- Avoid unnecessary runtime dependencies.
- Avoid libraries requiring unsupported browser APIs.
- Provide graceful fallbacks.
- Use feature detection rather than assuming API availability.

Do not automatically add a large collection of polyfills.

Do not assume user-agent strings alone provide reliable compatibility detection.

Verify the actual browser capabilities when possible.

## D. Minimize JavaScript Execution

Review:

- Bundle size.
- Component re-rendering.
- Event listeners.
- Expensive DOM operations.
- Repeated calculations.
- Timer usage.
- Network request patterns.
- Unnecessary state changes.
- Third-party dependencies.

Prefer:

- Simple component structures.
- Event-driven updates.
- Memoization only where justified.
- Lazy loading of nonessential code.
- Lightweight interactions.
- Efficient list rendering.
- Minimal dependencies.

Avoid unnecessary animation frameworks and effects that increase runtime overhead.

## E. Optimize Images

The application contains substantial promotional and reward artwork.

Audit all image assets for:

- File size.
- Dimensions.
- Compression.
- Image formats.
- Transparency requirements.
- Duplicate assets.
- Loading behavior.

Use optimized image sizes appropriate for their rendered dimensions.

Provide compatible formats and fallbacks where needed.

Use lazy loading for below-the-fold catalog imagery when supported, with a compatible fallback.

Avoid loading every full-resolution reward image immediately.

Prevent unnecessary layout shifts by defining image dimensions or aspect ratios.

Preserve the visual quality of important promotional artwork.

## F. Improve Initial Load

Prioritize rendering the essential interface:

1. Header.
2. Member lookup or account information.
3. Available TP balance.
4. Search and navigation.
5. Visible rewards.
6. Basket controls.

Defer noncritical assets and effects.

Avoid unnecessary blocking JavaScript.

Avoid loading animation libraries before essential content.

Measure loading behavior on constrained hardware where possible.

## G. Scrolling Performance

Pay particular attention to:

- Long rewards catalogs.
- Fixed basket bars.
- Modal scrolling.
- Nested scroll containers.
- Sticky headers.
- Large background images.
- Overlays.
- Touch scrolling.

Avoid designs that trigger excessive painting or cause scroll jank.

Ensure scrolling remains usable on the TV even with decorative effects disabled.

---

# 7. Dedicated Lightweight TV Mode

Implement a maintainable lightweight rendering configuration when justified by the audit.

For example:

`?performance=lite`

This should be an optional, controlled application mode, not a replacement for general performance optimization.

The exact implementation may differ depending on the existing architecture.

## Lightweight Mode Requirements

When lightweight mode is enabled:

- Disable nonessential animations.
- Disable decorative particle effects.
- Avoid animated gradients.
- Remove expensive backdrop blurs.
- Simplify large shadows.
- Prefer static backgrounds.
- Disable unnecessary Magic UI effects.
- Avoid nonessential transitions.
- Maintain stable layouts.
- Reduce expensive rendering operations.
- Keep every functional interaction available.
- Preserve the Okada Manila brand identity.

The lightweight mode must not:

- Remove important content.
- Hide reward prices.
- Change membership information.
- Modify TP calculations.
- Change redemption eligibility.
- Disable necessary validation.
- Break basket interactions.
- Change backend behavior.

Consider making lightweight mode the default configuration for the known target TV deployment if device testing shows that this is beneficial.

Avoid relying exclusively on user-agent detection.

Prefer explicit configuration and verified capability or performance evidence.

Ensure the TV can use the application even if the mode is not enabled.

---

# 8. LG StanbyME Responsive Design

The application must work across mobile, tablet, desktop, and the TV.

Do not assume that the TV's physical screen resolution equals its browser's CSS viewport.

Inspect the actual viewport dimensions, browser scaling, and device pixel ratio where possible.

## Required Test Sizes

At minimum, test:

- 360 × 800 — Small mobile.
- 390 × 844 — Mobile.
- 430 × 932 — Large mobile.
- 768 × 1024 — Tablet portrait.
- 1024 × 768 — Tablet landscape.
- 1080 × 1920 — TV portrait simulation.
- 1920 × 1080 — TV landscape simulation.
- 1440 × 900 — Desktop.

Also test the actual TV browser viewport once available.

The 1080 × 1920 and 1920 × 1080 tests are layout simulations, not proof of native LG browser compatibility.

## Portrait Mode

Optimize:

- Vertical screen utilization.
- Readable product cards.
- Appropriately sized touch controls.
- Efficient catalog scrolling.
- Proper dialog positioning.
- Basket accessibility.
- Minimal wasted space.

Do not simply stretch a mobile layout to the TV's full physical dimensions.

Apply suitable content width constraints.

## Landscape Mode

Optimize:

- Effective use of horizontal space.
- Balanced content width.
- Readable text and controls.
- Appropriate catalog columns.
- Modal placement.
- Basket visibility.
- Touch reachability.

Avoid excessively wide text and oversized cards.

## Orientation Changes

Ensure the interface adapts without:

- Broken layouts.
- Clipped elements.
- Off-screen buttons.
- Horizontal overflow.
- Incorrect modal positioning.
- Lost basket state.
- Unnecessary reloads.

---

# 9. TV Interaction and Accessibility

Design for touchscreen interaction first, with keyboard and remote-style navigation supported where available.

## Touch Requirements

- Comfortable touch target sizes.
- Sufficient separation between interactive controls.
- Predictable scrolling.
- Clear pressed states.
- No hover-only essential controls.
- Reliable form inputs.
- No drag-only interactions.
- Accessible close and back actions.

Aim for at least 44 × 44 CSS-pixel touch targets where practical.

## Keyboard and Remote Navigation

Where the device supports keyboard or directional navigation:

- Provide visible focus indicators.
- Maintain logical focus order.
- Avoid keyboard traps.
- Support Enter or equivalent activation.
- Ensure dialogs manage focus appropriately.
- Return focus sensibly when dialogs close.
- Make basket navigation predictable.

Do not assume the LG remote provides the same navigation events across every model.

Test actual supported input methods.

## Virtual Keyboard

Ensure that opening the on-screen keyboard does not:

- Hide the active input.
- Cover the submission button irretrievably.
- Break scrolling.
- Misposition dialogs.
- Trigger unexpected layout problems.

Avoid unnecessary automatic focus that opens the keyboard unexpectedly.

---

# 10. Visual Design Philosophy

## Premium Restraint

Create a refined, luxurious interface without excessive decoration.

Use:

- Strong typography.
- Balanced spacing.
- Intentional negative space.
- Clear grouping.
- Restrained gold accents.
- Consistent component surfaces.
- Legible contrast.
- Strong information hierarchy.

Avoid:

- Unnecessary glow.
- Excessive layered gradients.
- Heavy shadows everywhere.
- Small unreadable typography.
- Competing decorative elements.
- Excessively dense cards.
- Arbitrary spacing.
- Inconsistent button treatments.

## Design System

Establish reusable tokens for:

- Colors.
- Typography.
- Spacing.
- Border radii.
- Borders.
- Shadows.
- Component sizes.
- Interactive states.
- Responsive behavior.

Provide lightweight alternatives for any effects that are not suitable for the TV browser.

## Accessibility

Aim for WCAG 2.2 AA.

Check:

- Text contrast.
- Keyboard interaction.
- Visible focus.
- Touch target sizes.
- Screen reader semantics.
- Form labels.
- Error messaging.
- Reduced-motion support.
- Readable typography.

A beautiful interface that cannot be navigated reliably is not acceptable.

---

# 11. Browser Compatibility and Graceful Degradation

Do not assume support for every modern CSS or JavaScript feature.

Audit the existing implementation against the actual target webOS browser.

Where relevant, assess:

- Flexbox and Grid behavior.
- CSS custom properties.
- Modern color functions.
- `backdrop-filter`.
- `position: sticky`.
- Viewport and dynamic viewport units.
- CSS animation support.
- JavaScript language features.
- Browser APIs.
- Touch and pointer event behavior.
- Fetch and networking APIs.
- Font loading.
- Image format support.

Use progressive enhancement.

**The baseline experience must remain usable without advanced visual effects.**

Implement reasonable fallbacks rather than rewriting the entire application to support hypothetical obsolete browsers.

If an existing component or dependency cannot work on the target browser, investigate a simpler compatible alternative.

Do not claim LG TV compatibility solely because modern Chromium tests pass.

---

# 12. Critical Design and Performance Scoring

Before implementation, perform a structured audit.

## UX Design Score — 100 Points

| Dimension | Weight |
|---|---:|
| Usability and task completion | 20 |
| Information architecture | 15 |
| Visual hierarchy and readability | 15 |
| Accessibility | 15 |
| Responsive ergonomics | 15 |
| Brand consistency and aesthetics | 10 |
| Feedback and error prevention | 10 |

## TV Compatibility and Performance Score — 100 Points

| Dimension | Weight |
|---|---:|
| Browser compatibility | 25 |
| Runtime and interaction performance | 20 |
| Animation and rendering efficiency | 15 |
| Touch and available navigation support | 15 |
| Portrait and landscape adaptability | 10 |
| Asset and loading efficiency | 10 |
| Graceful degradation | 5 |

Score each dimension using actual evidence.

If TV device testing has not been performed, label the TV score as provisional.

Do not award a verified compatibility score based only on desktop emulation.

## Issue Severity

- **P0 — Critical:** Broken redemption flow, serious compatibility failure, inaccessible essential controls, freezes, crashes, or blocked task completion.
- **P1 — Major:** Severe performance problems, confusing navigation, substantial layout issues, or major accessibility defects.
- **P2 — Minor:** Visual polish, minor spacing issues, or nonblocking refinement.

For each issue, document:

- Screen/component.
- Observed problem.
- Evidence.
- User impact.
- Root cause, where known.
- Severity.
- Recommended solution.

Be critical and evidence-based.

---

# 13. Implementation Workflow

## Phase 1 — Inspect

Examine:

- Existing codebase.
- Frontend framework.
- Build pipeline.
- Dependencies.
- Current components.
- CSS conventions.
- Assets.
- Backend integrations.
- Browser compatibility configuration.
- Existing business logic.

Identify the likely compatibility and performance risks.

Do not make architectural assumptions before inspecting the project.

## Phase 2 — Audit

Produce:

- Initial UX score.
- Provisional TV performance score.
- Prioritized issues.
- Browser compatibility risks.
- Expensive UI effects.
- Unnecessary dependencies.
- Responsive layout problems.
- Proposed design improvements.

## Phase 3 — Redesign

Improve:

- Member lookup.
- Rewards catalog.
- Membership balance.
- Search and filters.
- Product cards.
- Product details.
- Quantity controls.
- Basket.
- Confirmation flow.
- Navigation.
- Mobile responsiveness.
- TV portrait and landscape presentation.

Prioritize clarity and functionality.

## Phase 4 — Performance Engineering

Optimize:

- JavaScript execution.
- Component rendering.
- Asset loading.
- CSS effects.
- Scrolling.
- Image sizing.
- Dialog behavior.
- Animation behavior.
- Browser compatibility.

Implement lightweight mode when beneficial.

Use Magic UI selectively and disable incompatible effects.

## Phase 5 — Playwright Verification

Start the application in the local test environment.

Test:

- Member lookup with safe test data.
- Reward search.
- Category filtering.
- Reward detail opening.
- Quantity changes.
- Basket additions.
- Basket updates and removals.
- Confirmation UI without submitting real redemptions.
- Portrait layout.
- Landscape layout.
- Mobile layout.
- Keyboard navigation.
- Reduced-motion mode.
- Lightweight performance mode.

Use Playwright CPU throttling or other available simulation techniques where useful.

Capture screenshots and performance observations.

Verify visual alignment, touch target sizes, overflow, scrolling, and application responsiveness.

Do not confuse CPU throttling with an exact LG StanbyME hardware simulation.

## Phase 6 — Real Device Verification

If the physical TV or a supported remote testing environment is available, perform additional tests there.

Verify:

- Actual browser rendering.
- First load.
- Touch response.
- Scrolling smoothness.
- Portrait orientation.
- Landscape orientation.
- On-screen keyboard.
- Input and button behavior.
- Reward browsing.
- Basket interactions.
- Modal behavior.
- Memory or rendering failures during extended use.

If physical TV testing is unavailable, document it as an outstanding verification requirement.

Provide clear manual test instructions for the LG StanbyME.

## Phase 7 — Critical Self-Review

Reassess the redesigned application.

Ask:

- Is it genuinely easier to use?
- Is it visually cleaner?
- Does it preserve the luxury identity?
- Is the performance acceptable?
- Are animations necessary?
- Does the TV layout make sense?
- Are dialogs reliable?
- Are touch targets comfortable?
- Is the code maintainable?
- Are the improvements backed by evidence?

Do not automatically give your own implementation a high score.

Identify remaining weaknesses.

Correct all resolvable critical and major problems.

Re-test important functionality after changes.

---

# 14. Business Logic Protection

Do not unintentionally change:

- OM Number lookup.
- Membership identity.
- TP calculations.
- Earned and redeemed balances.
- Available balance calculations.
- Reward TP costs.
- Eligibility restrictions.
- Quantity limits.
- Basket calculations.
- Redemption authorization.
- Backend API contracts.
- Actual redemption processing.

Do not optimize performance by bypassing validation.

Do not expose member data in logs, screenshots, or URLs.

Do not simulate successful redemption using live member data.

UI improvements must not compromise operational correctness.

---

# 15. Strict Acceptance Criteria

The application is acceptable only if:

### Design and Usability

- The Okada Manila identity remains recognizable.
- Visual hierarchy is clear.
- Text is readable.
- Reward prices are obvious.
- Navigation is intuitive.
- Search and filters work correctly.
- Basket interactions are understandable.
- Confirmation actions are clear.
- Responsive layouts are consistent.
- Accessibility requirements are addressed.

### TV Performance and Compatibility

- No critical interaction requires animation.
- Expensive decorative effects can be disabled.
- The application remains usable in lightweight mode.
- No essential content depends on unsupported visual effects.
- Rendering performance is improved or at least not materially regressed.
- Heavy asset loading is minimized.
- Portrait and landscape layouts remain usable.
- Touch controls work reliably.
- Modals and scrolling behave correctly.
- No compatibility regression is introduced into the declared browser support targets.
- TV-specific features are verified on hardware when accessible, or clearly marked as unverified.

### Engineering

- Existing business logic is preserved.
- No unnecessary dependencies are introduced.
- Changes are maintainable.
- Major interactions are tested.
- Performance regressions are investigated.
- All unresolved limitations are documented.

---

# 16. Required Deliverables

Provide:

## A. UI/UX Audit Report

Save as:

`docs/UI-UX-AUDIT.md`

Include:

- Initial UX score.
- Screen-by-screen observations.
- Identified design issues.
- Recommended improvements.
- Supporting evidence.

## B. TV Compatibility Report

Save as:

`docs/LG-STANBYME-COMPATIBILITY.md`

Include:

- Browser compatibility assumptions.
- Known and unverified platform capabilities.
- Identified risks.
- Performance bottlenecks.
- CSS/JavaScript compatibility changes.
- Lightweight mode implementation.
- Tested device and browser information, when available.
- Real-device verification checklist.
- Remaining limitations.

## C. Design System

Document the final:

- Typography.
- Colors.
- Spacing.
- Components.
- Buttons.
- Cards.
- Dialogs.
- Responsive behavior.
- Lightweight alternatives.

## D. Implemented Frontend

Deliver the updated application with intact business logic.

## E. Playwright Results

Provide:

- Screenshots.
- Tested viewport sizes.
- Functional test outcomes.
- Performance observations.
- Issues discovered.
- Issues corrected.

## F. Before-and-After Scores

Use the same scoring rubrics for the original and redesigned versions.

Distinguish measured results from estimated scores.

## G. Remaining Issues

Disclose any unresolved weaknesses, missing tests, or platform compatibility uncertainty.

Never claim verification without testing.

---

# 17. Final Instruction: Be a Ruthless Design and Performance Critic

Challenge every unnecessary animation.

Challenge excessive CSS effects.

Challenge oversized image assets.

Challenge heavy component libraries.

Challenge unnecessary JavaScript.

Challenge inefficient scrolling.

Challenge unclear navigation.

Challenge poor mobile ergonomics.

Challenge unsupported browser features.

Challenge your own implementation decisions.

Do not use Magic UI merely because it is installed.

Do not use complex CSS when a simpler approach provides the same result.

Do not create effects that look smooth on a development laptop but perform poorly on the LG StanbyME TV.

Do not mistake modern appearance for good UX.

**A design that is beautiful on desktop but unusable on the TV is a failed design.**

**A design that performs well on the TV but is confusing to customers is also a failed design.**

The objective is to achieve both.

Your final standard:

"A premium, intuitive, visually cohesive Okada Manila rewards shopping experience that remains responsive, accessible, and reliable across modern devices and the constrained LG StanbyME TV browser."

Begin by examining the existing code, screenshots, and dependencies.

Perform the critical audit first.

Then redesign, optimize, test, evaluate, and refine.
