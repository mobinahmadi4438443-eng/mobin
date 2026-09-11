import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F, types
from aiogram.utils.keyboard import InlineKeyboardBuilder

BOT_TOKEN = os.getenv("BOT_TOKEN", "توکن_را_اینجا_بگذار")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def main_menu_keyboard():
    b = InlineKeyboardBuilder()
    
    # ردیف اول
    b.button(text="حساب کاربری (5987865893084861885)", callback_data="btn_profile")
    b.button(text="بازار (5258024802010026053)", callback_data="btn_market")
    
    # ردیف دوم
    b.button(text="داستانی (5364052602357044385)", callback_data="btn_story")
    b.button(text="مولتی(چند جهانی) (5361741454685256344)", callback_data="btn_multi")
    
    # ردیف سوم
    b.button(text="اسکین (5987973065403797894)", callback_data="btn_skin")
    b.button(text="ارتقا (5375338737028841420)", callback_data="btn_upgrade")
    
    # ردیف چهارم
    b.button(text="ماموریت ها (5282996373229167849)", callback_data="btn_missions")
    
    # ردیف پنجم
    b.button(text="(5453991094435997597) جنگ ها (5453991094435997597)", callback_data="btn_wars")
    b.button(text="بازار سیاه (5296387887984580731)", callback_data="btn_blackmarket")
    
    # ردیف ششم
    b.button(text="فروشگاه (5406683434124859552)", callback_data="btn_shop")
    b.button(text="لیدربرد (5415655814079723871)", callback_data="btn_leaderboard")
    
    # ردیف هفتم
    b.button(text="کلن (5978687277390371946)", callback_data="btn_clan")
    b.button(text="اخبار (5443038326535759644)", callback_data="btn_news")
    
    # ردیف هشتم
    b.button(text="راهنما (5282843764451195532)", callback_data="btn_help")
    b.button(text="بستن منو (5210952531676504517)", callback_data="btn_close")

    # چیدمان: 2, 2, 2, 1, 2, 2, 2, 2
    b.adjust(2, 2, 2, 1, 2, 2, 2, 2)
    return b.as_markup()

@dp.message(F.text.contains("امپراطوری ها"))
async def trigger_empire_menu(message: types.Message):
    if message.chat.type in ["group", "supergroup"]:
        text = (
            '<tg-emoji emoji-id="5282974228377789040">👑</tg-emoji> <b>منوی اصلی بازی امپراطوری ها</b>\n\n'
            '<tg-emoji emoji-id="5019617635629794161">👇</tg-emoji> بخش مورد نظر خود را انتخاب کنید:'
        )
        
        await message.reply(text, reply_markup=main_menu_keyboard(), parse_mode="HTML")

@dp.callback_query(F.data == "btn_close")
async def close_menu(callback: types.CallbackQuery):
    await callback.message.delete()
    await callback.answer("منو بسته شد.", show_alert=False)

@dp.callback_query(F.data.startswith("btn_"))
async def handle_other_buttons(callback: types.CallbackQuery):
    if callback.data != "btn_close":
        await callback.answer("⏳ در حال توسعه...", show_alert=True)

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
