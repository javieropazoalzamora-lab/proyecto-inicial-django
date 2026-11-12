"""Utilidades para trabajar con los bloques horarios libres."""

HUECO_MAX_MIN = 20  # recreos de 15 min se unen; el almuerzo (60 min) no


def _minutos(hora):
    h, m = hora.split(':')
    return int(h) * 60 + int(m)


def _texto(minutos):
    return f"{minutos // 60}:{minutos % 60:02d}"


def unir_bloques(bloques):
    """['9:40-10:50', '11:05-12:15', '14:40-15:50'] -> [(580, 735), (880, 950)] (minutos desde 00:00).

    Une bloques seguidos o separados solo por un recreo corto."""
    intervalos = []
    for b in bloques or []:
        ini, fin = b.split('-')
        intervalos.append((_minutos(ini), _minutos(fin)))
    intervalos.sort()
    unidos = []
    for ini, fin in intervalos:
        if unidos and ini - unidos[-1][1] <= HUECO_MAX_MIN:
            unidos[-1] = (unidos[-1][0], max(unidos[-1][1], fin))
        else:
            unidos.append((ini, fin))
    return unidos


def ventanas_texto(bloques):
    """-> ['9:40-13:40', '14:40-15:50']"""
    return [f"{_texto(i)}-{_texto(f)}" for i, f in unir_bloques(bloques)]


def ventanas_con_minutos(bloques):
    """-> [{'inicio': '9:40', 'fin': '13:40', 'minutos': 240}, ...]"""
    return [{'inicio': _texto(i), 'fin': _texto(f), 'minutos': f - i} for i, f in unir_bloques(bloques)]
