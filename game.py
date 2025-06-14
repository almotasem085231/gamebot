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
    "أعلام الدول": [
  {"name": "علم السعودية", "desc": "علم أخضر يحمل الشهادتين وسيف، يرمز للإسلام والقوة", "link": "https://www.google.com/search?q=علم+السعودية"},
  {"name": "علم المغرب", "desc": "أحمر تتوسطه نجمة خماسية خضراء، يرمز للوحدة والهوية الإسلامية", "link": "https://www.google.com/search?q=علم+المغرب"},
  {"name": "علم الجزائر", "desc": "أخضر وأبيض مع هلال ونجمة حمراء، يرمز للإسلام والحرية", "link": "https://www.google.com/search?q=علم+الجزائر"},
  {"name": "علم تونس", "desc": "أحمر يتوسطه قرص أبيض بداخله هلال ونجمة حمراء", "link": "https://www.google.com/search?q=علم+تونس"},
  {"name": "علم مصر", "desc": "أحمر وأبيض وأسود مع نسر ذهبي في المنتصف، يرمز للوحدة والقوة", "link": "https://www.google.com/search?q=علم+مصر"},
  {"name": "علم الإمارات", "desc": "أحمر، أخضر، أبيض، وأسود، تمثل الوحدة العربية", "link": "https://www.google.com/search?q=علم+الإمارات"},
  {"name": "علم الأردن", "desc": "أسود، أبيض، أخضر مع مثلث أحمر ونجمة سباعية، يرمز للوحدة والحرية", "link": "https://www.google.com/search?q=علم+الأردن"},
  {"name": "علم قطر", "desc": "أبيض وعنابي مع تسعة رؤوس مثلثية، يرمز للهوية والثقافة", "link": "https://www.google.com/search?q=علم+قطر"},

  {"name": "علم المملكة المتحدة", "desc": "يتكون من تداخل أعلام إنجلترا واسكتلندا وإيرلندا، يرمز للوحدة الملكية", "link": "https://www.google.com/search?q=علم+المملكة+المتحدة"},
  {"name": "علم إسبانيا", "desc": "شريطان أحمران وشريط أصفر يتوسطه شعار الدولة", "link": "https://www.google.com/search?q=علم+إسبانيا"},
  {"name": "علم البرتغال", "desc": "أخضر وأحمر مع شعار يتوسطه درع وكرة أرضية، يرمز للاكتشافات البحرية", "link": "https://www.google.com/search?q=علم+البرتغال"},
  {"name": "علم سويسرا", "desc": "مربع أحمر يتوسطه صليب أبيض، يرمز للحياد والسلام", "link": "https://www.google.com/search?q=علم+سويسرا"},
  {"name": "علم ألمانيا", "desc": "أسود، أحمر، ذهبي، يرمز للوحدة والحرية", "link": "https://www.google.com/search?q=علم+ألمانيا"},
  {"name": "علم السويد", "desc": "أزرق مع صليب أصفر، يرمز للمسيحية والتراث الإسكندنافي", "link": "https://www.google.com/search?q=علم+السويد"},
  {"name": "علم فنلندا", "desc": "أبيض مع صليب أزرق، يرمز للثلج والبحيرات", "link": "https://www.google.com/search?q=علم+فنلندا"},

  {"name": "علم الهند", "desc": "زعفراني، أبيض، أخضر مع عجلة دارما زرقاء في الوسط", "link": "https://www.google.com/search?q=علم+الهند"},
  {"name": "علم إندونيسيا", "desc": "شريطان أفقيان: أحمر وأبيض، يرمز للشجاعة والنقاء", "link": "https://www.google.com/search?q=علم+إندونيسيا"},
  {"name": "علم باكستان", "desc": "أخضر مع هلال ونجمة بيضاء وشريط جانبي أبيض، يرمز للإسلام", "link": "https://www.google.com/search?q=علم+باكستان"},
  {"name": "علم الفلبين", "desc": "أزرق، أحمر، مثلث أبيض مع نجمة وشمس، يرمز للحرية", "link": "https://www.google.com/search?q=علم+الفلبين"},
  {"name": "علم فيتنام", "desc": "أحمر مع نجمة صفراء في المنتصف، يرمز للقيادة الشيوعية", "link": "https://www.google.com/search?q=علم+فيتنام"},

  {"name": "علم البرازيل", "desc": "أخضر مع معين أصفر وكرة زرقاء مع شعار ونجوم تمثل السماء", "link": "https://www.google.com/search?q=علم+البرازيل"},
  {"name": "علم الأرجنتين", "desc": "أزرق فاتح وأبيض مع شمس ذهبية، يرمز للحرية", "link": "https://www.google.com/search?q=علم+الأرجنتين"},
  {"name": "علم المكسيك", "desc": "أخضر وأبيض وأحمر مع نسر يأكل أفعى، يرمز للأسطورة الأزتيكية", "link": "https://www.google.com/search?q=علم+المكسيك"},
  {"name": "علم كوبا", "desc": "خمسة خطوط زرقاء وبيضاء مع مثلث أحمر ونجمة بيضاء، يرمز للحرية", "link": "https://www.google.com/search?q=علم+كوبا"},

  {"name": "علم جنوب أفريقيا", "desc": "أخضر، أسود، أصفر، أزرق، وأبيض وأحمر، يرمز للوحدة والتنوع", "link": "https://www.google.com/search?q=علم+جنوب+إفريقيا"},
  {"name": "علم نيجيريا", "desc": "أخضر، أبيض، أخضر، يرمز للزراعة والسلام", "link": "https://www.google.com/search?q=علم+نيجيريا"},
  {"name": "علم مصر", "desc": "أحمر، أبيض، وأسود مع نسر ذهبي", "link": "https://www.google.com/search?q=علم+مصر"},
  {"name": "علم كينيا", "desc": "أحمر، أخضر، وأسود مع درع وحراب تقليدية، يرمز للنضال من أجل الحرية", "link": "https://www.google.com/search?q=علم+كينيا"}
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

    async def is_admin(self, chat_id: int, user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Checks if a user is an administrator in the given chat."""
        try:
            chat_member = await context.bot.get_chat_member(chat_id, user_id)
            return chat_member.status in ['administrator', 'creator']
        except Exception as e:
            logger.error(f"Error checking admin status for user {user_id} in chat {chat_id}: {e}")
            return False

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id

        if update.effective_chat.type not in ['group', 'supergroup']:
            await update.message.reply_text("هذه اللعبة تعمل فقط في المجموعات!")
            return

        # Check if the user is an admin
        if not await self.is_admin(chat_id, user_id, context):
            await update.message.reply_text("لا يمكنك بدء اللعبة! يجب أن تكون أدمن في المجموعة.")
            return

        if chat_id in games:
            await update.message.reply_text("يوجد لعبة نشطة بالفعل في هذه المجموعة! استخدم /cancel لإنهائها أو /score لمعرفة حالة اللعبة.")
            return

        games[chat_id] = {
            'status': 'waiting_category_selection', 
            'creator_id': user_id,
            'players': [], 
            'current_turn': 0, 
            'round': 1,
            'max_rounds': 3, 
            'scores': {}, 
            'characters': {}, # for 1v1 mapping player_id to character
            'team_characters': {}, # for teams mapping team_name to character
            'waiting_for_answer': False,
            'question_asker': None, 
            'answerer_id': None,
            'pending_guess_confirmation': None,
            'game_type': None, # '1v1' or 'teams'
            'team_size': None, # 2 or 3 for teams
            'teams': {'blue': [], 'red': []},
            'current_team_turn': 'blue' # for team mode
        }

        # Present category selection
        keyboard = [
            [InlineKeyboardButton(cat, callback_data=f"select_category_{cat}")]
            for cat in CHARACTERS.keys()
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "🎯 **لعبة تخمين الشخصيات**\n\n"
            "الرجاء اختيار فئة اللعبة:",
            reply_markup=reply_markup, parse_mode='Markdown'
        )

    async def select_category_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        chat_id = query.message.chat_id
        user_id = query.from_user.id
        category = query.data.replace("select_category_", "")

        game = games.get(chat_id)
        if not game or game.get('status') != 'waiting_category_selection':
            await query.edit_message_text("هذه الجولة لانتخاب الفئة قد انتهت أو لا توجد لعبة نشطة.")
            return

        if user_id != game['creator_id']:
            await query.answer("فقط من بدأ اللعبة يمكنه اختيار الفئة.", show_alert=True)
            return

        game['selected_category'] = category
        game['status'] = 'waiting_mode_selection'

        keyboard = [
            [InlineKeyboardButton("1 ضد 1", callback_data="select_mode_1v1")],
            [InlineKeyboardButton("فرق", callback_data="select_mode_teams")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            f"✅ تم اختيار الفئة: **{category}**\n\nالرجاء اختيار نمط اللعبة:",
            reply_markup=reply_markup, parse_mode='Markdown'
        )

    async def select_mode_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        chat_id = query.message.chat_id
        user_id = query.from_user.id
        mode = query.data.replace("select_mode_", "")

        game = games.get(chat_id)
        if not game or game.get('status') != 'waiting_mode_selection':
            await query.edit_message_text("هذه الجولة لانتخاب النمط قد انتهت أو لا توجد لعبة نشطة.")
            return

        if user_id != game['creator_id']:
            await query.answer("فقط من بدأ اللعبة يمكنه اختيار نمط اللعبة.", show_alert=True)
            return

        game['game_type'] = mode

        if mode == '1v1':
            game['status'] = 'waiting_players'
            keyboard = [[InlineKeyboardButton("🎮 انضمام للعبة", callback_data="join_game_1v1")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                "🎯 **لعبة تخمين الشخصيات**\n\n"
                "تم اختيار نمط: **1 ضد 1**\n\n"
                "قواعد اللعبة:\n"
                "• يحتاج لاعبان للبدء\n"
                "• كل لاعب يحصل على شخصية عشوائية من فئة **" + game['selected_category'] + "**\n"
                "• اللاعبون يتناوبون طرح أسئلة نعم/لا\n"
                "• الهدف تخمين شخصية الخصم\n"
                f"• اللعبة ستستمر لـ {games[chat_id]['max_rounds']} جولات.\n\n"
                "اضغط على الزر للانضمام!",
                reply_markup=reply_markup, parse_mode='Markdown'
            )
        elif mode == 'teams':
            game['status'] = 'waiting_team_size_selection'
            keyboard = [
                [InlineKeyboardButton("2 ضد 2", callback_data="select_team_size_2")],
                [InlineKeyboardButton("3 ضد 3", callback_data="select_team_size_3")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "تم اختيار نمط: **فرق**\n\nالرجاء اختيار حجم الفريق:",
                reply_markup=reply_markup, parse_mode='Markdown'
            )

    async def select_team_size_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        chat_id = query.message.chat_id
        user_id = query.from_user.id
        team_size = int(query.data.replace("select_team_size_", ""))

        game = games.get(chat_id)
        if not game or game.get('status') != 'waiting_team_size_selection':
            await query.edit_message_text("هذه الجولة لانتخاب حجم الفريق قد انتهت أو لا توجد لعبة نشطة.")
            return

        if user_id != game['creator_id']:
            await query.answer("فقط من بدأ اللعبة يمكنه اختيار حجم الفريق.", show_alert=True)
            return

        game['team_size'] = team_size
        game['status'] = 'waiting_teams_join'

        keyboard = [
            [InlineKeyboardButton("🔵 الانضمام للفريق الأزرق", callback_data="join_team_blue")],
            [InlineKeyboardButton("🔴 الانضمام للفريق الأحمر", callback_data="join_team_red")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            f"✅ تم اختيار حجم الفريق: **{team_size} ضد {team_size}**\n\n"
            f"عدد اللاعبين المطلوب لكل فريق: {team_size}\n"
            "اضغط على الزر للانضمام إلى فريق!\n\n"
            f"الفريق الأزرق: {len(game['teams']['blue'])}/{team_size}\n"
            f"الفريق الأحمر: {len(game['teams']['red'])}/{team_size}",
            reply_markup=reply_markup, parse_mode='Markdown'
        )

    async def join_game_1v1_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        chat_id = query.message.chat_id
        user_id = query.from_user.id
        username = query.from_user.first_name

        game = games.get(chat_id)
        if not game or game.get('status') != 'waiting_players' or game.get('game_type') != '1v1':
            await query.answer("اللعبة بدأت بالفعل أو لا توجد لعبة 1v1 نشطة!", show_alert=True)
            return
        
        if user_id in [p['id'] for p in game['players']]:
            await query.answer("أنت مشترك بالفعل في اللعبة!", show_alert=True)
            return
        if len(game['players']) >= 2:
            await query.answer("اللعبة ممتلئة!", show_alert=True)
            return
        
        game['players'].append({'id': user_id, 'name': username})
        game['scores'][user_id] = 0

        players_joined_names = [p['name'] for p in game['players']]
        
        if len(game['players']) == 1:
            keyboard = [[InlineKeyboardButton("🎮 انضمام للعبة", callback_data="join_game_1v1")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"✅ **{username} انضم للعبة!**\n\n"
                f"اللاعبون المنضمون: {', '.join(players_joined_names)}\n"
                "في انتظار لاعب آخر...",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        elif len(game['players']) == 2:
            await query.edit_message_text(
                f"✅ **{username} انضم للعبة!**\n\n"
                f"اللاعبون المنضمون: {', '.join(players_joined_names)}\n"
                "جميع اللاعبين انضموا! اللعبة ستبدأ الآن...",
                parse_mode='Markdown'
            )
            await self.start_game_1v1(chat_id, context)

    async def join_team_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        chat_id = query.message.chat_id
        user_id = query.from_user.id
        username = query.from_user.first_name
        team_name = query.data.replace("join_team_", "") # 'blue' or 'red'

        game = games.get(chat_id)
        if not game or game.get('status') != 'waiting_teams_join' or game.get('game_type') != 'teams':
            await query.answer("هذه الجولة للانضمام للفريق قد انتهت أو لا توجد لعبة فرق نشطة!", show_alert=True)
            return
        
        # Check if already in a team
        for existing_team_name in game['teams']:
            if user_id in [p['id'] for p in game['teams'][existing_team_name]]:
                await query.answer(f"أنت مشترك بالفعل في الفريق {existing_team_name}!", show_alert=True)
                return

        # Check team capacity
        if len(game['teams'][team_name]) >= game['team_size']:
            await query.answer(f"الفريق {team_name} ممتلئ! اكتملت الفرق.", show_alert=True)
            return
        
        game['teams'][team_name].append({'id': user_id, 'name': username})
        game['players'].append({'id': user_id, 'name': username, 'team': team_name}) # Keep a flat list for score tracking
        game['scores'][user_id] = 0 # Initialize score for each player

        blue_players_names = [p['name'] for p in game['teams']['blue']]
        red_players_names = [p['name'] for p in game['teams']['red']]

        all_teams_full = (len(game['teams']['blue']) == game['team_size'] and
                          len(game['teams']['red']) == game['team_size'])

        keyboard = [
            [InlineKeyboardButton("🔵 الانضمام للفريق الأزرق", callback_data="join_team_blue")],
            [InlineKeyboardButton("🔴 الانضمام للفريق الأحمر", callback_data="join_team_red")]
        ]
        
        if all_teams_full:
            # Add a 'Start Game' button for the creator
            keyboard.append([InlineKeyboardButton("🚀 بدء اللعبة", callback_data="start_teams_game")])
            
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            f"✅ **{username} انضم للفريق {team_name}!**\n\n"
            f"الفريق الأزرق ({len(game['teams']['blue'])}/{game['team_size']}): {', '.join(blue_players_names) if blue_players_names else 'لا يوجد لاعبون'}\n"
            f"الفريق الأحمر ({len(game['teams']['red'])}/{game['team_size']}): {', '.join(red_players_names) if red_players_names else 'لا يوجد لاعبون'}\n\n" +
            ("جميع الفرق اكتملت! اضغط على 'بدء اللعبة' لبدء الجولة." if all_teams_full else "في انتظار اكتمال الفرق..."),
            reply_markup=reply_markup, parse_mode='Markdown'
        )


    async def start_teams_game_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        chat_id = query.message.chat_id
        user_id = query.from_user.id

        game = games.get(chat_id)
        if not game or game.get('status') != 'waiting_teams_join' or game.get('game_type') != 'teams':
            await query.edit_message_text("لا توجد لعبة فرق نشطة يمكن بدؤها.")
            return

        if user_id != game['creator_id']:
            await query.answer("فقط من بدأ اللعبة يمكنه بدء اللعبة.", show_alert=True)
            return
        
        if not (len(game['teams']['blue']) == game['team_size'] and len(game['teams']['red']) == game['team_size']):
            await query.answer("الفرق لم تكتمل بعد!", show_alert=True)
            return

        await query.edit_message_text(
            f"🚀 **{query.from_user.first_name} بدأ اللعبة!**\n"
            "جميع الفرق جاهزة! اللعبة ستبدأ الآن...",
            parse_mode='Markdown'
        )
        await self.start_game_teams(chat_id, context)


    async def start_game_1v1(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE):
        game = games[chat_id]
        game['status'] = 'playing'
        
        # Assign characters for 1v1
        for player in game['players']:
            category = game['selected_category'] # Use selected category
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
        players_text = " و ".join([p['name'] for p in game['players']])
        await context.bot.send_message(chat_id, f"🚀 اللعبة بدأت بين {players_text}!")
        await asyncio.sleep(2)
        await self.start_round(chat_id, context)

    async def start_game_teams(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE):
        game = games[chat_id]
        game['status'] = 'playing'

        # Assign a single character per team
        category = game['selected_category']
        blue_character = random.choice(CHARACTERS[category])
        red_character = random.choice(CHARACTERS[category])

        game['team_characters']['blue'] = {
            'category': category, 'character': blue_character, 'name': blue_character['name'],
            'desc': blue_character['desc'], 'link': blue_character['link']
        }
        game['team_characters']['red'] = {
            'category': category, 'character': red_character, 'name': red_character['name'],
            'desc': red_character['desc'], 'link': red_character['link']
        }

        # Send characters to each player privately
        for team_name, team_members in game['teams'].items():
            character_info = game['team_characters'][team_name]
            for player in team_members:
                try:
                    await context.bot.send_message(
                        chat_id=player['id'],
                        text=f"🎭 **شخصية فريقك ({'الأزرق' if team_name == 'blue' else 'الأحمر'}) في اللعبة:**\n\n"
                             f"**الاسم:** {character_info['name']}\n"
                             f"**الفئة:** {character_info['category']}\n"
                             f"**الوصف:** {character_info['desc']}\n\n"
                             f"🔗 [معلومات إضافية]({character_info['link']})\n\n⚠️ احتفظ بهذه المعلومات سرية من الفريق الخصم!\n\n"
                             "تذكر أن فريقك يتشارك نفس الشخصية. تواصلوا في المجموعة للتشاور حول الأسئلة والإجابات." ,
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
        
        await context.bot.send_message(chat_id, "🚀 اللعبة بدأت بين الفرق!")
        await asyncio.sleep(2)
        await self.start_round(chat_id, context)


    async def start_round(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE):
        game = games[chat_id]

        if game['game_type'] == '1v1':
            current_player = game['players'][game['current_turn']]
            other_player = game['players'][1 - game['current_turn']]
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"🏁 **الجولة {game['round']}**\n\n"
                     f"دور **{current_player['name']}** لطرح سؤال!\n"
                     f"يجب على **{other_player['name']}** الإجابة بنعم أو لا.\n\n"
                     f"💡 يمكنك أيضاً تخمين الشخصية مباشرة بكتابة اسمها!",
                parse_mode='Markdown'
            )
        elif game['game_type'] == 'teams':
            current_team_name = game['current_team_turn']
            other_team_name = 'red' if current_team_name == 'blue' else 'blue'
            current_team_players = [p['name'] for p in game['teams'][current_team_name]]
            other_team_players = [p['name'] for p in game['teams'][other_team_name]]

            await context.bot.send_message(
                chat_id=chat_id,
                text=f"🏁 **الجولة {game['round']}**\n\n"
                     f"دور **الفريق {'الأزرق' if current_team_name == 'blue' else 'الأحمر'}** ({', '.join(current_team_players)}) لطرح سؤال!\n"
                     f"يجب على **الفريق {'الأحمر' if other_team_name == 'red' else 'الأزرق'}** ({', '.join(other_team_players)}) الإجابة بنعم أو لا.\n\n"
                     f"💡 يمكن لأي لاعب من الفريق الذي عليه الدور أن يسأل أو يخمن. يمكن لأي لاعب من الفريق الآخر أن يجيب.",
                parse_mode='Markdown'
            )


    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        message_text = update.message.text
        if chat_id not in games: return
        game = games[chat_id]
        if game['status'] != 'playing': return

        # Check if the user is a player in the current game
        is_player = False
        player_info = None
        if game['game_type'] == '1v1':
            player_info = next((p for p in game['players'] if p['id'] == user_id), None)
            is_player = player_info is not None
        elif game['game_type'] == 'teams':
            for team_name, players_list in game['teams'].items():
                player_in_team = next((p for p in players_list if p['id'] == user_id), None)
                if player_in_team:
                    is_player = True
                    player_info = {'id': user_id, 'name': update.effective_user.first_name, 'team': team_name}
                    break
        
        if not is_player: return # If not a player, ignore message

        # Prevent actions if a guess confirmation is pending
        if game.get('pending_guess_confirmation'):
            # If the user is the one whose character was guessed (in 1v1) or from the guessed team (in teams)
            # they should use the buttons in their DM
            if game['game_type'] == '1v1' and user_id == game['pending_guess_confirmation']['guessed_id']:
                await update.message.reply_text("يرجى استخدام الأزرار في رسالتي الخاصة لتأكيد أو نفي التخمين.")
            elif game['game_type'] == 'teams' and player_info and player_info['team'] == game['pending_guess_confirmation']['guessed_team']:
                 await update.message.reply_text("يرجى استخدام الأزرار في رسالتي الخاصة لتأكيد أو نفي التخمين.")
            else:
                await update.message.reply_text("هناك تخمين معلق في انتظار التأكيد. يرجى الانتظار.")
            return

        # This part handles direct text answers "نعم" or "لا" from the answerer
        # In team mode, any member of the answering team can answer
        if game.get('waiting_for_answer'):
            if game['game_type'] == '1v1':
                if user_id == game.get('answerer_id'):
                    lower_text = message_text.lower().strip()
                    if lower_text in ['نعم', 'yes', 'y', 'نعم.', 'yes.']:
                        await self.process_answer(chat_id, context, "answer_yes", update.message)
                    elif lower_text in ['لا', 'no', 'n', 'لا.', 'no.']:
                        await self.process_answer(chat_id, context, "answer_no", update.message)
                    return
            elif game['game_type'] == 'teams':
                # Check if the user is part of the answering team
                current_team_turn = game['current_team_turn']
                other_team = 'red' if current_team_turn == 'blue' else 'blue'
                if user_id in [p['id'] for p in game['teams'][other_team]]:
                    lower_text = message_text.lower().strip()
                    if lower_text in ['نعم', 'yes', 'y', 'نعم.', 'yes.']:
                        await self.process_answer(chat_id, context, "answer_yes", update.message)
                    elif lower_text in ['لا', 'no', 'n', 'لا.', 'no.']:
                        await self.process_answer(chat_id, context, "answer_no", update.message)
                    return
            return # If awaiting answer but not the answerer/answering team member, ignore message

        # Check whose turn it is to ask/guess
        if game['game_type'] == '1v1':
            current_player = game['players'][game['current_turn']]
            if user_id != current_player['id']:
                await update.message.reply_text(f"انتظر دورك! دور {current_player['name']} الآن.")
                return
            other_player = game['players'][1 - game['current_turn']]
            other_character_name = game['characters'][other_player['id']]['name']
        elif game['game_type'] == 'teams':
            current_team_name = game['current_team_turn']
            if player_info['team'] != current_team_name:
                await update.message.reply_text(f"انتظر دور فريقك! دور الفريق {'الأزرق' if current_team_name == 'blue' else 'الأحمر'} الآن.")
                return
            other_team_name = 'red' if current_team_name == 'blue' else 'blue'
            other_character_name = game['team_characters'][other_team_name]['name']
            
        if game.get('waiting_for_answer'):
            await update.message.reply_text("في انتظار إجابة على السؤال السابق!")
            return
        
        # --- Handle Guessing ---
        if message_text.strip() == other_character_name:
            game['pending_guess_confirmation'] = {
                'guesser_id': user_id, # The player who made the guess
                'chat_id': chat_id,
            }
            if game['game_type'] == '1v1':
                game['pending_guess_confirmation']['guessed_id'] = other_player['id']
                target_user_id = other_player['id']
                target_user_name = other_player['name']
            elif game['game_type'] == 'teams':
                game['pending_guess_confirmation']['guessed_team'] = other_team_name
                # We need to send the confirmation to all members of the guessed team
                # but only one of them needs to confirm. For simplicity, we'll pick the first one
                # or better, send to all and any one can answer. The previous implementation
                # was sending to the 'other_player_id' which will be handled below.
                # In team mode, we should iterate through the guessed team members.
                target_user_ids = [p['id'] for p in game['teams'][other_team_name]]
                target_user_name = "الفريق " + ('الأحمر' if other_team_name == 'red' else 'الأزرق')

            keyboard = [[
                InlineKeyboardButton("✅ نعم، هذا هو!", callback_data=f"confirm_guess_{user_id}_{other_character_name}"),
                InlineKeyboardButton("❌ لا، ليس كذلك.", callback_data=f"deny_guess_{user_id}_{other_character_name}")
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            try:
                if game['game_type'] == '1v1':
                    confirm_msg = await context.bot.send_message(
                        chat_id=target_user_id,
                        text=f"🤔 **تخمين!**\n\nاللاعب {update.effective_user.first_name} في مجموعة **{update.effective_chat.title}** يعتقد أن شخصيتك هي:\n**{message_text.strip()}**\n\nهل هذا صحيح؟",
                        reply_markup=reply_markup,
                        parse_mode='Markdown'
                    )
                    game['pending_guess_confirmation']['message_id'] = confirm_msg.message_id
                elif game['game_type'] == 'teams':
                    # Send to all members of the opposing team
                    for member_id in target_user_ids:
                        confirm_msg = await context.bot.send_message(
                            chat_id=member_id,
                            text=f"🤔 **تخمين من الفريق الخصم!**\n\nاللاعب {update.effective_user.first_name} من فريقك في مجموعة **{update.effective_chat.title}** يعتقد أن شخصية فريقكم هي:\n**{message_text.strip()}**\n\nهل هذا صحيح؟\n\n"
                                 "**ملاحظة:** أي عضو في فريقك يمكنه تأكيد أو نفي التخمين بالضغط على الزر.",
                            reply_markup=reply_markup,
                            parse_mode='Markdown'
                        )
                        # Store message_ids for all messages sent, for later editing (optional, but good practice)
                        if 'message_ids' not in game['pending_guess_confirmation']:
                            game['pending_guess_confirmation']['message_ids'] = {}
                        game['pending_guess_confirmation']['message_ids'][member_id] = confirm_msg.message_id

                await update.message.reply_text(
                    f"🕵️‍♂️ **{update.effective_user.first_name} خمّن شخصية!**\n\n"
                    f"أرسلت طلباً إلى {target_user_name} لتأكيد التخمين. يرجى الانتظار...",
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Failed to send private guess confirmation: {e}")
                await update.message.reply_text(
                    f"⚠️ لم أتمكن من إرسال طلب التأكيد. "
                    "الرجاء التأكد من أن جميع اللاعبين قد بدأوا محادثة معي أولاً. يرجى إعادة التخمين بعد حل المشكلة."
                )
                game['pending_guess_confirmation'] = None # Reset state
            return

        elif message_text.strip() != other_character_name and any(p['name'] == message_text.strip() for category_list in CHARACTERS.values() for p in category_list):
            # If it's a known character name, but not the correct guess
            await update.message.reply_text(f"تخمين خاطئ! {message_text.strip()} ليس الشخصية الصحيحة.")
            
            # Pass the turn
            if game['game_type'] == '1v1':
                game['current_turn'] = 1 - game['current_turn']
            elif game['game_type'] == 'teams':
                game['current_team_turn'] = 'red' if game['current_team_turn'] == 'blue' else 'blue'

            await asyncio.sleep(1)
            await self.start_round(chat_id, context) # Announce next turn
            return

        # --- Handle Question Asking (if not a guess) ---
        game['waiting_for_answer'] = True
        game['question_asker'] = user_id
        
        if game['game_type'] == '1v1':
            game['answerer_id'] = other_player['id']
            answer_recipient_name = other_player['name']
        elif game['game_type'] == 'teams':
            other_team_name = 'red' if game['current_team_turn'] == 'blue' else 'blue'
            # We don't need a single 'answerer_id' as any team member can answer.
            # We just need to know which team is expected to answer.
            game['answerer_team'] = other_team_name
            answer_recipient_name = "الفريق " + ('الأحمر' if other_team_name == 'red' else 'الأزرق')

        keyboard = [[InlineKeyboardButton("✅ نعم", callback_data="answer_yes"),
                     InlineKeyboardButton("❌ لا", callback_data="answer_no")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"❓ **السؤال:** {message_text}\n\n👤 **{answer_recipient_name}**, اختر إجابتك:",
            reply_markup=reply_markup, parse_mode='Markdown'
        )

    async def handle_answer_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = query.from_user.id
        answer = query.data

        # Determine the original group chat_id
        main_game_chat_id = None
        for g_chat_id, g_state in games.items():
            if g_state.get('waiting_for_answer'):
                if g_state['game_type'] == '1v1' and g_state.get('answerer_id') == user_id:
                    main_game_chat_id = g_chat_id
                    break
                elif g_state['game_type'] == 'teams':
                    # Check if user is part of the answering team
                    current_team_turn = g_state['current_team_turn']
                    other_team = 'red' if current_team_turn == 'blue' else 'blue'
                    if user_id in [p['id'] for p in g_state['teams'][other_team]]:
                        main_game_chat_id = g_chat_id
                        break
        
        if not main_game_chat_id:
             await query.answer("لا توجد لعبة نشطة أو هذا السؤال لا يخص لعبة حالية.", show_alert=True)
             return

        game = games[main_game_chat_id]
        
        # Double check if it's their turn to answer (important for race conditions)
        if game['game_type'] == '1v1' and (not game.get('waiting_for_answer') or game.get('answerer_id') != user_id):
            await query.answer("تمت الإجابة على هذا السؤال بالفعل أو ليس دورك للإجابة.", show_alert=True)
            return
        elif game['game_type'] == 'teams':
            current_team_turn = game['current_team_turn']
            expected_answering_team = 'red' if current_team_turn == 'blue' else 'blue'
            if not game.get('waiting_for_answer') or user_id not in [p['id'] for p in game['teams'][expected_answering_team]]:
                await query.answer("تمت الإجابة على هذا السؤال بالفعل أو ليس دور فريقك للإجابة.", show_alert=True)
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
        game['question_asker'] = None
        game['answerer_id'] = None
        game['answerer_team'] = None

        # Pass the turn
        if game['game_type'] == '1v1':
            game['current_turn'] = 1 - game['current_turn']
        elif game['game_type'] == 'teams':
            game['current_team_turn'] = 'red' if game['current_team_turn'] == 'blue' else 'blue'
        
        await asyncio.sleep(2)
        await self.start_round(chat_id, context)

    async def handle_guess_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id # This is the ID of the player responding to the guess

        # Parse callback_data: confirm_guess_guesserid_guessedcharname or deny_guess_guesserid_guessedcharname
        parts = query.data.split('_')
        action = parts[0] # confirm or deny
        guesser_id = int(parts[2])
        guessed_character_name = parts[3] # The name that was guessed

        # Find the game where this confirmation is pending
        game_found = None
        main_game_chat_id = None
        for chat_id, game_state in games.items():
            pending = game_state.get('pending_guess_confirmation')
            if pending and pending['guesser_id'] == guesser_id:
                game_found = game_state
                main_game_chat_id = chat_id
                break
        
        if not game_found:
            await query.edit_message_text("هذا التخمين لم يعد معلقاً أو انتهت اللعبة.")
            return

        guesser_name = next(p['name'] for p in game_found['players'] if p['id'] == guesser_id)
        
        is_correct_confirmer = False
        if game_found['game_type'] == '1v1':
            # Check if the confirmer is the 'guessed_id'
            if user_id == game_found['pending_guess_confirmation']['guessed_id']:
                is_correct_confirmer = True
                guessed_player_id = user_id
                target_character_info = game_found['characters'][guessed_player_id]
                guessed_target_name = next(p['name'] for p in game_found['players'] if p['id'] == guessed_player_id)
            else:
                await query.edit_message_text("أنت لا تملك الصلاحية لتأكيد هذا التخمين أو نفيه.")
                return
        elif game_found['game_type'] == 'teams':
            # Check if the confirmer is part of the 'guessed_team'
            guessed_team_name = game_found['pending_guess_confirmation']['guessed_team']
            if user_id in [p['id'] for p in game_found['teams'][guessed_team_name]]:
                is_correct_confirmer = True
                guessed_player_id = user_id # Just using this as a placeholder, actual target is the team
                target_character_info = game_found['team_characters'][guessed_team_name]
                guessed_target_name = "الفريق " + ('الأحمر' if guessed_team_name == 'red' else 'الأزرق')
            else:
                await query.edit_message_text("أنت لا تملك الصلاحية لتأكيد هذا التخمين أو نفيه.")
                return

        if not is_correct_confirmer:
            await query.edit_message_text("حدث خطأ في تحديد صلاحيات التأكيد. يرجى المحاولة مرة أخرى.")
            return

        # Ensure the guessed character name matches the actual character if confirmed
        if action == "confirm":
            if guessed_character_name != target_character_info['name']:
                # This should ideally not happen if logic for sending guessed name is correct,
                # but it's a safety check.
                await query.edit_message_text("حدث خطأ! التخمين الذي أكدته لا يتطابق مع الشخصية الفعلية.")
                logger.warning(f"Mismatch in guess confirmation: Expected {target_character_info['name']}, got {guessed_character_name}")
                game_found['pending_guess_confirmation'] = None # Reset state on error
                return
            
            await query.edit_message_text(f"✅ لقد أكدت أن {guesser_name} خمن شخصية **{guessed_target_name}** بشكل صحيح: **{guessed_character_name}**.", parse_mode='Markdown')
            
            # In team mode, also edit other team members' private messages
            if game_found['game_type'] == 'teams' and 'message_ids' in game_found['pending_guess_confirmation']:
                for member_id, msg_id in game_found['pending_guess_confirmation']['message_ids'].items():
                    if member_id != user_id: # Don't re-edit the one that was just edited
                        try:
                            await context.bot.edit_message_text(
                                chat_id=member_id, message_id=msg_id,
                                text=f"✅ لقد أكد {query.from_user.first_name} أن التخمين كان صحيحاً: **{guessed_character_name}**.",
                                parse_mode='Markdown'
                            )
                        except Exception as e:
                            logger.error(f"Failed to edit other team member's guess confirmation message {member_id}: {e}")

            await context.bot.send_message(
                chat_id=main_game_chat_id,
                text=f"🎉 **{guesser_name} خمن شخصية {guessed_target_name} بشكل صحيح!**",
                parse_mode='Markdown'
            )
            game_found['pending_guess_confirmation'] = None # Clear pending state
            await self.handle_correct_guess(main_game_chat_id, guesser_id, context) # Award point, next round/end game
        else: # deny
            await query.edit_message_text(f"❌ لقد نفيت تخمين {guesser_name}. شخصية **{guessed_target_name}** ليست **{guessed_character_name}**.", parse_mode='Markdown')

            # In team mode, also edit other team members' private messages
            if game_found['game_type'] == 'teams' and 'message_ids' in game_found['pending_guess_confirmation']:
                for member_id, msg_id in game_found['pending_guess_confirmation']['message_ids'].items():
                    if member_id != user_id:
                        try:
                            await context.bot.edit_message_text(
                                chat_id=member_id, message_id=msg_id,
                                text=f"❌ لقد نفى {query.from_user.first_name} التخمين. شخصية فريقكم ليست **{guessed_character_name}**.",
                                parse_mode='Markdown'
                            )
                        except Exception as e:
                            logger.error(f"Failed to edit other team member's guess denial message {member_id}: {e}")

            await context.bot.send_message(
                chat_id=main_game_chat_id,
                text=f"🤷‍♂️ **{guesser_name} خمن شخصية {guessed_target_name} بشكل خاطئ!**",
                parse_mode='Markdown'
            )
            game_found['pending_guess_confirmation'] = None # Clear pending state
            
            # Pass the turn to the other player/team (the one who was just guessed)
            if game_found['game_type'] == '1v1':
                game_found['current_turn'] = 1 - game_found['current_turn']
            elif game_found['game_type'] == 'teams':
                game_found['current_team_turn'] = 'red' if game_found['current_team_turn'] == 'blue' else 'blue'

            await asyncio.sleep(1)
            await self.start_round(main_game_chat_id, context)


    async def handle_correct_guess(self, chat_id: int, guesser_id: int, context: ContextTypes.DEFAULT_TYPE):
        game = games[chat_id]
        guesser = next(p for p in game['players'] if p['id'] == guesser_id)
        
        if game['game_type'] == '1v1':
            other_player = next(p for p in game['players'] if p['id'] != guesser_id)
            character_info = game['characters'][other_player['id']]
            game['scores'][guesser_id] += 1
            guessed_target_name = other_player['name']
        elif game['game_type'] == 'teams':
            guesser_team_name = next(p['team'] for p in game['players'] if p['id'] == guesser_id)
            other_team_name = 'red' if guesser_team_name == 'blue' else 'blue'
            character_info = game['team_characters'][other_team_name]
            # Award points to all players in the guessing team
            for player_in_guesser_team in game['teams'][guesser_team_name]:
                game['scores'][player_in_guesser_team['id']] += 1
            guessed_target_name = "الفريق " + ('الأحمر' if other_team_name == 'red' else 'الأزرق')

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
        await asyncio.sleep(2)

        if game['round'] >= game['max_rounds']:
            await self.end_game(chat_id, context)
        else:
            game['round'] += 1
            game['current_turn'] = 0 # Reset for 1v1
            game['current_team_turn'] = 'blue' # Reset for teams
            game['waiting_for_answer'] = False
            
            # Re-assign characters for the new round
            if game['game_type'] == '1v1':
                for player in game['players']:
                    category = game['selected_category'] # Use the chosen category
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
                        return
            elif game['game_type'] == 'teams':
                category = game['selected_category']
                blue_character = random.choice(CHARACTERS[category])
                red_character = random.choice(CHARACTERS[category])

                game['team_characters']['blue'] = {
                    'category': category, 'character': blue_character, 'name': blue_character['name'],
                    'desc': blue_character['desc'], 'link': blue_character['link']
                }
                game['team_characters']['red'] = {
                    'category': category, 'character': red_character, 'name': red_character['name'],
                    'desc': red_character['desc'], 'link': red_character['link']
                }

                for team_name, team_members in game['teams'].items():
                    character_info = game['team_characters'][team_name]
                    for player in team_members:
                        try:
                            await context.bot.send_message(
                                chat_id=player['id'],
                                text=f"🎭 **شخصية فريقك الجديدة - الجولة {game['round']}:**\n\n"
                                     f"**الاسم:** {character_info['name']}\n"
                                     f"**الفئة:** {character_info['category']}\n"
                                     f"**الوصف:** {character_info['desc']}\n\n"
                                     f"🔗 [معلومات إضافية]({character_info['link']})\n\n⚠️ احتفظ بهذه المعلومات سرية!",
                                parse_mode='Markdown', disable_web_page_preview=True
                            )
                        except Exception as e:
                            logger.error(f"Failed to send private message to {player['id']}: {e}")
                            await context.bot.send_message(
                                chat_id,
                                f"⚠️ تعذر إرسال الشخصية الجديدة لـ {player['name']}. "
                                "يرجى التأكد من أنك بدأت محادثة معي أولاً. سيتم إنهاء اللعبة."
                            )
                            del games[chat_id]
                            return

            await context.bot.send_message(chat_id, f"⏳ يتم تجهيز الجولة {game['round']}...")
            await asyncio.sleep(3)
            await self.start_round(chat_id, context)

    async def end_game(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE):
        if chat_id not in games: return
        game = games[chat_id]

        # Calculate final scores for teams in team mode
        if game['game_type'] == 'teams':
            blue_team_score = sum(game['scores'].get(p['id'], 0) for p in game['teams']['blue'])
            red_team_score = sum(game['scores'].get(p['id'], 0) for p in game['teams']['red'])
            
            result_text = "🏆 **نتائج اللعبة:**\n\n"
            result_text += f"🔵 الفريق الأزرق: {blue_team_score} نقاط\n"
            result_text += f"🔴 الفريق الأحمر: {red_team_score} نقاط\n\n"

            if blue_team_score == red_team_score:
                result_text += "🤝 تعادل!\n\n"
            elif blue_team_score > red_team_score:
                result_text += "🥇 الفائز: الفريق الأزرق!\n\n"
            else:
                result_text += "🥇 الفائز: الفريق الأحمر!\n\n"
        else: # 1v1 mode
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

    async def cancel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Allows a user to cancel the current game in their group."""
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id

        if chat_id in games:
            # Only the creator or an admin can cancel the game
            if games[chat_id]['creator_id'] == user_id or await self.is_admin(chat_id, user_id, context):
                del games[chat_id]
                await update.message.reply_text("تم إلغاء اللعبة بنجاح! يمكنك بدء لعبة جديدة باستخدام /start.")
            else:
                await update.message.reply_text("فقط من بدأ اللعبة أو الأدمن يمكنه إلغاء اللعبة.")
        else:
            await update.message.reply_text("لا توجد لعبة نشطة لإلغائها في هذه المجموعة.")

    async def rules_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Displays the game rules."""
        chat_id = update.effective_chat.id
        max_rounds_text = "3" # Default value if no game is active
        game_type_text = "1 ضد 1"
        team_size_text = ""
        category_text = "أي فئة"

        if chat_id in games:
            game = games[chat_id]
            max_rounds_text = str(game['max_rounds'])
            if game.get('game_type') == 'teams':
                game_type_text = "فرق"
                team_size_text = f" ({game.get('team_size')} ضد {game.get('team_size')})"
            category_text = game.get('selected_category', 'أي فئة')


        await update.message.reply_text(
            f"📜 **قواعد لعبة تخمين الشخصيات:**\n\n"
            f"• اللعبة بنمط: **{game_type_text}{team_size_text}**.\n"
            f"• فئة الشخصيات: **{category_text}**.\n"
            "• عند الانضمام، يتلقى كل لاعب/فريق شخصية سرية.\n"
            "• يتناوب اللاعبون/الفرق على طرح أسئلة إجابتها 'نعم' أو 'لا' لتضييق نطاق الاحتمالات حول شخصية الخصم.\n"
            "• يمكن للاعب/الفريق محاولة تخمين شخصية الخصم في دوره بكتابة اسم الشخصية مباشرة. إذا كان التخمين صحيحاً، سيطلب من الخصم تأكيد ذلك.\n"
            "• التخمين الصحيح يمنح اللاعب/الفريق نقطة وينهي الجولة.\n"
            f"• اللعبة تستمر لـ {max_rounds_text} جولات. في نهاية كل جولة، يحصل اللاعبون/الفرق على شخصيات جديدة.\n"
            "• الفائز هو من يحصل على أكبر عدد من النقاط في نهاية الجولات.\n"
            "• في حالة تعادل النقاط، تعتبر اللعبة تعادلاً.\n\n"
            "استخدم /start لبدء لعبة جديدة."
            , parse_mode='Markdown'
        )

    async def score_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Displays the current scores of the active game."""
        chat_id = update.effective_chat.id
        if chat_id not in games or games[chat_id]['status'] not in ['playing', 'waiting_teams_join', 'waiting_players']:
            await update.message.reply_text("لا توجد لعبة نشطة لعرض نقاطها حاليًا. استخدم /start لبدء واحدة.")
            return

        game = games[chat_id]
        if not game['players'] and game['game_type'] == '1v1':
            await update.message.reply_text("لا يوجد لاعبون في اللعبة لعرض نقاطهم بعد.")
            return
        
        scores_text = "📊 **النقاط الحالية:**\n"
        if game['game_type'] == '1v1':
            for player in game['players']:
                player_id = player['id']
                player_name = player['name']
                score = game['scores'].get(player_id, 0)
                scores_text += f"• {player_name}: {score} نقاط\n"
        elif game['game_type'] == 'teams':
            blue_team_score = sum(game['scores'].get(p['id'], 0) for p in game['teams']['blue'])
            red_team_score = sum(game['scores'].get(p['id'], 0) for p in game['teams']['red'])
            scores_text += f"🔵 الفريق الأزرق: {blue_team_score} نقاط\n"
            scores_text += f"🔴 الفريق الأحمر: {red_team_score} نقاط\n"

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
        
        if game['game_type'] == '1v1':
            player_ids = [p['id'] for p in game['players']]
            if user_id not in player_ids:
                await update.message.reply_text("أنت لست جزءًا من هذه اللعبة.")
                return
            other_player = next((p for p in game['players'] if p['id'] != user_id), None)
            if not other_player: 
                await update.message.reply_text("حدث خطأ في تحديد اللاعب الآخر. لا يمكن التراجع.")
                return

            await context.bot.send_message(
                chat_id=chat_id,
                text=f"🏳️ **تراجع!**\n\nاللاعب **{user_name}** استسلم!\n"
                    f"**{other_player['name']}** يفوز بالجولة تلقائياً ويحصل على نقطة!",
                parse_mode='Markdown'
            )
            game['scores'][other_player['id']] += 1

        elif game['game_type'] == 'teams':
            forfeiting_team_name = None
            for team_name, players_list in game['teams'].items():
                if user_id in [p['id'] for p in players_list]:
                    forfeiting_team_name = team_name
                    break
            
            if not forfeiting_team_name:
                await update.message.reply_text("أنت لست جزءًا من هذه اللعبة.")
                return

            winning_team_name = 'red' if forfeiting_team_name == 'blue' else 'blue'
            
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"🏳️ **تراجع من الفريق!**\n\nاللاعب **{user_name}** من الفريق {'الأزرق' if forfeiting_team_name == 'blue' else 'الأحمر'} استسلم!\n"
                    f"**الفريق {'الأحمر' if winning_team_name == 'red' else 'الأزرق'}** يفوز بالجولة تلقائياً ويحصل على نقطة!",
                parse_mode='Markdown'
            )
            # Award point to all players in the winning team
            for player_in_winning_team in game['teams'][winning_team_name]:
                game['scores'][player_in_winning_team['id']] += 1

        await self.next_round_or_end_game(chat_id, context)

    async def approve_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """This command is mostly deprecated by the callback buttons, but can be a fallback."""
        await update.message.reply_text("يرجى استخدام الأزرار في رسالتي الخاصة لتأكيد أو نفي التخمين.")

    async def callback_query_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        data = query.data
        
        if data.startswith("select_category_"):
            await self.select_category_callback(update, context)
        elif data.startswith("select_mode_"):
            await self.select_mode_callback(update, context)
        elif data.startswith("select_team_size_"):
            await self.select_team_size_callback(update, context)
        elif data == "join_game_1v1":
            await self.join_game_1v1_callback(update, context)
        elif data.startswith("join_team_"):
            await self.join_team_callback(update, context)
        elif data == "start_teams_game":
            await self.start_teams_game_callback(update, context)
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
        application.add_handler(CommandHandler("approve", self.approve_command)) # Still keep as a fallback
        application.add_handler(CallbackQueryHandler(self.callback_query_handler))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

    def run_bot(self, token: str):
        """Run the bot."""
        self.application = Application.builder().token(token).build()
        self.setup_handlers(self.application)
        
        print("Bot is running...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)

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
