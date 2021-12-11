from django.urls import path, reverse_lazy
from . import views
from django.conf.urls import url

app_name='brainstorm'

urlpatterns = [
    path('', views.GameListView.as_view(), name='smartgames'),
    path('rating', views.RatingView.as_view(), name = 'games_rating'),
    path('gamesarcive', views.ArchiveListView.as_view(), name = 'games_all'),
    path('playerteams', views.TeamDetailView.as_view(), name = 'personal_teams'),
    path('game/<int:pk>', views.GameDetailView.as_view(), name = 'game_detail'),
    path('joingame/<int:pk>', views.GameRegister.as_view(success_url=reverse_lazy('brainstorm:smartgames')), name='game_reg'),
    path('addroster/<int:pk>', views.AddRoster.as_view(success_url=reverse_lazy('brainstorm:smartgames')), name='add_roster'),
    path('addcontest/<int:pk>', views.AddContest.as_view(success_url=reverse_lazy('brainstorm:games_all')), name='add_contest'),
    path('gamequestions/<int:pk>', views.GameQuestions.as_view(), name='game_questions'),
    path('player/<int:pk>/confirm', views.PlayerConfirmView.as_view(success_url=reverse_lazy('brainstorm:smartgames')), name='player_confirm'),
    path('export/<int:pk>', views.export_users_xls, name='export_users_xls'),
]
