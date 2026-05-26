import logging
import os
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# --- Ningaḷuḍe Original Token Number Iviḍe Add Cheythittunḍ ---
BOT_TOKEN = "8829939412:AAFCSWd3CXPk8LJ0cm_IJujH7_WRAJ5dzG4"
ADMIN_ID = 1913358609
AUTHORIZED_USERS: set[int] = {1913358609}

# Simple dictionary to store user language preference temporarily in memory
# Format: {user_id: 'en'} or {user_id: 'ml'}
USER_LANGUAGES = {}

GRAPHIC_KEYWORDS = re.compile(
    r"\b(no[\s\-]?graphic|graphic[\s\-]?issue|display[\s\-]?issue|screen[\s\-]?issue"
    r"|no[\s\-]?display|display[\s\-]?problem|screen[\s\-]?problem|lcd[\s\-]?issue)\b",
    re.IGNORECASE,
)

BACKLIGHT_KEYWORDS = re.compile(
    r"\b(black[\s\-]?display|light[\s\-]?issue|no[\s\-]?backlight|backlight[\s\-]?issue"
    r"|backlight[\s\-]?problem|no[\s\-]?light|screen[\s\-]?dark|dark[\s\-]?screen)\b",
    re.IGNORECASE,
)

BLANK_DISPLAY_KEYWORDS = re.compile(
    r"\b(blank[\s\-]?display|blank[\s\-]?screen|white[\s\-]?screen|white[\s\-]?display"
    r"|dead[\s\-]?screen|dead[\s\-]?display|no[\s\-]?picture|completely[\s\-]?blank)\b",
    re.IGNORECASE,
)

CHARGING_KEYWORDS = re.compile(
    r"\b(no[\s\-]?charging|not[\s\-]?charging|charging[\s\-]?issue|charging[\s\-]?problem"
    r"|won[\s\']?t[\s\-]?charge|cannot[\s\-]?charge|charge[\s\-]?fault|fake[\s\-]?charging"
    r"|slow[\s\-]?charging|usb[\s\-]?issue|charger[\s\-]?issue)\b",
    re.IGNORECASE,
)

NO_SERVICE_KEYWORDS = re.compile(
    r"\b(no[\s\-]?service|no[\s\-]?network|no[\s\-]?signal|network[\s\-]?issue"
    r"|signal[\s\-]?problem|searching[\s\-]?network|baseband[\s\-]?(missing|unknown)"
    r"|sim[\s\-]?not[\s\-]?working|no[\s\-]?sim|imei[\s\-]?(missing|issue))\b",
    re.IGNORECASE,
)

DEAD_PHONE_KEYWORDS = re.compile(
    r"\b(dead[\s\-]?phone|dead[\s\-]?complaint|not[\s\-]?turning[\s\-]?on"
    r"|won[\s\']?t[\s\-]?turn[\s\-]?on|phone[\s\-]?dead|device[\s\-]?dead"
    r"|no[\s\-]?power[\s\-]?on|completely[\s\-]?dead|phone[\s\-]?not[\s\-]?starting)\b",
    re.IGNORECASE,
)

TOUCH_KEYWORDS = re.compile(
    r"\b(touch[\s\-]?not[\s\-]?working|touch[\s\-]?issue|touch[\s\-]?problem"
    r"|touchscreen[\s\-]?issue|touch[\s\-]?screen[\s\-]?not[\s\-]?working"
    r"|unresponsive[\s\-]?touch|touch[\s\-]?dead|screen[\s\-]?touch[\s\-]?not[\s\-]?working"
    r"|touch[\s\-]?not[\s\-]?responding|digitizer[\s\-]?issue)\b",
    re.IGNORECASE,
)

MIC_KEYWORDS = re.compile(
    r"\b(mic[\s\-]?not[\s\-]?working|microphone[\s\-]?not[\s\-]?working|mic[\s\-]?issue"
    r"|microphone[\s\-]?issue|no[\s\-]?audio[\s\-]?during[\s\-]?calls|mic[\s\-]?dead"
    r"|microphone[\s\-]?dead|call[\s\-]?audio[\s\-]?issue|can[\s\']?t[\s\-]?hear[\s\-]?me"
    r"|voice[\s\-]?not[\s\-]?clear|mic[\s\-]?problem|microphone[\s\-]?problem)\b",
    re.IGNORECASE,
)

AUTOMATIC_BOOTLOOP_KEYWORDS = re.compile(
    r"\b(auto[\s\-]?restart|auto[\s\-]?reboot|stuck[\s\-]?on[\s\-]?logo|bootloop|logo[\s\-]?blink|restarts[\s\-]?continuously)\b",
    re.IGNORECASE,
)

SPEAKER_KEYWORDS = re.compile(
    r"\b(speaker[\s\-]?not[\s\-]?working|no[\s\-]?sound|loudspeaker[\s\-]?not[\s\-]?working"
    r"|earpiece[\s\-]?not[\s\-]?working|speaker[\s\-]?issue|speaker[\s\-]?problem"
    r"|speaker[\s\-]?dead|sound[\s\-]?not[\s\-]?working|no[\s\-]?audio"
    r"|loudspeaker[\s\-]?issue|earpiece[\s\-]?issue|sound[\s\-]?issue)\b",
    re.IGNORECASE,
)

FLOWS = {
    "g": {
        "title": "Graphic / Display Issue Detected",
        "steps": {
            1: {
                "text": (
                    "Step 1: Check with a known good display folder first.\n\n"
                    "Take Diode Mode (GR) readings on the LCD Connector MIPI Data and Clock lines "
                    "(MIPI_CLK_P/N, MIPI_DATA_P/N).\n\n"
                    "Are all MIPI lines showing balanced and normal GR values (approx 300–400 mV) "
                    "with no OL or short?"
                ),
                "yes": 2,
                "no": "g_s1_no",
            },
            2: {
                "text": (
                    "Step 2: Check the basic Display LDO digital voltages.\n\n"
                    "Power ON the phone and measure on the capacitors near the connector:\n"
                    "  • VREG_LCO_1P8 (1.8V)\n"
                    "  • VREG_LDO_2P8/3P0 (2.8V / 3.0V)\n\n"
                    "Are these basic logic supplies present?"
                ),
                "yes": 3,
                "no": "g_s2_no",
            },
            3: {
                "text": (
                    "Step 3: [Display OFF / Sleep Mode Test]\n\n"
                    "Keep the display connected, but let the phone go to sleep mode (Screen OFF). "
                    "Measure the Analog Graphic supply lines VSP (+5V) and VSN (-5V) near the Graphic IC.\n\n"
                    "Does it show 0V during Display OFF time?"
                ),
                "yes": 4,
                "no": "g_s3_no",
            },
            4: {
                "text": (
                    "Step 4: [Display ON / Active Mode Test]\n\n"
                    "Wake up the screen (press power button or insert charger) and immediately measure "
                    "VSP and VSN lines.\n\n"
                    "Do they boost up to exactly VSP (+5V) and VSN (-5V) during Display ON time?"
                ),
                "yes": 5,
                "no": "g_s4_no",
            },
            5: {
                "text": (
                    "Step 5: Check the CPU Control Signals.\n\n"
                    "Measure the LCD_RESET line (1.8V pulse) and LCD_TE (Tearing Effect) signal at "
                    "the connector when the display triggers.\n\n"
                    "Is the LCD_RESET signal present?"
                ),
                "yes": 6,
                "no": "g_s5_no",
            },
            6: {
                "text": (
                    "Step 6: Check the I2C Communication Lines.\n\n"
                    "Test the Graphic IC I2C lines (SDA and SCL) for proper GR values and 1.8V "
                    "pull-up voltages.\n\n"
                    "Are the Graphic IC communication lines normal?"
                ),
                "yes": 7,
                "no": "g_s6_no",
            },
            7: {
                "text": (
                    "Step 7: Since all external lines, MIPI data, digital/analog voltages (1.8V, +5V, -5V), "
                    "and CPU signals are completely perfect, the fault is inside the Graphic IC internal logic.\n\n"
                    "Do you want to try Reballing the existing Graphic IC / PMI?"
                ),
                "yes": "g_s7_yes",
                "no": 8,
            },
            8: {
                "text": (
                    "Step 8: [Final Solution]\n\n"
                    "If reballing did not fix the graphic fault, or if the IC is shorted/burnt internally, "
                    "the final step is to Replace the IC.\n\n"
                    "Swap the Graphic IC / PMI with a brand new working matching part number IC.\n\n"
                    "Issue Solved!"
                ),
                "yes": None,
                "no": None,
            },
        },
        "outcomes": {
            "g_s1_no": (
                "Diagnostic:\n\n"
                "MIPI lines go directly to the CPU.\n\n"
                "If any line is OL: Check for open Dual-ESD filter coils near the connector or dry "
                "solder under the CPU.\n\n"
                "If Short: Check the filter or CPU internal line damage."
            ),
            "g_s2_no": (
                "Diagnostic:\n\n"
                "Main PMIC is not producing the digital logic supply for the display circuit.\n\n"
                "Check for a short on these LDO lines or inspect the main PMIC output."
            ),
            "g_s3_no": (
                "Diagnostic:\n\n"
                "During Display OFF time, VSP and VSN must drop to 0V.\n\n"
                "If +5V or -5V is continuously present even in sleep mode, the Graphic IC is leaky or "
                "damaged, causing battery drain and graphic hang issues."
            ),
            "g_s4_no": (
                "Diagnostic:\n\n"
                "Graphic IC output is failing.\n\n"
                "Check the input voltage to the Graphic IC (VPH_PWR 4.2V). If input is present but "
                "+5V/-5V is missing, the Graphic IC, its boost coils, or output capacitors are faulty.\n\n"
                "Replace the coils first."
            ),
            "g_s5_no": (
                "Diagnostic:\n\n"
                "If LCD_RESET is 0V, the CPU is not sending the reset command to activate the display panel.\n\n"
                "This happens if the CPU fails to detect the display or due to dry solder under the CPU.\n\n"
                "Reball the CPU."
            ),
            "g_s6_no": (
                "Diagnostic:\n\n"
                "If I2C SDA/SCL lines are open or short, the CPU cannot communicate with the Graphic IC "
                "to control voltages.\n\n"
                "Trace the pull-up resistors or lines going to the CPU/PMIC."
            ),
            "g_s7_yes": (
                "Action: Reball the Graphic IC / PMI\n\n"
                "Desolder the Graphic IC / PMI carefully, clean the motherboard pads, reball the IC "
                "using high-quality solder paste, and solder it back.\n\n"
                "Check if graphics are restored."
            ),
        },
    },
    "bl": {
        "title": "Backlight / Black Display Issue Detected",
        "steps": {
            1: {
                "text": (
                    "Step 1: Check with a known good display folder. Verify under a bright torch light if "
                    "graphics are visible in the background.\n\n"
                    "Take Diode Mode (GR) readings on the LCD Connector Backlight Pins: "
                    "LED_ANODE, LED_K1, and LED_K2.\n\n"
                    "Are all GR values normal?"
                ),
                "yes": 2,
                "no": "bl_s1_no",
            },
            2: {
                "text": (
                    "Step 2: Check the Light IC input voltage.\n\n"
                    "Measure VPH_PWR / VBAT on the input side of the Boost Coil.\n\n"
                    "Does it show a steady battery voltage of approx 3.7V – 4.2V?"
                ),
                "yes": 3,
                "no": "bl_s2_no",
            },
            3: {
                "text": (
                    "Step 3: [Display OFF / Sleep Mode Test]\n\n"
                    "Keep the display connected, but let the phone go to sleep mode (Screen OFF). "
                    "Measure the voltage on the LED_ANODE pin.\n\n"
                    "Does it show normal battery voltage (approx 3.7V – 4.2V) during Display OFF time?"
                ),
                "yes": 4,
                "no": "bl_s3_no",
            },
            4: {
                "text": (
                    "Step 4: [Display ON / Active Mode Test]\n\n"
                    "Wake up the screen (press power button or insert charger) and immediately measure "
                    "the LED_ANODE voltage.\n\n"
                    "Does the voltage boost up to 15V – 40V during Display ON time?"
                ),
                "yes": 5,
                "no": "bl_s4_no",
            },
            5: {
                "text": (
                    "Step 5: Check the Hardware Enable signal.\n\n"
                    "Measure LCM_BACKLIGHT_EN (1.8V pulse) coming from the CPU/PMIC to the Light IC "
                    "when the screen turns ON.\n\n"
                    "Is the EN signal present?"
                ),
                "yes": 6,
                "no": "bl_s5_no",
            },
            6: {
                "text": (
                    "Step 6: Check the Brightness Control signals.\n\n"
                    "Check the PWM (Pulse Width Modulation) or CABC (Content Adaptive Backlight Control) "
                    "line from the CPU/Display IC to the Light IC.\n\n"
                    "Are PWM/CABC signals and feedback lines working properly?"
                ),
                "yes": 7,
                "no": "bl_s6_no",
            },
            7: {
                "text": (
                    "Step 7: Since all external components, input/boost voltages, and CPU signals "
                    "(EN/PWM) are perfect, the issue is inside the Light IC logic.\n\n"
                    "Do you want to try Reballing the existing Light IC / PMI?"
                ),
                "yes": "bl_s7_yes",
                "no": 8,
            },
            8: {
                "text": (
                    "Step 8: [Final Solution]\n\n"
                    "If reballing did not fix the problem, or if the Light IC is physically "
                    "damaged/burnt internally, the final step is to Replace the IC.\n\n"
                    "Replace the Backlight IC / PMI with a brand new working matching part number IC.\n\n"
                    "Issue Solved!"
                ),
                "yes": None,
                "no": None,
            },
        },
        "outcomes": {
            "bl_s1_no": (
                "Diagnostic:\n\n"
                "If LED_ANODE is OL: Check the series Zero-ohm resistor or Backlight Diode.\n\n"
                "If any LED_K line is OL: Check the series resistors near the Light IC.\n\n"
                "If ANODE is 000 (Short): Check the parallel high-voltage protection capacitors."
            ),
            "bl_s2_no": (
                "Diagnostic:\n\n"
                "Main power rail (VPH_PWR) is missing or broken before reaching the backlight circuit.\n\n"
                "Trace the connection from the main Power IC / DC-to-DC IC to the backlight section."
            ),
            "bl_s3_no": (
                "Diagnostic:\n\n"
                "During Display OFF time, the Anode line must get raw battery voltage through the boost "
                "coil and diode.\n\n"
                "If it is 0V: Either the boost coil is open, the diode is open, or the track from the "
                "PMIC/VBAT is broken."
            ),
            "bl_s4_no": (
                "Diagnostic:\n\n"
                "Boosting is failing. When display is ON, the IC must switch and pump voltage to 15V–40V.\n\n"
                "Since input is OK but boost is missing, replace the Boost Coil (10uH) and the Backlight "
                "Fast-Recovery Diode first."
            ),
            "bl_s5_no": (
                "Diagnostic:\n\n"
                "The CPU is not sending the EN command.\n\n"
                "This happens if the CPU does not detect the display panel (check LCD_RESET or MIPI lines) "
                "or if there is a dry solder under the CPU.\n\n"
                "Reball the CPU."
            ),
            "bl_s6_no": (
                "Diagnostic:\n\n"
                "If PWM/CABC signal is missing, the backlight will remain completely dim or completely OFF "
                "even if boost voltage is present.\n\n"
                "Trace the resistor on the PWM/CABC line from CPU."
            ),
            "bl_s7_yes": (
                "Action: Reball the Light IC / PMI\n\n"
                "Carefully desolder the Light IC / PMI, clean the motherboard pads, reball the IC with "
                "high-quality solder paste, and solder it back.\n\n"
                "Check if the backlight issue is fixed."
            ),
        },
    },
    "bd": {
        "title": "Blank Display Issue Detected",
        "steps": {
            1: {
                "text": (
                    "Step 1: Check with a known good display folder first.\n\n"
                    "Take Diode Mode (GR) readings on the LCD Connector MIPI Data/Clock lines "
                    "(MIPI_CLK_P/N, MIPI_DATA_P/N).\n\n"
                    "Are all MIPI lines showing balanced and normal GR values (approx 300–400 mV) "
                    "with no OL or short?"
                ),
                "yes": 2,
                "no": "bd_s1_no",
            },
            2: {
                "text": (
                    "Step 2: Take Diode Mode (GR) reading on the LCD_ID / Display ID pin of the connector.\n\n"
                    "Check if it has a normal GR value (usually 400–600 mV depending on the board) "
                    "and check its pull-up resistor.\n\n"
                    "Is the ID line GR value normal?"
                ),
                "yes": 3,
                "no": "bd_s2_no",
            },
            3: {
                "text": (
                    "Step 3: Check the basic Display LDO digital voltages.\n\n"
                    "Power ON the phone and measure on the capacitors near the connector:\n"
                    "  • VREG_LCO_1P8 (1.8V)\n"
                    "  • VREG_LDO_2P8/3P0 (2.8V / 3.0V)\n\n"
                    "Are these basic logic supplies present?"
                ),
                "yes": 4,
                "no": "bd_s3_no",
            },
            4: {
                "text": (
                    "Step 4: [Display OFF / Sleep Mode Test]\n\n"
                    "Keep the display connected, let the phone go to sleep mode (Screen OFF).\n\n"
                    "Measure the Analog Graphic supplies VSP (+5V) and VSN (-5V), "
                    "and Backlight LED_ANODE.\n\n"
                    "Do VSP/VSN show 0V and LED_ANODE show normal battery voltage (3.7V–4.2V)?"
                ),
                "yes": 5,
                "no": "bd_s4_no",
            },
            5: {
                "text": (
                    "Step 5: [Display ON / Active Mode Test — Graphics Side]\n\n"
                    "Wake up the screen (Trigger Display ON) and immediately measure VSP and VSN lines.\n\n"
                    "Do they boost up to exactly VSP (+5V) and VSN (-5V) during Display ON time?"
                ),
                "yes": 6,
                "no": "bd_s5_no",
            },
            6: {
                "text": (
                    "Step 6: [Display ON / Active Mode Test — Backlight Side]\n\n"
                    "With the screen still active, measure the LED_ANODE pin.\n\n"
                    "Does the voltage boost up properly to 15V – 40V during Display ON time?"
                ),
                "yes": 7,
                "no": "bd_s6_no",
            },
            7: {
                "text": (
                    "Step 7: Check CPU Control Signals.\n\n"
                    "Measure the LCM_BACKLIGHT_EN (1.8V pulse) and LCD_RESET (1.8V pulse) at the "
                    "connector when the screen triggers.\n\n"
                    "Are both the EN and RESET signals present from the CPU?"
                ),
                "yes": 8,
                "no": "bd_s7_no",
            },
            8: {
                "text": (
                    "Step 8: Check the Brightness Control Signals.\n\n"
                    "Check the PWM (Pulse Width Modulation) or CABC line from the CPU to the Light IC, "
                    "and the Graphic IC I2C lines (SDA and SCL).\n\n"
                    "Are these communication lines and signals working properly?"
                ),
                "yes": 9,
                "no": "bd_s8_no",
            },
            9: {
                "text": (
                    "Step 9: Since all external components, MIPI tracks, ID lines, LDOs, boost outputs, "
                    "and CPU commands are perfect, the issue is inside the Graphic or Light IC internal "
                    "silicon logic.\n\n"
                    "Do you want to try Reballing the Graphic IC / Backlight PMIC?"
                ),
                "yes": "bd_s9_yes",
                "no": 10,
            },
            10: {
                "text": (
                    "Step 10: [Final Solution]\n\n"
                    "If reballing did not fix the blank display fault, or if the ICs are internally "
                    "shorted/burnt, the final step is to Replace the components.\n\n"
                    "Swap the faulty Graphic IC, Light IC, or if needed, reball/replace the CPU itself "
                    "as a last resort.\n\n"
                    "Issue Solved!"
                ),
                "yes": None,
                "no": None,
            },
        },
        "outcomes": {
            "bd_s1_no": (
                "Diagnostic:\n\n"
                "MIPI lines go directly to the CPU.\n\n"
                "If any line is OL: Check for open Dual-ESD filter coils near the connector or dry "
                "solder under the CPU.\n\n"
                "If Short: CPU internal line is damaged."
            ),
            "bd_s2_no": (
                "Diagnostic:\n\n"
                "If LCD_ID line is OL/Short, the CPU cannot detect that a display panel is attached, "
                "so it will NOT trigger any Graphic voltages (VSP/VSN) or Backlight voltages.\n\n"
                "Trace the ID line track or pull-up resistor."
            ),
            "bd_s3_no": (
                "Diagnostic:\n\n"
                "Main PMIC is not producing the digital logic supply for the display circuit.\n\n"
                "Check for a short on these LDO lines or inspect the main PMIC output."
            ),
            "bd_s4_no": (
                "Diagnostic:\n\n"
                "During sleep mode, VSP/VSN must be 0V.\n\n"
                "If +5V/-5V are present during sleep: Graphic IC is leaking.\n\n"
                "If LED_ANODE is 0V during sleep: The backlight boost coil or protection "
                "diode/resistor is open."
            ),
            "bd_s5_no": (
                "Diagnostic:\n\n"
                "Graphic IC output is failing.\n\n"
                "Check the input voltage to the Graphic IC (VPH_PWR 4.2V). If input is present but "
                "+5V/-5V is missing, the Graphic IC, its boost coils, or output capacitors are faulty.\n\n"
                "Replace the coils first."
            ),
            "bd_s6_no": (
                "Diagnostic:\n\n"
                "Backlight switching/boosting is failing.\n\n"
                "Since input is OK but boost is missing, replace the Backlight Boost Coil (10uH) and "
                "the Fast-Recovery Diode. If the issue persists, the Light IC is faulty."
            ),
            "bd_s7_no": (
                "Diagnostic:\n\n"
                "CPU is not sending enable/reset commands.\n\n"
                "This happens if the CPU fails to detect the display panel due to dry solder under the "
                "CPU or broken tracks.\n\n"
                "Reball the CPU."
            ),
            "bd_s8_no": (
                "Diagnostic:\n\n"
                "If PWM/CABC or I2C communication lines are open or short, the CPU cannot talk to the "
                "Graphic/Light ICs to control brightness or voltage parameters.\n\n"
                "Trace the series resistors or pull-ups on these lines."
            ),
            "bd_s9_yes": (
                "Action: Reball the Graphic IC / Backlight PMIC\n\n"
                "Desolder the respective Graphic IC or Backlight PMIC carefully, clean the motherboard "
                "pads, reball the IC with high-quality solder paste, and solder it back.\n\n"
                "Check if display functions are restored."
            ),
        },
    },
    "nc": {
        "title": "No Charging / Charging Issue Detected",
        "steps": {
            1: {
                "text": (
                    "Step 1: Change and check with a known good original charger and a high-quality "
                    "USB cable first.\n\n"
                    "Does the phone start charging normally?"
                ),
                "yes": "nc_s1_yes",
                "no": 2,
            },
            2: {
                "text": (
                    "Step 2: Connect the charger. Measure the main USB input voltage VBUS (5V) at:\n"
                    "  • The sub-board / charging port\n"
                    "  • Charging CC flex cable\n"
                    "  • Main board input test point\n\n"
                    "Is the 5V VBUS voltage reaching the motherboard connector?"
                ),
                "yes": 3,
                "no": "nc_s2_no",
            },
            3: {
                "text": (
                    "Step 3: Track VBUS through the OVP (Over Voltage Protection) IC.\n\n"
                    "Measure the voltage before and after the OVP IC.\n\n"
                    "Is 5V present on the output side of the OVP IC?"
                ),
                "yes": 4,
                "no": "nc_s3_no",
            },
            4: {
                "text": (
                    "Step 4: Check the PMID / MID Capacitor voltage.\n\n"
                    "Locate the PMID capacitor (MID Cap) right next to the Charging IC and measure it.\n\n"
                    "Does it show stable 5V input filtering?"
                ),
                "yes": 5,
                "no": "nc_s4_no",
            },
            5: {
                "text": (
                    "Step 5: Check Charging IC core output.\n\n"
                    "Measure the system power line VPH_PWR (approx 3.7V – 4.2V) on the big Buck Coil "
                    "next to the Charging IC.\n\n"
                    "Is VPH_PWR present and normal?"
                ),
                "yes": 6,
                "no": "nc_s5_no",
            },
            6: {
                "text": (
                    "Step 6: Check the Boot Capacitor (BST / Boot Cap).\n\n"
                    "Measure both sides of the Boot Cap connected to the Charging IC switching node.\n\n"
                    "Do you see switching boost action (approx 8V – 9V on one side when charger is connected)?"
                ),
                "yes": 7,
                "no": "nc_s6_no",
            },
            7: {
                "text": (
                    "Step 7: Measure Charging Output to Battery (VBAT).\n\n"
                    "With the battery disconnected and charger plugged in, measure the voltage on the "
                    "positive terminal of the battery connector.\n\n"
                    "Does it give stable charging voltage (approx 3.7V – 4.2V)?"
                ),
                "yes": 8,
                "no": "nc_s7_no",
            },
            8: {
                "text": (
                    "Step 8: Check the Battery Thermistor / ID Lines (BTST / BAT_THERM).\n\n"
                    "Take Diode Mode (GR) readings and voltage on the Battery Thermal (BTST) and "
                    "Battery ID pins on the connector.\n\n"
                    "Are the values normal (no OL/Short, approx 1.8V present)?"
                ),
                "yes": 9,
                "no": "nc_s8_no",
            },
            9: {
                "text": (
                    "Step 9: Check CPU Thermal Signals (O-T / Over Temperature).\n\n"
                    "Verify if the PMIC/CPU O-T thermal warning line is triggered, or if the system "
                    "I2C/SMBus communication lines (SDA/SCL) between CPU and Charging IC are working "
                    "properly.\n\n"
                    "Are they normal?"
                ),
                "yes": 10,
                "no": "nc_s9_no",
            },
            10: {
                "text": (
                    "Step 10: Since all external components, VBUS, PMID cap, Boot cap, VBAT, and BTST "
                    "signals are completely perfect, the issue is inside the Charging IC silicon logic.\n\n"
                    "Do you want to try Reballing the Charging IC (PMI / Main PMIC / SMB IC)?"
                ),
                "yes": "nc_s10_yes",
                "no": 11,
            },
            11: {
                "text": (
                    "Step 11: [Final Solution]\n\n"
                    "If reballing did not fix the charging fault, or if the phone still draws 0.0A / 0.6A "
                    "(Fake charging), the final step is to Replace the IC.\n\n"
                    "Swap the Charging IC / PMI with a brand new working matching part number IC.\n\n"
                    "Issue Solved!"
                ),
                "yes": None,
                "no": None,
            },
        },
        "outcomes": {
            "nc_s1_yes": (
                "Result: Problem Solved!\n\n"
                "The fault was with the external charger or the damaged USB cable."
            ),
            "nc_s2_no": (
                "Diagnostic:\n\n"
                "VBUS 5V is missing. Fault is with the charging port (Type-C/Micro), sub-board PCB, "
                "or the main sub-board-to-motherboard connection flex cable.\n\n"
                "Replace the charging port or flex."
            ),
            "nc_s3_no": (
                "Diagnostic:\n\n"
                "OVP IC is faulty or damaged, blocking the 5V input from reaching the Charging IC.\n\n"
                "Bypass the OVP IC (jumper input to output cap) or replace the OVP IC."
            ),
            "nc_s4_no": (
                "Diagnostic:\n\n"
                "PMID line is shorted or the MID Cap is leaked/grounded.\n\n"
                "If PMID is short to ground, the Charging IC will lock down and won't charge.\n\n"
                "Remove the shorted parallel capacitor on PMID line."
            ),
            "nc_s5_no": (
                "Diagnostic:\n\n"
                "Charging IC is not switching to generate system power (VPH_PWR).\n\n"
                "Check for a direct short on VPH_PWR line (capacitors/modules) or replace the "
                "Charging IC / PMIC."
            ),
            "nc_s6_no": (
                "Diagnostic:\n\n"
                "If the Boot Cap is open, leaky, or value-shifted, the internal high-side driver inside "
                "the Charging IC cannot turn ON.\n\n"
                "This causes fake charging or no charging.\n\n"
                "Replace the Boot Cap (typically 100nF)."
            ),
            "nc_s7_no": (
                "Diagnostic:\n\n"
                "Charging IC is getting input but not pumping out charging voltage to the battery.\n\n"
                "Check the VBAT sense lines, parallel protection diodes near the connector, or replace "
                "the Charging IC."
            ),
            "nc_s8_no": (
                "Diagnostic:\n\n"
                "If the BTST (Thermistor) line is open or short, the phone will show 'Charging Paused', "
                "'Battery Temperature Too High/Low', or logo blinking.\n\n"
                "Check the 10k/100k pull-up resistor on the BTST line."
            ),
            "nc_s9_no": (
                "Diagnostic:\n\n"
                "If I2C communication fails or O-T line drops, the CPU won't permit the IC to ramp up "
                "charging current.\n\n"
                "Check I2C pull-up resistors or reflow the CPU/PMIC."
            ),
            "nc_s10_yes": (
                "Action: Reball the Charging IC / PMI\n\n"
                "Desolder the Charging IC carefully, clean the motherboard pads, reball the IC with "
                "high-quality solder paste, and solder it back.\n\n"
                "Connect a USB tester to check charging current."
            ),
        },
    },
    "ns": {
        "title": "No Service / Network Issue Detected",
        "steps": {
            1: {
                "text": (
                    "Step 1: Dial *#06# to check IMEI. Go to Settings -> About Phone -> Baseband Version.\n\n"
                    "Are both the IMEI numbers valid and is the Baseband Version showing correctly "
                    "(Not Unknown)?"
                ),
                "yes": 2,
                "no": 12,
            },
            2: {
                "text": (
                    "Step 2: Check the IMEI status online or with the operator to see if the device is "
                    "Blacklisted or blocked by the government/operator due to theft or unpaid bills.\n\n"
                    "Is the device clean and NOT blacklisted?"
                ),
                "yes": 3,
                "no": "ns_s2_no",
            },
            3: {
                "text": (
                    "Step 3: [Pre-Disassembly Test 1] Before opening the phone, go to Settings -> "
                    "Mobile Networks -> Preferred Network Type. Switch the network mode manually between "
                    "2G Only and 4G/LTE Only.\n\n"
                    "Does the phone successfully catch network signals on 2G mode but fails completely "
                    "on 4G mode?"
                ),
                "yes": "ns_s3_yes",
                "no": 4,
            },
            4: {
                "text": (
                    "Step 4: [Pre-Disassembly Test 2] In the Preferred Network Type settings, if you "
                    "select 4G Only or 3G but the network is dead, and switching to 2G Only also shows "
                    "No Service, it means 2G is completely dead.\n\n"
                    "Is 2G network totally missing even after forcing 2G mode?"
                ),
                "yes": "ns_s4_yes",
                "no": 5,
            },
            5: {
                "text": (
                    "Step 5: Insert a working SIM card. Check Manual Network Search in settings.\n\n"
                    "Does the phone search for a while and show a list of available network operators "
                    "(Airtel, Jio, VI etc.)?"
                ),
                "yes": 6,
                "no": "ns_s5_no",
            },
            6: {
                "text": (
                    "Step 6: Measure the basic Digital Logic Supply (1.8V) on the capacitors next to "
                    "the Transceiver IC (WTR/SDR).\n\n"
                    "Is this 1.8V line present?"
                ),
                "yes": 7,
                "no": "ns_s6_no",
            },
            7: {
                "text": (
                    "Step 7: Check Transceiver Core Low Voltages (0.9V or 1.0V LDO).\n\n"
                    "Measure the core analogue/digital supply on capacitors around the Transceiver IC.\n\n"
                    "Is this approx 0.9V - 1.0V line present?"
                ),
                "yes": 8,
                "no": "ns_s7_no",
            },
            8: {
                "text": (
                    "Step 8: [Screen OFF / Sleep Mode Test - APT Supply]\n\n"
                    "Keep the SIM inserted, but let the phone screen go to sleep (Display OFF). "
                    "Measure the APT (Average Power Tracking) Buck DC-to-DC voltage on the coil next "
                    "to the 4G/5G Power Amplifier (PA).\n\n"
                    "Does it show a low standby voltage of approx 0.5V to 1.5V "
                    "(or drops to 0V when fully idle)?"
                ),
                "yes": 9,
                "no": "ns_s8_no",
            },
            9: {
                "text": (
                    "Step 9: [Screen ON / Active Mode Test - APT Boost]\n\n"
                    "Turn the screen ON, go to manual network search or make an emergency call, and "
                    "immediately measure the APT Coil voltage.\n\n"
                    "Does it instantly boost up to its maximum capacity of approx 3.4V to 4.2V to "
                    "feed the 4G PA during active search/calling?"
                ),
                "yes": 10,
                "no": "ns_s9_no",
            },
            10: {
                "text": (
                    "Step 10: Check CPU-to-Network Communication Lines (RFFE Protocol).\n\n"
                    "Measure Diode Mode (GR) readings on the RFFE_SDA (Serial Data) and RFFE_SCL "
                    "(Serial Clock) control lines on the test points connecting CPU to PA and "
                    "Transceiver ICs.\n\n"
                    "Are the GR values balanced and normal (approx 350-500 mV, no OL/Short)?"
                ),
                "yes": 11,
                "no": "ns_s10_no",
            },
            11: {
                "text": (
                    "Step 11: Check physical Antenna Signal Paths.\n\n"
                    "Take Diode Mode readings from the antenna pad up to the Antenna Switch Module / "
                    "Frequency Filters. Check the RF coaxial cable and sub-board connection.\n\n"
                    "Are all physical components, antenna tips, and antenna switches making proper "
                    "contact with 0 ohms resistance?"
                ),
                "yes": 12,
                "no": "ns_s11_no",
            },
            12: {
                "text": (
                    "Step 12: [Final Solution & Master Note]\n\n"
                    "If reballing did not fix the No Service issue, replace the Transceiver IC "
                    "(WTR/SDR) or the 4G/2G PA with a brand new working part.\n\n"
                    "📝 NOTE FOR BASEBAND MISSING / UNKNOWN:\n\n"
                    "If the Baseband Version is completely MISSING or UNKNOWN in settings, check which "
                    "Transceiver IC is on the motherboard:\n\n"
                    "1️⃣ For WTR IC Phones: Baseband Missing points to a CPU Issue (needs reballing) "
                    "or a Software Issue (corrupted EFS/NVRAM partition).\n\n"
                    "2️⃣ For SDR IC Phones: Baseband Missing points directly to an SDR IC Issue. If the "
                    "SDR IC is internally shorted or dead, it blocks the entire network layer and causes "
                    "Baseband Unknown. Always replace the SDR IC first before working on the CPU!"
                ),
                "yes": None,
                "no": None,
            },
        },
        "outcomes": {
            "ns_s2_no": (
                "Diagnostic:\n\n"
                "The device is Blacklisted or Blocked by the network provider.\n\n"
                "Hardware repair cannot fix this. The customer must resolve the issue with the "
                "operator legally."
            ),
            "ns_s3_yes": (
                "Diagnostic:\n\n"
                "Since 2G network is working but 4G network is completely missing, the 4G Power "
                "Amplifier (4G PA IC) is faulty, or its specific supply/control lines are broken.\n\n"
                "Focus directly on the 4G PA section after opening."
            ),
            "ns_s4_yes": (
                "Diagnostic:\n\n"
                "If 2G network is completely missing, the 2G PA IC is faulty, or there is a critical "
                "missing 2G working voltage (usually VPH_PWR/VBAT line directly to 2G PA) or an RF IC "
                "(Transceiver) working voltage fault.\n\n"
                "Proceed to open the phone to check hardware lines."
            ),
            "ns_s5_no": (
                "Diagnostic:\n\n"
                "If manual search fails instantly or shows error without listing operators, the "
                "Transceiver IC (WTR/SDR) or its main clock/supply lines are faulty.\n\n"
                "Focus on the Transceiver section."
            ),
            "ns_s6_no": (
                "Diagnostic:\n\n"
                "1.8V digital logic supply from main PMIC is missing.\n\n"
                "Check for a short circuit on this line or inspect main PMIC outputs.\n\n"
                "Network section cannot boot without 1.8V."
            ),
            "ns_s7_no": (
                "Diagnostic:\n\n"
                "Core supply (0.9V / 1.0V) from PMIC is missing.\n\n"
                "Check for shorted parallel smd caps near Transceiver or trace line to PMIC source."
            ),
            "ns_s8_no": (
                "Diagnostic:\n\n"
                "During Screen OFF / Standby time, APT voltage must drop down significantly to save "
                "battery.\n\n"
                "If it is stuck at high VPH_PWR (3.7V - 4.2V) during sleep, the APT IC or 4G PA is "
                "leaking and causing network heating / battery drain."
            ),
            "ns_s9_no": (
                "Diagnostic:\n\n"
                "APT voltage is failing to boost during active search.\n\n"
                "If input VPH_PWR (4.2V) is present at APT IC but output coil doesn't boost to "
                "3.4V - 4.2V, the APT IC is faulty or the CPU is not triggering it.\n\n"
                "Replace the APT IC."
            ),
            "ns_s10_no": (
                "Diagnostic:\n\n"
                "MIPI RFFE lines are open or shorted.\n\n"
                "Since these lines control band selection and IC parameters directly from the CPU, "
                "an open line (OL) means a broken track or dry solder under the CPU/PA IC.\n\n"
                "Trace series resistors or reball the CPU."
            ),
            "ns_s11_no": (
                "Diagnostic:\n\n"
                "Antenna signal path is broken or shorted to ground.\n\n"
                "Check for damaged RF coaxial cables, missing series coils, or a grounded antenna "
                "switch track.\n\n"
                "Fix the hardware track break."
            ),
        },
    },
    "dp": {
        "title": "Dead Phone / Not Turning On Detected",
        "steps": {
            1: {
                "text": (
                    "Step 1: [Visual Test] Perform a thorough visual inspection of the device. Check "
                    "for any physical cracks on the screen/body or signs of water damage (corrosion on "
                    "components).\n\n"
                    "Is the phone physically clean and free of water damage?"
                ),
                "yes": 2,
                "no": "dp_s1_no",
            },
            2: {
                "text": (
                    "Step 2: [Force Restart] Try a Force Restart by pressing and holding the Power Button "
                    "+ Volume Down (or Volume Up) for 10 to 15 seconds.\n\n"
                    "Does the phone vibrate or display a logo?"
                ),
                "yes": "dp_s2_yes",
                "no": 3,
            },
            3: {
                "text": (
                    "Step 3: [6-Port Charger Test] Connect the dead phone to a professional 6-Port USB "
                    "Charger. Check the current consumption on the USB meter.\n\n"
                    "Is the amp drawing a normal charging current between 1.0A to 2.0A?"
                ),
                "yes": "dp_s3_yes",
                "no": 4,
            },
            4: {
                "text": (
                    "Step 4: [Battery Voltage Test] Open the back panel and detach the battery "
                    "connector. Measure the exact voltage directly on the battery terminals using a "
                    "multimeter.\n\n"
                    "Is the working voltage between 3.7V to 4.2V?"
                ),
                "yes": 5,
                "no": "dp_s4_no",
            },
            5: {
                "text": (
                    "Step 5: [DC Machine - Board Condition] Connect the motherboard to a DC Power "
                    "Supply machine set at 4.2V and 3A/5A limits. Look at the current meter before "
                    "pressing the Power Key.\n\n"
                    "Does it show an automatic current consumption/leakage (Auto-Amp) BEFORE pressing "
                    "the power button?"
                ),
                "yes": "dp_s5_yes",
                "no": 6,
            },
            6: {
                "text": (
                    "Step 6: [DC Machine - Power Key Response] Press the Power Key on the DC-connected "
                    "motherboard and observe the reading carefully.\n\n"
                    "Does the current trigger up slightly and get stuck (e.g., frozen at 0.02A - "
                    "0.06A) or instantly drop back to 0.00A when released?"
                ),
                "yes": 7,
                "no": "dp_s6_no",
            },
            7: {
                "text": (
                    "Step 7: [VPH_PWR Main Line Test] Check the primary systemic voltage output. "
                    "Measure the VPH_PWR voltage on the large inductor coil near the Charging IC "
                    "(SMB/OVP).\n\n"
                    "Is the full battery voltage (approx 3.7V - 4.2V) present on this coil?"
                ),
                "yes": 8,
                "no": "dp_s7_no",
            },
            8: {
                "text": (
                    "Step 8: [PMIC Core Buck Voltages] Check the secondary outputs. Keep the DC "
                    "machine connected, hold the power button, and measure the small Buck Coils "
                    "surrounding the Main PMIC.\n\n"
                    "Are all the core CPU voltages (0.8V, 1.0V, 1.2V) pulsing or steadily present?"
                ),
                "yes": 9,
                "no": "dp_s8_no",
            },
            9: {
                "text": (
                    "Step 9: [CPU Control & Reset Signals] Measure the PS_HOLD or PMIC_RESET_N line at "
                    "its respective test point or resistor (should read around 1.8V when power is pressed).\n\n"
                    "Is the 1.8V reset/hold signal stable?"
                ),
                "yes": 10,
                "no": "dp_s9_no",
            },
            10: {
                "text": (
                    "Step 10: [Final Diagnostic Solution]\n\n"
                    "Since all hardware lines, core power rails, and primary logic triggers are 100% "
                    "fine, the stuck DC current points to a corrupted Master Bootloader software layer.\n\n"
                    "Connect the motherboard to a PC via USB cable. If it detects ports like "
                    "'Qualcomm HS-USB QDLoader 9008' or 'MediaTek USB Port' automatically without "
                    "pressing buttons, flash the device using authorized software tools to fix the Dead issue."
                ),
                "yes": None,
                "no": None,
            },
        },
        "outcomes": {
            "dp_s1_no": (
                "Diagnostic:\n\n"
                "If water damage or heavy physical damage is found, do not power on.\n\n"
                "First, clean the motherboard with IsoPropyl Alcohol (IPA), dry it using a hot air "
                "blower, and inspect for corroded or shorted SMD components under the microscope."
            ),
            "dp_s2_yes": (
                "Diagnostic:\n\n"
                "Issue Solved! The phone was stuck in a software bootloop or screen-freeze state.\n\n"
                "Forced restart successfully recovered the device."
            ),
            "dp_s3_yes": (
                "Diagnostic:\n\n"
                "The motherboard, charging logic, and primary PMIC are active because it takes normal "
                "charging current.\n\n"
                "The issue is likely a dead/blank display folder or bad battery software connection. "
                "Check the display section."
            ),
            "dp_s4_no": (
                "Diagnostic:\n\n"
                "The battery is deeply discharged (below 3.6V). The phone cannot trigger boot logic "
                "with a dead battery.\n\n"
                "Boost the battery manually using a DC power supply or replace it, then try turning it on."
            ),
            "dp_s5_yes": (
                "Diagnostic:\n\n"
                "Auto-Amperage intake before pressing the power button means there is a Direct Short "
                "Circuit on the primary power lines, such as the VPH_PWR, VBAT, or Main System Rail.\n\n"
                "Locate the shorted capacitor using the rosin method or a thermal camera."
            ),
            "dp_s6_no": (
                "Diagnostic:\n\n"
                "If there is absolute 0.00A response after pressing the power button, check the "
                "physical Power Key flex connection, the power line's series resistor, or look for a dead/faulty Main PMIC."
            ),
            "dp_s7_no": (
                "Diagnostic:\n\n"
                "The VPH_PWR rail is failing to generate or is internally shorted. This blocks the "
                "main Power Management IC (PMIC) from booting.\n\n"
                "Inspect the Charging IC and replace it if necessary."
            ),
            "dp_s8_no": (
                "Diagnostic:\n\n"
                "Main PMIC is receiving input power but failing to produce output Buck voltages.\n\n"
                "This indicates a dead Main PMIC or a secondary short circuit on an LDO line. Replace the Main PMIC."
            ),
            "dp_s9_no": (
                "Diagnostic:\n\n"
                "PMIC is not getting the hold signal back, or the CPU is dead. The boot sequence is "
                "crashing at the hardware initialization stage.\n\n"
                "Reballing the CPU/RAM combo is necessary."
            ),
        },
    },
    "tw": {
        "title": "Touch Not Working Issue Detected",
        "steps": {
            1: {
                "text": (
                    "Step 1: [Visual Inspection] Carefully examine the screen surface and body for "
                    "physical cracks, deep scratches across the digitizer layer, or signs of pressure damage.\n\n"
                    "Is the screen physically intact with no cracks or visible digitizer damage?"
                ),
                "yes": 2,
                "no": "tw_s1_no",
            },
            2: {
                "text": (
                    "Step 2: Perform a full device restart. If that fails, attempt a factory reset or flash the stock firmware.\n\n"
                    "Does the touch respond correctly after a restart or software flash?"
                ),
                "yes": "tw_s2_yes",
                "no": 3,
            },
            3: {
                "text": (
                    "Step 3: Open the phone and carefully disconnect and reseat the display-to-motherboard flex connector. Clean the connector pins with IPA.\n\n"
                    "Does touch work correctly after reseating the connector?"
                ),
                "yes": "tw_s3_yes",
                "no": 4,
            },
            4: {
                "text": (
                    "Step 4: Locate the Touch IC on the motherboard. Measure the main VDD supply voltage on the capacitors around it (typically 3.3V or 1.8V).\n\n"
                    "Is the correct supply voltage present on the Touch IC?"
                ),
                "yes": 5,
                "no": "tw_s4_no",
            },
            5: {
                "text": (
                    "Step 5: Measure the RESET_N pin of the Touch IC at its test point or series resistor. It should briefly pulse to 1.8V during power-on.\n\n"
                    "Is the reset pulse present and reaching the Touch IC?"
                ),
                "yes": 6,
                "no": "tw_s5_no",
            },
            6: {
                "text": (
                    "Step 6: Measure the INT (Interrupt) pin from the Touch IC to the CPU in Diode Mode (GR) — it should show approx 400–600 mV.\n\n"
                    "Is the interrupt line intact (no OL/Short) and showing a normal GR value?"
                ),
                "yes": 7,
                "no": "tw_s6_no",
            },
            7: {
                "text": (
                    "Step 7: Measure the Touch_SDA and Touch_SCL lines in Diode Mode from the CPU side to the Touch IC. Normal GR values should read approx 500–700 mV.\n\n"
                    "Are both I2C lines balanced and reading normally?"
                ),
                "yes": 8,
                "no": "tw_s7_no",
            },
            8: {
                "text": (
                    "Step 8: [Final Diagnostic Solution]\n\n"
                    "All power rails, reset signal, interrupt line, and I2C communication lines are 100% intact. This confirms the Touch IC internal logic is dead.\n\n"
                    "Replace the Touch IC with a brand new working part."
                ),
                "yes": None,
                "no": None,
            },
        },
        "outcomes": {
            "tw_s1_no": (
                "Diagnostic:\n\n"
                "The digitizer glass or touch layer is physically cracked or damaged.\n\n"
                "Replace the complete display assembly (LCD + Digitizer)."
            ),
            "tw_s2_yes": (
                "Diagnostic:\n\n"
                "Issue Solved! The touch fault was caused by a software or firmware corruption."
            ),
            "tw_s3_yes": (
                "Diagnostic:\n\n"
                "Issue Solved! The touch fault was caused by a loose or dirty display flex connector."
            ),
            "tw_s4_no": (
                "Diagnostic:\n\n"
                "Touch IC main power supply (VDD) is missing. Trace the VDD line from the PMIC LDO output to the Touch IC."
            ),
            "tw_s5_no": (
                "Diagnostic:\n\n"
                "The Touch IC is not receiving its reset signal from the CPU. Check the RESET_N series resistor."
            ),
            "tw_s6_no": (
                "Diagnostic:\n\n"
                "The Touch IC interrupt line is open (OL) or shorted. An OL reading means the track between Touch IC and CPU is broken."
            ),
            "tw_s7_no": (
                "Diagnostic:\n\n"
                "I2C communication lines (SDA/SCL) between the CPU and Touch IC are faulty."
            ),
        },
    },
    "mc": {
        "title": "Mic / Microphone Not Working Issue Detected",
        "steps": {
            1: {
                "text": (
                    "Step 1: Open the Voice Recorder app and record a short audio clip.\n\n"
                    "Does the microphone work correctly in apps other than the Phone/Dialer?"
                ),
                "yes": "mc_s1_yes",
                "no": 2,
            },
            2: {
                "text": (
                    "Step 2: Inspect the microphone pinhole at the bottom of the phone for dust or blockage.\n\n"
                    "Is the microphone pinhole completely clear and unobstructed?"
                ),
                "yes": 3,
                "no": "mc_s2_no",
            },
            3: {
                "text": (
                    "Step 3: Open the phone, reseat all sub-board connectors, and clean pins with IPA.\n\n"
                    "Does the microphone work correctly after resetting the connectors?"
                ),
                "yes": "mc_s3_yes",
                "no": 4,
            },
            4: {
                "text": (
                    "Step 4: Measure the MICBIAS output voltage on the microphone bias line (should read approx 1.8V – 2.8V when mic is active).\n\n"
                    "Is the MICBIAS voltage present and within range?"
                ),
                "yes": 5,
                "no": "mc_s4_no",
            },
            5: {
                "text": (
                    "Step 5: Measure the MIC_IN signal line in Diode Mode (GR) from the microphone pad back to the Audio Codec IC input pin.\n\n"
                    "Is the MIC_IN line intact with a normal GR reading of approx 400–600 mV?"
                ),
                "yes": 6,
                "no": "mc_s5_no",
            },
            6: {
                "text": (
                    "Step 6: Measure the AVDD supply voltage on the decoupling capacitors around the Audio Codec IC (typically 1.8V or 3.3V).\n\n"
                    "Is the Audio Codec IC supply voltage present and correct?"
                ),
                "yes": 7,
                "no": "mc_s6_no",
            },
            7: {
                "text": (
                    "Step 7: Measure the I2C/I2S communication lines (SDA, SCL, BCLK, DOUT) from the CPU to the Audio Codec IC in Diode Mode.\n\n"
                    "Are all control lines showing balanced GR values (approx 400–700 mV)?"
                ),
                "yes": 8,
                "no": "mc_s7_no",
            },
            8: {
                "text": (
                    "Step 8: [Final Diagnostic Solution]\n\n"
                    "All primary rails are perfect. The Audio Codec IC internal mic amplifier is dead.\n\n"
                    "Replace the Audio Codec IC with a new working part."
                ),
                "yes": None,
                "no": None,
            },
        },
        "outcomes": {
            "mc_s1_yes": "Diagnostic:\n\nThe microphone hardware is working. Clear Dialer app cache and data.",
            "mc_s2_no": "Diagnostic:\n\nMicrophone hole is blocked. Clean it safely using a fine brush.",
            "mc_s3_yes": "Diagnostic:\n\nIssue Resolved! Reseating the sub-board/main flex fixed the issue.",
            "mc_s4_no": "Diagnostic:\n\nMICBIAS 1.8V-2.8V is missing. Check for shorted caps or replace Audio Codec IC.",
            "mc_s5_no": "Diagnostic:\n\nMIC_IN line is open (OL) or shorted. Fix the broken trace or change mic component.",
            "mc_s6_no": "Diagnostic:\n\nCodec AVDD main supply is missing. Check PMIC LDO output line.",
            "mc_s7_no": "Diagnostic:\n\nI2C/I2S digital lines are faulty. Check series resistors or reball CPU.",
        },
    },
    "ab": {
        "title": "Automatic Restart / Bootloop Issue Detected",
        "steps": {
            1: {
                "text": (
                    "Step 1: Open the phone panel. Disconnect the physical Power Key Flex Cable from the motherboard, then connect the battery and charger.\n\n"
                    "Does the phone still turn on automatically and continue to restart on the logo?"
                ),
                "yes": 2,
                "no": "ab_s1_no",
            },
            2: {
                "text": (
                    "Step 2: Connect the phone to a PC via USB cable while it is restarting.\n\n"
                    "Does the PC make a connection sound or temporarily show any USB diagnostic ports "
                    "(like Qualcomm 9008 or MediaTek Port) before the phone vibrates/restarts again?"
                ),
                "yes": "ab_s2_yes",
                "no": 3,
            },
            3: {
                "text": (
                    "Step 3: Measure the Battery Thermistor / ID line (BAT_THERM / BAT_ID) on the motherboard battery connector in Diode Mode (GR).\n\n"
                    "Is the GR value normal (typically 400-700 mV, no OL or short)?"
                ),
                "yes": 4,
                "no": "ab_s3_no",
            },
            4: {
                "text": (
                    "Step 4: Connect the motherboard to a DC Power Supply machine. Press the power button to trigger boot and observe the current meter when it restarts.\n\n"
                    "Does the current consumption jump up high (above 0.5A) and instantly drop or freeze at a specific low reading when the restart happens?"
                ),
                "yes": 5,
                "no": "ab_s4_no",
            },
            5: {
                "text": (
                    "Step 5: Measure the core digital supply voltages (1.8V LDO, System PMU lines) around the Main PMIC while the phone attempts to boot.\n\n"
                    "Are all primary communication voltages stable without dropping to 0V during the boot loop?"
                ),
                "yes": 6,
                "no": "ab_s5_no",
            },
            6: {
                "text": (
                    "Step 6: [Final Hardware Diagnostic Solution]\n\n"
                    "All buttons, thermistors, basic power rails, and logic supplies are completely stable, but the CPU execution halts during system initialization.\n\n"
                    "This strongly indicates dry solder balls underneath the Main CPU or RAM chip due to structural drops/heating.\n\n"
                    "Action: Reball the CPU and RAM. If the issue continues, flash the device with an authorized factory ROM firmware."
                ),
                "yes": None,
                "no": None,
            },
        },
        "outcomes": {
            "ab_s1_no": (
                "Diagnostic:\n\n"
                "The hardware Power Button switch is internally shorted or jammed, sending a continuous turn-on signal to the PMIC.\n\n"
                "Replace the Power Key Flex Cable or the SMD switch button component."
            ),
            "ab_s2_yes": (
                "Diagnostic:\n\n"
                "The device hardware is forcing an emergency download partition trigger.\n\n"
                "This is caused by either a deeply corrupted software Master Bootloader, a corrupted EMMC/UFS partition, or a hardware data line short.\n\n"
                "Attempt to full-flash the phone using specialized service tools."
            ),
            "ab_s3_no": (
                "Diagnostic:\n\n"
                "The CPU cannot read the battery thermal status or ID parameters due to an open/shorted line.\n\n"
                "To prevent damage, the system firmware triggers an automatic safety reboot loop.\n\n"
                "Repair the broken track or components connected to the BAT_THERM/ID pin."
            ),
            "ab_s4_no": (
                "Diagnostic:\n\n"
                "A sudden current drop or freeze below normal boot parameters indicates a secondary short circuit that triggers when high-power modules (like Wi-Fi, Audio Amp, or Baseband) activate.\n\n"
                "Isolate the shorted secondary LDO line using Rosin method."
            ),
            "ab_s5_no": (
                "Diagnostic:\n\n"
                "The Main PMIC internal logic or its reference buck coils are faulty, causing an instantaneous voltage collapse under load.\n\n"
                "Replace the Main PMIC or output power coils."
            ),
        },
    },
    "sp": {
        "title": "Speaker / No Sound Issue Detected",
        "steps": {
            1: {
                "text": (
                    "Step 1: Play audio in multiple apps — music player, YouTube, ringtone test.\n\n"
                    "Does sound work in any app at all, or is there complete silence across everything?"
                ),
                "yes": "sp_s1_yes",
                "no": 2,
            },
            2: {
                "text": (
                    "Step 2: Confirm the phone is NOT in Silent or Do Not Disturb mode. Set volumes to maximum.\n\n"
                    "Is the phone at full volume with all silent modes disabled, and still no sound?"
                ),
                "yes": 3,
                "no": "sp_s2_no",
            },
            3: {
                "text": (
                    "Step 3: Open the phone, clean and reseat the speaker flex and sub-board connector using IPA.\n\n"
                    "Does sound return after reseating the connector?"
                ),
                "yes": "sp_s3_yes",
                "no": 4,
            },
            4: {
                "text": (
                    "Step 4: Measure the resistance directly across the speaker or earpiece terminals using a multimeter.\n\n"
                    "Does the speaker show a normal resistance between 4 Ω and 32 Ω?"
                ),
                "yes": 5,
                "no": "sp_s4_no",
            },
            5: {
                "text": (
                    "Step 5: Locate the Speaker Amplifier IC. Measure the main supply voltage (PVDD / VDD) on its capacitors (typically 3.6V–4.2V).\n\n"
                    "Is the supply voltage present at the Speaker Amp IC?"
                ),
                "yes": 6,
                "no": "sp_s5_no",
            },
            6: {
                "text": (
                    "Step 6: Measure the differential output lines (SPK_OUTP and SPK_OUTN) from the Amp IC to the speaker pads in Diode Mode (GR).\n\n"
                    "Are both output lines intact with balanced GR readings?"
                ),
                "yes": 7,
                "no": "sp_s6_no",
            },
            7: {
                "text": (
                    "Step 7: Measure the I2C (SDA/SCL) or I2S (BCLK, DIN) control lines from the CPU to the Speaker Amp IC in Diode Mode.\n\n"
                    "Are all lines showing balanced GR values (approx 400–700 mV)?"
                ),
                "yes": 8,
                "no": "sp_s7_no",
            },
            8: {
                "text": (
                    "Step 8: [Final Diagnostic Solution]\n\n"
                    "Tracks and power are intact. The Speaker Amplifier IC is dead.\n\n"
                    "Replace the Speaker Amplifier IC."
                ),
                "yes": None,
                "no": None,
            },
        },
        "outcomes": {
            "sp_s1_yes": "Diagnostic:\n\nSpeaker hardware is fine. Check software routing or per-app audio settings.",
            "sp_s2_no": "Diagnostic:\n\nIssue Resolved! Phone was in silent or DND mode.",
            "sp_s3_yes": "Diagnostic:\n\nIssue Resolved! Fixed by cleaning and firmly locking the connectors.",
            "sp_s4_no": "Diagnostic:\n\nSpeaker voice coil is broken (OL) or shorted (0 Ω). Replace the speaker ringtone module.",
            "sp_s5_no": "Diagnostic:\n\nAmp supply voltage is missing. Trace power line back to VBAT / VPH_PWR rail.",
            "sp_s6_no": "Diagnostic:\n\nOutput lines SPK_OUTP/N are damaged. Repair broken PCB trace or replace Amp IC if shorted to ground.",
            "sp_s7_no": "Diagnostic:\n\nCPU to Speaker Amp I2C/I2S lines are broken. Check pull-ups or reball CPU.",
        },
    },
}


def make_yes_no_keyboard(flow: str, step: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("YES", callback_data=f"{flow}:{step}:yes"),
        InlineKeyboardButton("NO",  callback_data=f"{flow}:{step}:no"),
    ]])


def make_restart_keyboard(flow: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("Restart Diagnosis", callback_data=f"{flow}:restart"),
    ]])


def is_authorized(user_id: int) -> bool:
    return user_id == ADMIN_ID or user_id in AUTHORIZED_USERS


def welcome_text(first_name: str, lang: str) -> str:
    if lang == "ml":
        return (
            f"ഹലോ {first_name}! 👋 മൊബൈൽ ഫോൺ ഡയഗ്നോസ്റ്റിക് അസിസ്റ്റന്റിലേക്ക് സ്വാഗതം.\n\n"
            "നിങ്ങളുടെ ഫോണിന്റെ ഫോൾട്ട് എന്താണെന്ന് താഴെ ടൈപ്പ് ചെയ്യുക (ഉദാഹരണത്തിന്: 'no service', 'dead phone', 'dc reading'). "
            "വൺ-ബൈ-വൺ ആയി കംപ്ലാന്റ് കണ്ടുപിടിക്കാൻ ബോട്ട് നിങ്ങളെ സഹായിക്കും."
        )
    else:
        return (
            f"Hi {first_name}! 👋 Welcome to the Mobile Phone Diagnostic Assistant.\n\n"
            "Please type your exact issue (e.g., 'no service', 'dead phone', 'dc reading') to start the step-by-step troubleshooting."
        )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user

    if is_authorized(user.id):
        # Trigger Language Selection Buttons right at start
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
            InlineKeyboardButton("🇲🇱 മലയാളം", callback_data="lang_ml"),
        ]])
        await update.message.reply_text(
            "🌐 **Select Your Language / ഭാഷ തിരഞ്ഞെടുക്കുക**\n\n"
            "Please select your preferred language to continue:\n"
            "ദയവായി മുന്നോട്ട് പോകാൻ നിങ്ങളുടെ ഭാഷ തിരഞ്ഞെടുക്കുക:",
            reply_markup=keyboard,
        )
        return

    await update.message.reply_text(
        "Your access request has been sent to the Admin. Please wait for approval..."
    )

    if ADMIN_ID:
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("Accept ✅", callback_data=f"admin:accept:{user.id}"),
            InlineKeyboardButton("Reject ❌", callback_data=f"admin:reject:{user.id}"),
        ]])
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                "🔔 New Access Request!\n\n"
                f"👤 Name: {user.first_name}\n"
                f"🆔 Chat ID: {user.id}\n\n"
                "Do you want to allow this user?"
            ),
            reply_markup=keyboard,
        )
    else:
        logger.warning("ADMIN_ID is not set. Cannot forward access request.")


async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    _, action, target_id_str = query.data.split(":")
    target_id = int(target_id_str)

    if action == "accept":
        AUTHORIZED_USERS.add(target_id)
        await query.edit_message_text(
            text=query.message.text + "\n\nApproved ✅"
        )
        await context.bot.send_message(
            chat_id=target_id,
            text=(
                "🎉 Congratulations! Your request has been approved by the Admin.\n\n"
                "You can now use the bot. Send /start to select your language and begin!"
            ),
        )
    elif action == "reject":
        await query.edit_message_text(
            text=query.message.text + "\n\nRejected ❌"
        )
        await context.bot.send_message(
            chat_id=target_id,
            text="⚠️ Sorry, your request was declined by the Admin.",
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    lang = USER_LANGUAGES.get(user_id, "en")
    
    if lang == "ml":
        await update.message.reply_text(
            "ബോട്ട് ഉപയോഗിക്കേണ്ട രീതി:\n\n"
            "1. നിങ്ങളുടെ ഫോണിന്റെ കംപ്ലാന്റ് സാധാരണ വാക്കുകളിൽ ടൈപ്പ് ചെയ്യുക.\n\n"
            "ഉദാഹരണങ്ങൾ:\n"
            "  • graphic issue, no display, display problem\n"
            "  • black display, light issue, no backlight\n"
            "  • blank screen, white screen, dead screen\n"
            "  • no charging, not charging, slow charging\n"
            "  • no service, no network, baseband missing\n"
            "  • dead phone, not turning on, phone dead\n"
            "  • touch not working, touch issue, touchscreen\n"
            "  • mic not working, microphone issue, call audio\n"
            "  • speaker not working, no sound, earpiece\n"
            "  • auto restart, bootloop, logo blink\n"
            "  • dc reading, dc chart\n\n"
            "2. ചോദ്യങ്ങൾക്ക് താഴെ കാണുന്ന YES / NO ബട്ടണുകൾ ഉപയോഗിച്ച് മറുപടി നൽകുക.\n"
            "3. ബോട്ട് റൂട്ട് കോസ് കണ്ടെത്താനും പരിഹാരങ്ങൾ നൽകാനും സഹായിക്കും."
        )
    else:
        await update.message.reply_text(
            "How to use this bot:\n\n"
            "1. Type your phone problem in plain text.\n\n"
            "Examples:\n"
            "  • graphic issue, no graphic, display issue, screen problem\n"
            "  • black display, no backlight, light issue, screen dark\n"
            "  • blank display, blank screen, white screen, dead screen\n"
            "  • no charging, not charging, charging issue, charging problem\n"
            "  • no service, no network, no signal, baseband missing\n"
            "  • dead phone, dead complaint, not turning on, won't turn on\n"
            "  • touch not working, touch issue, touchscreen issue\n"
            "  • mic not working, microphone issue, call audio issue\n"
            "  • speaker not working, no sound, loudspeaker issue\n"
            "  • auto restart, bootloop, logo blink\n"
            "  • dc reading, dc chart\n\n"
            "2. Follow the YES / NO buttons at each step.\n"
            "3. The bot will guide you to the root cause and recommend a fix."
        )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not is_authorized(user.id):
        await update.message.reply_text(
            "⚠️ You are not authorized. Please send /start to request access."
        )
        return

    text = update.message.text or ""
    logger.info("Received message: %s", text)
    
    lang = USER_LANGUAGES.get(user.id, "en")

    if SPEAKER_KEYWORDS.search(text):
        flow = "sp"
        await update.message.reply_text(
            FLOWS[flow]["title"] + "\n\n" + FLOWS[flow]["steps"][1]["text"],
            reply_markup=make_yes_no_keyboard(flow, 1),
        )
    elif MIC_KEYWORDS.search(text):
        flow = "mc"
        await update.message.reply_text(
            FLOWS[flow]["title"] + "\n\n" + FLOWS[flow]["steps"][1]["text"],
            reply_markup=make_yes_no_keyboard(flow, 1),
        )
    elif TOUCH_KEYWORDS.search(text):
        flow = "tw"
        await update.message.reply_text(
            FLOWS[flow]["title"] + "\n\n" + FLOWS[flow]["steps"][1]["text"],
            reply_markup=make_yes_no_keyboard(flow, 1)
        )
    elif AUTOMATIC_BOOTLOOP_KEYWORDS.search(text):
        flow = "ab"
        await update.message.reply_text(
            FLOWS[flow]["title"] + "\n\n" + FLOWS[flow]["steps"][1]["text"],
            reply_markup=make_yes_no_keyboard(flow, 1)
        )
    elif re.search(r"\b(dc[\s\-]?reading|dc[\s\-]?chart)\b", text, re.IGNORECASE):
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton(
                "Auto Ampere (Before Power Key)", callback_data="dc:auto"
            ),
            InlineKeyboardButton(
                "After Power Key Press", callback_data="dc:boot"
            ),
        ]])
        
        msg = (
            "📊 DC Power Supply Fault Finding\n\n"
            "മദർബോർഡിൽ എപ്പോഴാണ് റീഡിങ് കാണിക്കുന്നത്? താഴെയുള്ള കൃത്യമായ ഓപ്ഷൻ സെലക്ട് ചെയ്യുക:"
            if lang == "ml" else
            "📊 DC Power Supply Fault Finding\n\n"
            "When does the machine show reading? Please select the exact option below:"
        )
        await update.message.reply_text(msg, reply_markup=keyboard)
        return
    elif DEAD_PHONE_KEYWORDS.search(text):
        flow = "dp"
        await update.message.reply_text(
            FLOWS[flow]["title"] + "\n\n" + FLOWS[flow]["steps"][1]["text"],
            reply_markup=make_yes_no_keyboard(flow, 1),
        )
    elif NO_SERVICE_KEYWORDS.search(text):
        flow = "ns"
        await update.message.reply_text(
            FLOWS[flow]["title"] + "\n\n" + FLOWS[flow]["steps"][1]["text"],
            reply_markup=make_yes_no_keyboard(flow, 1),
        )
    elif CHARGING_KEYWORDS.search(text):
        flow = "nc"
        await update.message.reply_text(
            FLOWS[flow]["title"] + "\n\n" + FLOWS[flow]["steps"][1]["text"],
            reply_markup=make_yes_no_keyboard(flow, 1),
        )
    elif BLANK_DISPLAY_KEYWORDS.search(text):
        flow = "bd"
        await update.message.reply_text(
            FLOWS[flow]["title"] + "\n\n" + FLOWS[flow]["steps"][1]["text"],
            reply_markup=make_yes_no_keyboard(flow, 1),
        )
    elif BACKLIGHT_KEYWORDS.search(text):
        flow = "bl"
        await update.message.reply_text(
            FLOWS[flow]["title"] + "\n\n" + FLOWS[flow]["steps"][1]["text"],
            reply_markup=make_yes_no_keyboard(flow, 1),
        )
    elif GRAPHIC_KEYWORDS.search(text):
        flow = "g"
        await update.message.reply_text(
            FLOWS[flow]["title"] + "\n\n" + FLOWS[flow]["steps"][1]["text"],
            reply_markup=make_yes_no_keyboard(flow, 1),
        )
    else:
        if lang == "ml":
            await update.message.reply_text(
                "മൊബൈൽ കംപ്ലാന്റുകൾ കണ്ടെത്താൻ ഞാൻ സഹായിക്കാം.\n\n"
                "ഇതുപോലെ ടൈപ്പ് ചെയ്ത് നോക്കൂ:\n"
                "  • graphic issue / no graphic / display issue\n"
                "  • black display / no backlight / light issue\n"
                "  • blank display / white screen / dead screen\n"
                "  • no charging / not charging / slow charging\n"
                "  • no service / no network / baseband unknown\n"
                "  • auto restart / bootloop / logo blink\n\n"
                "കൂടുതൽ വിവരങ്ങൾക്ക് /help എന്ന് ടൈപ്പ് ചെയ്യുക."
            )
        else:
            await update.message.reply_text(
                "I can help diagnose phone issues.\n\n"
                "Try describing a problem, for example:\n"
                "  • graphic issue / no graphic / display issue\n"
                "  • black display / no backlight / light issue\n"
                "  • blank display / blank screen / dead screen\n"
                "  • no charging / not charging / charging issue\n"
                "  • auto restart / bootloop / logo blink\n\n"
                "Use /help for more information."
            )


async def handle_language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    data = query.data
    
    if data == "lang_en":
        USER_LANGUAGES[user.id] = "en"
        await query.edit_message_text(text="🇬🇧 Language set to English!")
        await context.bot.send_message(chat_id=user.id, text=welcome_text(user.first_name, "en"))
    elif data == "lang_ml":
        USER_LANGUAGES[user.id] = "ml"
        await query.edit_message_text(text="🇲🇱 ഭാഷ മലയാളം ആയി സെറ്റ് ചെയ്തിരിക്കുന്നു!")
        await context.bot.send_message(chat_id=user.id, text=welcome_text(user.first_name, "ml"))


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    data = query.data
    parts = data.split(":")

    flow_key = parts[0]
    if flow_key not in FLOWS:
        return

    flow = FLOWS[flow_key]

    if parts[1] == "restart":
        await query.edit_message_text(
            text=flow["title"] + "\n\n" + flow["steps"][1]["text"],
            reply_markup=make_yes_no_keyboard(flow_key, 1),
        )
        return

    if len(parts) != 3:
        return

    _, step_str, choice = parts
    step = int(step_str)
    step_data = flow["steps"].get(step)
    if not step_data:
        return

    action = step_data["yes"] if choice == "yes" else step_data["no"]

    if action is None:
        await query.edit_message_text(
            text=step_data["text"] + "\n\n---\nDiagnosis complete. Consult a qualified technician for further assistance.",
            reply_markup=make_restart_keyboard(flow_key),
        )

    elif isinstance(action, str) and action in flow["outcomes"]:
        await query.edit_message_text(
            text=flow["outcomes"][action],
            reply_markup=make_restart_keyboard(flow_key),
        )

    elif isinstance(action, int) and action in flow["steps"]:
        await query.edit_message_text(
            text=flow["steps"][action]["text"],
            reply_markup=make_yes_no_keyboard(flow_key, action),
        )


async def handle_dc_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    choice = query.data.split(":")[1]

    if choice == "auto":
        await query.edit_message_text(
            "⚡ AUTO AMPERE INTAKE (Before Pressing Power Key):\n\n"
            "0.001A (Stuck): Secondary Line Short / Small Leakage\n"
            "0.002A (Stuck): 4G PA Section Issue\n"
            "0.001A - 0.003A (Stuck): Power IC Issue or Charging IC Issue\n"
            "FULL AMPERE (3A+ Stuck): VBAT / VPH_PWR Short Circuit\n"
            "0.003A (Stuck): Power IC Issue\n"
            "0.026A (Stuck): Secondary Line Short\n\n"
            "🛠️ Fix: Primary short ഓട്ടോ ആംപിയർ കാണിച്ചാൽ റസിൻ (Rosin Method) "
            "ഉപയോഗിച്ചോ തെർമൽ കാമറ ഉപയോഗിച്ചോ കംപ്ലാന്റ് ഉള്ള കപ്പാസിറ്റർ കണ്ടെത്തുക."
        )
    elif choice == "boot":
        await query.edit_message_text(
            "📲 AFTER PRESSING POWER KEY (Boot Readings):\n\n"
            "0.149A (0.120A - 0.200A Stuck): RAM Not Connected / RAM Communication Fault\n"
            "0.116A - 0.225A or 0.291A - 0.269A (Fluctuating): Check Charging Ampere / Check Battery ID Line\n"
            "0.00A - 0.60A (Fluctuating, Drops to 0 on release): Check Core Voltages / PMIC / CPU Initialization Fault\n"
            "0.640A - 0.639A (High Amp Fluctuating, Drops to 0 on release): Check Heat Component\n"
            "0.050A - 0.120A (Stuck): EMMC / UFS Storage or Software Issue\n"
            "0.004A - 0.005A (Fluctuating, Drops to 0 on release): LDO / Buck Voltage Missing\n"
            "0.120A - 0.200A (Stuck, Drops to 0 on release): Software Corrupted / EMMC Not Connected\n"
            "0.001A - 0.003A (Stuck): Power IC Issue / Charging IC Issue\n"
            "0.020A - 0.036A (Stuck, Drops to 0 on release): CPU Faulty / Dead CPU Core\n"
            "0.036A (Stuck, Drops to 0 on release): Secondary Line Short Circuit\n"
            "0.132A (Stuck, Drops to 0 on release): Check Port Manager / USB PHY Controller\n"
            "0.136A (Stuck): Check EMMC Health / Needs Reballing EMMC\n"
            "0.002A - 0.005A (Fluctuating): LDO / Buck Line Instability\n\n"
            "🛠️ Fix: കറന്റ് സ്റ്റക്ക് ആയി നിൽക്കുന്നതും ഫ്ലക്ചുവേറ്റ് ചെയ്യുന്നതും നോക്കി "
            "ഇഎംഎംസി (EMMC) മാറ്റി പ്രോഗ്രാം ചെയ്യുകയോ സിപിയു (CPU) റീബോൾ ചെയ്യുകയോ ചെയ്യുക."
        )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Exception while handling an update:", exc_info=context.error)


def main() -> None:
    if not BOT_TOKEN:
        raise ValueError(
            "TELEGRAM_BOT_TOKEN environment variable is not set. "
            "Get a token from @BotFather on Telegram."
        )

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(handle_language_callback, pattern=r"^lang_"))
    app.add_handler(CallbackQueryHandler(handle_admin_callback, pattern=r"^admin:"))
    app.add_handler(CallbackQueryHandler(handle_dc_callback, pattern=r"^dc:"))
    app.add_handler(CallbackQueryHandler(handle_callback, pattern=r"^(g|bl|bd|nc|ns|dp|tw|mc|sp|ab):"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)

    logger.info("Diagnostic bot is running. Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
