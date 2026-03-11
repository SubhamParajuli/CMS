from django.db import migrations, models


VALID_ROLES = ['admin', 'student', 'teacher']


def backfill_user_roles(apps, schema_editor):
    CustomUser = apps.get_model('accounts', 'CustomUser')

    CustomUser.objects.filter(role='', is_superuser=True).update(role='admin', is_staff=True)
    CustomUser.objects.filter(role='', is_staff=True).update(role='admin')
    CustomUser.objects.filter(role='admin').update(is_staff=True)

    remaining_invalid_roles = CustomUser.objects.exclude(role__in=VALID_ROLES)
    if remaining_invalid_roles.exists():
        invalid_users = list(remaining_invalid_roles.values_list('id', 'username', 'role'))
        raise ValueError(f'Invalid user roles remain in accounts_customuser: {invalid_users}')


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(backfill_user_roles, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name='customuser',
            constraint=models.CheckConstraint(
                check=models.Q(role__in=VALID_ROLES),
                name='accounts_customuser_valid_role',
            ),
        ),
    ]
