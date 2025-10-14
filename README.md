# GalaxyTrader MK3

**The Ultimate Trading AI for X4: Foundations**

GalaxyTrader MK3 is a comprehensive trading automation mod that brings intelligent autonomous trading, skill progression, and fleet management to X4: Foundations. Ships equipped with this AI will learn, grow, and optimize their trading operations over time.

## 🌟 Currently Implemented Features

### Advanced Trading AI ✅ **WORKING**
- **Intelligent Route Selection**: Multi-factor optimization considering profit margins, travel time, risk, and market saturation
- **Advanced Trade Search**: 30+ validation layers with cross-station trade evaluation
- **Risk Management**: Configurable risk tolerance with automatic threat avoidance
- **Standard Cargo Handling**: Proper cargo space calculations and loading

### XP Progression System ✅ **WORKING**
- **15 Skill Levels**: From Apprentice (Level 1) to Long-Distance Merchant (Level 15)
- **Experience-Based Growth**: Ships gain XP from successful trades using diff patch integration
- **Distance & Risk Bonuses**: Extra XP for long-distance and dangerous trades
- **Skill Benefits**: Higher levels unlock greater jump distances and efficiency
- **Event-Driven XP**: Immediate XP award on trade completion (no polling delays)

### Mandatory Training System ✅ **WORKING**
- **Training Requirements**: Certification needed at levels 3, 6, 9, and 12
- **Station-Based Training**: Automatic docking at shipyards, wharfs, or trade stations
- **XP Blocking**: Complete progression halt until training is completed
- **Immersive Messages**: Professional logbook entries for training events
- **Auto-Navigation**: Ships automatically find and travel to training stations

### Ship Management ✅ **WORKING**
- **Auto-Renaming**: Ships display pilot rank, level, and XP in their names
- **Pilot Tracking**: Experience tied to individual pilots, not ships
- **Training Status**: Visual indicators for training requirements and progress
- **German/English Localization**: Full translation support

### Threat Intelligence System ✅ **WORKING**
- **Real-Time Threat Detection**: Monitors attacks, missiles, and ship destruction
- **Fleet-Wide Intelligence**: Ships share threat information across the fleet
- **5-Level Threat Classification**: From minor threats to critical emergencies
- **Sector Risk Assessment**: Automatic avoidance of recently threatened areas
- **Smart Notifications**: Fleet alerts for high-threat situations

### Performance Features ✅ **WORKING**
- **Event-Driven Architecture**: 3-5x faster than polling-based systems
- **Comprehensive Logging**: Detailed debug output and trade tracking
- **Professional Integration**: Compatible logbook message system
- **Save Game Safe**: No save game corruption or compatibility issues

## 🚧 Planned Features (TODO)

### Mobile Satellite Intelligence 🔄 **PARTIALLY IMPLEMENTED**
- **Specification Complete**: Full technical design documented
- **Mobile Market Data**: Ships act as advanced satellites (75km range)
- **Skill-Gated**: Only Level 9+ pilots (3+ stars) can gather intelligence
- **Fleet Network**: Multiple traders create comprehensive market coverage
- **Real-Time Updates**: Fresh market data during trading operations

### Skill-Based Bonus/Malus System 📋 **PLANNED**
- **Progressive feature unlocks based on pilot level**
- **Threat Intelligence access (Level 6+)**
- **Mobile Satellite Intelligence (Level 9+)**
- **Fleet Coordination access (Level 12+)**
- **Advanced Analytics (Level 15 only)**

### Trading Intelligence System 📋 **PLANNED**
- **Experience-Based Trade Evaluation**: Pilot skill affects trading decision quality
- **Progressive Analysis Speed**: From 5 seconds (Courier) to instant (Master)
- **Profit Threshold Scaling**: Apprentices accept 0%+, Masters demand 45%+
- **Technology Progression**: Advanced trading computers unlock with experience
- **Realistic Trading Behavior**: Poor decisions → optimal trading strategies

### Dynamic Ship Modifications 📋 **PLANNED**
- **Certification-Based Improvements**: Ship performance only changes at training milestones
- **Stable Performance Between Levels**: No gradual changes - pilots maintain current capabilities until next certification
- **Training-Gated Bonuses**: Each certification (Levels 3, 6, 9, 12, 15) unlocks new performance tier
- **Ship Class Awareness**: Different bonuses for S/M/L/XL ships based on certification level
- **Severe Capital Ship Penalties**: Apprentices face -15% (L-class) and -25% (XL-class) penalties
- **Meaningful Training Impact**: Each certification provides substantial and lasting improvements

### Advanced Cargo Management 📋 **PLANNED**
- **Multi-Commodity Trading**: Buy/sell multiple different wares per trip
- **Cargo Mix Optimization**: Intelligent combination of wares for maximum profit
- **Route Planning**: Multi-stop trips with different goods at each station

### Fleet Coordination 🔄 **PARTIALLY IMPLEMENTED**
- **Multi-Ship Management**: Coordinate entire trading fleets
- **Route Conflict Prevention**: Automatic distribution to avoid oversaturation
- **Territory Specialization**: Ships develop expertise in specific sectors
- **Load Balancing**: Dynamic workload distribution across fleet

### Market Intelligence 🔄 **PARTIALLY IMPLEMENTED**
- **Real-Time Analysis**: Market trend prediction and opportunity identification
- **Price History**: Track market volatility and timing
- **Supply/Demand**: Advanced economic analysis
- **Competitive Intelligence**: Monitor other traders and factions

### Advanced Analytics 📋 **PLANNED**
- **Profit Tracking**: Detailed performance metrics per ship
- **Fleet Reports**: Periodic summaries of trading operations
- **Session Statistics**: Track overall mod performance
- **Territory Management**: 5-level expertise system with profit bonuses

## 📦 Installation

### **Prerequisites**
- **Required**: SirNukes Mod Support APIs (Steam Workshop: ws_2042901274)
  - Provides global mod menu integration and configuration system
  - Available on Steam Workshop and Nexus Mods

### **Installation Steps**
1. **Install Dependencies**: Ensure Mod Support APIs is installed and enabled
2. **Download** the GalaxyTrader MK3 mod
3. **Extract** to your X4 extensions folder:
   - Windows: `Documents\Egosoft\X4\<UserID>\extensions\`
   - Linux: `~/.config/EgoSoft/X4/<UserID>/extensions/`
4. **Enable** the mod in the X4 Extensions menu
5. **Start/Load** your game

## 🚀 Getting Started

### Basic Setup
1. Assign a ship to trading duty using the "GalaxyTrader MK3" order
2. The mod will automatically detect and register the ship
3. Ship begins at Level 1 with basic trading capabilities (1 jump maximum)
4. Monitor progress through ship renaming and notifications

### Training Your Traders
- Ships will automatically notify you when training is required
- Training is **mandatory** at levels 3, 6, 9, and 12
- Ships automatically find and travel to training stations
- Training duration is currently fixed at 30 seconds (configurable in future)
- Ship resumes trading after certification with increased capabilities

## ⚙️ Configuration

All settings are centralized in the mod's configuration system:

### Trading Settings
- **Minimum Profit Threshold**: Set minimum acceptable profit (default: 100 Cr)
- **Risk Tolerance**: 0.0 (safe) to 1.0 (risky) - default: 0.5
- **Cargo Utilization**: Target cargo fill percentage (default: 90%)
- **Update Interval**: Market data refresh rate (default: 60s)

### XP System
- **Enable/Disable**: Toggle the progression system
- **Base XP**: XP awarded per trade (default: 50)
- **XP Multiplier**: Adjust progression speed
- **Training Mode**: Automatic or manual training control

### Notifications
- **Logbook Entries**: Enable professional trade messages
- **Training Messages**: Immersive training start/completion notifications
- **Level Up Alerts**: Pilot advancement announcements
- **Debug Output**: Comprehensive logging levels (0-2)

## 📊 Skill Progression & Feature Unlocks (UPDATED)

| Level | Title | Max Distance | Training Required | Feature Unlocks | Ship Modifications | Trading Intelligence |
|-------|-------|--------------|-------------------|-----------------|-------------------|-------------------|
| 1-2 | Apprentice | 1 jump | No | Basic trading only | **Small**: 0% / **Medium**: -5% / **Large**: -15% / **XL**: -25% | **Takes first non-negative trade** (0%+ profit) |
| 3 | Apprentice | 1 jump | **Yes** - Basic Certification | Training system unlocked | **Small**: +3% / **Medium**: 0% / **Large**: -8% / **XL**: -15% | **Takes first 5%+ profit trade** |
| 4-5 | Courier | 3 jumps | No | Extended range trading | **Small**: +3% / **Medium**: 0% / **Large**: -8% / **XL**: -15% | **Manual comparison**: 5 sec/trade, 10%+ target |
| 6 | Courier | 3 jumps | **Yes** - Advanced Trade | **Threat Intelligence Access** | **Small**: +6% / **Medium**: +3% / **Large**: 0% / **XL**: -8% | **Enhanced comparison**: 3 sec/trade, 15%+ target |
| 7-8 | Supplier | 5 jumps | No | Regional trading expertise | **Small**: +6% / **Medium**: +3% / **Large**: 0% / **XL**: -8% | **Regional optimization**: 2 sec/trade, 20%+ target |
| 9 | Supplier | 5 jumps | **Yes** - Expert Trader | **Mobile Satellite Intelligence** | **Small**: +9% / **Medium**: +6% / **Large**: +3% / **XL**: 0% | **Advanced computer**: 1 sec/trade, 25%+ target |
| 10-11 | Trader | 10 jumps | No | Long-distance trading | **Small**: +9% / **Medium**: +6% / **Large**: +3% / **XL**: 0% | **Smart algorithms**: 0.5 sec/trade, 30%+ target |
| 12 | Trader | 10 jumps | **Yes** - Master Certification | **Fleet Coordination Access** | **Small**: +12% / **Medium**: +9% / **Large**: +6% / **XL**: +3% | **Master computer**: Instant analysis, 35%+ target |
| 13-14 | Merchant | 15 jumps | No | Cross-galaxy trading | **Small**: +12% / **Medium**: +9% / **Large**: +6% / **XL**: +3% | **Predictive analysis**: Instant, 40%+ target |
| 15 | Long-Distance Merchant | 25 jumps | No | Maximum capabilities | **Small**: +15% / **Medium**: +12% / **Large**: +9% / **XL**: +6% | **AI-assisted trading**: Instant, 45%+ optimal |

### **Ship Class Definitions:**
- **Small**: Fighters, scouts, small traders (S-class)
- **Medium**: Medium traders, corvettes (M-class)  
- **Large**: Large traders, destroyers (L-class) - **Severe apprentice penalties**
- **XL**: Capital traders, carriers (XL-class) - **Extreme apprentice penalties**

### **Trading Intelligence Progression:**
- **Apprentice (1-2)**: Takes any non-negative trade immediately - no analysis
- **Basic Certified (3)**: Requires minimum 5% profit before accepting
- **Courier (4-6)**: Manual trade comparison, 5 seconds per opportunity evaluation
- **Advanced Trade (6)**: Enhanced comparison speed, 3 seconds per trade
- **Supplier (7-9)**: Regional trading expertise, 2 seconds per trade analysis
- **Expert Trader (9)**: Advanced trading computer access, 1 second per trade
- **Master Trader (12+)**: Instant analysis with sophisticated algorithms
- **Long-Distance Merchant (15)**: AI-assisted trading with predictive capabilities

### **Feature Access Requirements:**
- **Basic Trading**: All levels
- **Threat Intelligence**: Level 6+ (Courier rank)
- **Mobile Satellite Intelligence**: Level 9+ (Supplier rank)  
- **Fleet Coordination**: Level 12+ (Trader rank)
- **Advanced Analytics**: Level 15 (Long-Distance Merchant)

### **Ship Performance Logic:**
- **Certification-Based Changes**: Ship performance only changes at training milestones (Levels 3, 6, 9, 12, 15)
- **Stable Performance Between Levels**: No gradual changes - pilots maintain current capabilities until next certification
- **Training Impact**: Each certification unlocks meaningful ship handling improvements
- **Capital Ship Penalties**: Severe penalties for apprentices on L-class (-15%), extreme penalties on XL-class (-25%)
- **Realistic Progression**: Large capital ships require significant experience to operate effectively

### **Trading Intelligence Logic:**
- **Experience-Based Decision Making**: Pilot skill directly affects trade opportunity evaluation
- **Progressive Analysis Speed**: Advanced pilots can evaluate trades faster (5 sec → instant)
- **Profit Threshold Scaling**: Higher-level pilots demand better profit margins (0% → 45%)
- **Technology Access**: Advanced trading computers unlock at higher certification levels
- **Realistic Trading Behavior**: Apprentices make poor decisions, masters optimize perfectly

## 🛠️ Troubleshooting

### Ship Not Gaining XP
- Check if XP system is enabled in configuration
- Verify ship is completing trades (selling goods, not just buying)
- Ensure ship isn't blocked at training threshold

### Training Not Starting
- Training is automatic when enabled
- Ship will show "[TRAINING]" prefix when training begins
- Check debug log for training station detection messages

### Ships Stuck with Question Marks
- The anti-stuck protection should prevent this
- Check debug log for validation failure messages
- Ensure stations are operational and accessible

## 🤝 Compatibility

- **Game Version**: X4 6.0+
- **DLC**: Compatible with all DLCs (not required)
- **Other Mods**: Designed for compatibility
  - Works alongside other trading mods
  - Respects faction relation mods
  - Compatible with economy overhauls

## 📝 Credits

- **Author**: GoAhead
- **Version**: 1.0.0
- **License**: MIT (see LICENSE.md)

## 🐛 Bug Reports & Suggestions

Please report issues or suggestions through the mod's official channels:
- Steam Workshop discussions
- Egosoft forums mod thread
- GitHub issues (if applicable)

## 🎮 Tips for Success

1. **Start Small**: Begin with 1-2 ships to learn the system
2. **Training Stations**: Position ships near shipyards/wharfs at levels 2, 5, 8, 11
3. **Skill Progression**: Let pilots advance naturally through trading
4. **Debug Logging**: Enable debug output to monitor system performance
5. **Save Regularly**: While save-safe, regular saves are always recommended

---

*GalaxyTrader MK3 - Teaching your ships to trade smarter, not harder!* 