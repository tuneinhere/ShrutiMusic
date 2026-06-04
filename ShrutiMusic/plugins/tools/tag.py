from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from pyrogram.enums import ChatMembersFilter
import asyncio
import random
from time import time
import logging

from ShrutiMusic import app

# ================= GLOBAL =================
tasks = {}  # simpan task per chat
message_ids_to_delete = {}

# ================= ADMIN CHECK =================
async def is_admin(chat_id, user_id, client):
    admins = [
        admin.user.id
        async for admin in client.get_chat_members(chat_id, filter=ChatMembersFilter.ADMINISTRATORS)
    ]
    return user_id in admins

def get_arg(message):
    return message.text.split(None, 1)[1] if len(message.text.split()) > 1 else ""

# ================= TAGALL =================
@app.on_message(filters.command(["tagall"]) & filters.group)
async def tag_all(c: Client, m: Message):
    if not await is_admin(m.chat.id, m.from_user.id, c):
        return await m.reply("<blockquote><b>❌ Khusus admin doang.</b></blockquote>")

    # kalau masih ada task lama → stop dulu
    if m.chat.id in tasks:
        try:
            tasks[m.chat.id].cancel()
        except:
            pass

    msg = await m.reply("<blockquote><b>⏳ Processing tagall...</b></blockquote>")
    start_time = time()

    emoji_list = ["🔥","🚀","💀","😂","😈","⚡","👽","🤖","👻","🐼"]

    # ambil user
    users = [
        f"<a href=tg://user?id={u.user.id}>{random.choice(emoji_list)}</a>"
        async for u in c.get_chat_members(m.chat.id)
        if not (u.user.is_bot or u.user.is_deleted)
    ]

    async def run_tag():
        sent_ids = []
        total = 0

        try:
            for chunk in [users[i:i+5] for i in range(0, len(users), 5)]:

                text = f"{get_arg(m)}\n<blockquote><b>@NakaiStore</b></blockquote>\n\n{' '.join(chunk)}"

                sent = await m.reply(
                    text,
                    quote=bool(m.reply_to_message),
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🚫 Stop", callback_data=f"stop:{m.chat.id}")]
                    ])
                )

                sent_ids.append(sent.id)
                total += len(chunk)

                # 🔥 delay responsive (bisa langsung cancel)
                for _ in range(20):
                    await asyncio.sleep(0.1)

        except asyncio.CancelledError:
            await m.reply("<blockquote><b>🚫 Tagall dihentikan</b></blockquote>")
            return

        except Exception as e:
            logging.error(f"Tagall error: {e}")
            await m.reply("<blockquote><b>❌ Terjadi error saat tagall.</b></blockquote>")
            return

        finally:
            # hapus pesan loading
            try:
                await msg.delete()
            except:
                pass

            # simpan id pesan buat dihapus nanti
            if sent_ids:
                message_ids_to_delete[m.chat.id] = sent_ids

            end_time = round(time() - start_time, 2)

            await m.reply(
                f"<blockquote><b>✅ Selesai tagall {total} user\n⏱ Waktu: {end_time} detik</b></blockquote>",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🗑 Hapus Tagall", callback_data="delete_all")]
                ])
            )

            # hapus task dari dict
            tasks.pop(m.chat.id, None)

    task = asyncio.create_task(run_tag())
    tasks[m.chat.id] = task


# ================= CANCEL COMMAND =================
@app.on_message(filters.command("cancel") & filters.group)
async def cancel_tag(c: Client, m: Message):
    if not await is_admin(m.chat.id, m.from_user.id, c):
        return await m.reply("<blockquote><b>❌ Bukan admin.</b></blockquote>")

    task = tasks.get(m.chat.id)

    if not task:
        return await m.reply("<blockquote><b>⚠️ Tagall tidak sedang berjalan.</b></blockquote>")

    task.cancel()
    tasks.pop(m.chat.id, None)

    await m.reply("<blockquote><b>🚫Tagall dihentikan</b></blockquote>")


# ================= BUTTON STOP =================
@app.on_callback_query(filters.regex(r"stop:(\d+)"))
async def stop_btn(c: Client, cq: CallbackQuery):
    chat_id = int(cq.data.split(":")[1])

    if not await is_admin(chat_id, cq.from_user.id, c):
        return await cq.answer("❌ Bukan admin!", show_alert=True)

    task = tasks.get(chat_id)

    if not task:
        return await cq.answer("⚠️ Sudah berhenti.", show_alert=True)

    task.cancel()
    tasks.pop(chat_id, None)

    await cq.answer("🚫 Tagall dihentikan", show_alert=True)

    try:
        await cq.message.edit("<blockquote><b>🚫 Tagall dihentikan</b></blockquote>")
    except:
        pass


# ================= DELETE ALL =================
@app.on_callback_query(filters.regex("delete_all"))
async def delete_all(c: Client, cq: CallbackQuery):
    chat_id = cq.message.chat.id

    if not await is_admin(chat_id, cq.from_user.id, c):
        return await cq.answer("❌ Bukan admin!", show_alert=True)

    ids = message_ids_to_delete.get(chat_id)

    if not ids:
        return await cq.answer("⚠️ Tidak ada pesan.", show_alert=True)

    try:
        for i in range(0, len(ids), 50):
            await c.delete_messages(chat_id, ids[i:i+50])

        message_ids_to_delete.pop(chat_id, None)

        await cq.answer("✅ Semua tag berhasil dihapus", show_alert=True)

    except Exception as e:
        logging.error(f"Delete error: {e}")
        await cq.answer("❌ Gagal menghapus pesan", show_alert=True)