import re
from django.db import migrations


def is_valid_user_code(user_code):
    return bool(re.fullmatch(r'\d{5}', user_code or ''))


def next_available_user_code(used_codes, start_number=1):
    for number in range(start_number, 100000):
        candidate = f'{number:05d}'
        if candidate not in used_codes:
            used_codes.add(candidate)
            return candidate

    raise ValueError('No available 5-digit user codes remain for backfill.')


def backfill_invalid_user_codes(apps, schema_editor):
    CustomUser = apps.get_model('accounts', 'CustomUser')

    used_codes = {
        user_code
        for user_code in CustomUser.objects.values_list('user_code', flat=True)
        if is_valid_user_code(user_code)
    }

    invalid_users = []
    for user in CustomUser.objects.order_by('id').only('id', 'user_code'):
        if not is_valid_user_code(user.user_code):
            invalid_users.append(user)

    for user in invalid_users:
        preferred_code = f'{user.pk:05d}' if 0 <= user.pk < 100000 else None
        if preferred_code and preferred_code not in used_codes:
            new_user_code = preferred_code
            used_codes.add(new_user_code)
        else:
            new_user_code = next_available_user_code(used_codes)

        CustomUser.objects.filter(pk=user.pk).update(user_code=new_user_code)


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_backfill_roles_and_add_role_constraint"),
    ]

    operations = [
        migrations.RunPython(backfill_invalid_user_codes, migrations.RunPython.noop),
    ]
