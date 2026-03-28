# Decisions

Track triage outcomes for August-originated feedback.

## Format

- Issue: `#<id>`
- Status: accepted | deferred | wontfix
- Reason:
- Planned milestone:

## Entries

- Issue: `#10`
  Status: accepted
  Reason: Latest consolidated qualitative review; use as primary input for current implementation cycle.
  Planned milestone: M1 - Core Loop

- Issue: `#9`
  Status: deferred
  Reason: Superseded by newer review issue #10 with same core findings.
  Planned milestone: M1 - Core Loop

- Issue: `#8`
  Status: wontfix
  Reason: Low-information review generated during parser stabilization; superseded by later high-signal reports.
  Planned milestone: M1 - Core Loop

- Issue: `#7`
  Status: accepted
  Reason: Clarifying lock/key behavior improves puzzle fairness and player understanding.
  Planned milestone: M1 - Core Loop

- Issue: `#6`
  Status: accepted
  Reason: Coin utility is currently missing and directly impacts reward and agency.
  Planned milestone: M1 - Core Loop

- Issue: `#5`
  Status: accepted
  Reason: Environmental descriptions need stronger identity and atmosphere to improve engagement.
  Planned milestone: M1 - Core Loop

- Issue: `#4`
  Status: deferred
  Reason: Overlaps with #7; fold key-role clarity into the same lock-mechanic improvements.
  Planned milestone: M1 - Core Loop

- Issue: `#3`
  Status: accepted
  Reason: Duplicate of #6 but still valid bug framing; resolve by implementing coin purpose.
  Planned milestone: M1 - Core Loop

- Issue: `#2`
  Status: wontfix
  Reason: Could not reproduce inconsistent lock state; path behavior currently depends on possessing key as designed.
  Planned milestone: M1 - Core Loop

- Issue: `#1`
  Status: deferred
  Reason: Earliest review is superseded by later review set (#9/#10).
  Planned milestone: M1 - Core Loop

- Issue: `#20`
  Status: accepted
  Reason: Latest consolidated review after core-loop improvements; use as primary input for this cycle.
  Planned milestone: M1 - Core Loop

- Issue: `#19`
  Status: accepted
  Reason: Water-echo motif is a good narrative hook and should be developed into meaningful world flavor.
  Planned milestone: M2 - Puzzle Depth

- Issue: `#18`
  Status: accepted
  Reason: Giving the idol a clearer gameplay purpose strengthens reward structure and long-term goals.
  Planned milestone: M2 - Puzzle Depth
  Implemented: Idols can be placed on the Treasury pedestal, revealing hidden alcove with ancient verses.

- Issue: `#17`
  Status: deferred
  Reason: Lamp and coin now have a complete primary loop; treat broader lamp utility as future feature work, not a current bug.
  Planned milestone: M2 - Puzzle Depth

- Issue: `#16`
  Status: deferred
  Reason: Superseded by newer consolidated review #20.
  Planned milestone: M1 - Core Loop

- Issue: `#15`
  Status: deferred
  Reason: Duplicates narrative theme request in #19.
  Planned milestone: M2 - Puzzle Depth

- Issue: `#14`
  Status: deferred
  Reason: Duplicates idol-purpose request in #18.
  Planned milestone: M2 - Puzzle Depth

- Issue: `#13`
  Status: accepted
  Reason: Treasury can support richer interaction and a secondary challenge to improve depth.
  Planned milestone: M2 - Puzzle Depth

- Issue: `#12`
  Status: deferred
  Reason: Same concern as #17 from earlier commit; track as future feature exploration.
  Planned milestone: M2 - Puzzle Depth

- Issue: `#11`
  Status: deferred
  Reason: Could not reproduce a deterministic idol-spawn bug; monitor in future runs before treating as engine defect.
  Planned milestone: M1 - Core Loop

- Issue: `#21`
  Status: deferred
  Reason: Latest consolidated review at commit a39242bfeba6; same findings as #20 (idol inconsistency, lamp utility). Supersedes #20 as primary reference; action items already tracked in accepted issues #18 (idol purpose) and #17 (lamp utility deferred).
  Planned milestone: M2 - Puzzle Depth

- Issue: `#22`
  Status: accepted
  Reason: Latest consolidated review (3.33/5); confirms idol placement working (#18) and highlights remaining gaps. Narrative fit HIGH (lore expansion fits world), Location fit HIGH (Foyer glyphs, Treasury pedestal). Will implement: lamp reveals Foyer inscriptions, tablet contains cryptic verses.
  Planned milestone: M2 - Puzzle Depth
  Implemented: Lamp reveals faded inscriptions on Foyer walls; tablet grants cryptic verses hinting at broader purpose.

- Issue: `#23`
  Status: deferred
  Reason: Latest review at commit e23eae75e002; same consolidated findings as #22. Supersedes all prior reviews. Remaining action items: fix idol duplication bug (idol appears twice in Treasury after placement), develop water echoes into a lamp interaction in the cavern.
  Planned milestone: M2 - Puzzle Depth

- Issue: `#24`
  Status: deferred
  Reason: Same findings as #22; superseded by #25 as primary reference.
  Planned milestone: M2 - Puzzle Depth

- Issue: `#25`
  Status: accepted
  Reason: Latest consolidated review at current commit 5adceaa3 (3.33/5). Narrative fit HIGH, Location fit HIGH. Confirms prior improvements working (lamp inscriptions, water echoes, idol pedestal, tablet verses). Remaining: idol description persistence after placement. Fixed: Treasury now renders contextual description (idol in shadows vs. rests upon pedestal).
  Planned milestone: M2 - Puzzle Depth
  Implemented: Treasury look() now generates contextual room description based on idol_placed flag; "ancient idol watches from the shadows" only shown when idol is still in room items; "idol rests upon the pedestal" shown after placement.

- Issue: `#26`
  Status: accepted
  Reason: Latest consolidated review at current commit 16d67c1a (3.33/5). Narrative fit HIGH, Location fit HIGH. Confirms improvements (lamp reveals inscriptions, pedestal puzzle, tablet verses). Remaining: consistent idol presence across all scenarios.
  Planned milestone: M2 - Puzzle Depth

- Issue: `#21`
  Status: deferred
  Reason: Same consolidated findings as #20/#25; superseded by #25 as primary reference.
  Planned milestone: M2 - Puzzle Depth

- Issue: `#27`
  Status: deferred
  Reason: Consolidated review at commit 06fde8f5bbc3 (3.33/5); same findings as #26. Narrative fit HIGH, Location fit HIGH. No new actionable items beyond those already accepted (#18 idol purpose, #19 water echoes, #22 lamp inscriptions, #25 contextual treasury).
  Planned milestone: M2 - Puzzle Depth

- Issue: `#28`
  Status: deferred
  Reason: Consolidated review at commit 4fadb1164eac (3.33/5); same findings as #27/#26. No new actionable items beyond prior accepted issues. Game is functionally complete for M2 scope.
  Planned milestone: M2 - Puzzle Depth

- Issue: `#29`
  Status: deferred
  Reason: Consolidated review at current commit cd17278cc9 (3.33/5); same findings as #28/#27. No new actionable items beyond prior accepted issues (#18 idol purpose, #19 water echoes, #22 lamp inscriptions). Game is functionally complete for M2 scope.
  Planned milestone: M2 - Puzzle Depth

- Issue: `#30`
  Status: accepted
  Reason: Bug report about idol inconsistency across scenarios; narrative fit HIGH (idol has purpose now per #18), location fit HIGH (Treasury). The idol is hardcoded in treasury room at build_world, so inconsistency likely from test script variation; will verify determinism and add explicit room state test.
  Planned milestone: M2 - Puzzle Depth
  Implemented: Verified idol is deterministic in treasury via build_world; added room state test to prevent regressions.

- Issue: `#31`
  Status: wontfix
  Reason: Duplicate of #17/#12 regarding lamp utility. Lamp now reveals Foyer inscriptions and cavern water echoes; full lamp expansion deferred to future milestone.
  Planned milestone: M3 - Extended Items

- Issue: `#32`
  Status: deferred
  Reason: Duplicate of #18 which is already accepted and implemented. Idol has purpose (reveals alcove with verses) in current build.
  Planned milestone: M2 - Puzzle Depth

- Issue: `#33`
  Status: accepted
  Reason: Feature suggestion for glyph decoding puzzle in Foyer; narrative fit HIGH (foyer already has glyphs), location fit HIGH (Foyer). Will integrate with existing lamp-inscriptions feature: use lamp to reveal glyphs, then examine them to decode a clue for the Treasury.
  Planned milestone: M2 - Puzzle Depth
  Implemented: Added examine command for glyphs; lamp reveals inscriptions, examine glyphs provides decoding hints referencing tablet and Treasury puzzle.

- Issue: `#34`
  Status: accepted
  Reason: Feature suggestion for water echoes shortcut at Trailhead via listen command; narrative fit HIGH (water echoes motif exists), location fit HIGH (Trailhead is starting area). Will add listen command that reveals hidden passage at Trailhead.
  Planned milestone: M2 - Puzzle Depth
  Implemented: Added listen command; listening at Trailhead reveals hidden passage east leading to Hidden Passage room with journal.

- Issue: `#35`
  Status: deferred
  Reason: Qualitative review at 3.33/5; mentions lingering idol inconsistencies and limited depth. Same concerns addressed by accepted issues #30, #33, #34. No new actionable items.
  Planned milestone: M2 - Puzzle Depth

- Issue: `#36`
  Status: deferred
  Reason: Qualitative review at 3.0/5 at commit e5ca67659093; no clear assessment provided for Environment Richness or Description Vividness. No new actionable items beyond prior accepted issues.
  Planned milestone: M2 - Puzzle Depth

- Issue: `#37`
  Status: deferred
  Reason: Qualitative review at 3.0/5 at commit ad70ac024794; no clear assessment provided for Environment Richness or Description Vividness. No new actionable items beyond prior accepted issues.
  Planned milestone: M2 - Puzzle Depth

- Issue: `#38`
  Status: accepted
  Reason: Minor polish improvement to player experience. More informative error messages reduce friction. Narrative fit LOW (gameplay message only), location fit N/A. Quick win.
  Planned milestone: M3 - Polish
  Implemented: Improved error messages for use lamp/key/coin with contextual hints about where items might be found.

- Issue: `#39`
  Status: deferred
  Reason: "There is no idol here" is technically correct since idol is in Treasury. Ambiguity arises from thematic naming, but fix would be low-impact.
  Planned milestone: M3 - Polish

- Issue: `#40`
  Status: deferred
  Reason: "use key" is sufficient and consistent with game style. Explicit "use key on gate" would add complexity without clear player value.
  Planned milestone: M3 - Polish

- Issue: `#45`
  Status: accepted
  Reason: Minor consistency fix for error messaging. Improved "take" error messages to provide contextual hints.
  Planned milestone: M3 - Polish
  Implemented: Enhanced take error messages with hints (e.g., "You recall seeing a similar stone figure deeper within the ruins" for idol).

- Issue: `#46`
  Status: wontfix
  Reason: Discovery mechanic is intentional game design - players must experiment. Adding explicit clues would reduce exploration reward.
  Planned milestone: N/A

- Issue: `#47`
  Status: wontfix
  Reason: Room description already states "A locked bronze gate blocks the northern tunnel" which informs the player of the lock requirement.
  Planned milestone: N/A

- Issue: `#52`
  Status: wontfix
  Reason: Inconsistent messages ("You do not have X" vs "You are not carrying X") are minor stylistic differences; both are clear. Would require broader message standardization effort.
  Planned milestone: M3 - Polish

- Issue: `#53`
  Status: deferred
  Reason: Minor inconsistency between "You see nothing useful" and hidden coin reveal. Not a gameplay blocker; could be addressed by revising cavern initial description.
  Planned milestone: M3 - Polish

- Issue: `#54`
  Status: wontfix
  Reason: Truncated text bug not reproducible at current commit 8ba5478. Pedestal reveal text is complete ("revealing a weathered tablet. Strange symbols cover its surface, hinting at a purpose beyond these ruins.").
  Planned milestone: N/A

- Issue: `#59`
  Status: wontfix
  Reason: Bronze gate lock state bug not reproducible at current commit. Gate correctly shows "stands open" after using key and remains accessible on return.
  Planned milestone: N/A

- Issue: `#60`
  Status: wontfix
  Reason: Same as #54 - truncated text bug not reproducible. Pedestal reveal is complete.
  Planned milestone: N/A

- Issue: `#61`
  Status: wontfix
  Reason: Same as #59 - gate lock state working correctly after using key.
  Planned milestone: N/A

- Issue: `#62`
  Status: deferred
  Reason: Duplicates #33 which is already accepted and implemented. Glyph examination is integrated with lamp/tablet mechanics.
  Planned milestone: M2 - Puzzle Depth

- Issue: `#63`
  Status: deferred
  Reason: Alternative lever mechanic is interesting but adds complexity. Current key-gate puzzle is clear and functional. Could be future expansion if needed.
  Planned milestone: M4 - Alternative Paths

- Issue: `#64`
  Status: wontfix
  Reason: Journal lore item is already implemented in Hidden Passage per #34. Journal provides builders' history and prophecy hints.
  Planned milestone: N/A

- Issue: `#65`
  Status: deferred
  Reason: Qualitative review at 3.83/5; notes good atmosphere and puzzles but suggests deeper lore and more branching. Same themes addressed by accepted issues. No new actionable items beyond prior scope.
  Planned milestone: M4 - Content Expansion

- Issue: `#66`
  Status: wontfix
  Reason: Same as #59/#61 - gate lock state working correctly at current commit. Bug not reproducible.
  Planned milestone: N/A

- Issue: `#67`
  Status: wontfix
  Reason: Same as #54/#60 - truncated text bug not reproducible. Pedestal reveal text is complete.
  Planned milestone: N/A

- Issue: `#50`
  Status: accepted
  Reason: Feature suggestion to expand Hidden Passage. Current hidden passage is functional (revealed via listen, contains journal). Will add a second room "Ancient Alcove" to expand exploration. Narrative fit HIGH (adds lore depth), Location fit HIGH (extends hidden_passage).
  Planned milestone: M2 - Puzzle Depth
  Implemented: Added "Ancient Alcove" room east of Hidden Passage; contains a small altar with inscription that hints at idol placement purpose.

- Issue: `#51`
  Status: deferred
  Reason: Qualitative review at 3.17/5 at commit 72a1d70311e6. Notes good atmosphere and puzzles but suggests deeper lore. Same themes addressed by accepted issues. No new actionable items beyond prior scope.
  Planned milestone: M2 - Puzzle Depth

- Issue: `#56`
  Status: deferred
  Reason: Feature suggestion for multi-item puzzle integration. Partially implemented via existing lamp/tablet/coin/idol mechanics. Full combination puzzle deferred to future milestone for scope control.
  Planned milestone: M3 - Extended Items

- Issue: `#57`
  Status: wontfix
  Reason: Feature suggestion for environmental interaction puzzle. Already implemented: listen at Trailhead reveals hidden passage, use lamp in cavern reveals coin, use lamp in foyer reveals inscriptions.
  Planned milestone: N/A

- Issue: `#58`
  Status: deferred
  Reason: Qualitative review at 2.5/5. Notes promising atmosphere but suggests need for deeper lore and more branching. Same themes addressed by accepted issues. No new actionable items beyond prior scope.
  Planned milestone: M4 - Content Expansion

- Issue: `#68`
  Status: wontfix
  Reason: Inspect command already implemented. Parser maps "inspect" to "examine" action (line 57 of parser.py). Examine provides detailed room/item info.
  Planned milestone: N/A

- Issue: `#55`
  Status: deferred
  Reason: Feature suggestion for lore expansion through readable items. Duplicate of lore already implemented (#34 journal, #50 altar inscription, #22 lamp reveals inscriptions). All readable items accessible via examine/use commands.
  Planned milestone: M4 - Content Expansion

- Issue: `#49`
  Status: deferred
  Reason: Feature suggestion for multi-stage Treasury puzzle. Current Treasury has two stages (coin pedestal -> tablet, idol placement -> alcove). Further expansion deferred to future milestone for scope control.
  Planned milestone: M4 - Content Expansion

- Issue: `#48`
  Status: deferred
  Reason: Feature suggestion for lore fragments and environmental storytelling. Duplicate of #34/#42. Journal, altar inscription, glyph examination already implemented. Water echoes motif developed throughout.
  Planned milestone: M4 - Content Expansion

- Issue: `#44`
  Status: deferred
  Reason: Qualitative review at 3.5/5 at commit ebb3d45ede5f. Notes solid foundation with functional puzzles but suggests more evocative descriptions. Same themes addressed by prior accepted issues. No new actionable items.
  Planned milestone: M2 - Puzzle Depth

- Issue: `#43`
  Status: deferred
  Reason: Feature suggestion for more interactive elements. Interactive elements already implemented: examine (glyphs, altar, journal, tablet, idol, pedestal), listen (reveals hidden passage), use (lamp/key/coin/idol interactions).
  Planned milestone: M3 - Extended Items

- Issue: `#42`
  Status: deferred
  Reason: Feature suggestion for optional narrative lore fragments. Duplicate of #34/#48. Journal, altar inscription, tablet verses all provide optional lore. Water echoes motif provides environmental storytelling.
  Planned milestone: M4 - Content Expansion

- Issue: `#41`
  Status: deferred
  Reason: Feature suggestion for expanded environmental descriptions with sensory details. Descriptions already rich with sensory language (dripping water, amber light, shifting glyphs, dust motes). Minor expansion deferred for scope control.
  Planned milestone: M3 - Extended Items

- Issue: `#96`
  Status: wontfix
  Reason: Lamp-activated hidden coin in cavern is already implemented (use lamp in cavern reveals coin).
  Planned milestone: N/A

- Issue: `#95`
  Status: wontfix
  Reason: Interactive glyph clue system already implemented. Lamp reveals inscriptions, examine glyphs provides contextual hints.
  Planned milestone: N/A

- Issue: `#94`
  Status: wontfix
  Reason: Echo chamber puzzle already implemented. Listen at Trailhead reveals hidden passage; lamp in cavern reveals water echoes.
  Planned milestone: N/A

- Issue: `#92`
  Status: wontfix
  Reason: Hidden water passage already implemented. Listen at Trailhead reveals hidden passage to east.
  Planned milestone: N/A

- Issue: `#93`
  Status: wontfix
  Reason: Interactive glyph in foyer already implemented. Examine glyphs after lamp reveals decoding hints.
  Planned milestone: N/A

- Issue: `#91`
  Status: accepted
  Reason: Feature suggestion for lamp revealing hidden coin on pedestal. Currently lamp has no effect in Treasury. Narrative fit HIGH, location fit HIGH. Will implement lamp interaction in Treasury that reveals hidden details.
  Planned milestone: M3 - Polish
  Implemented: Using lamp in Treasury reveals a hidden coin resting near the pedestal base.

- Issue: `#90`
  Status: wontfix
  Reason: Idol-triggered secret compartment already implemented. Placing idol on pedestal reveals hidden alcove.
  Planned milestone: N/A

- Issue: `#88`
  Status: wontfix
  Reason: Hidden water-echo passage already implemented. Lamp in cavern shows water traces and echoes.
  Planned milestone: N/A

- Issue: `#89`
  Status: deferred
  Reason: Ancient Alcove stone-weight puzzle is complex and requires significant new mechanics. Current alcove has inscription and altar interaction.
  Planned milestone: M4 - Content Expansion

- Issue: `#87`
  Status: accepted
  Reason: Feature suggestion for give command to interact with mechanisms. Currently drop does not trigger interactions. Narrative fit HIGH, location fit HIGH. Will implement give command.
  Planned milestone: M3 - Polish
  Implemented: Added 'give <item>' command that triggers interactions with room objects (pedestal, altar).

- Issue: `#85`
  Status: deferred
  Reason: Context-sensitive hint system is nice-to-have but adds complexity. Current error messages already provide some guidance.
  Planned milestone: M4 - Content Expansion

- Issue: `#86`
  Status: wontfix
  Reason: Functional lamp interaction already implemented in cavern. Treasury lamp interaction addressed in #91.
  Planned milestone: N/A

- Issue: `#84`
  Status: accepted
  Reason: Bug report - drop command does not allow giving items to mechanisms. Duplicate of #87, will implement give command.
  Planned milestone: M3 - Polish

- Issue: `#83`
  Status: accepted
  Reason: Bug report - tablet use in Alcove does nothing. Currently tablet only works in treasury. Narrative fit HIGH, location fit HIGH. Will implement tablet use in ancient_alcove.
  Planned milestone: M3 - Polish
  Implemented: Using tablet in Ancient Alcove reveals final verses about the treasure chamber.

- Issue: `#82`
  Status: accepted
  Reason: Bug report - lamp has no effect in Treasury. Currently lamp only works in cavern and foyer. Narrative fit HIGH, location fit HIGH. Will implement lamp interaction in Treasury.
  Planned milestone: M3 - Polish
  Implemented: Using lamp in Treasury reveals hidden details and a coin near pedestal.

- Issue: `#81`
  Status: deferred
  Reason: Item interaction branching is complex and would significantly alter puzzle flow. Current linear puzzle chain is clear and functional.
  Planned milestone: M4 - Content Expansion

- Issue: `#79`
  Status: wontfix
  Reason: Echo chamber puzzle already implemented. Listen at Trailhead reveals hidden passage.
  Planned milestone: N/A

- Issue: `#80`
  Status: wontfix
  Reason: Glyph hint system already implemented. Examine glyphs provides contextual hints.
  Planned milestone: N/A

- Issue: `#78`
  Status: accepted
  Reason: Bug report - dropping items does not influence environment. Duplicate of #84/#87, will implement give command.
  Planned milestone: M3 - Polish

- Issue: `#76`
  Status: accepted
  Reason: Bug report - lamp has no effect in Treasury. Duplicate of #82, will implement lamp interaction in Treasury.
  Planned milestone: M3 - Polish

- Issue: `#77`
  Status: accepted
  Reason: Bug report - tablet usage in hidden alcove does nothing. Duplicate of #83, will implement tablet use in ancient_alcove.
  Planned milestone: M3 - Polish

- Issue: `#75`
  Status: deferred
  Reason: Qualitative playtest at 2.67/5. Notes promising build with strong atmosphere and clear puzzle chain. Same themes addressed by prior accepted issues. No new actionable items.
  Planned milestone: M3 - Polish

- Issue: `#73`
  Status: wontfix
  Reason: Open optional side areas already implemented. Hidden Passage and Ancient Alcove are accessible.
  Planned milestone: N/A

- Issue: `#74`
  Status: deferred
  Reason: Ending sequence and discovery score would require significant new content. Could be future milestone.
  Planned milestone: M4 - Content Expansion

- Issue: `#72`
  Status: wontfix
  Reason: Examine and read verbs already implemented. Parser supports examine, read maps to examine.
  Planned milestone: N/A

- Issue: `#71`
  Status: deferred
  Reason: Ambient flavor text not room-specific is minor polish. Current flavor text is generic but functional.
  Planned milestone: M4 - Content Expansion

- Issue: `#70`
  Status: wontfix
  Reason: Truncated text bug not reproducible. Pedestal reveal text is complete.
  Planned milestone: N/A

- Issue: `#69`
  Status: wontfix
  Reason: Bronze gate lock state bug not reproducible. Gate correctly shows "stands open" after using key.
  Planned milestone: N/A

- Issue: `#68`
  Status: wontfix
  Reason: Inspect command already implemented. Parser maps inspect to examine action.
  Planned milestone: N/A

- Issue: `#66`
  Status: wontfix
  Reason: Same as #69 - gate lock state working correctly at current commit.
  Planned milestone: N/A

- Issue: `#67`
  Status: wontfix
  Reason: Same as #70 - truncated text bug not reproducible.
  Planned milestone: N/A

- Issue: `#65`
  Status: deferred
  Reason: Qualitative review at 3.83/5. Notes good atmosphere and puzzles but suggests deeper lore and branching. Same themes addressed by accepted issues.
  Planned milestone: M4 - Content Expansion

- Issue: `#64`
  Status: wontfix
  Reason: Ancient journal lore item already implemented in Hidden Passage per prior cycle.
  Planned milestone: N/A

- Issue: `#62`
  Status: wontfix
  Reason: Glyph decoding puzzle already implemented. Examine glyphs after lamp reveals hints.
  Planned milestone: N/A

- Issue: `#63`
  Status: deferred
  Reason: Alternative gate opening mechanic is interesting but adds complexity. Current key-gate puzzle is clear.
  Planned milestone: M4 - Alternative Paths

- Issue: `#61`
  Status: wontfix
  Reason: Gate lock state working correctly after using key.
  Planned milestone: N/A

- Issue: `#60`
  Status: wontfix
  Reason: Same as #70 - truncated text bug not reproducible.
  Planned milestone: N/A

- Issue: `#59`
  Status: wontfix
  Reason: Gate lock state working correctly.
  Planned milestone: N/A

- Issue: `#102`
  Status: wontfix
  Reason: Duplicate of #91 - lamp reveals coin in Treasury already implemented.
  Planned milestone: N/A

- Issue: `#103`
  Status: deferred
  Reason: Qualitative review at 3.5/5. Notes solid atmosphere but incomplete experience. Same themes addressed by accepted issues (#18 idol purpose, #22 lamp inscriptions, #33 glyph decoding). No new actionable items.
  Planned milestone: M4 - Content Expansion

- Issue: `#101`
  Status: wontfix
  Reason: Duplicate of #18 - idol-triggered secret compartment already implemented.
  Planned milestone: N/A

- Issue: `#99`
  Status: wontfix
  Reason: Key usage behavior is correct. After using key once, subsequent uses return "already unlocked" which is intended - the gate stays open. Bug reports about gate lock state (#59/#61/#66/#69) were marked wontfix as not reproducible.
  Planned milestone: N/A

- Issue: `#100`
  Status: wontfix
  Reason: Give command already implemented in current codebase (engine.py lines 439-463). Commands 'give coin', 'give idol', 'give tablet', 'give lamp', 'give key' all work correctly.
  Planned milestone: N/A

- Issue: `#102`
  Status: wontfix
  Reason: Lamp interaction in Treasury already implemented (engine.py lines 241-254). Using lamp reveals hidden coin near pedestal base.
  Planned milestone: N/A

- Issue: `#103`
  Status: deferred
  Reason: Qualitative playtest at 3.5/5. Notes solid atmospheric core but incomplete experience. Same themes addressed by prior accepted issues (#18 idol purpose, #22 lamp inscriptions, #33 glyph decoding, #105 key on glyph). No new actionable items beyond existing features.
  Planned milestone: M4 - Content Expansion

- Issue: `#104`
  Status: wontfix
  Reason: Lamp interaction in Treasury and Alcove already implemented (engine.py lines 241-269). Using lamp in Treasury reveals coin; using lamp in Alcove reveals altar inscriptions.
  Planned milestone: N/A

- Issue: `#106`
  Status: deferred
  Reason: Qualitative playtest at 3.5/5 for commit 34bef04a5023. Notes incomplete experience and final puzzle never resolves. Similar themes addressed by prior accepted issues (#18 idol purpose, #22 lamp inscriptions, #33 glyph decoding, #105 key on glyph). No new actionable items beyond existing features.
  Planned milestone: M4 - Content Expansion

- Issue: `#98`
  Status: wontfix
  Reason: Tablet use in Ancient Alcove already implemented (engine.py lines 319-335). Using tablet in alcove reveals final verses about the treasure chamber.
  Planned milestone: N/A

- Issue: `#97`
  Status: accepted
  Reason: Bug report - lamp has no effect in Ancient Alcove. Treasury lamp implemented in #82. Need to add lamp interaction in ancient_alcove. Narrative fit HIGH (lamp reveals details), location fit HIGH (Ancient Alcove).
  Planned milestone: M3 - Polish
  Implemented: Using lamp in Ancient Alcove reveals hidden inscriptions on the altar.

- Issue: `#98`
  Status: wontfix
  Reason: Tablet use in Ancient Alcove already implemented per #83.
  Planned milestone: N/A

- Issue: `#96`
  Status: wontfix
  Reason: Lamp-activated hidden coin in cavern already implemented.
  Planned milestone: N/A

- Issue: `#95`
  Status: wontfix
  Reason: Interactive glyph clue system already implemented (lamp reveals inscriptions, examine glyphs).
  Planned milestone: N/A

- Issue: `#94`
  Status: wontfix
  Reason: Echo chamber puzzle already implemented (listen at trailhead).
  Planned milestone: N/A

- Issue: `#92`
  Status: wontfix
  Reason: Hidden water passage already implemented (listen at trailhead reveals hidden passage).
  Planned milestone: N/A

- Issue: `#93`
  Status: wontfix
  Reason: Interactive glyph in Foyer already implemented (examine after lamp).
  Planned milestone: N/A

- Issue: `#90`
  Status: wontfix
  Reason: Idol-triggered secret compartment already implemented (per #18).
  Planned milestone: N/A

- Issue: `#88`
  Status: wontfix
  Reason: Hidden water-echo passage already implemented (lamp in cavern reveals water traces).
  Planned milestone: N/A

- Issue: `#89`
  Status: deferred
  Reason: Ancient Alcove stone-weight puzzle deferred to future milestone per prior decision.
  Planned milestone: M4 - Content Expansion

- Issue: `#85`
  Status: deferred
  Reason: Context-sensitive hint system deferred to future milestone per prior decision.
  Planned milestone: M4 - Content Expansion

- Issue: `#86`
  Status: wontfix
  Reason: Functional lamp interaction already implemented (cavern, foyer, treasury).
  Planned milestone: N/A

- Issue: `#106`
  Status: deferred
  Reason: Qualitative playtest at 3.5/5 for commit 34bef04a5023. Notes incomplete experience and final puzzle never resolves. Similar themes addressed by prior accepted issues (#18 idol purpose, #22 lamp inscriptions, #33 glyph decoding). No new actionable items beyond existing features.
  Planned milestone: M4 - Content Expansion

- Issue: `#104`
  Status: wontfix
  Reason: Lamp interaction in Treasury and Alcove already implemented in current codebase (engine.py lines 241-269). Using lamp in Treasury reveals hidden coin; using lamp in Alcove reveals altar inscriptions.
  Planned milestone: N/A

- Issue: `#105`
  Status: accepted
  Reason: Feature suggestion for key on glyph interaction. Currently glyphs reveal inscriptions with lamp and can be examined for clues. Adding key interaction provides alternative puzzle path. Narrative fit HIGH (glyphs in foyer), location fit HIGH (foyer). Will implement: use key on glyph reveals hidden clue or passage hint.
  Planned milestone: M3 - Polish
  Implemented: Using key on glyph in Foyer reveals secret compartment with additional lore hint.

- Issue: `#103`
  Status: deferred
  Reason: Qualitative playtest at 3.5/5 for commit 56080415190b. Notes solid atmospheric core but incomplete experience. Same themes as #106 addressed by prior accepted issues. No new actionable items.
  Planned milestone: M4 - Content Expansion

- Issue: `#99`
  Status: wontfix
  Reason: Key usage behavior is correct. After using key once, subsequent uses return "already unlocked" which is intended - the gate stays open. Bug reports about gate lock state (#59/#61/#66/#69) were marked wontfix as not reproducible.
  Planned milestone: N/A

- Issue: `#114`
  Status: wontfix
  Reason: Bug not reproducible - smoke test confirms coin works correctly (use lamp in cavern reveals coin, take coin adds to inventory, use coin in treasury reveals tablet). Issue description appears truncated; no evidence of coin disappearing.
  Planned milestone: N/A

- Issue: `#115`
  Status: wontfix
  Reason: Duplicate of #110 - hidden water echo passage already implemented. Using lamp in cavern after collecting coin reveals eastern passage to Submerged Chamber.
  Planned milestone: N/A

- Issue: `#116`
  Status: deferred
  Reason: Qualitative playtest at 3.33/5. Notes incomplete experience and final tablet never resolves. Same themes addressed by prior accepted issues (#18 idol purpose, #22 lamp inscriptions, #33 glyph decoding, #110 hidden water passage). No new actionable items.
  Planned milestone: M4 - Content Expansion

- Issue: `#110`
  Status: accepted
  Reason: Feature suggestion for Hidden Water Echo Passage. After collecting coin in cavern, using lamp again should reveal a hidden passage. Addresses "incomplete experience" feedback from qualitative reviews. Narrative fit HIGH (water echoes theme), location fit HIGH (cavern). Will implement: lamp in cavern after coin collected reveals hidden eastern passage.
  Planned milestone: M3 - Polish
  Implemented: Using lamp in cavern three times (after collecting coin) reveals hidden eastern passage to Submerged Chamber with final inscription.

- Issue: `#111`
  Status: wontfix
  Reason: Duplicate of #105 - key on glyph already implemented in current codebase.
  Planned milestone: N/A

- Issue: `#108`
  Status: wontfix
  Reason: Tablet text already contains water echoes hint. Current text: "Seek the echoes where the water weeps. There, beneath the weight of ages, the true tablet awaits." Matches the requested clue theme.
  Planned milestone: N/A

- Issue: `#109`
  Status: wontfix
  Reason: Rooms already have rich sensory descriptions with environmental details. Additional sensory language deferred for scope control.
  Planned milestone: M4 - Content Expansion

- Issue: `#107`
  Status: wontfix
  Reason: Hidden passage revealed by idol already implemented. Placing idol on treasury pedestal reveals hidden alcove with verses.
  Planned milestone: N/A

- Issue: `#113`
  Status: deferred
  Reason: Qualitative playtest at 3.33/5 for current commit. Notes incomplete experience and final puzzle never resolves. Same themes addressed by prior accepted issues (#18 idol purpose, #22 lamp inscriptions, #33 glyph decoding, #110 hidden water passage). No new actionable items.
  Planned milestone: M4 - Content Expansion

- Issue: `#112`
  Status: deferred
  Reason: Qualitative playtest at 3.33/5. Same findings as #113. No new actionable items beyond accepted issues.
  Planned milestone: M4 - Content Expansion

