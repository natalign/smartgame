from django import forms
from django.forms import fields
from django.contrib.admin import widgets
from brainstorm.models import Team_Player, Team, Player, Game
from django.core.validators import MaxValueValidator, MinValueValidator

class CreateFormContest(forms.Form):
    """
    Выбор команды из списка при регистрации на игру.
    """
    team = forms.ModelChoiceField(label ='Команда', \
                                queryset=Team.objects.all(), \
                                to_field_name="name", blank = True, \
                                required = False, \
                                widget=forms.Select(attrs={'class': 'form-control'}))

class CreateFormTeam(forms.ModelForm):
    """
    Форма создания новой команды.
    """
    name = forms.CharField(label ='Название', \
                        required = False, \
                        widget=forms.TextInput(attrs={'class': 'form-control'}))
    class Meta:
        model = Team
        fields = ['name']


class CreateFormRoster(forms.Form):
    """
    Форма внесения состава игроков после игры.
    """
    playerlist = forms.ModelMultipleChoiceField(label ='Участники', \
                                                queryset=Player.objects.all(), \
                                                widget=forms.CheckboxSelectMultiple)

class CreateFormQuestions(forms.Form):
    howmany = forms.IntegerField(label = 'Сколько вопросов было?', \
                                required = False, \
                                validators=[MinValueValidator(1), MaxValueValidator(50)])


class CreateFormPlayer(forms.ModelForm):
    """
    Форма добавления нового игрока с возможностью выбора из доступных команд.
    """
    team = forms.ModelChoiceField(label ='Команда', \
                                queryset=Team.objects.all(), \
                                required = True, \
                                widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta:
        model = Player
        fields = ['name','phone','team']
        help_texts = {
            'review ': ' ',
        }

        widgets = {
            'name' :  forms.TextInput(attrs={'class': 'form-control'}), #для визуально приятных форм
            'phone' : forms.TextInput(attrs={'class': 'form-control'}),
        }

class CreateFormPlayerMin(forms.ModelForm):
    """
    Форма добавление игрока без выбора команды. Для внесения состава.
    """
    class Meta:
        model = Player
        fields = ['name','phone']

        widgets = {
            'name' :  forms.TextInput(attrs={'class': 'form-control'}),
            'phone' : forms.TextInput(attrs={'class': 'form-control'}),
        }

class UpdateFormStatus(forms.ModelForm):
    """
    Изменине статуса игрока.
    """
    class Meta:
        model = Team_Player
        fields = ['status']


class UpdateFormContest(forms.ModelForm):
    """
    Изменине списка участвующих в игре команды.
    """
    team = forms.ModelMultipleChoiceField(label ='Участники', \
                                        queryset=Team.objects.all().order_by('name'), \
                                        widget=forms.CheckboxSelectMultiple)

    class Meta:
        model = Game
        fields = ['name', 'team']


