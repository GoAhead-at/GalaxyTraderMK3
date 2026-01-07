GALAXYTRADER MK3 - 0.6.11
=========================

Give your traders a brain. GalaxyTrader MK3 teaches your freighters to plan routes,
earn experience, attend mandatory training, and take care of repairs and equipment
without constant micromanagement.


REQUIREMENTS

- X4: Foundations latest Version 8+  (tested with  8+ only) older version  might work
- SirNukes Mod Support APIs (Steam Workshop ID ws_2042901274)
- kuertee UI Extensions and HUD
- Optional DLCs simply add more stations to trade with; the mod should work fine without them


FEATURES

- Smarter Trading
  - Ships evaluate thousands of buy/sell combinations, score every candidate by profit,
    travel time, distance penalty, and blacklist safety, then reserve the best option so
    no other trader can snatch it.
  - If a route becomes dangerous or blocked mid-flight, they immediately re-score the next-best
    cached trade instead of starting from scratch, which keeps the economy moving.
  - Already carrying cargo? They immediately look for the best buyer before seeking a new deal.

- Pilot Progression
  - Every successful trade pays XP. Pilots climb from Apprentice (1 jump) to
    Long-Distance Merchant (25 jumps).
  - XP gain automatically pauses at levels 3, 6, 9, and 12 until the pilot completes a
    short certification dock.

- Fleet Coordination
  - Ships that share a commander divide markets, avoid piling into the same station, and
    share profitable intel with their squadmates.

- Threat Awareness
  - Traders react to pirate attacks or ship losses by blacklisting the affected sector,
    then automatically clear the block as soon as the dangerous ships disappear, so routes
    reopen without manual cleanup.

- Mobile Market Intelligence
  - Level 9+ pilots automatically detect stations as they enter radar range (event-driven,
    zero overhead when no stations nearby) and update your trade data instantly, meaning
    far fewer dry runs to empty factories.

- Automatic Upkeep
  - Level 12+ pilots head to shipyards for repairs when hull drops below the threshold you set.
  - Level 15 pilots also restock countermeasures, drones, and laser towers in the same visit.

- Automatic Ship Modifications
  - Qualifying pilots automatically receive engine and hull mods that boost travel speed
    and survivability, and the mods are removed again the moment you revoke the GalaxyTrader
    order.

- Player-Friendly Feedback
  - Pop-up summaries tell you how many ships are active, how much profit they made, and
    when they finish training, repairing, or resupplying.
  - Ships can automatically rename themselves with rank, level, XP, and status so you can
    see their progress from the map.

- Nine Languages
  - English, German, French, Spanish, Italian, Russian, Portuguese, Korean, and Simplified Chinese.


INSTALLATION

1. Subscribe/install SirNukes Mod Support APIs and kuertee UI Extensions.
2. Copy GalaxyTraderMK3 into your X4 extensions folder.
3. Enable the mod in the Extensions menu and start/reload your save.
4. Open SirNukes' Mod Support menu (Interactions -> Extensions -> GalaxyTrader MK3) to
   review the default settings.
5. Give any freighter the GalaxyTrader MK3 order. Within a few seconds it registers
   with the system and starts trading on its own.


GETTING STARTED

- Start with a single ship so you can watch the flow. Level 1 pilots stay within one jump.
- Enable ship renaming in the global settings if you want rank/level shown in the name.
- Watch the logbook: you'll see XP gains, route reports, training notices, and maintenance
  summaries in neatly organized categories.
- When a pilot hits a training gate, they'll dock automatically, display a [TRAINING]
  prefix, and resume trading when the course completes (10+ minutes, varies by level).


CONFIGURATION

Access everything through SirNukes' Mod Support menu.

- XP & Training – Turn the whole progression system on/off, set the XP multiplier
  (50–200%), and control automatic training initiation.
- Trade Cache – Enable/disable the shared trade cache that speeds up searches, set the
  minimum profit a route must have before it's stored, and define how long a reservation
  stays locked.
- Notifications – Choose whether you want simple pop-ups every minute, detailed logbook
  reports every 30 minutes, or no reports at all.
- Threat Avoidance – Decide how hostile a faction must be before its space is considered
  off-limits, and what threat level triggers an automatic blacklist.
- Ship Naming – Mix and match rank, level, XP, operational state, and ship class in the
  name prefix or suffix.
- Auto-Repair & Defensive Equipment – Set the hull percentage that triggers repairs, the
  minimum pilot level allowed to use the feature, and the percentage that counts as "low"
  for countermeasures, drones, and towers.
- Ship Modifications – Turn the automatic engine/hull mod installer on or off; the mods
  are automatically dismantled when you revoke the order or uninstall the mod.
- Performance (advanced/experimental) – Only change these if you're troubleshooting.
  They adjust how many ships may search at once, how many trades are analyzed per batch,
  and how aggressively the mod yields back CPU time.

Every setting applies immediately—no save/reload required.


ORDER OPTIONS

When you issue the GalaxyTrader MK3 order you can fine-tune that specific ship:

- Home base or sector (used for distance calculations and fallback behaviour).
- Maximum buy/sell distance (soft-capped by the pilot's management level).
- Whether to trade illegal wares, avoid carrier/auxiliary stations, or skip build storage stations.
- Faction priority: player-only, foreign-first (default), or treat everyone equally.
- Auto wares vs a hand-picked ware basket.
- Distance penalty (0% = pure profit, 100% = prefers nearby trades).
- Cargo fill target (how full the ship should get before heading to sell).
- Market update frequency (30–300 seconds, default: 60 seconds).
- Notification level override and per-ship debug verbosity if you're troubleshooting.


SKILL PROGRESSION

Level 1 - Apprentice - Jump Limit: 1 - Key Unlocks: Basic trading
Level 2 - Apprentice - Jump Limit: 1 - Key Unlocks: XP continues
Level 3* - Apprentice - Jump Limit: 3 - Key Unlocks: Training unlocks multi-sector routes
Level 4-5 - Courier - Jump Limit: 3 - Key Unlocks: Better range and naming upgrades
Level 6* - Courier - Jump Limit: 5 - Key Unlocks: Threat intelligence access
Level 7-8 - Supplier - Jump Limit: 5 - Key Unlocks: Fleet coordination perks
Level 9* - Supplier - Jump Limit: 10 - Key Unlocks: Mobile market scanning (event-driven)
Level 10-11 - Trader - Jump Limit: 10 - Key Unlocks: Long-distance specialization
Level 12* - Trader - Jump Limit: 15 - Key Unlocks: Auto-repair + master certification
Level 13 - Trader - Jump Limit: 15 - Key Unlocks: Advanced trading range
Level 14 - Trader - Jump Limit: 25 - Key Unlocks: Maximum jump range unlocked
Level 15 - Long-Distance Merchant - Jump Limit: 25 - Key Unlocks: Defensive equipment automation

*Training required before earning more XP.


TROUBLESHOOTING

Ship isn't gaining XP
- Make sure XP Progression and Auto Training are enabled in the global settings.
- Check that the ship actually completed a buy and sell. XP is paid when a trade cycle ends.

Training never starts
- Training stations are automatically found within range—ensure there's a shipyard, wharf,
  trade station, or equipment dock nearby.
- If the ship is still flying freight, wait until the current job finishes—training only
  triggers when they're free.

Ship keeps trying to sell leftover cargo
- That's the safety net doing its job. Let it run—each failed attempt increases the wait
  time, and after a few tries you'll see a logbook summary explaining the situation.

Maintenance spam
- Lower the Auto-Repair hull threshold or disable defensive replenishment in the global
  settings if you don't want ships using these services.

Too many notifications
- Set Simple Reports or Comprehensive Reports to 0 in the global settings, or change the
  per-ship notification level to "Minimal".


COMPATIBILITY

- Works with vanilla and most economy mods—GalaxyTrader uses its own orders and doesn't
  overwrite Egosoft scripts.
- Ships always draw from the single player wallet; there are no hidden budgets to refill.
- If you remove the mod, the included removal script clears all automatic equipment mods,
  so your save stays clean.
- All UI text is localized, so you can play in any supported language.


TIPS FOR SUCCESS

1. Keep the XP multiplier at 100% for a balanced climb (roughly 500 trades to level 15).
2. Assign a commander with solid defenses and let several subordinates share its blacklist.
3. Use the Ship Naming system to spot who needs training or repairs at a glance.
4. Turn on auto-repair as soon as your pilots hit level 12—lost hull equals lost profits.
5. Enable defensive equipment at level 15 so elite traders always carry countermeasures,
   drones, and towers when jumping into risky space.
6. Don't panic when a ship pauses; check the logbook. You'll usually see a clear reason
   (waiting for trade, fleeing danger, training, maintenance, etc.).


KNOWN ISSUES

- Assigning 50+ ships at once may cause a short hitch while they register; it clears on its own.
- Debug logging can be spammy if you enable every option—leave it off unless you're
  diagnosing a problem.
- Ships reassigned to manual orders need a few seconds to deregister from the GalaxyTrader
  roster; they'll stop receiving updates once the cleanup finishes.


BUG REPORTS & SUGGESTIONS

- Nexus Mods discussion: https://www.nexusmods.com/x4foundations/mods/1857


CREDITS

- SirNukes – Mod Support APIs
- kuertee – UI Extensions & HUD
- Community testers, translators, and supporters
- Egosoft – X4: Foundations and ongoing modding support

License: MIT (LICENSE.md)

GalaxyTrader MK3 – Teaching your ships to trade smarter, not harder!
