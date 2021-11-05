from django.contrib import admin
from brainstorm.models import Player, Team, Game, Roster, Contest, Team_Player, Question

admin.site.register(Player)
admin.site.register(Team)
admin.site.register(Game)
admin.site.register(Roster)
admin.site.register(Contest)
admin.site.register(Team_Player)
admin.site.register(Question)

# Register your models here.
