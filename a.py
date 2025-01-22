import discord
from discord.ext import commands

# 봇의 프리픽스 및 클라이언트 설정
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.guilds = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# 변경된 이모지 포지션
positions = {
    "GK": "🧤",  # 골키퍼
    "LB": "◀️",  # 왼쪽 풀백
    "CB1": "🔶",  # 왼쪽 센터백
    "CB2": "🔷",  # 오른쪽 센터백
    "RB": "▶️",  # 오른쪽 풀백
    "CDM": "🟠",  # 수미 (중앙 수비형 미드필더)
    "LCM": "🟩",  # 왼쪽 중앙 미드필더
    "RCM": "🟦",  # 오른쪽 중앙 미드필더
    "LW": "🔺",  # 왼쪽 윙어
    "RW": "🔻",  # 오른쪽 윙어
    "ST": "🔴",  # 스트라이커
}

# 4-3-3 포메이션의 각 포지션
lineup = {
    "GK": [],
    "LB": [],
    "CB1": [],
    "CB2": [],
    "RB": [],
    "CDM": [],
    "LCM": [],
    "RCM": [],
    "LW": [],
    "RW": [],
    "ST": [],
}

# 유저가 배정된 포지션을 저장
user_assigned_positions = {}

# 라인업 설정 상태 및 메시지
lineup_ongoing = False
lineup_message = None  # 라인업 메시지 객체 저장용
lineup_thread = None  # 라인업 스레드 저장용

# 메시지 카운트 트래킹 변수
message_count = 0
MAX_MESSAGES_BEFORE_REFRESH = 10  # 채팅 메시지 10개마다 라인업 재출력

# 라인업 설정 함수
@bot.command()
async def 라인업(ctx):
    global lineup_ongoing, lineup_message, lineup, user_assigned_positions, lineup_thread

    if lineup_ongoing:
        await ctx.send("이미 라인업 설정이 진행 중입니다. 먼저 종료하려면 `!라인업끝`을 사용하세요.")
        return

    # 라인업 초기화
    lineup = {key: [] for key in lineup.keys()}
    user_assigned_positions = {}  # 유저 포지션 초기화
    lineup_ongoing = True

    lineup_message = await ctx.send(
        "라인업을 설정하세요! 이모지를 클릭하여 포지션을 선택하세요.\n\n"
        "골키퍼: 🧤, 왼쪽 풀백: ◀️, 왼쪽 센터백: 🔶, 오른쪽 센터백: 🔷, "
        "오른쪽 풀백: ▶️, 수미: 🟠, 왼쪽 중앙 미드필더: 🟩, 오른쪽 중앙 미드필더: 🟦, "
        "왼쪽 윙어: 🔺, 오른쪽 윙어: 🔻, 스트라이커: 🔴"
    )

    # 스레드 생성
    lineup_thread = await lineup_message.create_thread(name="라인업 현황", auto_archive_duration=60)

    # 이모지를 포지션에 맞게 추가
    for pos, emoji in positions.items():
        await lineup_message.add_reaction(emoji)

    await ctx.send("라인업을 설정하기 위해 이모지를 클릭하세요!")

# 유저가 이모지를 클릭할 때 라인업에 반영
@bot.event
async def on_reaction_add(reaction, user):
    global user_assigned_positions

    if user.bot:
        return  # 봇의 반응은 무시

    if not lineup_ongoing:
        await reaction.message.channel.send("라인업 설정이 종료되었습니다.")
        return

    # 사용자가 서버에서 사용 중인 닉네임 가져오기
    nickname = user.nick if user.nick else user.name

    # 사용자가 이미 배정된 포지션 확인
    if user.id in user_assigned_positions:
        await reaction.message.channel.send(f"{nickname}님, 이미 {user_assigned_positions[user.id]} 포지션에 배정되었습니다.")
        return

    # 각 포지션에 유저 추가
    for pos, emoji in positions.items():
        if str(reaction.emoji) == emoji:
            lineup[pos].append(nickname)
            user_assigned_positions[user.id] = pos  # 유저 포지션 저장
            await update_lineup_message(reaction.message)
            return

# 라인업을 출력하는 함수
async def update_lineup_message(message):
    # 포지션별 라인업 출력
    lineup_message_content = "**현재 라인업**\n\n"
    for pos, emoji in positions.items():
        players = ", ".join(lineup[pos]) if lineup[pos] else "비어있음"
        lineup_message_content += f"{emoji} {pos}: {players}\n"

    await message.edit(content=lineup_message_content)
    
    # 스레드에도 업데이트
    if lineup_thread:
        await lineup_thread.send(lineup_message_content)

# 라인업 종료 명령어
@bot.command()
async def 라인업끝(ctx):
    global lineup_ongoing, lineup_thread

    if not lineup_ongoing:
        await ctx.send("라인업은 이미 종료되었습니다.")
        return

    lineup_ongoing = False
    await ctx.send("라인업 설정이 종료되었습니다. 더 이상 포지션을 설정할 수 없습니다.")

    # 스레드 종료
    if lineup_thread:
        await lineup_thread.edit(archived=True)
        lineup_thread = None

# 용병 추가 명령어
@bot.command()
async def 용병추가(ctx, nickname: str, position: str):
    global lineup

    if position not in lineup:
        await ctx.send("올바르지 않은 포지션입니다. 다시 확인해주세요.")
        return

    lineup[position].append(f"{nickname}(용병)")
    await ctx.send(f"{nickname}(용병)이 {position} 포지션에 추가되었습니다.")

    if lineup_message:
        await update_lineup_message(lineup_message)

# 용병 삭제 명령어
@bot.command()
async def 용병삭제(ctx, nickname: str, position: str):
    global lineup

    if position not in lineup:
        await ctx.send("올바르지 않은 포지션입니다. 다시 확인해주세요.")
        return

    player_to_remove = f"{nickname}(용병)"
    if player_to_remove in lineup[position]:
        lineup[position].remove(player_to_remove)
        await ctx.send(f"{nickname}(용병)이 {position} 포지션에서 제거되었습니다.")
    else:
        await ctx.send(f"{nickname}(용병)은 {position} 포지션에 없습니다.")

    if lineup_message:
        await update_lineup_message(lineup_message)

# 팀원 추가 명령어
@bot.command()
async def 팀원추가(ctx, nickname: str, position: str):
    global lineup

    if position not in lineup:
        await ctx.send("올바르지 않은 포지션입니다. 다시 확인해주세요.")
        return

    lineup[position].append(nickname)
    await ctx.send(f"{nickname}님이 {position} 포지션에 추가되었습니다.")

    if lineup_message:
        await update_lineup_message(lineup_message)

# 팀원 삭제 명령어
@bot.command()
async def 팀원삭제(ctx, nickname: str, position: str):
    global lineup

    if position not in lineup:
        await ctx.send("올바르지 않은 포지션입니다. 다시 확인해주세요.")
        return

    if nickname in lineup[position]:
        lineup[position].remove(nickname)
        await ctx.send(f"{nickname}님이 {position} 포지션에서 제거되었습니다.")
    else:
        await ctx.send(f"{nickname}님은 {position} 포지션에 없습니다.")

    if lineup_message:
        await update_lineup_message(lineup_message)
        
# 메시지 모니터링 및 자동 라인업 표시
@bot.event
async def on_message(message):
    global message_count, lineup_message

    if message.author.bot:
        return  # 봇 메시지는 무시

    message_count += 1

    # 메시지 개수에 따라 라인업 현황 다시 출력
    if lineup_message and message_count >= MAX_MESSAGES_BEFORE_REFRESH:
        await update_lineup_message(lineup_message)
        message_count = 0  # 카운트 초기화

    await bot.process_commands(message)  # 다른 명령어 처리

# 봇의 동작을 위한 토큰
bot.run('MTMzMDUyMTU5NTEyMjU0ODc0OQ.GVmy57.txWVEBFlCraLJRvxbvf-q5OI7jkQ_FGdxsOQwk')
