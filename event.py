class Damage(dict):
    @property
    def val(self):
        return self['amount']

    @property
    def is_dh(self):
        return self.get('multistrike', False)

    @property
    def is_crit(self):
        return self['hitType'] == 2

    @property
    def buffs(self):
        return [int(b) for b in self['buffs'].split('.') if b]


class Aura(object):
    BATTLE_LITANY = 1000786
    BATTLE_VOICE = 1000141
    CHAIN_STRATAGEM = 1001221


# 0の場合も少数を返さないと演算でエラーが出る
def get_crit_synergy(self):
    return sum([.1 for b in self.buffs if b in [Aura.BATTLE_LITANY, Aura.CHAIN_STRATAGEM]]) or 0.0


def get_dh_synergy(self):
    return .2 if Aura.BATTLE_VOICE in self.buffs else 0.0
