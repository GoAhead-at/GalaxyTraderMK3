--[[
==============================================================================
GalaxyTrader MK3 - UI Element Library
==============================================================================
Reusable UI components for consistent styling and behavior across all GT UI

Features:
- Standard table creation with scrolling support
- Consistent button styling
- Text formatting helpers
- Row creation helpers
- Header creation helpers

Usage:
    local GT_UI = require("extensions/GalaxyTraderMK3/ui/gt_ui_library")
    local table = GT_UI.createStandardTable(frame, 10, { y = 0 })

Author: GalaxyTrader Development Team
Version: 1.0
==============================================================================
]]--

local GT_UI = {}

-- =============================================================================
-- CONFIGURATION
-- =============================================================================

GT_UI.CONFIG = {
    -- Standard dimensions
    rowHeight = Helper.standardTextHeight,
    fontSize = Helper.standardFontSize,
    -- Calculate standard width: use playerInfoConfig.width minus sidebar and borders (like vanilla)
    -- This gives us the actual available width for tables in the info menu
    -- Add safety margin to ensure we don't exceed max width
    standardWidth = (function()
        local sidebarWidth = Helper.sidebarWidth or 40
        local borderSize = Helper.borderSize or 3
        local safetyMargin = 5  -- Safety margin to ensure we stay under max width
        local baseWidth = (Helper.playerInfoConfig and Helper.playerInfoConfig.width) or (Helper.viewWidth * 0.8)
        return baseWidth - sidebarWidth - borderSize - safetyMargin
    end)(),
    
    -- Colors
    colors = {
        rowTitleBackground = Color["row_title_background"],
        rowBackgroundSelected = Color["row_background_selected"],
        buttonBackgroundDefault = Color["button_background_default"],
        textWarning = Color["text_warning"],
    },
}

-- =============================================================================
-- TABLE CREATION
-- =============================================================================

--[[
    Creates a standard table with scrolling support and default cell properties
    
    Parameters:
        frame: Parent frame to add table to
        columnCount: Number of columns
        options: Table with optional parameters:
            - tabOrder: Tab order (default: 2)
            - width: Table width (default: standardWidth)
            - y: Y offset (default: 0)
            - maxVisibleHeight: Max visible height (default: Helper.viewHeight)
            - rowHeight: Row height (default: CONFIG.rowHeight)
            - fontSize: Font size (default: CONFIG.fontSize)
    
    Returns:
        table: Configured table object
]]
function GT_UI.createStandardTable(frame, columnCount, options)
    options = options or {}
    
    -- Ensure width is valid (not 0 or negative)
    local tableWidth = options.width or GT_UI.CONFIG.standardWidth
    if tableWidth <= 0 then
        DebugError(string.format("[GT UI] Warning: Invalid table width %d, using default", tableWidth))
        tableWidth = GT_UI.CONFIG.standardWidth
    end
    
    -- Don't set x position - it causes width=0 issues in X4
    -- Let X4 handle table positioning within the frame
    
    -- Use reserveScrollBar = true when using fixed pixel widths
    -- When using setColWidth (pixels), remaining columns become variable width automatically
    local table = frame:addTable(columnCount, {
        tabOrder = options.tabOrder or 2,
        reserveScrollBar = true,  -- Enable scrollbar when using fixed pixel widths
        width = tableWidth,
        -- x = options.x,  -- REMOVED: Causes width=0 issues
        y = options.y or 0,
        maxVisibleHeight = options.maxVisibleHeight or Helper.viewHeight
    })
    
    -- Set default cell properties
    table:setDefaultCellProperties("text", {
        minRowHeight = options.rowHeight or GT_UI.CONFIG.rowHeight,
        fontsize = options.fontSize or GT_UI.CONFIG.fontSize
    })
    
    return table
end

--[[
    Sets column widths using fixed pixel values
    
    Parameters:
        table: Table object
        widths: Array of width values in pixels (remaining columns become variable width)
    
    Example:
        GT_UI.setColumnWidths(table, {30, 300, 200, 150})
        -- Columns 1-4 get fixed pixel widths, remaining columns are variable
    
    Note: Uses setColWidth (pixels) instead of setColWidthPercent
    This avoids scrollbar finalization errors!
]]
function GT_UI.setColumnWidths(table, widths)
    if not widths or #widths == 0 then
        return
    end
    
    -- Get total column count from table
    local totalColumns = table.numcolumns
    if not totalColumns or totalColumns == 0 then
        -- Fallback: infer from widths (assumes remaining columns are variable)
        totalColumns = #widths + 1
    end
    
    -- Verify table has valid width before setting column widths
    if table.properties and table.properties.width and table.properties.width <= 0 then
        DebugError(string.format("[GT UI] Warning: Table width is %d, cannot set column widths", table.properties.width))
        return
    end
    
    -- Set widths for columns 1 through (#widths) using fixed pixel values
    -- Remaining columns automatically become variable width for scrollbar
    for i = 1, #widths do
        if widths[i] and widths[i] > 0 then
            table:setColWidth(i, widths[i])
        end
    end
    
    -- CRITICAL: Remaining columns (from #widths+1 to totalColumns) are left unset
    -- This makes them variable width, which automatically accommodates the scrollbar
    -- This approach avoids scrollbar finalization errors!
end

-- =============================================================================
-- HEADER CREATION
-- =============================================================================

--[[
    Creates a standard header row
    
    Parameters:
        table: Table object
        headers: Array of header configurations:
            - Can be string (text) or table with:
                - text: Header text
                - textId: Text ID for ReadText (if text not provided)
                - halign: Horizontal alignment (default: "center")
                - sortable: Whether header is sortable (default: false)
                - sortColumn: Column name for sorting (if sortable)
                - currentSort: Current sort state {column, descending}
                - onSort: Sort callback function (if sortable)
        isFixed: Whether header is fixed (default: true)
    
    Returns:
        row: Header row object
]]
function GT_UI.createHeaderRow(table, headers, isFixed)
    isFixed = (isFixed ~= false)  -- Default to true
    
    local headerRow = table:addRow(true, {
        bgColor = GT_UI.CONFIG.colors.rowTitleBackground,
        fixed = isFixed
    })
    
    -- Get total column count to ensure we don't exceed table columns
    local totalColumns = table.numcolumns or #headers
    
    for i, headerConfig in ipairs(headers) do
        -- Only create headers for columns that exist (don't exceed table column count)
        if i > totalColumns then
            break
        end
        
        local cell = headerRow[i]
        if not cell then
            -- Safety check: if cell doesn't exist, skip
            break
        end
        
        local text = ""
        local halign = "center"
        local isSortable = false
        local sortColumn = nil
        local currentSort = nil
        local onSort = nil
        
        -- Handle string or table configuration
        if type(headerConfig) == "string" then
            text = headerConfig
        else
            text = headerConfig.text or (headerConfig.textId and ReadText(77000, headerConfig.textId)) or ""
            halign = headerConfig.halign or "center"
            isSortable = headerConfig.sortable or false
            sortColumn = headerConfig.sortColumn
            currentSort = headerConfig.currentSort
            onSort = headerConfig.onSort
        end
        
        -- Ensure text is not empty (X4 requires content in cells)
        if text == "" then
            text = " "  -- Use space as placeholder
        end
        
        -- Always create content - X4 requires content in every cell
        if isSortable and onSort then
            -- Create sortable header button
            local displayText = text
            
            -- Add arrow indicator for currently sorted column
            if currentSort and currentSort.column == sortColumn then
                displayText = displayText .. (currentSort.descending and " ▼" or " ▲")
            end
            
            local btn = cell:createButton({ height = GT_UI.CONFIG.rowHeight })
            if btn then
                btn:setText(displayText, { halign = halign })
                cell.handlers.onClick = function()
                    onSort(sortColumn)
                    return true
                end
            else
                -- Fallback: create text if button creation fails
                cell:createText(text, { halign = halign })
            end
        else
            -- Create simple text header
            cell:createText(text, { halign = halign })
        end
    end
    
    return headerRow
end

-- =============================================================================
-- ROW CREATION
-- =============================================================================

--[[
    Creates a standard data row
    
    Parameters:
        table: Table object
        cells: Array of cell configurations:
            - Can be string (text) or table with:
                - text: Cell text
                - halign: Horizontal alignment (default: "left")
                - cellBGColor: Background color (for selection highlighting)
                - onClick: Click handler (makes row selectable if provided)
        isSelectable: Whether row is selectable (default: false)
        bgColor: Row background color (optional)
    
    Returns:
        row: Row object
]]
function GT_UI.createDataRow(table, cells, isSelectable, bgColor)
    isSelectable = isSelectable or false
    
    local rowOptions = {}
    if bgColor then
        rowOptions.bgColor = bgColor
    end
    
    local row = table:addRow(isSelectable, rowOptions)
    
    for i, cellConfig in ipairs(cells) do
        local cell = row[i]
        local text = ""
        local halign = "left"
        local cellBGColor = nil
        local onClick = nil
        
        -- Handle string or table configuration
        if type(cellConfig) == "string" then
            text = cellConfig
        else
            text = cellConfig.text or ""
            halign = cellConfig.halign or "left"
            cellBGColor = cellConfig.cellBGColor
            onClick = cellConfig.onClick
        end
        
        cell:createText(text, { halign = halign, cellBGColor = cellBGColor })
        
        if onClick then
            cell.handlers.onClick = onClick
        end
    end
    
    return row
end

--[[
    Creates an empty row with a message spanning all columns
    
    Parameters:
        table: Table object
        message: Message text
        columnCount: Number of columns to span (default: table column count)
        options: Optional table with:
            - fontSize: Font size multiplier (default: 1.0)
            - halign: Horizontal alignment (default: "center")
    
    Returns:
        row: Empty row object
]]
function GT_UI.createEmptyRow(table, message, columnCount, options)
    options = options or {}
    columnCount = columnCount or table:getColumnCount()
    
    local row = table:addRow(nil, {})
    local fontSize = options.fontSize or 1.0
    local halign = options.halign or "center"
    
    row[1]:setColSpan(columnCount):createText(message, {
        halign = halign,
        fontsize = GT_UI.CONFIG.fontSize * fontSize
    })
    
    return row
end

-- =============================================================================
-- BUTTON CREATION
-- =============================================================================

--[[
    Creates a standard button
    
    Parameters:
        cell: Cell object to add button to
        text: Button text (or textId for ReadText)
        options: Table with optional parameters:
            - textId: Text ID for ReadText (if text not provided)
            - height: Button height (default: rowHeight)
            - bgColor: Background color (default: buttonBackgroundDefault)
            - fontSize: Font size multiplier (default: 0.8)
            - halign: Horizontal alignment (default: "center")
            - color: Text color (optional)
            - onClick: Click handler function
    
    Returns:
        button: Button object
]]
function GT_UI.createButton(cell, text, options)
    options = options or {}
    
    -- Get text
    local displayText = text
    if options.textId then
        displayText = ReadText(77000, options.textId)
    end
    
    -- Create button
    local button = cell:createButton({
        height = options.height or GT_UI.CONFIG.rowHeight,
        bgColor = options.bgColor or GT_UI.CONFIG.colors.buttonBackgroundDefault
    })
    
    -- Set button text
    local fontSize = (options.fontSize or 0.8) * GT_UI.CONFIG.fontSize
    local textOptions = {
        halign = options.halign or "center",
        fontsize = fontSize
    }
    if options.color then
        textOptions.color = options.color
    end
    button:setText(displayText, textOptions)
    
    -- Set click handler
    if options.onClick then
        cell.handlers.onClick = function()
            options.onClick()
            return true
        end
    end
    
    return button
end

-- =============================================================================
-- TEXT FORMATTING
-- =============================================================================

--[[
    Formats money with M/B suffixes
    
    Parameters:
        amount: Amount in cents
    
    Returns:
        string: Formatted money string (e.g., "1.5M Cr", "2.3B Cr")
]]
function GT_UI.formatMoney(amount)
    local credits = amount / 100  -- Convert from cents to credits
    if credits >= 1000000000 then
        return string.format("%.1fB Cr", credits / 1000000000)
    elseif credits >= 1000000 then
        return string.format("%.1fM Cr", credits / 1000000)
    else
        return ConvertMoneyString(amount, false, false, 0, true)
    end
end

--[[
    Formats XP as "current / next" (e.g., "1500 / 2000")
    
    Parameters:
        current: Current XP value
        next: Next level XP threshold
    
    Returns:
        string: Formatted XP string
]]
function GT_UI.formatXP(current, next)
    return string.format("%d / %d", current or 0, next or 1000)
end

-- =============================================================================
-- UTILITY FUNCTIONS
-- =============================================================================

--[[
    Gets selection background color for a row
    
    Parameters:
        isSelected: Whether row is selected
    
    Returns:
        color: Background color or nil
]]
function GT_UI.getSelectionColor(isSelected)
    return isSelected and GT_UI.CONFIG.colors.rowBackgroundSelected or nil
end

--[[
    Creates a footer row with totals
    
    Parameters:
        table: Table object
        message: Footer message (e.g., "Total Pilots: 80")
        columnCount: Number of columns to span (default: table column count)
    
    Returns:
        row: Footer row object
]]
function GT_UI.createFooterRow(table, message, columnCount)
    columnCount = columnCount or table:getColumnCount()
    
    local footerRow = table:addRow(nil, {
        bgColor = GT_UI.CONFIG.colors.rowTitleBackground
    })
    
    footerRow[1]:setColSpan(columnCount):createText(message, {})
    
    return footerRow
end

-- =============================================================================
-- MODULE EXPORT
-- =============================================================================

-- Export as global for X4 ui.xml loading (files loaded via ui.xml don't use require)
-- Also return for compatibility if require is used
if not _G.GT_UI then
    _G.GT_UI = GT_UI
end

return GT_UI

