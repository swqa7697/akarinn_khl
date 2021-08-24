import yaml

bot_conf = yaml.load(open('../conf/bot.yaml', encoding='utf-8'), Loader=yaml.FullLoader)


def conf_general() -> dict:
    return bot_conf['general']


def api_root() -> dict:
    return bot_conf['general']['api_root']


def conf_khl() -> dict:
    return bot_conf['khl']

def conf_enable_shaidao() -> bool:
    return bot_conf['extra']['is_shaidao_mode']
