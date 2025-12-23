# Reasoning Log

This document walks through how the system handled each of the 10 test cases and explains the logic behind each mapping decision.

---

## Case 1

**Tags given:** Love

**Story:** They hated each other for years, working in the same cubicle, until a late-night deadline changed everything.

**Result:** Fiction > Romance > Enemies-to-Lovers

**Why:** The tag says "Love" which is vague. But the text has "hated each other for years" followed by something that "changed everything" - that is the classic enemies-to-lovers arc. The hatred turning into romance is the defining pattern here.

---

## Case 2

**Tags given:** Action, Spies

**Story:** Agent Smith must recover the stolen drive without being detected by the Kremlin.

**Result:** Fiction > Thriller > Espionage

**Why:** The tags actually point in the right direction here. "Agent", "stolen drive", "Kremlin", "without being detected" - this is spy fiction. Espionage fits better than generic Action because the focus is on covert operations, not combat.

---

## Case 3

**Tags given:** Scary, House

**Story:** The old Victorian mansion seemed to breathe, its corridors whispering secrets of the family's dark past.

**Result:** Fiction > Horror > Gothic

**Why:** "Scary" and "House" are too generic. But Victorian mansion, corridors whispering, family secrets, dark past - that is textbook Gothic horror. The atmosphere and setting matter more than jump scares here, which is what separates Gothic from Slasher or Psychological Horror.

---

## Case 4

**Tags given:** Love, Future

**Story:** A story about a man who falls in love with his AI operating system in a neon-drenched Tokyo.

**Result:** Fiction > Sci-Fi > Cyberpunk

**Why:** This one could go either way. There is a romance angle (falling in love), but the setting dominates: AI operating system, neon-drenched, Tokyo. That aesthetic is Cyberpunk through and through. The romance happens to take place in a cyberpunk world, rather than the other way around. I prioritized setting over relationship.

---

## Case 5

**Tags given:** Action

**Story:** The lawyer stood before the judge, knowing this cross-examination would decide the fate of the city.

**Result:** Fiction > Thriller > Legal Thriller

**Why:** The user tagged this as "Action" but there is nothing action-oriented in the text. No fights, no chases. Instead we have a lawyer, a judge, cross-examination, high stakes. This is a courtroom drama. The system correctly ignored the misleading tag and went with what the content actually describes.

---

## Case 6

**Tags given:** Space

**Story:** How to build a telescope in your backyard using basic household items.

**Result:** [UNMAPPED]

**Why:** The "Space" tag suggests Sci-Fi, but the content is clearly instructional. "How to build", "basic household items" - this is a DIY guide, not fiction. The taxonomy only covers fiction genres, so this gets flagged as unmapped rather than being forced into a category it does not belong to.

---

## Case 7

**Tags given:** Sad, Love

**Story:** They met again 20 years after the war, both gray-haired, wondering what could have been.

**Result:** Fiction > Romance > Second Chance

**Why:** "Met again", "20 years after", "what could have been" - this is about reconnecting with a past love and wondering about missed opportunities. Second Chance romance is exactly this: former lovers or almost-lovers getting another shot. The "Sad" tag fits the bittersweet tone but does not change the category.

---

## Case 8

**Tags given:** Robots

**Story:** A deep dive into the physics of FTL travel and the metabolic needs of long-term stasis.

**Result:** Fiction > Sci-Fi > Hard Sci-Fi

**Why:** "Robots" is misleading - there are no robots mentioned in the text. What we have is "physics of FTL travel" and "metabolic needs of long-term stasis". That is technical, science-focused writing. Hard Sci-Fi is defined by its attention to scientific accuracy and plausibility, which matches this exactly.

---

## Case 9

**Tags given:** Ghost

**Story:** A masked killer stalks a group of teenagers at a summer camp.

**Result:** Fiction > Horror > Slasher

**Why:** The user tagged "Ghost" but there is nothing supernatural here. Masked killer, stalking teenagers, summer camp - this is the Slasher formula (think Friday the 13th). The system correctly identified the actual content over the incorrect tag.

---

## Case 10

**Tags given:** Recipe, Sweet

**Story:** Mix two cups of flour with sugar and bake at 350 degrees.

**Result:** [UNMAPPED]

**Why:** This is a baking recipe. "Mix two cups of flour", "bake at 350 degrees" - there is no story here at all. The tags actually say "Recipe" which confirms it. Marked as unmapped because recipes are not part of the fiction taxonomy.

---

## Summary

Out of 10 cases:
- 8 were successfully mapped to specific subcategories
- 2 were correctly identified as non-fiction and marked [UNMAPPED]
- 0 errors

The system handled misleading tags correctly in cases 5 and 9, and made a reasonable judgment call on the ambiguous case 4.
