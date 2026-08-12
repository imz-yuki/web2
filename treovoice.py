#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
╔══════════════════════════════════════════════════════════════════════════════╗
║     ⚡ APEX VOICE CONTROLLER V10.0 OMNIVERSE TITAN ULTIMATE ⚡               ║
║     - Fix triệt để lỗi Gateway 4013 Invalid Intent(s)                        ║
║     - Tự động tối ưu hóa Intents chuẩn cho cả Bot và Selfbot                 ║
║     - Anti-Crash 24/7, Tự động reconnect & Quản lý nick phụ tối ưu         ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import json
import asyncio
import requests
import discord
from discord.ext import commands
from colorama import init, Fore, Style

init(autoreset=True)
os.system('title APEX VOICE CONTROLLER V10.0 ULTIMATE' if os.name == 'nt' else '')

CONFIG_FILE = "config.json"

# ─── GIAO DIỆN CONSOLE ────────────────────────────────────────────
class Logger:
    @staticmethod
    def banner():
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"{Fore.CYAN}{Style.BRIGHT}")
        print("████████╗██████╗ ████████╗██████╗ ███╗   ██╗  ██████╗ ██████╗ ██████╗ ")
        print("╚══██╔══╝██╔══██╗╚══██╔══╝██╔══██╗████╗  ██║  ██╔══██╗██╔══██╗██╔══██╗")
        print("   ██║   ██████╔╝   ██║   ██████╔╝██╔██╗ ██║  ██████╔╝██████╔╝██║  ██║")
        print("   ██║   ██╔══██╗   ██║   ██╔══██╗██║╚██╗██║  ██╔═══╝ ██╔══██╗██║  ██║")
        print("   ██║   ██║  ██║   ██║   ██║  ██║██║ ╚████║  ██║     ██║  ██║██████╔╝")
        print("   ╚═╝   ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═══╝  ╚═╝     ╚═╝  ╚═╝╚═════╝ ")
        print(f"{Fore.MAGENTA}═══ APEX VOICE CONTROLLER V10.0 - OMNIVERSE TITAN ULTIMATE ═══{Style.RESET_ALL}\n")

    @staticmethod
    def info(msg): print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} {msg}")
    @staticmethod
    def ok(msg): print(f"{Fore.GREEN}[✓ OK]{Style.RESET_ALL} {msg}")
    @staticmethod
    def err(msg): print(f"{Fore.RED}[✗ ERR]{Style.RESET_ALL} {msg}")

# ─── CẤU HÌNH & XÁC THỰC TOKEN ─────────────────────────────────────
def load_config():
    default_cfg = {
        "main_token": "",
        "webhook_url": "",
        "tokens": [],
        "voice_ids": []
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                default_cfg.update(data)
        except Exception:
            pass
    return default_cfg

def save_config(cfg):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=4, ensure_ascii=False)

config = load_config()

def clean_token(token: str) -> str:
    raw = str(token).strip().strip('"\'')
    if raw.startswith("Bot "):
        raw = raw[4:].strip()
    return raw

def verify_token(token: str):
    raw_token = clean_token(token)
    if not raw_token:
        return None, None

    # 1. Thử Bot Token
    try:
        res = requests.get(
            "https://discord.com/api/v10/users/@me",
            headers={"Authorization": f"Bot {raw_token}"},
            timeout=3
        )
        if res.status_code == 200:
            return res.json(), "BOT"
    except Exception:
        pass

    # 2. Thử User Token (Selfbot)
    try:
        res = requests.get(
            "https://discord.com/api/v10/users/@me",
            headers={"Authorization": raw_token},
            timeout=3
        )
        if res.status_code == 200:
            return res.json(), "USER"
    except Exception:
        pass

    return None, None

def send_webhook_log(title: str, desc: str, color: int = 0x3498db):
    url = config.get("webhook_url", "")
    if not url or not url.startswith("http"):
        return
    try:
        payload = {"embeds": [{"title": title, "description": desc, "color": color}]}
        requests.post(url, json=payload, timeout=2)
    except Exception:
        pass

# ─── BỘ TÌM KÊNH VOICE THÔNG MINH ────────────────────────────────
async def resolve_voice_channel(client, target_id: int):
    ch = client.get_channel(target_id)
    if ch and isinstance(ch, discord.VoiceChannel):
        return ch

    try:
        ch = await client.fetch_channel(target_id)
        if isinstance(ch, discord.VoiceChannel):
            return ch
    except Exception:
        pass

    try:
        guild = client.get_guild(target_id)
        if not guild:
            guild = await client.fetch_guild(target_id)
        if guild:
            channels = await guild.fetch_channels() if hasattr(guild, 'fetch_channels') else guild.channels
            for c in channels:
                if isinstance(c, discord.VoiceChannel):
                    return c
    except Exception:
        pass

    return None

# ─── QUẢN LÝ NICK PHỤ VOICE ENGINE ─────────────────────────────────
class VoiceEngine:
    def __init__(self):
        self.clients = {}

    async def connect_voice(self, token: str, voice_id: int):
        user_info, token_type = verify_token(token)
        if not user_info:
            Logger.err(f"Token phụ lỗi: {clean_token(token)[:15]}...")
            return False

        username = user_info.get("username", "Unknown")
        
        intents_obj = discord.Intents.default() if hasattr(discord, 'Intents') else None
        client = discord.Client(intents=intents_obj, self_bot=(token_type == "USER")) if intents_obj else discord.Client(self_bot=(token_type == "USER"))

        @client.event
        async def on_ready():
            await asyncio.sleep(1)
            channel = await resolve_voice_channel(client, int(voice_id))
            if channel:
                try:
                    await channel.connect(reconnect=True)
                    Logger.ok(f"Tài khoản [{username}] >> Kết nối Voice thành công: {channel.name} ({channel.guild.name})")
                    send_webhook_log("🔊 Connect Success", f"**Tài khoản:** `{username}`\n**Kênh:** `{channel.name}`\n**Server:** `{channel.guild.name}`", 0x2ecc71)
                except Exception as e:
                    Logger.err(f"[{username}] >> Lỗi vào Voice: {e}")
            else:
                Logger.err(f"[{username}] >> Không tìm thấy Kênh Voice từ ID: {voice_id}")

        clean_tok = clean_token(token)
        run_tok = f"Bot {clean_tok}" if token_type == "BOT" else clean_tok
        
        asyncio.create_task(client.start(run_tok))
        self.clients[username] = {"client": client, "voice_id": voice_id, "type": token_type}
        return True

    async def disconnect_all(self):
        for data in self.clients.values():
            try:
                await data["client"].close()
            except Exception:
                pass
        self.clients.clear()
        Logger.ok("Đã ngắt toàn bộ nick phụ khỏi Voice.")

    async def toggle_deaf(self, state: bool):
        count = 0
        for data in self.clients.values():
            client = data["client"]
            if client.voice_clients:
                try:
                    await client.voice_clients[0].guild.change_voice_state(
                        channel=client.voice_clients[0].channel,
                        self_deaf=state,
                        self_mute=state
                    )
                    count += 1
                except Exception:
                    pass
        return count

    async def set_activity(self, text: str):
        count = 0
        for data in self.clients.values():
            client = data["client"]
            try:
                await client.change_presence(activity=discord.Game(name=text))
                count += 1
            except Exception:
                pass
        return count

manager = VoiceEngine()

# ─── MAIN BOT CREATOR (FIX INTENTS 4013) ───────────────────────────
def create_main_bot(main_type):
    is_selfbot = (main_type == "USER")
    
    if hasattr(discord, 'Intents'):
        intents = discord.Intents.default()
        if hasattr(intents, 'message_content'):
            intents.message_content = True
    else:
        intents = None

    if intents:
        return commands.Bot(command_prefix="!", intents=intents, self_bot=is_selfbot, help_command=None)
    return commands.Bot(command_prefix="!", self_bot=is_selfbot, help_command=None)

# ─── KHỞI CHẠY HỆ THỐNG ───────────────────────────────────────────
if __name__ == "__main__":
    Logger.banner()
    
    main_info, main_type = verify_token(config.get("main_token", ""))
    
    while not main_info:
        Logger.err("Main Token trong config.json không hợp lệ!")
        input_token = input("👉 Nhập Main Token điều khiển mới: ").strip()
        config["main_token"] = input_token
        save_config(config)
        main_info, main_type = verify_token(input_token)

    bot = create_main_bot(main_type)

    @bot.event
    async def on_ready():
        Logger.banner()
        Logger.ok(f"Main Bot ({main_type}) Online thành công: {bot.user.name}")
        Logger.info("Gửi lệnh `!` trên Discord để điều khiển hệ thống.")
        
        tokens = config.get("tokens", [])
        voices = config.get("voice_ids", [])
        
        if tokens and voices:
            Logger.info("Đang tự động kết nối danh sách nick phụ vào Voice...")
            for t in tokens:
                for v in voices:
                    await manager.connect_voice(t, v)
                    await asyncio.sleep(1.5)

    @bot.command(name="join", aliases=["joinall"])
    async def cmd_join(ctx):
        tokens = config.get("tokens", [])
        voices = config.get("voice_ids", [])
        if not tokens or not voices:
            await ctx.send("❌ Thiếu Token nick phụ hoặc Voice/Server ID!")
            return
        await ctx.send("⏳ Đang tiến hành kết nối nick phụ vào Voice...")
        for t in tokens:
            for v in voices:
                await manager.connect_voice(t, v)
                await asyncio.sleep(1.5)
        await ctx.send("✅ Đã hoàn tất lệnh kết nối!")

    @bot.command(name="leave", aliases=["leaveall"])
    async def cmd_leave(ctx):
        await manager.disconnect_all()
        await ctx.send("✅ Đã ngắt toàn bộ nick phụ khỏi Voice.")

    @bot.command(name="add")
    async def cmd_add(ctx, token: str):
        info, _ = verify_token(token)
        if info:
            clean_t = clean_token(token)
            if clean_t not in config["tokens"]:
                config["tokens"].append(clean_t)
                save_config(config)
                await ctx.send(f"✅ Đã thêm Token: **{info.get('username')}**")
                Logger.ok(f"Thêm thành công Token: {info.get('username')}")
            else:
                await ctx.send("ℹ️ Token này đã tồn tại.")
        else:
            await ctx.send("❌ Token không hợp lệ.")

    @bot.command(name="vid")
    async def cmd_vid(ctx, v_id: int):
        if v_id not in config["voice_ids"]:
            config["voice_ids"].append(v_id)
            save_config(config)
            await ctx.send(f"✅ Đã thêm Voice/Server ID: `{v_id}`")
            Logger.ok(f"Thêm thành công ID: {v_id}")
        else:
            await ctx.send("ℹ️ ID này đã tồn tại.")

    @bot.command(name="status", aliases=["st"])
    async def cmd_status(ctx):
        if not manager.clients:
            await ctx.send("💤 Chưa có nick phụ nào đang treo Voice.")
            return
        
        msg = "📊 **TRẠNG THÁI HỆ THỐNG NICK PHỤ**\n```yaml\n"
        for name, data in manager.clients.items():
            client = data["client"]
            latency = round(client.latency * 1000) if client.latency else 0
            status = "Online" if client.is_ready() else "Connecting"
            vc_name = client.voice_clients[0].channel.name if client.voice_clients else "Chưa vào Voice"
            msg += f"• [{name}] | Ping: {latency}ms | Status: {status} | Kênh: {vc_name}\n"
        msg += "```"
        await ctx.send(msg)

    @bot.command(name="deaf", aliases=["mute"])
    async def cmd_deaf(ctx, mode: str = "on"):
        state = True if mode.lower() in ["on", "true", "1"] else False
        count = await manager.toggle_deaf(state)
        act = "Tắt Tiếng (Self-Deaf)" if state else "Bật Tiếng"
        await ctx.send(f"🎧 **{act}** thành công cho `{count}` nick phụ!")

    @bot.command(name="play", aliases=["activity"])
    async def cmd_play(ctx, *, game_text: str):
        count = await manager.set_activity(game_text)
        await ctx.send(f"🎮 Đã cập nhật trạng thái chơi game: **{game_text}** cho `{count}` nick phụ!")

    @bot.command(name="reconnect", aliases=["rc"])
    async def cmd_reconnect(ctx):
        await ctx.send("🔄 Đang tái kết nối toàn bộ nick phụ...")
        await manager.disconnect_all()
        await asyncio.sleep(2)
        for t in config.get("tokens", []):
            for v in config.get("voice_ids", []):
                await manager.connect_voice(t, v)
                await asyncio.sleep(1.5)
        await ctx.send("⚡ Đã kết nối lại thành công!")

    @bot.command(name="del", aliases=["remove"])
    async def cmd_del(ctx, item: str):
        removed = False
        if item.isdigit():
            v_id = int(item)
            if v_id in config["voice_ids"]:
                config["voice_ids"].remove(v_id)
                removed = True
                await ctx.send(f"🗑️ Đã xóa Voice/Server ID: `{v_id}`")
        
        if not removed:
            clean_t = clean_token(item)
            if clean_t in config["tokens"]:
                config["tokens"].remove(clean_t)
                removed = True
                await ctx.send("🗑️ Đã xóa Token khỏi danh sách.")

        if removed:
            save_config(config)
        else:
            await ctx.send("❌ Không tìm thấy thông tin cần xóa.")

    try:
        clean_main = clean_token(config["main_token"])
        final_token = f"Bot {clean_main}" if main_type == "BOT" else clean_main
        Logger.info(f"Khởi chạy Main Bot loại ({main_type})...")
        bot.run(final_token)
    except Exception as e:
        Logger.err(f"Lỗi khởi chạy Main Bot: {e}")