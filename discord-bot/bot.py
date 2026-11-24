import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
import discord
from discord.ext import commands, tasks
import aiohttp

# Load configuration from config.json (relative to this script) with env vars fallback
CONFIG_PATH = Path(__file__).parent / 'config.json'
config = {}
if CONFIG_PATH.exists():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        config = json.load(f)

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN') or config.get('discord_token')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN') or config.get('github_token')
REPO = os.getenv('GITHUB_REPO') or config.get('repo')
CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID') or config.get('channel_id', 0))

if not DISCORD_TOKEN:
    print('⚠️ DISCORD_TOKEN не задано. Бот не запущено.')
    raise SystemExit(0)

HEADERS = {
    'Authorization': f'Bearer {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json',
    'Cache-Control': 'no-cache'
}

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Stored repository state
known_branches = None      # {branch_name: latest_commit_sha}
known_prs = None           # {pr_number: status ('open', 'closed', 'merged')}
seen_member_events = None  # Set of already processed MemberEvent IDs


def get_commit_info(commit_obj):
    """Safely extract the author and the first line of the commit message."""
    author = (commit_obj.get('author') or {}).get('login')
    if not author:
        author = commit_obj.get('commit', {}).get('author', {}).get('name', 'Невідомий')
    raw_msg = commit_obj.get('commit', {}).get('message', '')
    first_line = raw_msg.splitlines()[0] if raw_msg else 'без опису'
    return author, first_line


async def check_member_events(session, channel):
    """Check GitHub Events API for new MemberEvent entries."""
    global seen_member_events

    try:
        events_url = f'https://api.github.com/repos/{REPO}/events?per_page=30'
        async with session.get(events_url, headers=HEADERS) as resp:
            if resp.status != 200:
                print(f'Помилка отримання подій (MemberEvent): HTTP {resp.status}')
                return

            events_data = await resp.json()
            member_events = [e for e in events_data if e.get('type') == 'MemberEvent']

            # On first run, record existing event IDs without sending notifications
            if seen_member_events is None:
                seen_member_events = {e['id'] for e in member_events if 'id' in e}
                print(f'Ініціалізація: зафіксовано {len(seen_member_events)} подій MemberEvent.')
                return

            action_map = {
                'added': 'додав учасника',
                'removed': 'видалив учасника',
                'edited': 'змінив права учасника'
            }

            for event in reversed(member_events):
                event_id = event.get('id')
                if not event_id or event_id in seen_member_events:
                    continue

                actor = (event.get('actor') or {}).get('login', 'Невідомий')
                payload = event.get('payload', {})
                action = payload.get('action', 'оновив')
                member = (payload.get('member') or {}).get('login', 'Невідомий')

                action_text = action_map.get(action, f'виконав дію ({action}) щодо')
                await channel.send(f'👤 **{actor}** {action_text} **`{member}`** у репозиторії!')

                seen_member_events.add(event_id)
    except Exception as e:
        print(f'Помилка при перевірці MemberEvent: {e}')


@bot.event
async def on_ready():
    print(f'Бот {bot.user} успішно запущений!')
    if not check_github.is_running():
        check_github.start()


@bot.command()
async def status(ctx):
    url = f'https://api.github.com/repos/{REPO}'
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=HEADERS) as response:
            if response.status == 200:
                data = await response.json()
                repo_name = data.get('full_name', REPO)
                default_branch = data.get('default_branch', 'невідомо')
                pushed_at_raw = data.get('pushed_at')

                if pushed_at_raw:
                    dt_utc = datetime.fromisoformat(pushed_at_raw.replace('Z', '+00:00'))
                    dt_utc2 = dt_utc.astimezone(timezone(timedelta(hours=2)))
                    pushed_at = dt_utc2.strftime('%d.%m.%Y %H:%M:%S')
                else:
                    pushed_at = 'Невідомо'

                await ctx.send(
                    f'✅ **Зв\'язок із GitHub успішний!**\n'
                    f'📁 Репозиторій: `{repo_name}`\n'
                    f'🌿 Основна гілка: `{default_branch}`\n'
                    f'🕒 Останній пуш (UTC+2): `{pushed_at}`'
                )
            else:
                await ctx.send(f'❌ Помилка доступу до `{REPO}`. Код відповіді: `{response.status}`')


@tasks.loop(seconds=30)
async def check_github():
    global known_branches, known_prs

    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print(f'Помилка: канал {CHANNEL_ID} не знайдено!')
        return

    async with aiohttp.ClientSession() as session:
        # --- 1. CHECK BRANCHES AND PUSHES ---
        try:
            branches_url = f'https://api.github.com/repos/{REPO}/branches?per_page=100'
            async with session.get(branches_url, headers=HEADERS) as resp:
                if resp.status == 200:
                    branches_data = await resp.json()
                    current_branches = {b['name']: b['commit']['sha'] for b in branches_data}

                    if known_branches is None:
                        known_branches = current_branches
                        print(f'Ініціалізація: відстежую {len(known_branches)} гілок.')
                    else:
                        # New branches
                        for name in current_branches:
                            if name not in known_branches:
                                await channel.send(f'🌿 Створено нову гілку: `{name}`')

                        # Deleted branches
                        for name in known_branches:
                            if name not in current_branches:
                                await channel.send(f'🗑️ Видалено гілку: `{name}`')

                        # New pushes to existing branches
                        for name, new_sha in current_branches.items():
                            old_sha = known_branches.get(name)
                            if old_sha and old_sha != new_sha:
                                compare_url = f'https://api.github.com/repos/{REPO}/compare/{old_sha}...{new_sha}'
                                async with session.get(compare_url, headers=HEADERS) as comp_resp:
                                    if comp_resp.status == 200:
                                        comp_data = await comp_resp.json()
                                        commits = comp_data.get('commits', [])
                                        if commits:
                                            author, msg = get_commit_info(commits[-1])
                                            await channel.send(
                                                f'🔄 **{author}** запушив {len(commits)} коміт(ів) у гілку `{name}`\n'
                                                f'> `{msg}`'
                                            )
                                            continue

                                # Fallback option (e.g., if a force-push occurred)
                                commit_url = f'https://api.github.com/repos/{REPO}/commits/{new_sha}'
                                async with session.get(commit_url, headers=HEADERS) as c_resp:
                                    if c_resp.status == 200:
                                        author, msg = get_commit_info(await c_resp.json())
                                        await channel.send(
                                            f'🔄 **{author}** оновив гілку `{name}` (force-push / rebase)\n'
                                            f'> `{msg}`'
                                        )
                                    else:
                                        await channel.send(f'🔄 Новий пуш у гілку `{name}` (`{new_sha[:7]}`)')

                        known_branches = current_branches
                else:
                    print(f'Помилка отримання гілок: HTTP {resp.status}')
        except Exception as e:
            print(f'Помилка при перевірці гілок: {e}')

        # --- 2. CHECK PULL REQUESTS ---
        try:
            prs_url = f'https://api.github.com/repos/{REPO}/pulls?state=all&sort=updated&direction=desc&per_page=30'
            async with session.get(prs_url, headers=HEADERS) as resp:
                if resp.status == 200:
                    prs_data = await resp.json()

                    if known_prs is None:
                        known_prs = {
                            pr['number']: ('merged' if pr.get('merged_at') else pr.get('state'))
                            for pr in prs_data
                        }
                        print(f'Ініціалізація: зафіксовано {len(known_prs)} Pull Requests.')
                    else:
                        for pr in reversed(prs_data):
                            num = pr['number']
                            title = pr.get('title', 'Без назви')
                            author = (pr.get('user') or {}).get('login', 'Невідомий')
                            state = 'merged' if pr.get('merged_at') else pr.get('state')

                            if num not in known_prs:
                                await channel.send(f'🔀 **{author}** відкрив Pull Request #{num}: "{title}"')
                                known_prs[num] = state
                            elif known_prs[num] != state:
                                status_text = {
                                    'merged': 'змерджив',
                                    'closed': 'закрив',
                                    'open': 'перевідкрив'
                                }.get(state, f'змінив статус ({state})')
                                await channel.send(f'🔀 Pull Request #{num} "{title}" — **{status_text}**')
                                known_prs[num] = state
                else:
                    print(f'Помилка отримання PR: HTTP {resp.status}')
        except Exception as e:
            print(f'Помилка при перевірці PR: {e}')

        # --- 3. CHECK MEMBERS (MemberEvent) ---
        await check_member_events(session, channel)


bot.run(DISCORD_TOKEN)