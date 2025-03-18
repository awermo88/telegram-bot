import logging
import os
import math
import matplotlib.pyplot as plt
from pyproj import Proj, Transformer, Geod
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, CallbackContext

# تنظیمات لاگ
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


TOKEN = "7565947478:AAGdwaH8on-OnhC9rEhZuFi3S_GUkm3MbMw"

# --- ایجاد منوها ---
def create_main_menu():
    keyboard = [
        [InlineKeyboardButton("جعبه ابزار", callback_data="tools")],
        [InlineKeyboardButton("ورود به کانال", url="https://t.me/TEST2069")],
        [InlineKeyboardButton("ورود به سایت", url="https://MYSURVEY.IR")]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_tools_menu():
    keyboard = [
        [InlineKeyboardButton("ابزار نقشه‌برداری", callback_data="surveying_tools")],
        [InlineKeyboardButton("بازگشت", callback_data="back")]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_surveying_menu():
    keyboard = [
        [InlineKeyboardButton("📍 تبدیل UTM به Lat/Lon", callback_data="utm_to_latlon")],
        [InlineKeyboardButton("📏 فاصله و آزیموت", callback_data="distance_azimuth")],
        [InlineKeyboardButton("📐 تبدیل DMS به درجه اعشاری", callback_data="dms_to_decimal")],
        [InlineKeyboardButton("📊 محاسبه مساحت چندضلعی", callback_data="polygon_area")],
        [InlineKeyboardButton("🛰️ تبدیل سیستم مختصاتی", callback_data="coordinate_conversion")],
        [InlineKeyboardButton("🔢 تصحیح انحراف زمین", callback_data="geodetic_correction")],
        [InlineKeyboardButton("⛰️ محاسبه شیب", callback_data="slope_calculation")],
        [InlineKeyboardButton("📝 تبدیل مختصات به رشته", callback_data="coord_to_string")],
        [InlineKeyboardButton("📦 محاسبه حجم مخروط", callback_data="cone_volume")],
        [InlineKeyboardButton("∠ زاویه بین سه نقطه", callback_data="angle_three_points")],
        [InlineKeyboardButton("🔲 مختصات نقطه تقاطع", callback_data="intersection_point")],
        [InlineKeyboardButton("📏 تصحیح زاویه بسته", callback_data="angle_closure")],
        [InlineKeyboardButton("↕️ فاصله عمودی", callback_data="vertical_distance")],
        [InlineKeyboardButton("🌍 تبدیل به UTM محلی", callback_data="local_utm_conversion")],
        [InlineKeyboardButton("🗺️ ترسیم مساحت زمین", callback_data="plot_land_area")],
        [InlineKeyboardButton("بازگشت", callback_data="tools")]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_continue_menu():
    keyboard = [[InlineKeyboardButton("بازگشت به ابزارها", callback_data="surveying_tools")]]
    return InlineKeyboardMarkup(keyboard)

# --- مدیریت خطاها ---
async def error_handler(update: Update, context: CallbackContext):
    logger.error(f"خطا رخ داد: {context.error}")
    if update and update.message:
        await update.message.reply_text("❌ یه مشکلی پیش اومد! لطفاً دوباره امتحان کنید یا اتصال اینترنت رو چک کنید.")

# --- مدیریت منوها ---
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("به ربات خوش آمدید! گزینه‌ای را انتخاب کنید:", reply_markup=create_main_menu())

async def menu_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    if query.data == "tools":
        await query.edit_message_text("لطفاً یک گزینه را انتخاب کنید:", reply_markup=create_tools_menu())
    elif query.data == "surveying_tools":
        await query.edit_message_text("📍 ابزارهای نقشه‌برداری:", reply_markup=create_surveying_menu())
    elif query.data == "utm_to_latlon":
        context.user_data["waiting_for"] = "easting"
        await query.edit_message_text("لطفاً مقدار **Easting** را وارد کنید (متر):")
    elif query.data == "distance_azimuth":
        context.user_data["waiting_for"] = "lat1"
        await query.edit_message_text("لطفاً **عرض جغرافیایی نقطه ۱** را وارد کنید (درجه):")
    elif query.data == "dms_to_decimal":
        context.user_data["waiting_for"] = "degree"
        await query.edit_message_text("لطفاً مقدار **درجه** را وارد کنید:")
    elif query.data == "polygon_area":
        context.user_data["polygon_points"] = []
        context.user_data["waiting_for"] = "polygon"
        await query.edit_message_text("📌 نقاط چندضلعی را وارد کنید (lat, lon) یا 'محاسبه' را بنویسید:")
    elif query.data == "coordinate_conversion":
        context.user_data["waiting_for"] = "source_x"
        await query.edit_message_text("📍 مقدار X را برای تبدیل سیستم مختصاتی وارد کنید:")
    elif query.data == "geodetic_correction":
        context.user_data["waiting_for"] = "distance"
        await query.edit_message_text("📏 فاصله بین دو نقطه را وارد کنید (متر):")
    elif query.data == "slope_calculation":
        context.user_data["waiting_for"] = "height1"
        await query.edit_message_text("لطفاً **ارتفاع نقطه ۱** را وارد کنید (متر):")
    elif query.data == "coord_to_string":
        context.user_data["waiting_for"] = "lat_string"
        await query.edit_message_text("لطفاً **عرض جغرافیایی** را وارد کنید (درجه اعشاری):")
    elif query.data == "cone_volume":
        context.user_data["waiting_for"] = "radius"
        await query.edit_message_text("لطفاً **شعاع قاعده مخروط** را وارد کنید (متر):")
    elif query.data == "angle_three_points":
        context.user_data["waiting_for"] = "x1_angle"
        await query.edit_message_text("لطفاً **X نقطه ۱** را وارد کنید:")
    elif query.data == "intersection_point":
        context.user_data["waiting_for"] = "x1_intersect"
        await query.edit_message_text("لطفاً **X نقطه ۱ خط اول** را وارد کنید:")
    elif query.data == "angle_closure":
        context.user_data["angles"] = []
        context.user_data["waiting_for"] = "angle_input"
        await query.edit_message_text("لطفاً زوایا را یکی‌یکی وارد کنید (درجه) یا 'محاسبه' را بنویسید:")
    elif query.data == "vertical_distance":
        context.user_data["waiting_for"] = "height_v"
        await query.edit_message_text("لطفاً **ارتفاع نقطه** را وارد کنید (متر):")
    elif query.data == "local_utm_conversion":
        context.user_data["waiting_for"] = "lat_utm"
        await query.edit_message_text("لطفاً **عرض جغرافیایی** را وارد کنید (درجه):")
    elif query.data == "plot_land_area":
        context.user_data["land_points"] = []
        context.user_data["waiting_for"] = "location"
        await query.edit_message_text("📍 لطفاً لوکیشن نقاط زمین رو یکی‌یکی بفرستید (با دکمه لوکیشن تلگرام). وقتی تموم شد، بنویسید 'محاسبه'.")
    elif query.data == "back":
        await query.edit_message_text("به منوی اصلی بازگشتید.", reply_markup=create_main_menu())

# --- دریافت داده‌های ورودی از کاربر ---
async def handle_text(update: Update, context: CallbackContext):
    waiting_for = context.user_data.get("waiting_for")
    text = update.message.text.strip() if update.message.text else None

    try:
        if waiting_for == "easting":
            context.user_data["easting"] = float(text)
            context.user_data["waiting_for"] = "northing"
            await update.message.reply_text("لطفاً مقدار **Northing** را وارد کنید:")
        elif waiting_for == "northing":
            context.user_data["northing"] = float(text)
            context.user_data["waiting_for"] = "zone"
            await update.message.reply_text("لطفاً شماره **Zone** را وارد کنید:")
        elif waiting_for == "zone":
            lat, lon = utm_to_latlon(context.user_data["easting"], context.user_data["northing"], int(text))
            await update.message.reply_text(f"✅ تبدیل انجام شد:\n**Latitude:** {lat:.6f}\n**Longitude:** {lon:.6f}", reply_markup=create_continue_menu())
            context.user_data.clear()

        elif waiting_for == "lat1":
            context.user_data["lat1"] = float(text)
            context.user_data["waiting_for"] = "lon1"
            await update.message.reply_text("لطفاً **طول جغرافیایی نقطه ۱** را وارد کنید:")
        elif waiting_for == "lon1":
            context.user_data["lon1"] = float(text)
            context.user_data["waiting_for"] = "lat2"
            await update.message.reply_text("لطفاً **عرض جغرافیایی نقطه ۲** را وارد کنید:")
        elif waiting_for == "lat2":
            context.user_data["lat2"] = float(text)
            context.user_data["waiting_for"] = "lon2"
            await update.message.reply_text("لطفاً **طول جغرافیایی نقطه ۲** را وارد کنید:")
        elif waiting_for == "lon2":
            distance, azimuth = calculate_distance_azimuth(context.user_data["lat1"], context.user_data["lon1"], context.user_data["lat2"], float(text))
            await update.message.reply_text(f"✅ فاصله: {distance:.2f} متر\n📏 آزیموت: {azimuth:.2f} درجه", reply_markup=create_continue_menu())
            context.user_data.clear()

        elif waiting_for == "degree":
            context.user_data["degree"] = float(text)
            context.user_data["waiting_for"] = "minute"
            await update.message.reply_text("لطفاً مقدار **دقیقه** را وارد کنید:")
        elif waiting_for == "minute":
            context.user_data["minute"] = float(text)
            context.user_data["waiting_for"] = "second"
            await update.message.reply_text("لطفاً مقدار **ثانیه** را وارد کنید:")
        elif waiting_for == "second":
            decimal = dms_to_decimal(context.user_data["degree"], context.user_data["minute"], float(text))
            await update.message.reply_text(f"✅ درجه اعشاری: {decimal:.6f}", reply_markup=create_continue_menu())
            context.user_data.clear()

        elif waiting_for == "polygon":
            if text.lower() == "محاسبه":
                if len(context.user_data["polygon_points"]) < 3:
                    await update.message.reply_text("❌ حداقل ۳ نقطه برای محاسبه مساحت لازم است.")
                else:
                    area = calculate_polygon_area(context.user_data["polygon_points"])
                    await update.message.reply_text(f"✅ مساحت چندضلعی: {area:.2f} متر مربع", reply_markup=create_continue_menu())
                    context.user_data.clear()
            else:
                lat, lon = map(float, text.split(","))
                context.user_data["polygon_points"].append((lat, lon))
                await update.message.reply_text(f"نقطه ({lat}, {lon}) اضافه شد. نقطه بعدی یا 'محاسبه':")

        elif waiting_for == "source_x":
            context.user_data["source_x"] = float(text)
            context.user_data["waiting_for"] = "source_y"
            await update.message.reply_text("لطفاً مقدار **Y** را وارد کنید:")
        elif waiting_for == "source_y":
            context.user_data["source_y"] = float(text)
            context.user_data["waiting_for"] = "source_proj"
            await update.message.reply_text("لطفاً سیستم مختصاتی مبدا (مثلا 'utm') را وارد کنید:")
        elif waiting_for == "source_proj":
            context.user_data["source_proj"] = text
            context.user_data["waiting_for"] = "target_proj"
            await update.message.reply_text("لطفاً سیستم مختصاتی مقصد (مثلا 'latlong') را وارد کنید:")
        elif waiting_for == "target_proj":
            x, y = coordinate_conversion(context.user_data["source_x"], context.user_data["source_y"], context.user_data["source_proj"], text)
            await update.message.reply_text(f"✅ مختصات تبدیل‌شده: X: {x:.2f}, Y: {y:.2f}", reply_markup=create_continue_menu())
            context.user_data.clear()

        elif waiting_for == "distance":
            context.user_data["distance"] = float(text)
            context.user_data["waiting_for"] = "lat1_geo"
            await update.message.reply_text("لطفاً **عرض جغرافیایی نقطه ۱** را وارد کنید (درجه):")
        elif waiting_for == "lat1_geo":
            context.user_data["lat1"] = float(text)
            context.user_data["waiting_for"] = "lon1_geo"
            await update.message.reply_text("لطفاً **طول جغرافیایی نقطه ۱** را وارد کنید (درجه):")
        elif waiting_for == "lon1_geo":
            context.user_data["lon1"] = float(text)
            context.user_data["waiting_for"] = "lat2_geo"
            await update.message.reply_text("لطفاً **عرض جغرافیایی نقطه ۲** را وارد کنید (درجه):")
        elif waiting_for == "lat2_geo":
            context.user_data["lat2"] = float(text)
            context.user_data["waiting_for"] = "lon2_geo"
            await update.message.reply_text("لطفاً **طول جغرافیایی نقطه ۲** را وارد کنید (درجه):")
        elif waiting_for == "lon2_geo":
            corrected_distance = geodetic_correction(
                context.user_data["distance"],
                context.user_data["lat1"],
                context.user_data["lon1"],
                context.user_data["lat2"],
                float(text)
            )
            await update.message.reply_text(f"✅ فاصله تصحیح‌شده: {corrected_distance:.2f} متر", reply_markup=create_continue_menu())
            context.user_data.clear()

        elif waiting_for == "height1":
            context.user_data["height1"] = float(text)
            context.user_data["waiting_for"] = "height2"
            await update.message.reply_text("لطفاً **ارتفاع نقطه ۲** را وارد کنید (متر):")
        elif waiting_for == "height2":
            context.user_data["height2"] = float(text)
            context.user_data["waiting_for"] = "distance_slope"
            await update.message.reply_text("لطفاً **فاصله افقی** بین دو نقطه را وارد کنید (متر):")
        elif waiting_for == "distance_slope":
            slope = calculate_slope(context.user_data["height1"], context.user_data["height2"], float(text))
            await update.message.reply_text(f"✅ شیب: {slope:.2f} درصد", reply_markup=create_continue_menu())
            context.user_data.clear()

        elif waiting_for == "lat_string":
            context.user_data["lat"] = float(text)
            context.user_data["waiting_for"] = "lon_string"
            await update.message.reply_text("لطفاً **طول جغرافیایی** را وارد کنید (درجه اعشاری):")
        elif waiting_for == "lon_string":
            lat_str, lon_str = coord_to_string(context.user_data["lat"], float(text))
            await update.message.reply_text(f"✅ مختصات:\n**Latitude:** {lat_str}\n**Longitude:** {lon_str}", reply_markup=create_continue_menu())
            context.user_data.clear()

        elif waiting_for == "radius":
            context.user_data["radius"] = float(text)
            context.user_data["waiting_for"] = "height_cone"
            await update.message.reply_text("لطفاً **ارتفاع مخروط** را وارد کنید (متر):")
        elif waiting_for == "height_cone":
            volume = calculate_cone_volume(context.user_data["radius"], float(text))
            await update.message.reply_text(f"✅ حجم مخروط: {volume:.2f} متر مکعب", reply_markup=create_continue_menu())
            context.user_data.clear()

        elif waiting_for == "x1_angle":
            context.user_data["x1"] = float(text)
            context.user_data["waiting_for"] = "y1_angle"
            await update.message.reply_text("لطفاً **Y نقطه ۱** را وارد کنید:")
        elif waiting_for == "y1_angle":
            context.user_data["y1"] = float(text)
            context.user_data["waiting_for"] = "x2_angle"
            await update.message.reply_text("لطفاً **X نقطه ۲** را وارد کنید:")
        elif waiting_for == "x2_angle":
            context.user_data["x2"] = float(text)
            context.user_data["waiting_for"] = "y2_angle"
            await update.message.reply_text("لطفاً **Y نقطه ۲** را وارد کنید:")
        elif waiting_for == "y2_angle":
            context.user_data["y2"] = float(text)
            context.user_data["waiting_for"] = "x3_angle"
            await update.message.reply_text("لطفاً **X نقطه ۳** را وارد کنید:")
        elif waiting_for == "x3_angle":
            context.user_data["x3"] = float(text)
            context.user_data["waiting_for"] = "y3_angle"
            await update.message.reply_text("لطفاً **Y نقطه ۳** را وارد کنید:")
        elif waiting_for == "y3_angle":
            angle = calculate_angle_three_points(
                (context.user_data["x1"], context.user_data["y1"]),
                (context.user_data["x2"], context.user_data["y2"]),
                (context.user_data["x3"], float(text))
            )
            await update.message.reply_text(f"✅ زاویه: {angle:.2f} درجه", reply_markup=create_continue_menu())
            context.user_data.clear()

        elif waiting_for == "x1_intersect":
            context.user_data["x1"] = float(text)
            context.user_data["waiting_for"] = "y1_intersect"
            await update.message.reply_text("لطفاً **Y نقطه ۱ خط اول** را وارد کنید:")
        elif waiting_for == "y1_intersect":
            context.user_data["y1"] = float(text)
            context.user_data["waiting_for"] = "az1_intersect"
            await update.message.reply_text("لطفاً **آزیموت خط اول** را وارد کنید (درجه):")
        elif waiting_for == "az1_intersect":
            context.user_data["az1"] = float(text)
            context.user_data["waiting_for"] = "x2_intersect"
            await update.message.reply_text("لطفاً **X نقطه ۱ خط دوم** را وارد کنید:")
        elif waiting_for == "x2_intersect":
            context.user_data["x2"] = float(text)
            context.user_data["waiting_for"] = "y2_intersect"
            await update.message.reply_text("لطفاً **Y نقطه ۱ خط دوم** را وارد کنید:")
        elif waiting_for == "y2_intersect":
            context.user_data["y2"] = float(text)
            context.user_data["waiting_for"] = "az2_intersect"
            await update.message.reply_text("لطفاً **آزیموت خط دوم** را وارد کنید (درجه):")
        elif waiting_for == "az2_intersect":
            x, y = calculate_intersection_point(
                (context.user_data["x1"], context.user_data["y1"]), context.user_data["az1"],
                (context.user_data["x2"], context.user_data["y2"]), float(text)
            )
            await update.message.reply_text(f"✅ نقطه تقاطع: X: {x:.2f}, Y: {y:.2f}", reply_markup=create_continue_menu())
            context.user_data.clear()

        elif waiting_for == "angle_input":
            if text.lower() == "محاسبه":
                if len(context.user_data["angles"]) < 3:
                    await update.message.reply_text("❌ حداقل ۳ زاویه برای تصحیح لازم است.")
                else:
                    corrected_angles = angle_closure_correction(context.user_data["angles"])
                    result = "✅ زوایا پس از تصحیح:\n" + "\n".join([f"{angle:.2f} درجه" for angle in corrected_angles])
                    await update.message.reply_text(result, reply_markup=create_continue_menu())
                    context.user_data.clear()
            else:
                context.user_data["angles"].append(float(text))
                await update.message.reply_text(f"زاویه {len(context.user_data['angles'])}: {text} اضافه شد. زاویه بعدی یا 'محاسبه':")

        elif waiting_for == "height_v":
            context.user_data["height"] = float(text)
            context.user_data["waiting_for"] = "angle_v"
            await update.message.reply_text("لطفاً **زاویه شیب** را وارد کنید (درجه):")
        elif waiting_for == "angle_v":
            distance = calculate_vertical_distance(context.user_data["height"], float(text))
            await update.message.reply_text(f"✅ فاصله عمودی: {distance:.2f} متر", reply_markup=create_continue_menu())
            context.user_data.clear()

        elif waiting_for == "lat_utm":
            context.user_data["lat"] = float(text)
            context.user_data["waiting_for"] = "lon_utm"
            await update.message.reply_text("لطفاً **طول جغرافیایی** را وارد کنید (درجه):")
        elif waiting_for == "lon_utm":
            context.user_data["lon"] = float(text)
            context.user_data["waiting_for"] = "zone_utm"
            await update.message.reply_text("لطفاً شماره **Zone UTM** را وارد کنید:")
        elif waiting_for == "zone_utm":
            easting, northing = local_utm_conversion(context.user_data["lat"], context.user_data["lon"], int(text))
            await update.message.reply_text(f"✅ مختصات UTM:\n**Easting:** {easting:.2f}\n**Northing:** {northing:.2f}", reply_markup=create_continue_menu())
            context.user_data.clear()

        elif waiting_for == "location" and text and text.lower() == "محاسبه":
            if len(context.user_data["land_points"]) < 3:
                await update.message.reply_text("❌ حداقل ۳ نقطه برای محاسبه مساحت لازم است.")
            else:
                area = calculate_polygon_area(context.user_data["land_points"])
                points_str = "\n".join([f"نقطه {i+1}: ({p[0]:.6f}, {p[1]:.6f})" for i, p in enumerate(context.user_data["land_points"])])
                
                # ترسیم نقشه با matplotlib
                plot_land_area(context.user_data["land_points"], "land_area.png")
                
                # ارسال تصویر به کاربر
                with open("land_area.png", "rb") as photo:
                    await update.message.reply_photo(photo=photo, caption=f"✅ مساحت زمین: {area:.2f} متر مربع\nنقاط زمین:\n{points_str}")
                
                # پاک کردن فایل موقت
                os.remove("land_area.png")
                
                await update.message.reply_text("محاسبه انجام شد.", reply_markup=create_continue_menu())
                context.user_data.clear()

    except ValueError:
        await update.message.reply_text("❌ مقدار عددی معتبر وارد کنید.")
    except Exception as e:
        logger.error(f"خطا در پردازش ورودی: {str(e)}")
        await update.message.reply_text(f"❌ خطا: {str(e)}")

# --- مدیریت لوکیشن ---
async def handle_location(update: Update, context: CallbackContext):
    waiting_for = context.user_data.get("waiting_for")
    
    if waiting_for == "location" and update.message.location:
        latitude = update.message.location.latitude
        longitude = update.message.location.longitude
        context.user_data["land_points"].append((latitude, longitude))
        await update.message.reply_text(
            f"نقطه {len(context.user_data['land_points'])}: ({latitude:.6f}, {longitude:.6f}) اضافه شد.\n"
            "لوکیشن بعدی رو بفرستید یا 'محاسبه' رو بنویسید."
        )

# --- توابع محاسباتی ---
def utm_to_latlon(easting, northing, zone, northern_hemisphere=True):
    proj_utm = Proj(proj="utm", zone=zone, ellps="WGS84", south=not northern_hemisphere)
    proj_latlon = Proj(proj="latlong", datum="WGS84")
    transformer = Transformer.from_proj(proj_utm, proj_latlon)
    lon, lat = transformer.transform(easting, northing)
    return lat, lon

def calculate_distance_azimuth(lat1, lon1, lat2, lon2):
    geod = Geod(ellps="WGS84")
    azimuth, _, distance = geod.inv(lon1, lat1, lon2, lat2)
    return distance, azimuth

def dms_to_decimal(degree, minute, second):
    return degree + (minute / 60) + (second / 3600)

def calculate_polygon_area(points):
    geod = Geod(ellps="WGS84")
    area, _ = geod.polygon_area_perimeter([p[1] for p in points], [p[0] for p in points])
    return abs(area)

def coordinate_conversion(x, y, source_proj, target_proj):
    source = Proj(proj=source_proj, ellps="WGS84")
    target = Proj(proj=target_proj, ellps="WGS84")
    transformer = Transformer.from_proj(source, target)
    new_x, new_y = transformer.transform(x, y)
    return new_x, new_y

def geodetic_correction(distance, lat1=0, lon1=0, lat2=None, lon2=None, ellipsoid="WGS84", elevation=0):
    geod = Geod(ellps=ellipsoid)
    if lat2 is None or lon2 is None:
        lat1, lon1 = 0, 0
        lon2, lat2, _ = geod.fwd(lon1, lat1, 0, distance)
    azimuth1, azimuth2, geodetic_distance = geod.inv(lon1, lat1, lon2, lat2)
    R = 6378137
    correction_factor = 1 + (elevation / R)
    corrected_distance = geodetic_distance * correction_factor
    return corrected_distance

def calculate_slope(height1, height2, distance):
    delta_h = height2 - height1
    slope = (delta_h / distance) * 100
    return slope

def coord_to_string(lat, lon):
    lat_dir = "N" if lat >= 0 else "S"
    lon_dir = "E" if lon >= 0 else "W"
    lat = abs(lat)
    lon = abs(lon)
    lat_deg = int(lat)
    lat_min = int((lat - lat_deg) * 60)
    lat_sec = (lat - lat_deg - lat_min / 60) * 3600
    lon_deg = int(lon)
    lon_min = int((lon - lon_deg) * 60)
    lon_sec = (lon - lon_deg - lon_min / 60) * 3600
    lat_str = f"{lat_dir} {lat_deg}° {lat_min}' {lat_sec:.1f}\""
    lon_str = f"{lon_dir} {lon_deg}° {lon_min}' {lon_sec:.1f}\""
    return lat_str, lon_str

def calculate_cone_volume(radius, height):
    volume = (1/3) * math.pi * radius**2 * height
    return volume

def calculate_angle_three_points(p1, p2, p3):
    a = math.sqrt((p2[0] - p3[0])**2 + (p2[1] - p3[1])**2)
    b = math.sqrt((p1[0] - p3[0])**2 + (p1[1] - p3[1])**2)
    c = math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
    angle_rad = math.acos((a**2 + b**2 - c**2) / (2 * a * b))
    angle_deg = math.degrees(angle_rad)
    return angle_deg

def calculate_intersection_point(p1, az1, p2, az2):
    x1, y1 = p1
    x2, y2 = p2
    az1_rad = math.radians(az1)
    az2_rad = math.radians(az2)
    dx = x2 - x1
    dy = y2 - y1
    tan1 = math.tan(az1_rad)
    tan2 = math.tan(az2_rad)
    if abs(tan1 - tan2) < 1e-10:
        raise ValueError("خطوط موازی هستند و تقاطعی ندارند.")
    t = (dy - dx * tan2) / (tan1 - tan2)
    x = x1 + t
    y = y1 + t * tan1
    return x, y

def angle_closure_correction(angles):
    n = len(angles)
    expected_sum = (n - 2) * 180
    actual_sum = sum(angles)
    error = expected_sum - actual_sum
    correction_per_angle = error / n
    corrected_angles = [angle + correction_per_angle for angle in angles]
    return corrected_angles

def calculate_vertical_distance(height, angle):
    angle_rad = math.radians(angle)
    vertical_distance = height / math.tan(angle_rad)
    return vertical_distance

def local_utm_conversion(lat, lon, zone):
    proj_utm = Proj(proj="utm", zone=zone, ellps="WGS84")
    proj_latlon = Proj(proj="latlong", datum="WGS84")
    transformer = Transformer.from_proj(proj_latlon, proj_utm)
    easting, northing = transformer.transform(lon, lat)
    return easting, northing

def plot_land_area(points, output_file="land_area.png"):
    """ترسیم چندضلعی زمین با matplotlib"""
    lats = [p[0] for p in points]
    lons = [p[1] for p in points]
    
    # بستن چندضلعی با اضافه کردن نقطه اول به آخر
    lats.append(lats[0])
    lons.append(lons[0])
    
    plt.figure(figsize=(8, 6))
    plt.plot(lons, lats, 'b-', linewidth=2)  # خطوط آبی
    plt.fill(lons, lats, 'b', alpha=0.3)  # پرشدگی با شفافیت
    plt.title("نقشه زمین")
    plt.xlabel("طول جغرافیایی (درجه)")
    plt.ylabel("عرض جغرافیایی (درجه)")
    plt.grid(True)
    plt.savefig(output_file, dpi=100, bbox_inches='tight')
    plt.close()

# --- اجرای ربات ---
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(menu_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.LOCATION, handle_location))
    app.add_error_handler(error_handler)

    logger.info("ربات شروع شد.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()