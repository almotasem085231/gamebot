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

        all_teams_full = (len(game['teams']['blue']) == game['team_size'] and len(game['teams']['red']) == game['team_size'])

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
            f"الفريق الأحمر ({len(game['teams']['red'])}/{game['team_size']}): {', '.join(red_players_names) if red_players_names else 'لا يوجد لاعبون'}\n\n"
            + ("جميع الفرق اكتملت! اضغط على 'بدء اللعبة' لبدء الجولة." if all_teams_full else "في انتظار اكتمال الفرق..."),
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
                'category': category,
                'character': character,
                'name': character['name'],
                'desc': character['desc'],
                'link': character['link']
            }
            try:
                await context.bot.send_message(
                    chat_id=player['id'],
                    text=f"🎭 **شخصيتك في اللعبة:**\n\n**الاسم:** {character['name']}\n"
                         f"**الفئة:** {category}\n**الوصف:** {character['desc']}\n\n"
                         f"🔗 [معلومات إضافية]({character['link']})\n\n⚠️ احتفظ بهذه المعلومات سرية!",
                    parse_mode='Markdown',
                    disable_web_page_preview=True
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
            'category': category,
            'character': blue_character,
            'name': blue_character['name'],
            'desc': blue_character['desc'],
            'link': blue_character['link']
        }
        game['team_characters']['red'] = {
            'category': category,
            'character': red_character,
            'name': red_character['name'],
            'desc': red_character['desc'],
            'link': red_character['link']
        }

        # Notify each team about their character
        for player in game['teams']['blue']:
            try:
                await context.bot.send_message(
                    chat_id=player['id'],
                    text=f"🔵 **شخصية فريقك الأزرق:**\n\n**الاسم:** {blue_character['name']}\n"
                         f"**الفئة:** {category}\n**الوصف:** {blue_character['desc']}\n\n"
                         f"🔗 [معلومات إضافية]({blue_character['link']})\n\n⚠️ احتفظ بهذه المعلومات سرية ضمن فريقك!",
                    parse_mode='Markdown',
                    disable_web_page_preview=True
                )
            except Exception as e:
                logger.error(f"Failed to send private message to blue team player {player['id']}: {e}")
                await context.bot.send_message(
                    chat_id,
                    f"⚠️ لم أتمكن من إرسال رسالة خاصة إلى {player['name']} في الفريق الأزرق. "
                    "الرجاء التأكد من أنك بدأت محادثة معي أولاً! سيتم إلغاء اللعبة."
                )
                del games[chat_id]
                return

        for player in game['teams']['red']:
            try:
                await context.bot.send_message(
                    chat_id=player['id'],
                    text=f"🔴 **شخصية فريقك الأحمر:**\n\n**الاسم:** {red_character['name']}\n"
                         f"**الفئة:** {category}\n**الوصف:** {red_character['desc']}\n\n"
                         f"🔗 [معلومات إضافية]({red_character['link']})\n\n⚠️ احتفظ بهذه المعلومات سرية ضمن فريقك!",
                    parse_mode='Markdown',
                    disable_web_page_preview=True
                )
            except Exception as e:
                logger.error(f"Failed to send private message to red team player {player['id']}: {e}")
                await context.bot.send_message(
                    chat_id,
                    f"⚠️ لم أتمكن من إرسال رسالة خاصة إلى {player['name']} في الفريق الأحمر. "
                    "الرجاء التأكد من أنك بدأت محادثة معي أولاً! سيتم إلغاء اللعبة."
                )
                del games[chat_id]
                return

        await context.bot.send_message(chat_id, "🚀 اللعبة بدأت بين الفرق!")
        await asyncio.sleep(2)
        await self.start_round_teams(chat_id, context)

    async def start_round(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE):
        game = games[chat_id]
        game['current_turn'] = 0 # Reset turn for new round
        game['waiting_for_answer'] = False
        game['question_asker'] = None
        game['answerer_id'] = None
        game['pending_guess_confirmation'] = None

        if game['game_type'] == '1v1':
            player1_name = game['players'][0]['name']
            player2_name = game['players'][1]['name']
            
            # Determine who asks first based on round number for fairness
            if game['round'] % 2 != 0: # Odd rounds, player 1 asks
                game['question_asker'] = game['players'][0]['id']
                game['answerer_id'] = game['players'][1]['id']
                first_asker_name = player1_name
                first_answerer_name = player2_name
            else: # Even rounds, player 2 asks
                game['question_asker'] = game['players'][1]['id']
                game['answerer_id'] = game['players'][0]['id']
                first_asker_name = player2_name
                first_answerer_name = player1_name

            await context.bot.send_message(
                chat_id,
                f"الجولة {game['round']}/{game['max_rounds']} تبدأ!\n\n"
                f"**{first_asker_name}**، يرجى طرح سؤالك الأول بنعم/لا حول شخصية **{first_answerer_name}**."
                f" أو قم بتخمين شخصية خصمك باستخدام الأمر /guess [الاسم] [الفئة]."
                f"\n\n**{first_answerer_name}**، استعد للإجابة!"
                "\n\nيمكنك استخدام /forfeit لإنهاء اللعبة في أي وقت."
                "\n\nيمكنك استخدام /score لمعرفة النقاط."
,
                parse_mode='Markdown'
            )
        elif game['game_type'] == 'teams':
            await self.start_round_teams(chat_id, context)
    
    async def start_round_teams(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE):
        game = games[chat_id]
        game['current_turn'] = 0
        game['waiting_for_answer'] = False
        game['question_asker'] = None
        game['answerer_id'] = None
        game['pending_guess_confirmation'] = None

        # Determine starting team for the round
        starting_team = 'blue' if game['round'] % 2 != 0 else 'red'
        game['current_team_turn'] = starting_team

        # Select a random player from the starting team to be the first question_asker
        first_asker_player = random.choice(game['teams'][starting_team])
        game['question_asker'] = first_asker_player['id']

        # The other team is the answerer
        answerer_team = 'red' if starting_team == 'blue' else 'blue'
        # The answerer_id is not a single person in teams, it's the team
        # We will use the question_asker to determine who needs to answer
        game['answerer_team'] = answerer_team 
        game['question_asker_name'] = first_asker_player['name']

        await context.bot.send_message(
            chat_id,
            f"الجولة {game['round']}/{game['max_rounds']} تبدأ!\n\n"
            f"الفريق {game['current_team_turn']} هو من يبدأ.\n"
            f"**{first_asker_player['name']}** من الفريق {game['current_team_turn']}، يرجى طرح سؤالكم الأول بنعم/لا حول شخصية الفريق الآخر. "
            "أو قم بتخمين شخصية الفريق الخصم باستخدام الأمر /guess [الاسم] [الفئة]."
            "\n\nيمكنك استخدام /forfeit لإنهاء اللعبة في أي وقت."
            "\n\nيمكنك استخدام /score لمعرفة النقاط."
,
            parse_mode='Markdown'
        )


    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        message_text = update.message.text

        game = games.get(chat_id)

        if not game or game.get('status') != 'playing':
            return # Ignore messages if no game is playing

        if game['game_type'] == '1v1':
            await self.handle_message_1v1(chat_id, user_id, message_text, game, context)
        elif game['game_type'] == 'teams':
            await self.handle_message_teams(chat_id, user_id, message_text, game, context)

    async def handle_message_1v1(self, chat_id: int, user_id: int, message_text: str, game: Dict, context: ContextTypes.DEFAULT_TYPE):
        player_ids = [p['id'] for p in game['players']]
        
        # Only allow current question_asker or answerer to send messages
        if user_id not in player_ids:
            return

        if game['waiting_for_answer']:
            if user_id == game['answerer_id']:
                if message_text.lower() in ['نعم', 'yes']:
                    await context.bot.send_message(chat_id, f"✅ **{game['players'][[p['id'] for p in game['players']].index(game['answerer_id'])]['name']}** يقول: نعم!")
                    game['waiting_for_answer'] = False
                    await self.next_turn(chat_id, context)
                elif message_text.lower() in ['لا', 'no']:
                    await context.bot.send_message(chat_id, f"❌ **{game['players'][[p['id'] for p in game['players']].index(game['answerer_id'])]['name']}** يقول: لا!")
                    game['waiting_for_answer'] = False
                    await self.next_turn(chat_id, context)
                else:
                    await context.bot.send_message(chat_id, "الرجاء الإجابة بـ 'نعم' أو 'لا' فقط.")
            else:
                await context.bot.send_message(chat_id, "الرجاء الانتظار حتى يجيب الخصم على السؤال.")
        elif user_id == game['question_asker']:
            await context.bot.send_message(chat_id, "لقد طرحت سؤالاً: " + message_text + "\nالرجاء الانتظار حتى يجيب خصمك.")
            game['waiting_for_answer'] = True

    async def handle_message_teams(self, chat_id: int, user_id: int, message_text: str, game: Dict, context: ContextTypes.DEFAULT_TYPE):
        # Check if the user is part of the game
        is_player = False
        for team_name in game['teams']:
            if user_id in [p['id'] for p in game['teams'][team_name]]:
                is_player = True
                break
        
        if not is_player:
            return # Ignore messages if not a player

        current_asker_team_name = game['current_team_turn']
        answerer_team_name = 'red' if current_asker_team_name == 'blue' else 'blue'

        user_is_question_asker_team = user_id in [p['id'] for p in game['teams'][current_asker_team_name]]
        user_is_answerer_team = user_id in [p['id'] for p in game['teams'][answerer_team_name]]

        if game['waiting_for_answer']:
            if user_is_answerer_team:
                if message_text.lower() in ['نعم', 'yes']:
                    await context.bot.send_message(chat_id, f"✅ الفريق {answerer_team_name} يقول: نعم!")
                    game['waiting_for_answer'] = False
                    await self.next_turn_teams(chat_id, context)
                elif message_text.lower() in ['لا', 'no']:
                    await context.bot.send_message(chat_id, f"❌ الفريق {answerer_team_name} يقول: لا!")
                    game['waiting_for_answer'] = False
                    await self.next_turn_teams(chat_id, context)
                else:
                    await context.bot.send_message(chat_id, "الرجاء الإجابة بـ 'نعم' أو 'لا' فقط.")
            elif user_is_question_asker_team:
                await context.bot.send_message(chat_id, "الرجاء الانتظار حتى يجيب الفريق الخصم على السؤال.")
            else:
                return # Message from a non-involved player during answer phase
        elif user_is_question_asker_team:
            # Only the designated question asker can ask
            if user_id == game['question_asker']:
                await context.bot.send_message(chat_id, "لقد طرحت سؤالاً: " + message_text + "\nالرجاء الانتظار حتى يجيب الفريق الخصم.")
                game['waiting_for_answer'] = True
            else:
                await context.bot.send_message(chat_id, "فقط **" + game['question_asker_name'] + "** يمكنه طرح السؤال في هذه الجولة.")
        else:
            return # Ignore messages from the answerer team or other players when not waiting for an answer

    async def next_turn(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE):
        game = games[chat_id]
        
        # Increment turn
        game['current_turn'] += 1

        player_ids = [p['id'] for p in game['players']]
        player_names = [p['name'] for p in game['players']]

        # Switch roles: current answerer becomes asker, current asker becomes answerer
        game['question_asker'], game['answerer_id'] = game['answerer_id'], game['question_asker']
        
        current_asker_name = game['players'][player_ids.index(game['question_asker'])]['name']
        current_answerer_name = game['players'][player_ids.index(game['answerer_id'])]['name']

        await context.bot.send_message(
            chat_id,
            f"الان دور **{current_asker_name}** لطرح سؤال حول شخصية **{current_answerer_name}**. "
            f"أو قم بتخمين شخصية خصمك باستخدام الأمر /guess [الاسم] [الفئة]."
        )

    async def next_turn_teams(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE):
        game = games[chat_id]

        # Switch current team turn
        game['current_team_turn'] = 'red' if game['current_team_turn'] == 'blue' else 'blue'
        
        # Select a random player from the new current team to be the question_asker
        new_asker_player = random.choice(game['teams'][game['current_team_turn']])
        game['question_asker'] = new_asker_player['id']
        game['question_asker_name'] = new_asker_player['name']

        # The other team is now the answerer team
        game['answerer_team'] = 'red' if game['current_team_turn'] == 'blue' else 'blue'

        await context.bot.send_message(
            chat_id,
            f"الان دور الفريق **{game['current_team_turn']}**.\n"
            f"**{new_asker_player['name']}** من الفريق {game['current_team_turn']}، يرجى طرح سؤالكم حول شخصية الفريق الآخر. "
            "أو قم بتخمين شخصية الفريق الخصم باستخدام الأمر /guess [الاسم] [الفئة]."
        )

    async def guess_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        game = games.get(chat_id)

        if not game or game.get('status') != 'playing':
            await update.message.reply_text("لا توجد لعبة نشطة لتخمين الشخصيات!")
            return

        if game['game_type'] == '1v1':
            await self.handle_guess_1v1(update, context, chat_id, user_id, game)
        elif game['game_type'] == 'teams':
            await self.handle_guess_teams(update, context, chat_id, user_id, game)

    async def handle_guess_1v1(self, update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int, game: Dict):
        if user_id != game['question_asker']:
            await update.message.reply_text("ليس دورك للتخمين! فقط اللاعب الذي يحين دوره يمكنه التخمين.")
            return

        args = context.args
        if len(args) < 2:
            await update.message.reply_text("الرجاء استخدام: `/guess [اسم الشخصية] [الفئة]`", parse_mode='Markdown')
            return

        guessed_name = args[0]
        guessed_category = args[1]
        
        # Get the character of the answerer
        answerer_char_info = game['characters'][game['answerer_id']]

        if guessed_name.lower() == answerer_char_info['name'].lower() and \
           guessed_category.lower() == answerer_char_info['category'].lower():
            
            game['scores'][user_id] += 1
            await update.message.reply_text(
                f"🎉 **{update.effective_user.first_name} خمن بشكل صحيح!**\n\n"
                f"الشخصية كانت: **{answerer_char_info['name']}** من فئة **{answerer_char_info['category']}**.\n"
                f"🔗 [معلومات إضافية]({answerer_char_info['link']})\n\n"
                f"النقطة تذهب إلى {update.effective_user.first_name}!"
,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
            await self.end_round(chat_id, context)
        else:
            await update.message.reply_text(
                f"❌ **{update.effective_user.first_name} خمن خطأ!**\n"
                "حاول مرة أخرى في دورك القادم."
            )
            # Incorrect guess, turn passes to the other player
            await self.next_turn(chat_id, context)

    async def handle_guess_teams(self, update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int, game: Dict):
        # Check if it's the guessing team's turn and the user is the designated asker
        if user_id != game['question_asker']:
            await update.message.reply_text("ليس دور فريقك للتخمين! فقط اللاعب الذي يحين دوره يمكنه التخمين.")
            return

        args = context.args
        if len(args) < 2:
            await update.message.reply_text("الرجاء استخدام: `/guess [اسم الشخصية] [الفئة]`", parse_mode='Markdown')
            return

        guessed_name = args[0]
        guessed_category = args[1]
        
        current_asker_team_name = game['current_team_turn']
        answerer_team_name = 'red' if current_asker_team_name == 'blue' else 'blue'
        
        answerer_team_char_info = game['team_characters'][answerer_team_name]

        if guessed_name.lower() == answerer_team_char_info['name'].lower() and \
           guessed_category.lower() == answerer_team_char_info['category'].lower():
            
            # Award points to all players in the guessing team
            for player in game['teams'][current_asker_team_name]:
                game['scores'][player['id']] += 1

            await update.message.reply_text(
                f"🎉 **الفريق {current_asker_team_name} خمن بشكل صحيح!**\n\n"
                f"الشخصية كانت: **{answerer_team_char_info['name']}** من فئة **{answerer_team_char_info['category']}**.\n"
                f"🔗 [معلومات إضافية]({answerer_team_char_info['link']})\n\n"
                f"النقطة تذهب إلى الفريق {current_asker_team_name}!"
,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
            await self.end_round(chat_id, context)
        else:
            await update.message.reply_text(
                f"❌ **الفريق {current_asker_team_name} خمن خطأ!**\n"
                "حاول مرة أخرى في دوركم القادم."
            )
            # Incorrect guess, turn passes to the other team
            await self.next_turn_teams(chat_id, context)

    async def forfeit_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        game = games.get(chat_id)

        if not game:
            await update.message.reply_text("لا توجد لعبة نشطة لإنهاءها!")
            return

        if game['game_type'] == '1v1':
            player_ids = [p['id'] for p in game['players']]
            if user_id not in player_ids:
                await update.message.reply_text("أنت لست جزءًا من هذه اللعبة النشطة.")
                return

            await update.message.reply_text(f"💔 **{update.effective_user.first_name} استسلم!**\n\nاللعبة انتهت.")
            del games[chat_id]
        elif game['game_type'] == 'teams':
            user_team = None
            for team_name, players in game['teams'].items():
                if user_id in [p['id'] for p in players]:
                    user_team = team_name
                    break
            
            if not user_team:
                await update.message.reply_text("أنت لست جزءًا من هذه اللعبة النشطة.")
                return
            
            await update.message.reply_text(f"💔 **الفريق {user_team} استسلم!**\n\nاللعبة انتهت.")
            del games[chat_id]

    async def score_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        game = games.get(chat_id)

        if not game:
            await update.message.reply_text("لا توجد لعبة نشطة لعرض النتائج.")
            return

        if not game['scores']:
            await update.message.reply_text("لم يتم تسجيل أي نقاط بعد في هذه اللعبة.")
            return
        
        score_message = "📊 **النتائج الحالية:**\n\n"

        if game['game_type'] == '1v1':
            for player_id, score in game['scores'].items():
                player_name = next(p['name'] for p in game['players'] if p['id'] == player_id)
                score_message += f"**{player_name}**: {score} نقطة\n"
        elif game['game_type'] == 'teams':
            blue_team_score = sum(game['scores'].get(p['id'], 0) for p in game['teams']['blue'])
            red_team_score = sum(game['scores'].get(p['id'], 0) for p in game['teams']['red'])
            score_message += f"🔵 **الفريق الأزرق**: {blue_team_score} نقطة\n"
            score_message += f"🔴 **الفريق الأحمر**: {red_team_score} نقطة\n"
        
        await update.message.reply_text(score_message, parse_mode='Markdown')

    async def rules_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        rules_text = (
            "📜 **قواعد لعبة تخمين الشخصيات**\n\n"
            "**الهدف:** تخمين الشخصية السرية للخصم/الفريق الآخر.\n\n"
            "**كيفية اللعب:**\n"
            "1. يبدأ اللاعب/الفريق دوره بطرح سؤال يمكن الإجابة عليه بـ 'نعم' أو 'لا' فقط. (مثال: هل شخصيتك ذكر؟ هل شخصيتك من عالم الأنمي؟)\n"
            "2. بعد الإجابة، ينتقل الدور إلى اللاعب/الفريق الآخر.\n"
            "3. يمكنك محاولة تخمين الشخصية في دورك باستخدام الأمر `/guess [اسم الشخصية] [الفئة]`.\n"
            "4. إذا كان التخمين صحيحًا، تربح نقطة وتنتهي الجولة.\n"
            "5. إذا كان التخمين خاطئًا، تخسر دورك وينتقل الدور للخصم/الفريق الآخر.\n\n"
            "**الأنماط:**\n"
            "• **1 ضد 1:** لاعبان يتنافسان فرديًا. كل لاعب لديه شخصية سرية خاصة به.\n"
            "• **فرق:** فريقان (أزرق وأحمر) يتنافسان. كل فريق لديه شخصية سرية واحدة يجب على الفريق الآخر تخمينها.\n\n"
            "**الأوامر:**\n"
            "• `/start`: لبدء لعبة جديدة (يجب أن تكون أدمن في المجموعة).\n"
            "• `/guess [اسم الشخصية] [الفئة]`: لتخمين الشخصية السرية.\n"
            "• `/score`: لعرض النتائج الحالية.\n"
            "• `/forfeit`: للاستسلام وإنهاء اللعبة.\n"
            "• `/rules`: لعرض هذه القواعد.\n\n"
            "استمتع باللعب!"
        )
        await context.bot.send_message(chat_id, rules_text, parse_mode='Markdown')

    async def end_round(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE):
        game = games[chat_id]
        game['round'] += 1

        if game['round'] > game['max_rounds']:
            await self.end_game(chat_id, context)
        else:
            await context.bot.send_message(
                chat_id,
                f"انتهت الجولة {game['round'] - 1}!\n\n"
                "جارٍ بدء الجولة الجديدة..."
            )
            await asyncio.sleep(3)
            if game['game_type'] == '1v1':
                await self.start_game_1v1(chat_id, context) # Re-assign characters for next round
            elif game['game_type'] == 'teams':
                await self.start_game_teams(chat_id, context) # Re-assign characters for next round

    async def end_game(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE):
        game = games[chat_id]
        
        final_score_message = "🏆 **اللعبة انتهت! النتائج النهائية:**\n\n"

        if game['game_type'] == '1v1':
            player1 = game['players'][0]
            player2 = game['players'][1]
            score1 = game['scores'].get(player1['id'], 0)
            score2 = game['scores'].get(player2['id'], 0)

            final_score_message += f"**{player1['name']}**: {score1} نقطة\n"
            final_score_message += f"**{player2['name']}**: {score2} نقطة\n\n"

            if score1 > score2:
                final_score_message += f"🎉 **{player1['name']} يفوز باللعبة!**"
            elif score2 > score1:
                final_score_message += f"🎉 **{player2['name']} يفوز باللعبة!**"
            else:
                final_score_message += "🤝 **تعادل!**"
        elif game['game_type'] == 'teams':
            blue_team_score = sum(game['scores'].get(p['id'], 0) for p in game['teams']['blue'])
            red_team_score = sum(game['scores'].get(p['id'], 0) for p in game['teams']['red'])

            final_score_message += f"🔵 **الفريق الأزرق**: {blue_team_score} نقطة\n"
            final_score_message += f"🔴 **الفريق الأحمر**: {red_team_score} نقطة\n\n"

            if blue_team_score > red_team_score:
                final_score_message += "🎉 **الفريق الأزرق يفوز باللعبة!**"
            elif red_team_score > blue_team_score:
                final_score_message += "🎉 **الفريق الأحمر يفوز باللعبة!**"
            else:
                final_score_message += "🤝 **تعادل!**"

        await context.bot.send_message(chat_id, final_score_message, parse_mode='Markdown')
        del games[chat_id] # Clear game data

    async def cancel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        game = games.get(chat_id)

        if not game:
            await update.message.reply_text("لا توجد لعبة نشطة لإلغائها.")
            return

        # Only the creator or an admin can cancel the game
        if user_id != game['creator_id'] and not await self.is_admin(chat_id, user_id, context):
            await update.message.reply_text("فقط من بدأ اللعبة أو مسؤول في المجموعة يمكنه إلغاء اللعبة.")
            return

        await update.message.reply_text("🗑️ تم إلغاء اللعبة الحالية.")
        del games[chat_id]

    async def approve_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # This command is just a fallback to satisfy the handler, 
        # actual approval logic might be integrated elsewhere or removed.
        await update.message.reply_text("تم استلام أمر الموافقة. (هذا الأمر قد لا يكون له وظيفة محددة في اللعبة الحالية).")

    async def callback_query_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        # Acknowledge the query to remove the loading animation from the button
        await query.answer()

        if query.data.startswith("select_category_"):
            await self.select_category_callback(update, context)
        elif query.data.startswith("select_mode_"):
            await self.select_mode_callback(update, context)
        elif query.data.startswith("select_team_size_"):
            await self.select_team_size_callback(update, context)
        elif query.data == "join_game_1v1":
            await self.join_game_1v1_callback(update, context)
        elif query.data.startswith("join_team_"):
            await self.join_team_callback(update, context)
        elif query.data == "start_teams_game":
            await self.start_teams_game_callback(update, context)
        # Add more conditions for other callback data as needed

    def setup_handlers(self, application: Application):
        """Set up the bot's command and message handlers."""
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("cancel", self.cancel_command))
        application.add_handler(CommandHandler("rules", self.rules_command))
        application.add_handler(CommandHandler("score", self.score_command))
        application.add_handler(CommandHandler("forfeit", self.forfeit_command))
        application.add_handler(CommandHandler("guess", self.guess_command)) # Add guess command handler
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
    bot.run_bot(bot_token)
