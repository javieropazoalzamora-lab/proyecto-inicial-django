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


def ventanas_con_minutos(bloques, clases=None):
    """-> [{'inicio': '9:40', 'fin': '13:40', 'minutos': 240, 'lugar': 'universidad'}, ...]

    'lugar' solo se informa si el día tiene clases: 'universidad' si la ventana cae entre la primera
    y la última clase; 'casa' si queda antes o después (el usuario ya está/estará en casa)."""
    span = rango_clases(clases)
    salida = []
    for i, f in unir_bloques(bloques):
        v = {'inicio': _texto(i), 'fin': _texto(f), 'minutos': f - i}
        if span:
            v['lugar'] = 'universidad' if i >= span[0] and f <= span[1] else 'casa'
        salida.append(v)
    return salida


# ---------------- módulos (grilla de la encuesta) ----------------

def _modulos():
    from .constantes import MODULOS
    return MODULOS


def modulos_cubiertos(ventanas):
    """Números de módulo que quedan completamente dentro de las ventanas dadas (['9:40-12:15', ...])."""
    unidos = unir_bloques(ventanas)
    return {n for n, ini, fin in _modulos()
            if any(a <= _minutos(ini) and _minutos(fin) <= b for a, b in unidos)}


def ventanas_desde_modulos(numeros):
    from .constantes import MODULO_TEXTO
    return ventanas_texto([MODULO_TEXTO[n] for n in sorted(set(numeros)) if n in MODULO_TEXTO])


def _enteros_validos(valores):
    validos = {n for n, _i, _f in _modulos()}
    salida = set()
    for v in valores:
        try:
            n = int(v)
        except (TypeError, ValueError):
            continue
        if n in validos:
            salida.add(n)
    return salida


def _lista(data, clave):
    if hasattr(data, 'getlist'):
        return data.getlist(clave)
    v = data.get(clave, [])
    return list(v) if isinstance(v, (list, tuple)) else [v]


def modulos_desde_post(data, dia):
    """-> (libres, clases) como conjuntos de números de módulo.

    Acepta el formato nuevo (libre_<dia>, clase_<dia>) y el antiguo (<dia> con bloques de 70 min)."""
    from .constantes import BLOQUES_VALIDOS
    libres = _enteros_validos(_lista(data, f'libre_{dia}'))
    antiguos = [b for b in _lista(data, dia) if b in BLOQUES_VALIDOS]
    libres |= modulos_cubiertos(antiguos)
    clases = _enteros_validos(_lista(data, f'clase_{dia}'))
    return libres - clases, clases  # si un módulo se marca como clase, no cuenta como libre


def rango_clases(clases):
    """(inicio, fin) en minutos de la primera a la última clase, o None si no hay clases."""
    from .constantes import MODULOS
    if not clases:
        return None
    mods = [m for m in MODULOS if m[0] in set(clases)]
    if not mods:
        return None
    return _minutos(mods[0][1]), _minutos(mods[-1][2])


def viaje_del_dia(clases, transporte_min):
    """Hora de salida y de llegada a casa a partir de las clases y el transporte (solo con ambos)."""
    span = rango_clases(clases)
    if not span:
        return None
    datos = {'primera_clase': _texto(span[0]), 'ultima_clase': _texto(span[1])}
    if transporte_min is not None:
        datos['sale_de_casa'] = _texto(max(span[0] - transporte_min, 0))
        datos['llega_a_casa'] = _texto(span[1] + transporte_min)
    return datos
