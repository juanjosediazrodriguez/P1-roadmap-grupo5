from django import template

register = template.Library()


@register.filter(is_safe=True)
def format_cop(value):
    """Formatea un número entero como moneda COP con separador de miles punto. """
    try:
        val_int = int(value)
    except Exception:
        return value
    s = f"{val_int:,}"
    return s.replace(",", ".")
