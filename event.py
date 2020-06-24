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
    WANDERERS_MINUET = 1002216
    ARMYS_PAEON = 1002218


# 0の場合も少数を返さないと演算でエラーが出る
def get_synergy(pool, buffs):
    return sum([pool.get(b, .0) for b in buffs]) or .0


def get_crit_synergy(d):
    return get_synergy({Aura.BATTLE_LITANY: .1, Aura.CHAIN_STRATAGEM: .1, Aura.WANDERERS_MINUET: .02}, d.buffs)


def get_dh_synergy(d):
    return get_synergy({Aura.BATTLE_VOICE: .2, Aura.ARMYS_PAEON: .03}, d.buffs)
