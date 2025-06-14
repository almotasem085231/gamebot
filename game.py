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
 {"name": "علم الفلبين", "desc": "أزرق، أحمر، مثلث أبيض مع نجمة وشمس، يرمز للحرية", "link": "https://www.com/search?q=علم+الفلبين"},
 {"name": "علم فيتنام", "desc": "أحمر مع نجمة صفراء في المنتصف، يرمز للقيادة الشيوعية", "link": "https://www.google.com/search?q=علم+فيتنام"},

 {"name": "علم البرازيل", "desc": "أخضر مع معين أصفر وكرة زرقاء مع شعار ونجوم تمثل السماء", "link": "https://www.google.com/search?q=علم+البرازيل"},
 {"name": "علم الأرجنتين", "desc": "أزرق فاتح وأبيض مع شمس ذهبية، يرمز للحرية", "link": "https://www.google.com/search?q=علم+الأرجنتين"},
 {"name": "علم المكسيك", "desc": "أخضر وأبيض وأحمر مع نسر يأكل أفعى، يرمز للأسطورة الأزتيكية", "link": "https://www.google.com/search?q=علم+المكسيك"},
 {"name": "علم كوبا", "desc": "خمسة خطوط زرقاء وبيضاء مع مثلث أحمر ونجمة بيضاء، يرمز للحرية", "link": "https://www.google.com/search?q=علم+كوبا"},

 {"name": "علم جنوب أفريقيا", "desc": "أخضر، أسود، أصفر، أزرق، وأبيض وأحمر، يرمز للوحدة والتنوع", "link": "https://www.google.com/search?q=علم+جنوب+إفريقيا"},
 {"name": "علم نيجيريا", "desc": "أخضر، أبيض، أخضر، يرمز للزراعة والسلام", "link": "https://www.google.com/search?q=علم+نيجيريا"},
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

    async def get_team_for_player(self, game: Dict, user_id: int) -> Optional[str]:
        """Helper to get the team name for a given user ID."""
        for team_name, members in game['teams'].items():
            if user_id in [m['id'] for m in members]:
                return team_name
        return None

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
            'scores': {},  # Player-specific scores for 1v1
            'team_scores': {'blue': 0, 'red': 0}, # Add team scores
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
                await query.answer(f"أنت مشترك بالفعل في الفريق {'الأزرق' if existing_team_name == 'blue' else 'الأحمر'}!", show_alert=True)
                return

        # Check team capacity
        if len(game['teams'][team_name]) >= game['team_size']:
            await query.answer(f"الفريق {'الأزرق' if team_name == 'blue' else 'الأحمر'} ممتلئ!", show_alert=True)
            return

        game['teams'][team_name].append({'id': user_id, 'name': username})
        # Keep game['players'] flat for easier iteration if needed for general player handling
        game['players'].append({'id': user_id, 'name': username, 'team': team_name})
        game['scores'][user_id] = 0 # Initialize score for each player individually (will aggregate for team_scores)

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
            f"✅ **{username} انضم للفريق {'الأزرق' if team_name == 'blue' else 'الأحمر'}!**\n\n"
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
        await self.start_round_1v1(chat_id, context) # Changed to start_round_1v1 for clarity

    async def start_game_teams(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE):
        game = games[chat_id]
        game['status'] = 'playing'

        # Assign a single character per team
        category = game['selected_category']
        blue_character = random.choice(CHARACTERS[category])
        # Ensure red character is different from blue character
        remaining_characters = [c for c in CHARACTERS[category] if c['name'] != blue_character['name']]
        if not remaining_characters: # Fallback if only one character is available
            remaining_characters = CHARACTERS[category]
        red_character = random.choice(remaining_characters)

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
                        f"⚠️ لم أتمكن من إرسال رسالة خاصة إلى {player['name']} في الفريق {'الأزرق' if team_name == 'blue' else 'الأحمر'}. "
                        "الرجاء التأكد من أن جميع اللاعبين قد بدأوا محادثة معي أولاً! سيتم إلغاء اللعبة."
                    )
                    del games[chat_id]
                    return

        await context.bot.send_message(chat_id, "🚀 اللعبة بدأت بين الفرق!")
        await asyncio.sleep(2)
        await self.start_round_teams(chat_id, context) # Start the first round for teams

    async def start_round_1v1(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE):
        game = games[chat_id]
        if game['round'] > game['max_rounds']:
            await self.end_game_1v1(chat_id, context)
            return

        current_player = game['players'][game['current_turn']]
        opponent_player = game['players'][1 - game['current_turn']] # The other player
        opponent_character = game['characters'][opponent_player['id']]

        game['question_asker'] = current_player['id']
        game['answerer_id'] = opponent_player['id']
        game['waiting_for_answer'] = True
        game['pending_guess_confirmation'] = None # Clear any previous pending confirmation

        await context.bot.send_message(
            chat_id,
            f"**الجولة {game['round']}**: دور اللاعب {current_player['name']} لسؤال اللاعب {opponent_player['name']}.\n"
            f"يا {current_player['name']}، اسأل سؤال *بنعم/لا* عن شخصية {opponent_player['name']} المخفية."
        )
        await context.bot.send_message(
            chat_id,
            f"يا {opponent_player['name']}، عندما يسألك {current_player['name']}، أجب بـ `نعم` أو `لا` فقط."
        )


    async def start_round_teams(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE):
        game = games[chat_id]
        if game['round'] > game['max_rounds']:
            await self.end_game_teams(chat_id, context)
            return

        current_team_name = game['current_team_turn']
        opponent_team_name = 'red' if current_team_name == 'blue' else 'blue'

        current_team_members = game['teams'][current_team_name]
        opponent_team_members = game['teams'][opponent_team_name]
        opponent_team_character = game['team_characters'][opponent_team_name]

        game['question_asker_team'] = current_team_name # Track which team asks
        game['answerer_team'] = opponent_team_name # Track which team answers
        game['waiting_for_answer'] = True
        game['pending_guess_confirmation'] = None

        current_team_names_str = ", ".join([p['name'] for p in current_team_members])
        opponent_team_names_str = ", ".join([p['name'] for p in opponent_team_members])

        await context.bot.send_message(
            chat_id,
            f"**الجولة {game['round']}**: دور الفريق {'الأزرق' if current_team_name == 'blue' else 'الأحمر'} ({current_team_names_str}) لسؤال الفريق {'الأزرق' if opponent_team_name == 'blue' else 'الأحمر'} ({opponent_team_names_str}).\n"
            f"يا فريق {'الأزرق' if current_team_name == 'blue' else 'الأحمر'}، اسألوا سؤال *بنعم/لا* عن شخصية الفريق الخصم المخفية."
        )
        await context.bot.send_message(
            chat_id,
            f"يا فريق {'الأزرق' if opponent_team_name == 'blue' else 'الأحمر'}، عندما يُسأل فريقكم، أجب بـ `نعم` أو `لا` فقط في المجموعة. *فقط أحد أعضاء الفريق يجيب*."
        )


    async def end_game_1v1(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE):
        game = games.pop(chat_id, None)
        if not game:
            return

        winner = None
        highest_score = -1
        # Determine winner based on individual scores
        for player_id, score in game['scores'].items():
            if score > highest_score:
                highest_score = score
                winner = next((p['name'] for p in game['players'] if p['id'] == player_id), "لاعب غير معروف")
            elif score == highest_score and winner:
                # Handle ties - for simplicity, let's just pick one or declare a tie.
                winner = "تعادل" # Or list both players

        if winner == "تعادل":
            result_message = "اللعبة انتهت بالتعادل!"
        elif winner:
            result_message = f"اللعبة انتهت! الفائز هو: *{winner}* برصيد *{highest_score}* نقطة!"
        else:
            result_message = "اللعبة انتهت. لم يتم تسجيل نقاط."

        await context.bot.send_message(chat_id, result_message, parse_mode='Markdown')
        logger.info(f"Game in chat {chat_id} ended. Winner: {winner}")

        # Offer to play again
        keyboard = [[
            InlineKeyboardButton("نعم، لنبدأ لعبة جديدة!", callback_data='start_new_game'),
            InlineKeyboardButton("لا، شكرا", callback_data='no_thanks')
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(chat_id, "هل ترغب في بدء لعبة جديدة؟", reply_markup=reply_markup)


    async def end_game_teams(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE):
        game = games.pop(chat_id, None)
        if not game:
            return

        blue_score = game['team_scores'].get('blue', 0)
        red_score = game['team_scores'].get('red', 0)

        result_message = ""
        if blue_score > red_score:
            result_message = f"اللعبة انتهت! فاز الفريق الأزرق برصيد {blue_score} نقاط مقابل {red_score} نقطة!"
        elif red_score > blue_score:
            result_message = f"اللعبة انتهت! فاز الفريق الأحمر برصيد {red_score} نقاط مقابل {blue_score} نقطة!"
        else:
            result_message = f"اللعبة انتهت بالتعادل! كلا الفريقين لديهما {blue_score} نقاط."

        await context.bot.send_message(chat_id, result_message, parse_mode='Markdown')
        logger.info(f"Team game in chat {chat_id} ended. Scores: Blue={blue_score}, Red={red_score}")

        # Offer to play again
        keyboard = [[
            InlineKeyboardButton("نعم، لنبدأ لعبة جديدة!", callback_data='start_new_game'),
            InlineKeyboardButton("لا، شكرا", callback_data='no_thanks')
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(chat_id, "هل ترغب في بدء لعبة جديدة؟", reply_markup=reply_markup)


    async def cancel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Cancels the current game."""
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id

        if chat_id in games:
            game = games.get(chat_id)
            if user_id != game['creator_id'] and not await self.is_admin(chat_id, user_id, context):
                await update.message.reply_text("فقط من بدأ اللعبة أو الأدمن يمكنه إلغاء اللعبة.")
                return

            del games[chat_id]
            await update.message.reply_text(
                "لقد ألغيت اللعبة الحالية."
            )
            # Ask if the user wants to play again
            keyboard = [[
                InlineKeyboardButton("نعم، لنبدأ لعبة جديدة!", callback_data='start_new_game'),
                InlineKeyboardButton("لا، شكرا", callback_data='no_thanks')
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("هل ترغب في بدء لعبة جديدة؟", reply_markup=reply_markup)
            logger.info(f"Game in chat {chat_id} cancelled by user {user_id}.")
        else:
            await update.message.reply_text("لا توجد لعبة جارية لتلغيها.")

    async def rules_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Explains the game rules."""
        await update.message.reply_text(
            "قواعد اللعبة:\n"
            "• لبدء لعبة جديدة، استخدم `/start` (يجب أن تكون أدمن).\n"
            "• اختر الفئة ونمط اللعبة (1 ضد 1 أو فرق).\n"
            "• في وضع 1 ضد 1: كل لاعب يمتلك شخصية ويحاول تخمين شخصية الخصم عن طريق أسئلة نعم/لا.\n"
            "• في وضع الفرق: كل فريق يمتلك شخصية ويحاول تخمين شخصية الفريق الخصم.\n"
            "• `نعم` أو `لا` للإجابة على الأسئلة.\n"
            "• لتخمين الإجابة: اكتب الإجابة مباشرة.\n"
            "• الأوامر المتاحة:\n"
            "`/start` - لبدء لعبة جديدة (للأدمن).\n"
            "`/cancel` - لإلغاء اللعبة الحالية (لمنشئ اللعبة أو الأدمن).\n"
            "`/score` - لعرض نتائج اللعبة.\n"
            "`/forfeit` - للاستسلام في الجولة الحالية وكشف الإجابة.\n"
            "`/approve` - (في كلا الوضعين) للإقرار بصحة التخمين أو منح نقطة للخصم وإنهاء الجولة.\n"
            "حظا سعيدا!"
        )
        logger.info(f"User {update.effective_user.id} requested rules.")

    async def score_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Shows the current game scores."""
        chat_id = update.effective_chat.id
        game = games.get(chat_id)

        if not game or game.get('status') == 'waiting_category_selection':
            await update.message.reply_text("لا توجد لعبة نشطة أو لم تبدأ بعد لعرض النتائج.")
            return

        if game['game_type'] == '1v1':
            score_message = "نتائج اللعبة (1 ضد 1):\n"
            if game['players']:
                for player in game['players']:
                    score = game['scores'].get(player['id'], 0)
                    score_message += f"*{player['name']}:* {score} نقاط\n"
            else:
                score_message += "لا توجد لاعبين بعد."
        elif game['game_type'] == 'teams':
            blue_score = game['team_scores'].get('blue', 0)
            red_score = game['team_scores'].get('red', 0)
            score_message = (
                f"نتائج اللعبة (فرق):\n"
                f"🔵 الفريق الأزرق: *{blue_score}* نقاط\n"
                f"🔴 الفريق الأحمر: *{red_score}* نقاط\n\n"
            )
        await update.message.reply_text(score_message, parse_mode='Markdown')


    async def forfeit_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Allows the current asking player/team to forfeit the round."""
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name
        game = games.get(chat_id)

        if not game or game.get('status') != 'playing':
            await update.message.reply_text("لا توجد لعبة نشطة حالياً.")
            return

        if game['game_type'] == '1v1':
            current_player = game['players'][game['current_turn']]
            opponent_player = game['players'][1 - game['current_turn']]
            
            # Only the current asking player can forfeit in 1v1 (the one who's supposed to guess or ask)
            if user_id != current_player['id']:
                await update.message.reply_text("لا يمكنك الاستسلام الآن، ليس دورك للسؤال/التخمين.")
                return

            revealed_character = game['characters'][opponent_player['id']]
            await context.bot.send_message(
                chat_id,
                f"*{current_player['name']}* استسلم في هذه الجولة!\n"
                f"الشخصية المخفية لـ *{opponent_player['name']}* كانت: *{revealed_character['name']}* ({revealed_character['desc']})."
                f"\n🔗 [معلومات إضافية]({revealed_character['link']})",
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
            # No points are awarded for forfeit in 1v1, it's just to reveal and move on
            game['waiting_for_answer'] = False
            game['pending_guess_confirmation'] = None

            game['round'] += 1
            game['current_turn'] = 1 - game['current_turn'] # Opponent gets to ask next
            await self.start_round_1v1(chat_id, context)

        elif game['game_type'] == 'teams':
            current_team_name = game['current_team_turn']
            opponent_team_name = 'red' if current_team_name == 'blue' else 'blue'

            # Check if the user is part of the current asking team
            user_in_current_team = await self.get_team_for_player(game, user_id) == current_team_name

            if not user_in_current_team:
                await update.message.reply_text(f"فقط أعضاء الفريق {'الأزرق' if current_team_name == 'blue' else 'الأحمر'} يمكنهم الاستسلام في دورهم.")
                return

            # Award point to opponent team because the current asking team forfeited (couldn't guess or ask correctly)
            game['team_scores'][opponent_team_name] += 1
            revealed_character = game['team_characters'][opponent_team_name] # Reveal opponent's character as the asking team failed to guess it

            await context.bot.send_message(
                chat_id,
                f"الفريق {'الأزرق' if current_team_name == 'blue' else 'الأحمر'} استسلم في هذه الجولة عن طريق *{user_name}*!\n"
                f"النقاط تذهب للفريق {'الأزرق' if opponent_team_name == 'blue' else 'الأحمر'}!\n"
                f"الشخصية المخفية للفريق {'الأزرق' if opponent_team_name == 'blue' else 'الأحمر'} كانت: *{revealed_character['name']}* ({revealed_character['desc']})."
                f"\n🔗 [معلومات إضافية]({revealed_character['link']})",
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
            game['waiting_for_answer'] = False
            game['pending_guess_confirmation'] = None

            game['round'] += 1
            game['current_team_turn'] = opponent_team_name # The team that just got the point gets to ask next
            await self.start_round_teams(chat_id, context) # This function will check if max rounds are reached


    async def approve_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Allows any player/team member to use /approve, which signifies a surrender of the round
        and grants a point to the opponent, ending the current round.
        """
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name
        game = games.get(chat_id)

        if not game or game.get('status') != 'playing':
            await update.message.reply_text("لا توجد لعبة نشطة حالياً.")
            return

        if game['game_type'] == '1v1':
            # In 1v1, the user using /approve is the one whose character is being guessed,
            # or who is simply conceding the round. The point goes to their opponent.
            # Find the player using /approve
            approver_player = None
            opponent_player = None
            for player in game['players']:
                if player['id'] == user_id:
                    approver_player = player
                else:
                    opponent_player = player
            
            if not approver_player or not opponent_player:
                await update.message.reply_text("يبدو أن هناك مشكلة في تحديد اللاعبين في هذه اللعبة الفردية.")
                return

            # Grant point to the opponent
            game['scores'][opponent_player['id']] += 1
            
            # Reveal the character of the player who approved (as they are conceding the round)
            revealed_character = game['characters'][approver_player['id']]

            await context.bot.send_message(
                chat_id,
                f"✅ *{approver_player['name']}* وافق على الإجابة عن طريق استخدام `/approve`!\n"
                f"النقطة تذهب إلى *{opponent_player['name']}*!\n"
                f"الشخصية المخفية لـ *{approver_player['name']}* كانت: *{revealed_character['name']}* ({revealed_character['desc']})."
                f"\n🔗 [معلومات إضافية]({revealed_character['link']})",
                parse_mode='Markdown',
                disable_web_page_preview=True
            )

            game['waiting_for_answer'] = False
            game['pending_guess_confirmation'] = None

            game['round'] += 1
            # Next turn goes to the player who just received the point (opponent_player)
            # Find index of opponent_player
            opponent_index = next((i for i, p in enumerate(game['players']) if p['id'] == opponent_player['id']), 0)
            game['current_turn'] = opponent_index
            await self.start_round_1v1(chat_id, context)

        elif game['game_type'] == 'teams':
            # Get the team of the user who issued /approve
            approver_team_name = await self.get_team_for_player(game, user_id)

            if not approver_team_name:
                await update.message.reply_text("أنت لست جزءاً من أي فريق في هذه اللعبة.")
                return

            # Determine the opponent team
            opponent_team_name = 'red' if approver_team_name == 'blue' else 'blue'

            # Grant point to the opponent team
            game['team_scores'][opponent_team_name] += 1

            # Reveal the character of the team that approved (as they are 'surrendering' the guess)
            revealed_character = game['team_characters'][approver_team_name]

            await context.bot.send_message(
                chat_id,
                f"✅ الفريق {'الأزرق' if approver_team_name == 'blue' else 'الأحمر'} وافق على الإجابة عن طريق *{user_name}*!\n"
                f"النقاط تذهب للفريق {'الأزرق' if opponent_team_name == 'blue' else 'الأحمر'}!\n"
                f"الشخصية المخفية للفريق {'الأزرق' if approver_team_name == 'blue' else 'الأحمر'} كانت: *{revealed_character['name']}* ({revealed_character['desc']})."
                f"\n🔗 [معلومات إضافية]({revealed_character['link']})",
                parse_mode='Markdown',
                disable_web_page_preview=True
            )

            game['waiting_for_answer'] = False
            game['pending_guess_confirmation'] = None

            # Move to next round
            game['round'] += 1
            # The team that just got the point gets to ask next (opponent_team)
            game['current_team_turn'] = opponent_team_name
            await self.start_round_teams(chat_id, context) # This function will check if max rounds are reached


    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        text = update.message.text.strip()
        game = games.get(chat_id)

        if not game or game.get('status') != 'playing':
            return # Not in an active game or game not in playing state

        # Handle "yes" or "no" answers
        if game['waiting_for_answer']:
            if game['game_type'] == '1v1':
                if user_id != game['answerer_id']:
                    # Only the designated answerer can reply with yes/no
                    return

                if text.lower() == 'نعم' or text.lower() == 'لا':
                    game['waiting_for_answer'] = False
                    await context.bot.send_message(
                        chat_id,
                        f"الإجابة من *{update.effective_user.first_name}*: **{text.upper()}**.\n"
                        f"يا {game['players'][game['current_turn']]['name']}، يمكنك الآن تخمين الشخصية أو طرح سؤال آخر في الجولة القادمة.\n"
                        f"للتخمين اكتب الاسم مباشرة، أو انتظر للجولة القادمة."
                    )
                    # For simplicity, if no guess is made after an answer, the turn passes.
                    await asyncio.sleep(2) # Give a moment for user to see the answer
                    game['round'] += 1
                    game['current_turn'] = 1 - game['current_turn'] # Switch turn
                    await self.start_round_1v1(chat_id, context) # Start next round automatically

            elif game['game_type'] == 'teams':
                # Check if the user is part of the team whose turn it is to answer
                user_team = await self.get_team_for_player(game, user_id)
                if user_team != game['answerer_team']:
                    return # Only a member of the answering team can reply

                if text.lower() == 'نعم' or text.lower() == 'لا':
                    game['waiting_for_answer'] = False
                    await context.bot.send_message(
                        chat_id,
                        f"الإجابة من فريق {'الأزرق' if user_team == 'blue' else 'الأحمر'} عن طريق *{update.effective_user.first_name}*: **{text.upper()}**.\n"
                        f"الآن، يا فريق {'الأزرق' if game['question_asker_team'] == 'blue' else 'الأحمر'}، يمكنكم تخمين الشخصية أو طرح سؤال آخر في الجولة القادمة."
                    )
                    await asyncio.sleep(2)
                    game['round'] += 1
                    game['current_team_turn'] = game['answerer_team'] # The team that just answered will be the one asking next.
                    await self.start_round_teams(chat_id, context)

        # Handle guesses (for both 1v1 and teams) - only if not waiting for a yes/no answer
        elif not game['waiting_for_answer']: # This condition means we're expecting a guess or command
            if game['game_type'] == '1v1':
                current_player = game['players'][game['current_turn']]
                opponent_player = game['players'][1 - game['current_turn']]

                if user_id == current_player['id']: # Only the asking player can guess
                    if text.lower() == game['characters'][opponent_player['id']]['name'].lower():
                        await context.bot.send_message(
                            chat_id,
                            f"🎉 تهانينا! *{update.effective_user.first_name}* خمن الإجابة الصحيحة: *{game['characters'][opponent_player['id']]['name']}*!"
                        )
                        game['scores'][user_id] += 1
                        game['waiting_for_answer'] = False
                        game['pending_guess_confirmation'] = None
                        game['round'] += 1
                        game['current_turn'] = game['current_turn'] # Player who guessed correctly keeps turn
                        await self.start_round_1v1(chat_id, context)
                    else:
                        await context.bot.send_message(
                            chat_id,
                            f"تخمين خاطئ يا *{update.effective_user.first_name}*! حاول مرة أخرى في جولة قادمة أو اسأل سؤالاً آخر."
                        )
                        game['waiting_for_answer'] = False
                        game['pending_guess_confirmation'] = None
                        game['round'] += 1
                        game['current_turn'] = 1 - game['current_turn'] # Turn passes to the other player on wrong guess
                        await self.start_round_1v1(chat_id, context)

            elif game['game_type'] == 'teams':
                # Only a member of the current asking team can make a guess
                user_team = await self.get_team_for_player(game, user_id)
                current_asking_team = game['question_asker_team']

                if user_team != current_asking_team:
                    return # Only members of the asking team can guess

                opponent_team_name = game['answerer_team'] # The team whose character is being guessed
                opponent_character = game['team_characters'][opponent_team_name]

                if text.lower() == opponent_character['name'].lower():
                    await context.bot.send_message(
                        chat_id,
                        f"🎉 تهانينا! فريق {'الأزرق' if current_asking_team == 'blue' else 'الأحمر'} خمن الإجابة الصحيحة: *{opponent_character['name']}*!"
                    )
                    game['team_scores'][current_asking_team] += 1 # Point to the team that guessed correctly
                    game['waiting_for_answer'] = False
                    game['pending_guess_confirmation'] = None
                    game['round'] += 1
                    game['current_team_turn'] = current_asking_team # The team that guessed correctly gets to ask again
                    await self.start_round_teams(chat_id, context)
                else:
                    await context.bot.send_message(
                        chat_id,
                        f"تخمين خاطئ يا فريق {'الأزرق' if current_asking_team == 'blue' else 'الأحمر'}! حاولوا مرة أخرى في جولة قادمة أو اسألوا سؤالاً آخر."
                    )
                    game['waiting_for_answer'] = False
                    game['pending_guess_confirmation'] = None
                    game['round'] += 1
                    game['current_team_turn'] = opponent_team_name # Turn passes to the other team on wrong guess
                    await self.start_round_teams(chat_id, context)


    async def callback_query_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

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
        elif data == "start_new_game":
            await self.start_command(update, context) # Re-use start command to begin new game flow
        elif data == "no_thanks":
            await query.edit_message_text("تمام، ربما في وقت لاحق!")
            logger.info(f"User {query.from_user.id} declined to play again.")


    def run_bot(self, token: str):
        """Run the bot."""
        self.application = Application.builder().token(token).build()
        
        # Handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("cancel", self.cancel_command))
        self.application.add_handler(CommandHandler("rules", self.rules_command))
        self.application.add_handler(CommandHandler("score", self.score_command))
        self.application.add_handler(CommandHandler("forfeit", self.forfeit_command))
        self.application.add_handler(CommandHandler("approve", self.approve_command)) # Handler for the new /approve command
        
        self.application.add_handler(CallbackQueryHandler(self.callback_query_handler))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

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
    bot.run_bot(bot_token)
