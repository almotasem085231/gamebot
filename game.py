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
        game = games.get(chat_id)
        if not game or game['status'] != 'playing':
            return

        if game['round'] > game['max_rounds']:
            await self.end_game(chat_id, context)
            return

        if game['game_type'] == '1v1':
            player1_id = game['players'][0]['id']
            player2_id = game['players'][1]['id']

            # Determine whose turn it is
            current_player_idx = (game['round'] - 1) % 2
            game['current_turn_player_id'] = game['players'][current_player_idx]['id']
            game['current_turn_player_name'] = game['players'][current_player_idx]['name']
            
            # The other player is the answerer
            answerer_idx = (current_player_idx + 1) % 2
            game['answerer_id'] = game['players'][answerer_idx]['id']
            game['answerer_name'] = game['players'][answerer_idx]['name']


            await context.bot.send_message(
                chat_id,
                f"--- **الجولة {game['round']} من {game['max_rounds']}** ---\n\n"
                f" الدور الآن على اللاعب **{game['current_turn_player_name']}**! "
                f"اطرح سؤالًا بنعم/لا لتخمين شخصية **{game['answerer_name']}**.\n"
                "يمكنك أيضًا محاولة التخمين مباشرة بقول \"أعتقد أن الشخصية هي [اسم الشخصية]\".",
                parse_mode='Markdown'
            )
            game['waiting_for_answer'] = False # Reset for new question

        elif game['game_type'] == 'teams':
            current_team = game['current_team_turn']
            other_team = 'red' if current_team == 'blue' else 'blue'

            # Determine the character to guess
            character_to_guess_name = game['team_characters'][other_team]['name']
            
            # Message to the current team
            team_members_names = [p['name'] for p in game['teams'][current_team]]
            
            await context.bot.send_message(
                chat_id,
                f"--- **الجولة {game['round']} من {game['max_rounds']}** ---\n\n"
                f"الآن دور الفريق **{'الأزرق' if current_team == 'blue' else 'الأحمر'}**! "
                f"({', '.join(team_members_names)})\n"
                f"اطرحوا سؤالًا بنعم/لا لتخمين شخصية الفريق **{'الأحمر' if current_team == 'blue' else 'الأزرق'}**.\n"
                f"يمكنكم أيضًا محاولة التخمين مباشرة بقول \"أعتقد أن الشخصية هي [اسم الشخصية]\".",
                parse_mode='Markdown'
            )
            game['waiting_for_answer'] = False # Reset for new question

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        text = update.message.text.strip()
        username = update.effective_user.first_name

        game = games.get(chat_id)

        if not game or game['status'] != 'playing':
            return # Ignore messages if no game or not in playing status

        if game['game_type'] == '1v1':
            current_turn_player_id = game['current_turn_player_id']
            answerer_id = game['answerer_id']
            
            if user_id == current_turn_player_id:
                # Player asking a question or making a guess
                if text.lower().startswith("أعتقد أن الشخصية هي"):
                    guessed_character_name = text.lower().replace("أعتقد أن الشخصية هي", "").strip()
                    await self.handle_guess(chat_id, user_id, username, guessed_character_name, context)
                else:
                    # Assume it's a question
                    game['question_asker'] = user_id
                    game['waiting_for_answer'] = True

                    keyboard = [
                        [InlineKeyboardButton("✅ نعم", callback_data="answer_yes")],
                        [InlineKeyboardButton("❌ لا", callback_data="answer_no")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)

                    await context.bot.send_message(
                        chat_id,
                        f"**{game['answerer_name']}**، هل إجابة سؤال \"{text}\" هي:",
                        reply_markup=reply_markup, parse_mode='Markdown'
                    )
            elif user_id == answerer_id and game['waiting_for_answer']:
                await update.message.reply_text("الرجاء استخدام الأزرار للإجابة على السؤال.")
            else:
                await update.message.reply_text(f"الرجاء الانتظار، ليس دورك يا {username}.")

        elif game['game_type'] == 'teams':
            current_team_name = game['current_team_turn']
            current_team_members_ids = [p['id'] for p in game['teams'][current_team_name]]
            other_team_name = 'red' if current_team_name == 'blue' else 'blue'

            # A player from the current team is asking a question or making a guess
            if user_id in current_team_members_ids:
                if text.lower().startswith("أعتقد أن الشخصية هي"):
                    guessed_character_name = text.lower().replace("أعتقد أن الشخصية هي", "").strip()
                    await self.handle_team_guess(chat_id, user_id, current_team_name, guessed_character_name, context)
                else:
                    # Assume it's a question
                    game['question_asker'] = user_id # Store the specific player who asked
                    game['waiting_for_answer'] = True
                    game['answerer_id'] = [p['id'] for p in game['teams'][other_team_name]] # All members of the other team can answer

                    keyboard = [
                        [InlineKeyboardButton("✅ نعم", callback_data="answer_yes")],
                        [InlineKeyboardButton("❌ لا", callback_data="answer_no")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    # Notify the other team to answer
                    await context.bot.send_message(
                        chat_id,
                        f"فريق **{'الأحمر' if current_team_name == 'blue' else 'الأزرق'}**، "
                        f"هل إجابة سؤال \"{text}\" هي:",
                        reply_markup=reply_markup, parse_mode='Markdown'
                    )
            # A player from the other team (the one whose character is being guessed) is trying to answer
            elif user_id in [p['id'] for p in game['teams'][other_team_name]] and game['waiting_for_answer']:
                await update.message.reply_text("الرجاء استخدام الأزرار للإجابة على السؤال.")
            else:
                await update.message.reply_text(f"الرجاء الانتظار، ليس دور فريقك يا {username}.")


    async def callback_query_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        chat_id = query.message.chat_id
        user_id = query.from_user.id
        username = query.from_user.first_name

        game = games.get(chat_id)

        if not game:
            await query.edit_message_text("لا توجد لعبة نشطة حاليًا في هذه المجموعة.")
            return

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
        elif query.data in ["answer_yes", "answer_no"]:
            await self.handle_answer_callback(update, context)
        elif query.data == "confirm_guess_yes":
            await self.handle_guess_confirmation(chat_id, user_id, True, context)
        elif query.data == "confirm_guess_no":
            await self.handle_guess_confirmation(chat_id, user_id, False, context)


    async def handle_answer_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        chat_id = query.message.chat_id
        user_id = query.from_user.id
        answer = query.data.replace("answer_", "") # 'yes' or 'no'

        game = games.get(chat_id)

        if not game or not game.get('waiting_for_answer'):
            await query.answer("لا يوجد سؤال معلق للإجابة عليه.", show_alert=True)
            return
        
        if game['game_type'] == '1v1':
            # In 1v1, only the designated answerer can answer
            if user_id != game['answerer_id']:
                await query.answer("ليس دورك للإجابة على السؤال.", show_alert=True)
                return
            
            await query.edit_message_text(
                f"{query.message.text}\n\nالإجابة: **{ 'نعم' if answer == 'yes' else 'لا' }**",
                parse_mode='Markdown'
            )
            game['waiting_for_answer'] = False
            await self.next_turn(chat_id, context)

        elif game['game_type'] == 'teams':
            # In teams, any player from the 'other' team can answer
            current_team_name = game['current_team_turn']
            other_team_name = 'red' if current_team_name == 'blue' else 'blue'
            other_team_members_ids = [p['id'] for p in game['teams'][other_team_name]]

            if user_id not in other_team_members_ids:
                await query.answer("ليس دور فريقك للإجابة على السؤال.", show_alert=True)
                return

            await query.edit_message_text(
                f"{query.message.text}\n\nأجاب الفريق **{'الأحمر' if current_team_name == 'blue' else 'الأزرق'}**: **{ 'نعم' if answer == 'yes' else 'لا' }**",
                parse_mode='Markdown'
            )
            game['waiting_for_answer'] = False
            await self.next_turn(chat_id, context)


    async def handle_guess(self, chat_id: int, guesser_id: int, guesser_name: str, guessed_character_name: str, context: ContextTypes.DEFAULT_TYPE):
        game = games.get(chat_id)
        if not game or game['status'] != 'playing' or game.get('game_type') != '1v1':
            return

        # Ensure it's the guesser's turn
        if guesser_id != game['current_turn_player_id']:
            await context.bot.send_message(chat_id, f"الرجاء الانتظار، ليس دورك للتخمين يا {guesser_name}.")
            return
        
        answerer_id = game['answerer_id']
        answerer_name = game['answerer_name']
        actual_character_name = game['characters'][answerer_id]['name']

        # Store pending guess for confirmation
        game['pending_guess_confirmation'] = {
            'guesser_id': guesser_id,
            'guesser_name': guesser_name,
            'guessed_name': guessed_character_name,
            'answerer_id': answerer_id,
            'actual_character_name': actual_character_name
        }

        keyboard = [
            [InlineKeyboardButton("✅ نعم، هذا صحيح!", callback_data="confirm_guess_yes")],
            [InlineKeyboardButton("❌ لا، هذا ليس صحيحًا.", callback_data="confirm_guess_no")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(
            chat_id,
            f"**{answerer_name}**، هل تخمين **{guesser_name}** بأن الشخصية هي \"**{guessed_character_name}**\" صحيح؟",
            reply_markup=reply_markup, parse_mode='Markdown'
        )

    async def handle_team_guess(self, chat_id: int, guesser_id: int, guesser_team_name: str, guessed_character_name: str, context: ContextTypes.DEFAULT_TYPE):
        game = games.get(chat_id)
        if not game or game['status'] != 'playing' or game.get('game_type') != 'teams':
            return

        # Ensure it's the guesser's team's turn
        current_team_name = game['current_team_turn']
        current_team_members_ids = [p['id'] for p in game['teams'][current_team_name]]
        if guesser_id not in current_team_members_ids:
            await context.bot.send_message(chat_id, f"الرجاء الانتظار، ليس دور فريقك للتخمين.")
            return
        
        other_team_name = 'red' if current_team_name == 'blue' else 'blue'
        actual_character_name = game['team_characters'][other_team_name]['name']

        # Store pending guess for confirmation
        game['pending_guess_confirmation'] = {
            'guesser_id': guesser_id, # The player who initiated the guess
            'guesser_team_name': guesser_team_name,
            'guessed_name': guessed_character_name,
            'answerer_team_name': other_team_name,
            'answerer_ids': [p['id'] for p in game['teams'][other_team_name]],
            'actual_character_name': actual_character_name
        }

        keyboard = [
            [InlineKeyboardButton("✅ نعم، هذا صحيح!", callback_data="confirm_guess_yes")],
            [InlineKeyboardButton("❌ لا، هذا ليس صحيحًا.", callback_data="confirm_guess_no")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(
            chat_id,
            f"فريق **{'الأحمر' if current_team_name == 'blue' else 'الأزرق'}**، "
            f"هل تخمين الفريق **{'الأزرق' if current_team_name == 'blue' else 'الأحمر'}** بأن الشخصية هي \"**{guessed_character_name}**\" صحيح؟",
            reply_markup=reply_markup, parse_mode='Markdown'
        )


    async def handle_guess_confirmation(self, chat_id: int, confirmer_id: int, is_correct: bool, context: ContextTypes.DEFAULT_TYPE):
        game = games.get(chat_id)
        if not game or not game.get('pending_guess_confirmation'):
            await context.bot.send_message(chat_id, "لا يوجد تخمين معلق للتأكيد.")
            return

        pending_guess = game['pending_guess_confirmation']

        if game['game_type'] == '1v1':
            # Only the answerer can confirm the guess in 1v1
            if confirmer_id != pending_guess['answerer_id']:
                await context.bot.send_message(chat_id, "فقط اللاعب الآخر يمكنه تأكيد التخمين.")
                return
            
            guesser_id = pending_guess['guesser_id']
            guesser_name = pending_guess['guesser_name']
            guessed_character_name = pending_guess['guessed_name']
            actual_character_name = pending_guess['actual_character_name']

            if is_correct:
                if guessed_character_name.lower() == actual_character_name.lower():
                    await context.bot.send_message(
                        chat_id,
                        f"🎉 **تخمين صحيح!**\n\n"
                        f"لقد خمّن **{guesser_name}** شخصية **{actual_character_name}** بشكل صحيح!\n"
                        f"تم إضافة نقطة لـ **{guesser_name}**.",
                        parse_mode='Markdown'
                    )
                    game['scores'][guesser_id] += 1
                else:
                    await context.bot.send_message(
                        chat_id,
                        f"❌ **تخمين غير صحيح!**\n\n"
                        f"للأسف، \"**{guessed_character_name}**\" ليست الشخصية الصحيحة.\n"
                        f"الشخصية الحقيقية كانت **{actual_character_name}**.",
                        parse_mode='Markdown'
                    )
                    # No score change, but turn ends
            else:
                await context.bot.send_message(
                    chat_id,
                    f"**{guesser_name}**، تخمينك \"**{guessed_character_name}**\" لم يكن صحيحًا. حاول مرة أخرى!",
                    parse_mode='Markdown'
                )
            
            game['pending_guess_confirmation'] = None # Clear pending guess
            await self.end_round(chat_id, context)

        elif game['game_type'] == 'teams':
            # Any player from the 'answerer' team can confirm
            answerer_team_members_ids = pending_guess['answerer_ids']
            if confirmer_id not in answerer_team_members_ids:
                await context.bot.send_message(chat_id, "فقط أعضاء الفريق الآخر يمكنهم تأكيد التخمين.")
                return

            guesser_team_name = pending_guess['guesser_team_name']
            guessed_character_name = pending_guess['guessed_name']
            actual_character_name = pending_guess['actual_character_name']

            if is_correct:
                if guessed_character_name.lower() == actual_character_name.lower():
                    await context.bot.send_message(
                        chat_id,
                        f"🎉 **تخمين صحيح!**\n\n"
                        f"لقد خمّن الفريق **{'الأزرق' if guesser_team_name == 'blue' else 'الأحمر'}** شخصية **{actual_character_name}** بشكل صحيح!\n"
                        f"تم إضافة نقطة للفريق **{'الأزرق' if guesser_team_name == 'blue' else 'الأحمر'}**.",
                        parse_mode='Markdown'
                    )
                    # Award score to all players in the guessing team
                    for player in game['teams'][guesser_team_name]:
                        game['scores'][player['id']] += 1
                else:
                    await context.bot.send_message(
                        chat_id,
                        f"❌ **تخمين غير صحيح!**\n\n"
                        f"للأسف، \"**{guessed_character_name}**\" ليست الشخصية الصحيحة.\n"
                        f"الشخصية الحقيقية كانت **{actual_character_name}**.",
                        parse_mode='Markdown'
                    )
                    # No score change, but turn ends
            else:
                await context.bot.send_message(
                    chat_id,
                    f"الفريق **{'الأزرق' if guesser_team_name == 'blue' else 'الأحمر'}**، تخمينكم \"**{guessed_character_name}**\" لم يكن صحيحًا. حاولوا مرة أخرى!",
                    parse_mode='Markdown'
                )
            
            game['pending_guess_confirmation'] = None # Clear pending guess
            await self.end_round(chat_id, context)


    async def next_turn(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE):
        game = games.get(chat_id)
        if not game or game['status'] != 'playing':
            return

        if game['game_type'] == '1v1':
            # Switch current player and answerer for the next turn within the same round
            game['current_turn_player_id'], game['answerer_id'] = game['answerer_id'], game['current_turn_player_id']
            game['current_turn_player_name'], game['answerer_name'] = game['answerer_name'], game['current_turn_player_name']
            
            await context.bot.send_message(
                chat_id,
                f" الدور الآن على اللاعب **{game['current_turn_player_name']}**! "
                f"اطرح سؤالًا بنعم/لا لتخمين شخصية **{game['answerer_name']}**.",
                parse_mode='Markdown'
            )
        elif game['game_type'] == 'teams':
            # Switch current team for the next turn within the same round
            game['current_team_turn'] = 'red' if game['current_team_turn'] == 'blue' else 'blue'
            current_team = game['current_team_turn']
            other_team = 'red' if current_team == 'blue' else 'blue'
            
            team_members_names = [p['name'] for p in game['teams'][current_team]]
            
            await context.bot.send_message(
                chat_id,
                f"الآن دور الفريق **{'الأزرق' if current_team == 'blue' else 'الأحمر'}**! "
                f"({', '.join(team_members_names)})\n"
                f"اطرحوا سؤالًا بنعم/لا لتخمين شخصية الفريق **{'الأحمر' if current_team == 'blue' else 'الأزرق'}**.",
                parse_mode='Markdown'
            )
        
        # In both modes, after a question and answer, or an incorrect guess, it's the same round.
        # The round only ends after a correct guess or if everyone had a chance to guess (which is handled by `end_round`).
        # This simplifies the flow for questions vs. guesses.

    async def end_round(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE):
        game = games.get(chat_id)
        if not game or game['status'] != 'playing':
            return
        
        game['round'] += 1
        await self.start_round(chat_id, context) # Start next round or end game

    async def score_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /score command"""
        chat_id = update.effective_chat.id
        game = games.get(chat_id)

        if not game:
            await update.message.reply_text("لا توجد لعبة نشطة حاليًا.")
            return

        score_message = "📊 **النتائج الحالية:**\n\n"
        if game['game_type'] == '1v1':
            for player_id, score in game['scores'].items():
                player_name = next((p['name'] for p in game['players'] if p['id'] == player_id), "لاعب غير معروف")
                score_message += f"**{player_name}**: {score} نقطة\n"
            score_message += f"\nالجولة الحالية: {game['round']} من {game['max_rounds']}"
        elif game['game_type'] == 'teams':
            team_scores = {'blue': 0, 'red': 0}
            for player_id, score in game['scores'].items():
                player_info = next((p for p in game['players'] if p['id'] == player_id), None)
                if player_info and 'team' in player_info:
                    team_scores[player_info['team']] += score
            
            score_message += f"🔵 **الفريق الأزرق**: {team_scores['blue']} نقطة\n"
            score_message += f"🔴 **الفريق الأحمر**: {team_scores['red']} نقطة\n"
            score_message += f"\nالجولة الحالية: {game['round']} من {game['max_rounds']}"

        await update.message.reply_text(score_message, parse_mode='Markdown')

    async def end_game(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE):
        game = games.pop(chat_id, None)
        if not game:
            await context.bot.send_message(chat_id, "لا توجد لعبة نشطة لإنهاءها.")
            return

        final_score_message = "🏆 **اللعبة انتهت!**\n\n**النتائج النهائية:**\n\n"

        if game['game_type'] == '1v1':
            sorted_scores = sorted(game['scores'].items(), key=lambda item: item[1], reverse=True)
            for player_id, score in sorted_scores:
                player_name = next((p['name'] for p in game['players'] if p['id'] == player_id), "لاعب غير معروف")
                final_score_message += f"**{player_name}**: {score} نقطة\n"
            
            if len(sorted_scores) > 1 and sorted_scores[0][1] > sorted_scores[1][1]:
                winner_name = next((p['name'] for p in game['players'] if p['id'] == sorted_scores[0][0]), "لاعب غير معروف")
                final_score_message += f"\n🎉 **الفائز: {winner_name}!**"
            elif len(sorted_scores) > 1 and sorted_scores[0][1] == sorted_scores[1][1]:
                final_score_message += "\n🤝 **تعادل!**"

        elif game['game_type'] == 'teams':
            team_scores = {'blue': 0, 'red': 0}
            for player_id, score in game['scores'].items():
                player_info = next((p for p in game['players'] if p['id'] == player_id), None)
                if player_info and 'team' in player_info:
                    team_scores[player_info['team']] += score
            
            final_score_message += f"🔵 **الفريق الأزرق**: {team_scores['blue']} نقطة\n"
            final_score_message += f"🔴 **الفريق الأحمر**: {team_scores['red']} نقطة\n"

            if team_scores['blue'] > team_scores['red']:
                final_score_message += "\n🎉 **الفائز: الفريق الأزرق!**"
            elif team_scores['red'] > team_scores['blue']:
                final_score_message += "\n🎉 **الفائز: الفريق الأحمر!**"
            else:
                final_score_message += "\n🤝 **تعادل!**"

        await context.bot.send_message(chat_id, final_score_message, parse_mode='Markdown')

    async def cancel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /cancel command"""
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id

        game = games.get(chat_id)

        if not game:
            await update.message.reply_text("لا توجد لعبة نشطة لإلغائها.")
            return
        
        # Allow only the creator or an admin to cancel the game
        if user_id == game['creator_id'] or await self.is_admin(chat_id, user_id, context):
            del games[chat_id]
            await update.message.reply_text("تم إلغاء اللعبة بنجاح.")
        else:
            await update.message.reply_text("فقط من بدأ اللعبة أو مشرف المجموعة يمكنه إلغاء اللعبة.")
    
    async def rules_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Display game rules."""
        rules_text = (
            "📜 **قواعد لعبة تخمين الشخصيات**\n\n"
            "**نمط 1 ضد 1:**\n"
            "• يبدأ اللعبة مشرف المجموعة /start.\n"
            "• يتم اختيار فئة للعبة (مثال: أنمي، أفلام، كرة قدم، أعلام دول، ألعاب فيديو).\n"
            "• ينضم لاعبان للعبة.\n"
            "• يتلقى كل لاعب شخصية سرية من الفئة المختارة في رسالة خاصة.\n"
            "• يتناوب اللاعبان على طرح أسئلة 'نعم/لا' لتخمين شخصية الخصم.\n"
            "• يمكن للاعبين محاولة التخمين مباشرة بقول 'أعتقد أن الشخصية هي [اسم الشخصية]'.\n"
            "• إذا كان التخمين صحيحًا، يحصل اللاعب على نقطة وتنتقل اللعبة للجولة التالية.\n"
            "• إذا كان التخمين خاطئًا، يستمر الدور للخصم.\n"
            "• تستمر اللعبة لـ 3 جولات، والفائز هو من يجمع نقاطًا أكثر.\n\n"
            "**نمط الفرق:**\n"
            "• يبدأ اللعبة مشرف المجموعة /start.\n"
            "• يتم اختيار فئة للعبة ثم حجم الفريق (2 ضد 2 أو 3 ضد 3).\n"
            "• ينضم اللاعبون إلى الفريق الأزرق أو الأحمر حتى تكتمل الفرق.\n"
            "• يتلقى كل عضو في الفريق شخصية سرية مشتركة لفريقه في رسالة خاصة.\n"
            "• يتناوب الفريقان على طرح أسئلة 'نعم/لا' لتخمين شخصية الفريق الخصم.\n"
            "• يمكن لأي عضو من الفريق المعني الإجابة على السؤال بالأزرار.\n"
            "• يمكن للفريق محاولة التخمين مباشرة بقول 'أعتقد أن الشخصية هي [اسم الشخصية]'.\n"
            "• إذا كان التخمين صحيحًا، يحصل الفريق على نقطة وتنتقل اللعبة للجولة التالية.\n"
            "• إذا كان التخمين خاطئًا، يستمر الدور للفريق الخصم.\n"
            "• تستمر اللعبة لـ 3 جولات، والفريق الفائز هو من يجمع نقاطًا أكثر.\n\n"
            "**الأوامر:**\n"
            "• `/start`: لبدء لعبة جديدة (للمشرفين فقط).\n"
            "• `/cancel`: لإلغاء اللعبة الحالية (لمن بدأ اللعبة أو المشرفين).\n"
            "• `/score`: لمعرفة النتائج الحالية.\n"
            "• `/rules`: لعرض هذه القواعد.\n"
            "• `/forfeit`: للاستسلام في اللعبة (في وضع 1 ضد 1 فقط).\n"
            "• `/approve`: (للمشرفين فقط) الموافقة على تخمين لاعب في حال وجود مشكلة تقنية.\n\n"
            "استمتعوا باللعبة!"
        )
        await update.message.reply_text(rules_text, parse_mode='Markdown', disable_web_page_preview=True)

    async def forfeit_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /forfeit command to allow a player to surrender in 1v1."""
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        username = update.effective_user.first_name

        game = games.get(chat_id)

        if not game or game['status'] != 'playing':
            await update.message.reply_text("لا توجد لعبة نشطة يمكنك الاستسلام فيها.")
            return

        if game['game_type'] != '1v1':
            await update.message.reply_text("الاستسلام متاح فقط في نمط 1 ضد 1.")
            return

        if user_id not in [p['id'] for p in game['players']]:
            await update.message.reply_text("أنت لست لاعبًا في هذه اللعبة.")
            return
        
        # Identify the winner
        winner_player = None
        for player in game['players']:
            if player['id'] != user_id:
                winner_player = player
                break
        
        if winner_player:
            winner_name = winner_player['name']
            winner_id = winner_player['id']
            game['scores'][winner_id] += 1 # Award a point to the winner
            await context.bot.send_message(
                chat_id,
                f"🏳️ **استسلام!**\n\n"
                f"اللاعب **{username}** استسلم. تهانينا لـ **{winner_name}** على الفوز بالجولة!\n"
                f"تم إضافة نقطة لـ **{winner_name}**.",
                parse_mode='Markdown'
            )
        else:
            # This case should theoretically not happen in a 1v1 game with 2 players
            await context.bot.send_message(chat_id, f"اللاعب **{username}** استسلم. تم إنهاء الجولة.")

        await self.end_round(chat_id, context) # Proceed to next round or end game

    async def approve_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Admin command to manually approve a guess in case of technical issues.
        Usage: /approve [player_id_who_guessed] [actual_character_name]
        """
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        
        # Only admins can use this command
        if not await self.is_admin(chat_id, user_id, context):
            await update.message.reply_text("ليس لديك الصلاحية لاستخدام هذا الأمر.")
            return

        if not context.args or len(context.args) < 2:
            await update.message.reply_text("الاستخدام: `/approve [معرف_اللاعب_الذي_خمّن] [الاسم_الحقيقي_للشخصية]`", parse_mode='Markdown')
            return

        game = games.get(chat_id)
        if not game or game['status'] != 'playing':
            await update.message.reply_text("لا توجد لعبة نشطة للموافقة على تخمين فيها.")
            return

        try:
            guesser_id = int(context.args[0])
            actual_character_name = " ".join(context.args[1:]).strip()
        except ValueError:
            await update.message.reply_text("معرف اللاعب يجب أن يكون رقمًا صحيحًا.")
            return

        guesser_name = next((p['name'] for p in game['players'] if p['id'] == guesser_id), "لاعب غير معروف")

        if game['game_type'] == '1v1':
            # Find the other player (the answerer)
            answerer_id = None
            for player_id in game['characters'].keys():
                if player_id != guesser_id:
                    answerer_id = player_id
                    break
            
            if not answerer_id:
                await update.message.reply_text("لا يمكن تحديد اللاعب الآخر (صاحب الشخصية) في اللعبة.")
                return

            game['scores'][guesser_id] += 1
            await context.bot.send_message(
                chat_id,
                f"✅ **تمت الموافقة يدويًا!**\n\n"
                f"قام المشرف **{update.effective_user.first_name}** بالموافقة على تخمين **{guesser_name}** بأن الشخصية هي \"**{actual_character_name}**\" (أو ما يعادلها).\n"
                f"تم إضافة نقطة لـ **{guesser_name}**.",
                parse_mode='Markdown'
            )
            # End the round after manual approval
            await self.end_round(chat_id, context)

        elif game['game_type'] == 'teams':
            guesser_team_name = None
            for team_name, members in game['teams'].items():
                if guesser_id in [m['id'] for m in members]:
                    guesser_team_name = team_name
                    break

            if not guesser_team_name:
                await update.message.reply_text("اللاعب المحدد ليس في أي فريق حاليًا.")
                return

            # Award score to all players in the guessing team
            for player in game['teams'][guesser_team_name]:
                game['scores'][player['id']] += 1
            
            await context.bot.send_message(
                chat_id,
                f"✅ **تمت الموافقة يدويًا!**\n\n"
                f"قام المشرف **{update.effective_user.first_name}** بالموافقة على تخمين الفريق **{'الأزرق' if guesser_team_name == 'blue' else 'الأحمر'}** بأن الشخصية هي \"**{actual_character_name}**\" (أو ما يعادلها).\n"
                f"تم إضافة نقطة للفريق **{'الأزرق' if guesser_team_name == 'blue' else 'الأحمر'}**.",
                parse_mode='Markdown'
            )
            # End the round after manual approval
            await self.end_round(chat_id, context)


    def setup_handlers(self, application: Application):
        """Set up the bot's command and message handlers."""
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
    bot.run_bot(bot_token)
