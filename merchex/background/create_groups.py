from django.db import migrations

def create_groups_for_existing_bets(apps, schema_editor):
    Pari = apps.get_model('your_app_name', 'Pari')
    GroupePari = apps.get_model('your_app_name', 'GroupePari')
    
    # Pour chaque pari existant sans groupe
    for pari in Pari.objects.filter(groupe__isnull=True):
        # Créer un nouveau groupe pour ce pari
        groupe = GroupePari.objects.create(
            mise=0,  # Vous devrez ajuster cela selon vos besoins
            type_pari='SIMPLE',
            cote_totale=pari.cote,
            gain_potentiel=0  # À calculer selon vos besoins
        )
        # Associer le pari au groupe
        pari.groupe = groupe
        pari.save()

def reverse_groups_creation(apps, schema_editor):
    GroupePari = apps.get_model('your_app_name', 'GroupePari')
    GroupePari.objects.all().delete()