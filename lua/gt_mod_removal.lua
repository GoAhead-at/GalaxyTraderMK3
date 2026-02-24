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
        -- Some runtimes don't expose DebugWarning; use DebugError as safe fallback.
        DebugError(prefix .. message)
    end
end

-- FFI setup for C API access
local ffi = require("ffi")
local C = ffi.C

-- FFI definitions for C API mod removal functions
ffi.cdef[[
    typedef uint64_t UniverseID;
    typedef struct {
        const char* Name;
        const char* RawName;
        const char* Ware;
        uint32_t Quality;
        const char* PropertyType;
        float ForwardThrustFactor;
        float StrafeAccFactor;
        float StrafeThrustFactor;
        float RotationThrustFactor;
        float BoostAccFactor;
        float BoostThrustFactor;
        float BoostDurationFactor;
        float BoostAttackTimeFactor;
        float BoostReleaseTimeFactor;
        float BoostChargeTimeFactor;
        float BoostRechargeTimeFactor;
        float TravelThrustFactor;
        float TravelStartThrustFactor;
        float TravelAttackTimeFactor;
        float TravelReleaseTimeFactor;
        float TravelChargeTimeFactor;
    } UIEngineMod2;
    typedef struct {
        const char* Name;
        const char* RawName;
        const char* Ware;
        uint32_t Quality;
        const char* PropertyType;
        float MassFactor;
        float DragFactor;
        float MaxHullFactor;
        float RadarRangeFactor;
        uint32_t AddedUnitCapacity;
        uint32_t AddedMissileCapacity;
        uint32_t AddedCountermeasureCapacity;
        uint32_t AddedDeployableCapacity;
        float RadarCloakFactor;
        float RegionDamageProtection;
        float HideCargoChance;
    } UIShipMod2;
    void DismantleShipMod(UniverseID shipid);
    void DismantleEngineMod(UniverseID objectid);
    void DismantleShieldMod(UniverseID defensibleid, UniverseID contextid, const char* group);
    void DismantleWeaponMod(UniverseID weaponid);
    void DismantleThrusterMod(UniverseID objectid);
    bool InstallEngineMod(UniverseID objectid, const char* wareid);
    bool InstallShipMod(UniverseID shipid, const char* wareid);
    bool InstallShieldMod(UniverseID defensibleid, UniverseID contextid, const char* group, const char* wareid);
    bool GetInstalledEngineMod2(UniverseID objectid, UIEngineMod2* enginemod);
    bool GetInstalledShipMod2(UniverseID shipid, UIShipMod2* shipmod);
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

local function SafeCString(value, defaultValue)
    defaultValue = defaultValue or "none"
    if value == nil then
        return defaultValue
    end
    local ok, text = pcall(ffi.string, value)
    if ok and text and text ~= "" then
        return text
    end
    return defaultValue
end

local function IsGTShipModWareId(wareId)
    return wareId == "mod_ship_gt_level1"
        or wareId == "mod_ship_gt_level2"
        or wareId == "mod_ship_gt_level3"
        or wareId == "mod_penalty_ship_light"
        or wareId == "mod_penalty_ship_moderate"
        or wareId == "mod_penalty_ship_severe"
        or wareId == "mod_penalty_light"
        or wareId == "mod_penalty_moderate"
        or wareId == "mod_penalty_severe"
end

local function IsGTEngineModWareId(wareId)
    return wareId == "mod_engine_gt_level1"
        or wareId == "mod_engine_gt_level2"
        or wareId == "mod_engine_gt_level3"
        or wareId == "mod_penalty_engine_light"
        or wareId == "mod_penalty_engine_moderate"
        or wareId == "mod_penalty_engine_severe"
        or wareId == "mod_penalty_light"
        or wareId == "mod_penalty_moderate"
        or wareId == "mod_penalty_severe"
end

local function GT_DismantleDetectedGTMods(_, params)
    -- Format: "shipId|shipIdCode|reason"
    if not params then
        logDebug("ERROR: GT_DismantleDetectedGTMods called with nil params", "ERROR")
        return
    end

    local tPackets = SplitParams(params, "|")
    if not tPackets[1] then
        logDebug(string.format("ERROR: Invalid GT_DismantleDetectedGTMods params format: %s", tostring(params)), "ERROR")
        return
    end

    local shipIdStr = tPackets[1]
    local shipIdCode = tPackets[2] or shipIdStr
    local reason = tPackets[3] or "manual"
    local shipId = ConvertStringTo64Bit(shipIdStr)

    local shipBuf = ffi.new("UIShipMod2")
    local engineBuf = ffi.new("UIEngineMod2")
    local hasShip = C.GetInstalledShipMod2(shipId, shipBuf)
    local hasEngine = C.GetInstalledEngineMod2(shipId, engineBuf)
    local shipWare = hasShip and SafeCString(shipBuf.Ware) or "none"
    local engineWare = hasEngine and SafeCString(engineBuf.Ware) or "none"

    local removedShip = false
    local removedEngine = false

    if hasShip and IsGTShipModWareId(shipWare) then
        C.DismantleShipMod(shipId)
        removedShip = true
    end
    if hasEngine and IsGTEngineModWareId(engineWare) then
        C.DismantleEngineMod(shipId)
        removedEngine = true
    end

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
    
    if type == "ship" then
        C.DismantleShipMod(shipId)
    elseif type == "engine" then
        C.DismantleEngineMod(shipId)
    elseif type == "shield" then
        -- For shield mods, we need context (ship) and group
        -- If group is "null" or not provided, we need to remove from all groups
        -- For now, try removing with ship as context and nil group
        -- Note: Parameters shifted - componentId is now tPackets[4], contextId is tPackets[5], group is tPackets[6]
        local contextId = shipId -- Ship is the context
        local group = (tPackets[6] and tPackets[6] ~= "null") and tPackets[6] or nil
        
        if group then
            C.DismantleShieldMod(shipId, contextId, group)
        else
            -- Cannot pass nil to const char* parameter - FFI will crash
            -- Pass empty string instead (X4 may interpret this as "all groups" or skip if not supported)
            -- Note: This might need iteration through actual shield groups if empty string doesn't work
            C.DismantleShieldMod(shipId, contextId, "")
        end
    elseif type == "weapon" then
        -- For weapon mods, we need the component ID
        -- Component ID is provided from MD script iteration
        -- Note: Parameters shifted - componentId is now tPackets[4]
        local componentId = (tPackets[4] and tonumber(tPackets[4]) ~= 0) and ConvertStringTo64Bit(tostring(tonumber(tPackets[4]))) or nil
        
        if componentId then
            C.DismantleWeaponMod(componentId)
        else
            logDebug(string.format("⚠ WARNING: No component ID provided for weapon mod - cannot remove individual weapon mods without component ID (ship: %s)", shipIdCode), "WARNING")
        end
    elseif type == "thruster" then
        C.DismantleThrusterMod(shipId)
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
    
    if type == "thruster" then
        -- Thruster mods are installed via InstallEngineMod since they affect engine properties
        local success = C.InstallEngineMod(shipId, wareId)
        if not success then
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

    local success3 = pcall(RegisterEvent, "GT_DismantleDetectedGTMods", GT_DismantleDetectedGTMods)
    if success3 then
        logDebug("Registered event: GT_DismantleDetectedGTMods")
    else
        logDebug("Failed to register event: GT_DismantleDetectedGTMods", "ERROR")
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

