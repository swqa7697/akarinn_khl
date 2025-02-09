import re
from datetime import datetime, date, timedelta

from khl import Bot, Cert, TextMsg, logger

from config import conf_general, conf_khl, conf_extra, conf_enable_shaidao
from req import get_status, today_battle_count, today_battle_logs, add_member, get_game_id, commit_battle, \
    commit_current_battle, get_current_battle

bot = Bot(cert=Cert(**conf_khl()))

is_shaidao_mode = conf_enable_shaidao()
admins = conf_extra()['admins']

def pcr_today() -> date:
    return date.today() - timedelta(hours=(conf_general()['time_zone'] - 3))


@bot.command(name='状态')
async def info(msg: TextMsg):
    if is_shaidao_mode:
        return
    
    status = await get_status()
    count = await today_battle_count()
    logs = await today_battle_logs()

    last_battle_time_str = '今日无出刀记录'
    last_defeat_time_str = '今日无击败记录'
    if len(logs):
        last_battle_time_str = f'{int((datetime.utcnow() - logs[0].when).seconds / 60)} 分钟前'
        for i in logs:
            if i.is_defeat_boss:
                last_defeat_time_str = f'{int((datetime.utcnow() - i.when).seconds / 60)} 分钟'
                break

    ext_info_fields = [{
        "type": "kmarkdown",
        "content": f"**今日出刀数**\n {count} / 90"
    }, {
        "type": "kmarkdown",
        "content": f"**上一刀时间**\n{last_battle_time_str}"
    }, {
        "type": "kmarkdown",
        "content": f"**当前王已存活**\n{last_defeat_time_str}"
    }]

    card = [{
        "type":
            "card",
        "size":
            "lg",
        "theme":
            "info",
        "modules": [{
            "type": "header",
            "text": f"当前进度：{status.glob.round} 周目"
        }, *[{
            "type":
                "action-group",
            "elements": [{
                "type": "button",
                "theme": {
                    'active': 'success',
                    'defeated': 'danger',
                    'waiting': 'info'
                }[i.status.value],
                "value": "",
                "text": f"{i.number} 王：{i.hp}/{i.max_hp}"
            }]
        } for i in status.detail], {
            "type": "divider"
        }, {
            "type": "section",
            "text": {
                "type": "paragraph",
                "cols": len(ext_info_fields),
                "fields": ext_info_fields
            }
        }]
    }]

    await msg.reply_card(card)


@bot.command(name='加入公会', aliases=['加入工会'])
async def join_clan(msg: TextMsg, game_id: str):
    if is_shaidao_mode:
        return
    
    try:
        await add_member({
            "game_id": int(game_id),
            "contact_khl": msg.author_id
        })
        await msg.reply('已加入')
    except Exception as e:
        print(e)
        await msg.reply(f'错误：{e.args}\n用法：加入公会+空格+游戏数字id')


@bot.command(name='报刀')
async def post_battle_commit(msg: TextMsg, boss: str, dmg: str, day: str = ''):
    if is_shaidao_mode:
        return
    
    status = await get_status()

    match = re.match(r'(\d+)([Ww万Kk千])?', dmg)
    dmg = int(match.group(1)) * {
        'W': 10000,
        'w': 10000,
        '万': 10000,
        'k': 1000,
        'K': 1000,
        '千': 1000
    }.get(match.group(2), 1)

    real_day = pcr_today()
    if day == '昨天':
        real_day = real_day - timedelta(1)

    try:
        resp = await commit_battle({
            "who": (await get_game_id(msg.author_id))[0],
            "which_day":
                str(real_day),
            "which_round":
                status.glob.round,
            "which_boss":
                int(boss),
            "damage":
                dmg,
            "executor": (await get_game_id(msg.author_id))[0]
        })

        status = resp.status
        which = status.detail[resp.log.which_boss - 1]
        card = [{
            "type":
                "card",
            "size":
                "lg",
            "theme":
                "info",
            "modules": [{
                "type": "section",
                "text": f"报刀成功，当前进度：{status.glob.round} 周目",
                "mode": "right",
                "accessory": {
                    "type": "button",
                    "theme": {
                        'active': 'success',
                        'defeated': 'danger',
                        'waiting': 'info'
                    }[which.status.value],
                    "text":
                        f"{resp.log.which_boss} 王：{which.hp}/{which.max_hp}"
                }
            }]
        }]
    except Exception as e:
        print(e)
        card = [{
            "type": "card",
            "theme": "danger",
            "size": "lg",
            "modules": [{
                "type": "section",
                "text": f"报刀失败：{e.args}"
            }]
        }]

    await msg.reply_card(card)


@bot.command('sl', aliases=['SL'])
async def sl(msg: TextMsg, day: str = ''):
    if is_shaidao_mode:
        return
    
    real_day = pcr_today()
    if day == '昨天':
        real_day = real_day - timedelta(1)

    try:
        await commit_battle({
            "who": (await get_game_id(msg.author_id))[0],
            "executor": (await get_game_id(msg.author_id))[0],
            "which_day": str(real_day),
            "sl": True
        })
        card = [{
            "type": "card",
            "theme": "info",
            "size": "lg",
            "modules": [{
                "type": "section",
                "text": f"sl成功"
            }]
        }]
    except Exception as e:
        print(e)
        card = [{
            "type": "card",
            "theme": "danger",
            "size": "lg",
            "modules": [{
                "type": "section",
                "text": f"sl失败：{e.args}"
            }]
        }]

    await msg.reply_card(card)


@bot.command('尾刀')
async def weidao(msg: TextMsg, which_boss: str, day: str = ''):
    if is_shaidao_mode:
        return
    
    which_boss = int(which_boss)
    status = await get_status()

    dmg = status.detail[which_boss - 1].hp

    real_day = pcr_today()
    if day == '昨天':
        real_day = real_day - timedelta(1)

    try:
        resp = await commit_battle({
            "who": (await get_game_id(msg.author_id))[0],
            "which_day":
                str(real_day),
            "which_round":
                status.glob.round,
            "which_boss":
                which_boss,
            "damage":
                dmg,
            "executor": (await get_game_id(msg.author_id))[0]
        })

        status = resp.status
        card = [{
            "type":
                "card",
            "size":
                "lg",
            "theme":
                "info",
            "modules": [{
                "type": "section",
                "text": f"报刀成功，当前进度：{status.glob.round} 周目"
            }, *[{
                "type":
                    "action-group",
                "elements": [{
                    "type": "button",
                    "theme": {
                        'active': 'success',
                        'defeated': 'danger',
                        'waiting': 'info'
                    }[i.status.value],
                    "value": "",
                    "text": f"{i.number} 王：{i.hp}/{i.max_hp}"
                }]
            } for i in status.detail]]
        }]
    except Exception as e:
        print(e)
        card = [{
            "type": "card",
            "theme": "danger",
            "size": "lg",
            "modules": [{
                "type": "section",
                "text": f"报刀失败：{e.args}"
            }]
        }]

    await msg.reply_card(card)


@bot.command('进刀')
async def enter(msg: TextMsg, which_boss: str = '', comment: str = ''):
    if not is_shaidao_mode:
        try:
            if not which_boss:
                raise Exception("arg 'which_boss' is required")
            
            await commit_current_battle({
                "who": (await get_game_id(msg.author_id))[0],
                "executor": (await get_game_id(msg.author_id))[0],
                "which_boss":
                    int(which_boss),
                "type":
                    "enter",
                "comment":
                    comment
            })
            card = [{
                "type": "card",
                "theme": "info",
                "size": "lg",
                "modules": [{
                    "type": "section",
                    "text": f"成功进刀"
                }]
            }]
        except Exception as e:
            print(e)
            card = [{
                "type": "card",
                "theme": "danger",
                "size": "lg",
                "modules": [{
                    "type": "section",
                    "text": f"进刀失败：{e.args}"
                }]
            }]

        await msg.reply_card(card)
    
    else:
        if not msg.mention:
            card = [{
                "type": "card",
                "theme": "danger",
                "size": "lg",
                "modules": [{
                    "type": "section",
                    "text": {
                        "type": "paragraph",
                        "cols": 2,
                        "fields": [{
                            "type": "kmarkdown",
                            "content": "**进刀失败**\n请勿进入实战！"
                        },
                        {
                            "type": "kmarkdown",
                            "content": "**原因**\n请@被代刀人"
                        }]
                    }
                }]
            }]
            await msg.reply_card(card)
        elif len(msg.mention) == 1:
            mentioned = msg.mention[0]
            if mentioned not in daidao_status:
                card = [{
                    "type": "card",
                    "theme": "danger",
                    "size": "lg",
                    "modules": [{
                        "type": "section",
                        "text": {
                            "type": "paragraph",
                            "cols": 2,
                            "fields": [{
                                "type": "kmarkdown",
                                "content": "**进刀失败**\n请勿进入实战！"
                            },
                            {
                                "type": "kmarkdown",
                                "content": "**原因**\n请先记录上号"
                            }]
                        }
                    }]
                }]
                await msg.reply_card(card)
            elif daidao_status[mentioned] != msg.author_id:
                daidao_message = "**负责刀手**\n(met)" + daidao_status[mentioned] + "(met)"
                card = [{
                    "type": "card",
                    "theme": "danger",
                    "size": "lg",
                    "modules": [{
                        "type": "section",
                        "text": {
                            "type": "paragraph",
                            "cols": 3,
                            "fields": [{
                                "type": "kmarkdown",
                                "content": "**进刀失败**\n请勿进入实战！"
                            },
                            {
                                "type": "kmarkdown",
                                "content": "**原因**\n此账号正在代刀"
                            },
                            {
                                "type": "kmarkdown",
                                "content": daidao_message
                            }]
                        }
                    }]
                }]
                await msg.reply_card(card)
            else:
                card = [{
                    "type": "card",
                    "theme": "success",
                    "size": "lg",
                    "modules": [{
                        "type": "section",
                        "text": {
                            "type": "kmarkdown",
                            "content": "**进刀成功**\n请确认阵容截图无误后进入实战"
                        }
                    }]
                }]
                await msg.reply_card(card)


@bot.command('挂树')
async def tree(msg: TextMsg, which_boss: str, comment: str = ''):
    if is_shaidao_mode:
        return
    
    try:
        await commit_current_battle({
            "who": (await get_game_id(msg.author_id))[0],
            "executor": (await get_game_id(msg.author_id))[0],
            "which_boss":
                int(which_boss),
            "type":
                "waiting",
            "comment":
                comment
        })
        card = [{
            "type": "card",
            "theme": "info",
            "size": "lg",
            "modules": [{
                "type": "section",
                "text": f"成功上树"
            }]
        }]
    except Exception as e:
        print(e)
        card = [{
            "type": "card",
            "theme": "danger",
            "size": "lg",
            "modules": [{
                "type": "section",
                "text": f"上树失败：{e.args}"
            }]
        }]

    await msg.reply_card(card)


@bot.command('查进')
async def check_enter(msg: TextMsg):
    if is_shaidao_mode:
        return
    
    resp = await get_current_battle()
    if not resp:
        await msg.reply(f'当前无人进刀')
    rep_str = '\n'.join(
        [f"{i.who} {i.which_boss} {i.type} {i.comment}" for i in resp])
    await msg.reply(f'当前进刀情况：\n{rep_str}')


daidao_status = dict()

@bot.command('上号')
async def daidaoLogin(msg: TextMsg, *args):
    if not is_shaidao_mode:
        return
    
    sender = msg.author_id
    for person in msg.mention:
        if person in daidao_status:
            #正在代刀，不可上号
            daidao_message = "**负责刀手**\n(met)" + daidao_status[person] + "(met)"
            card = [{
                "type": "card",
                "theme": "danger",
                "size": "lg",
                "modules": [{
                    "type": "section",
                    "text": {
                        "type": "paragraph",
                        "cols": 2,
                        "fields": [{
                            "type": "kmarkdown",
                            "content": "**请勿上号！**\n此账号正在代刀"
                        },
                        {
                            "type": "kmarkdown",
                            "content": daidao_message
                        }]
                    }
                }]
            }]
            await msg.reply_card(card)
        else:
            #可以上号，记录上号情况
            daidao_status[person] = sender
            card = [{
                "type": "card",
                "theme": "success",
                "size": "lg",
                "modules": [{
                    "type": "section",
                    "text": {
                        "type": "kmarkdown",
                        "content": "可以上号，已记录"
                    }
                }]
            }]
            await msg.reply_card(card)


@bot.command('下号')
async def daidaoLogout(msg: TextMsg, *args):
    if not is_shaidao_mode:
        return
    
    sender = msg.author_id
    for person in msg.mention:
        if not person in daidao_status:
            card = [{
                "type": "card",
                "theme": "warning",
                "size": "lg",
                "modules": [{
                    "type": "section",
                    "text": {
                        "type": "kmarkdown",
                        "content": "该账号没有代刀"
                    }
                }]
            }]
            await msg.reply_card(card)
        elif daidao_status[person] != sender:
            card = [{
                "type": "card",
                "theme": "warning",
                "size": "lg",
                "modules": [{
                    "type": "section",
                    "text": {
                        "type": "kmarkdown",
                        "content": "该账号不由您代刀"
                    }
                }]
            }]
            await msg.reply_card(card)
        else:
            del daidao_status[person]
            card = [{
                "type": "card",
                "theme": "success",
                "size": "lg",
                "modules": [{
                    "type": "section",
                    "text": {
                        "type": "kmarkdown",
                        "content": "已记录下号，请及时**回到登录界面**并删除登录记录，防止重开游戏自动登录原账号"
                    }
                }]
            }]
            await msg.reply_card(card)


@bot.command('我的代刀')
async def daidaoSender(msg: TextMsg):
    if not is_shaidao_mode:
        return
    
    sender = msg.author_id
    people = []
    for person in daidao_status:
        if daidao_status[person] == sender:
            people.append(person)
    if len(people) == 0:
        await msg.reply('您当前没有代刀')
    else:
        daidao_message = "**您的代刀**"
        for person in people:
            daidao_message += "\n(met)" + person + "(met)"
        
        card = [{
            "type": "card",
            "theme": "success",
            "size": "lg",
            "modules": [{
                "type": "section",
                "text": {
                    "type": "kmarkdown",
                    "content": daidao_message
                }
            }]
        }]
        await msg.reply_card(card)

@bot.command('所有代刀')
async def daidaoAll(msg: TextMsg):
    if not is_shaidao_mode:
        return
    
    if not daidao_status:
        await msg.reply('当前没有代刀记录')
    else:
        daidao_message1 = "**刀手**"
        daidao_message2 = "**被代刀账号**"
        for k, v in sorted(daidao_status.items(), key = lambda item: item[1]):
            daidao_message1 += "\n(met)" + v + "(met)"
            daidao_message2 += "\n(met)" + k + "(met)"
        card = [{
            "type": "card",
            "theme": "success",
            "size": "lg",
            "modules": [{
                "type": "section",
                "text": {
                    "type": "paragraph",
                    "cols": 2,
                    "fields": [{
                        "type": "kmarkdown",
                        "content": daidao_message1
                    },
                    {
                        "type": "kmarkdown",
                        "content": daidao_message2
                    }]
                }
            }]
        }]
        await msg.reply_card(card)


@bot.command('删除代刀')
async def daidaoDelet(msg: TextMsg, *args):
    if not is_shaidao_mode:
        return
    
    if msg.author_id not in admins:
        card = [{
            "type": "card",
            "theme": "warning",
            "size": "lg",
            "modules": [{
                "type": "section",
                "text": {
                    "type": "kmarkdown",
                    "content": "无管理权限"
                }
            }]
        }]
        await msg.reply_card(card)
        return
    
    if not msg.mention:
        await msg.reply('请@删除对象的号主')
    elif len(msg.mention) > 1:
        await msg.reply('本指令单次仅删除一条代刀记录；如需删除**全部**代刀记录，请使用清除代刀指令')
    else:
        to_be_del = msg.mention[0]
        if to_be_del in daidao_status:
            del daidao_status[to_be_del]
            await msg.reply('已删除代刀记录')
        else:
            await msg.reply('该账号没有代刀')


@bot.command('清除代刀')
async def daidaoClear(msg: TextMsg):
    if not is_shaidao_mode:
        return
    
    if msg.author_id not in admins:
        card = [{
            "type": "card",
            "theme": "warning",
            "size": "lg",
            "modules": [{
                "type": "section",
                "text": {
                    "type": "kmarkdown",
                    "content": "无管理权限"
                }
            }]
        }]
        await msg.reply_card(card)
        return
    
    global daidao_status
    daidao_status = {}
    await msg.reply('已重置代刀记录')

logger.enable_debug()

if __name__ == '__main__':
    bot.run()
