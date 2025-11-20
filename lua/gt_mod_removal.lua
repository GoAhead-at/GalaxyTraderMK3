--[[
GalaxyTrader MK3 - Equipment Mod Removal Lua Module
Handles removal of GT-installed modifications using C API
]]

local GT_ModRemoval = {}

-- Debug logging wrapper
-- Note: X4 Lua only has DebugError and DebugWarning, not DebugLog
local function logDebug(message, level)
    level = level or "INFO"
    local prefix = "[GT-Mods-Lua] "
    if level == "ERROR" then
        DebugError(prefix .. message)
    elseif level == "WARNING" then
        DebugWarning(prefix .. message)
    else
        -- Use DebugError for info messages (appears in log but not as critical error)
        DebugError(prefix .. message)
    end
end

-- FFI setup for C API access
local ffi = require("ffi")
local C = ffi.C

-- FFI definitions for C API mod removal functions
ffi.cdef[[
    typedef uint64_t UniverseID;
    void DismantleShipMod(UniverseID shipid);
    void DismantleEngineMod(UniverseID objectid);
    void DismantleShieldMod(UniverseID defensibleid, UniverseID contextid, const char* group);
    void DismantleWeaponMod(UniverseID weaponid);
    void DismantleThrusterMod(UniverseID objectid);
    bool InstallEngineMod(UniverseID objectid, const char* wareid);
    bool InstallShipMod(UniverseID shipid, const char* wareid);
    bool InstallShieldMod(UniverseID defensibleid, UniverseID contextid, const char* group, const char* wareid);
]]

-- Convert string to 64-bit integer (ship ID from MD)
-- MD passes ship object as numeric ID string when concatenated
local function ConvertStringTo64Bit(str)
    if not str or str == "" then
        logDebug("ERROR: Empty string passed to ConvertStringTo64Bit", "ERROR")
        return 0
    end
    local num = tonumber(str)
    if not num then
        logDebug(string.format("ERROR: Failed to convert '%s' to number", tostring(str)), "ERROR")
        return 0
    end
    return ffi.cast("uint64_t", num)
end

-- Split pipe-separated parameters (format: "type|shipId|componentId|contextId|group")
local function SplitParams(params, sep)
    sep = sep or "|"
    local result = {}
    local pattern = string.format("([^%s]+)", sep)
    for match in string.gmatch(params, pattern) do
        table.insert(result, match)
    end
    return result
end

-- Remove modification from ship
local function GT_DismantleMod(_, params)
    -- Parse parameters: "type|shipId|shipIdCode|componentId|contextId|group"
    -- Format: "ship|12345|ABC-123|0|0|null" or "engine|12345|ABC-123|0|0|null"
    -- Note: shipIdCode is optional (for backward compatibility), defaults to numeric ID if not provided
    if not params then
        logDebug("ERROR: GT_DismantleMod called with nil params", "ERROR")
        return
    end
    
    local tPackets = SplitParams(params, "|")
    if not tPackets[1] or not tPackets[2] then
        logDebug(string.format("ERROR: Invalid params format: %s", tostring(params)), "ERROR")
        return
    end
    
    local type = tPackets[1]
    local shipIdStr = tPackets[2]
    local shipIdCode = tPackets[3] or shipIdStr  -- Use shipIdCode if provided, otherwise fall back to numeric ID
    local shipId = ConvertStringTo64Bit(shipIdStr)
    
    -- FIX: Include readable ship ID code in log messages
    logDebug(string.format("Removing %s mod from ship ID string: %s (converted: %s) => %s", type, shipIdStr, tostring(shipId), shipIdCode))
    
    if type == "ship" then
        C.DismantleShipMod(shipId)
        logDebug(string.format("Removed ship mod from ship ID: %s => %s", tostring(shipId), shipIdCode))
    elseif type == "engine" then
        C.DismantleEngineMod(shipId)
        logDebug(string.format("Removed engine mod from ship ID: %s => %s", tostring(shipId), shipIdCode))
    elseif type == "shield" then
        -- For shield mods, we need context (ship) and group
        -- If group is "null" or not provided, we need to remove from all groups
        -- For now, try removing with ship as context and nil group
        -- Note: Parameters shifted - componentId is now tPackets[4], contextId is tPackets[5], group is tPackets[6]
        local contextId = shipId -- Ship is the context
        local group = (tPackets[6] and tPackets[6] ~= "null") and tPackets[6] or nil
        
        if group then
            C.DismantleShieldMod(shipId, contextId, group)
            logDebug(string.format("Removed shield mod from ship ID: %s => %s, group: %s", tostring(shipId), shipIdCode, group))
        else
            -- Try removing with nil group (may remove from all groups)
            -- Note: This might need iteration through actual shield groups
            C.DismantleShieldMod(shipId, contextId, nil)
            logDebug(string.format("Removed shield mod from ship ID: %s => %s (all groups)", tostring(shipId), shipIdCode))
        end
    elseif type == "weapon" then
        -- For weapon mods, we need the component ID
        -- Component ID is provided from MD script iteration
        -- Note: Parameters shifted - componentId is now tPackets[4]
        local componentId = (tPackets[4] and tonumber(tPackets[4]) ~= 0) and ConvertStringTo64Bit(tostring(tonumber(tPackets[4]))) or nil
        
        if componentId then
            C.DismantleWeaponMod(componentId)
            logDebug(string.format("Removed weapon mod from component ID: %s (ship: %s)", tostring(componentId), shipIdCode))
        else
            logDebug(string.format("⚠ WARNING: No component ID provided for weapon mod - cannot remove individual weapon mods without component ID (ship: %s)", shipIdCode), "WARNING")
        end
    elseif type == "thruster" then
        C.DismantleThrusterMod(shipId)
        logDebug(string.format("Removed thruster mod from ship ID: %s => %s", tostring(shipId), shipIdCode))
    else
        logDebug(string.format("ERROR: Unknown mod type: %s", type), "ERROR")
    end
end

-- Install modification on ship
local function GT_InstallMod(_, params)
    -- Parse parameters: "type|shipId|wareId"
    -- Format: "thruster|12345|mod_thruster_gt_level1"
    local tPackets = SplitParams(params, "|")
    local type = tPackets[1]
    local shipId = ConvertStringTo64Bit(tostring(tonumber(tPackets[2])))
    local wareId = tPackets[3]
    
    logDebug(string.format("Installing %s mod (%s) on ship ID: %s", type, wareId, tostring(shipId)))
    
    if type == "thruster" then
        -- Thruster mods are installed via InstallEngineMod since they affect engine properties
        local success = C.InstallEngineMod(shipId, wareId)
        if success then
            logDebug(string.format("Installed thruster mod (%s) on ship ID: %s", wareId, tostring(shipId)))
        else
            logDebug(string.format("Failed to install thruster mod (%s) on ship ID: %s", wareId, tostring(shipId)), "ERROR")
        end
    else
        logDebug(string.format("ERROR: Unknown mod type for installation: %s", type), "ERROR")
    end
end

-- Initialize module
local function init()
    logDebug("================================================================================")
    logDebug("GalaxyTrader MK3 - Mod Removal Lua Module Loading...")
    logDebug("================================================================================")
    
    -- Verify FFI availability
    if not ffi then
        logDebug("ERROR: FFI not available!", "ERROR")
        return false
    end
    
    -- Register event handlers
    local success1 = pcall(RegisterEvent, "GT_DismantleMod", GT_DismantleMod)
    if success1 then
        logDebug("Registered event: GT_DismantleMod")
    else
        logDebug("Failed to register event: GT_DismantleMod", "ERROR")
        return false
    end
    
    local success2 = pcall(RegisterEvent, "GT_InstallMod", GT_InstallMod)
    if success2 then
        logDebug("Registered event: GT_InstallMod")
    else
        logDebug("Failed to register event: GT_InstallMod", "ERROR")
        return false
    end
    
    logDebug("================================================================================")
    logDebug("Mod Removal Lua Module loaded successfully!")
    logDebug("================================================================================")
    
    return true
end

-- Initialize module immediately
init()

-- Export module
return GT_ModRemoval

