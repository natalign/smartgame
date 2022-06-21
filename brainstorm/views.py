from django.views import View
from django.shortcuts import render, redirect
from django.views.generic import ListView, DetailView
from brainstorm.models import Game, Contest, Team_Player, Player, Question, Team, Roster, Subtotal
from brainstorm.forms import CreateFormContest, UpdateFormContest, CreateFormTeam, CreateFormRoster, CreateFormQuestions, CreateFormPlayer, CreateFormPlayerMin, UpdateFormStatus
from datetime import datetime
from django.db.models import Max, Min
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from dateutil.relativedelta import relativedelta
from django.db import connection, transaction
from openpyxl import Workbook
import xlwt
from django.http import HttpResponse


def xls_round(ws, row_num, start_num, finish_num):
    """
    Создает нужное количество колонок в excel с указанными номерами
    (файл, номер строки, первый номер, последний номер)
    """
    font_style = xlwt.XFStyle()
    columns = ['Team ID', 'Название', 'Город', 'Тур']
    res = [x for x in range(start_num, finish_num)]
    columns = columns+res
    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)


def xls_results(ws, round, pk, start_num, finish_num, row_num):
    """
    Заполняет excel по указанным номерам.
    (файл, тур, первый номер вопроса, последний номер вопроса, номер строки)
    """
    font_style = xlwt.XFStyle()
    contests = Contest.objects.filter(game = pk)
    for tm in contests:
        team = Team.objects.get(id = tm.team.id) #получаем команду как объект, для отбора ниже
        row_num += 1
        ws.write(row_num, 0, team.id_site, font_style)
        ws.write(row_num, 1, team.name, font_style)
        ws.write(row_num, 2, 'Тюмень', font_style)
        ws.write(row_num, 3, round, font_style)
        # Выбираем вопросы текущей команды которые больше или равны первому номеру и меньше или равны последнему
        questions = Question.objects.filter(contest__team = team) \
                                    .filter(contest__game = pk) \
                                    .filter(q_number__lte = finish_num) \
                                    .filter(q_number__gte = start_num) \
                                    .order_by('q_number')
        for qs in questions:
            if qs.correct:
                # для подстраховки, что бы данные не поехали, номер колонки определяю по номеру вопроса.
                # в excel данные выводятся в три блока друг под другом.
                # поэтому из вопроса вычитаем, то количество вопросов на которое надо сдвинутся в обратную сторону
                # +4 колонки дополнительных данных
                # 1 - это верный ответ
                ws.write(row_num, qs.q_number-start_num+4, 1, font_style)

    return row_num


def export_users_xls(request, pk):
    """
    Выгрузка результатов игры в excel.
    (HttpRequest, id игры)
    """
    game = Game.objects.get(id = pk)
    response = HttpResponse(content_type='application/ms-excel') #возможно в итоге надо будет делать xmls но пока xls
    file_name = game.date_time.strftime("%d-%m-%Y")+".xls"
    response['Content-Disposition'] = 'attachment; filename="%s"' % file_name

    wb = xlwt.Workbook(encoding='utf-8')
    sheetname = game.name[:31] if len(game.name) > 31 else game.name
    sheetname = sheetname.replace(':','')
    ws = wb.add_sheet(sheetname)
    
    questions = Question.objects.filter(contest__game = pk).order_by('contest__team','q_number')
    max_q = questions.aggregate(Max('q_number')) #Сколько вопросов было на игре
    mq = max_q['q_number__max']
    #вопросов в турах поровну, делим их на три для трех блоков выгрузки.
    if mq>0:
        mq = int(mq/3)
    else:
        mq=0

    #Номера первого вопроса в блоке и последнего
    start_num=1
    finish_num = mq
    row_num = 1 #Первая строка
    # заполняем три блока выгрузки
    #TO DO переделать после того как добавлю туры.
    for i in range(1, 4):
        xls_round(ws, row_num, start_num, finish_num+1)
        row_num = xls_results(ws, str(i), pk, start_num, finish_num, row_num)
        start_num = start_num+mq
        finish_num = finish_num+mq
        row_num += 2

    wb.save(response) #сохраняем файл
    return response


class GameListView(ListView):
    """
    Главная страница.
    Список анонсированных игр, запросов на внесение составов. Распознавание новых пользователей.
    """
    model = Game
    template_name = "brainstorm/game_list.html"
    success_url = reverse_lazy('brainstorm:smartgames')

    def get(self, request):
        today = datetime.today()
        games = Game.objects.filter(date_time__gte = today).order_by('date_time') #Получаем еще непроведенные игры
        playername = ""
        if request.user.is_authenticated:
            try:
                currentplayer = Player.objects.get(user=self.request.user) #get чтобы получить единственный объект
            except Player.DoesNotExist:
                currentplayer = None
            # если пользователь не привязан к игроку, пробуем найти игрока без пользователя с его именем
            if currentplayer is None:
                username = request.user.last_name +" "+ request.user.first_name
                try:
                    results = Player.objects.filter(user__isnull=True).get(name__icontains=username)
                    playername = results.name
                    findplayer = True #если нашел игрока с такими же ФИО, но без привязанного пользователя
                except Player.DoesNotExist:
                    findplayer = False
            else:
                findplayer = False
            #CP - капитаны. Только они вносят составы.
            teams = Team_Player.objects.filter(player = currentplayer).filter(status = 'CP')
            valuelist = teams.values_list('team')
            twomonth = today - relativedelta(months=2)
            #выбираем игры в которых команда участвовала последние два месяца.
            contests = Contest.objects.filter(team__in = valuelist) \
                                    .filter(game__date_time__lte = today) \
                                    .filter(game__date_time__gte = twomonth)
            notinroster = [] #список игр по которым не внесен состав
            for earlygame in contests:
                #Проверяем внесен ли состав по игре
                if not Roster.objects.filter(team = earlygame.team).filter(game = earlygame.game).exists():
                   notinroster.append(earlygame.id)
            addroster = Contest.objects.filter(id__in = notinroster)
            ctx = {'games':games, 'addroster': addroster, 'findplayer':findplayer, 'playername':playername}
        else:
            #если не авторезирован, то он видит только список анонсированных игр
            ctx = {'games':games}
        retval = render(request, self.template_name, ctx)
        return retval

    def post(self, request):
        """
        Если нашел непривязанного игрока для этого пользователя, то мы попадает сюда.
        """
        username = request.user.last_name +" "+ request.user.first_name
        #Если подтвердил, что это он - записываем пользователя игроку.
        #Если отклонил - создаем нового игрока, что бы больше этого вопроса не возникало.
        if 'confirm' in request.POST:
            try:
                results = Player.objects.filter(user__isnull=True).get(name__icontains=username)
                results.user = request.user
                results.save()
            except Player.DoesNotExist:
                results = None
        elif 'decline' in request.POST:
            player = Player()
            player.user = request.user
            player.name = username
            player.save()
        return redirect(self.success_url)


class RatingView(DetailView):
    """
    Общий рейтинг по командам.
    """
    model = Contest
    template_name = "brainstorm/rating.html"

    def get(self, request):
        #Для рейтинга используем чистый sql запрос.
        result=_custom_sql()

        ctx = {'rating':result}
        retval = render(request, self.template_name, ctx)
        return retval


class ArchiveListView(ListView):
    """
    Общий список игр.
    """
    model = Game
    template_name = "brainstorm/game_archive.html"

    def get(self, request):
        games = Game.objects.all().order_by('-date_time')

        ctx = {'games':games}
        retval = render(request, self.template_name, ctx)
        return retval


class TeamDetailView(LoginRequiredMixin, DetailView):
    """
    Детализация по команде(командам) игрока.
    """
    model = Team_Player
    template_name = "brainstorm/team_detail.html"

    def get(self, request):
        try:
            currentplayer = Player.objects.get(user=self.request.user)
        except Player.DoesNotExist:
            currentplayer = None
        if request.user.is_superuser:
            playerteams = Team_Player.objects.all() # все команды для админа
            teams = Team.objects.order_by('name')
        else:
            # filter, а не get потому что команд может быть несколько
            playerteams = Team_Player.objects.filter(player = currentplayer).order_by('player__name')
            valuelist = playerteams.values_list('team')
            teams = Team.objects.filter(id__in = valuelist)
        teamplayers = Team_Player.objects.filter(team__in = teams).order_by('team__name', 'player__name')
        playerform=CreateFormPlayer(instance=Team_Player()) #добавление нового игрока
        #для нового игрока можно выбрать команду из доступных пользователю и любую команду если добавляет админ
        playerform.fields['team'].queryset = teams
        statusform = UpdateFormStatus(instance=Team_Player()) #изменение статусов игроков
        ctx = {'teams' : teamplayers, 'form_player': playerform, 'form_status': statusform}
        return render(request, self.template_name, ctx)


    def post(self, request, pk=None):
        try:
            currentplayer = Player.objects.get(user=self.request.user)
        except Player.DoesNotExist:
            currentplayer = None
        if request.user.is_superuser:
            playerteams = Team_Player.objects.all()
            teams = Team.objects.order_by('name')
        else:
            playerteams = Team_Player.objects.filter(player = currentplayer)
            valuelist = playerteams.values_list('team')
            teams = Team.objects.filter(id__in = valuelist)
        playerform = CreateFormPlayer(request.POST, request.FILES or None, instance=Player())
        playerform.fields['team'].queryset = teams
        # Если создается новый игрок
        if 'newplayer' in request.POST:
            if not playerform.is_valid():
                messages.error(request, "Ошибка! Проверьте обязательные поля.")
                return redirect(reverse('brainstorm:personal_teams'))
            newplayer = playerform.cleaned_data['name']
            playerteam = playerform.cleaned_data['team']
            # Проверяем не пытаются ли завести существующего игрока дважды. Он уже может быть в другой команде
            if Player.objects.filter(name = newplayer).exists():
                player = Player.objects.get(name = newplayer)
                # Если игрок существует, то проверяем что не в этой команде и приписываем его команде
                if not Team_Player.objects.filter(team = playerteam).filter(player = player).exists():
                    teamplayer = Team_Player()
                    teamplayer.player = player
                    teamplayer.team = playerteam
                    teamplayer.save()
            else:
                #Если игрока нет, то записываем его, а потом записываем его в команду
                player = playerform.save(commit=True)
                teamplayer = Team_Player()
                teamplayer.player = player
                teamplayer.team = playerteam
                teamplayer.save()
            messages.success(request, "Игрок успешно добавлен!")
        else:
            # Изменения статуса. Кроме данных изменного игрока в запросе еще csrf token, поэтому с try
            for key, value in request.POST.items():
                print(key, value)
                #Данные игрока разделены + (имя и команда)
                playerdata = (key.split("+"))
                try:
                    changeplayer = Player.objects.get(name = playerdata[0])
                    changeteam = Team.objects.get(name = playerdata[1])
                    teampl = Team_Player.objects.filter(team=changeteam).get(player=changeplayer)
                    teampl.status = value
                    teampl.save()
                except Player.DoesNotExist:
                    pass
        return redirect(reverse('brainstorm:personal_teams')) #после обоих вариантов post попадаем сюда


class GameDetailView(DetailView):
    """
    Детализация по игре.
    """
    model = Question
    template_name = "brainstorm/game_detail.html"

    def get(self, request, pk):
        currentgame = Game.objects.get(id = pk)
        questions = Question.objects.filter(contest__game = pk).order_by('contest__team','q_number')
        contests = Contest.objects.filter(game = pk)
        max_q = questions.aggregate(Max('q_number')) #сколько вопросов было на игре
        mq = max_q['q_number__max']
        if mq is None:
            listmax_q = []
        else:
            listmax_q = [i for i in range(1,mq+1)] #+1 чтобы попал последний вопрос
        fisrtround = Subtotal.objects.filter(game = pk).aggregate(Min('q_last'))
        finfirstq = fisrtround['q_last__min']
        secondround = Subtotal.objects.filter(game = pk).aggregate(Max('q_last'))
        finsecondq = secondround['q_last__max']
        finalcount=_custom_sql(pk, finfirstq, finsecondq) # данные собираем через sql запрос

        ctx = {'questions' : questions, 'contests' : contests, "game" : currentgame, "listmax_q" : listmax_q, "queryall": finalcount}
        retval = render(request, self.template_name, ctx)
        return retval


class GameRegister(LoginRequiredMixin, View):
    """
    Регистрация на игру.
    """
    model = Team
    template_name = "brainstorm/join_game.html"
    success_url = reverse_lazy('brainstorm:smartgames')

    def get(self, request, pk=None):
        try:
            currentplayer = Player.objects.get(user=self.request.user)
        except Player.DoesNotExist:
            currentplayer = None
        playerteams = Team_Player.objects.filter(player = currentplayer).filter(status = 'CP')
        valuelist = playerteams.values_list('team')
        gameform = CreateFormContest()
        gameform.fields['team'].queryset = Team.objects.filter(id__in = valuelist) #поле выбора команд из списка
        teamform = CreateFormTeam(instance=Team())
        ctx = {'form_game': gameform, 'form_team': teamform}
        return render(request, self.template_name, ctx)

    def post(self, request, pk=None):
        try:
            currentplayer = Player.objects.get(user=self.request.user)
        except Player.DoesNotExist:
            #Если игрока нет, то создаем его перед регистрацией
            username = request.user.last_name +" "+ request.user.first_name
            currentplayer = Player()
            currentplayer.name = username
            currentplayer.save()
        currentgame = Game.objects.get(id = pk) #для проверки, что команда уже не участвует
        playerteams = Team_Player.objects.filter(player = currentplayer).filter(status = 'CP')
        valuelist = playerteams.values_list('team')
        gameform = CreateFormContest(request.POST, request.FILES or None)
        gameform.fields['team'].queryset = Team.objects.filter(id__in = valuelist) #список из команд доступых игроку
        teamform = CreateFormTeam(request.POST, request.FILES or None, instance=Team())
        # Если регистрируется существующая команда
        if 'oldteam' in request.POST:
            if not gameform.is_valid():
                ctx = {'form_game': gameform, 'form_team': teamform}
                return render(request, self.template_name, ctx)
            chosenteam = gameform.cleaned_data['team']
            if Contest.objects.filter(team = chosenteam).filter(game = currentgame).exists():
                messages.error(request, "Ваша команда уже зарегистрирована!")
                ctx = {'form_game': gameform, 'form_team': teamform}
                return render(request, self.template_name, ctx)
            contest = Contest()
            contest.team = chosenteam
            contest.game = currentgame
            contest.save()
        # Если создают новую
        elif 'newteam' in request.POST:
            if not teamform.is_valid():
                ctx = {'form_game': gameform, 'form_team': teamform}
                return render(request, self.template_name, ctx)
            newteam=teamform.cleaned_data['name']
            if Team.objects.filter(name = newteam).exists():
                messages.error(request, "Такая команда уже существует!")
                ctx = {'form_game': gameform, 'form_team': teamform}
                return render(request, self.template_name, ctx)
            #Сохраняем команду, ее участие в игре и делаем игрока ее капитаном
            team = teamform.save(commit=True)
            contest = Contest()
            contest.team = team
            contest.game = currentgame
            contest.save()
            teamplayer = Team_Player()
            teamplayer.team = team
            teamplayer.player = currentplayer
            teamplayer.status = 'CP'
            teamplayer.save()
        messages.success(request, "Ваша команда зарегистрирована!")
        return redirect(self.success_url)


class AddRoster(LoginRequiredMixin, View):
    """
    Внесение составов после игры.
    """
    model = Roster
    template_name = "brainstorm/add_roster.html"
    success_url = reverse_lazy('brainstorm:smartgames')

    def get(self, request, pk):
        contest = Contest.objects.get(id = pk)
        teamplayers = Team_Player.objects.filter(team = contest.team).exclude(status = 'EP') #всегда 1 команда. Убираем игроков со статусом неактивный
        playerlist = teamplayers.values_list('player') #переводим список игроков в кортеж для фильтра
        rosterform = CreateFormRoster()
        rosterform.fields['playerlist'].queryset = Player.objects.filter(id__in = playerlist).order_by('name')
        playerform = CreateFormPlayerMin(instance=Player())
        ctx = {'form_roster' : rosterform, 'contest': contest, 'form_player': playerform}
        retval = render(request, self.template_name, ctx)
        return retval

    def post(self, request, pk=None):
        contest = Contest.objects.get(id = pk)
        teamplayers = Team_Player.objects.filter(team = contest.team).exclude(status = 'EP')
        playerlist = teamplayers.values_list('player')
        rosterform = CreateFormRoster(request.POST, request.FILES or None)
        rosterform.fields['playerlist'].queryset = Player.objects.filter(id__in = playerlist).order_by('name')
        playerform = CreateFormPlayerMin(request.POST, request.FILES or None, instance=Player())
        if 'player' in request.POST:
            if not playerform.is_valid():
                 ctx = {'form_roster' : rosterform, 'contest': contest, 'form_player': playerform}
                 return render(request, self.template_name, ctx)
                 #return redirect(reverse('brainstorm:add_roster', args=[pk]))
            newplayer = playerform.cleaned_data['name']
            if Player.objects.filter(name = newplayer).exists(): #Ищем существует ли уже в базе добавляемый игрок
                player=Player.objects.get(name = newplayer) #Берем этого существующего игрока и добавляем его в команду
                if not Team_Player.objects.filter(team = contest.team).filter(player = player).exists():
                    teamplayer = Team_Player()
                    teamplayer.player = player
                    teamplayer.team = contest.team
                    teamplayer.save()
            else:
                player = playerform.save(commit=True) # если такого игрока нет, сохраняем игрока и потом добавляем его в команду
                teamplayer = Team_Player()
                teamplayer.player = player
                teamplayer.team = contest.team
                teamplayer.save()
            ctx = {'form_roster' : rosterform, 'contest': contest,  'form_player': playerform}
            return render(request, self.template_name, ctx)
            #return redirect(reverse('brainstorm:add_roster', args=[pk]))
        elif 'roster' in request.POST:
            if not rosterform.is_valid():
                ctx = {'form_roster' : rosterform, 'contest': contest,  'form_player': playerform}
                return render(request, self.template_name, ctx)
            chosenplayers=rosterform.cleaned_data['playerlist']
            for human in chosenplayers:
                roster = Roster()
                roster.game = contest.game
                roster.team = contest.team
                roster.player = human
                roster.save()
            messages.success(request, "Состав внесен. Спасибо!")
            return redirect(self.success_url)


class AddContest(LoginRequiredMixin, View):
    """
    Добавление/изменения списка команд участников игры.
    """
    model = Contest
    template_name = "brainstorm/add_contest.html"
    success_url = reverse_lazy('brainstorm:games_all')

    def get(self, request, pk):
        game = Game.objects.get(id=pk)
        listcontest = Contest.objects.filter(game = game).values_list('team')
        querysetofinitialvalues = Team.objects.filter(id__in=listcontest) #получаем список уже зарегистрированных на игру команд
        contestform = UpdateFormContest(instance=game, initial={'team':querysetofinitialvalues}) # и накладываем их на список всех возможных команд
        teamform = CreateFormTeam(instance=Team());
        ctx = {'form_contest' : contestform, 'form_team' : teamform, 'currentgame' : game}
        return render(request, self.template_name, ctx)

    def post(self, request, pk=None):
        game = Game.objects.get(id=pk)
        contestform = UpdateFormContest(request.POST, request.FILES or None, instance=game)
        teamform = CreateFormTeam(request.POST, request.FILES or None, instance=Team())
        if not contestform.is_valid():
            ctx = {'form_contest' : contestform, 'form_team' : teamform, 'currentgame' : game}
            return render(request, self.template_name, ctx)
        game = contestform.save(commit=False)
        chosenteam = contestform.cleaned_data['team']
        #Удаляем из списка участников, все команды кроме отмечанных
        Contest.objects.filter(game=game).exclude(id__in=chosenteam).delete()
        #Добавляем участвующие команды, если записи по ним еще не было.
        if 'contestteams' in request.POST:
            for tm in chosenteam:
                contest, created = Contest.objects.get_or_create(
                    team = tm,
                    game = game,
                )
                if created:
                    contest.save()
            return redirect(self.success_url)
        elif 'newteam' in request.POST:
            ctx = {'form_contest' : contestform, 'form_team' : teamform}
            if not teamform.is_valid():
                return render(request, self.template_name, ctx)
            newteam=teamform.cleaned_data['name']
            if Team.objects.filter(name = newteam).exists():
                messages.error(request, "Такая команда уже существует!")
                return render(request, self.template_name, ctx)
            teamform.save(commit=True)
            return redirect(reverse('brainstorm:add_contest', args=[pk]))


class PlayerConfirmView(LoginRequiredMixin, View):
    model = Player
    template_name = "brainstorm/player_confirm.html"
    success_url = reverse_lazy('brainstorm:smartgames')


class GameQuestions(LoginRequiredMixin, View):
    """
    Добавление/изменения вопросов игры.
    """
    model = Contest
    template_name = "brainstorm/game_questions.html"
    success_url = reverse_lazy('brainstorm:games_all')

    def get(self, request, pk=None):
        currentgame = Game.objects.get(id = pk)
        questions = Question.objects.filter(contest__game = pk).order_by('contest__team','q_number')
        contests = Contest.objects.filter(game = pk)
        #можно указать сколько вопросов будет создано и где будут промежуточные итоги туров, по умолчанию на игре их 36 (по 12 на тур)
        questionsform = CreateFormQuestions(initial={'howmany': 36, 'firstround': 12, 'secondround': 24})
        max_q = questions.aggregate(Max('q_number'))
        mq = max_q['q_number__max']
        questionsform.fields['howmany'].initial = mq
        if mq is None:
            listmax_q = []
        else:
            listmax_q = [i for i in range(1,mq+1)] #+1 чтобы попал последний вопрос
        ctx = {'form_questions': questionsform, 'questions' : questions, 'contests' : contests, "game" : currentgame, "listmax_q" : listmax_q}
        retval = render(request, self.template_name, ctx)
        return retval
    #транзакция будет записана целиком либо вообще не. Существенно ускоряет работу
    @transaction.atomic
    def post(self, request, pk=None):
        currentgame = Game.objects.get(id = pk)
        questions = Question.objects.filter(contest__game = pk).order_by('contest__team','q_number')
        contests = Contest.objects.filter(game = pk)
        max_q = questions.aggregate(Max('q_number'))
        mq = max_q['q_number__max']
        if mq is None:
            listmax_q = []
        else:
            listmax_q = [i for i in range(1,mq+1)] #+1 чтобы попал последний вопрос
        questionsform = CreateFormQuestions(request.POST, request.FILES or None)
        if not questionsform.is_valid():
            ctx = {'form_questions': questionsform, 'questions' : questions, 'contests' : contests, "game" : currentgame, "listmax_q" : listmax_q}
            return render(request, self.template_name, ctx)
        #Записываем в базу все вопросы по командам
        if 'thismany' in request.POST:
            howmany = questionsform.cleaned_data['howmany']
            firstround = questionsform.cleaned_data['firstround']
            secondround = questionsform.cleaned_data['secondround']
            Subtotal.objects.filter(game=currentgame).delete()
            subtotal= Subtotal.objects.create(
            game = currentgame,
            q_last = firstround,
            )
            subtotal.save()
            subtotal= Subtotal.objects.create(
            game = currentgame,
            q_last = secondround,
            )
            subtotal.save()
            for cont in contests:
                for i in range (1,howmany+1):
                    question, created = Question.objects.get_or_create(
                    q_number = i,
                    contest = cont,
                    )
                    if created:
                        question.save()
        #Сохраняем ответы
        elif 'results' in request.POST:
            for quest in questions:
               answer = request.POST.get(str(quest.id), '') == 'on' #если галочка взведена, тогда отвечен
               currentquestion=Question.objects.get(id = quest.id)
               currentquestion.correct = answer
               currentquestion.save()
            messages.success(request, "Результат сохранен.")
        return redirect(reverse('brainstorm:game_questions', args=[pk]))

def dictfetchall(cursor):
    "Возвращает все поля курсора как словарь"
    desc = cursor.description
    return [
            dict(zip([col[0] for col in desc], row))
            for row in cursor.fetchall()
    ]



def _custom_sql(pk=None, firstround=0, secondround=0):
    """
    Получаем количество взятых вопросов, вопросы которые взяла только 1 команда, и сумму рейтинга вопросов.
    """
    with connection.cursor() as cursor:
        cursor.execute('DROP TABLE IF EXISTS q_temp')
        cursor.execute('DROP TABLE IF EXISTS q_coffins')
        cursor.execute('DROP TABLE IF EXISTS q_rating')
        cursor.execute('DROP TABLE IF EXISTS q_firstround')
        cursor.execute('DROP TABLE IF EXISTS q_secondround')
        cursor.execute('DROP TABLE IF EXISTS q_thirdround')
        cursor.execute('''CREATE TEMP TABLE q_temp (
                team_id INTEGER,
                game_id INTEGER,
                q_number INTEGER,
                correct INTEGER
        )''')
        cursor.execute('''CREATE TEMP TABLE q_coffins (
                game_id INTEGER,
                q_number INTEGER,
                q_saved INTEGER
        )''')
        cursor.execute('''CREATE TEMP TABLE q_rating (
                game_id INTEGER,
                q_number INTEGER,
                rating INTEGER
        )''')
        cursor.execute('''CREATE TEMP TABLE q_firstround (
                team_id INTEGER,
                game_id INTEGER,
                q_number INTEGER,
                correct INTEGER
        )''')
        cursor.execute('''CREATE TEMP TABLE q_secondround (
                team_id INTEGER,
                game_id INTEGER,
                q_number INTEGER,
                correct INTEGER
        )''')
        cursor.execute('''CREATE TEMP TABLE q_thirdround (
                team_id INTEGER,
                game_id INTEGER,
                q_number INTEGER,
                correct INTEGER
        )''')
        if pk is None:
            cursor.execute('''INSERT INTO q_temp
                SELECT
                    c.team_id,
                    c.game_id,
                    q.q_number,
                    q.correct
                FROM
                    brainstorm_contest c
                    INNER JOIN brainstorm_question q
                    ON c.id = q.contest_id''')
        else:
            cursor.execute('''INSERT INTO q_temp
                SELECT
                    c.team_id,
                    c.game_id,
                    q.q_number,
                    q.correct
                FROM
                    brainstorm_contest c
                    INNER JOIN brainstorm_question q
                    ON c.id = q.contest_id
                WHERE
                    c.game_id = %s''',[pk])
        cursor.execute('''INSERT INTO q_coffins
                SELECT
                    qti.game_id,
                    qti.q_number,
                    1 as q_saved
                FROM
                    q_temp qti
                WHERE
                    qti.correct = 1
                GROUP BY
                    qti.game_id,
                    qti.q_number
                HAVING
                    COUNT(qti.team_id) = 1''')
        cursor.execute('''INSERT INTO q_rating
                SELECT
                    qt.game_id,
                    qt.q_number,
                    COUNT(qt.correct) as rating
                FROM
                    q_temp qt
                WHERE
                    qt.correct = 0
                GROUP BY
                    qt.game_id,
                    qt.q_number''')
        cursor.execute('''INSERT INTO q_firstround
                SELECT
                    qf.team_id,
                    qf.game_id,
                    qf.q_number,
                    qf.correct
                FROM
                    q_temp qf
                WHERE
                    qf.q_number <= %s
                GROUP BY
                    qf.team_id,
                    qf.game_id,
                    qf.q_number''', [firstround])
        cursor.execute('''INSERT INTO q_secondround
                SELECT
                    qs.team_id,
                    qs.game_id,
                    qs.q_number,
                    qs.correct
                FROM
                    q_temp qs
                WHERE
                    qs.q_number > %s
                    AND qs.q_number <= %s
                GROUP BY
                    qs.team_id,
                    qs.game_id,
                    qs.q_number''', [firstround, secondround])
        cursor.execute('''INSERT INTO q_thirdround
                SELECT
                    qth.team_id,
                    qth.game_id,
                    qth.q_number,
                    qth.correct
                FROM
                    q_temp qth
                WHERE
                    qth.q_number > %s
                GROUP BY
                    qth.team_id,
                    qth.game_id,
                    qth.q_number''', [secondround])

        cursor.execute('''SELECT
                    qt.team_id,
                    qt.game_id,
                    t.name,
                    sum(ifnull(qt.correct, 0)) as score,
                    sum(ifnull(qc.q_saved, 0)) as coffins_saved,
                    sum(ifnull(qr.rating, 0)) as rating,
                    count(DISTINCT qt.game_id) as game_played,
                    sum(ifnull(qf.correct, 0)) as firstscore,
                    sum(ifnull(qs.correct, 0)) as secondscore,
                    sum(ifnull(qth.correct, 0)) as thirdscore
                FROM
                    q_temp AS qt
                        LEFT JOIN q_coffins AS qc
                        ON qt.q_number = qc.q_number
                            AND qt.correct = 1
                            AND qt.game_id = qc.game_id
                        LEFT JOIN q_rating AS qr
                            ON qt.q_number = qr.q_number
                                AND qt.correct = 1
                                AND qt.game_id = qr.game_id
                        LEFT JOIN brainstorm_team AS t
                            ON qt.team_id = t.id
                        LEFT JOIN q_firstround AS qf
                            ON qt.q_number = qf.q_number
                                AND qt.game_id = qf.game_id
                                AND qt.team_id = qf.team_id
                        LEFT JOIN q_secondround AS qs
                            ON qt.q_number = qs.q_number
                                AND qt.game_id = qs.game_id
                                AND qt.team_id = qs.team_id
                        LEFT JOIN q_thirdround AS qth
                            ON qt.q_number = qth.q_number
                                AND qt.game_id = qth.game_id
                                AND qt.team_id = qth.team_id
                GROUP BY
                    qt.team_id
                ORDER BY
                    sum(qt.correct) DESC,
                    sum(ifnull(qc.q_saved, 0)) DESC,
                    sum(ifnull(qr.rating, 0)) DESC''')
        querys = dictfetchall(cursor)
    return querys
