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
        
        # Ensure distinct characters for each team, if possible
        all_characters_in_category = list(CHARACTERS[category])
        if len(all_characters_in_category) < 2:
            await context.bot.send_message(chat_id, "⚠️ لا توجد شخصيات كافية في هذه الفئة لبدء لعبة فرق. الرجاء اختيار فئة أخرى أو تقليل عدد الجولات.")
            del games[chat_id]
            return

        chosen_characters = random.sample(all_characters_in_category, 2)
        blue_character = chosen_characters[0]
        red_character = chosen_characters[1]

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
                        f"⚠️ لم أتمكن من إرسال رسالة خاصة إلى {player['name']} في الفريق {team_name}. "
                        "الرجاء التأكد من أن جميع اللاعبين قد بدأوا محادثة معي أولاً! سيتم إلغاء اللعبة."
                    )
                    del games[chat_id]
                    return
        
        blue_team_names = ", ".join([p['name'] for p in game['teams']['blue']])
        red_team_names = ", ".join([p['name'] for p in game['teams']['red']])

        await context.bot.send_message(
            chat_id, 
            f"🚀 اللعبة بدأت! الفرق جاهزة:\n\n"
            f"🔵 *الفريق الأزرق:* {blue_team_names}\n"
            f"🔴 *الفريق الأحمر:* {red_team_names}\n\n"
            "سيبدأ الفريق الأزرق أولاً.",
            parse_mode='Markdown'
        )
        await asyncio.sleep(2)
        await self.start_round(chat_id, context)

    async def start_round(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE):
        game = games[chat_id]
        game_type = game['game_type']

        if game['round'] > game['max_rounds']:
            await self.end_game(chat_id, context)
            return

        game['waiting_for_answer'] = False
        game['question_asker'] = None
        game['answerer_id'] = None
        game['pending_guess_confirmation'] = None

        if game_type == '1v1':
            player1 = game['players'][0]
            player2 = game['players'][1]

            if game['round'] % 2 != 0: # Odd rounds: Player 1 asks
                question_asker_id = player1['id']
                answerer_id = player2['id']
                question_asker_name = player1['name']
                answerer_name = player2['name']
            else: # Even rounds: Player 2 asks
                question_asker_id = player2['id']
                answerer_id = player1['id']
                question_asker_name = player2['name']
                answerer_name = player1['name']

            game['question_asker'] = {'id': question_asker_id, 'name': question_asker_name}
            game['answerer_id'] = answerer_id

            await context.bot.send_message(
                chat_id,
                f"--- **الجولة {game['round']}** ---\n\n"
                f"دور اللاعب {question_asker_name} ({answerer_name} هو صاحب الشخصية المخفية لهذه الجولة).\n\n"
                "يمكنك طرح سؤال بنعم/لا أو محاولة التخمين بكتابة 'تخمين:' متبوعاً بالشخصية.\n"
                "مثال: `هل هو ذكر؟` أو `تخمين: ناروتو`"
            )
        elif game_type == 'teams':
            current_team_turn = game['current_team_turn']
            opponent_team_turn = 'red' if current_team_turn == 'blue' else 'blue'

            game['question_asker_team'] = current_team_turn
            game['answerer_team'] = opponent_team_turn

            current_team_name_arabic = 'الأزرق' if current_team_turn == 'blue' else 'الأحمر'
            opponent_team_name_arabic = 'الأحمر' if opponent_team_turn == 'blue' else 'الأزرق'

            current_team_members_names = [p['name'] for p in game['teams'][current_team_turn]]
            opponent_team_members_names = [p['name'] for p in game['teams'][opponent_team_turn]]

            await context.bot.send_message(
                chat_id,
                f"--- **الجولة {game['round']}** ---\n\n"
                f"دور **الفريق {current_team_name_arabic}** ({', '.join(current_team_members_names) if current_team_members_names else 'لا يوجد لاعبون'}).\n"
                f"الفريق {opponent_team_name_arabic} ({', '.join(opponent_team_members_names) if opponent_team_members_names else 'لا يوجد لاعبون'}) هو صاحب الشخصية المخفية لهذه الجولة.\n\n"
                "يمكن لأي عضو في الفريق الذي يحين دوره طرح سؤال بنعم/لا أو محاولة التخمين بكتابة 'تخمين:' متبوعاً بالشخصية.\n"
                "مثال: `هل هو ذكر؟` أو `تخمين: ناروتو`"
            )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name
        message_text = update.message.text.strip()

        game = games.get(chat_id)

        if not game or game.get('status') != 'playing':
            return # Ignore messages if no game is active or in playing state

        game_type = game['game_type']

        # Handle answer to pending question (Yes/No)
        if game.get('waiting_for_answer') and game.get('answerer_id') == user_id:
            question_asker_id = game['question_asker']['id']
            question_asker_name = game['question_asker']['name']
            
            if message_text.lower() == 'نعم':
                answer = "نعم"
            elif message_text.lower() == 'لا':
                answer = "لا"
            else:
                await update.message.reply_text("الرجاء الإجابة بـ 'نعم' أو 'لا' فقط.")
                return

            await context.bot.send_message(
                chat_id,
                f"أجاب {user_name} بـ **{answer}** على سؤال {question_asker_name}."
            )
            game['waiting_for_answer'] = False
            game['question_asker'] = None # Clear question asker
            game['answerer_id'] = None # Clear answerer
            return # Answer processed, wait for next action

        # Handle team answer to pending question (Yes/No)
        if game.get('waiting_for_answer') and game_type == 'teams':
            if user_id not in [p['id'] for p in game['teams'][game['answerer_team']]]:
                return # Only members of the answering team can answer

            question_asker_team_name_arabic = 'الأزرق' if game['question_asker_team'] == 'blue' else 'الأحمر'
            answerer_team_name_arabic = 'الأزرق' if game['answerer_team'] == 'blue' else 'الأحمر'

            if message_text.lower() == 'نعم':
                answer = "نعم"
            elif message_text.lower() == 'لا':
                answer = "لا"
            else:
                await update.message.reply_text("الرجاء الإجابة بـ 'نعم' أو 'لا' فقط.")
                return

            await context.bot.send_message(
                chat_id,
                f"أجاب الفريق {answerer_team_name_arabic} بـ **{answer}** على سؤال الفريق {question_asker_team_name_arabic}."
            )
            game['waiting_for_answer'] = False
            # No need to clear question_asker_team/answerer_team as they determine the next turn
            return

        # Handle guesses (for both 1v1 and teams)
        if message_text.lower().startswith('تخمين:'):
            if game_type == '1v1':
                # In 1v1, only the current question asker can guess
                if user_id != game['question_asker']['id']:
                    await update.message.reply_text("ليس دورك للتخمين! انتظر دورك.")
                    return
                opponent_player_id = game['answerer_id']
                opponent_player_name = next(p['name'] for p in game['players'] if p['id'] == opponent_player_id)
                correct_character_name = game['characters'][opponent_player_id]['name']
                guesser_name = game['question_asker']['name']
            elif game_type == 'teams':
                # In teams, any member of the current asking team can guess
                if user_id not in [p['id'] for p in game['teams'][game['question_asker_team']]]:
                    await update.message.reply_text("ليس دور فريقك للتخمين! انتظر دور فريقك.")
                    return
                opponent_team_key = game['answerer_team']
                opponent_team_name_arabic = 'الأزرق' if opponent_team_key == 'blue' else 'الأحمر'
                correct_character_name = game['team_characters'][opponent_team_key]['name']
                guesser_name = user_name # The specific user who made the guess

            guessed_character = message_text.lower().replace('تخمين:', '').strip()

            if guessed_character == correct_character_name.lower():
                if game_type == '1v1':
                    game['scores'][user_id] += 1
                    await update.message.reply_text(
                        f"🎉 أحسنت يا {guesser_name}! لقد خمنت الشخصية بشكل صحيح: "
                        f"*{correct_character_name}*!\n\n"
                        f"نقاط {guesser_name}: {game['scores'][user_id]}"
                    )
                    logger.info(f"Player {guesser_name} guessed correctly.")
                elif game_type == 'teams':
                    current_team_key = game['question_asker_team']
                    game['teams'][current_team_key]['score'] = game['teams'].get(current_team_key, {}).get('score', 0) + 1 # Update team score
                    current_team_name_arabic = 'الأزرق' if current_team_key == 'blue' else 'الأحمر'
                    await update.message.reply_text(
                        f"🎉 أحسنت يا فريق {current_team_name_arabic}! لقد خمنتم الشخصية بشكل صحيح: "
                        f"*{correct_character_name}*!\n\n"
                        f"نقاط فريق {current_team_name_arabic}: {game['teams'][current_team_key]['score']}"
                    )
                    logger.info(f"Team {current_team_name_arabic} guessed correctly.")
                
                await self.end_round(chat_id)
                await self.start_new_round(chat_id)
            else:
                await update.message.reply_text(
                    f"⛔️ التخمين خاطئ يا {guesser_name}! حاول مرة أخرى في دورك التالي."
                )
                if game_type == '1v1':
                    # Switch turn immediately after wrong guess in 1v1
                    await self.end_round(chat_id) # End current turn
                    await self.start_new_round(chat_id) # Start new turn, which will rotate to other player
                elif game_type == 'teams':
                    # In teams, a wrong guess ends the turn for the team
                    await self.end_round(chat_id) # End current turn
                    await self.start_new_round(chat_id) # Start new turn, which will rotate to other team
            return

        # Handle questions (for both 1v1 and teams)
        if message_text.endswith('؟'):
            if game_type == '1v1':
                # In 1v1, check if it's the player's turn to ask
                if user_id != game['question_asker']['id']:
                    await update.message.reply_text("ليس دورك لطرح الأسئلة! انتظر دورك.")
                    return
                
                game['waiting_for_answer'] = True
                game['question_asker'] = {'id': user_id, 'name': user_name} # Reconfirm asker
                answerer_name = next(p['name'] for p in game['players'] if p['id'] == game['answerer_id'])
                await update.message.reply_text(
                    f"سأل {user_name}: *'{message_text}'*\n\n"
                    f"يا {answerer_name}، الرجاء الإجابة بـ 'نعم' أو 'لا'.",
                    parse_mode='Markdown'
                )
                logger.info(f"Player {user_name} asked a question to {answerer_name}.")

            elif game_type == 'teams':
                # In teams, check if the user is part of the current asking team
                if user_id not in [p['id'] for p in game['teams'][game['question_asker_team']]]:
                    await update.message.reply_text("ليس دور فريقك لطرح الأسئلة! انتظر دور فريقك.")
                    return
                
                game['waiting_for_answer'] = True
                # question_asker_team is already set
                answerer_team_name_arabic = 'الأزرق' if game['answerer_team'] == 'blue' else 'الأحمر'
                current_team_name_arabic = 'الأزرق' if game['question_asker_team'] == 'blue' else 'الأحمر'
                
                await update.message.reply_text(
                    f"الفريق {current_team_name_arabic} يسأل: *'{message_text}'*\n\n"
                    f"يا فريق {answerer_team_name_arabic}، الرجاء الإجابة بـ 'نعم' أو 'لا'.",
                    parse_mode='Markdown'
                )
                logger.info(f"Team {current_team_name_arabic} asked a question to team {answerer_team_name_arabic}.")
            return


    async def end_round(self, chat_id: int) -> None:
        game = games[chat_id]
        game['round'] += 1
        logger.info(f"Round {game['round']-1} ended for chat {chat_id}.")

    async def start_new_round(self, chat_id: int, delay: int = 3):
        game = games[chat_id]
        await asyncio.sleep(delay)
        if game['round'] <= game['max_rounds']:
            await self.start_round(chat_id, self.application.bot.get_context()) # Use application's bot context
        else:
            await self.end_game(chat_id, self.application.bot.get_context())


    async def end_game(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
        game = games.pop(chat_id, None)
        if not game:
            await context.bot.send_message(chat_id, "لا توجد لعبة جارية حاليًا لإنهاؤها.")
            return

        game['status'] = 'ended'
        
        if game['game_type'] == '1v1':
            player1 = game['players'][0]
            player2 = game['players'][1]
            score_p1 = game['scores'].get(player1['id'], 0)
            score_p2 = game['scores'].get(player2['id'], 0)

            final_message = f"🏆 **اللعبة انتهت! النتائج النهائية:**\n\n"
            final_message += f"{player1['name']}: {score_p1} نقطة\n"
            final_message += f"{player2['name']}: {score_p2} نقطة\n\n"

            if score_p1 > score_p2:
                final_message += f"🎉 **{player1['name']} هو الفائز!**"
            elif score_p2 > score_p1:
                final_message += f"🎉 **{player2['name']} هو الفائز!**"
            else:
                final_message += "🤝 **تعادل!**"
        elif game['game_type'] == 'teams':
            score_blue = game['teams'].get('blue', {}).get('score', 0)
            score_red = game['teams'].get('red', {}).get('score', 0)

            blue_players_names = ", ".join([p['name'] for p in game['teams']['blue']])
            red_players_names = ", ".join([p['name'] for p in game['teams']['red']])

            final_message = f"🏆 **اللعبة انتهت! النتائج النهائية:**\n\n"
            final_message += f"🔵 *الفريق الأزرق* ({blue_players_names}): {score_blue} نقطة\n"
            final_message += f"🔴 *الفريق الأحمر* ({red_players_names}): {score_red} نقطة\n\n"

            if score_blue > score_red:
                final_message += f"🎉 **الفريق الأزرق هو الفائز!**"
            elif score_red > score_blue:
                final_message += f"🎉 **الفريق الأحمر هو الفائز!**"
            else:
                final_message += "🤝 **تعادل!**"

        await context.bot.send_message(chat_id, final_message, parse_mode='Markdown')
        logger.info(f"Game ended for chat {chat_id}.")


    async def cancel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /cancel command to end the current game."""
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id

        game = games.get(chat_id)

        if not game:
            await update.message.reply_text("لا توجد لعبة جارية حاليًا لكي ألغيها.")
            return

        # Only the game creator or an admin can cancel the game
        if user_id != game['creator_id'] and not await self.is_admin(chat_id, user_id, context):
            await update.message.reply_text("فقط من بدأ اللعبة أو الأدمن يمكنه إلغاء اللعبة.")
            return

        del games[chat_id]
        await update.message.reply_text("تم إلغاء اللعبة بنجاح!")
        logger.info(f"Game in chat {chat_id} cancelled by {user_id}.")

    async def rules_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Display game rules."""
        rules_text = """
        📝 **قواعد لعبة تخمين الشخصيات:**

        **لبدء اللعبة:**
        • استخدم الأمر /start.
        • اختر الفئة (أنمي، أفلام، كرة قدم، أعلام دول، ألعاب فيديو).
        • اختر نمط اللعب: '1 ضد 1' أو 'فرق'.
        • إذا اخترت 'فرق'، اختر حجم الفريق (2 ضد 2 أو 3 ضد 3).
        • انتظر حتى ينضم جميع اللاعبين.

        **نمط 1 ضد 1:**
        • لاعبين اثنين فقط.
        • يتلقى كل لاعب شخصية سرية خاصة به في رسالة خاصة من البوت.
        • يتناوب اللاعبون على طرح أسئلة 'نعم/لا' لتخمين شخصية الخصم.
        • للإجابة: أجب بـ 'نعم' أو 'لا' عندما يحين دورك.
        • للتخمين: اكتب 'تخمين: [اسم الشخصية]' (مثال: 'تخمين: ناروتو').
        • إذا كان التخمين صحيحاً، يحصل اللاعب المخمِّن على نقطة وتنتهي الجولة.
        • إذا كان التخمين خاطئاً، لا يحصل اللاعب المخمِّن على نقطة وينتقل الدور للخصم.
        • اللاعب الذي لديه الشخصية يمكنه استخدام /approve لمنح نقطة لخصمه وإنهاء الجولة.
        • يمكن لأي لاعب استخدام /forfeit للاستسلام في الجولة الحالية (دون نقاط).
        • اللعبة تستمر لعدد محدد من الجولات. اللاعب صاحب أعلى نقاط يفوز.

        **نمط الفرق:**
        • فريقان (أزرق وأحمر)، وكل فريق يختار حجمه (2 أو 3 لاعبين).
        • يتلقى كل فريق شخصية سرية واحدة في رسالة خاصة من البوت (يتشاركها جميع أفراد الفريق).
        • يتناوب فريق على طرح الأسئلة أو التخمين، والفريق الآخر يجيب.
        • للإجابة: أي عضو من الفريق صاحب الشخصية يجيب بـ 'نعم' أو 'لا'.
        • للتخمين: أي عضو من الفريق الذي يحين دوره يكتب 'تخمين: [اسم الشخصية]'.
        • إذا كان التخمين صحيحاً، يحصل الفريق المخمِّن على نقطة وتنتهي الجولة.
        • إذا كان التخمين خاطئاً، لا يحصل الفريق المخمِّن على نقطة وينتقل الدور للفريق الخصم.
        • يمكن لأي عضو في الفريق صاحب الشخصية استخدام /approve لمنح نقطة للفريق الخصم وإنهاء الجولة.
        • يمكن لأي عضو في الفريق الذي يحين دوره في السؤال/التخمين استخدام /forfeit للاستسلام في الجولة الحالية (يمنح نقطة للخصم).
        • اللعبة تستمر لعدد محدد من الجولات. الفريق صاحب أعلى نقاط يفوز.

        **الأوامر الهامة:**
        • /start - لبدء لعبة جديدة.
        • /cancel - لإلغاء اللعبة الحالية (فقط من بدأ اللعبة أو الأدمن).
        • /score - لعرض النتائج الحالية.
        • /forfeit - للاستسلام في الجولة الحالية.
        • /approve - لمنح نقطة للخصم وكشف شخصيتك (أو شخصية فريقك).
        """
        await update.message.reply_text(rules_text, parse_mode='Markdown')

    async def score_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Display current scores."""
        chat_id = update.effective_chat.id
        game = games.get(chat_id)

        if not game or game.get('status') == 'ended':
            await update.message.reply_text("لا توجد لعبة جارية حاليًا.")
            return

        score_message = "📊 **النتائج الحالية:**\n\n"
        score_message += f"الجولة الحالية: {game['round']} من {game['max_rounds']}\n\n"

        if game['game_type'] == '1v1':
            if 'players' in game and len(game['players']) == 2:
                for player in game['players']:
                    score_message += f"{player['name']}: {game['scores'].get(player['id'], 0)} نقطة\n"
            else:
                score_message += "في انتظار اكتمال اللاعبين في وضع 1 ضد 1.\n"
        elif game['game_type'] == 'teams':
            score_blue = game['teams'].get('blue', {}).get('score', 0)
            score_red = game['teams'].get('red', {}).get('score', 0)
            
            blue_players_names = [p['name'] for p in game['teams']['blue']]
            red_players_names = [p['name'] for p in game['teams']['red']]

            score_message += f"🔵 *الفريق الأزرق* ({', '.join(blue_players_names) if blue_players_names else 'لا يوجد لاعبون'}): {score_blue} نقطة\n"
            score_message += f"🔴 *الفريق الأحمر* ({', '.join(red_players_names) if red_players_names else 'لا يوجد لاعبون'}): {score_red} نقطة\n"

        await update.message.reply_text(score_message, parse_mode='Markdown')

    async def forfeit_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /forfeit command."""
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name

        game = games.get(chat_id)

        if not game or game.get('status') != 'playing':
            await update.message.reply_text("لا توجد لعبة نشطة للاستسلام فيها حاليًا.")
            return

        game_type = game['game_type']
        
        can_forfeit = False
        message_to_send = ""
        
        if game_type == '1v1':
            # Only the current question asker can forfeit
            if game['question_asker'] and user_id == game['question_asker']['id']:
                can_forfeit = True
                opponent_player_id = game['answerer_id']
                opponent_character_info = game['characters'][opponent_player_id]
                message_to_send = (
                    f"🏳️ استسلم {user_name} في هذه الجولة.\n"
                    f"الشخصية التي كانت لدى {opponent_player_id} هي: "
                    f"*{opponent_character_info['name']}* ({opponent_character_info['desc']})"
                    f"\n🔗 {opponent_character_info['link']}"
                )
                logger.info(f"Player {user_name} used /forfeit in 1v1. No points awarded.")
            else:
                await update.message.reply_text("يمكنك استخدام /forfeit عندما يكون دورك في طرح الأسئلة أو التخمين.")
                return

        elif game_type == 'teams':
            current_team_key = game['question_asker_team']
            if user_id in [p['id'] for p in game['teams'][current_team_key]]:
                can_forfeit = True
                opponent_team_key = game['answerer_team']
                opponent_team_name_arabic = 'الأزرق' if opponent_team_key == 'blue' else 'الأحمر'
                current_team_name_arabic = 'الأزرق' if current_team_key == 'blue' else 'الأحمر'
                
                game['teams'][opponent_team_key]['score'] = game['teams'].get(opponent_team_key, {}).get('score', 0) + 1 # Award point to opponent
                
                opponent_character_info = game['team_characters'][opponent_team_key]
                message_to_send = (
                    f"🏳️ استسلم الفريق {current_team_name_arabic}.\n"
                    f"نقطة للفريق {opponent_team_name_arabic}!\n"
                    f"الشخصية التي كانت لدى فريق {opponent_team_name_arabic} هي: "
                    f"*{opponent_character_info['name']}* ({opponent_character_info['desc']})"
                    f"\n🔗 {opponent_character_info['link']}"
                )
                logger.info(f"Team {current_team_name_arabic} used /forfeit. Team {opponent_team_name_arabic} gets a point.")
            else:
                await update.message.reply_text("يمكن لفريقك استخدام /forfeit عندما يحين دوره في طرح الأسئلة أو التخمين.")
                return

        if can_forfeit:
            await update.message.reply_text(message_to_send, parse_mode='Markdown')
            await self.end_round(chat_id)
            await self.start_new_round(chat_id)
        else:
            await update.message.reply_text("لا يمكنك استخدام هذا الأمر الآن.")


    async def approve_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = update.effective_chat.id
        game = games.get(chat_id)
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name

        if not game or game.get('status') != 'playing':
            await update.message.reply_text("لا توجد لعبة جارية حاليًا لاستخدام هذا الأمر فيها.")
            return

        game_type = game['game_type']

        if game_type == '1v1':
            player1_id = game['players'][0]['id']
            player2_id = game['players'][1]['id']

            # Determine who used /approve and who is the opponent
            # The user using /approve is the one whose character is to be revealed
            # The opponent is the one who gets the point
            if user_id == player1_id:
                approving_player_key = 'player1'
                opponent_player_id = player2_id
                approving_player_info = game['players'][0]
            elif user_id == player2_id:
                approving_player_key = 'player2'
                opponent_player_id = player1_id
                approving_player_info = game['players'][1]
            else:
                await update.message.reply_text("أنت لست جزءًا من هذه اللعبة.")
                return
            
            # Check if the player using /approve is the one whose character is currently hidden
            # i.e., they are the "answerer" for this turn, or it's implicitly their character
            # if game['question_asker'] is not None and user_id == game['question_asker']['id']:
            #     await update.message.reply_text("لا يمكنك استخدام /approve عندما يكون دورك لطرح الأسئلة. هذا الأمر للموافقة على تخمين خصمك أو منحه نقطة.")
            #     return

            # Grant point to the opponent
            game['scores'][opponent_player_id] = game['scores'].get(opponent_player_id, 0) + 1
            approving_player_character = game['characters'][user_id]
            opponent_player_name = next(p['name'] for p in game['players'] if p['id'] == opponent_player_id)

            await update.message.reply_text(
                f"🎉 {user_name} وافق على التخمين أو منح النقطة!\n"
                f"نقطة لـ {opponent_player_name}!\n"
                f"الشخصية التي كانت لدى {user_name} هي: "
                f"*{approving_player_character['name']}* "
                f"({approving_player_character['desc']})"
                f"\n🔗 {approving_player_character['link']}",
                parse_mode='Markdown', disable_web_page_preview=True
            )
            logger.info(f"Player {user_name} used /approve. {opponent_player_name} gets a point.")

        elif game_type == 'teams':
            team_a_members_ids = [member['id'] for member in game['teams']['blue']]
            team_b_members_ids = [member['id'] for member in game['teams']['red']]

            approving_team_key = None
            opponent_team_key = None

            if user_id in team_a_members_ids:
                approving_team_key = 'blue'
                opponent_team_key = 'red'
            elif user_id in team_b_members_ids:
                approving_team_key = 'red'
                opponent_team_key = 'blue'
            else:
                await update.message.reply_text("أنت لست جزءًا من هذه اللعبة.")
                return
            
            # Check if the team using /approve is the one whose character is currently hidden
            # if approving_team_key == game.get('question_asker_team'):
            #     await update.message.reply_text("لا يمكن لفريقك استخدام /approve عندما يكون دوركم لطرح الأسئلة. هذا الأمر للموافقة على تخمين الفريق الخصم أو منحه نقطة.")
            #     return

            # Grant point to the opposing team
            game['teams'][opponent_team_key]['score'] = game['teams'].get(opponent_team_key, {}).get('score', 0) + 1
            approving_team_character = game['team_characters'][approving_team_key]
            opponent_team_name_arabic = 'الأزرق' if opponent_team_key == 'blue' else 'الأحمر'
            approving_team_name_arabic = 'الأزرق' if approving_team_key == 'blue' else 'الأحمر'

            await update.message.reply_text(
                f"🎉 فريق {approving_team_name_arabic} وافق على التخمين أو منح النقطة!\n"
                f"نقطة لفريق {opponent_team_name_arabic}!\n"
                f"الشخصية التي كانت لدى فريق {approving_team_name_arabic} هي: "
                f"*{approving_team_character['name']}* "
                f"({approving_team_character['desc']})"
                f"\n🔗 {approving_team_character['link']}",
                parse_mode='Markdown', disable_web_page_preview=True
            )
            logger.info(f"Team {approving_team_name_arabic} used /approve. Team {opponent_team_name_arabic} gets a point.")

        # End the current round
        await self.end_round(chat_id)
        # Start a new round
        await self.start_new_round(chat_id)


    def setup_handlers(self, application: Application):
        """Set up the bot's command and message handlers."""
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("cancel", self.cancel_command))
        application.add_handler(CommandHandler("rules", self.rules_command))
        application.add_handler(CommandHandler("score", self.score_command))
        application.add_handler(CommandHandler("forfeit", self.forfeit_command))
        application.add_handler(CommandHandler("approve", self.approve_command)) # New Handler for /approve
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
