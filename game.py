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

# Character library
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
    "شخصيات الفانتازيا والأساطير": [
        {"name": "غاندالف", "desc": "ساحر قوي ومرشد في أرض الوسط", "link": "https://www.google.com/search?q=غاندالف"},
        {"name": "أرغورن", "desc": "وارث عرش غوندور وقائد شجاع", "link": "https://www.google.com/search?q=أرغورن"},
        {"name": "ليجولاس", "desc": "قزم بارع في استخدام القوس والسهم", "link": "https://www.google.com/search?q=ليجولاس"},
        {"name": "فرودو باجنز", "desc": "هوبيت يحمل الخاتم الأوحد لتدميره", "link": "https://www.google.com/search?q=فرودو+باجنز"},
        {"name": "سارومان", "desc": "ساحر قوي تحول إلى الشر", "link": "https://www.google.com/search?q=سارومان"},
        {"name": "ملكة الثلج (إلسا)", "desc": "ملكة تمتلك القدرة على التحكم بالجليد والثلوج", "link": "https://www.google.com/search?q=ملكة+الثلج+إلسا"},
        {"name": "هرقل", "desc": "نصف إله يوناني يمتلك قوة خارقة", "link": "https://www.google.com/search?q=هرقل+أسطورة"},
        {"name": "زيوس", "desc": "ملك آلهة الأوليمب وحاكم السماء والرعد", "link": "https://www.google.com/search?q=زيوس"},
        {"name": "ميدوسا", "desc": "كائن أسطوري يوناني بشعر من الثعابين يحول الناظرين إليه إلى حجر", "link": "https://www.google.com/search?q=ميدوسا"},
        {"name": "آرثر بيندراغون", "desc": "ملك بريطانيا الأسطوري وصاحب السيف إكسكاليبور", "link": "https://www.google.com/search?q=الملك+آرثر"}
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
        self.application: Optional[Application] = None
        self.game_timeout_task: Dict[int, asyncio.Task] = {}
        self.game_active_message: Dict[int, int] = {} # To store message_id for game status updates

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
                        f"⚠️ لم أتمكن من إرسال رسالة خاصة إلى {player['name']} في الفريق {team_name}. "
                        "الرجاء التأكد من أن جميع اللاعبين بدؤوا محادثة معي أولاً! سيتم إلغاء اللعبة."
                    )
                    del games[chat_id]
                    return

        await context.bot.send_message(chat_id, "🚀 اللعبة بدأت بين الفرق!")
        await asyncio.sleep(2)
        await self.start_round(chat_id, context)

    async def start_round(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE):
        game = games[chat_id]
        if game['round'] > game['max_rounds']:
            await self.end_game(chat_id, context)
            return

        game['waiting_for_answer'] = False
        game['question_asker'] = None
        game['answerer_id'] = None
        game['pending_guess_confirmation'] = None

        await context.bot.send_message(chat_id, f"🌟 **بدء الجولة {game['round']}!** 🌟", parse_mode='Markdown')
        await asyncio.sleep(1)

        if game['game_type'] == '1v1':
            player_1 = game['players'][0]
            player_2 = game['players'][1]

            # Determine who asks and who answers
            # In 1v1, they take turns asking. Player 1 asks in round 1, Player 2 answers.
            # In round 2, Player 2 asks, Player 1 answers.
            if game['round'] % 2 != 0: # Odd rounds: Player 1 asks, Player 2 answers
                game['question_asker'] = player_1
                game['answerer_id'] = player_2['id']
            else: # Even rounds: Player 2 asks, Player 1 answers
                game['question_asker'] = player_2
                game['answerer_id'] = player_1['id']

            answerer_character = game['characters'][game['answerer_id']]

            # Inform the question asker
            await context.bot.send_message(
                chat_id=game['question_asker']['id'],
                text=f"دورك لطرح سؤال نعم/لا لـ {self.get_player_name(game['answerer_id'], game['players'])}!\n"
                     f"يمكنك السؤال عن شخصية {answerer_character['name']} (التي يعرفها {self.get_player_name(game['answerer_id'], game['players'])})."
            )
            # Inform the group
            await context.bot.send_message(
                chat_id,
                f"**{game['question_asker']['name']}** يطرح سؤالاً في الجولة {game['round']}!\n"
                f"على **{self.get_player_name(game['answerer_id'], game['players'])}** الإجابة في الخاص."
                "\n\nيمكن للاعبين الآخرين تخمين الشخصية في أي وقت بكتابة اسمها مباشرة في المجموعة.",
                parse_mode='Markdown'
            )
            game['waiting_for_answer'] = True

        elif game['game_type'] == 'teams':
            current_team_name = game['current_team_turn']
            other_team_name = 'red' if current_team_name == 'blue' else 'blue'

            # Assign a random player from the current team to be the question asker
            asker_player = random.choice(game['teams'][current_team_name])
            game['question_asker'] = asker_player
            game['answerer_id'] = None # No specific answerer in teams, it's about the character.

            await context.bot.send_message(
                chat_id=asker_player['id'],
                text=f"دورك يا {asker_player['name']} من الفريق {'الأزرق' if current_team_name == 'blue' else 'الأحمر'} لطرح سؤال نعم/لا!\n"
                     f"يمكنك السؤال عن شخصية الفريق الخصم ({'الأزرق' if other_team_name == 'blue' else 'الأحمر'})."
            )
            await context.bot.send_message(
                chat_id,
                f"دور **الفريق {'الأزرق' if current_team_name == 'blue' else 'الأحمر'}**! 🔵🔴\n"
                f"اللاعب **{asker_player['name']}** سيطرح سؤالاً.\n\n"
                "يمكن للاعبين تخمين الشخصية في أي وقت بكتابة اسمها مباشرة في المجموعة.",
                parse_mode='Markdown'
            )
            game['waiting_for_answer'] = True

        # Start a timeout for the turn
        if chat_id in self.game_timeout_task:
            self.game_timeout_task[chat_id].cancel()
        self.game_timeout_task[chat_id] = asyncio.create_task(self.turn_timeout(chat_id, context))


    async def turn_timeout(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE):
        game = games[chat_id]
        if game['game_type'] == '1v1':
            timeout_message = f"انتهى وقت سؤال {game['question_asker']['name']}! سيتم الانتقال إلى الجولة التالية."
        else: # teams
            current_team_name = game['current_team_turn']
            timeout_message = f"انتهى وقت سؤال الفريق {'الأزرق' if current_team_name == 'blue' else 'الأحمر'}! سيتم الانتقال إلى الجولة التالية."

        await asyncio.sleep(60) # 60 seconds for a turn
        if game['waiting_for_answer']: # If still waiting for an answer
            await context.bot.send_message(chat_id, timeout_message)
            game['round'] += 1 # Advance round if no question asked/answered in time
            await self.start_round(chat_id, context)


    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name

        if not update.message or not update.message.text: # Added this check
            logger.warning(f"Received an update in handle_message without text: {update}")
            return # Ignore updates without text

        message_text = update.message.text.strip()

        game = games.get(chat_id)
        if not game or game.get('status') != 'playing':
            return # Not in an active game or not in playing state

        if game['game_type'] == '1v1':
            question_asker = game['question_asker']
            answerer_id = game['answerer_id']

            # Check if it's the current question asker
            if question_asker and user_id == question_asker['id'] and game['waiting_for_answer']:
                if '?' in message_text:
                    # Player is asking a question
                    game['waiting_for_answer'] = False # Question asked, now waiting for answer
                    game['question_text'] = message_text # Store the question
                    game['question_asker'] = question_asker # Ensure this is preserved

                    target_character = game['characters'][answerer_id]
                    keyboard = [
                        [InlineKeyboardButton("✅ نعم", callback_data=f"answer_yes_{user_id}"),
                         InlineKeyboardButton("❌ لا", callback_data=f"answer_no_{user_id}")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)

                    await context.bot.send_message(
                        chat_id=answerer_id,
                        text=f"شخصيتك هي: **{target_character['name']}**\n\n"
                             f"**{question_asker['name']} يسألك:** \"{message_text}\"\n\n"
                             f"الرجاء الإجابة بنعم أو لا:",
                        reply_markup=reply_markup,
                        parse_mode='Markdown'
                    )
                    await context.bot.send_message(chat_id, f"**{question_asker['name']}** طرح سؤالاً. **{self.get_player_name(answerer_id, game['players'])}** يجيب في الخاص.", parse_mode='Markdown')

                    # Cancel old timeout, start new one for answer
                    if chat_id in self.game_timeout_task:
                        self.game_timeout_task[chat_id].cancel()
                    self.game_timeout_task[chat_id] = asyncio.create_task(self.answer_timeout(chat_id, context, question_asker['id']))
                else:
                    await update.message.reply_text("الرجاء طرح سؤال بصيغة نعم/لا. يجب أن يحتوي على علامة استفهام '؟'.")
                return

            # Allow any player (not the asker or answerer) to guess
            if user_id not in [p['id'] for p in game['players'] if p['id'] == question_asker['id'] or p['id'] == answerer_id]:
                # If a guess is made
                guesser = self.get_player_by_id(user_id, game['players'])
                await self.process_guess(chat_id, context, guesser, message_text)
                return

        elif game['game_type'] == 'teams':
            current_team_name = game['current_team_turn']
            asker_player = game['question_asker']

            # Only a player from the current team can ask
            is_player_in_current_team = any(p['id'] == user_id for p in game['teams'][current_team_name])

            if is_player_in_current_team and game['waiting_for_answer'] and user_id == asker_player['id']:
                if '?' in message_text:
                    # Player is asking a question for their team
                    game['waiting_for_answer'] = False
                    game['question_text'] = message_text
                    # The opponent team will answer the character they hold
                    opponent_team_name = 'red' if current_team_name == 'blue' else 'blue'
                    opponent_character = game['team_characters'][opponent_team_name]

                    # Inform the opponent team
                    for opponent_player in game['teams'][opponent_team_name]:
                        keyboard = [
                            [InlineKeyboardButton("✅ نعم", callback_data=f"team_answer_yes_{user_id}"),
                             InlineKeyboardButton("❌ لا", callback_data=f"team_answer_no_{user_id}")]
                        ]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        try:
                            await context.bot.send_message(
                                chat_id=opponent_player['id'],
                                text=f"شخصية فريقكم هي: **{opponent_character['name']}**\n\n"
                                     f"**{user_name} من الفريق {'الأزرق' if current_team_name == 'blue' else 'الأحمر'} يسأل:** \"{message_text}\"\n\n"
                                     f"الرجاء الإجابة بنعم أو لا نيابة عن فريقك. (أي عضو من الفريق يمكنه الإجابة)",
                                reply_markup=reply_markup,
                                parse_mode='Markdown'
                            )
                        except Exception as e:
                            logger.error(f"Failed to send private message to {opponent_player['id']}: {e}")
                            await context.bot.send_message(
                                chat_id,
                                f"⚠️ لم أتمكن من إرسال رسالة خاصة إلى {opponent_player['name']}. الرجاء التأكد من أن جميع اللاعبين بدؤوا محادثة معي أولاً!"
                            )

                    await context.bot.send_message(
                        chat_id,
                        f"**{user_name} من الفريق {'الأزرق' if current_team_name == 'blue' else 'الأحمر'}** طرح سؤالاً!\n"
                        f"على **الفريق {'الأزرق' if opponent_team_name == 'blue' else 'الأحمر'}** الإجابة في الخاص.",
                        parse_mode='Markdown'
                    )

                    # Cancel old timeout, start new one for team answer
                    if chat_id in self.game_timeout_task:
                        self.game_timeout_task[chat_id].cancel()
                    self.game_timeout_task[chat_id] = asyncio.create_task(self.answer_timeout(chat_id, context, user_id)) # Pass asker ID
                else:
                    await update.message.reply_text("الرجاء طرح سؤال بصيغة نعم/لا. يجب أن يحتوي على علامة استفهام '؟'.")
                return

            # Allow any player (not the current team asker) to guess
            if not is_player_in_current_team: # This means it's a player from the opponent team
                guesser = self.get_player_by_id(user_id, game['players'])
                await self.process_guess(chat_id, context, guesser, message_text)
                return


    async def answer_timeout(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE, asker_id: int):
        game = games[chat_id]
        asker_name = self.get_player_name(asker_id, game['players'])
        timeout_message = f"انتهى وقت إجابة السؤال الذي طرحه {asker_name}! سيتم الانتقال إلى الجولة التالية."
        await asyncio.sleep(60) # 60 seconds for an answer
        if not game['waiting_for_answer']: # If the answer was given, this will be False
            return # Answer was received, no timeout needed

        await context.bot.send_message(chat_id, timeout_message)
        game['round'] += 1 # Advance round if no answer in time
        await self.start_round(chat_id, context)


    async def callback_query_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()
        chat_id = query.message.chat_id
        user_id = query.from_user.id
        data = query.data

        game = games.get(chat_id)

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
        elif data.startswith("answer_"):
            # This is for 1v1 game mode
            if not game or game.get('status') != 'playing' or user_id != game['answerer_id']:
                await query.answer("لا يمكنك الإجابة الآن.", show_alert=True)
                return

            original_asker_id = int(data.split('_')[2])
            answer = "نعم" if data.startswith("answer_yes") else "لا"

            game['waiting_for_answer'] = False # Answer received

            await query.edit_message_text(f"أجبت: **{answer}**", parse_mode='Markdown')
            await context.bot.send_message(
                chat_id,
                f"**{query.from_user.first_name}** أجاب: **{answer}** على سؤال **{self.get_player_name(original_asker_id, game['players'])}**.",
                parse_mode='Markdown'
            )
            # Cancel current answer timeout task
            if chat_id in self.game_timeout_task:
                self.game_timeout_task[chat_id].cancel()

            # Advance to the next turn/round
            game['round'] += 1
            await self.start_round(chat_id, context)

        elif data.startswith("team_answer_"):
            # This is for team game mode
            if not game or game.get('status') != 'playing':
                await query.answer("لا يمكنك الإجابة الآن.", show_alert=True)
                return

            user_team = next((team_name for team_name, members in game['teams'].items() if any(p['id'] == user_id for p in members)), None)
            if not user_team:
                await query.answer("أنت لست في فريق.", show_alert=True)
                return

            current_team_turn = game['current_team_turn']
            if user_team == current_team_turn: # Only opponent team answers
                 await query.answer("لا يمكنك الإجابة على سؤال طرحه فريقك الخاص.", show_alert=True)
                 return

            original_asker_id = int(data.split('_')[3])
            answer = "نعم" if data.startswith("team_answer_yes") else "لا"

            game['waiting_for_answer'] = False # Answer received

            await query.edit_message_text(f"أجبت: **{answer}**", parse_mode='Markdown')
            await context.bot.send_message(
                chat_id,
                f"**{query.from_user.first_name}** من الفريق {'الأزرق' if user_team == 'blue' else 'الأحمر'} أجاب: **{answer}** على سؤال **{self.get_player_name(original_asker_id, game['players'])}**.",
                parse_mode='Markdown'
            )
            # Cancel current answer timeout task
            if chat_id in self.game_timeout_task:
                self.game_timeout_task[chat_id].cancel()

            # Switch turn to the other team
            game['current_team_turn'] = 'red' if current_team_turn == 'blue' else 'blue'
            game['round'] += 1 # Teams also advance rounds
            await self.start_round(chat_id, context)

        elif data.startswith("confirm_guess_"):
            action = data.split('_')[2] # 'yes' or 'no'
            guesser_id = game['pending_guess_confirmation']['guesser_id']
            guesser_name = self.get_player_name(guesser_id, game['players'])

            if action == 'yes':
                if game['game_type'] == '1v1':
                    await query.edit_message_text(f"✅ تم تأكيد التخمين: **{game['pending_guess_confirmation']['guess_text']}**!", parse_mode='Markdown')
                    await context.bot.send_message(chat_id, f"صحيح! **{guesser_name}** خمن الشخصية بنجاح: **{game['pending_guess_confirmation']['guess_text']}**! 🎉")
                    # Award points to the guesser
                    game['scores'][guesser_id] += 1
                elif game['game_type'] == 'teams':
                    await query.edit_message_text(f"✅ تم تأكيد التخمين: **{game['pending_guess_confirmation']['guess_text']}**!", parse_mode='Markdown')
                    guesser_team = next((p['team'] for p in game['players'] if p['id'] == guesser_id), None)
                    if guesser_team:
                        game['scores'][guesser_team] = game['scores'].get(guesser_team, 0) + 1
                        await context.bot.send_message(chat_id, f"صحيح! **{guesser_name}** من الفريق {'الأزرق' if guesser_team == 'blue' else 'الأحمر'} خمن شخصية الفريق الخصم بنجاح: **{game['pending_guess_confirmation']['guess_text']}**! 🎉")


                await self.end_game(chat_id, context) # End game on correct guess
            else: # action == 'no'
                await query.edit_message_text(f"❌ تم رفض التخمين: **{game['pending_guess_confirmation']['guess_text']}**.", parse_mode='Markdown')
                await context.bot.send_message(chat_id, f"التخمين من **{guesser_name}** غير صحيح. استمروا في التخمين!")
                # Revert game state to waiting for question/answer or next turn
                game['waiting_for_answer'] = True # Continue the current turn
                game['pending_guess_confirmation'] = None # Clear pending guess
                # Resume turn timeout if it was active
                if chat_id in self.game_timeout_task:
                    self.game_timeout_task[chat_id].cancel() # Cancel existing timeout
                await self.start_round(chat_id, context) # Restart turn to reset timeout and prompt for next action

            game['pending_guess_confirmation'] = None # Clear the pending confirmation

    async def process_guess(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE, guesser: dict, guess_text: str):
        game = games[chat_id]

        if game['pending_guess_confirmation']:
            await context.bot.send_message(chat_id, "يوجد تخمين معلق بالفعل، الرجاء الانتظار حتى يتم تأكيده أو رفضه.")
            return

        target_character_name = None
        if game['game_type'] == '1v1':
            # The guesser is trying to guess the *opponent's* character
            # Find the other player's ID
            opponent_id = next((p['id'] for p in game['players'] if p['id'] != guesser['id']), None)
            if opponent_id:
                target_character_name = game['characters'][opponent_id]['name']
        elif game['game_type'] == 'teams':
            # The guesser is trying to guess the *opponent team's* character
            guesser_team = next((p['team'] for p in game['players'] if p['id'] == guesser['id']), None)
            if guesser_team:
                opponent_team_name = 'red' if guesser_team == 'blue' else 'blue'
                target_character_name = game['team_characters'][opponent_team_name]['name']

        if target_character_name:
            game['pending_guess_confirmation'] = {
                'guesser_id': guesser['id'],
                'guess_text': guess_text,
                'target_character_name': target_character_name # Store for verification
            }

            keyboard = [
                [InlineKeyboardButton("✅ نعم، صحيح!", callback_data=f"confirm_guess_yes_{guesser['id']}"),
                 InlineKeyboardButton("❌ لا، غير صحيح", callback_data=f"confirm_guess_no_{guesser['id']}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Get the ID of the person who holds the character to confirm
            if game['game_type'] == '1v1':
                # In 1v1, the person who "owns" the character (the answerer for the current turn) confirms
                confirmer_id = game['answerer_id']
                confirmer_name = self.get_player_name(confirmer_id, game['players'])
                await context.bot.send_message(
                    chat_id=confirmer_id,
                    text=f"**{guesser['name']}** خمن شخصيتك: **{guess_text}**\n\n"
                         "الرجاء التأكيد أو الرفض:",
                    reply_markup=reply_markup, parse_mode='Markdown'
                )
                await context.bot.send_message(
                    chat_id,
                    f"**{guesser['name']}** خمن الشخصية بـ **{guess_text}**. "
                    f"**{confirmer_name}**، الرجاء التأكيد في الخاص.",
                    parse_mode='Markdown'
                )
            elif game['game_type'] == 'teams':
                # In teams, any member of the team whose character is being guessed can confirm
                confirmer_team = opponent_team_name
                confirmer_members = game['teams'][confirmer_team]
                await context.bot.send_message(
                    chat_id,
                    f"**{guesser['name']}** من الفريق {'الأزرق' if guesser_team == 'blue' else 'الأحمر'} خمن الشخصية بـ **{guess_text}**.\n"
                    f"يا أعضاء الفريق {'الأزرق' if confirmer_team == 'blue' else 'الأحمر'}، الرجاء من أي منكم تأكيد التخمين في الخاص.",
                    parse_mode='Markdown'
                )
                for member in confirmer_members:
                    try:
                        await context.bot.send_message(
                            chat_id=member['id'],
                            text=f"**{guesser['name']}** من الفريق الآخر خمن شخصية فريقكم: **{guess_text}**\n\n"
                                 "الرجاء التأكيد أو الرفض:",
                            reply_markup=reply_markup, parse_mode='Markdown'
                        )
                    except Exception as e:
                        logger.error(f"Failed to send private message to {member['id']}: {e}")
                        # Not critical, as other team members might still see it.


        # Pause current turn's flow until guess is confirmed/denied
        if chat_id in self.game_timeout_task:
            self.game_timeout_task[chat_id].cancel() # Cancel any active timeouts

    async def cancel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id

        if chat_id not in games:
            await update.message.reply_text("لا توجد لعبة نشطة لإلغائها في هذه المجموعة.")
            return

        game = games[chat_id]

        # Allow creator or admin to cancel
        if user_id == game['creator_id'] or await self.is_admin(chat_id, user_id, context):
            await context.bot.send_message(chat_id, "تم إلغاء اللعبة! 👋")
            self.clear_game_state(chat_id)
        else:
            await update.message.reply_text("فقط من بدأ اللعبة أو مشرف المجموعة يمكنه إلغاء اللعبة.")

    async def rules_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text(
            "📜 **قواعد لعبة تخمين الشخصيات:**\n\n"
            "**النمط 1 ضد 1:**\n"
            "• يبدأ اللعبة أدمن المجموعة باستخدام /start.\n"
            "• يختار الأدمن فئة الشخصيات ونمط 1 ضد 1.\n"
            "• ينضم لاعبان للعبة.\n"
            "• كل لاعب يحصل على شخصية سرية عشوائية من الفئة المختارة (في رسالة خاصة من البوت).\n"
            "• يتناوب اللاعبون على طرح أسئلة 'نعم/لا' لتخمين شخصية الخصم.\n"
            "• اللاعب الذي يطرح السؤال يقوم بذلك في المجموعة، واللاعب الآخر يجيب في الخاص بالبوت.\n"
            "• يمكن لأي لاعب في أي وقت تخمين شخصية الخصم بكتابة اسمها مباشرة في المجموعة.\n"
            "• عندما يقوم لاعب بتخمين، يطلب البوت من اللاعب صاحب الشخصية التأكيد (صحيح/غير صحيح) في الخاص.\n"
            "• إذا كان التخمين صحيحًا، يفوز اللاعب الذي خمن ويكسب نقطة.\n"
            "• اللعبة تستمر لعدد معين من الجولات (3 جولات افتراضياً). اللاعب الذي يجمع نقاطًا أكثر يفوز.\n"
            "• إذا انتهت الجولات ولم يتمكن أحد من التخمين، تنتهي اللعبة بالتعادل.\n\n"
            "**نمط الفرق:**\n"
            "• نفس طريقة البدء والاختيار.\n"
            "• ينقسم اللاعبون إلى فريقين (أزرق وأحمر) بحجم فريق محدد (2 ضد 2 أو 3 ضد 3).\n"
            "• كل فريق يحصل على شخصية سرية واحدة يشاركها جميع أعضاء الفريق.\n"
            "• الفرق تتناوب على طرح الأسئلة.\n"
            "• اللاعب الذي يطرح السؤال يكون من الفريق الذي دوره.\n"
            "• الفريق الآخر يجيب على السؤال (أي عضو من الفريق يمكنه الإجابة) في الخاص.\n"
            "• يمكن لأي لاعب من أي فريق تخمين شخصية الفريق الخصم في أي وقت.\n"
            "• الفريق الذي يخمن الشخصية بشكل صحيح يكسب نقطة.\n"
            "• الفريق صاحب النقاط الأعلى يفوز.\n\n"
            "**الأوامر:**\n"
            "• /start - لبدء لعبة جديدة (فقط للمشرفين).\n"
            "• /cancel - لإلغاء اللعبة الحالية (فقط لمن بدأ اللعبة أو المشرفين).\n"
            "• /score - لعرض لوحة النتائج.\n"
            "• /forfeit - للاستسلام في الدور الحالي (1 ضد 1) أو إلغاء اللعبة (فرق).",
            parse_mode='Markdown'
        )

    async def score_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = update.effective_chat.id
        game = games.get(chat_id)

        if not game:
            await update.message.reply_text("لا توجد لعبة نشطة لعرض النتائج.")
            return

        score_message = "📊 **النتائج الحالية:**\n\n"
        if game['game_type'] == '1v1':
            sorted_scores = sorted(game['scores'].items(), key=lambda item: item[1], reverse=True)
            for player_id, score in sorted_scores:
                player_name = self.get_player_name(player_id, game['players'])
                score_message += f"**{player_name}**: {score} نقطة\n"
        elif game['game_type'] == 'teams':
            blue_score = game['scores'].get('blue', 0)
            red_score = game['scores'].get('red', 0)
            score_message += f"🔵 **الفريق الأزرق**: {blue_score} نقطة\n"
            score_message += f"🔴 **الفريق الأحمر**: {red_score} نقطة\n\n"
            score_message += "--- تفاصيل اللاعبين ---\n"
            blue_players = [p['name'] for p in game['teams']['blue']]
            red_players = [p['name'] for p in game['teams']['red']]
            score_message += f"الفريق الأزرق: {', '.join(blue_players) if blue_players else 'لا يوجد لاعبون'}\n"
            score_message += f"الفريق الأحمر: {', '.join(red_players) if red_players else 'لا يوجد لاعبون'}\n"


        await update.message.reply_text(score_message, parse_mode='Markdown')

    async def forfeit_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name

        game = games.get(chat_id)
        if not game or game.get('status') != 'playing':
            await update.message.reply_text("لا توجد لعبة نشطة للاستسلام فيها.")
            return

        if game['game_type'] == '1v1':
            # Only the current asker or answerer can forfeit their turn.
            if game['question_asker'] and user_id == game['question_asker']['id']:
                await update.message.reply_text(f"**{user_name}** استسلم في هذه الجولة! سيتم الانتقال للجولة التالية.", parse_mode='Markdown')
                game['round'] += 1
                await self.start_round(chat_id, context)
            elif game['answerer_id'] and user_id == game['answerer_id']:
                await update.message.reply_text(f"**{user_name}** استسلم في هذه الجولة! سيتم الانتقال للجولة التالية.", parse_mode='Markdown')
                game['round'] += 1
                await self.start_round(chat_id, context)
            else:
                await update.message.reply_text("لا يمكنك الاستسلام الآن. فقط اللاعب الذي عليه الدور (للسؤال أو الإجابة) يمكنه الاستسلام في الدور.")
        elif game['game_type'] == 'teams':
            # Any team member can forfeit the whole game.
            user_team = next((team_name for team_name, members in game['teams'].items() if any(p['id'] == user_id for p in members)), None)
            if user_team:
                await update.message.reply_text(f"**{user_name}** من الفريق {'الأزرق' if user_team == 'blue' else 'الأحمر'} استسلم! تم إنهاء اللعبة.", parse_mode='Markdown')
                self.clear_game_state(chat_id)
            else:
                await update.message.reply_text("أنت لست جزءًا من الفرق النشطة في هذه اللعبة.")


    async def end_game(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
        game = games[chat_id]
        final_score_message = "🏆 **اللعبة انتهت! النتائج النهائية:** 🏆\n\n"

        if game['game_type'] == '1v1':
            sorted_scores = sorted(game['scores'].items(), key=lambda item: item[1], reverse=True)
            for player_id, score in sorted_scores:
                player_name = self.get_player_name(player_id, game['players'])
                final_score_message += f"**{player_name}**: {score} نقطة\n"

            if sorted_scores[0][1] > sorted_scores[1][1]:
                winner_name = self.get_player_name(sorted_scores[0][0], game['players'])
                final_score_message += f"\n**الفائز هو: {winner_name}! تهانينا! 🎉**"
            elif sorted_scores[0][1] == sorted_scores[1][1]:
                final_score_message += "\n**تعادل! لا يوجد فائز واضح هذه المرة. 🤝**"

        elif game['game_type'] == 'teams':
            blue_score = game['scores'].get('blue', 0)
            red_score = game['scores'].get('red', 0)
            final_score_message += f"🔵 **الفريق الأزرق**: {blue_score} نقطة\n"
            final_score_message += f"🔴 **الفريق الأحمر**: {red_score} نقطة\n\n"

            if blue_score > red_score:
                final_score_message += "\n**الفائز هو: الفريق الأزرق! تهانينا! 🏆🔵**"
            elif red_score > blue_score:
                final_score_message += "\n**الفائز هو: الفريق الأحمر! تهانينا! 🏆🔴**"
            else:
                final_score_message += "\n**تعادل! لا يوجد فائز واضح هذه المرة. 🤝**"

        await context.bot.send_message(chat_id, final_score_message, parse_mode='Markdown')
        self.clear_game_state(chat_id)

    def clear_game_state(self, chat_id: int) -> None:
        if chat_id in games:
            del games[chat_id]
        if chat_id in self.game_timeout_task:
            self.game_timeout_task[chat_id].cancel()
            del self.game_timeout_task[chat_id]
        if chat_id in self.game_active_message:
            del self.game_active_message[chat_id]

    def get_player_name(self, player_id: int, players_list: List[Dict]) -> str:
        for player in players_list:
            if player['id'] == player_id:
                return player['name']
        return "لاعب غير معروف"

    def get_player_by_id(self, player_id: int, players_list: List[Dict]) -> Optional[Dict]:
        for player in players_list:
            if player['id'] == player_id:
                return player
        return None

    def setup_handlers(self, application: Application):
        """Setup all handlers"""
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("cancel", self.cancel_command))
        application.add_handler(CommandHandler("rules", self.rules_command))
        application.add_handler(CommandHandler("score", self.score_command))
        application.add_handler(CommandHandler("forfeit", self.forfeit_command))
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
    print("✅ Bot initialized.")
    bot.run_bot(bot_token)
