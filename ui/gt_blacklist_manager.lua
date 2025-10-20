--[[
==============================================================================
GalaxyTrader MK3 - Dynamic Blacklist Manager
==============================================================================
Bridges MD threat intelligence with X4's native blacklist system

Features:
- Creates empty fleet blacklist at game start/save load (avoids creation lag)
- Updates blacklist dynamically as threats are detected/cleared
- Automatically applies blacklist to all GT ships
- Uses vanilla pathfinding for automatic route recalculation

Dependencies: 
- sn_mod_support_apis (Lua Loader API)
- X4 FFI blacklist functions

Author: GalaxyTrader Development Team
Version: 1.0
==============================================================================
]]--

local ffi = require("ffi")
local C = ffi.C

-- =============================================================================
-- FFI DEFINITIONS - X4 Blacklist API
-- =============================================================================

ffi.cdef[[
    typedef int32_t BlacklistID;
    
    typedef struct {
        const char* name;
        const char* type;           // "sectortravel" or "sectoractivity"
        uint32_t nummacros;         // Number of sector macros
        const char** macros;        // Array of sector macro names
        uint32_t numfactions;       // Number of factions
        const char** factions;      // Array of faction IDs
        const char* relation;       // Relation threshold
        bool hazardous;
        bool usemacrowhitelist;
        bool usefactionwhitelist;
        BlacklistID id;             // ID for updates
    } BlacklistInfo2;
    
    BlacklistID CreateBlacklist2(BlacklistInfo2 info);
    void UpdateBlacklist2(BlacklistInfo2 info);
    void RemoveBlacklist(BlacklistID id);
    void SetControllableBlacklist(uint64_t controllableid, BlacklistID id, const char* listtype, bool value);
    BlacklistID GetControllableBlacklistID(uint64_t controllableid, const char* listtype, const char* defaultgroup);
    bool IsComponentBlacklisted(uint64_t componentid, const char* listtype, const char* defaultgroup, uint64_t controllableid);
    
    // Component lookup
    uint64_t ConvertStringTo64Bit(const char* idcode);
    const char* ConvertIDToString(uint64_t componentid);
    const char* GetComponentData(uint64_t componentid, const char* propertyname);
]]

-- =============================================================================
-- MODULE STATE
-- =============================================================================

local GT_Blacklist = {
    -- Configuration
    CONFIG = {
        DEBUG_MODE = true,
        BLACKLIST_NAME_PREFIX = "GT_ThreatAvoid_",
        THREAT_LEVEL_THRESHOLD = 3,  -- Blacklist sectors with threat >= 3
        UPDATE_INTERVAL = 5.0,        -- Check for updates every 5 seconds
    },
    
    -- State tracking
    dynamic_blacklists = {},  -- { ship_id -> blacklist_id }
    blacklisted_sectors = {}, -- { sector_name -> { threat_level, timestamp } }
    fleet_blacklist_id = nil, -- Shared fleet-wide blacklist ID
    last_update = 0,
    initialized = false,
}

-- =============================================================================
-- UTILITY FUNCTIONS
-- =============================================================================

local function debugLog(message, level)
    if GT_Blacklist.CONFIG.DEBUG_MODE then
        local prefix = level == "ERROR" and "❌" or level == "WARN" and "⚠️" or "🛡️"
        DebugError(string.format("[GT-Blacklist] %s %s", prefix, message))
    end
end

local function convertStringToID(idcode)
    if not idcode or idcode == "" then
        return 0
    end
    -- Match UPB pattern: tonumber -> tostring -> ConvertStringTo64Bit
    -- This handles numeric strings from MD like "123456789"
    local num = tonumber(idcode)
    if not num then
        debugLog(string.format("Failed to convert '%s' to number", idcode), "WARN")
        return 0
    end
    return C.ConvertStringTo64Bit(tostring(num))
end

-- NOTE: ConvertIDToString is restricted in FFI, so we can't use it
-- local function convertIDToString(componentid)
--     if not componentid or componentid == 0 then
--         return ""
--     end
--     return ffi.string(C.ConvertIDToString(componentid))
-- end

-- =============================================================================
-- BLACKLIST MANAGEMENT - CORE FUNCTIONS
-- =============================================================================

--- Create or update the fleet-wide dynamic blacklist
local function updateFleetBlacklist(threatened_macro_list)
    debugLog(string.format("Updating fleet blacklist with %d threatened sector macros", #threatened_macro_list))
    
    -- MD already sent us the macros, so we can use them directly!
    local macro_strings = {}  -- Keep references to prevent garbage collection
    
    for _, macro_name in ipairs(threatened_macro_list) do
        if macro_name and macro_name ~= "" and macro_name ~= "nil" then
            -- Store FFI string to prevent GC
            table.insert(macro_strings, ffi.new("char[?]", #macro_name + 1, macro_name))
            debugLog(string.format("  → Added macro: %s", macro_name))
        else
            debugLog(string.format("WARNING: Skipping invalid macro: '%s'", tostring(macro_name)), "WARN")
        end
    end
    
    -- Allow empty blacklist (0 sectors) - this is intentional for "clear all threats"
    debugLog(string.format("Processed %d valid sector macros", #macro_strings))
    
    -- Prepare FFI array of string pointers (handle empty case)
    local macros_array = nil
    if #macro_strings > 0 then
        macros_array = ffi.new("const char*[?]", #macro_strings)
        for i, macro_str in ipairs(macro_strings) do
            macros_array[i-1] = macro_str
        end
    end
    
    -- Create blacklist info structure
    local blacklist_name = GT_Blacklist.CONFIG.BLACKLIST_NAME_PREFIX .. "Fleet"
    local name_str = ffi.new("char[?]", #blacklist_name + 1, blacklist_name)
    local type_str = ffi.new("char[?]", 13, "sectortravel")  -- 12 chars + null
    local relation_str = ffi.new("char[?]", 1, "")  -- Empty string
    
    local info = ffi.new("BlacklistInfo2")
    info.name = name_str
    info.type = type_str
    info.nummacros = #macro_strings
    info.macros = macros_array
    info.numfactions = 0
    info.factions = nil
    info.relation = relation_str
    info.hazardous = false
    info.usemacrowhitelist = false
    info.usefactionwhitelist = false
    
    -- Create or update blacklist
    if not GT_Blacklist.fleet_blacklist_id then
        debugLog(string.format("Creating new fleet blacklist: %s", blacklist_name))
        GT_Blacklist.fleet_blacklist_id = C.CreateBlacklist2(info)
        debugLog(string.format("✅ Fleet blacklist created with ID: %d", GT_Blacklist.fleet_blacklist_id))
    else
        debugLog(string.format("Updating existing fleet blacklist ID: %d", GT_Blacklist.fleet_blacklist_id))
        info.id = GT_Blacklist.fleet_blacklist_id
        C.UpdateBlacklist2(info)
        debugLog("✅ Fleet blacklist updated")
    end
    
    return true
end

--- Apply blacklist to a specific ship
local function applyBlacklistToShip(ship_id, blacklist_id)
    if not ship_id or ship_id == 0 then
        debugLog("Invalid ship ID provided", "ERROR")
        return false
    end
    
    if not blacklist_id or blacklist_id == 0 then
        debugLog("Invalid blacklist ID provided", "ERROR")
        return false
    end
    
    -- Apply blacklist to ship for sector travel (no per-ship logging for performance)
    C.SetControllableBlacklist(ship_id, blacklist_id, "sectortravel", true)
    
    -- Track assignment
    GT_Blacklist.dynamic_blacklists[ship_id] = blacklist_id
    
    return true
end

--- Remove blacklist from a specific ship
local function removeBlacklistFromShip(ship_id)
    if not ship_id or ship_id == 0 then
        debugLog("Invalid ship ID provided", "ERROR")
        return false
    end
    
    local blacklist_id = GT_Blacklist.dynamic_blacklists[ship_id]
    if not blacklist_id then
        return true -- Already has no blacklist
    end
    
    -- Remove blacklist assignment (-1 = use default)
    C.SetControllableBlacklist(ship_id, -1, "sectortravel", false)
    
    -- Clear tracking
    GT_Blacklist.dynamic_blacklists[ship_id] = nil
    
    return true
end

--- Apply fleet blacklist to non-subordinate GT ships (subordinates inherit from commanders)
local function applyFleetBlacklistToAllShips(ship_list)
    if not GT_Blacklist.fleet_blacklist_id then
        debugLog("No fleet blacklist to apply", "WARN")
        return false
    end
    
    debugLog(string.format("Applying fleet blacklist to %d non-subordinate ships", #ship_list))
    
    -- Debug: Show first 3 ship ID strings
    if #ship_list > 0 then
        debugLog(string.format("Sample ship IDs: %s, %s, %s", 
            ship_list[1] or "nil", 
            ship_list[2] or "nil", 
            ship_list[3] or "nil"))
    end
    
    local success_count = 0
    local fail_count = 0
    for i, ship_id_string in ipairs(ship_list) do
        local ship_id = convertStringToID(ship_id_string)
        
        -- Debug first 3 conversions
        if i <= 3 then
            debugLog(string.format("  Ship %d: '%s' → ID: %s", i, ship_id_string, tostring(ship_id)))
        end
        
        if ship_id ~= 0 then
            if applyBlacklistToShip(ship_id, GT_Blacklist.fleet_blacklist_id) then
                success_count = success_count + 1
            else
                fail_count = fail_count + 1
            end
        else
            fail_count = fail_count + 1
            if i <= 3 then
                debugLog(string.format("  ❌ Failed to convert ship ID string: '%s'", ship_id_string), "WARN")
            end
        end
    end
    
    debugLog(string.format("✅ Fleet blacklist applied to %d/%d non-subordinate ships (%d failed)", success_count, #ship_list, fail_count))
    return true
end

-- =============================================================================
-- THREAT DATA PROCESSING
-- =============================================================================

--- Parse threat data from MD script format
local function parseThreatData(threat_data_string)
    debugLog(string.format("Parsing threat data: %s", threat_data_string))
    
    -- Format: "sector_macro1:level1:timestamp1|sector_macro2:level2:timestamp2|..."
    local threatened_macros = {}
    
    for sector_entry in string.gmatch(threat_data_string, "([^|]+)") do
        local parts = {}
        for part in string.gmatch(sector_entry, "([^:]+)") do
            table.insert(parts, part)
        end
        
        if #parts >= 3 then
            local sector_macro = parts[1]
            local threat_level = tonumber(parts[2]) or 0
            local timestamp = tonumber(parts[3]) or 0
            
            -- Only blacklist if threat level is above threshold and macro is valid
            if threat_level >= GT_Blacklist.CONFIG.THREAT_LEVEL_THRESHOLD and sector_macro and sector_macro ~= "" and sector_macro ~= "nil" then
                table.insert(threatened_macros, sector_macro)
                GT_Blacklist.blacklisted_sectors[sector_macro] = {
                    threat_level = threat_level,
                    timestamp = timestamp
                }
            end
        end
    end
    
    debugLog(string.format("Found %d sector macros above threat threshold", #threatened_macros))
    return threatened_macros
end

--- Clean up expired threats from tracking
local function cleanupExpiredThreats(current_time, expiry_time)
    local removed_count = 0
    
    for sector_name, threat_info in pairs(GT_Blacklist.blacklisted_sectors) do
        local age = current_time - threat_info.timestamp
        if age > expiry_time then
            GT_Blacklist.blacklisted_sectors[sector_name] = nil
            removed_count = removed_count + 1
        end
    end
    
    if removed_count > 0 then
        debugLog(string.format("Cleaned up %d expired threat entries", removed_count))
    end
    
    return removed_count
end

-- =============================================================================
-- EVENT HANDLERS - MD SCRIPT INTERFACE
-- =============================================================================

--- Initialize the blacklist system
local function onInitialize(_, event_data)
    debugLog("Initializing GalaxyTrader Dynamic Blacklist System...")
    
    if GT_Blacklist.initialized then
        debugLog("System already initialized", "WARN")
        return true
    end
    
    -- Verify FFI functions are available
    if type(C.CreateBlacklist2) ~= "cdata" then
        debugLog("ERROR: CreateBlacklist2 FFI function not available!", "ERROR")
        return false
    end
    
    -- Create empty blacklist at startup (avoids creation lag on first threat)
    debugLog("Creating empty fleet blacklist at startup...")
    local empty_sectors = {}
    local success = updateFleetBlacklist(empty_sectors)
    
    if success then
        debugLog("✅ Empty fleet blacklist created successfully")
    else
        debugLog("⚠️ Failed to create empty blacklist, will retry on first threat", "WARN")
    end
    
    GT_Blacklist.initialized = true
    debugLog("✅ Dynamic Blacklist System initialized successfully")
    
    return true
end

--- Update blacklists based on current threat data
local function onUpdateBlacklist(_, event_data)
    if not GT_Blacklist.initialized then
        debugLog("System not initialized - ignoring update request", "WARN")
        return false
    end
    
    debugLog("Received blacklist update request")
    
    -- Parse threat data from MD (empty string = no threats)
    local threatened_sectors = {}
    if event_data and event_data ~= "" then
        threatened_sectors = parseThreatData(event_data)
    else
        debugLog("No threat data provided - updating blacklist to empty")
    end
    
    -- Update fleet blacklist (will update to empty if no threats)
    return updateFleetBlacklist(threatened_sectors)
end

--- Apply blacklist to GT fleet ships
local function onApplyToFleet(_, event_data)
    if not GT_Blacklist.initialized then
        debugLog("System not initialized - ignoring apply request", "WARN")
        return false
    end
    
    debugLog("Received fleet application request")
    
    if not event_data or event_data == "" then
        debugLog("No ship list provided", "ERROR")
        return false
    end
    
    -- Parse ship list: "ship1,ship2,ship3,..."
    local ship_list = {}
    for ship_id in string.gmatch(event_data, "([^,]+)") do
        table.insert(ship_list, ship_id)
    end
    
    return applyFleetBlacklistToAllShips(ship_list)
end

--- Clean up expired threats and update blacklist
local function onCleanupExpired(_, event_data)
    if not GT_Blacklist.initialized then
        return false
    end
    
    -- Format: "current_time:expiry_time"
    local parts = {}
    for part in string.gmatch(event_data, "([^:]+)") do
        table.insert(parts, part)
    end
    
    if #parts < 2 then
        debugLog("Invalid cleanup parameters", "ERROR")
        return false
    end
    
    local current_time = tonumber(parts[1]) or 0
    local expiry_time = tonumber(parts[2]) or 3600
    
    debugLog(string.format("Cleaning up threats older than %d seconds", expiry_time))
    
    -- Remove expired threats
    local removed = cleanupExpiredThreats(current_time, expiry_time)
    
    -- Rebuild blacklist with remaining threats
    local threatened_sectors = {}
    for sector_name, _ in pairs(GT_Blacklist.blacklisted_sectors) do
        table.insert(threatened_sectors, sector_name)
    end
    
    updateFleetBlacklist(threatened_sectors)
    
    return true
end

--- Remove blacklist from a specific ship
local function onRemoveFromShip(_, event_data)
    if not GT_Blacklist.initialized then
        return false
    end
    
    local ship_id = convertStringToID(event_data)
    return removeBlacklistFromShip(ship_id)
end

-- =============================================================================
-- MODULE INITIALIZATION
-- =============================================================================

local function init()
    debugLog("================================================================================")
    debugLog("GalaxyTrader MK3 - Dynamic Blacklist Manager Loading...")
    debugLog("================================================================================")
    
    -- Verify FFI availability
    if not ffi then
        debugLog("ERROR: FFI not available!", "ERROR")
        return false
    end
    
    -- Register event handlers
    local events = {
        { name = "GT_Blacklist.Initialize",      handler = onInitialize },
        { name = "GT_Blacklist.Update",          handler = onUpdateBlacklist },
        { name = "GT_Blacklist.ApplyToFleet",    handler = onApplyToFleet },
        { name = "GT_Blacklist.CleanupExpired",  handler = onCleanupExpired },
        { name = "GT_Blacklist.RemoveFromShip",  handler = onRemoveFromShip },
    }
    
    for _, event in ipairs(events) do
        local success = pcall(RegisterEvent, event.name, event.handler)
        if success then
            debugLog(string.format("✅ Registered event: %s", event.name))
        else
            debugLog(string.format("❌ Failed to register event: %s", event.name), "ERROR")
        end
    end
    
    debugLog("================================================================================")
    debugLog("✅ Dynamic Blacklist Manager loaded successfully!")
    debugLog("Waiting for initialization signal from MD scripts...")
    debugLog("================================================================================")
    
    return true
end

-- Initialize module immediately
init()

-- Export module for debugging/testing
return GT_Blacklist

