import random
import string

from guardian.shortcuts import assign_perm


def generate_unique_text():
    characters = string.ascii_letters + string.digits
    unique_text = "".join(random.choices(characters, k=25))

    return unique_text


def assign_perms(perms, user, obj):
    for perm in perms:
        assign_perm(perm, user, obj)
