import logging
import os
import json
from datetime import datetime
from zoneinfo import ZoneInfo  # Modul untuk timezone
from io import BytesIO  # Untuk menyimpan foto di memori

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
    ConversationHandler,
)

# ======================= Konfigurasi Awal =======================

# Ganti dengan token bot Telegram Anda
BOT_TOKEN = '7694075913:AAHauaSB8Gp9E025WOttNKOdmUmN_DYGmmQ'

# Ganti dengan username atau ID channel Telegram Anda (misalnya, @mytestimonialchannel)
CHANNEL_ID = '@online_jualbeli'

# File untuk menyimpan data testimoni
DATA_FILE = 'data.json'

# Daftar produk
PRODUCTS = ['DIGITALOCEAN', 'AWS', 'AZURE', 'ALIBABA', 'GCP', 'LINODE']

# Zona waktu WIB
WIB_ZONE = ZoneInfo('Asia/Jakarta')  # Timezone untuk WIB

# Daftar nama bulan dalam bahasa Indonesia
MONTHS = [
    "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember"
]

# Daftar nama hari dalam bahasa Indonesia
DAYS = [
    "Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"
]

# URL untuk tombol link
LIST_PRODUK_URL = 'https://shopee.co.id/toko_jk'  # Ganti dengan URL daftar produk Anda
CONTACT_PERSON_URL = 'https://wa.me/6285895995512'  # Ganti dengan link contact person Anda

# ======================= Pengaturan Logging =======================

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ======================= Helper Functions =======================

def load_data():
    """Muat data dari file JSON. Jika tidak ada, buat dengan nilai awal."""
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w') as f:
            json.dump({'testimonial_number': 1}, f)
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_data(data):
    """Simpan data ke file JSON."""
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

# ======================= Definisi States =======================

# Definisikan state untuk ConversationHandler
AWAITING_PHOTO, AWAITING_PRODUCT = range(2)

# ======================= Handler Functions =======================

async def receive_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler untuk menerima foto dari pengguna, kemudian meminta pemilihan produk.
    """
    photo = update.message.photo[-1]  # Mengambil versi resolusi tertinggi dari foto
    file = await photo.get_file()
    
    # Mengunduh foto ke dalam buffer memori
    photo_bytes = BytesIO()
    await file.download_to_memory(photo_bytes)
    photo_bytes.seek(0)  # Reset pointer untuk membaca dari awal

    # Simpan foto dalam memori ke user_data untuk digunakan nanti
    context.user_data['photo_bytes'] = photo_bytes

    # Mengirimkan daftar produk sebagai tombol
    keyboard = [
        [InlineKeyboardButton(product, callback_data=product)] for product in PRODUCTS
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Silakan pilih produk untuk testimoni Anda:",
        reply_markup=reply_markup
    )

    return AWAITING_PRODUCT

async def product_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler untuk menerima pilihan produk dan mengirimkan testimoni ke channel.
    """
    query = update.callback_query
    await query.answer()

    selected_product = query.data
    context.user_data['selected_product'] = selected_product

    # Memuat data untuk nomor testimoni
    data = load_data()
    testimonial_number = data.get('testimonial_number', 1)
    data['testimonial_number'] = testimonial_number + 1
    save_data(data)

    # Mengambil tanggal dan waktu saat ini dalam WIB
    current_datetime = datetime.now(WIB_ZONE)
    current_day = DAYS[current_datetime.weekday()]  # Mengambil nama hari
    current_date = f"{current_datetime.day} {MONTHS[current_datetime.month - 1]} {current_datetime.year}"
    current_time = current_datetime.strftime("%H:%M:%S")

    # Mengambil foto yang disimpan dalam memori
    photo_bytes = context.user_data.get('photo_bytes')

    if not photo_bytes:
        await query.edit_message_text(
            text="Terjadi kesalahan saat memproses foto Anda. Silakan coba lagi.",
            parse_mode='Markdown'
        )
        context.user_data.clear()
        return ConversationHandler.END

    # Membuat caption otomatis
    caption = f'''
Hari: {current_day}
Date: {current_date}
Time: {current_time}
Number Transaction: {testimonial_number}
Product: {selected_product}
    '''.strip()

    # Membuat tombol link
    buttons = [
        [
            InlineKeyboardButton("List Produk", url=LIST_PRODUK_URL),
            InlineKeyboardButton("Contact Person", url=CONTACT_PERSON_URL)
        ]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)

    # Mengirim ke channel
    try:
        photo_bytes.seek(0)  # Pastikan pointer berada di awal
        await context.bot.send_photo(
            chat_id=CHANNEL_ID,
            photo=photo_bytes,
            caption=caption,
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Error sending photo to channel: {e}")
        await query.edit_message_text(
            text="Terjadi kesalahan saat mengirim testimoni ke channel. Silakan coba lagi nanti."
        )
        context.user_data.clear()
        return ConversationHandler.END

    await query.edit_message_text(
        text="Testimoni Anda telah diperbarui di channel kami. Terima kasih!"
    )

    # Menghapus data sementara
    context.user_data.clear()

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler untuk perintah /cancel. Membatalkan proses testimoni.
    """
    await update.message.reply_text(
        'Proses testimoni dibatalkan.',
        reply_markup=InlineKeyboardMarkup([])
    )
    context.user_data.clear()
    return ConversationHandler.END

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler untuk perintah yang tidak dikenali.
    """
    await update.message.reply_text(
        "Maaf, saya tidak mengerti perintah itu. Silakan kirimkan foto testimoni Anda untuk memulai."
    )

# ======================= Main Function =======================

def main():
    """
    Fungsi utama untuk menjalankan bot.
    """
    # Inisialisasi Application
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Menambahkan ConversationHandler untuk update testimoni
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.PHOTO, receive_photo)],
        states={
            AWAITING_PRODUCT: [CallbackQueryHandler(product_selected, pattern='^(' + '|'.join(PRODUCTS) + ')$')],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True
    )
    application.add_handler(conv_handler)

    # Handler untuk perintah /cancel
    application.add_handler(CommandHandler('cancel', cancel))

    # Handler untuk perintah yang tidak dikenali
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))

    # Menjalankan bot hingga Ctrl+C ditekan
    logger.info("Bot mulai dijalankan...")
    application.run_polling()

# ======================= Eksekusi Utama =======================

if __name__ == '__main__':
    main()
