# Python 3.14 compatibility patch for Django
import django.template.context

original_copy = django.template.context.BaseContext.__copy__

def patched_copy(self):
    duplicate = self.__class__.__new__(self.__class__)
    duplicate.__dict__ = self.__dict__.copy()
    return duplicate

django.template.context.BaseContext.__copy__ = patched_copy