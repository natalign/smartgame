from django.db import models
from django.core.validators import MinLengthValidator, RegexValidator, MinValueValidator
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class Player(models.Model):
    """
    Игрок.
    """
    name = models.CharField(
        "ФИО",
        max_length=200,
        blank=True,
        validators=[MinLengthValidator(2,"Имя должно быть длиннее чем 1 символ")
        ]
    )
    phone_regex = RegexValidator(regex=r'^\+?1?\d{11}$', message="Номер телефона должен быть введен в формате: '+99999999999'. ")
    phone = models.CharField("Номер телефона",validators=[phone_regex], max_length=12, blank=True) # validators should be a list
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null = True, on_delete = models.SET_NULL, blank=True)

    class Meta:
        verbose_name = 'Игрок'
        verbose_name_plural = 'Игроки'

    def __str__(self):
        return self.name


class Team(models.Model):
    """
    Команда.
    """
    name = models.CharField(
        "Название команды",
        max_length=200,
        validators=[MinLengthValidator(2,"Название должно быть длиннее чем 1 символ")]
    )
    id_site = models.IntegerField("Id для выгрузки на сайт ЧГК", null = True, blank=True, validators=[MinValueValidator(0)])

    class Meta:
        verbose_name = 'Команда'
        verbose_name_plural = 'Команды'

    def __str__(self):
        return self.name


class Game(models.Model):
    """
    Игра.
    """
    name = models.CharField(
        "Название игры",
        max_length=200,
        validators=[MinLengthValidator(2,"Название должно быть длиннее чем 1 символ")]
    )
    date_time = models.DateTimeField("дата и время", auto_now_add=False)
    location = models.CharField(
        "Место проведения",
        max_length=200,
        validators=[MinLengthValidator(2,"Место должно быть длиннее чем 1 символ")]  # TODO Сделать геодатой
    )

    class Meta:
        verbose_name = 'Игра'
        verbose_name_plural = 'Игры'

    def __str__(self):
        return f'{self.name} {self.date_time}'.format('%d.%m.%Y %H:%M')


class Roster(models.Model):
    """
    Состав команды, который участвовал в игре.
    """
    player = models.ForeignKey(Player, null=True, on_delete=models.SET_NULL)
    team = models.ForeignKey(Team, null=True, on_delete=models.SET_NULL)
    game = models.ForeignKey(Game, null=True, on_delete=models.SET_NULL)

    class Meta:
        verbose_name = 'Состав команды'
        verbose_name_plural = 'Составы команд'

    def __str__(self):
        return f'{self.player} {self.team} {self.game}'


class Contest(models.Model):
    """
    Команда, зарегистрировавшаяся на игру.
    """
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Зарегистрировавшаяся команда'
        verbose_name_plural = 'Зарегистрировавшиеся команды'

    def __str__(self):
        return f'{self.team.name} {self.game.name}'


class Team_Player(models.Model):
    """
    Состав команды, один игрок может быть в нескольких командах.
    """
    class EarnedStatus(models.TextChoices) :
        CAPITAN = 'CP', _('Капитан')
        MAINPLAYER = 'MP', _('Игрок')
        EXPLAYER = 'EP', _('Неактивный')

    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    status =  models.CharField("Статус игрока",
        max_length=2,
        choices=EarnedStatus.choices,
        default=EarnedStatus.MAINPLAYER,
    )

    class Meta:
        verbose_name = 'Команда игрока'
        verbose_name_plural = 'Команды игроков'

    def __str__(self):
        return f'{self.team.name} {self.player.name}'


class Question(models.Model):
    """
    Вопросы игры и кто ответил верно.
    """
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE)
    q_number = models.IntegerField("Номер вопроса", validators=[MinValueValidator(0)])
    correct = models.BooleanField("Вопрос взят", null=True)

    class Meta:
        verbose_name = 'Вопрос игры'
        verbose_name_plural = 'Вопросы игры'

    def __str__(self):
        return f'{self.q_number} {self.contest.team.name} {self.contest.game.name}'


class Subtotal(models.Model):
    """
    Последний вопрос тура для промежуточных результатов.
    """
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    q_last = models.IntegerField("Финал тура", validators=[MinValueValidator(1)])

    class Meta:
        verbose_name = 'Финал тура'
        verbose_name_plural = 'Финалы туров'

    def __str__(self):
        return f'{self.game.name} {self.q_last}'

