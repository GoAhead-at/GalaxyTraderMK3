--[[
==============================================================================
GalaxyTrader MK3 - String Utilities
==============================================================================
Provides string manipulation functions for MD scripts.
MD XML has very limited string API - Lua handles the heavy lifting.

Features:
- Strip GT formatting from ship names (prefixes and suffixes)
- Language-independent pattern matching
- Fast and reliable string operations

Dependencies: 
- sn_mod_support_apis (Lua Loader API)

Author: GalaxyTrader Development Team
Version: 1.0
==============================================================================
]]--

local Lib = {}

-- =============================================================================
-- UTILITY FUNCTIONS
-- =============================================================================

local function debugLog(message)
    DebugError(string.format("[GT-StringUtils] %s", message))
end

-- =============================================================================
-- STRING MANIPULATION FUNCTIONS
-- =============================================================================

-- Strip GT formatting from ship names
-- Removes: prefixes like "ADVANCE", "[TRAINING]", "AVANÇAR" (any ALL-CAPS word or bracketed text)
-- Removes: suffixes like "(Comerciante Lv.10 XP:3150)"
function Lib.stripGTFormatting(shipName)
    if not shipName or shipName == "" then
        debugLog("Strip called with empty/nil name")
        return ""
    end
    
    local originalName = shipName
    local cleanName = shipName
    
    -- Step 1: Remove bracketed prefix like "[TRAINING]", "[AUSBILDUNG]", "[TREINAMENTO]", etc.
    cleanName = cleanName:gsub("^%[.-%]%s+", "")
    
    -- Step 2: Remove ALL-CAPS word prefix (like "ADVANCE ", "AVANÇAR ", "FORTSCHRITT ", etc.)
    -- Pattern: Match any sequence of non-lowercase chars at start, followed by space
    -- This handles ASCII uppercase, accented chars, numbers, etc.
    -- Check if first word is all uppercase (no lowercase letters)
    local firstWord = cleanName:match("^(%S+)%s")
    if firstWord and not firstWord:match("%l") then
        -- First word has no lowercase letters - it's all caps, strip it
        cleanName = cleanName:gsub("^%S+%s+", "", 1)
    end
    
    -- Step 3: Remove parenthetical suffix like "(Comerciante Lv.10 XP:3150)"
    local parenPos = cleanName:find("%s%(")
    if parenPos then
        cleanName = cleanName:sub(1, parenPos - 1)
    end
    
    -- Step 4: Trim any trailing/leading whitespace
    cleanName = cleanName:match("^%s*(.-)%s*$")
    
    if cleanName ~= originalName then
        debugLog(string.format("Stripped: '%s' -> '%s'", originalName, cleanName))
    end
    
    return cleanName
end

-- =============================================================================
-- EXTERNAL API (callable from MD via raise_lua_event)
-- =============================================================================

-- Handle strip request from MD
function Lib.onStripShipName(_, luaParam)
    -- luaParam format: "SHIPID|ShipName"
    local pipePos = luaParam:find("|")
    if not pipePos then
        debugLog(string.format("⚠️ ERROR: Invalid parameter format: '%s'", tostring(luaParam)))
        return
    end
    
    local shipId = luaParam:sub(1, pipePos - 1)
    local shipName = luaParam:sub(pipePos + 1)
    
    debugLog(string.format("📨 Received MD request to strip: '%s' (ship: %s)", shipName, shipId))
    
    local cleaned = Lib.stripGTFormatting(shipName)
    
    -- Return result via UI event that MD can listen to
    -- Use ship ID as identifier (safe, unique, simple string like "CJO-545")
    AddUITriggeredEvent(shipId, cleaned, "1")
    
    debugLog(string.format("✅ Returning cleaned name: '%s' for ship %s", cleaned, shipId))
    
    return cleaned
end

-- =============================================================================
-- MODULE INITIALIZATION
-- =============================================================================

function Init()
    debugLog("🚀 Initializing GT String Utils...")
    
    -- Register MD event listener (X4 Lua API)
    RegisterEvent("GT_StringUtils.StripShipName", Lib.onStripShipName)
    
    debugLog("✅ Event listener registered for 'GT_StringUtils.StripShipName'")
    
    -- Signal MD that we're ready
    AddUITriggeredEvent("gt_string_utils", "Initialized", "1")
    
    debugLog("✅ String utilities initialized successfully!")
end

-- Call Init when module loads
Init()

