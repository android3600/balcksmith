# Blacksmith Polish Design

## Goal

Improve the existing single-file mobile prototype so it feels more like a finished score-attack game without changing the core balance formula.

## Scope

- Keep `blacksmith.html` as the only playable app file.
- Preserve the existing roll, satisfaction, score, lives, combo, and one-reroll-per-customer rules.
- Improve first-screen clarity, forging readability, slot quality feedback, and final result presentation.
- Keep all text in Korean.
- Keep offline operation with local assets and visual fallbacks.

## User Experience

The player should immediately understand who arrived, what weapon they brought, what the target satisfaction is, and whether the current slot is worth keeping. The action area should guide the player through four clear decisions: reveal a slot, inspect its quality, optionally reroll once, and confirm.

## Interface Changes

- Add a compact customer request strip showing grade, weapon, target, and remaining gap.
- Add slot quality styling and labels for hit, okay, miss, curse, and jackpot.
- Make the reroll decision clearer by showing the current slot verdict and remaining rerolls near the action buttons.
- Refresh start and game-over overlays so they look like part of the game rather than temporary prototype screens.
- Tighten mobile spacing and typography so important values fit on narrow screens.

## Implementation Approach

Use small, local edits inside `blacksmith.html`. Add helper functions for slot verdict text/class and round progress copy. Reuse existing `attrQuality`, `slotValue`, `partialPct`, and `REROLLS_PER_CUSTOMER` instead of introducing new balance logic. Update `simulate.mjs` only if verification reveals drift or output confusion.

## Verification

- Run `node simulate.mjs` and confirm the original no-reroll sanity check remains close to the SPEC values.
- Open `blacksmith.html` in a browser or automated browser, start a game, reveal a slot, reroll once, confirm all four slots, and verify no layout overlap at mobile width.

## Notes

This directory is not a git repository, so the design cannot be committed here.
