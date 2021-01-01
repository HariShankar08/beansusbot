from discord.ext.commands import Bot
from discord.ext import commands
import discord
import asyncio
import pickle
import random

with open("auth.pkl", "rb") as file:
    token = pickle.load(file)

with open('skeld_locations.pkl', 'rb') as pkl_file:
    skeld_locations = pickle.load(pkl_file)

with open('skeld_map.pkl', 'rb') as pkl_file:
    skeld_map = pickle.load(pkl_file)

with open('skeld_vents.pkl', 'rb') as pkl_file:
    skeld_vents = pickle.load(pkl_file)

bot = Bot(command_prefix='!')
bot.remove_command('help')
games = {}
in_a_game = {}
guild_premium = [776347343133081630]


class NoPremiumError(Exception):
    pass


class InvalidMovement(Exception):
    pass


class Game:
    def __init__(self, n_players=2):
        self.n_players = n_players
        self.game_in_progress = False
        self.meeting_in_progress = False
        self.has_killed = {}
        self.impostors = []
        self.players = []
        self.players_alive = []
        self.player_locations = []
        self.death_place = [None] * len(skeld_map)
        self.player_colours = {}
        self.voting_names = []
        self.ejected = ''
        self.ej_list = []
        self.vote_count = 0
        self.votes = {}
        self.can_emergency = False
        self.discuss = False
        self.can_vote = False
        self.voted = []
        self.temptask = dict.fromkeys(
            ['filter', 'enter_id', 'ali_eng', 'wires', 'emp', 'power', 'scan_card', 'sample', 'shields', 'steer',
             'fuel', 'reac_start'], [])
        self.tasking = {}
        self.taskdisp = {}
        self.total = 0
        self.emer_dict = {}
        self.help_commands = {
            '!game': 'Starts a game with two players',
            '!game (n_players)': 'Starts a game with the entered number of players. Also takes additional parameter to set the unique code for the game',
            '!join (code)': 'Join the game using the unique code',
            '!which': 'Which game (unique code) you are in right now (if in a game)',
            '!reset (code)': 'Reset game using the unique code if in a game',
            '!m (tile number)': 'Move to the tile as per the map',
            '!em': 'Call an emergency meeting',
            '!v': 'Vent (If you can)',
            '!v up': 'Get out of a vent(If you\'re in one)',
            '!v (tile number)': 'Move to the vent tile as per map',
            '!rep': 'Report a dead body',
            '!vo (nickname)': 'Vote for a person in meetings',
            '!vo skip': 'Skip voting',
            '!k': 'Kill (If you are an impostor)',
            '!my_tasks': 'Shows your tasks for the game',
            '!taskstat': 'Shows task completion status',
            '!tasks': 'Shows task details'
        }
        self.task_commands = {
            '!med_scan': 'Do the medical scan task.(in MedBay)',
            '!ali_eng': 'Align engine task.(in Engines)',
            '!wires': 'The electricals task.(in Electrical and Storage)',
            '!emp': 'Empty the garbage chute.(in Cafe and Storage)',
            '!upload': 'Upload data.(in Navigation and Admin)',
            '!download': 'Download data.(in Comm and Shields)',
            '!power': 'Divert power.(in Comm and Security)',
            '!enterid': 'Enter the Id code.(in Weapons and Admin)',
            '!reactor-start': 'Start the reactor.(in Reactor)',
            '!fuel': 'Collect fuel and empty it into the engine.(in Engines)',
            '!steer': 'Stabilize the steering of the ship.(in Navigation)',
            '!shields': 'The shields priming task.(in Shields)',
            '!sample': 'Inspect samples.(in Medbay)',
            '!scan-card': 'Scan boarding pass(in Weapons and Security)',
            '!filter': 'Clean the O2 filters(in O2)'
        }


@bot.command()
async def help(ctx):
    gm = Game()
    embed = await make_embed('Help', 'List of available Commands', gm.help_commands)
    del gm
    await ctx.send(embed=embed)


@bot.command()
async def tasks(ctx):
    gm = Game()
    embed = await make_embed('Tasks', 'List of available Tasks and  their Commands', gm.task_commands)
    del gm
    await ctx.send(embed=embed)


@bot.command()
async def game(ctx, *args):
    global games
    try:
        if not args:
            this_game = Game()
            n_players = 2
            code = str(round(random.random() * 1000))
            await ctx.guild.create_role(name=f"IN GAME {code}", colour=discord.Color.red())
            await ctx.channel.set_permissions(discord.utils.get(ctx.guild.roles, name=f'IN GAME {code}'),
                                              send_messages=False, read_messages=False)
        else:
            try:
                n_players = int(args[0])
            except ValueError:
                await ctx.send('Placeholder angry message.')
                return
            this_game = Game(n_players=n_players)
            try:
                code = args[1]
                await ctx.guild.create_role(name=f"IN GAME {code}", colour=discord.Color.red())
                await ctx.channel.set_permissions(discord.utils.get(ctx.guild.roles, name=f'IN GAME {code}'),
                                                  send_messages=False, read_messages=False)
            except IndexError:
                code = str(round(random.random() * 1000))
                await ctx.guild.create_role(name=f"IN GAME {code}", colour=discord.Color.red())
                await ctx.channel.set_permissions(discord.utils.get(ctx.guild.roles, name=f'IN GAME {code}'),
                                                  send_messages=False, read_messages=False)
        g_id = ctx.message.guild.id
        if g_id in games.keys():
            if len(games[g_id]) >= 2:
                if g_id not in guild_premium:
                    raise NoPremiumError(f'Guild with Guild ID {g_id} does not have premium.')
        try:
            games[ctx.message.guild.id][code] = this_game
        except KeyError:  # No games running at the time on that server
            games[ctx.message.guild.id] = {code: this_game}

        await ctx.send(f'Alright. Queueing game of {n_players} with unique code {code}')
    except NoPremiumError as npe:
        await ctx.send(f'Whoa, got this error...\n```\nNoPremiumError: {str(npe)}```')
        await ctx.send('Only Premium guilds can have more than 2 games running at a time.')


@bot.command()
async def join(ctx, *args):
    global games
    global in_a_game
    g_id = ctx.message.guild.id
    available_games = games[g_id]
    if ctx.message.author not in in_a_game:
        try:
            if args[0] in available_games:
                game_ = available_games[args[0]]
                if not game_.game_in_progress:
                    game_.players.append(ctx.message.author)
                    await ctx.send(f'Ok, joined the game, {ctx.message.author}.\nSet a nickname with !nick.')
                    available_games[args[0]] = game_
                    games[g_id] = available_games
                    in_a_game[ctx.message.author] = [g_id, args[0]]
                else:
                    await ctx.send('Sorry, that game is in progress.')
            else:
                await ctx.send('Invalid Code. Are you sure this is the one?')
        except IndexError:
            await ctx.send('Ok, sure, you want to join a game... but I need the game code for that!')
    else:
        await ctx.send(f'I can\'t allow you more than one game, {ctx.message.author}')


@bot.command()
async def which(ctx):
    if ctx.message.author in in_a_game:
        await ctx.send(f'You have joined the game with unique code: {in_a_game[ctx.message.author][1]}')
    else:
        await ctx.send(f'You aren\'t in a game yet, {ctx.message.author}.')


@bot.command()
async def my_tasks(ctx):
    if ctx.message.author in in_a_game:
        g_id, u_id = tuple(in_a_game[ctx.message.author])
        gm = games[g_id][u_id]
        white_square, tick_mark = '\U00002B1C', '✅'
        try:
            for k, v in gm.tasking[ctx.message.author].items():
                if v:
                    gm.taskdisp[ctx.message.author][k] = white_square
                else:
                    gm.taskdisp[ctx.message.author][k] = tick_mark
            await ctx.message.author.send(str(gm.taskdisp[ctx.message.author]))
        except KeyError:
            await ctx.send("You're an impostor! Can't do tasks")
    else:
        await ctx.send('You\'re not even in a game, {}'.format(ctx.message.author))


@bot.command()
async def taskstat(ctx):
    if ctx.message.author in in_a_game:
        g_id, u_id = tuple(in_a_game[ctx.message.author])
        gm = games[g_id][u_id]
        tasks_done = 0
        for player in gm.players:
            if player in gm.tasking:
                for v in gm.tasking[player].values():
                    if not v:
                        tasks_done += 1
        if not gm.total == 0:
            percent = int((tasks_done / gm.total) * 100)
        else:
            await ctx.message.author.send("No tasks assigned")
        await ctx.message.author.send(str(percent) + '% completed')
    else:
        await ctx.send('You\'re not even in a game, {}'.format(ctx.message.author))


@bot.command()
async def nick(ctx, *args):
    global games
    guild = ctx.guild
    try:
        if ctx.message.author in in_a_game:
            g_id = ctx.message.guild.id
            nick_ = args[0]
            if nick_.startswith('http'):
                raise ValueError("You can't use links!")
            elif nick_.strip().lower() == 'skip':
                raise ValueError("Disallowed Nickname")
            elif len(nick_) > 32:
                raise ValueError("That's too long!")
            gm = games[g_id][in_a_game[ctx.message.author][1]]
            if not gm.game_in_progress and nick_ not in gm.player_colours.values():
                gm.player_colours[ctx.message.author] = nick_
                await ctx.send('Ok, nickname set.')
                await putback_game(gm, ctx.message.author)
                u_id = in_a_game[ctx.message.author][1]
                await ctx.message.author.add_roles(discord.utils.get(guild.roles, name=f"IN GAME {u_id}"))
                if len(gm.players) == len(gm.player_colours) == gm.n_players:
                    await ctx.send('Alright, starting game.')
                    await start_game(gm)
            elif gm.game_in_progress:
                await ctx.send('Hey! You can\'t change nicknames in between the game!')
            elif nick_ in gm.player_colours.values():
                raise ValueError('Nickname has already been taken.')
        else:
            await ctx.send('You aren\'t in a game yet, {}'.format(ctx.message.author))

    except IndexError:
        await ctx.send('You want to set a nickname, huh? I need the name for that!')

    except ValueError as ve:
        await ctx.send(f'I can\'t allow you to take that nickname.\n```\nReason: {str(ve)}```')


@bot.command()
async def reset(ctx, u_id):
    global games
    if ctx.message.author in in_a_game:
        if u_id == in_a_game[ctx.message.author][1]:
            g_id = in_a_game[ctx.message.author][0]
            guild = bot.get_guild(g_id)
            gm = games[g_id][u_id]
            role = discord.utils.get(guild.roles, name=f"IN GAME {u_id}")
            for player in gm.players:
                await player.send(f'Game has been reset by {ctx.message.author}')
                await map.unpin()
                await player.remove_roles(role)
                del in_a_game[player]

            await role.delete()
            del games[g_id][u_id]
            await ctx.send('Reset complete.')


@bot.command()
async def m(ctx, tile):
    try:
        tile = int(tile)
        if ctx.message.author in in_a_game:
            g_id, u_id = tuple(in_a_game[ctx.message.author])
            gm = games[g_id][u_id]
            await move_player(gm, ctx.message.author, tile)
        else:
            await ctx.send('You\'re not even in a game, {}'.format(ctx.message.author))
    except ValueError:
        await ctx.send('I\'m just going to pretend nothing was wrong there...')


@bot.command()
async def v(ctx, tile='default'):
    try:
        tile = int(tile)
        if ctx.message.author in in_a_game:
            g_id, u_id = tuple(in_a_game[ctx.message.author])
            gm = games[g_id][u_id]
            await venting(gm, ctx.message.author, tile)
        else:
            await ctx.send('You\'re not even in a game, {}'.format(ctx.message.author))
    except ValueError:
        if str(tile) == 'up':
            # Now tile stores 'up'
            tile = str(tile)
            if ctx.message.author in in_a_game:
                g_id, u_id = tuple(in_a_game[ctx.message.author])
                gm = games[g_id][u_id]
                await venting(gm, ctx.message.author, tile)
            else:
                await ctx.send('You\'re not even in a game, {}'.format(ctx.message.author))
        elif str(tile) == 'default':
            # Now tile stores 'default'
            tile = str(tile)
            if ctx.message.author in in_a_game:
                g_id, u_id = tuple(in_a_game[ctx.message.author])
                gm = games[g_id][u_id]
                await venting(gm, ctx.message.author, tile)
            else:
                await ctx.send('You\'re not even in a game, {}'.format(ctx.message.author))
        else:
            await ctx.send('I\'m just going to pretend nothing was wrong there...')


@bot.command()
async def k(ctx):
    try:
        if ctx.message.author in in_a_game:
            g_id, u_id = tuple(in_a_game[ctx.message.author])
            gm = games[g_id][u_id]
            await killing(gm, ctx.message.author)
        else:
            await ctx.send('You\'re not even in a game, {}'.format(ctx.message.author))
    except ValueError:
        await ctx.send('I\'m just going to pretend nothing was wrong there...')


@bot.command()
async def rep(ctx):
    try:
        if ctx.message.author in in_a_game:
            g_id, u_id = tuple(in_a_game[ctx.message.author])
            gm = games[g_id][u_id]
            await reporting(gm, ctx.message.author)
        else:
            await ctx.send('You\'re not even in a game, {}'.format(ctx.message.author))
    except ValueError:
        await ctx.send('I\'m just going to pretend nothing was wrong there...')


@bot.command()
async def vo(ctx, word):
    try:
        word = str(word)
        if ctx.message.author in in_a_game:
            g_id, u_id = tuple(in_a_game[ctx.message.author])
            gm = games[g_id][u_id]
            await voting(gm, ctx.message.author, word)
        else:
            await ctx.send('You\'re not even in a game, {}'.format(ctx.message.author))
    except ValueError:
        await ctx.send('I\'m just going to pretend nothing was wrong there...')


@bot.command()
async def em(ctx):
    try:
        if ctx.message.author in in_a_game:
            g_id, u_id = tuple(in_a_game[ctx.message.author])
            gm = games[g_id][u_id]
            await emeeting(gm, ctx.message.author)
        else:
            await ctx.send('You\'re not even in a game, {}'.format(ctx.message.author))
    except ValueError:
        await ctx.send('I\'m just going to pretend nothing was wrong there...')


'''
@bot.event
async def on_command_error(ctx, error):
    await ctx.send('I\'m just gonna pretend nothing was wrong there...')
'''


# --- Non bot commands ---

async def start_game(gm):
    global map
    for player in gm.players:
        await player.send("Game is now in progress.")
        map = await player.send(file=discord.File('map.png'))
        await map.pin()
    gm.game_in_progress = True
    n_impostors = 1
    gm.players_alive = [1] * len(gm.players)  # 1 for alive, 0 for dead
    gm.player_locations = [14] * len(gm.players_alive)
    gm.impostors = random.sample(gm.players, n_impostors)
    gm.has_killed = dict.fromkeys(gm.impostors, True)
    d = {player: gm.player_colours[player] for player in gm.players}
    gm.emer_dict = dict.fromkeys(gm.players, True)
    gm.votes['skip'] = 0
    task_list = ['filter', 'enter_id', 'med_scan', 'ali_eng', 'wires', 'emp', 'upload', 'download', 'power',
                 'scan_card', 'sample', 'shields', 'steer', 'fuel', 'reac_start']
    gm.tasking = {player: dict.fromkeys(random.sample(task_list, 6), True) for player in gm.players if
                  player not in gm.impostors}
    for player in gm.tasking:
        gm.taskdisp[player] = {k: v for k, v in gm.tasking[player].items()}  # copy of nested dictionary
    for player in gm.players:
        if player not in gm.impostors:
            if 'download' in gm.tasking[player]:
                gm.tasking[player]['upload'] = True
            elif 'upload' in gm.tasking[player]:
                gm.tasking[player]['download'] = True
            gm.total += sum(gm.tasking[player].values())
            await task_loc(gm, player)
    for i in range(len(gm.players)):
        if gm.players[i] in gm.impostors:
            await gm.players[i].send('You are the `impostor`. Don\'t get caught!')
            embed = await make_embed('In Game', 'Players and their Nicknames:', dict_=d, is_impostor=True, gm=gm)
            await gm.players[i].send(embed=embed)
        else:
            await gm.players[i].send(f'You are a `crew-mate`. There is 1 impostor among you.')
            embed = await make_embed('In Game', 'Players and their Nicknames:', dict_=gm.player_colours)
            await gm.players[i].send(embed=embed)

        await gm.players[i].send(f"You are currently in {skeld_locations[gm.player_locations[i]]} \
(Tile {gm.player_locations[i]})")
    await putback_game(gm, random.choice(gm.players))
    await asyncio.sleep(20)
    gm.has_killed = dict.fromkeys(gm.impostors, False)
    gm.can_emergency = True
    gm.can_vote = True
    pl = random.choice(gm.players)
    await putback_game(gm, pl)


async def putback_game(gm, pl):
    global games
    global in_a_game

    g_id, u_id = tuple(in_a_game[pl])
    games[g_id][u_id] = gm


async def move_player(gm, pl, tile):
    try:
        current_location = gm.player_locations[gm.players.index(pl)]
        if not gm.meeting_in_progress:
            allowed_tiles = skeld_map[current_location]
            for i in range(len(gm.player_locations)):
                if gm.player_locations[i] == current_location and gm.players_alive[i] != 0:
                    if gm.players[i] != pl:
                        if tile in allowed_tiles:
                            await gm.players[i].send(f'{pl}: {gm.player_colours[pl]} is leaving \
    {skeld_locations[current_location]}: Tile {current_location}, moving to {skeld_locations[tile]}: Tile {tile}')

            if tile in allowed_tiles:
                gm.player_locations[gm.players.index(pl)] = tile
                await pl.send(f'You are currently in {skeld_locations[tile]}: Tile {tile}')

                await task_loc(gm, pl)

                if gm.death_place[tile] is not None and gm.players_alive[gm.players.index(pl)] != 0:
                    await pl.send('There is a dead body here! Report using "!rep"')

                if pl in gm.impostors and tile in skeld_vents:
                    await pl.send('You can vent here. Use "!v" to enter the vent.')

                same_place = []
                for i in range(len(gm.player_locations)):
                    if gm.player_locations[i] == tile and gm.players_alive[i] != 0:
                        same_place.append(gm.players[i])
                same_place = [player for player in same_place if player != pl]
                if same_place:  # Runs if non-empty
                    d = {player: gm.player_colours[player] for player in same_place}
                    embed = await make_embed('Players here', 'You also see:', d, is_impostor=pl in gm.impostors, gm=gm)
                    for player in same_place:
                        await player.send(f'{pl} has entered \
    {skeld_locations[tile]}: Tile {tile}')
                    await pl.send(embed=embed)
                else:
                    await pl.send('You\'re the only one here.')
            else:
                await pl.send('That\'s not allowed Use "!map" to view a map and corresponding tile numbers.')
        else:
            await pl.send('You are in a meeting!!')
    except IndexError:
        await pl.send('Sorry, that\'s not allowed.')
    await putback_game(gm, pl)


async def venting(gm, pl, tile):
    current_location = gm.player_locations[gm.players.index(pl)]
    if not gm.meeting_in_progress:
        if pl in gm.impostors:
            #  Check if in a vent-able location
            current_tile = gm.player_locations[gm.players.index(pl)]
            # Getting into vents
            if str(tile) == 'default':
                if current_tile < 50:
                    if current_tile in skeld_vents.keys():
                        # Make "invisible"
                        gm.player_locations[gm.players.index(pl)] = current_tile + 50
                        # Get the allowed movements
                        allowed_tiles = skeld_vents[current_tile]
                        d = {skeld_locations[tilee]: tilee for tilee in allowed_tiles}
                        embed = await make_embed('You can move to', 'Move using !v (Tile Number)', d)
                        await pl.send(embed=embed)
                        same_place = []
                        for i in range(len(gm.player_locations)):
                            if gm.player_locations[i] == current_tile and gm.players_alive[i] != 0:
                                same_place.append(gm.players[i])
                        same_place = [player for player in same_place if player != pl]
                        if same_place:  # Runs if non-empty
                            embed = discord.Embed(title='Players here', description='You also see:')

                            for player in same_place:
                                embed.add_field(name=str(player), value=gm.player_colours[player].title())
                                # Send message to players as well
                                await player.send(f'{pl}: {gm.player_colours[pl]} has gotten into a vent \
    {skeld_locations[current_tile]}: Tile {current_tile}!')
                            await pl.send(embed=embed)
                    else:
                        await pl.send("You can't vent here!")
                else:
                    await pl.send("You are already in a vent")
            elif str(tile) == 'up':
                if current_tile > 40:
                    current_tile -= 50
                    gm.player_locations[gm.players.index(pl)] = current_tile
                    same_place = []
                    await pl.send(f"You are currently in {skeld_locations[current_tile]} \
    (Tile {current_tile})")
                    await task_loc(gm, pl)
                    for i in range(len(gm.player_locations)):
                        if gm.player_locations[i] == current_tile and gm.players_alive[i] != 0:
                            same_place.append(gm.players[i])
                    same_place = [player for player in same_place if player != pl]
                    if same_place:  # Runs if non-empty
                        embed = discord.Embed(title='Players here', description='You also see:')

                        for player in same_place:
                            embed.add_field(name=str(player), value=gm.player_colours[player].title())
                            # Send message to player as well
                            await player.send(f'{pl} has vented into\
    {skeld_locations[current_tile]}: Tile {current_tile}!')
                        await pl.send(embed=embed)
                    else:
                        await pl.send("You're the only one here.")

                    gm.player_locations[gm.players.index(pl)] = current_tile
                else:
                    await pl.send('You\'re not even in a vent. Seriously. Think I wouldn\'t notice?')
            else:
                # Moving in vents
                if current_tile > 40:
                    current_tile -= 50
                    if tile in skeld_vents[current_tile]:
                        gm.player_locations[gm.players.index(pl)] = tile + 50
                        await pl.send(f"You are currently in the vent at {skeld_locations[tile]}: Tile Number {tile}.\
            \nYou are not seen.")
                        same_place = []
                        for i in range(len(gm.player_locations)):
                            if gm.player_locations[i] == tile and gm.players_alive[i] != 0:
                                same_place.append(gm.players[i])
                        same_place = [player for player in same_place if player != pl]
                        if same_place:  # Runs if non-empty
                            d = {player: gm.player_colours[player].title() for player in same_place}
                            embed = await make_embed('People here', 'You also see:', d)
                            await pl.send(embed=embed)
                        else:
                            await pl.send("You're the only one here.")
                        # Get the allowed movements
                        allowed_tiles = skeld_vents[tile]
                        d = {skeld_locations[tilee]: tilee for tilee in allowed_tiles}
                        embed = await make_embed('You can move to', 'Move using !v (Tile Number)', d)
                        await pl.send(embed=embed)
                    else:
                        await pl.send("Enter a correct vent number man(temp msg)")
                else:
                    await pl.send('You\'re not even in a vent. Seriously. Think I wouldn\'t notice?')
        else:
            await pl.send("You're not even an impostor.")
    else:
        await pl.send("You are in a meeting!!")
    await putback_game(gm, pl)


async def killing(gm, pl):
    if pl in gm.players and not gm.meeting_in_progress:
        if pl in gm.impostors:
            if not gm.has_killed[pl]:
                current_tile = gm.player_locations[gm.players.index(pl)]
                if current_tile < 40:
                    same_place = []
                    for i in range(len(gm.player_locations)):
                        if gm.player_locations[i] == current_tile and gm.players_alive[i] != 0:
                            same_place.append(gm.players[i])
                    same_place = [player for player in same_place if player != pl]
                    if same_place:  # Runs if non-empty
                        gm.players_alive[gm.players.index(same_place[0])] = 0
                        u_id = in_a_game[pl][1]
                        g_id = in_a_game[pl][0]
                        guild = bot.get_guild(g_id)
                        role = discord.utils.get(guild.roles, name=f"IN GAME {u_id}")
                        await same_place[0].remove_roles(role)
                        await pl.send(f"You just killed {same_place[0]}!")
                        await same_place[0].send(f'You have been killed by {pl}')
                        for player in same_place[1:]:
                            await player.send(f"Player {same_place[0]} has been killed by {pl}")
                        if gm.death_place[current_tile] is None:
                            gm.death_place[current_tile] = [same_place[0]]
                        else:
                            gm.death_place[current_tile].append(same_place[0])
                        gm.has_killed[pl] = True
                        await check_game_win(gm, pl)
                        await putback_game(gm, pl)
                        await asyncio.sleep(30)
                        gm.has_killed[pl] = False
                        await putback_game(gm, pl)
                    else:
                        await pl.send("You're the only one here.")
                else:
                    await pl.send("You can't kill from a vent! Get out!")

            else:
                await pl.send('Sorry, can\'t kill anyone just yet.')
        else:
            await pl.send("Do you think you're an impostor?\nYou're not. Run along now.")


async def reporting(gm, pl):
    current_tile = gm.player_locations[gm.players.index(pl)]
    if gm.death_place[current_tile] is not None and gm.players_alive[gm.players.index(pl)] == 1:
        gm.player_locations = [14] * len(gm.players_alive)
        for player in gm.players:
            await player.send(f"A dead body was found!\nReported by {pl}: \
{gm.player_colours[pl]} \nDiscuss!!\nYou've got one minute.")
        gm.death_place[current_tile] = [None]
        gm.meeting_in_progress = True
        gm.discuss = True
        await create_channel(pl)
        d = {str(player): gm.player_colours[player] for player in gm.players if
             gm.players_alive[gm.players.index(player)] == 1}
        embed = await make_embed('List of players', 'Players and their nicknames', d)
        gm.discuss = False
        for player in gm.players:
            await player.send(embed=embed)
            await player.send('Times up! Voting starts now!')
            await player.send('Use !vo (nickname) to vote, or !vo skip to abstain')
            await end_voting(gm, pl)


async def voting(gm, pl, word):
    if gm.meeting_in_progress and gm.players_alive[gm.players.index(pl)] == 1 and not gm.discuss:
        if not gm.voted:
            gm.votes = {player: 0 for player in gm.players}
            gm.voted = []
            gm.votes['skip'] = 0
        if pl in gm.voted:
            await pl.send('You can\'t vote again, bruh.')
        else:
            for player in gm.players:
                if word == gm.player_colours[player]:
                    if gm.players_alive[gm.players.index(player)] == 1:
                        gm.votes[player] += 1
                        await pl.send('Ok.')
                        gm.voted.append(pl)
                    else:
                        await pl.send('This player is dead.')
                elif word == 'skip':
                    gm.votes['skip'] += 1
                    await pl.send('Ok.')
                    gm.voted.append(pl)


async def emeeting(gm, pl):
    if gm.players_alive[gm.players.index(pl)] and gm.player_locations[gm.players.index(pl)] == 14:
        if gm.can_emergency and gm.emer_dict[pl] and not gm.meeting_in_progress:
            gm.emer_dict[pl] = False
            gm.player_locations = [14] * len(gm.players_alive)
            gm.meeting_in_progress = True
            await putback_game(gm, pl)
            for player in gm.players:
                await player.send(f"Emergency meeting called by {pl}\nDiscuss!\nYou got one minute.")
            gm.discuss = True
            await create_channel(pl)
            d = {str(player): gm.player_colours[player] for player in gm.players if
                 gm.players_alive[gm.players.index(player)] == 1}
            embed = await make_embed('List of players', 'Players and their nicknames', d)
            gm.discuss = False
            for player in gm.players:
                await player.send('Times up! Voting starts now!')
                await player.send('Use !vo (nickname) to vote, or !vo skip to abstain')
                await player.send(embed=embed)
            await end_voting(gm, pl)
        else:
            await pl.send("You can't call one right now")


async def make_embed(title, desc, dict_, is_impostor=False, footer=None, gm=None):
    embed = discord.Embed(title=title,
                          description=desc)
    embed.set_thumbnail(url=bot.user.avatar_url)
    if not is_impostor:
        for key, val in dict_.items():
            embed.add_field(name=str(key), value=val)
    else:
        for key, val in dict_.items():
            if key in gm.impostors:
                embed.add_field(name=str(key) + ' (Impostor)', value=val)
            else:
                embed.add_field(name=str(key), value=val)
    if footer is not None:
        embed.set_footer(text=footer, icon_url=bot.user.avatar_url)
    else:
        embed.set_footer(text='BEAN SUS: TEXT BASED AMONG US ON DISCORD', icon_url=bot.user.avatar_url)

    return embed


async def create_channel(pl):
    g_id = in_a_game[pl][0]
    guild = bot.get_guild(g_id)
    u_id = in_a_game[pl][1]
    in_game_role = discord.utils.get(guild.roles, name=f"IN GAME {u_id}")
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        in_game_role: discord.PermissionOverwrite(read_messages=True)
    }
    channel = await guild.create_text_channel('Discussion Channel', overwrites=overwrites)
    await channel.send('Welcome')
    await asyncio.sleep(70)
    await channel.delete()


async def end_voting(gm, pl):
    await asyncio.sleep(40)
    gm.can_vote = False
    await putback_game(gm, pl)
    for player in gm.players:
        if gm.players_alive[gm.players.index(player)] == 1 and player not in gm.voted:
            gm.votes['skip'] += 1
            gm.voted.append(player)
    max_votes = max(gm.votes.values())
    m_ = {v: k for k, v in gm.votes.items()}
    max_vote_player = m_[max_votes]
    ej_list = [player for player in gm.votes.keys() if gm.votes[player] == max_votes]  # to find multiple maximums
    for player in gm.players:
        if len(ej_list) > 1:
            await player.send('No one was ejected (Tie)')
        elif max_vote_player == 'skip':
            await player.send("No one was ejected (Skipped)")
            max_vote_player = None
        else:
            await player.send(f"Player {max_vote_player} was ejected!")
            if max_vote_player in gm.impostors:
                await player.send(f'{max_vote_player} was the/an Impostor.')
                await player.send(f'{len(gm.impostors) - 1} Impostor(s) Remain.')
            else:
                await player.send(f'{max_vote_player} was not the/an Impostor.')
                await player.send(f'{len(gm.impostors)} Impostor(s) Remain.')
    if max_vote_player is not None:  # to check which player was ejected
        gm.players_alive[gm.players.index(max_vote_player)] = 0
        g_id = in_a_game[pl][0]
        guild = bot.get_guild(g_id)
        u_id = in_a_game[pl][1]
        role = discord.utils.get(guild.roles, name=f"IN GAME {u_id}")
        await gm.players[gm.players.index(max_vote_player)].remove_roles(role)
        if max_vote_player in gm.impostors:
            gm.impostors.remove(max_vote_player)
    gm.meeting_in_progress = False
    gm.can_vote = True
    await putback_game(gm, pl)
    await check_game_win(gm, pl)


async def check_game_win(gm, pl):
    global games
    g_id = in_a_game[pl][0]
    u_id = in_a_game[pl][1]
    guild = bot.get_guild(g_id)
    role = discord.utils.get(guild.roles, name=f"IN GAME {u_id}")
    tasks_over = False
    for player in gm.players:
        if player in gm.tasking:
            for k in gm.tasking[player].keys():
                if gm.tasking[player][k]:
                    break
            else:
                continue
            break
    else:
        tasks_over = True
    if gm.impostors and sum(gm.players_alive) <= 2:
        await imp_victory(gm, role, g_id, u_id)
    elif tasks_over or not gm.impostors:
        await imp_defeat(gm, role, g_id, u_id)


async def imp_defeat(gm, role, g_id, u_id):
    for player in gm.players:
        if player not in gm.tasking:
            await player.send('DEFEAT')
        else:
            await player.send('VICTORY')
        await map.unpin()
        if gm.players_alive[gm.players.index(player)] == 1:
            await player.remove_roles(role)
        del in_a_game[player]
    await role.delete()
    del games[g_id][u_id]


async def imp_victory(gm, role, g_id, u_id):
    for player in gm.players:
        if player not in gm.tasking:
            await player.send('VICTORY')
        else:
            await player.send('DEFEAT')
        await map.unpin()
        if gm.players_alive[gm.players.index(player)] == 1:
            await player.remove_roles(role)
        del in_a_game[player]
    await role.delete()
    del games[g_id][u_id]


# ---tasks---

@bot.command()
async def med_scan(ctx):
    pl = ctx.message.author
    if pl in in_a_game:
        try:
            g_id, u_id = tuple(in_a_game[pl])
            gm = games[g_id][u_id]
            if gm.player_locations[gm.players.index(pl)] == 17 and gm.tasking[pl]['med_scan']:
                gm.temptask['med_scan'].append(pl)
                await pl.send(f'Starting medical scan...')
                medical_status_message = await pl.send('Status: 0 percent complete.')
                medical_status = 0
                while medical_status < 100:
                    medical_status += random.randint(1, 6)
                    if medical_status <= 100:
                        await medical_status_message.edit(content=f'Status: {medical_status} percent complete.')
                    else:
                        await medical_status_message.edit(content=f'Status: 100 percent complete.')
                    await asyncio.sleep(0.01)
                else:
                    await medical_status_message.edit(content=f'Medical scan is complete.')
                    gm.tasking[pl]['med_scan'] = False
                    await check_game_win(gm, pl)
        except KeyError:
            await pl.send("Sorry, that's not allowed")
    else:
        await ctx.send('You\'re not even in a game, {}'.format(pl))


@bot.command()
async def ali_eng(ctx, *args):
    pl = ctx.message.author
    g_id, u_id = tuple(in_a_game[pl])
    gm = games[g_id][u_id]
    loc_list = [0, 1, 5, 6]
    if pl in in_a_game:
        try:
            if not args:
                if gm.player_locations[gm.players.index(pl)] in loc_list and gm.tasking[pl]['ali_eng'] and not \
                gm.temptask['ali_eng']:
                    global antiAlign, alignEng_output, alignEngMessage
                    gm.temptask['ali_eng'].append(pl)
                    antiAlign = random.randint(0, 1)
                    if antiAlign == 0:
                        slash_up = '\u2196'
                        slash_down = ''
                    else:
                        slash_up = ''
                        slash_down = '\u2199'
                    alignEng_output = f'''
                                         {slash_up}
                         ------------
                                         {slash_down}
                     '''
                    alignEngMessage = await pl.send(f'Here is the current engine output:\n{alignEng_output}\
                     \nType up or down(preceded by !ali_eng) to move the engine output.')
                else:
                    await pl.send("Sorry, that's not allowed")
            else:
                if pl in gm.temptask['ali_eng'] and gm.player_locations[gm.players.index(pl)] in loc_list:
                    ans = str(args[0])
                    if (ans == 'down' and antiAlign == 0) or (ans == 'up' and antiAlign == 1):
                        await pl.send(f'Task is successfully completed!')
                        alignEng_output = f'''

                            ----------<:arrow_left:770205021647274004>

                        '''
                        await alignEngMessage.edit(content=f'Here is the current engine output:\n{alignEng_output}')
                        gm.temptask['ali_eng'].remove(pl)
                        gm.tasking[pl]['ali_eng'] = False
                        await check_game_win(gm, pl)
                    else:
                        await pl.send('That isnt the right answer! Try again.')
        except KeyError:
            await pl.send("Sorry; that's not allowed")
    else:
        await ctx.send('You\'re not even in a game, {}'.format(pl))


@bot.command()
async def emp(ctx, *args):
    pl = ctx.message.author
    g_id, u_id = tuple(in_a_game[pl])
    gm = games[g_id][u_id]
    loc_list = [14, 15, 10, 11]
    if pl in in_a_game:
        try:
            if not args:
                if gm.player_locations[gm.players.index(pl)] in loc_list and gm.tasking[pl]['emp'] and not gm.temptask[
                    'emp']:
                    gm.temptask['emp'].append(pl)
                    await pl.send("Type 'down' (preceded by !emp) to pull the lever down and eject the garbage.")
                else:
                    await pl.send("Sorry; that's not allowed")
            else:
                if pl in gm.temptask['emp'] and gm.player_locations[gm.players.index(pl)] in loc_list:
                    ans = str(args[0])
                    if ans == 'down':
                        await pl.send(f'Starting ejection...')
                        emptyChute_status_message = await pl.send('Status: 0 percent complete.')
                        emptyChute_status = 0
                        while emptyChute_status < 100:
                            emptyChute_status += random.randint(1, 6)
                            if emptyChute_status <= 100:
                                await emptyChute_status_message.edit(
                                    content=f'Status: {emptyChute_status} percent ejected.')
                            else:
                                await emptyChute_status_message.edit(content=f'Status: 100 percent complete.')
                            await asyncio.sleep(0.01)
                        else:
                            await emptyChute_status_message.edit(content=f'Chute is empty.')
                            gm.temptask['emp'].remove(pl)
                            gm.tasking[pl]['emp'] = False
                            await check_game_win(gm, pl)
                    else:
                        await pl.send('That isnt the right answer! Try again.')
        except KeyError:
            await pl.send("Sorry; that's not allowed")
    else:
        await ctx.send('You\'re not even in a game, {}'.format(pl))


@bot.command()
async def wires(ctx, *args):
    pl = ctx.message.author
    g_id, u_id = tuple(in_a_game[pl])
    gm = games[g_id][u_id]
    loc_list = [8, 9, 10, 11]
    if pl in in_a_game:
        try:
            if not args:
                if gm.player_locations[gm.players.index(pl)] in loc_list and gm.tasking[pl]['wires'] and not \
                gm.temptask['wires']:
                    gm.temptask['wires'].append(pl)
                    global wireMatchColors
                    wireMatchColors = []
                    colors = ['<:yellow_square:771729639223066654>',
                              '<:red_square:771731748564369418>',
                              '<:green_square:771731921846796318>',
                              '<:blue_square:771732144279388210>']
                    colors_copy = colors.copy()
                    random.shuffle(colors_copy)
                    letters = ['a', 'b', 'c', 'd']

                    wireMatchColors = [None] * 4
                    for color in colors:
                        for color_copy in colors_copy:
                            if color == color_copy:
                                wireMatchColors[colors.index(color)
                                ] = f'{colors.index(color) + 1}-{letters[colors_copy.index(color_copy)]}'
                    await pl.send('Match the colors in order to connect the wires,\
                     type number-letter to answer one at a time. (preceded by !wires each time)')
                    for i in range(4):
                        await pl.send(f'{i + 1}                {letters[i]}\n{colors[i]}          {colors_copy[i]}')
            else:
                if pl in gm.temptask['wires'] and gm.player_locations[gm.players.index(pl)] in loc_list:
                    prevlen = len(wireMatchColors)
                    for i in wireMatchColors:
                        if str(args[0]) == i:
                            wireMatchColors.remove(i)
                            await pl.send(f'Correct match! {len(wireMatchColors)} matches left.')
                            break
                    if len(wireMatchColors) == prevlen:
                        await pl.send(f'Incorrect match! {len(wireMatchColors)} matches left.')
                    if len(wireMatchColors) == 0:
                        await pl.send('Task completed!')
                        gm.temptask['wires'].remove(pl)
                        gm.tasking[pl]['wires'] = False
                        await check_game_win(gm, pl)
        except KeyError:
            await pl.send("Sorry, that's not allowed")
    else:
        await ctx.send('You\'re not even in a game, {}'.format(pl))


@bot.command()
async def download(ctx):
    pl = ctx.message.author
    g_id, u_id = tuple(in_a_game[pl])
    gm = games[g_id][u_id]
    loc_list = [25, 27]
    if pl in in_a_game:
        try:
            if gm.player_locations[gm.players.index(pl)] in loc_list and gm.tasking[pl]['download']:
                await pl.send(f'Starting data download...')
                download_status_message = await pl.send('Status: 0 percent complete.')
                download_status = 0
                while download_status < 100:
                    download_status += random.randint(1, 6)
                    if download_status <= 100:
                        await download_status_message.edit(content=f'Status: {download_status} percent complete.')
                    else:
                        await download_status_message.edit(content=f'Status: 100 percent complete.')
                    await asyncio.sleep(0.01)
                else:
                    await download_status_message.edit(content=f'Download is complete.')
                    gm.tasking[pl]['download'] = False
                    await check_game_win(gm, pl)
        except KeyError:
            await pl.send("Sorry; that's not allowed")
    else:
        await ctx.send('You\'re not even in a game, {}'.format(pl))


@bot.command()
async def upload(ctx):
    pl = ctx.message.author
    g_id, u_id = tuple(in_a_game[pl])
    gm = games[g_id][u_id]
    loc_list = [13, 23, 24]
    if pl in in_a_game:
        try:
            if gm.player_locations[gm.players.index(pl)] in loc_list and gm.tasking[pl]['upload']:
                if not gm.tasking[pl]['download']:
                    await pl.send(f'Starting data upload...')
                    upload_status_message = await pl.send('Status: 0 percent complete.')
                    upload_status = 0
                    while upload_status < 100:
                        upload_status += random.randint(1, 6)
                        if upload_status <= 100:
                            await upload_status_message.edit(content=f'Status: {upload_status} percent complete.')
                        else:
                            await upload_status_message.edit(content=f'Status: 100 percent complete.')
                        await asyncio.sleep(0.01)
                    else:
                        await upload_status_message.edit(content=f'Upload is complete.')
                        gm.tasking[pl]['upload'] = False
                        await check_game_win(gm, pl)
                else:
                    await pl.send("You have to download first!")
        except KeyError:
            await pl.send("Sorry; that's not allowed")
    else:
        await ctx.send('You\'re not even in a game, {}'.format(pl))


@bot.command()
async def power(ctx, *args):
    pl = ctx.message.author
    g_id, u_id = tuple(in_a_game[pl])
    gm = games[g_id][u_id]
    loc_list = [27, 4]
    if pl in in_a_game:
        try:
            if not args:
                if gm.player_locations[gm.players.index(pl)] in loc_list and gm.tasking[pl]['power'] and not \
                gm.temptask['power']:
                    gm.temptask['power'].append(pl)
                    global power_switch, switches, messes
                    switches = ['cafetaria', 'admin',
                                'navigation', 'reactor', 'communications']
                    power_switch = random.choice(switches)
                    names = ''
                    for i in switches:
                        names += i + '     '
                    await pl.send('Type in the name of the section which needs more power. (preceded by !power)')
                    await pl.send(names)
                    messes = []
                    for i in range(4):
                        mess = ''
                        for j in switches:
                            if j == power_switch and i < 2:
                                mess += '<:small_red_triangle:774298438309117963>       '
                            else:
                                mess += '<:red_square:774296927059443735>       '
                        messes.append(await pl.send(mess))
                else:
                    await pl.send("Sorry; that's not allowed")
            else:
                if pl in gm.temptask['power'] and gm.player_locations[gm.players.index(pl)] in loc_list:
                    ans = str(args[0])
                    if ans == power_switch:
                        for i in range(4):
                            mess = ''
                            for _ in switches:
                                mess += '<:red_square:774296927059443735>       '
                            await messes[i].edit(content=mess)
                        await pl.send('Power successfully diverted.')
                        gm.temptask['power'].remove(pl)
                        gm.tasking[pl]['power'] = False
                        await check_game_win(gm, pl)
                    else:
                        await pl.send('That isnt the right answer! Try again.')
        except KeyError:
            await pl.send("Sorry; that's not allowed")
    else:
        await ctx.send('You\'re not even in a game, {}'.format(pl))


@bot.command()
async def enter_id(ctx, *args):
    pl = ctx.message.author
    g_id, u_id = tuple(in_a_game[pl])
    gm = games[g_id][u_id]
    loc_list = [19, 13]
    if pl in in_a_game:
        try:
            if not args:
                if gm.player_locations[gm.players.index(pl)] in loc_list and gm.tasking[pl]['enter_id'] and not \
                gm.temptask['enter_id']:
                    gm.temptask['enter_id'].append(pl)
                    global code
                    code = random.randint(20000, 80000)
                    await pl.send('Type the id before it changes: (preceded by !enter_id)')
                    code_message = await pl.send(f'{code}')
                    await asyncio.sleep(8)
                    while gm.tasking[pl]['enter_id']:
                        code = random.randint(20000, 80000)
                        await code_message.edit(content=f'{code}')
                        await asyncio.sleep(8)
                else:
                    await pl.send("Sorry, that's not allowed")
            else:
                if pl in gm.temptask['enter_id'] and gm.player_locations[gm.players.index(pl)] in loc_list:
                    ans = str(args[0])
                    if ans == str(code):
                        gm.tasking[pl]['enter_id'] = False
                        gm.temptask['enter_id'].remove(pl)
                        code = ''
                        await pl.send('Id accepted!')
                        await check_game_win(gm, pl)
                    else:
                        await pl.send('That isnt the right answer! Try again.')
        except KeyError:
            await pl.send("Sorry; that's not allowed")
    else:
        await ctx.send('You\'re not even in a game, {}'.format(pl))


@bot.command()
async def reac_start(ctx, *args):
    pl = ctx.message.author
    g_id, u_id = tuple(in_a_game[pl])
    gm = games[g_id][u_id]
    loc_list = [3]
    if pl in in_a_game:
        try:
            if not args:
                if gm.player_locations[gm.players.index(pl)] in loc_list and gm.tasking[pl]['reac_start'] and not \
                gm.temptask['reac_start']:
                    gm.temptask['reac_start'].append(pl)
                    global reactor_nums, current_num_mess, current_num
                    reactor_nums = [random.randint(1, 6) for _ in range(5)]
                    current_num = 0
                    await pl.send(
                        'Memorize the digits shown below and type them out as a number (preceded by !reac_start)\
                        \n(there are 5 digits, wait and memorize):')
                    current_num_mess = await pl.send(
                        f' {reactor_nums[current_num]} <:blue_square:771732144279388210>  <:blue_square:771732144279388210>  <:blue_square:771732144279388210>  <:blue_square:771732144279388210>  ')
                    await asyncio.sleep(2.5)
                    while pl in gm.temptask['reac_start']:
                        mess = ''
                        current_num = current_num + 1 if current_num < 4 else 0
                        for i in range(5):
                            if i == current_num:
                                mess += f' {reactor_nums[current_num]} '
                            else:
                                mess += ' <:blue_square:771732144279388210> '
                        await current_num_mess.edit(content=f'{mess}')
                        await asyncio.sleep(2)
                else:
                    await pl.send("Sorry, that's not allowed")
            else:
                if pl in gm.temptask['reac_start'] and gm.player_locations[gm.players.index(pl)] in loc_list:
                    ans = str(args[0])
                    actual_reactor_code = ''
                    for i in reactor_nums:
                        actual_reactor_code += f'{i}'
                    if ans == actual_reactor_code:
                        await current_num_mess.edit(
                            content=' <:green_square:771731921846796318>  <:green_square:771731921846796318>  <:green_square:771731921846796318>  <:green_square:771731921846796318>  <:green_square:771731921846796318> ')
                        await pl.send('Reactor has been started!')
                        reactor_nums, current_num = [], 0
                        gm.tasking[pl]['reac_start'] = False
                        gm.temptask['reac_start'].remove(pl)
                        await check_game_win(gm, pl)
                    else:
                        await pl.send('That was the wrong code! Try again.')
        except KeyError:
            await pl.send("Sorry; that's not allowed")
    else:
        await ctx.send('You\'re not even in a game, {}'.format(pl))


@bot.command()
async def fuel(ctx, *args):
    pl = ctx.message.author
    g_id, u_id = tuple(in_a_game[pl])
    gm = games[g_id][u_id]
    loc_list = [0, 1, 5, 6]
    if pl in in_a_game:
        try:
            if not args:
                if gm.player_locations[gm.players.index(pl)] in loc_list and gm.tasking[pl]['fuel'] and not gm.temptask[
                    'fuel']:
                    gm.temptask['fuel'].append(pl)
                    global start, fuelFill_status, fuelFill_status_message, mess
                    start = await pl.send(f'Starting fuel filling...')
                    fuelFill_status_message = await pl.send('...')
                    fuelFill_status = 0
                    for i in range(5):
                        fuelFill_status += 1
                        mess = fuelFill_status_message.content + ' <:yellow_square:771729639223066654> ' \
                            if i != 0 else ' <:yellow_square:771729639223066654> '
                        await fuelFill_status_message.edit(content=f'{mess}')
                        await asyncio.sleep(1.75)
                    else:
                        await start.edit(content='_')
                        await pl.send(
                            'Fuel is filled and ready to be loaded into reactor.\
                            \nType load (preceded by !fuel) to lead the fuel into the reactor.')
                else:
                    await pl.send("Sorry, that's not allowed")
            else:
                if pl in gm.temptask['fuel'] and gm.player_locations[gm.players.index(pl)] in loc_list:
                    ans = str(args[0])
                    if ans == 'load':
                        await start.edit(content='Emptying fuel...')
                        for _ in range(5):
                            fuelFill_status -= 1
                            mess = ' <:yellow_square:771729639223066654> ' * \
                                   fuelFill_status if fuelFill_status != 0 else ' . '
                            await fuelFill_status_message.edit(content=f'{mess}')
                            await asyncio.sleep(1.75)
                        else:
                            await start.edit(content='_')
                            await pl.send('Reactors are filled with fuel, the task is complete.')
                            gm.tasking[pl]['fuel'] = False
                            gm.temptask['fuel'].remove(pl)
                            fuelFill_status = 0
                            await check_game_win(gm, pl)
                    else:
                        await pl.send('That isnt the right answer! Try again.')
        except KeyError:
            await pl.send("Sorry; that's not allowed")
    else:
        await ctx.send('You\'re not even in a game, {}'.format(pl))


@bot.command()
async def steer(ctx, *args):
    pl = ctx.message.author
    g_id, u_id = tuple(in_a_game[pl])
    gm = games[g_id][u_id]
    loc_list = [23, 24]
    if pl in in_a_game:
        try:
            if not args:
                if gm.player_locations[gm.players.index(pl)] in loc_list and gm.tasking[pl]['steer'] and not \
                gm.temptask['steer']:
                    gm.temptask['steer'].append(pl)
                    global aim_display, needed_aim
                    aims = ['right', 'left', 'up', 'down', 'center']
                    current_aim = aims[4]
                    needed_aim = aims[random.randint(0, 3)]
                    await pl.send(
                        'Type in up, down, right, or left to align the steering (blue)\
                         with the required direction (green).')
                    aim_display = []
                    if needed_aim == 'up':
                        aim_display.append(await pl.send(
                            f'<:red_square:771731748564369418>  <:green_square:771731921846796318>  <:red_square:771731748564369418>'))
                    else:
                        aim_display.append(await pl.send(
                            f'<:red_square:771731748564369418>  <:red_square:771731748564369418>  <:red_square:771731748564369418>'))
                    if needed_aim == 'left':
                        aim_display.append(await pl.send(
                            f'<:green_square:771731921846796318>  <:blue_circle:778569261378437120>  <:red_square:771731748564369418>'))
                    elif needed_aim == 'right':
                        aim_display.append(await pl.send(
                            f'<:red_square:771731748564369418>  <:blue_circle:778569261378437120>  <:green_square:771731921846796318>'))
                    else:
                        aim_display.append(await pl.send(
                            f'<:red_square:771731748564369418>  <:blue_circle:778569261378437120>  <:red_square:771731748564369418>'))
                    if needed_aim == 'down':
                        aim_display.append(await pl.send(
                            f'<:red_square:771731748564369418>  <:green_square:771731921846796318>  <:red_square:771731748564369418>'))
                    else:
                        aim_display.append(await pl.send(
                            f'<:red_square:771731748564369418>  <:red_square:771731748564369418>  <:red_square:771731748564369418>'))
                else:
                    await pl.send("Sorry, that's not allowed")
            else:
                if pl in gm.temptask['steer'] and gm.player_locations[gm.players.index(pl)] in loc_list:
                    ans = str(args[0])
                    if ans == needed_aim:
                        if needed_aim == 'up':
                            await aim_display[0].edit(
                                content=f'<:green_square:771731921846796318>  <:blue_circle:778569261378437120>  <:green_square:771731921846796318>')
                        else:
                            await aim_display[0].edit(
                                content=f'<:green_square:771731921846796318>  <:green_square:771731921846796318>  <:green_square:771731921846796318>')
                        if needed_aim == 'left':
                            await aim_display[1].edit(
                                content=f'<:blue_circle:778569261378437120>  <:green_square:771731921846796318>  <:green_square:771731921846796318>')
                        elif needed_aim == 'right':
                            await aim_display[1].edit(
                                content=f'<:green_square:771731921846796318>  <:green_square:771731921846796318>  <:blue_circle:778569261378437120>')
                        else:
                            await aim_display[1].edit(
                                content=f'<:green_square:771731921846796318>  <:green_square:771731921846796318>  <:green_square:771731921846796318>')
                        if needed_aim == 'down':
                            await aim_display[2].edit(
                                content=f'<:green_square:771731921846796318>  <:blue_circle:778569261378437120>  <:green_square:771731921846796318>')
                        else:
                            await aim_display[2].edit(
                                content=f'<:green_square:771731921846796318>  <:green_square:771731921846796318>  <:green_square:771731921846796318>')
                        await pl.send('Steering is now perfectly aligned.')
                        gm.tasking[pl]['steer'] = False
                        gm.temptask['steer'].remove(pl)
                        await check_game_win(gm, pl)
                    else:
                        await pl.send('That is the wrong direction, try again.')
        except KeyError:
            await pl.send("Sorry; that's not allowed")
    else:
        await ctx.send('You\'re not even in a game, {}'.format(pl))


@bot.command()
async def shields(ctx, *args):
    pl = ctx.message.author
    g_id, u_id = tuple(in_a_game[pl])
    gm = games[g_id][u_id]
    loc_list = [25]
    if pl in in_a_game:
        try:
            if not args:
                if gm.player_locations[gm.players.index(pl)] in loc_list and gm.tasking[pl]['shields'] and not \
                gm.temptask['shields']:
                    gm.temptask['shields'].append(pl)
                    global red_square, yellow_square, tiles, tile_messages
                    red_square, yellow_square = '\U0001F7E5', '\U0001F7E8'
                    letters = ['a', 'b', 'c']
                    tiles = []
                    for i in range(3):
                        row = []
                        for j in range(3):
                            square = random.choice((red_square, yellow_square))
                            row.append(square)
                        tiles.append(row)
                    await pl.send(f'This is the shields log.\
                     \nRed {red_square} represents an unactivated shield.\
                     \nYellow {yellow_square} represents an activated shield.')
                    await pl.send('0\t1\t\t2\t\t3')
                    tile_messages = []
                    for i in range(3):
                        tile_message = letters[i] + '\t'
                        for j in range(3):
                            tile_message += tiles[i][j] + '\t'
                        tile_messages.append(await pl.send(tile_message))
                    await pl.send('Enter the shields you want to activate (preceded by !shields each time)\
                    \nExample: a2 for shield at row a column 2')
                else:
                    await pl.send("Sorry, that's not allowed")
            else:
                if pl in gm.temptask['shields'] and gm.player_locations[gm.players.index(pl)] in loc_list:
                    ans = str(args[0])
                    letters = {'a': 0, 'b': 1, 'c': 2}
                    if ans[0] in letters.keys() and int(ans[1]) in range(1, 4):
                        index1, index2 = letters[ans[0]], int(ans[1]) - 1
                        row, row_message = tiles[index1], tile_messages[index1]
                        row[index2] = yellow_square if row[index2] == red_square else red_square
                        content = f'{ans[0]}\t'
                        for square in row:
                            content += square + '\t'
                        await row_message.edit(content=content)
                        shields_done = True  # checking whether shields has been fixed
                        for rows in tiles:
                            for square in rows:
                                if square != yellow_square:
                                    shields_done = False
                        if shields_done:
                            await pl.send('Shields fixed!')
                        gm.tasking[pl]['shields'] = False
                        gm.temptask['shields'].remove(pl)
                        await check_game_win(gm, pl)
                    else:
                        await pl.send('That isnt the right answer! Try again.')
        except KeyError:
            await pl.send("Sorry; that's not allowed")
    else:
        await ctx.send('You\'re not even in a game, {}'.format(pl))


@bot.command()
async def sample(ctx, *args):
    pl = ctx.message.author
    g_id, u_id = tuple(in_a_game[pl])
    gm = games[g_id][u_id]
    loc_list = [17]
    if pl in in_a_game:
        try:
            if not args:
                if gm.player_locations[gm.players.index(pl)] in loc_list and gm.tasking[pl]['sample'] and not \
                gm.temptask['sample']:
                    gm.temptask['sample'].append(pl)
                    global white_square, blue_square, red_square, samples, display_message, heading
                    white_square, blue_square, red_square = '\U00002B1C', '\U0001F7E6', '\U0001F7E5'
                    heading = await pl.send("Medical samples:")
                    samples = await pl.send(white_square * 5)
                    display_message = await pl.send("Press x (preceded by !sample) to start:")
                else:
                    await pl.send("Sorry, that's not allowed")
            else:
                if pl in gm.temptask['sample'] and gm.player_locations[gm.players.index(pl)] in loc_list:
                    try:
                        ans = int(args[0])
                        its_int = True
                    except:
                        ans = str(args[0])
                        its_int = False
                    if ans == 'x':
                        global n
                        for m in range(1, 6):
                            await samples.edit(content=(blue_square * m + white_square * (5 - m)))
                            await asyncio.sleep(1)
                        await samples.edit(content='.')
                        await display_message.edit(
                            content="Wait for some time before inspecting sample again. Go do something else meanwhile.")
                        for i in range(40, -1, -1):
                            await heading.edit(content=("ETA: " + str(i)))
                            await asyncio.sleep(1)
                        n = random.randint(1, 5)
                        await heading.edit(content='.')
                        await samples.edit(content='.')
                        await display_message.edit(content='.')
                        heading = await pl.send(content="Medical samples:")
                        samples = await pl.send(content=(blue_square * (n - 1) + red_square + blue_square * (5 - n)))
                        display_message = await pl.send(content="Pick the incorrect sample [in Medbay]\
                         (Example: 'sample 1' for 1st sample)")
                    elif its_int and ans == n:
                        await samples.edit(content=blue_square * 5)
                        await display_message.edit(content="Inspect samples task finished!")
                        gm.tasking[pl]['sample'] = False
                        gm.temptask['sample'].remove(pl)
                        await check_game_win(gm, pl)
                    elif its_int and not ans == n:
                        await pl.send("Wrong sample! Try again")
        except KeyError:
            await pl.send("Sorry; that's not allowed")
    else:
        await ctx.send('You\'re not even in a game, {}'.format(pl))


@bot.command()
async def scan_card(ctx, *args):
    pl = ctx.message.author
    g_id, u_id = tuple(in_a_game[pl])
    gm = games[g_id][u_id]
    loc_list = [4, 19]
    if pl in in_a_game:
        try:
            if not args:
                if gm.player_locations[gm.players.index(pl)] in loc_list and gm.tasking[pl]['scan_card'] and not \
                gm.temptask['scan_card']:
                    gm.temptask['scan_card'].append(pl)
                    global can_scan, display, instruction, blue_square, orange_square, card, tick_mark, forward_arrow
                    can_scan = False
                    blue_square, orange_square, card, tick_mark, forward_arrow = '\U0001F7E6', '\U0001F7E7', '💳', '✅', '▶'
                    display = await pl.send(f'{forward_arrow}{blue_square * 5}')
                    instruction = await pl.send("Type 'card' to bring your card")
                else:
                    await pl.send("Sorry, that's not allowed")
            else:
                if pl in gm.temptask['scan_card'] and gm.player_locations[gm.players.index(pl)] in loc_list:
                    ans = str(args[0])
                    if not can_scan:
                        if ans == 'card':
                            await display.edit(content=f'{card}{blue_square * 5}')
                            await instruction.edit(content="Type 'scan' to scan your card")
                            can_scan = True
                        elif ans == 'scan':
                            await pl.send("Bring your card first!")
                    else:
                        if ans == 'scan':
                            await instruction.edit(content="Scanning your card...")
                            for i in range(6):
                                s = ''
                                for j in range(6):
                                    if j == i:
                                        s += card
                                    else:
                                        s += blue_square
                                await display.edit(content=s)
                                await asyncio.sleep(0.1)
                            await instruction.edit(content=tick_mark)
                            gm.tasking[pl]['scan_card'] = False
                            gm.temptask['scan_card'].remove(pl)
                            await check_game_win(gm, pl)
        except KeyError:
            await pl.send("Sorry; that's not allowed")
    else:
        await ctx.send('You\'re not even in a game, {}'.format(pl))


@bot.command()
async def filter(ctx, *args):
    pl = ctx.message.author
    g_id, u_id = tuple(in_a_game[pl])
    gm = games[g_id][u_id]
    loc_list = [21, 3]
    if pl in in_a_game:
        try:
            if not args:
                if gm.player_locations[gm.players.index(pl)] in loc_list and gm.tasking[pl]['filter'] and not \
                gm.temptask['filter']:
                    gm.temptask['filter'].append(pl)
                    global leaf_messages, leaf, leaves
                    leaves = [True if random.randint(0, 1) == 1 else False for _ in range(3)]
                    leaf_messages = [None] * 3
                    leaf = '<:fallen_leaf:786165147198685194>'
                    await pl.send('Type the number(s) (preceded by !filter) against which you see leaves.\
                    \n For example, !filter 12')
                    for i in range(3):
                        leaf_messages[i] = await pl.send(f"{i + 1} {leaf if leaves[i] else ' '}")
                else:
                    await pl.send("Sorry, that's not allowed")
            else:
                if pl in gm.temptask['filter'] and gm.player_locations[gm.players.index(pl)] in loc_list:
                    ans = str(args[0])
                    for i in ans:
                        if leaves[int(i) - 1]:
                            leaves[int(i) - 1] = False
                            for j in range(3):
                                await leaf_messages[j].edit(content=f"{j + 1} {leaf if leaves[j] else ' '}")
                        else:
                            await pl.send('That isnt the right answer! Try again.')
                            break
                    else:
                        leaves = [None] * 3
                        await pl.send('Filters are clean!')
                        gm.tasking[pl]['filter'] = False
                        gm.temptask['filter'].remove(pl)
                        await check_game_win(gm, pl)
        except KeyError:
            await pl.send("Sorry, that's not allowed")
    else:
        await ctx.send('You\'re not even in a game, {}'.format(pl))


async def task_loc(gm, pl):
    current_location = gm.player_locations[gm.players.index(pl)]
    try:
        if current_location in [0, 1, 5, 6]:  # engines
            if gm.tasking[pl]['ali_eng'] == True:
                await pl.send("You can do the Align Engines task. Type !ali_eng")
            if gm.tasking[pl]['fuel'] == True:
                await pl.send("You can do the Fuel Fill task. Type !fuel")
        elif current_location in [14, 15]:  # cafe
            if gm.tasking[pl]['emp'] == True:
                await pl.send("You can do the Empty Chute task. Type !emp")
        elif current_location in [8, 9]:  # electrical
            if gm.tasking[pl]['wires'] == True:
                await pl.send("You can do the Fix Wires task. Type !wires")
        elif current_location in [25]:  # shields
            if gm.tasking[pl]['download'] == True:
                await pl.send("You can do the Download Data task. Type !download")
            if gm.tasking[pl]['shields'] == True:
                await pl.send("You can do the Shields Primer task. Type !shields")
        elif current_location in [13]:  # admin
            if not gm.tasking[pl]['download']:
                if gm.tasking[pl]['upload'] == True:
                    await pl.send("You can do the Upload Data task. Type !upload")
            if gm.tasking[pl]['enter_id'] == True:
                await pl.send("You can do the Enter ID task. Type !enter_id")
        elif current_location in [27]:  # communications
            if gm.tasking[pl]['power'] == True:
                await pl.send("You can do the Divert Power task. Type !power")
            if gm.tasking[pl]['download'] == True:
                await pl.send("You can do the Download Data task. Type !download")
        elif current_location in [19]:  # weapons
            if gm.tasking[pl]['enter_id'] == True:
                await pl.send("You can do the Enter ID task. Type !enter_id")
            if gm.tasking[pl]['scan_card'] == True:
                await pl.send("You can do the Scan Card task. Type !scan_card")
        elif current_location in [3]:  # reactor
            if gm.tasking[pl]['reac_start'] == True:
                await pl.send("You can do the Start Reactor task. Type !reac_start")
            if gm.tasking[pl]['filter'] == True:
                await pl.send("You can do the Clean Filter task. Type !filter")
        elif current_location in [10, 11]:  # storage
            if gm.tasking[pl]['emp'] == True:
                await pl.send("You can do the Empty Chute task. Type !emp")
            if gm.tasking[pl]['wires'] == True:
                await pl.send("You can do the Fix Wires task. Type !wires")
        elif current_location in [23, 24]:  # navigation
            if gm.tasking[pl]['steer'] == True:
                await pl.send("You can do the Stabilize Steering task. Type !steer")
            if not gm.tasking[pl]['download']:
                if gm.tasking[pl]['upload'] == True:
                    await pl.send("You can do the Upload Data task. Type !upload")
        elif current_location in [17]:  # medbay
            if gm.tasking[pl]['med_scan'] == True:
                await pl.send("You can do the Medical Scan task. Type !med_scan")
            if gm.tasking[pl]['sample'] == True:
                await pl.send("You can do the Inspect Samples task. Type !sample")
        elif current_location in [4]:  # security
            if gm.tasking[pl]['scan_card'] == True:
                await pl.send("You can do the Scan Card task. Type !scan_card")
            if gm.tasking[pl]['power'] == True:
                await pl.send("You can do the Divert Power task. Type !power")
        elif current_location in [21]:  # O2
            if gm.tasking[pl]['filter'] == True:
                await pl.send("You can do the Clean Filter task. Type !filter")
    except KeyError:
        pass


# --- Running the bot ---

if __name__ == '__main__':
    print('Running...')
    bot.run(token)
