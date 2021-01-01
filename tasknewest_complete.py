import discord
import time
import asyncio
import random

client = discord.Client()

token = 'NzY5MjA3MjAxNzc1NjE2MDEw.X5LqCA.t55mdsPWQMhI9kAVNBjOexs8Crc'
# id = 767582781621403698
help_message_info = [
    ['!medical-scan', 'Do the medical scan task.'],
    ['!align-eng', 'Align engine task.'],
    ['!wires', 'The electricals task.'],
    ['!emp', 'Empty the garbage chute.'],
    ['!upload', 'Upload data.'],
    ['!download', 'Download data.'],
    ['!power', 'Divert power.'],
    ['!enterid', 'Enter the Id code.'],
    ['!reactor-start', 'Start the reacter.'],
    ['!fuel', 'Collect fuel and empty it into the engine.'],
    ['!steer', 'Stabilize the steering of the ship.'],
    ['!shields', 'The shields priming task.'],
    ['!sample', 'Inspect the samples in MedBay.'],
    ['!scan-card', 'Scan boarding pass'],
    ['!filter', 'Clean the O2 filters.'],
]

task_takers = {
    'medical': '',
    'alignEng': '',
    'emptyChute': '',
    'wireMatch': '',
    'uploadData': '',
    'downloadData': '',
    'power': '',
    'enterid': '',
    'reactorStart': '',
    'fuelFill': '',
    'steer': '',
    'shields': '',
    'sample': '',
    'scan-card': '',
    'filter': '',
}
tasks_taken = {
    'medical': False,
    'alignEng': False,
    'emptyChute': False,
    'wireMatch': False,
    'uploadData': False,
    'downloadData': False,
    'power': False,
    'enterid': False,
    'reactorStart': False,
    'fuelFill': False,
    'steer': False,
    'shields': False,
    'sample': False,
    'scan-card': False,
    'filter': False,
}


async def medical(member, channel, message):
    global task_takers, tasks_taken
    tasks_taken['medical'] = True
    task_takers['medical'] = member
    await member.send(f'Starting medical scan...')
    global medical_status, medical_status_message
    medical_status_message = await member.send('Status: 0 percent complete.')
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
        tasks_taken['medical'] = False
        task_takers['medical'] = ''


async def alignEng(member, channel, message):
    global task_takers, tasks_taken
    tasks_taken['alignEng'] = True
    task_takers['alignEng'] = member
    global antiAlign, alignEng_output
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
    global alignEngMessage
    alignEngMessage = await member.send(
        f'Here is the current engine output:\n{alignEng_output}\nType up or down to move the engine output.')
    alignEngMessage


async def alignEngCheck(member, channel, message):
    global task_takers, tasks_taken, antiAlign, alignEng_output
    ans = message.content.lower().strip()
    if (ans == 'down' and antiAlign == 0) or (ans == 'up' and antiAlign == 1):
        await member.send(f'Task is successfully completed!')
        tasks_taken['alignEng'] = False
        task_takers['alignEng'] = ''
        alignEng_output = f'''

            ----------<:arrow_left:770205021647274004>

        '''
        await alignEngMessage.edit(content=f'Here is the current engine output:\n{alignEng_output}')
    else:
        await member.send('That isnt the right answer! Try again.')


async def emptyChute(member, channel, message):
    global task_takers, tasks_taken
    task_takers['emptyChute'] = member
    tasks_taken['emptyChute'] = True
    await member.send("Type 'down' to pull the lever down and eject the garbage.")


async def emptyChuteCheck(member, channel, message):
    global task_takers, tasks_taken
    ans = message.content.lower().strip()
    if ans == 'down':
        await member.send(f'Starting ejection...')
        tasks_taken['emptyChute'] = False
        task_takers['emptyChute'] = ''
        emptyChute_status_message = await member.send('Status: 0 percent complete.')
        emptyChute_status = 0
        while emptyChute_status < 100:
            emptyChute_status += random.randint(1, 6)
            if emptyChute_status <= 100:
                await emptyChute_status_message.edit(content=f'Status: {emptyChute_status} percent ejected.')
            else:
                await emptyChute_status_message.edit(content=f'Status: 100 percent complete.')
            await asyncio.sleep(0.01)
        else:
            await emptyChute_status_message.edit(content=f'Chute is empty.')
            tasks_taken['emptyChute'] = False
            task_takers['emptyChute'] = ''
    else:
        await member.send('That isnt the right answer! Try again.')


wireMatchColors = []


async def wireMatch(member, channel, message):
    global task_takers, tasks_taken, wireMatchColors
    if tasks_taken['wireMatch']:
        prevlen = len(wireMatchColors)
        for i in wireMatchColors:
            if str(message.content) == i:
                wireMatchColors.remove(i)
                await member.send(f'Correct match! {len(wireMatchColors)} matches left.')
                break
        if len(wireMatchColors) == prevlen:
            await member.send(f'Incorrect match! {len(wireMatchColors)} matches left.')
        if len(wireMatchColors) == 0:
            await member.send('Task completed!')
            tasks_taken['wireMatch'] = False
            task_takers['wireMatch'] = ''

    else:
        tasks_taken['wireMatch'] = True
        task_takers['wireMatch'] = member
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
        await member.send('Match the colors in order to connect the wires, type number-letter to answer one at a time.')
        for i in range(4):
            await member.send(f'{i + 1}                {letters[i]}\n{colors[i]}          {colors_copy[i]}')


async def uploadData(member, channel, message):
    global task_takers, tasks_taken
    task_takers['uploadData'] = member
    tasks_taken['uploadData'] = True
    await member.send(f'Starting data upload...')
    global upload_status, upload_status_message
    upload_status_message = await member.send('Status: 0 percent complete.')
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
        tasks_taken['uploadData'] = False
        task_takers['uploadData'] = ''


async def downloadData(member, channel, message):
    global task_takers, tasks_taken
    task_takers['downloadData'] = member
    tasks_taken['downloadData'] = True
    await member.send(f'Starting data download...')
    global download_status, download_status_message
    download_status_message = await member.send('Status: 0 percent complete.')
    download_status = 0
    while download_status < 100:
        download_status += random.randint(1, 6)
        if download_status <= 100:
            await download_status_message.edit(content=f'Status: {download_status} percent complete.')
        else:
            await download_status_message.edit(content=f'Status: 100 percent complete.')
        await asyncio.sleep(0.01)
    else:
        await download_status_message.edit(content=f'download is complete.')
        tasks_taken['downloadData'] = False
        task_takers['downloadData'] = ''


async def power(member, channel, message):
    global task_takers, tasks_taken
    task_takers['power'], tasks_taken['power'] = member, True
    global power_switch, names, switches
    switches = ['cafetaria', 'admin',
                'navigation', 'reactor', 'communications']
    power_switch = random.choice(switches)
    names = ''
    for i in switches:
        names += i + '     '
    await member.send('Type in the name of the section which needs more power.')
    await member.send(names)
    global messes
    messes = []
    for i in range(4):
        mess = ''
        for j in switches:
            if j == power_switch and i < 2:
                mess += '<:small_red_triangle:774298438309117963>       '
            else:
                mess += '<:red_square:774296927059443735>       '
        messes.append(await member.send(mess))


async def powerCheck(member, channel, message):
    global task_takers, tasks_taken
    ans = message.content.lower().strip()
    if ans == power_switch:
        global messes
        for i in range(4):
            mess = ''
            for _ in switches:
                mess += '<:red_square:774296927059443735>       '
            await messes[i].edit(content=mess)
        await member.send('Power successfully diverted.')
        tasks_taken['power'], task_takers['power'] = False, ''
    else:
        await member.send('Thats not the correct answer, try again.')


async def enterid(member, channel, message):
    global task_takers, tasks_taken, code, code_message
    code = random.randint(20000, 80000)
    tasks_taken['enterid'], task_takers['enterid'] = True, member
    await member.send('Type the id before it changes:')
    code_message = await member.send(f'{code}')
    await asyncio.sleep(8)
    while tasks_taken['enterid']:
        code = random.randint(20000, 80000)
        await code_message.edit(content=f'{code}')
        await asyncio.sleep(8)


async def enteridCheck(member, channel, message):
    global task_takers, tasks_taken, code, code_message
    ans = message.content.lower().strip()
    if ans == str(code):
        task_takers['enterid'], tasks_taken['enterid'] = '', False
        await member.send('Id accepted!')
        code = ''
    else:
        await member.send('That was the wrong id! Try again.')


async def reactorStart(member, channel, message):
    global task_takers, tasks_taken, reactor_nums, current_num_mess, current_num
    reactor_nums = [random.randint(1, 6) for _ in range(5)]
    tasks_taken['reactorStart'], task_takers['reactorStart'] = True, member
    current_num = 0
    await member.send(
        'Memorize the digits shown below and type them out as a number\nExample: 12345\n(there are 5 digits, wait and memorize):')
    current_num_mess = await member.send(
        f' {reactor_nums[current_num]} <:blue_square:771732144279388210>  <:blue_square:771732144279388210>  <:blue_square:771732144279388210>  <:blue_square:771732144279388210>  ')
    await asyncio.sleep(2.5)
    while tasks_taken['reactorStart']:
        mess = ''
        current_num = current_num + 1 if current_num < 4 else 0
        for i in range(5):
            if i == current_num:
                mess += f' {reactor_nums[current_num]} '
            else:
                mess += ' <:blue_square:771732144279388210> '
        await current_num_mess.edit(content=f'{mess}')
        await asyncio.sleep(2)


async def reactorStartCheck(member, channel, message):
    global task_takers, tasks_taken, reactor_nums, current_num_mess, current_num
    ans = message.content.lower().strip()
    actual_reactor_code = ''
    for i in reactor_nums:
        actual_reactor_code += f'{i}'
    if ans == actual_reactor_code:
        task_takers['reactorStart'], tasks_taken['reactorStart'] = '', False
        await current_num_mess.edit(
            content=' <:green_square:771731921846796318>  <:green_square:771731921846796318>  <:green_square:771731921846796318>  <:green_square:771731921846796318>  <:green_square:771731921846796318> ')
        await member.send('Reactor has been started!')
        reactor_nums, current_num = [], 0
    else:
        await member.send('That was the wrong code! Try again.')


async def fuelFill(member, channel, message):
    global task_takers, tasks_taken
    task_takers['fuelFill'] = member
    tasks_taken['fuelFill'] = True
    global fuelFill_status, fuelFill_status_message, start
    start = await member.send(f'Starting fuel filling...')
    fuelFill_status_message = await member.send('...')
    fuelFill_status = 0
    for i in range(5):
        fuelFill_status += 1
        mess = fuelFill_status_message.content + \
            ' <:yellow_square:771729639223066654> ' if i != 0 else ' <:yellow_square:771729639223066654> '
        await fuelFill_status_message.edit(content=f'{mess}')
        await asyncio.sleep(1.75)
    else:
        await start.edit(content='_')
        await member.send(
            'Fuel is filled and ready to be loaded into reactor.\nType !load to lead the fuel into the reactor.')


async def fuelFillCheck(member, channel, message):
    global task_takers, tasks_taken, fuelFill_status, fuelFill_status_message, start
    if fuelFill_status == 5:
        await start.edit(content='Emptying fuel...')
        for _ in range(5):
            fuelFill_status -= 1
            mess = ' <:yellow_square:771729639223066654> ' * \
                   fuelFill_status if fuelFill_status != 0 else ' . '
            await fuelFill_status_message.edit(content=f'{mess}')
            await asyncio.sleep(1.75)
        else:
            await start.edit(content='_')
            await member.send('Reactors are filled with fuel, the task is complete.')
            task_takers['fuelFill'], tasks_taken['fuelFill'] = '', False
            fuelFill_status = 0
    else:
        await member.send('The fuel has not completely filled yet, wait for a while.')


async def steer(member, channel, message):
    global task_takers, tasks_taken, current_aim, needed_aim, aims, aim_display
    task_takers['steer'] = member
    tasks_taken['steer'] = True
    aims = ['right', 'left', 'up', 'down', 'center']
    current_aim = aims[4]
    needed_aim = aims[random.randint(0, 3)]
    await member.send(
        'Type in up, down, right, or left to align the steering (blue) with the required direction (green).')
    aim_display = []
    if needed_aim == 'up':
        aim_display.append(await member.send(
            f'<:red_square:771731748564369418>  <:green_square:771731921846796318>  <:red_square:771731748564369418>'))
    else:
        aim_display.append(await member.send(
            f'<:red_square:771731748564369418>  <:red_square:771731748564369418>  <:red_square:771731748564369418>'))
    if needed_aim == 'left':
        aim_display.append(await member.send(
            f'<:green_square:771731921846796318>  <:blue_circle:778569261378437120>  <:red_square:771731748564369418>'))
    elif needed_aim == 'right':
        aim_display.append(await member.send(
            f'<:red_square:771731748564369418>  <:blue_circle:778569261378437120>  <:green_square:771731921846796318>'))
    else:
        aim_display.append(await member.send(
            f'<:red_square:771731748564369418>  <:blue_circle:778569261378437120>  <:red_square:771731748564369418>'))
    if needed_aim == 'down':
        aim_display.append(await member.send(
            f'<:red_square:771731748564369418>  <:green_square:771731921846796318>  <:red_square:771731748564369418>'))
    else:
        aim_display.append(await member.send(
            f'<:red_square:771731748564369418>  <:red_square:771731748564369418>  <:red_square:771731748564369418>'))


async def steerCheck(member, channel, message):
    global task_takers, tasks_taken, current_aim, needed_aim, aims, aim_display
    ans = message.content.lower().strip()
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
        await member.send('Steering is now perfectly aligned.')
        task_takers['steer'] = ''
        tasks_taken['steer'] = False
    else:
        await member.send('That is the wrong direction, try again.')


async def shields(member, channel, message):
    global task_takers, tasks_taken, tiles, tile_messages
    task_takers['shields'], tasks_taken['shields'] = member, True
    red_square, yellow_square = '\U0001F7E5', '\U0001F7E8'
    letters = ['a', 'b', 'c']
    tiles = []
    for i in range(3):
        row = []
        for j in range(3):
            square = random.choice((red_square, yellow_square))
            row.append(square)
        tiles.append(row)
    await member.send(f'This is the shields log.')
    await member.send(f'Red {red_square} represents an unactivated shield.')
    await member.send(f'Yellow {yellow_square} represents an activated shield.')
    await member.send('0\t1\t\t2\t\t3')
    tile_messages = []
    for i in range(3):
        tile_message = letters[i] + '\t'
        for j in range(3):
            tile_message += tiles[i][j] + '\t'
        tile_messages.append(await member.send(tile_message))
    await member.send('Enter the shields you want to activate')
    await member.send('Example: a2 for shield at row a column 2')


async def shields_check(member, channel, message):
    global task_takers, tasks_taken, tiles, tile_messages
    red_square, yellow_square = '\U0001F7E5', '\U0001F7E8'
    letters = {'a': 0, 'b': 1, 'c': 2}
    letter, number = message.content[0], eval(message.content[1])
    if letter in letters.keys() and number in range(1, 4):
        index1, index2 = letters[letter], number - 1
        row, row_message = tiles[index1], tile_messages[index1]
        row[index2] = yellow_square if row[index2] == red_square else red_square
        content = f'{letter}\t'
        for square in row:
            content += square + '\t'
        await row_message.edit(content=content)
        shields_done = True  # checking whether shields has been fixed
        for rows in tiles:
            for square in rows:
                if square != yellow_square:
                    shields_done = False
        if shields_done:
            await member.send('Shields fixed!')
            task_takers['shields'], tasks_taken['shields'] = '', False
    else:
        await member.send('Invalid choice. Try again')


async def sample(member, channel, message):
    global task_takers, tasks_taken, heading, samples, display_message, n
    content = message.content
    white_square, blue_square, red_square = '\U00002B1C', '\U0001F7E6', '\U0001F7E5'
    if not tasks_taken['sample'] and content.startswith('!sample'):
        task_takers['sample'], tasks_taken['sample'] = member, True
        heading = await member.send("Medical samples:")
        samples = await member.send(white_square * 5)
        display_message = await member.send("Press x to start:")
    elif member == task_takers['sample'] and content == 'x':
        for i in range(1, 6):
            await samples.edit(content=(blue_square * i + white_square * (5 - i)))
            await asyncio.sleep(1)
        await samples.edit(content='.')
        await display_message.edit(
            content="Wait for 60 seconds to inspect sample again. \nGo do something else meanwhile.")
        await member.send("Use !sample to return to this task later.")
        for i in range(60, -1, -1):
            await heading.edit(content=("ETA: " + str(i)))
            await asyncio.sleep(1)
        n = random.randint(1, 5)
        await heading.edit(content="Medical samples:")
        await samples.edit(content=(blue_square * (n - 1) + red_square + blue_square * (5 - n)))
        await display_message.edit(content="Pick the incorrect sample (Example: 'sample 1' for 1st sample)")
    elif member == task_takers['sample'] and content == '!sample':
        heading_content = heading.content
        samples_content = samples.content
        display_message_content = display_message.content
        await heading.edit(content='.')
        await samples.edit(content='.')
        await display_message.edit(content='.')
        heading = await member.send(heading_content)
        samples = await member.send(samples_content)
        display_message = await member.send(display_message_content)
    elif member == task_takers['sample'] and content.startswith('sample'):
        choice = content.split()[1]
        if eval(choice) == n:
            await samples.edit(content=blue_square*5)
            await display_message.edit(content="Inspect samples task finished!")
            task_takers['sample'], tasks_taken['sample'] = '', False
        else:
            await member.send("Wrong sample! Try again")


async def scan_boarding_pass(member, channel, message):
    global task_takers, tasks_taken, display, instruction
    content = message.content
    blue_square, orange_square, card, tick_mark, forward_arrow = '\U0001F7E6', '\U0001F7E7', '💳', '✅', '▶'
    if not tasks_taken['scan-card']:
        task_takers['scan-card'], tasks_taken['scan-card'] = member, True
        display = await member.send(f'{forward_arrow}{blue_square*5}')
        instruction = await member.send("Type 'card' to bring your card")
    elif content.startswith('card'):
        await display.edit(content=f'{card}{blue_square*5}')
        await instruction.edit(content="Type 'scan' to scan your card")
    elif content.startswith('scan'):
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
        task_takers['scan-card'], tasks_taken['scan-card'] = '', False


async def filter_leaves(member, channel, message):
    global task_takers, tasks_taken, leaves, leaf_messages
    tasks_taken['filter'], task_takers['filter'] = True, member
    leaves = [True if random.randint(0, 1) == 1 else False for _ in range(3)]
    leaf_messages = [None]*3
    leaf = '<:fallen_leaf:786165147198685194>'
    await member.send('Type the number(s) against which you see leaves.')
    for i in range(3):
        leaf_messages[i] = await member.send(f"{i+1} {leaf if leaves[i] else ' '}")


async def filter_leaves_check(member, channel, message):
    global tasks_taken, task_takers, leaves, leaf_messages
    try:
        ans = int(message.content.lower().strip())
        if leaves[ans-1]:
            leaves[ans-1] = False
            leaf = '<:fallen_leaf:786165147198685194>'
            for i in range(3):
                await leaf_messages[i].edit(content=f"{i+1} {leaf if leaves[i] else ' '}")
            if leaves == [False]*3:
                tasks_taken['filter'], task_takers['filter'] = False, ''
                leaves = [None]*3
                await member.send('Filters are clean!')
    except:
        return


@client.event
async def on_ready():
    print('{0.user} online.'.format(client))
    global task_takers, tasks_taken


@client.event
async def on_message(message):
    id = client.get_guild(767582781621403698)

    if message.author == client.user:
        return

    else:
        if message.content == '!help':
            embed = discord.Embed(title='Help on the bot',
                                  description='Some useful stuff')
            for item in help_message_info:
                embed.add_field(name=item[0], value=item[1])
            await message.channel.send(embed=embed)

        elif message.content.startswith('!medical-scan'):
            await medical(message.author, message.channel, message)
            # await message.channel.send(response)

        elif message.content.startswith('!align-eng'):
            await alignEng(message.author, message.channel, message)

        elif message.author == task_takers['alignEng']:
            await alignEngCheck(message.author, message.channel, message)

        elif message.content.startswith('!emp'):
            await emptyChute(message.author, message.channel, message)

        elif message.author == task_takers['emptyChute']:
            await emptyChuteCheck(message.author, message.channel, message)

        elif message.content.startswith('!wires'):
            await wireMatch(message.author, message.channel, message)

        elif message.author == task_takers['wireMatch']:
            await wireMatch(message.author, message.channel, message)

        elif message.content.startswith('!upload'):
            await uploadData(message.author, message.channel, message)

        elif message.content.startswith('!download'):
            await downloadData(message.author, message.channel, message)

        elif message.content.startswith('!power'):
            await power(message.author, message.channel, message)

        elif message.author == task_takers['power']:
            await powerCheck(message.author, message.channel, message)

        elif message.content.startswith('!enterid'):
            await enterid(message.author, message.channel, message)

        elif message.author == task_takers['enterid']:
            await enteridCheck(message.author, message.channel, message)

        elif message.content.startswith('!reactor-start'):
            await reactorStart(message.author, message.channel, message)

        elif message.author == task_takers['reactorStart']:
            await reactorStartCheck(message.author, message.channel, message)

        elif message.content.startswith('!fuel'):
            await fuelFill(message.author, message.channel, message)

        elif message.author == task_takers['fuelFill'] and message.content.startswith('!load'):
            await fuelFillCheck(message.author, message.channel, message)

        elif message.content.startswith('!steer'):
            await steer(message.author, message.channel, message)

        elif message.author == task_takers['steer']:
            await steerCheck(message.author, message.channel, message)

        elif message.content.startswith('!shields'):
            await shields(message.author, message.channel, message)

        elif message.author == task_takers['shields']:
            await shields_check(message.author, message.channel, message)

        elif message.content.startswith('!sample') or message.author == task_takers['sample']:
            await sample(message.author, message.channel, message)

        elif message.content.startswith('!scan-card') or message.author == task_takers['scan-card']:
            await scan_boarding_pass(message.author, message.channel, message)

        elif message.content.startswith('!filter'):
            await filter_leaves(message.author, message.channel, message)

        elif message.author == task_takers['filter']:
            await filter_leaves_check(message.author, message.channel, message)


# client.loop.create_task(task())
# client.loop.create_task(task_check())
client.run(token)
