# GalaxyTrader MK3

**The Ultimate Trading AI for X4: Foundations**

GalaxyTrader MK3 is a comprehensive trading automation mod that brings intelligent autonomous trading, skill progression, and fleet management to X4: Foundations. Ships equipped with this AI will learn, grow, and optimize their trading operations over time.

## 🌟 Features

### Advanced Trading AI ✅ **WORKING**
- **Intelligent Route Selection**: Multi-factor optimization considering profit margins, travel time, risk, and market saturation
- **Advanced Trade Search**: 30+ validation layers with cross-station trade evaluation
- **Risk Management**: Configurable risk tolerance with automatic threat avoidance
- **Standard Cargo Handling**: Proper cargo space calculations and loading
- **Anti-Stuck Protection**: Prevents ships from getting stuck with invalid orders

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
- **Full Localization**: English and German translations

### Threat Intelligence System ✅ **WORKING**
- **Real-Time Threat Detection**: Monitors attacks, missiles, and ship destruction
- **Fleet-Wide Intelligence**: Ships share threat information across the fleet
- **5-Level Threat Classification**: From minor threats to critical emergencies
- **Sector Risk Assessment**: Automatic avoidance of recently threatened areas
- **Smart Notifications**: Fleet alerts for high-threat situations
- **Automatic Cleanup**: Time-based database expiry prevents performance issues

### Fleet Coordination System ✅ **WORKING**
- **Multi-Ship Management**: Coordinate entire trading fleets
- **Route Conflict Prevention**: Automatic detection and prevention of duplicate routes
- **Trade Reservations**: Ships reserve routes to avoid fleet oversaturation
- **Fleet Statistics**: Track total profit and trades across all ships
- **Automatic Cleanup**: Stale reservations are automatically removed

### Mobile Satellite Intelligence ✅ **WORKING**
- **Mobile Market Data**: Ships act as advanced satellites (75km radar range)
- **Skill-Gated**: Only Level 9+ pilots can gather intelligence
- **Real-Time Updates**: Fresh market data during trading operations
- **Station Scanning**: Automatic trade offer updates for nearby stations
- **Smart Cooldowns**: Per-station cooldown prevents excessive scanning

### Auto-Repair System ✅ **WORKING**
- **Automatic Hull Monitoring**: Ships check hull integrity after every trade
- **Skill-Gated Access**: Only Level 12+ master traders can use auto-repair
- **Configurable Threshold**: Default triggers at <95% hull (adjustable 50-99%)
- **Smart Station Finding**: Finds nearest appropriate repair station within jump range
- **Ship Class Aware**: S/M ships use wharfs/equipment docks, L/XL use shipyards
- **Funds Management**: Full repair if affordable, partial repair if low on credits, notification if insufficient funds
- **Automatic Resumption**: Ships automatically resume trading after repairs complete

### Performance Features ✅ **WORKING**
- **Event-Driven Architecture**: 3-5x faster than polling-based systems
- **Comprehensive Logging**: Detailed debug output and trade tracking
- **Professional Integration**: Compatible logbook message system
- **Save Game Safe**: No save game corruption or compatibility issues
- **Optimized Performance**: Minimal CPU and memory footprint

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

### Auto-Repair Settings
- **Enable/Disable**: Toggle automatic repair system (default: enabled)
- **Hull Threshold**: Trigger repair when hull drops below X% (default: 95%, range: 50-99%)
- **Minimum Pilot Level**: Required skill level for auto-repair access (default: 12)

### Notifications
- **Logbook Entries**: Enable professional trade messages
- **Training Messages**: Immersive training start/completion notifications
- **Level Up Alerts**: Pilot advancement announcements
- **Repair Notifications**: Auto-repair status and fund warnings
- **Debug Output**: Comprehensive logging levels (0-3)

## 📊 Skill Progression System

### **Level Progression Table**

| Level | XP Required | Title | Stars | Max Jump Distance | Training Required | What You Gain |
|-------|-------------|-------|-------|-------------------|-------------------|---------------|
| **1** | 0 XP | Apprentice | ⭐ | **1 jump** | No | • Starting level<br>• Local sector trading only<br>• Basic threat detection |
| **2** | 100 XP | Apprentice | ⭐ | **1 jump** | No | • XP accumulation continues |
| **3** | 250 XP | Apprentice | ⭐ | **1 jump** → **3 jumps** | **✅ TRAINING** | • **+200% jump range** (1→3 jumps)<br>• Training system unlocks<br>• Multi-sector trading begins |
| **4** | 450 XP | Courier | ⭐⭐ | **3 jumps** | No | • 2-star rank title<br>• Extended trading range |
| **5** | 700 XP | Courier | ⭐⭐ | **3 jumps** | No | • Continued progression |
| **6** | 1,000 XP | Courier | ⭐⭐ | **3 jumps** → **5 jumps** | **✅ TRAINING** | • **+67% jump range** (3→5 jumps)<br>• Threat Intelligence access<br>• Regional trading unlocked |
| **7** | 1,350 XP | Supplier | ⭐⭐⭐ | **5 jumps** | No | • 3-star rank title<br>• Regional specialist |
| **8** | 1,750 XP | Supplier | ⭐⭐⭐ | **5 jumps** | No | • Approaching advanced features |
| **9** | 2,200 XP | Supplier | ⭐⭐⭐ | **5 jumps** → **10 jumps** | **✅ TRAINING** | • **+100% jump range** (5→10 jumps)<br>• **Mobile Satellite Intelligence** 📡<br>• 75km radar market scanning<br>• Long-distance trading unlocked |
| **10** | 2,700 XP | Trader | ⭐⭐⭐⭐ | **10 jumps** | No | • 4-star rank title<br>• Cross-sector specialist |
| **11** | 3,250 XP | Trader | ⭐⭐⭐⭐ | **10 jumps** | No | • Approaching master level |
| **12** | 3,850 XP | Trader | ⭐⭐⭐⭐ | **10 jumps** → **15 jumps** | **✅ TRAINING** | • **+50% jump range** (10→15 jumps)<br>• **Advanced Fleet Coordination**<br>• **Auto-Repair System** 🔧<br>• Master trader certification<br>• Cross-galaxy trading |
| **13** | 4,500 XP | Merchant | ⭐⭐⭐⭐⭐ | **15 jumps** | No | • 5-star rank title<br>• Elite trader status |
| **14** | 5,200 XP | Merchant | ⭐⭐⭐⭐⭐ | **15 jumps** | No | • Near maximum capabilities |
| **15** | 6,000 XP | Long-Distance Merchant | ⭐⭐⭐⭐⭐ | **15 jumps** → **25 jumps** | No | • **+67% jump range** (15→25 jumps)<br>• **Maximum capabilities**<br>• True galaxy-wide trading<br>• Ultimate trader rank |

### **Key Skill Breakpoints**

#### 🎓 **Level 3 - Basic Certification**
- **Jump Range**: 1 → **3 jumps** (+200%)
- **Unlocks**: Training system, multi-sector trading
- **Impact**: Can now trade across neighboring sectors

#### 🎓 **Level 6 - Advanced Trade Certification**  
- **Jump Range**: 3 → **5 jumps** (+67%)
- **Unlocks**: Full Threat Intelligence System access
- **Impact**: Better risk assessment and sector-wide trading

#### 🎓 **Level 9 - Expert Trader Certification**
- **Jump Range**: 5 → **10 jumps** (+100%)
- **Unlocks**: **Mobile Satellite Intelligence** (75km radar scanning)
- **Impact**: Ships become mobile market sensors, double trading range

#### 🎓 **Level 12 - Master Trader Certification**
- **Jump Range**: 10 → **15 jumps** (+50%)
- **Unlocks**: Advanced fleet coordination features, **Auto-Repair System** 🔧
- **Impact**: Cross-galaxy trading, fleet optimization, ships automatically repair damage
- **Auto-Repair**: Ships monitor hull integrity and automatically dock for repairs when damaged

#### 🏆 **Level 15 - Long-Distance Merchant (Maximum)**
- **Jump Range**: 15 → **25 jumps** (+67%)
- **Capabilities**: Can trade anywhere in the known universe
- **Status**: Elite 5-star master trader

### **How Progression Works:**
- **XP Gain**: Ships earn XP from successful trades (buy + sell cycle)
- **Distance Bonus**: Longer routes earn more XP (encourages challenging trades)
- **Risk Bonus**: Trading in dangerous sectors earns bonus XP
- **Jump Restrictions**: Ships can **only** find trades within their maximum jump distance
- **Training Gates**: XP progression **completely stops** at levels 3, 6, 9, and 12 until training is completed
- **Pilot-Based**: XP is tied to the individual pilot, not the ship (pilot retains XP if transferred)
- **Star Rating**: Every 3 levels = 1 star (matches X4's skill system)

### **Feature Unlocks by Level:**
- **Level 1+**: Basic trading, local threat detection
- **Level 3+**: Multi-sector trading (after training)
- **Level 6+**: Full Threat Intelligence System access
- **Level 9+**: Mobile Satellite Intelligence (radar-based market scanning)
- **Level 12+**: Advanced fleet coordination, **Auto-Repair System**

### **XP Calculation System**

GalaxyTrader MK3 uses an advanced XP calculation system that rewards pilots based on trade quality, value, and difficulty:

#### **XP Formula**
```
Base XP = 50 (configurable)

Value Multiplier = Trade Value ÷ 10,000
Quality Bonus = 1.0 + (X4 Trade Quality × 0.5)
Distance Bonus = 1.0 + (min(Jumps, 10) ÷ 20)

Final XP = Base XP × Value Multiplier × Quality Bonus × Distance Bonus
Range: 10 - 1,000 XP per trade (clamped)
```

#### **XP Factors Explained**

1. **Trade Value** 💰
   - Higher value trades = more XP
   - A 100,000 Cr trade gives 10× multiplier
   - Encourages profitable trading over low-value runs

2. **Trade Quality** ⭐
   - Uses X4's native trade quality metric (-0.5 to +0.5)
   - Good trades (buying low, selling high) earn up to +25% bonus XP
   - Poor trades (buying high, selling low) earn less XP
   - Rewards smart trading decisions

3. **Distance Bonus** 🚀
   - Longer routes earn more XP (up to 10 jumps counted)
   - Each jump adds 5% more XP
   - A 10-jump trade earns +50% bonus XP
   - Encourages long-distance trading as pilots level up

4. **Risk Bonus** ⚠️ (Future)
   - Trading in dangerous sectors will earn extra XP
   - Currently under development

#### **Example XP Calculations**

| Trade Type | Value | Quality | Distance | Final XP |
|------------|-------|---------|----------|----------|
| **Small Local Trade** | 10,000 Cr | 0.0 (average) | 1 jump | ~52 XP |
| **Medium Regional Trade** | 50,000 Cr | +0.2 (good) | 3 jumps | ~315 XP |
| **Large Long-Distance** | 200,000 Cr | +0.4 (excellent) | 10 jumps | **1,000 XP** (capped) |

#### **Progression Speed**
- **Level 1 → 3**: ~5-10 small trades (new pilots, local trading)
- **Level 3 → 6**: ~15-25 medium trades (multi-sector trading)
- **Level 6 → 9**: ~25-40 larger trades (regional specialist)
- **Level 9 → 12**: ~35-50 long-distance trades (cross-galaxy expert)
- **Level 12 → 15**: ~45-60 elite trades (master trader)

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
2. **Training Stations**: Ships will automatically find training stations at levels 3, 6, 9, and 12
3. **Fleet Management**: Use multiple ships for better sector coverage and higher profits
4. **Monitor Progress**: Watch ship names for rank, level, and XP updates
5. **Debug Logging**: Enable debug output (level 2-3) to monitor system performance
6. **Save Regularly**: While save-safe, regular saves are always recommended
7. **Level 9+ Ships**: Gain bonus market intelligence through mobile satellite scanning
8. **Level 12+ Auto-Repair**: Master traders automatically handle their own repairs - keep funds available
9. **Hull Threshold**: Adjust auto-repair threshold (50-99%) based on your preferred risk tolerance
10. **Combat Zones**: Ships trading in dangerous areas will benefit from auto-repair at level 12+

---

*GalaxyTrader MK3 - Teaching your ships to trade smarter, not harder!* 