import asyncio
import random
import logging
import os
import sys
from typing import Dict, List, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Game data storage (in-memory)
games: Dict[int, dict] = {}

# Character library (unchanged)
CHARACTERS = {
    "أنمي": [
        {"name": "ناروتو أوزوماكي", "desc": "نينجا شاب يحلم بأن يصبح هوكاجي قريته", "link": "https://www.google.com/search?q=ناروتو+أوزوماكي"},
        {"name": "لوفي", "desc": "قرصان مطاطي يبحث عن الكنز الأسطوري ون بيس", "link": "https://www.google.com/search?q=مونكي+دي+لوفي"},
        {"name": "غوكو", "desc": "محارب سايان قوي يحمي الأرض من الأعداء", "link": "https://www.google.com/search?q=سون+غوكو"},
        {"name": "إيتشيغو كوروساكي", "desc": "طالب ثانوي يحارب الأرواح الشريرة", "link": "https://www.google.com/search?q=إيتشيغو+كوروساكي"},
        {"name": "إدوارد إلريك", "desc": "خيميائي شاب يبحث عن حجر الفيلسوف", "link": "https://www.google.com/search?q=إدوارد+إلريك"},
        {"name": "ليفاي أكرمان", "desc": "جندي ماهر في قتال العمالقة", "link": "https://www.google.com/search?q=ليفاي+أكرمان"},
        {"name": "تانجيرو كامادو", "desc": "قاتل شياطين يحمي أخته المتحولة", "link": "https://www.google.com/search?q=تانجيرو+كامادو"},
        {"name": "ديكو", "desc": "طالب في أكاديمية الأبطال الخارقين", "link": "https://www.google.com/search?q=إيزوكو+ميدوريا"},
        {"name": "ساسكي أوتشيها", "desc": "نينجا من عشيرة أوتشيها الشهيرة", "link": "https://www.google.com/search?q=ساسكي+أوتشيها"},
        {"name": "كيليوا زولديك", "desc": "قاتل محترف صغير السن بقدرات كهربائية", "link": "https://www.google.com/search?q=كيليوا+زولديك"},
        {"name": "سينكو", "desc": "طفلة بقوى تدميرية هائلة", "link": "https://www.google.com/search?q=سينكو+إلفن+ليد"},
        {"name": "يوسوكي أورامشي", "desc": "محقق روحي يحمي عالم البشر", "link": "https://www.google.com/search?q=يوسوكي+أورامشي"},
        {"name": "إنوياشا", "desc": "نصف شيطان يبحث عن شظايا الجوهرة المقدسة", "link": "https://www.google.com/search?q=إنوياشا"},
        {"name": "فيجيتا", "desc": "أمير السايان المتكبر والقوي", "link": "https://www.google.com/search?q=فيجيتا"},
        {"name": "كاكاشي هاتاكي", "desc": "نينجا نسخ ومعلم الفريق السابع", "link": "https://www.google.com/search?q=كاكاشي+هاتاكي"},
        {"name": "زورو", "desc": "مبارز بثلاثة سيوف في طاقم القبعة القش", "link": "https://www.google.com/search?q=رورونوا+زورو"},
        {"name": "سانجي", "desc": "طباخ وقاتل أنيق في طاقم القراصنة", "link": "https://www.google.com/search?q=فينسموك+سانجي"},
        {"name": "جيرايا", "desc": "حكيم الضفادع ومعلم ناروتو", "link": "https://www.google.com/search?q=جيرايا+ناروتو"},
        {"name": "غون فريكس", "desc": "صياد مبتدئ يبحث عن والده", "link": "https://www.google.com/search?q=غون+فريكس"},
        {"name": "نيزوكو كامادو", "desc": "فتاة تحولت إلى شيطان لكنها تحافظ على إنسانيتها", "link": "https://www.google.com/search?q=نيزوكو+كامادو"}
    ],
    "أفلام": [
        {"name": "جيمس بوند", "desc": "جاسوس بريطاني سري برقم 007", "link": "https://www.google.com/search?q=جيمس+بوند"},
        {"name": "توني ستارك", "desc": "مليونير عبقري يرتدي درع الحديد", "link": "https://www.google.com/search?q=توني+ستارك+آيرون+مان"},
        {"name": "باتمان", "desc": "فارس الظلام حامي مدينة جوثام", "link": "https://www.google.com/search?q=باتمان"},
        {"name": "سوبرمان", "desc": "البطل الخارق من كوكب كريبتون", "link": "https://www.google.com/search?q=سوبرمان"},
        {"name": "هاري بوتر", "desc": "ساحر شاب يدرس في مدرسة هوجوورتس", "link": "https://www.google.com/search?q=هاري+بوتر"},
        {"name": "لوك سكايووكر", "desc": "فارس جيداي يحارب الإمبراطورية", "link": "https://www.google.com/search?q=لوك+سكايووكر"},
        {"name": "دارث فيدر", "desc": "سيد الظلام السابق أناكين سكايووكر", "link": "https://www.google.com/search?q=دارث+فيدر"},
        {"name": "الجوكر", "desc": "عدو باتمان المجنون والفوضوي", "link": "https://www.google.com/search?q=الجوكر"},
        {"name": "ثور", "desc": "إله الرعد الأسجاردي", "link": "https://www.google.com/search?q=ثور+مارفل"},
        {"name": "إندي جونز", "desc": "عالم آثار مغامر يبحث عن الكنوز", "link": "https://www.google.com/search?q=إنديانا+جونز"},
        {"name": "رامبو", "desc": "جندي سابق في القوات الخاصة", "link": "https://www.google.com/search?q=رامبو"},
        {"name": "تيرمينيتور", "desc": "روبوت قاتل من المستقبل", "link": "https://www.google.com/search?q=تيرمينيتور"},
        {"name": "ريد", "desc": "محتال سجين في شاوشانك", "link": "https://www.google.com/search?q=إليس+ريد+شاوشانك"},
        {"name": "فيتو كورليوني", "desc": "عراب عائلة الجريمة الإيطالية", "link": "https://www.google.com/search?q=فيتو+كورليوني"},
        {"name": "فوريست جامب", "desc": "رجل بسيط عاش أحداثاً تاريخية مهمة", "link": "https://www.google.com/search?q=فوريست+جامب"},
        {"name": "إلين ريبلي", "desc": "ضابطة تحارب المخلوقات الفضائية", "link": "https://www.google.com/search?q=إلين+ريبلي"},
        {"name": "نيو", "desc": "المختار في عالم المصفوفة الرقمي", "link": "https://www.google.com/search?q=نيو+ماتريكس"},
        {"name": "هانيبال ليكتر", "desc": "طبيب نفسي مجرم وآكل لحوم بشر", "link": "https://www.google.com/search?q=هانيبال+ليكتر"},
        {"name": "روكي بالبوا", "desc": "ملاكم من الطبقة العاملة يحقق المجد", "link": "https://www.google.com/search?q=روكي+بالبوا"},
        {"name": "الأسد الملك سيمبا", "desc": "أسد صغير يستعيد عرش والده", "link": "https://www.google.com/search?q=سيمبا+الأسد+الملك"}
    ],
    "كرة القدم": [
        {"name": "ليونيل ميسي", "desc": "نجم الأرجنتين وبرشلونة السابق", "link": "https://www.google.com/search?q=ليونيل+ميسي"},
        {"name": "كريستيانو رونالدو", "desc": "نجم البرتغال ومان يونايتد السابق", "link": "https://www.google.com/search?q=كريستيانو+رونالدو"},
        {"name": "بيليه", "desc": "أسطورة كرة القدم البرازيلية", "link": "https://www.google.com/search?q=بيليه"},
        {"name": "دييغو مارادونا", "desc": "أسطورة الأرجنتين وهدف القرن", "link": "https://www.google.com/search?q=مارادونا"},
        {"name": "زين الدين زيدان", "desc": "نجم فرنسا ومدرب ريال مدريد السابق", "link": "https://www.google.com/search?q=زين+الدين+زيدان"},
        {"name": "رونالدينيو", "desc": "ساحر الكرة البرازيلي", "link": "https://www.google.com/search?q=رونالدينيو"},
        {"name": "روبرتو كارلوس", "desc": "ظهير أيسر برازيلي بركلات حرة قوية", "link": "https://www.google.com/search?q=روبرتو+كارلوس"},
        {"name": "فرانك ريبيري", "desc": "جناح فرنسي سريع وماهر", "link": "https://www.google.com/search?q=فرانك+ريبيري"},
        {"name": "كيليان مبابي", "desc": "نجم فرنسا الشاب السريع", "link": "https://www.google.com/search?q=كيليان+مبابي"},
        {"name": "نيمار جونيور", "desc": "نجم البرازيل المهاري", "link": "https://www.google.com/search?q=نيمار"},
        {"name": "محمد صلاح", "desc": "فرعون مصر ونجم ليفربول", "link": "https://www.google.com/search?q=محمد+صلاح"},
        {"name": "سيرجيو راموس", "desc": "قائد إسبانيا ومدافع ريال مدريد السابق", "link": "https://www.google.com/search?q=سيرجيو+راموس"},
        {"name": "لوكا مودريتش", "desc": "صانع ألعاب كرواتي ماهر", "link": "https://www.google.com/search?q=لوكا+مودريتش"},
        {"name": "إرلينغ هالاند", "desc": "مهاجم نرويجي قاتل للأهداف", "link": "https://www.google.com/search?q=إرلينغ+هالاند"},
        {"name": "كيفين دي بروين", "desc": "صانع ألعاب بلجيكي متميز", "link": "https://www.google.com/search?q=كيفين+دي+بروين"},
        {"name": "فيرجيل فان دايك", "desc": "مدافع هولندي قوي وقائد", "link": "https://www.google.com/search?q=فيرجيل+فان+دايك"},
        {"name": "لويس سواريز", "desc": "مهاجم أوروجوايي حاد", "link": "https://www.google.com/search?q=لويس+سواريز"},
        {"name": "جاريث بيل", "desc": "جناح ويلزي سريع وقوي", "link": "https://www.google.com/search?q=جاريث+بيل"},
        {"name": "ساديو ماني", "desc": "جناح سنغالي سريع ومؤثر", "link": "https://www.google.com/search?q=ساديو+ماني"},
        {"name": "أنطوان جريزمان", "desc": "مهاجم فرنسي ذكي ومتنوع", "link": "https://www.google.com/search?q=أنطوان+جريزمان"}
    ],
    "شخصيات تاريخية": [
        {"name": "نابليون بونابرت", "desc": "إمبراطور فرنسا والقائد العسكري العظيم", "link": "https://www.google.com/search?q=نابليون+بونابرت"},
        {"name": "يوليوس قيصر", "desc": "دكتاتور روماني وقائد عسكري", "link": "https://www.google.com/search?q=يوليوس+قيصر"},
        {"name": "الإسكندر الأكبر", "desc": "الملك المقدوني الذي غزا العالم القديم", "link": "https://www.google.com/search?q=الإسكندر+الأكبر"},
        {"name": "صلاح الدين الأيوبي", "desc": "القائد المسلم محرر القدس", "link": "https://www.google.com/search?q=صلاح+الدين+الأيوبي"},
        {"name": "كليوباترا", "desc": "ملكة مصر الأسطورية", "link": "https://www.google.com/search?q=كليوباترا"},
        {"name": "أدولف هتلر", "desc": "ديكتاتور ألمانيا النازية", "link": "https://www.google.com/search?q=أدولف+هتلر"},
        {"name": "ونستون تشرشل", "desc": "رئيس وزراء بريطانيا في الحرب العالمية الثانية", "link": "https://www.google.com/search?q=ونستون+تشرشل"},
        {"name": "غاندي", "desc": "زعيم الاستقلال الهندي واللاعنف", "link": "https://www.google.com/search?q=المهاتما+غاندي"},
        {"name": "نيلسون مانديلا", "desc": "رئيس جنوب أفريقيا ومحارب الفصل العنصري", "link": "https://www.google.com/search?q=نيلسون+مانديلا"},
        {"name": "مارتن لوثر كينغ", "desc": "زعيم الحقوق المدنية الأمريكي", "link": "https://www.google.com/search?q=مارتن+لوثر+كينغ"},
        {"name": "أبراهام لينكولن", "desc": "الرئيس الأمريكي الذي ألغى العبودية", "link": "https://www.google.com/search?q=أبراهام+لينكولن"},
        {"name": "جورج واشنطن", "desc": "أول رئيس للولايات المتحدة الأمريكية", "link": "https://www.google.com/search?q=جورج+واشنطن"},
        {"name": "لينين", "desc": "زعيم الثورة البلشفية الروسية", "link": "https://www.google.com/search?q=فلاديمير+لينين"},
        {"name": "ستالين", "desc": "زعيم الاتحاد السوفيتي الديكتاتوري", "link": "https://www.google.com/search?q=جوزيف+ستالين"},
        {"name": "ماو تسي تونغ", "desc": "زعيم الصين الشيوعية", "link": "https://www.google.com/search?q=ماو+تسي+تونغ"},
        {"name": "تشي جيفارا", "desc": "الثوري الأرجنتيني في كوبا", "link": "https://www.google.com/search?q=تشي+جيفارا"},
        {"name": "حنبعل", "desc": "القائد القرطاجي الذي عبر الألب", "link": "https://www.google.com/search?q=حنبعل"},
        {"name": "أتيلا الهوني", "desc": "ملك الهون المدمر لأوروبا", "link": "https://www.google.com/search?q=أتيلا+الهوني"},
        {"name": "جنكيز خان", "desc": "إمبراطور المغول العظيم", "link": "https://www.google.com/search?q=جنكيز+خان"},
        {"name": "هارون الرشيد", "desc": "الخليفة العباسي في العصر الذهبي", "link": "https://www.google.com/search?q=هارون+الرشيد"}
    ],
    "ألعاب فيديو": [
        {"name": "ماريو", "desc": "السباك الإيطالي بطل ألعاب نينتندو", "link": "https://www.google.com/search?q=سوبر+ماريو"},
        {"name": "سونيك", "desc": "القنفذ الأزرق السريع من سيجا", "link": "https://www.google.com/search?q=سونيك+القنفذ"},
        {"name": "لينك", "desc": "البطل الصامت في أسطورة زيلدا", "link": "https://www.google.com/search?q=لينك+زيلدا"},
        {"name": "ماستر تشيف", "desc": "جندي فضائي في لعبة هيلو", "link": "https://www.google.com/search?q=ماستر+تشيف"},
        {"name": "كراتوس", "desc": "إله الحرب اليوناني الغاضب", "link": "https://www.google.com/search?q=كراتوس+إله+الحرب"},
        {"name": "جيرالت من ريفيا", "desc": "صائد الوحوش الأبيض الشعر", "link": "https://www.google.com/search?q=جيرالت+ويتشر"},
        {"name": "آرثر مورغان", "desc": "خارج عن القانون في الغرب الأمريكي", "link": "https://www.google.com/search?q=آرثر+مورغان"},
        {"name": "إيزيو أوديتوري", "desc": "القاتل الإيطالي في عصر النهضة", "link": "https://www.google.com/search?q=إيزيو+أوديتوري"},
        {"name": "ناثان دريك", "desc": "صائد الكنوز المغامر", "link": "https://www.google.com/search?q=ناثان+دريك"},
        {"name": "لارا كروفت", "desc": "عالمة آثار مغامرة", "link": "https://www.google.com/search?q=لارا+كروفت"},
        {"name": "سوليد سنيك", "desc": "جندي التسلل الأسطوري", "link": "https://www.google.com/search?q=سوليد+سنيك"},
        {"name": "دووم جاي", "desc": "مقاتل الشياطين في المريخ", "link": "https://www.google.com/search?q=دووم+سلاير"},
        {"name": "جوردن فريمان", "desc": "عالم الفيزياء المحارب", "link": "https://www.google.com/search?q=جوردن+فريمان"},
        {"name": "سام فيشر", "desc": "جاسوس الظل الماهر", "link": "https://www.google.com/search?q=سام+فيشر"},
        {"name": "أليكس ميرسر", "desc": "المصاب بالفيروس الجيني", "link": "https://www.google.com/search?q=أليكس+ميرسر"},
        {"name": "كلود سترايف", "desc": "المرتزق حامل السيف الضخم", "link": "https://www.google.com/search?q=كلود+سترايف"},
        {"name": "ديفيد ماسون", "desc": "جندي من المستقبل القريب", "link": "https://www.google.com/search?q=ديفيد+ماسون"},
        {"name": "ألتائير", "desc": "القاتل في الحروب الصليبية", "link": "https://www.google.com/search?q=ألتائير"},
        {"name": "جوني كيج", "desc": "نجم أكشن في بطولة القتال الدموي", "link": "https://www.google.com/search?q=جوني+كيج"},
        {"name": "سوب زيرو", "desc": "محارب الجليد الأزرق", "link": "https://www.google.com/search?q=سوب+زيرو"}
    ]
}

class GameBot:
    def __init__(self):
        self.application = None

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        chat_id = update.effective_chat.id

        if update.effective_chat.type not in ['group', 'supergroup']:
            await update.message.reply_text("هذه اللعبة تعمل فقط في المجموعات!")
            return

        if chat_id in games:
            await update.message.reply_text("يوجد لعبة نشطة بالفعل في هذه المجموعة! استخدم /cancel لإنهائها أو /score لمعرفة حالة اللعبة.")
            return

        games[chat_id] = {
            'status': 'waiting_players', 'players': [], 'current_turn': 0, 'round': 1,
            'max_rounds': 3, 'scores': {}, 'characters': {}, 'waiting_for_answer': False,
            'question_asker': None, 'answerer_id': None,
            'pending_guess_confirmation': None # New state for guess confirmation
        }

        keyboard = [[InlineKeyboardButton("🎮 انضمام للعبة", callback_data="join_game")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "🎯 **لعبة تخمين الشخصيات**\n\n"
            "قواعد اللعبة:\n"
            "• يحتاج لاعبان للبدء\n"
            "• كل لاعب يحصل على شخصية عشوائية\n"
            "• اللاعبون يتناوبون طرح أسئلة نعم/لا\n"
            "• الهدف تخمين شخصية الخصم\n"
            f"• اللعبة ستستمر لـ {games[chat_id]['max_rounds']} جولات.\n\n"
            "اضغط على الزر للانضمام!",
            reply_markup=reply_markup, parse_mode='Markdown'
        )

    async def cancel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Allows a user to cancel the current game in their group."""
        chat_id = update.effective_chat.id
        if chat_id in games:
            del games[chat_id]
            await update.message.reply_text("تم إلغاء اللعبة بنجاح! يمكنك بدء لعبة جديدة باستخدام /start.")
        else:
            await update.message.reply_text("لا توجد لعبة نشطة لإلغائها في هذه المجموعة.")

    async def rules_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Displays the game rules."""
        chat_id = update.effective_chat.id
        max_rounds_text = "3" # Default value if no game is active
        if chat_id in games:
            max_rounds_text = str(games[chat_id]['max_rounds'])

        await update.message.reply_text(
            "📜 **قواعد لعبة تخمين الشخصيات:**\n\n"
            "• اللعبة تتطلب لاعبين اثنين.\n"
            "• عند الانضمام، يتلقى كل لاعب شخصية سرية (أنمي، فيلم، كرة قدم، أو تاريخية).\n"
            "• يتناوب اللاعبون على طرح أسئلة إجابتها 'نعم' أو 'لا' لتضييق نطاق الاحتمالات حول شخصية الخصم.\n"
            "• يمكن للاعب محاولة تخمين شخصية الخصم في دوره بكتابة اسم الشخصية مباشرة. إذا كان التخمين صحيحاً، سيطلب من الخصم تأكيد ذلك.\n"
            "• التخمين الصحيح يمنح اللاعب نقطة وينهي الجولة.\n"
            f"• اللعبة تستمر لـ {max_rounds_text} جولات. في نهاية كل جولة، يحصل اللاعبون على شخصيات جديدة.\n"
            "• الفائز هو من يحصل على أكبر عدد من النقاط في نهاية الجولات.\n"
            "• في حالة تعادل النقاط، تعتبر اللعبة تعادلاً.\n\n"
            "استخدم /start لبدء لعبة جديدة."
            , parse_mode='Markdown'
        )

    async def score_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Displays the current scores of the active game."""
        chat_id = update.effective_chat.id
        if chat_id not in games or games[chat_id]['status'] == 'waiting_players':
            await update.message.reply_text("لا توجد لعبة نشطة لعرض نقاطها حاليًا. استخدم /start لبدء واحدة.")
            return

        game = games[chat_id]
        if not game['players']:
            await update.message.reply_text("لا يوجد لاعبون في اللعبة لعرض نقاطهم بعد.")
            return

        scores_text = "📊 **النقاط الحالية:**\n"
        for player in game['players']:
            player_id = player['id']
            player_name = player['name']
            score = game['scores'].get(player_id, 0) # Get score, default to 0 if not found
            scores_text += f"• {player_name}: {score} نقاط\n"
        
        current_round = game.get('round', 0)
        max_rounds = game.get('max_rounds', 0)
        if max_rounds > 0:
            scores_text += f"\nالجولة {current_round} من {max_rounds}"

        await update.message.reply_text(scores_text, parse_mode='Markdown')

    async def forfeit_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Allows a player to forfeit the game."""
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name

        if chat_id not in games or games[chat_id]['status'] != 'playing':
            await update.message.reply_text("لا توجد لعبة نشطة لتتراجع عنها.")
            return
        
        game = games[chat_id]
        player_ids = [p['id'] for p in game['players']]

        if user_id not in player_ids:
            await update.message.reply_text("أنت لست جزءًا من هذه اللعبة.")
            return
        
        # Identify the other player
        other_player = next((p for p in game['players'] if p['id'] != user_id), None)

        if not other_player: # Should not happen in a 2-player game
            await update.message.reply_text("حدث خطأ في تحديد اللاعب الآخر. لا يمكن التراجع.")
            return

        # Announce forfeiture and declare winner
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"🏳️ **تراجع!**\n\nاللاعب **{user_name}** استسلم!\n"
                 f"**{other_player['name']}** يفوز بالجولة تلقائياً ويحصل على نقطة!",
            parse_mode='Markdown'
        )
        
        # Award a point to the winner
        game['scores'][other_player['id']] += 1

        # Proceed to next round or end game
        await self.next_round_or_end_game(chat_id, context)

    async def approve_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Allows the player whose character was guessed to approve a correct guess."""
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name

        if chat_id not in games or games[chat_id]['status'] != 'playing':
            await update.message.reply_text("لا توجد لعبة نشطة لتأكيد تخمين فيها.")
            return
        
        game = games[chat_id]
        player_ids = [p['id'] for p in game['players']]

        if user_id not in player_ids:
            await update.message.reply_text("أنت لست جزءًا من هذه اللعبة.")
            return

        # The user calling /approve is the one whose character was guessed.
        # So, the other player must be the one who made the (correct) guess.
        guesser_player = next((p for p in game['players'] if p['id'] != user_id), None)

        if not guesser_player:
            await update.message.reply_text("حدث خطأ: لا يمكن تحديد اللاعب الذي خمّن. يرجى التأكد من أن اللعبة مستمرة بشكل صحيح.")
            return
        
        # Ensure that the person approving is actually the one whose character *would be* guessed
        # and that the other player is the guesser.
        # This is an implicit approval for the "other player" who just made a guess.
        
        guessed_character_info = game['characters'][user_id]
        
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"✅ **{user_name} يؤكد أن التخمين كان صحيحاً!**\n"
                 f"الشخصية التي خمنها {guesser_player['name']} كانت:\n"
                 f"**{guessed_character_info['name']}**\n"
                 f"من فئة: {guessed_character_info['category']}\n"
                 f"🔗 [معلومات إضافية]({guessed_character_info['link']})\n\n"
                 f"**{guesser_player['name']}** يحصل على نقطة!",
            parse_mode='Markdown', disable_web_page_preview=True
        )

        game['scores'][guesser_player['id']] += 1
        
        # Reset any pending guess confirmation if it existed, as this command overrides it
        game['pending_guess_confirmation'] = None 
        game['waiting_for_answer'] = False # Ensure no pending questions

        await self.next_round_or_end_game(chat_id, context)


    async def join_game_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        chat_id = query.message.chat_id
        user_id = query.from_user.id
        username = query.from_user.first_name

        if chat_id not in games:
            await query.edit_message_text("لا توجد لعبة نشطة! استخدم /start لبدء واحدة.")
            return
        game = games[chat_id]
        if game['status'] != 'waiting_players':
            await query.answer("اللعبة بدأت بالفعل!", show_alert=True)
            return
        if user_id in [p['id'] for p in game['players']]:
            await query.answer("أنت مشترك بالفعل في اللعبة!", show_alert=True)
            return
        if len(game['players']) >= 2:
            await query.answer("اللعبة ممتلئة!", show_alert=True)
            return
        
        game['players'].append({'id': user_id, 'name': username})
        game['scores'][user_id] = 0

        # Build the message text dynamically based on current players
        players_joined_names = [p['name'] for p in game['players']]
        
        if len(game['players']) == 1:
            # Keep the join button while waiting for the second player
            keyboard = [[InlineKeyboardButton("🎮 انضمام للعبة", callback_data="join_game")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"✅ **{username} انضم للعبة!**\n\n"
                f"اللاعبون المنضمون: {', '.join(players_joined_names)}\n"
                "في انتظار لاعب آخر...",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        elif len(game['players']) == 2:
            # Once two players join, remove the join button and start the game
            await query.edit_message_text(
                f"✅ **{username} انضم للعبة!**\n\n"
                f"اللاعبون المنضمون: {', '.join(players_joined_names)}\n"
                "جميع اللاعبين انضموا! اللعبة ستبدأ الآن...",
                parse_mode='Markdown'
            )
            await self.start_game(chat_id, context)

    async def start_game(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE):
        game = games[chat_id]
        game['status'] = 'playing'
        for player in game['players']:
            category = random.choice(list(CHARACTERS.keys()))
            character = random.choice(CHARACTERS[category])
            game['characters'][player['id']] = {
                'category': category, 'character': character, 'name': character['name'],
                'desc': character['desc'], 'link': character['link']
            }
            try:
                await context.bot.send_message(
                    chat_id=player['id'],
                    text=f"🎭 **شخصيتك في اللعبة:**\n\n**الاسم:** {character['name']}\n"
                         f"**الفئة:** {category}\n**الوصف:** {character['desc']}\n\n"
                         f"🔗 [معلومات إضافية]({character['link']})\n\n⚠️ احتفظ بهذه المعلومات سرية!",
                    parse_mode='Markdown', disable_web_page_preview=True
                )
            except Exception as e:
                logger.error(f"Failed to send private message to {player['id']}: {e}")
                await context.bot.send_message(
                    chat_id,
                    f"⚠️ لم أتمكن من إرسال رسالة خاصة إلى {player['name']}. "
                    "الرجاء التأكد من أنك بدأت محادثة معي أولاً! سيتم إلغاء اللعبة."
                )
                del games[chat_id]
                return
        players_text = " و ".join([p['name'] for p in game['players']]) # Corrected: 'انضم' to 'join'
        await context.bot.send_message(chat_id, f"🚀 اللعبة بدأت بين {players_text}!")
        await asyncio.sleep(2)
        await self.start_round(chat_id, context)

    async def start_round(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE):
        game = games[chat_id]
        current_player = game['players'][game['current_turn']]
        other_player = game['players'][1 - game['current_turn']]
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"🏁 **الجولة {game['round']}**\n\n"
                 f"دور {current_player['name']} لطرح سؤال!\n"
                 f"يجب على {other_player['name']} الإجابة بنعم أو لا.\n\n"
                 f"💡 يمكنك أيضاً تخمين الشخصية مباشرة بكتابة اسمها!",
            parse_mode='Markdown'
        )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        message_text = update.message.text
        if chat_id not in games: return
        game = games[chat_id]
        if game['status'] != 'playing': return
        player_ids = [p['id'] for p in game['players']]
        if user_id not in player_ids: return
        current_player = game['players'][game['current_turn']]
        other_player = game['players'][1 - game['current_turn']]
        
        # Prevent actions if a guess confirmation is pending
        if game.get('pending_guess_confirmation'):
            if user_id == game['pending_guess_confirmation']['guessed_id']:
                await update.message.reply_text("يرجى استخدام الأزرار في رسالتي الخاصة لتأكيد أو نفي التخمين.")
            elif user_id == game['pending_guess_confirmation']['guesser_id']:
                await update.message.reply_text(f"في انتظار تأكيد التخمين من {next(p['name'] for p in game['players'] if p['id'] == game['pending_guess_confirmation']['guessed_id'])}.")
            else:
                await update.message.reply_text("هناك تخمين معلق في انتظار التأكيد. يرجى الانتظار.")
            return

        # This part handles direct text answers "نعم" or "لا" from the answerer
        if game.get('waiting_for_answer') and user_id == game.get('answerer_id'):
            lower_text = message_text.lower().strip()
            if lower_text in ['نعم', 'yes', 'y', 'نعم.', 'yes.']:
                await self.process_answer(chat_id, context, "answer_yes", update.message)
            elif lower_text in ['لا', 'no', 'n', 'لا.', 'no.']:
                await self.process_answer(chat_id, context, "answer_no", update.message)
            return

        if user_id != current_player['id']:
            await update.message.reply_text(f"انتظر دورك! دور {current_player['name']} الآن.")
            return
        if game.get('waiting_for_answer'):
            await update.message.reply_text("في انتظار إجابة على السؤال السابق!")
            return
        
        other_character_name = game['characters'][other_player['id']]['name']
        
        # --- Handle Guessing ---
        if message_text.strip() == other_character_name:
            # Correct guess, ask for confirmation
            game['pending_guess_confirmation'] = {
                'guesser_id': user_id,
                'guessed_id': other_player['id'],
                'chat_id': chat_id # Store group chat_id for later messages
            }
            keyboard = [[
                InlineKeyboardButton("✅ نعم، هذا هو!", callback_data=f"confirm_guess_{user_id}_{other_player['id']}"),
                InlineKeyboardButton("❌ لا، ليس كذلك.", callback_data=f"deny_guess_{user_id}_{other_player['id']}")
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            try:
                # Send confirmation request to the guessed player's DM
                confirm_msg = await context.bot.send_message(
                    chat_id=other_player['id'],
                    text=f"🤔 **تخمين!**\n\nاللاعب {current_player['name']} في مجموعة **{update.effective_chat.title}** يعتقد أن شخصيتك هي:\n**{message_text.strip()}**\n\nهل هذا صحيح؟",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                game['pending_guess_confirmation']['message_id'] = confirm_msg.message_id
                await update.message.reply_text(
                    f"🕵️‍♂️ **{current_player['name']} خمّن شخصية!**\n\n"
                    f"أرسلت طلباً إلى {other_player['name']} لتأكيد التخمين. يرجى الانتظار...",
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Failed to send private guess confirmation to {other_player['id']}: {e}")
                await update.message.reply_text(
                    f"⚠️ لم أتمكن من إرسال طلب التأكيد إلى {other_player['name']}. "
                    "الرجاء التأكد من أن اللاعب قد بدأ محادثة معي أولاً. يرجى إعادة التخمين بعد حل المشكلة."
                )
                game['pending_guess_confirmation'] = None # Reset state
            return

        elif message_text.strip() != other_character_name and any(p['name'] == message_text.strip() for category in CHARACTERS.values() for p in category):
            # If it's a known character name, but not the correct guess
            await update.message.reply_text(f"تخمين خاطئ! {message_text.strip()} ليس الشخصية الصحيحة.")
            
            # Pass the turn to the other player immediately for incorrect guess
            game['current_turn'] = 1 - game['current_turn']
            await asyncio.sleep(1)
            next_asker = game['players'][game['current_turn']]
            next_answerer = game['players'][1 - game['current_turn']]
            await update.message.reply_text(
                f"🔄 دور {next_asker['name']} لطرح سؤال!\n"
                f"يجب على {next_answerer['name']} الإجابة."
                , parse_mode='Markdown'
            )
            return

        # --- Handle Question Asking (if not a guess) ---
        game['waiting_for_answer'] = True
        game['question_asker'] = user_id
        game['answerer_id'] = other_player['id']
        game['last_question_message_id'] = update.message.message_id # Store message_id for editing
        keyboard = [[InlineKeyboardButton("✅ نعم", callback_data="answer_yes"),
                     InlineKeyboardButton("❌ لا", callback_data="answer_no")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"❓ **السؤال:** {message_text}\n\n👤 {other_player['name']}, اختر إجابتك:",
            reply_markup=reply_markup, parse_mode='Markdown'
        )

    async def handle_answer_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = query.from_user.id
        answer = query.data

        # Determine the original group chat_id
        main_game_chat_id = None
        for g_chat_id, g_state in games.items():
            if g_state.get('answerer_id') == user_id and query.message.chat_id == g_chat_id:
                # If the callback is from the group chat where the question was asked
                main_game_chat_id = g_chat_id
                break
        
        if not main_game_chat_id:
             await query.answer("لا توجد لعبة نشطة أو هذا السؤال لا يخص لعبة حالية.", show_alert=True)
             return

        game = games[main_game_chat_id]
        
        if not game.get('waiting_for_answer') or game.get('answerer_id') != user_id:
            await query.answer("تمت الإجابة على هذا السؤال بالفعل أو ليس دورك للإجابة.", show_alert=True)
            return
        
        await query.answer() # Acknowledge the callback immediately

        # Call process_answer only if it's a valid, unanswered query
        await self.process_answer(main_game_chat_id, context, answer, query.message)

    async def process_answer(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE, answer: str, message_obj):
        game = games[chat_id]
        
        if not game['waiting_for_answer']:
            return

        answer_text = "نعم ✅" if answer == "answer_yes" else "لا ❌"
        
        original_question_prefix = "❓ **السؤال:** "
        message_lines = message_obj.text.split('\n')
        
        question = "السؤال غير متوفر"
        for line in message_lines:
            if line.startswith(original_question_prefix):
                question = line.replace(original_question_prefix, '').strip()
                break

        # Edit the message to show the answer and remove the buttons
        await context.bot.edit_message_text(
            chat_id=chat_id, message_id=message_obj.message_id,
            text=f"❓ **السؤال:** {question}\n\n💬 **الإجابة:** {answer_text}",
            parse_mode='Markdown'
        )
        
        game['waiting_for_answer'] = False
        game['current_turn'] = 1 - game['current_turn']
        game['question_asker'] = None
        game['answerer_id'] = None
        
        await asyncio.sleep(2)
        current_player = game['players'][game['current_turn']]
        other_player = game['players'][1 - game['current_turn']]
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"🔄 دور {current_player['name']} لطرح سؤال!\n"
                 f"يجب على {other_player['name']} الإجابة.",
            parse_mode='Markdown'
        )

    async def handle_guess_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id # This is the ID of the player whose character was guessed
        
        # Parse callback_data: confirm_guess_guesserid_guessedid or deny_guess_guesserid_guessedid
        parts = query.data.split('_')
        action = parts[0] # confirm or deny
        guesser_id = int(parts[2])
        guessed_id = int(parts[3])

        # Find the game where this confirmation is pending
        game_found = None
        main_game_chat_id = None
        for chat_id, game_state in games.items():
            if (game_state.get('pending_guess_confirmation') and
                game_state['pending_guess_confirmation']['guesser_id'] == guesser_id and
                game_state['pending_guess_confirmation']['guessed_id'] == guessed_id):
                game_found = game_state
                main_game_chat_id = chat_id
                break
        
        if not game_found:
            await query.edit_message_text("هذا التخمين لم يعد معلقاً أو انتهت اللعبة.")
            return

        if user_id != guessed_id:
            await query.edit_message_text("أنت لا تملك الصلاحية لتأكيد هذا التخمين أو نفيه.")
            return

        guesser_name = next(p for p in game_found['players'] if p['id'] == guesser_id)
        guessed_name = next(p for p in game_found['players'] if p['id'] == guessed_id)
        guessed_character_name = game_found['characters'][guessed_id]['name']
        
        # Edit the confirmation message in DM to remove buttons and show outcome
        if action == "confirm":
            await query.edit_message_text(f"✅ لقد أكدت أن {guesser_name} خمن شخصيتك بشكل صحيح: **{guessed_character_name}**.", parse_mode='Markdown')
            await context.bot.send_message(
                chat_id=main_game_chat_id,
                text=f"🎉 **{guesser_name} خمن شخصية {guessed_name} بشكل صحيح!**",
                parse_mode='Markdown'
            )
            game_found['pending_guess_confirmation'] = None # Clear pending state
            await self.handle_correct_guess(main_game_chat_id, guesser_id, context) # Award point, next round/end game
        else: # deny
            await query.edit_message_text(f"❌ لقد نفيت تخمين {guesser_name}. شخصيتك ليست **{guessed_character_name}**.", parse_mode='Markdown')
            await context.bot.send_message(
                chat_id=main_game_chat_id,
                text=f"🤷‍♂️ **{guesser_name} خمن شخصية {guessed_name} بشكل خاطئ!**",
                parse_mode='Markdown'
            )
            game_found['pending_guess_confirmation'] = None # Clear pending state
            
            # Pass the turn to the other player (the one who was just guessed)
            game_found['current_turn'] = 1 - game_found['current_turn']
            await asyncio.sleep(1)
            next_asker = game_found['players'][game_found['current_turn']]
            next_answerer = game_found['players'][1 - game_found['current_turn']]
            await context.bot.send_message(
                chat_id=main_game_chat_id,
                text=f"🔄 دور {next_asker['name']} لطرح سؤال!\n"
                    f"يجب على {next_answerer['name']} الإجابة.",
                parse_mode='Markdown'
            )


    async def handle_correct_guess(self, chat_id: int, guesser_id: int, context: ContextTypes.DEFAULT_TYPE):
        game = games[chat_id]
        guesser = next(p for p in game['players'] if p['id'] == guesser_id)
        other_player = next(p for p in game['players'] if p['id'] != guesser_id)
        character_info = game['characters'][other_player['id']]
        game['scores'][guesser_id] += 1
        
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"🎉 تخمين صحيح! {guesser['name']} يحصل على نقطة!\n\n"
                 f"الشخصية كانت: **{character_info['name']}**\n"
                 f"من فئة: {character_info['category']}\n"
                 f"🔗 [معلومات إضافية]({character_info['link']})",
            parse_mode='Markdown', disable_web_page_preview=True
        )
        await self.next_round_or_end_game(chat_id, context)
        
    async def next_round_or_end_game(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE):
        game = games[chat_id]
        
        # Display current scores after each round
        scores_text = "📊 **النقاط الحالية:**\n"
        for player in game['players']:
            player_id = player['id']
            player_name = player['name']
            score = game['scores'].get(player_id, 0)
            scores_text += f"• {player_name}: {score} نقاط\n"
        await context.bot.send_message(
            chat_id=chat_id,
            text=scores_text,
            parse_mode='Markdown'
        )
        await asyncio.sleep(2) # Give players time to read scores

        if game['round'] >= game['max_rounds']:
            await self.end_game(chat_id, context)
        else:
            game['round'] += 1
            game['current_turn'] = 0
            game['waiting_for_answer'] = False
            
            # Re-assign characters for the new round
            for player in game['players']:
                category = random.choice(list(CHARACTERS.keys()))
                character = random.choice(CHARACTERS[category])
                game['characters'][player['id']] = {
                    'category': category, 'character': character, 'name': character['name'],
                    'desc': character['desc'], 'link': character['link']
                }
                try:
                    await context.bot.send_message(
                        chat_id=player['id'],
                        text=f"🎭 **شخصيتك الجديدة - الجولة {game['round']}:**\n\n"
                             f"**الاسم:** {character['name']}\n**الفئة:** {category}\n"
                             f"**الوصف:** {character['desc']}\n\n"
                             f"🔗 [معلومات إضافية]({character['link']})",
                        parse_mode='Markdown', disable_web_page_preview=True
                    )
                except Exception as e:
                    logger.error(f"Failed to send private message: {e}")
                    await context.bot.send_message(
                        chat_id,
                        f"⚠️ تعذر إرسال الشخصية الجديدة لـ {player['name']}. "
                        "يرجى التأكد من أنك بدأت محادثة معي أولاً. سيتم إنهاء اللعبة."
                    )
                    del games[chat_id]
                    return # Stop game progression
            await context.bot.send_message(chat_id, f"⏳ يتم تجهيز الجولة {game['round']}...")
            await asyncio.sleep(3)
            await self.start_round(chat_id, context)

    async def end_game(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE):
        if chat_id not in games: return
        game = games[chat_id]
        scores = [(game['scores'][p['id']], p['name']) for p in game['players']]
        scores.sort(key=lambda x: x[0], reverse=True)

        result_text = "🏆 **نتائج اللعبة:**\n\n"
        if len(scores) < 2:
            result_text += "اللعبة انتهت بلا فائز واضح (عدد اللاعبين غير كافٍ).\n"
        elif scores[0][0] == scores[1][0]:
            result_text += "🤝 تعادل!\n\n"
        else:
            result_text += f"🥇 الفائز: {scores[0][1]} بنتيجة {scores[0][0]} نقطة!\n\n"
        
        result_text += "📊 **النقاط النهائية:**\n"
        for score, name in scores:
            result_text += f"• {name}: {score} نقاط\n"
        result_text += "\n🎮 شكراً لكم على اللعب! لبدء لعبة جديدة، اكتب /start"
        await context.bot.send_message(
            chat_id=chat_id, text=result_text, parse_mode='Markdown'
        )
        del games[chat_id]

    async def callback_query_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        data = query.data
        if data == "join_game":
            await self.join_game_callback(update, context)
        elif data in ["answer_yes", "answer_no"]:
            await self.handle_answer_callback(update, context)
        elif data.startswith("confirm_guess_") or data.startswith("deny_guess_"):
            await self.handle_guess_confirmation(update, context)

    def setup_handlers(self, application):
        """Setup all handlers"""
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("cancel", self.cancel_command))
        application.add_handler(CommandHandler("rules", self.rules_command))
        application.add_handler(CommandHandler("score", self.score_command))
        application.add_handler(CommandHandler("forfeit", self.forfeit_command))
        application.add_handler(CommandHandler("approve", self.approve_command)) # New approve command handler
        application.add_handler(CallbackQueryHandler(self.callback_query_handler))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

    def run_bot(self, token: str):
        """Run the bot."""
        self.application = Application.builder().token(token).build()
        self.setup_handlers(self.application)
        
        print("Bot is running...")
        self.application.run_polling()

if __name__ == "__main__":
    bot_token = os.getenv('BOT_TOKEN')
    
    if not bot_token:
        print("❌ Error: BOT_TOKEN not found!")
        print("Please create a .env file with your bot token:")
        print("BOT_TOKEN=your_bot_token_here")
        sys.exit(1)
    
    bot = GameBot()
    
    print("🤖 Starting Telegram Character Guessing Game Bot...")
    print("✅ Bot token loaded from .env file")
    
    bot.run_bot(bot_token)
    
    print("\n👋 Bot stopped by user.")