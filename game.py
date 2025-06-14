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
        {"name": "ريد", "desc": "محتال سجين في شاوشانك", "link": "https://www.com/search?q=إليس+ريد+شاوشانك"},
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
            'pending_guess_confirmation': None, # This will no longer be used for /approve
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
        blue_team_names = ", ".join([p['name'] for p in game['teams']['blue']])
        red_team_names = ", ".join([p['name'] for p in game['teams']['red']])
        await context.bot.send_message(
            chat_id,
            f"🚀 اللعبة بدأت بين الفريق الأزرق ({blue_team_names}) والفريق الأحمر ({red_team_names})!"
        )
        await asyncio.sleep(2)
        await self.start_round(chat_id, context)

    async def start_round(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE):
        game = games[chat_id]
        if game['round'] > game['max_rounds']:
            await self.end_game(chat_id, context)
            return

        game['waiting_for_answer'] = False
        game['pending_guess_confirmation'] = None # Clear any pending confirmation
        game['question_asker'] = None
        game['answerer_id'] = None

        if game['game_type'] == '1v1':
            current_player_index = (game['round'] - 1) % len(game['players'])
            current_player = game['players'][current_player_index]
            
            # Determine the opposing player whose character needs to be guessed
            opponent_index = (current_player_index + 1) % len(game['players'])
            opponent_player = game['players'][opponent_index]
            
            game['question_asker'] = current_player['id']
            game['answerer_id'] = opponent_player['id']

            await context.bot.send_message(
                chat_id,
                f"--- **الجولة {game['round']}** ---\n\n"
                f" الدور الآن على اللاعب **{current_player['name']}**.\n"
                f"اللاعب **{current_player['name']}** يمكنه الآن طرح سؤال بنعم/لا أو محاولة التخمين.\n"
                f"اللاعب **{opponent_player['name']}** هو من يملك الشخصية التي سيتم تخمينها في هذه الجولة."
                "\n\n**تلميحات:**\n"
                "• لاستعادة الشخصية: /my_character\n"
                "• للسؤال: اكتب سؤالك بوضوح\n"
                "• للتخمين: اكتب `تخمين:` متبوعًا بالاسم الكامل للشخصية (مثال: `تخمين: ناروتو أوزوماكي`)\n"
                "• لتأكيد التخمين (من اللاعب صاحب الشخصية): /approve\n"
                "• لرفض التخمين (من اللاعب صاحب الشخصية): /deny",
                parse_mode='Markdown'
            )
        elif game['game_type'] == 'teams':
            # Alternate turns between blue and red teams
            current_team_name = game['current_team_turn']
            opponent_team_name = 'red' if current_team_name == 'blue' else 'blue'

            # Pick a random player from the current team to be the question asker (just for display)
            # In team mode, any member of the guessing team can make a guess/ask a question.
            # The character belongs to the entire opposing team.
            
            await context.bot.send_message(
                chat_id,
                f"--- **الجولة {game['round']}** ---\n\n"
                f"الدور الآن على الفريق **{'الأزرق' if current_team_name == 'blue' else 'الأحمر'}**.\n"
                f"يمكن لأي لاعب من الفريق **{'الأزرق' if current_team_name == 'blue' else 'الأحمر'}** طرح سؤال بنعم/لا أو محاولة التخمين.\n"
                f"الشخصية التي سيتم تخمينها تخص الفريق **{'الأحمر' if opponent_team_name == 'red' else 'الأزرق'}**.\n"
                "\n\n**تلميحات:**\n"
                "• لاستعادة شخصية فريقك: /my_team_character\n"
                "• للسؤال: اكتب سؤالك بوضوح\n"
                "• للتخمين: اكتب `تخمين:` متبوعًا بالاسم الكامل للشخصية (مثال: `تخمين: ناروتو أوزوماكي`)\n"
                "• لتأكيد التخمين (من أي لاعب في الفريق صاحب الشخصية): /approve\n"
                "• لرفض التخمين (من أي لاعب في الفريق صاحب الشخصية): /deny",
                parse_mode='Markdown'
            )
            game['current_team_turn'] = opponent_team_name # Switch turn for the next round
        
        game['waiting_for_answer'] = True # Bot is now waiting for a question/guess
        
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        text = update.message.text

        game = games.get(chat_id)

        if not game or game.get('status') != 'playing':
            return # Not in a game or game not in playing state

        if text.lower().startswith("تخمين:"):
            await self.handle_guess(update, context, text)
        else:
            await self.handle_question(update, context, text)
            

    async def handle_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        question = update.message.text
        
        game = games.get(chat_id)

        if game['game_type'] == '1v1':
            if user_id != game['question_asker']:
                await update.message.reply_text("هذا ليس دورك للسؤال.")
                return
            
            answerer_player = next((p for p in game['players'] if p['id'] == game['answerer_id']), None)
            if not answerer_player:
                logger.error(f"Answerer not found in game {chat_id}")
                return

            keyboard = [[
                InlineKeyboardButton("نعم", callback_data=f"answer_yes_{user_id}"),
                InlineKeyboardButton("لا", callback_data=f"answer_no_{user_id}")
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            try:
                # Send private message to the answerer for their response
                await context.bot.send_message(
                    chat_id=game['answerer_id'],
                    text=f"لقد سألك اللاعب **{update.effective_user.first_name}**: \"{question}\"\n\n"
                         "الرجاء استخدام الأزرار في رسالتي الخاصة للإجابة.",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                await update.message.reply_text(
                    f"تم إرسال سؤالك إلى **{answerer_player['name']}**.\n"
                    f"ينتظر منك **{answerer_player['name']}** الإجابة في رسالته الخاصة."
                )
            except Exception as e:
                logger.error(f"Failed to send private message for answer to {game['answerer_id']}: {e}")
                await update.message.reply_text(
                    f"⚠️ لم أتمكن من إرسال رسالة خاصة إلى {answerer_player['name']}. "
                    "الرجاء التأكد من أنهم بدأوا محادثة معي أولاً!"
                )
                
        elif game['game_type'] == 'teams':
            current_team_name = game['current_team_turn']
            guessing_team_ids = [p['id'] for p in game['teams'][current_team_name]]
            
            if user_id not in guessing_team_ids:
                await update.message.reply_text("هذا ليس دور فريقك للسؤال.")
                return

            opponent_team_name = 'red' if current_team_name == 'blue' else 'blue'
            opponent_team_members = game['teams'][opponent_team_name]

            if not opponent_team_members:
                logger.error(f"Opponent team members not found in game {chat_id}")
                return

            keyboard = [[
                InlineKeyboardButton("نعم", callback_data=f"answer_yes_team_{current_team_name}"), # Store guessing team
                InlineKeyboardButton("لا", callback_data=f"answer_no_team_{current_team_name}") # Store guessing team
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Send private message to ALL members of the opposing team for their response
            for player in opponent_team_members:
                try:
                    await context.bot.send_message(
                        chat_id=player['id'],
                        text=f"لقد سألك الفريق **{'الأزرق' if current_team_name == 'blue' else 'الأحمر'}**: \"{question}\"\n\n"
                             "الرجاء استخدام الأزرار في رسالتي الخاصة للإجابة. (جميع أعضاء فريقك سيشاهدون هذا السؤال)",
                        reply_markup=reply_markup,
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    logger.error(f"Failed to send private message for team answer to {player['id']}: {e}")
                    await context.bot.send_message(
                        chat_id,
                        f"⚠️ لم أتمكن من إرسال رسالة خاصة إلى {player['name']} من الفريق {'الأزرق' if opponent_team_name == 'blue' else 'الأحمر'}. "
                        "الرجاء التأكد من أنهم بدأوا محادثة معي أولاً! قد يؤثر هذا على سير اللعبة."
                    )
            
            await update.message.reply_text(
                f"تم إرسال سؤال فريقك إلى الفريق **{'الأحمر' if opponent_team_name == 'red' else 'الأزرق'}**.\n"
                f"ينتظر فريقك الإجابة منهم في رسائلهم الخاصة."
            )
            # Store who asked the question in team mode, so we know whose turn it is
            game['question_asker'] = user_id 
            game['waiting_for_answer'] = True # Set this true when waiting for answer

    async def answer_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        chat_id = query.message.chat_id # This is the private chat ID with the bot
        user_id = query.from_user.id
        data = query.data

        # Extract original group chat ID from context.user_data or find it.
        # This assumes the bot keeps track of the active game for each user.
        # A more robust solution might pass the group chat ID in the callback data.
        group_chat_id = None
        for gc_id, game_data in games.items():
            if game_data.get('status') == 'playing':
                if game_data['game_type'] == '1v1' and user_id in [p['id'] for p in game_data['players']]:
                    group_chat_id = gc_id
                    break
                elif game_data['game_type'] == 'teams':
                    for team_name, members in game_data['teams'].items():
                        if user_id in [p['id'] for p in members]:
                            group_chat_id = gc_id
                            break
            if group_chat_id:
                break

        if not group_chat_id:
            await query.edit_message_text("لا توجد لعبة نشطة في أي مجموعة تشارك فيها.")
            return

        game = games.get(group_chat_id)
        if not game or game.get('status') != 'playing' or not game.get('waiting_for_answer'):
            await query.edit_message_text("هذه الجولة قد انتهت أو لا توجد لعبة نشطة تنتظر إجابة.")
            return

        answer_type = data.split('_')[1] # 'yes' or 'no'
        
        # Check if the user is the actual answerer in 1v1 or part of the answering team in team mode
        if game['game_type'] == '1v1':
            if user_id != game['answerer_id']:
                await query.answer("أنت لست الشخص الذي يجب أن يجيب على هذا السؤال.", show_alert=True)
                return
        elif game['game_type'] == 'teams':
            guessing_team_name_from_callback = data.split('_')[2]
            opponent_team_name = 'blue' if guessing_team_name_from_callback == 'red' else 'red'
            
            if user_id not in [p['id'] for p in game['teams'][opponent_team_name]]:
                 await query.answer("أنت لست جزءًا من الفريق الذي يجب أن يجيب على هذا السؤال.", show_alert=True)
                 return
            
            # For teams, any member of the opponent team can answer. Once one answers, the question is answered.
            # We need to make sure the same question isn't answered multiple times.
            if not game['waiting_for_answer']:
                await query.edit_message_text("هذا السؤال تم الإجابة عليه بالفعل.")
                return

        game['waiting_for_answer'] = False # Question has been answered

        question_asker_name = next((p['name'] for p in game['players'] if p['id'] == game['question_asker']), "لاعب غير معروف")

        if answer_type == 'yes':
            answer_text = "نعم"
            await context.bot.send_message(group_chat_id, f"✅ الإجابة على السؤال هي: **نعم**.", parse_mode='Markdown')
        else:
            answer_text = "لا"
            await context.bot.send_message(group_chat_id, f"❌ الإجابة على السؤال هي: **لا**.", parse_mode='Markdown')

        await query.edit_message_text(f"لقد أجبت على السؤال بـ: **{answer_text}**.", parse_mode='Markdown')

        await asyncio.sleep(1) # Give time for messages to send
        
        # Advance to the next round if no guess was made or if it's a team game
        # In 1v1, the question asker gets another turn to guess.
        # In team game, the turn always switches.
        if game['game_type'] == '1v1':
            # The question asker now has the opportunity to guess.
            # No need to advance round immediately. The game waits for a guess or /end_turn.
            pass
        elif game['game_type'] == 'teams':
            # For team mode, the turn always switches after a question is answered.
            game['round'] += 1
            await self.start_round(group_chat_id, context)

    async def handle_guess(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        guesser_name = update.effective_user.first_name
        guessed_char_name = text.replace("تخمين:", "").strip()

        game = games.get(chat_id)

        if not game or game.get('status') != 'playing':
            return await update.message.reply_text("لا توجد لعبة نشطة حالياً.")

        if game['game_type'] == '1v1':
            # Check if it's the current player's turn to guess
            current_player_index = (game['round'] - 1) % len(game['players'])
            current_player = game['players'][current_player_index]
            if user_id != current_player['id']:
                await update.message.reply_text("هذا ليس دورك للتخمين.")
                return
            
            # Identify the opponent whose character is being guessed
            opponent_index = (current_player_index + 1) % len(game['players'])
            opponent_player = game['players'][opponent_index]
            opponent_character = game['characters'][opponent_player['id']]
            
            game['question_asker'] = user_id # The guesser
            game['answerer_id'] = opponent_player['id'] # The one who owns the character and approves/denies
            game['guessed_character_name'] = guessed_char_name # Store the guessed character name
            
            # Instead of sending confirmation, we'll wait for /approve from the answerer
            await context.bot.send_message(
                chat_id,
                f"**{guesser_name}** خمن شخصية **{guessed_char_name}**!\n"
                f"يا **{opponent_player['name']}**، يرجى استخدام الأمر `/approve` لتأكيد التخمين "
                "إذا كان صحيحاً، أو `/deny` إذا كان خاطئاً.",
                parse_mode='Markdown'
            )

        elif game['game_type'] == 'teams':
            current_team_name = game['current_team_turn']
            guessing_team_ids = [p['id'] for p in game['teams'][current_team_name]]

            if user_id not in guessing_team_ids:
                await update.message.reply_text("هذا ليس دور فريقك للتخمين.")
                return

            opponent_team_name = 'red' if current_team_name == 'blue' else 'blue'
            opponent_character = game['team_characters'][opponent_team_name]

            # Store information for the approval process
            game['question_asker'] = user_id # The player who made the guess
            game['answerer_id'] = opponent_team_name # The team that needs to approve/deny
            game['guessed_character_name'] = guessed_char_name

            await context.bot.send_message(
                chat_id,
                f"الفريق **{'الأزرق' if current_team_name == 'blue' else 'الأحمر'}** (بواسطة **{guesser_name}**) خمن شخصية **{guessed_char_name}**!\n"
                f"يا أعضاء الفريق **{'الأحمر' if opponent_team_name == 'red' else 'الأزرق'}**، يرجى استخدام الأمر `/approve` لتأكيد التخمين "
                "إذا كان صحيحاً، أو `/deny` إذا كان خاطئاً.",
                parse_mode='Markdown'
            )
        game['waiting_for_answer'] = True # Still waiting for the approve/deny command

    async def approve_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        username = update.effective_user.first_name

        game = games.get(chat_id)

        if not game or game.get('status') != 'playing' or not game.get('guessed_character_name'):
            await update.message.reply_text("لا يوجد تخمين معلق للموافقة عليه حالياً.")
            return

        guesser_id = game['question_asker']
        guessed_char_name = game['guessed_character_name']

        if game['game_type'] == '1v1':
            # In 1v1, only the answerer can approve.
            if user_id != game['answerer_id']:
                await update.message.reply_text("أنت لست اللاعب الذي يمكنه تأكيد هذا التخمين.")
                return

            opponent_player_id = game['answerer_id']
            opponent_character = game['characters'][opponent_player_id]

            if guessed_char_name.lower() == opponent_character['name'].lower():
                guesser_player = next((p for p in game['players'] if p['id'] == guesser_id), None)
                if guesser_player:
                    game['scores'][guesser_id] += 1
                    await update.message.reply_text(
                        f"🎉 **{username} أكد التخمين!**\n"
                        f"التخمين كان صحيحاً! **{guesser_player['name']}** يحصل على نقطة!\n"
                        f"الشخصية الصحيحة كانت: **{opponent_character['name']}**.",
                        parse_mode='Markdown'
                    )
                else:
                    await update.message.reply_text(f"🎉 **{username} أكد التخمين!**\n"
                                                    "التخمين كان صحيحاً! تم منح نقطة للاعب المخمن.\n"
                                                    f"الشخصية الصحيحة كانت: **{opponent_character['name']}**.",
                                                    parse_mode='Markdown')
                
                game['round'] += 1
                await self.start_round(chat_id, context)
            else:
                await update.message.reply_text(
                    f"❌ **{username} أكد التخمين، ولكن التخمين ({guessed_char_name}) لم يكن صحيحاً.**\n"
                    f"الشخصية الصحيحة لم تكن **{guessed_char_name}**.",
                    parse_mode='Markdown'
                )
                # If guess is incorrect, it's still a turn lost, so move to next round
                game['round'] += 1
                await self.start_round(chat_id, context)

        elif game['game_type'] == 'teams':
            # In teams, any member of the opposing team can approve.
            opponent_team_name = game['answerer_id'] # This now stores the team name ('blue' or 'red')
            if user_id not in [p['id'] for p in game['teams'][opponent_team_name]]:
                await update.message.reply_text("أنت لست جزءًا من الفريق الذي يمكنه تأكيد هذا التخمين.")
                return

            opponent_character = game['team_characters'][opponent_team_name]

            if guessed_char_name.lower() == opponent_character['name'].lower():
                guesser_team_name = 'blue' if opponent_team_name == 'red' else 'red'
                
                # Find the player who made the guess to credit them if needed, or simply update team score
                guesser_player_obj = next((p for p in game['players'] if p['id'] == guesser_id), None)
                
                # Update scores for all players in the guessing team
                for player in game['teams'][guesser_team_name]:
                    game['scores'][player['id']] += 1
                
                await update.message.reply_text(
                    f"🎉 **{username} أكد التخمين!**\n"
                    f"التخمين كان صحيحاً! الفريق **{'الأزرق' if guesser_team_name == 'blue' else 'الأحمر'}** يحصل على نقطة!\n"
                    f"الشخصية الصحيحة كانت: **{opponent_character['name']}**.",
                    parse_mode='Markdown'
                )
                game['round'] += 1
                await self.start_round(chat_id, context)
            else:
                await update.message.reply_text(
                    f"❌ **{username} أكد التخمين، ولكن التخمين ({guessed_char_name}) لم يكن صحيحاً.**\n"
                    f"الشخصية الصحيحة لم تكن **{guessed_char_name}**.",
                    parse_mode='Markdown'
                )
                game['round'] += 1
                await self.start_round(chat_id, context)
        
        # Clear the pending guess data after approval/denial logic
        game['guessed_character_name'] = None
        game['question_asker'] = None
        game['answerer_id'] = None
        game['waiting_for_answer'] = False # Reset waiting for answer

    async def deny_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        username = update.effective_user.first_name

        game = games.get(chat_id)

        if not game or game.get('status') != 'playing' or not game.get('guessed_character_name'):
            await update.message.reply_text("لا يوجد تخمين معلق لرفضه حالياً.")
            return

        guesser_id = game['question_asker']
        guessed_char_name = game['guessed_character_name']

        if game['game_type'] == '1v1':
            if user_id != game['answerer_id']:
                await update.message.reply_text("أنت لست اللاعب الذي يمكنه رفض هذا التخمين.")
                return

            guesser_player = next((p for p in game['players'] if p['id'] == guesser_id), None)
            
            await update.message.reply_text(
                f"❌ **{username} رفض التخمين!**\n"
                f"التخمين **{guessed_char_name}** كان خاطئاً.\n"
                f"الجولة تنتهي.",
                parse_mode='Markdown'
            )
            
        elif game['game_type'] == 'teams':
            opponent_team_name = game['answerer_id']
            if user_id not in [p['id'] for p in game['teams'][opponent_team_name]]:
                await update.message.reply_text("أنت لست جزءًا من الفريق الذي يمكنه رفض هذا التخمين.")
                return
            
            guesser_team_name = 'blue' if opponent_team_name == 'red' else 'red'
            
            await update.message.reply_text(
                f"❌ **{username} رفض التخمين!**\n"
                f"التخمين **{guessed_char_name}** من الفريق **{'الأزرق' if guesser_team_name == 'blue' else 'الأحمر'}** كان خاطئاً.\n"
                "الجولة تنتهي.",
                parse_mode='Markdown'
            )

        # Clear the pending guess data after approval/denial logic
        game['guessed_character_name'] = None
        game['question_asker'] = None
        game['answerer_id'] = None
        game['waiting_for_answer'] = False # Reset waiting for answer
        
        game['round'] += 1
        await self.start_round(chat_id, context)

    async def my_character_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id

        game = games.get(chat_id)

        if not game or game.get('status') != 'playing' or game.get('game_type') != '1v1':
            await update.message.reply_text("هذه الميزة متاحة فقط في ألعاب 1 ضد 1 النشطة.")
            return

        character_info = game['characters'].get(user_id)
        if character_info:
            await update.message.reply_text(
                f"🎭 **شخصيتك في اللعبة:**\n\n**الاسم:** {character_info['name']}\n"
                f"**الفئة:** {character_info['category']}\n**الوصف:** {character_info['desc']}\n\n"
                f"🔗 [معلومات إضافية]({character_info['link']})\n\n⚠️ احتفظ بهذه المعلومات سرية!",
                parse_mode='Markdown', disable_web_page_preview=True
            )
        else:
            await update.message.reply_text("ليس لديك شخصية مخصصة في اللعبة الحالية.")

    async def my_team_character_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id

        game = games.get(chat_id)

        if not game or game.get('status') != 'playing' or game.get('game_type') != 'teams':
            await update.message.reply_text("هذه الميزة متاحة فقط في ألعاب الفرق النشطة.")
            return

        user_team = None
        for team_name, members in game['teams'].items():
            if user_id in [p['id'] for p in members]:
                user_team = team_name
                break

        if user_team:
            character_info = game['team_characters'].get(user_team)
            if character_info:
                await update.message.reply_text(
                    f"🎭 **شخصية فريقك ({'الأزرق' if user_team == 'blue' else 'الأحمر'}) في اللعبة:**\n\n"
                    f"**الاسم:** {character_info['name']}\n"
                    f"**الفئة:** {character_info['category']}\n"
                    f"**الوصف:** {character_info['desc']}\n\n"
                    f"🔗 [معلومات إضافية]({character_info['link']})\n\n⚠️ احتفظ بهذه المعلومات سرية من الفريق الخصم!",
                    parse_mode='Markdown', disable_web_page_preview=True
                )
            else:
                await update.message.reply_text("لا توجد شخصية مخصصة لفريقك في اللعبة الحالية.")
        else:
            await update.message.reply_text("أنت لست جزءًا من فريق في اللعبة الحالية.")

    async def score_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        game = games.get(chat_id)

        if not game:
            await update.message.reply_text("لا توجد لعبة نشطة في هذه المجموعة.")
            return

        if game['game_type'] == '1v1':
            score_message = "Current Scores (1v1):\n"
            for player_id, score in game['scores'].items():
                player_name = next((p['name'] for p in game['players'] if p['id'] == player_id), "Unknown Player")
                score_message += f"- {player_name}: {score} points\n"
        elif game['game_type'] == 'teams':
            team_scores = {'blue': 0, 'red': 0}
            for player_id, score in game['scores'].items():
                player_info = next((p for p in game['players'] if p['id'] == player_id), None)
                if player_info and 'team' in player_info:
                    team_scores[player_info['team']] += score
            
            score_message = "Current Team Scores:\n"
            score_message += f"🔵 الفريق الأزرق: {team_scores['blue']} نقطة\n"
            score_message += f"🔴 الفريق الأحمر: {team_scores['red']} نقطة\n"
        else:
            score_message = "لا يمكن عرض النقاط. نمط اللعبة غير محدد."

        await update.message.reply_text(score_message, parse_mode='Markdown')

    async def cancel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id

        game = games.get(chat_id)

        if not game:
            await update.message.reply_text("لا توجد لعبة نشطة لإلغائها.")
            return

        if not await self.is_admin(chat_id, user_id, context) and user_id != game['creator_id']:
            await update.message.reply_text("فقط من بدأ اللعبة أو المشرفين يمكنهم إلغاء اللعبة.")
            return

        del games[chat_id]
        await update.message.reply_text("تم إلغاء اللعبة بنجاح.")

    async def end_game(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE):
        game = games.get(chat_id)
        if not game:
            return

        if game['game_type'] == '1v1':
            await context.bot.send_message(chat_id, "🏆 **انتهت اللعبة!**")
            final_scores = sorted(game['scores'].items(), key=lambda item: item[1], reverse=True)
            
            winner_message = "النتائج النهائية:\n"
            if not final_scores:
                winner_message += "لا توجد نقاط مسجلة."
            else:
                for player_id, score in final_scores:
                    player_name = next((p['name'] for p in game['players'] if p['id'] == player_id), "Unknown Player")
                    winner_message += f"- {player_name}: {score} نقطة\n"

                # Determine winner(s)
                max_score = final_scores[0][1]
                winners = [p['name'] for p_id, score in final_scores if score == max_score]

                if len(winners) > 1:
                    winner_message += f"\nالتعادل بين: {', '.join(winners)}!"
                else:
                    winner_message += f"\nالفائز هو: **{winners[0]}**!"
        
        elif game['game_type'] == 'teams':
            await context.bot.send_message(chat_id, "🏆 **انتهت اللعبة!**")
            team_scores = {'blue': 0, 'red': 0}
            for player_id, score in game['scores'].items():
                player_info = next((p for p in game['players'] if p['id'] == player_id), None)
                if player_info and 'team' in player_info:
                    team_scores[player_info['team']] += score
            
            winner_message = "النتائج النهائية:\n"
            winner_message += f"🔵 الفريق الأزرق: {team_scores['blue']} نقطة\n"
            winner_message += f"🔴 الفريق الأحمر: {team_scores['red']} نقطة\n\n"

            if team_scores['blue'] > team_scores['red']:
                winner_message += "الفريق الفائز هو: **الفريق الأزرق**! 🎉"
            elif team_scores['red'] > team_scores['blue']:
                winner_message += "الفريق الفائز هو: **الفريق الأحمر**! 🎉"
            else:
                winner_message += "تعادل بين الفريقين!"

        await context.bot.send_message(chat_id, winner_message, parse_mode='Markdown')
        del games[chat_id] # Clear game data

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_text = """
👋 **مرحباً بك في لعبة تخمين الشخصيات!**

إليك كيفية اللعب:

**للبدء:**
* `/start`: لبدء لعبة جديدة. (يحتاج لمشرف المجموعة أو منشئ اللعبة)
* بعد البدء، سيطلب منك اختيار فئة (أنمي، أفلام، كرة قدم، أعلام دول، ألعاب فيديو) ثم نمط اللعب (1 ضد 1 أو فرق).

**أثناء اللعب (1 ضد 1):**
* يتناوب اللاعبون على طرح الأسئلة أو التخمين.
* **لطرح سؤال:** اكتب سؤالك مباشرة في الدردشة. سيتلقى اللاعب صاحب الشخصية رسالة خاصة للإجابة بنعم أو لا.
* **للتخمين:** اكتب `تخمين:` متبوعًا بالاسم الكامل للشخصية. مثال: `تخمين: ناروتو أوزوماكي`
* **لتأكيد التخمين (من اللاعب صاحب الشخصية المخمنة):** `/approve`
* **لرفض التخمين (من اللاعب صاحب الشخصية المخمنة):** `/deny`
* `/my_character`: لمعرفة الشخصية الخاصة بك (في رسالة خاصة).
* `/score`: لعرض النتائج الحالية.

**أثناء اللعب (فرق):**
* يتناوب فريقان (الأزرق والأحمر) على طرح الأسئلة أو التخمين.
* **لطرح سؤال:** اكتب سؤالك مباشرة في الدردشة. سيتلقى كل عضو في الفريق الخصم رسالة خاصة للإجابة بنعم أو لا.
* **للتخمين:** اكتب `تخمين:` متبوعًا بالاسم الكامل للشخصية. مثال: `تخمين: كريستيانو رونالدو`
* **لتأكيد التخمين (من أي لاعب في الفريق صاحب الشخصية المخمنة):** `/approve`
* **لرفض التخمين (من أي لاعب في الفريق صاحب الشخصية المخمنة):** `/deny`
* `/my_team_character`: لمعرفة شخصية فريقك (في رسالة خاصة).
* `/score`: لعرض النتائج الحالية للفرق.

**الأوامر العامة:**
* `/cancel`: لإلغاء اللعبة الحالية. (يحتاج لمشرف المجموعة أو منشئ اللعبة)
* `/help`: لعرض هذه الرسالة المساعدة.

استمتعوا باللعب! 🚀
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')

    def run(self):
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            logger.error("TELEGRAM_BOT_TOKEN environment variable not set.")
            sys.exit(1)

        self.application = Application.builder().token(token).build()

        # Command Handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("approve", self.approve_command)) # Keep as CommandHandler
        self.application.add_handler(CommandHandler("deny", self.deny_command))     # Keep as CommandHandler
        self.application.add_handler(CommandHandler("my_character", self.my_character_command))
        self.application.add_handler(CommandHandler("my_team_character", self.my_team_character_command))
        self.application.add_handler(CommandHandler("score", self.score_command))
        self.application.add_handler(CommandHandler("cancel", self.cancel_command))
        self.application.add_handler(CommandHandler("help", self.help_command))


        # Callback Query Handlers (for inline keyboard buttons)
        self.application.add_handler(CallbackQueryHandler(self.select_category_callback, pattern=r"^select_category_"))
        self.application.add_handler(CallbackQueryHandler(self.select_mode_callback, pattern=r"^select_mode_"))
        self.application.add_handler(CallbackQueryHandler(self.select_team_size_callback, pattern=r"^select_team_size_"))
        self.application.add_handler(CallbackQueryHandler(self.join_game_1v1_callback, pattern=r"^join_game_1v1"))
        self.application.add_handler(CallbackQueryHandler(self.join_team_callback, pattern=r"^join_team_"))
        self.application.add_handler(CallbackQueryHandler(self.start_teams_game_callback, pattern=r"^start_teams_game"))
        self.application.add_handler(CallbackQueryHandler(self.answer_callback, pattern=r"^(answer_yes_|answer_no_)"))


        # Message Handler (for questions and guesses)
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

        logger.info("Bot started polling.")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    bot = GameBot()
    bot.run()
