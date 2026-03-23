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
