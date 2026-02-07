--[[
==============================================================================
GalaxyTrader MK3 - Pilot Data Bridge
==============================================================================
Bridges MD pilot/ship data with Lua UI for the Info Menu

Features:
- Receives pilot data from MD via events
- Stores data in Lua-accessible format
- Provides data to gt_info_menu.lua for display

Dependencies: 
- sn_mod_support_apis (Lua Loader API)

Author: GalaxyTrader Development Team
Version: 1.0
==============================================================================
]]--

local ffi = require("ffi")
local C = ffi.C

-- =============================================================================
-- FFI DEFINITIONS
-- =============================================================================

ffi.cdef[[
    const char* GetComponentName(uint64_t componentid);
    uint64_t ConvertStringTo64Bit(const char* idcode);
    const char* ConvertIDToString(uint64_t componentid);
]]

-- =============================================================================
-- MODULE STATE
-- =============================================================================

local GT_PilotData = {
    -- Configuration
    CONFIG = {
        DEBUG_MODE = false,  -- Set to true to enable debug logging
    },
    
    -- Global settings (received from MD)
    settings = {
        autoTraining = true,    -- Default: automatic training enabled
        autoRepair = true,      -- Default: automatic repair enabled
        autoResupply = true,    -- Default: automatic resupply enabled
    },
    
    -- Pilot data storage (received from MD)
    pilots = {},  -- Array of pilot info tables
    lastUpdate = 0,
    initialized = false,
}

-- =============================================================================
-- DEBUG LOGGING
-- =============================================================================

local function debugLog(message)
    if GT_PilotData.CONFIG.DEBUG_MODE then
        DebugError("[GT Pilot Bridge] " .. tostring(message))
    end
end

-- =============================================================================
-- HELPER FUNCTIONS
-- =============================================================================

-- Format money with M/B suffixes
local function formatMoney(amount)
    local credits = amount / 100  -- Convert from cents to credits
    if credits >= 1000000000 then
        return string.format("%.1fB Cr", credits / 1000000000)
    elseif credits >= 1000000 then
        return string.format("%.1fM Cr", credits / 1000000)
    else
        return ConvertMoneyString(amount, false, false, 0, true)
    end
end

-- =============================================================================
-- DATA RECEPTION FROM MD
-- =============================================================================

-- Receive pilot data from MD
-- Expected format: "CONFIG:autoTraining|autoRepair|autoResupply||shipId|pilotName|...|tradeCount||..."
-- Config flags separated by "|", pilots separated by "||"
local function onReceivePilotData(_, param)
    debugLog("Received pilot data from MD")
    
    if not param or param == "" then
        debugLog("No pilot data received (empty)")
        GT_PilotData.pilots = {}
        return
    end
    
    -- Parse the data string
    local pilots = {}
    local pilotStrings = {}
    
    -- Split by pilot separator "||" (double pipe)
    -- Use pattern that captures everything up to double-pipe or end of string
    for pilotStr in string.gmatch(param .. "||", "(.-)||") do
        if pilotStr ~= "" then
            table.insert(pilotStrings, pilotStr)
        end
    end
    
    debugLog(string.format("Parsing %d records (including config)", #pilotStrings))
    
    -- Check if first record is config data
    local startIndex = 1
    if #pilotStrings > 0 and string.sub(pilotStrings[1], 1, 7) == "CONFIG:" then
        local configStr = string.sub(pilotStrings[1], 8)  -- Remove "CONFIG:" prefix
        local configFields = {}
        for field in string.gmatch(configStr, "[^|]+") do
            table.insert(configFields, field)
        end
        
        if #configFields >= 3 then
            GT_PilotData.settings.autoTraining = (tonumber(configFields[1]) or 1) ~= 0
            GT_PilotData.settings.autoRepair = (tonumber(configFields[2]) or 1) ~= 0
            GT_PilotData.settings.autoResupply = (tonumber(configFields[3]) or 1) ~= 0
            
            debugLog(string.format("Config flags: AutoTraining=%s, AutoRepair=%s, AutoResupply=%s",
                tostring(GT_PilotData.settings.autoTraining),
                tostring(GT_PilotData.settings.autoRepair),
                tostring(GT_PilotData.settings.autoResupply)))
        end
        
        startIndex = 2  -- Skip config record, start parsing pilots from index 2
    end
    
    debugLog(string.format("Parsing %d pilot records", #pilotStrings - startIndex + 1))
    
    for i = startIndex, #pilotStrings do
        local pilotStr = pilotStrings[i]
        
        -- Split pilot data by pipe (handling empty fields correctly)
        -- Pattern [^|]+ skips empty fields, causing field misalignment
        -- Use manual splitting to preserve empty fields
        local fields = {}
        local startPos = 1
        while startPos <= #pilotStr do
            local endPos = string.find(pilotStr, "|", startPos)
            if endPos == nil then
                -- Last field (no trailing pipe)
                table.insert(fields, string.sub(pilotStr, startPos))
                break
            else
                -- Field ends at pipe (includes empty fields)
                table.insert(fields, string.sub(pilotStr, startPos, endPos - 1))
                startPos = endPos + 1
            end
        end
        
        if #fields >= 13 then
            local pilotInfo = {
                shipId = fields[1] or "???",
                pilotName = fields[2] or "Unknown",
                shipType = fields[3] or "Unknown Ship",
                status = fields[4] or "[ADVANCE]",  -- Already formatted by MD
                rank = fields[5] or "Apprentice",
                rankIndex = tonumber(fields[6]) or 1,
                level = tonumber(fields[7]) or 1,
                xp = tonumber(fields[8]) or 0,
                xpNext = tonumber(fields[9]) or 1000,
                pilotProfit = tonumber(fields[10]) or 0,  -- Pilot's lifetime profit (follows pilot)
                shipProfit = tonumber(fields[11]) or 0,   -- Ship's profit (current ship)
                location = fields[12] or "Unknown",
                tradeCount = tonumber(fields[13]) or 0,
            }
            
            -- Format XP for display
            pilotInfo.xpFormatted = string.format("%s / %s",
                ConvertIntegerString(pilotInfo.xp, true, 0, true),
                ConvertIntegerString(pilotInfo.xpNext, true, 0, true))
            
            -- Format both profit values for display
            pilotInfo.pilotProfitFormatted = formatMoney(pilotInfo.pilotProfit)
            pilotInfo.shipProfitFormatted = formatMoney(pilotInfo.shipProfit)
            
            table.insert(pilots, pilotInfo)
            
            debugLog(string.format("  Pilot %d: %s (%s) - Level %d, Pilot: %s Cr, Ship: %s Cr", 
                i, pilotInfo.pilotName, pilotInfo.shipType, pilotInfo.level, 
                pilotInfo.pilotProfitFormatted, pilotInfo.shipProfitFormatted))
        else
            debugLog(string.format("  WARNING: Pilot %d has incomplete data (%d fields)", i, #fields))
        end
    end
    
    GT_PilotData.pilots = pilots
    GT_PilotData.lastUpdate = getElapsedTime()
    GT_PilotData.initialized = true
    
    debugLog(string.format("Stored %d pilots in Lua", #pilots))
    
    -- Trigger UI refresh if menu is open
    if Mods and Mods.GalaxyTrader and Mods.GalaxyTrader.InfoMenu and Mods.GalaxyTrader.InfoMenu.onDataUpdate then
        Mods.GalaxyTrader.InfoMenu.onDataUpdate()
    end
end

-- =============================================================================
-- PUBLIC API (for gt_info_menu.lua)
-- =============================================================================

function GT_PilotData.getPilots()
    -- Return a COPY of the pilots array to prevent external sorting from modifying our stored data
    local pilots = GT_PilotData.pilots or {}
    local copy = {}
    for i = 1, #pilots do
        copy[i] = pilots[i]
    end
    return copy
end

function GT_PilotData.getLastUpdate()
    return GT_PilotData.lastUpdate
end

function GT_PilotData.isInitialized()
    return GT_PilotData.initialized
end

function GT_PilotData.requestRefresh()
    debugLog("Refresh requested - sending event to MD")
    AddUITriggeredEvent("gt_pilot_data_bridge", "RequestPilotData", 1)
end

-- =============================================================================
-- INITIALIZATION
-- =============================================================================

local function init()
    debugLog("Initializing GT Pilot Data Bridge")
    
    -- Register event listener for pilot data from MD
    RegisterEvent("GT_PilotData.Update", onReceivePilotData)
    
    debugLog("GT Pilot Data Bridge initialized - waiting for data from MD")
end

-- =============================================================================
-- MODULE EXPORT
-- =============================================================================

-- Export to global scope so gt_info_menu.lua can access it
if not Mods then Mods = {} end
if not Mods.GalaxyTrader then Mods.GalaxyTrader = {} end
Mods.GalaxyTrader.PilotData = GT_PilotData

-- Initialize on load
init()

return GT_PilotData

