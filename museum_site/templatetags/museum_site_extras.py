from django import template

register = template.Library()


def cut(val, rep):
    return val.strip(rep)
