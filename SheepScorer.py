from tkinter import *
from tkinter import filedialog, messagebox, ttk
import xml.etree.ElementTree as ET
from enum import Enum
import re
import sys
import math


def quit():
    sys.exit()


class EdPlayer:

    def __init__(self, *args):
        new_player_original_position: int = -1
        if len(args) == 0:
            self.Name = ""
            self.Answers = []
            self.OriginalPosition = new_player_original_position
            self.StartScore = 0
            self.NeedsRegrouping = FALSE
        elif len(args) == 1:
            newname = args[0]
            new_answers = []
            self.Name = newname
            self.Answers = new_answers
            self.StartScore = 0
            self.NeedsRegroupIng = FALSE
            self.OriginalPosition = -1
        elif len(args) == 2:
            newname = args[0]
            new_answers = args[1]
            self.Name = newname
            self.Answers = new_answers
            self.StartScore = 0
            self.NeedsRegroupIng = FALSE
            self.OriginalPosition = -1
        elif len(args) == 3:
            newname = args[0]
            new_answers = args[1]
            start_score = args[2]
            self.Name = newname
            self.Answers = new_answers
            self.StartScore = start_score
            self.NeedsRegroupIng = FALSE
            self.OriginalPosition = -1
        elif len(args) == 4:
            newname = args[0]
            new_answers = args[1]
            start_score = args[2]
            orig_pos = args[3]
            self.Name = newname
            self.Answers = new_answers
            self.StartScore = start_score
            self.NeedsRegroupIng = FALSE
            self.OriginalPosition = orig_pos


class ShGame:
    class ShQuestion:
        def __init__(self, ref_game, new_text):
            self.Text = new_text
            self.Groups = []
            self._Game = ref_game

        def __str__(self):
            return f'Question: {self.Text} Groups: {self.Groups} ref_game: {self._Game}'

        @property
        def game_index(self):
            return self._Game.Questions.index(self)

        @property
        def Game(self):
            return self._Game

        def StartNewGroup(self, new_text):
            newGrp = ShGame.ShGroup(self, new_text)
            self.Groups.append(newGrp)
            return newGrp

        def SyncGroups(self):
            self.Groups = [shg for shg in self.Groups if shg.Answers]

        def GetAllAnswers(self):
            all_answers = []
            for grp in self.Groups:
                all_answers.extend(grp.Answers)
            return all_answers

        # returns list of scores for this question
        # SCORING METHODS
        # Sheep:    each player gets total answers in his group as his score
        # Peehs1:   incorrects = 1.5 * highest correct score
        # Peehs2:   incorrects = highest correct score + 0.5 * number of distinct
        #          correct answers
        # Heep:     highest score gets 0, 2nd highest get doubled
        # Kangaroo: must be incorrect; correct answers get 0

        def scores(self, include_bonus):
            cur_score = {}
            for plr in self._Game.Players:
                cur_score[plr] = 0
            if len(self._Game.Players) == 0 or len(self._Game.Questions) == 0:
                return cur_score
            highest_score = 0
            second_highest_score = 0
            num_distinct_correct = 0
            for grp in self.Groups:
                for ans in grp.Answers:
                    if ans.Player not in cur_score:
                        continue
                    cur_score[ans.Player] = len(grp.Answers)

                # for peehs/heep
                if grp.Correct:
                    num_distinct_correct += 1
                    if len(grp.Answers) > highest_score:
                        second_highest_score = highest_score
                        highest_score = len(grp.Answers)
                    elif len(grp.Answers) > highest_score and len(grp.Answers) < highest_score:
                        second_highest_score = len(grp.Answers)

            # apply special scores depending on scoring method
            for grp in self.Groups:
                for ans in grp.Answers:
                    if ans.Player not in cur_score:
                        continue
                    if self._Game.Method == sg.ShMethod.Sheep:
                        if not grp.Correct:
                            cur_score[ans.Player] = 0
                        # incorrect means invalid for sheep
                    elif self._Game.Method == sg.ShMethod.PeehsDM:
                        # incorrect -> 1.5*sheep
                        if not grp.Correct:
                            cur_score[ans.Player] = 1.5 * highest_score
                    elif self._Game.Method == sg.ShMethod.PeehsFB:
                        # incorrect -> sheep + 0.5*distinct
                        if not grp.Correct:
                            cur_score[ans.Player] = highest_score + 0.5 * num_distinct_correct
                    elif self._Game.Method == sg.ShMethod.PeehsHybrid:
                        # incorrect -> sheep + 0.5*distinct
                        if not grp.Correct:
                            cur_score[ans.Player] = 1.25 * highest_score + 0.25 * num_distinct_correct
                    elif self._Game.Method == sg.ShMethod.Heep or self._Game.Method == sg.ShMethod.Heep15 or self._Game.Method == sg.ShMethod.Heep2:
                        if cur_score[ans.Player] == highest_score or not grp.Correct:
                            cur_score[ans.Player] = 0
                        elif cur_score[ans.Player] == second_highest_score:
                            if self._Game.Method == sg.ShMethod.Heep15:
                                cur_score[ans.Player] *= 1.5
                            elif self._Game.Method == sg.ShMethod.Heep2:
                                cur_score[ans.Player] *= 2
                    elif self._Game.Method == sg.ShMethod.Kangaroo:
                        if grp.Correct:
                            cur_score[ans.Player] = 0
                    elif self._Game.Method == sg.ShMethod.Manual:
                        cur_score[ans.Player] = 0
                    # apply rounding
                    if self._Game.Rounding == sg.ShRoundingType.Up:
                        cur_score[ans.Player] = math.ceil(cur_score[ans.Player])
                    elif self._Game.Rounding == sg.ShRoundingType.Down:
                        cur_score[ans.Player] = math.floor(cur_score[ans.Player])
                    elif self._Game.Rounding == sg.ShRoundingType.Nearest:
                        cur_score[ans.Player] = round(cur_score[ans.Player])

                    # apply player & group bonuses
                    if include_bonus:
                        temp_score = cur_score[ans.Player]
                        if grp.BonusType == sg.ShBonusType.Override:
                            temp_score = grp.GroupBonus
                        elif grp.BonusType == sg.ShBonusType.Add:
                            temp_score += grp.GroupBonus
                        if ans.BonusType == sg.ShBonusType.Override:
                            temp_score = ans.AnswerBonus
                        elif ans.BonusType == sg.ShBonusType.Add:
                            temp_score += ans.AnswerBonus
                        cur_score[ans.Player] = temp_score
            return cur_score

        # returns a dictionary of total scores after this question
        def score_up_to(self, include_bonus):

            cur_score = {}
            next_score = {}

            for plr in self._Game.Players:
                cur_score[plr] = 0

            for x, que in enumerate(self._Game.Questions):

                if que.game_index <= self.game_index:
                    next_score = que.scores(include_bonus)

                    for k, v in next_score.items():
                        if k in cur_score:
                            cur_score[k] += v

            return cur_score

    # Generate post for score totals up to and including this question

    class ShPlayer:
        counter = 0

        def __init__(self, ref_game, player_name, start_score=0):
            self._Game = ref_game
            self.Name = player_name
            self.Answers = []
            self.StartScore = start_score
            ShGame.ShPlayer.counter += 1

        def __str__(self):
            return f'Player: {self.Name} Answers: {self.Answers} StartScore: {self.StartScore}'

        @property
        def Count(self):
            return self.counter

        @property
        def game_index(self):
            return self._Game.Players.index(self)

        @property
        def Game(self):
            return self._Game

        def __del__(self):
            for ans in self.Answers:
                self.counter -= 1
                ans.Group.Answers.remove(ans)

    class ShGroup:
        def __init__(self, ref_question, new_text):
            self.Text = new_text
            self.Correct = True
            self.GroupBonus = 0
            self.BonusType = sg.ShBonusType.NONE
            self.Answers = []
            self._Question = ref_question  # reference to question
            # constructor
            # declares with an empty list for Answers
            # self.Answers = [ShAnswer() for _ in range(len(ref_question.Game.Players))]
            # self.Answers = [ShGame.ShAnswer(len(ref_question.Game.Players)) for _ in range(len(ref_question.Game.Players))]

        def __str__(self):
            return f'Group.Text: {self.Text} ref_question: {self._Question} Answers: {self.Answers}'

        @property
        def Question(self):
            return self._Question

        # moves all answers to ref_group and deletes itself
        def MergeToGroup(self, ref_group):
            if ref_group == self:
                # throw new Exception("Trying to merge a group to itself")
                return
            while len(self.Answers) != 0:
                self.Answers[0].ChangeGroup(ref_group)
            try:
                self._Question.Groups.remove(self)
            except:
                pass
        def GetScore(self, include_bonus):
            if len(self.Answers) == 0:
                return 0
            else:
                try:
                    baseScore = self._Question.scores(False)[self.Answers[0].Player]
                    if include_bonus:
                        if self.BonusType == sg.ShBonusType.Override:
                            return self.GroupBonus
                        elif self.BonusType == sg.ShBonusType.Add:
                            return self.GroupBonus + baseScore
                        else:
                            return baseScore
                    else:
                        return baseScore
                except:
                    return 0



        def __del__(self):
            for ans in self.Answers:
                try:
                    ans.Player.Answers.remove(ans)
                except:
                    pass
    class ShAnswer:
        def __init__(self, ref_group, ref_player, new_text):
            self.Text = new_text
            self.AnswerBonus = 0
            self.BonusType = None
            self._Group = ref_group
            self._Player = ref_player

        def __str__(self):
            return f'Answer.Text:{self.Text} ref_group: {self._Group} ref_player: {self._Player}'

        @property
        def Group(self):
            return self._Group

        @property
        def Player(self):
            return self._Player

        def ChangeGroup(self, ref_group):
            if ref_group == self._Group:
                return
            if self._Group.Question != ref_group.Question:
                raise Exception("Moving an answer to a group in a different question.")
            oldGroup = self._Group
            self._Group = ref_group
            ref_group.Answers.append(self)
            try:
                oldGroup.Answers.remove(self)
            except:
                pass
            if len(oldGroup.Answers) == 0:
                oldGroup.Question.Groups.remove(oldGroup)

        def StartNewGroup(self):
            oldGroup = self._Group
            newGroup = ShGame.ShGroup(self._Group.Question, self.Text)
            oldGroup.Question.Groups.append(newGroup)
            self._Group = newGroup
            newGroup.Answers.append(self)
            oldGroup.Answers.remove(self)
            if len(oldGroup.Answers) == 0:
                oldGroup.Question.Groups.remove(oldGroup)

    class ShMethod(Enum):
        Sheep = 1
        PeehsDM = 2
        PeehsFB = 3
        PeehsHybrid = 4
        Heep = 5
        Heep15 = 6
        Heep2 = 7
        Kangaroo = 8
        Manual = 9

    class ShBonusType(Enum):
        NONE = 0
        Add = 1
        Override = 2

    class ShRoundingType(Enum):
        NONE = 0
        Up = 1
        Down = 2
        Nearest = 3

    def __init__(self, *args):
        if len(args) == 0:
            self.Questions = []
            self.Players = []
            self.Method = self.ShMethod.Sheep
            self.Rounding = self.ShRoundingType.NONE
        elif len(args) == 3:
            new_questions = args[0]
            new_players = args[1]
            new_answers = args[2]
            if len(new_answers) != len(new_questions) or len(new_answers[0]) != len(new_players):
                raise Exception("Answer list must be size [num questions, num players]")
            self.Questions = [sg.ShQuestion(self, txt) for txt in new_questions]
            self.Players = [sg.ShPlayer(self, txt) for txt in new_players]
            for iques in range(len(new_questions)):
                for iplayer in range(len(new_players)):
                    new_group = sg.ShGroup(self.Questions[iques], new_answers[iques][iplayer])
                    self.Questions[iques].Groups.append(new_group)
                    new_answer = sg.ShAnswer(new_group, self.Players[iplayer], new_answers[iques][iplayer])
                    new_group.Answers.append(new_answer)
                    self.Players[iplayer].Answers.append(new_answer)

    def __str__(self):
        return 'ShGame'

    # attempts to guess groupings for ans
    def guess_group(self, ans):
        # red
        anstxt = re.sub(r'\W', '', ans.Text.lower())
        for grp in ans.Group.Question.Groups:
            if grp == ans.Group:
                continue
            if re.sub(r'\W', '', grp.Text.lower()) == anstxt:
                ans.ChangeGroup(grp)
                return
        # didn't find any but let's try individual answers
        for grp in ans.Group.Question.Groups:
            if grp == ans.Group:
                continue
            for ans2 in grp.Answers:
                if re.sub(r'\W', '', ans2.Text.lower()) == anstxt:
                    ans.ChangeGroup(grp)
                    return

    def get_correct_text(self, method, correct):
        if method == sg.ShMethod.Sheep or method == sg.ShMethod.Heep or method == sg.ShMethod.Heep15 or method == sg.ShMethod.Heep2 or method == sg.ShMethod.Manual:
            return "Valid" if correct else "Invalid"
        else:
            return "Correct" if correct else "Incorrect"

    def is_score_descending(method):
        if method == sg.ShMethod.PeehsDM or method == sg.ShMethod.PeehsFB or method == sg.ShMethod.PeehsHybrid:
            return False
        else:
            return True

    def loadReveal(self):

        global myLabel2, Roundtype
        filename = ""
        #filename = "C:/Users/keith/Desktop/sheep/test.sheep17"
        filename = filedialog.askopenfilename(title="Load Sheep Scoring File",filetypes=[("Sheep Score 2017 File", "*.sheep17")])
        if filename == "": return
        resetProgram()
        tree = ET.parse(filename)
        root = tree.getroot()
        if root.tag == "SheepScore2012Game":
            list = []
            for child in root:  # sanity check file need unique player names
                if child.tag == "Player":
                    list.append(child.text)
                    if len(list) != len(set(list)):
                        messagebox.showinfo(title="File Load error",
                                            message="Duplicate name found in player list. All players require a unique player name, please fix the game file manually.")
                        return -1
            for child in root:
                if child.tag == "ScoringMethod":
                    self.Method = self.ShMethod[child.text]
                    # Gametype.set(gt[child.text])
                elif child.tag == "Rounding":
                    if child.text == "None":
                        child.text = "NONE"
                    self.Rounding = self.ShRoundingType[child.text]
                    # Roundtype.set(rt[child.text])
                elif child.tag == "Question":
                    qindex = int(child.attrib['GameIndex'])
                    while len(self.Questions) < qindex + 1:
                        self.Questions.append(self.ShQuestion(self, "(blank)"))
                    self.Questions[qindex].Text = child.text
                elif child.tag == "Player":
                    pindex = int(child.attrib['GameIndex'])
                    start_score = child.attrib['StartScore']
                    while len(self.Players) < pindex + 1:
                        self.Players.append(self.ShPlayer(self, "(blank)", start_score))
                    self.Players[pindex].Name = child.text.strip()
                elif child.tag == "Group":
                    group_q_index = int(child.attrib['QuestionIndex'])
                    tempcorrect = child.attrib['Correct']
                    tempgroupbonus = child.attrib['GroupBonus']
                    tempgroupbonustype = child.attrib['BonusType']
                    if tempgroupbonustype=="None": tempgroupbonustype="NONE"
                    newGroup = self.ShGroup(self.Questions[group_q_index], "")
                    newGroup.Correct = tempcorrect
                    newGroup.GroupBonus = tempgroupbonus
                    newGroup.BonusType = self.ShBonusType[tempgroupbonustype]
                    self.Questions[group_q_index].Groups.append(newGroup)
                    for item in child:
                        if item.tag == "Text":
                            newGroup.Text = item.text
                        elif item.tag == "Answer":

                            ans_p_index = int(item.attrib['PlayerIndex'])
                            tempansbonus = int(item.attrib["AnswerBonus"])
                            tempansbonustype = item.attrib['BonusType']
                            if tempansbonustype == "None": tempansbonustype = "NONE"
                            anstext = item.text
                            newAns = ShGame.ShAnswer(newGroup, self.Players[ans_p_index], anstext)
                            newAns.AnswerBonus = tempansbonus
                            newAns.BonusType = self.ShBonusType[tempansbonustype]
                            newGroup.Answers.append(newAns)

            if len(self.Questions) >= curQ:
                myLabel2.grid_forget()
                myLabel2 = Label(window, text=self.Questions[curQ - 1].Text)
                myLabel2.grid(row=0, column=5)
            else:
                qdown()
            updateTreeview()
        else:
            messagebox.showinfo(title="File load error", message="This is not a recognized sheep file!")

    def saveReveal(self):
        filename = filedialog.asksaveasfilename(title="Save Sheep Scoring File",
                                                filetypes=[("Sheep Score 2017 File", "*.sheep17")])
        sheep_score_game = ET.Element('SheepScore2012Game')
        scoring_method = ET.SubElement(sheep_score_game, "ScoringMethod")
        scoring_method.text = str(self.Method.name)
        rounding = ET.SubElement(sheep_score_game, "Rounding")
        rounding.text = str(self.Rounding.name)
        for que in self.Questions:
            question = ET.SubElement(sheep_score_game, "Question")
            question.set("GameIndex", str(que.game_index))
            question.text = que.Text
        for plr in self.Players:
            player = ET.SubElement(sheep_score_game, "Player")
            player.set("GameIndex", str(plr.game_index))
            player.set("StartScore", str(plr.StartScore))
            player.text = plr.Name
        for que in self.Questions:
            for grp in que.Groups:
                group = ET.SubElement(sheep_score_game, "Group")
                group.set("QuestionIndex", str(que.game_index))
                group.set("GroupBonus", str(grp.GroupBonus))
                group.set("BonusType", str(grp.BonusType))
                group.set("Correct", str(grp.Correct))
                group2 = ET.SubElement(group, "Text")
                group2.text = grp.Text
                for ans in grp.Answers:
                    answer = ET.SubElement(group, "Answer")
                    answer.set("AnswerBonus", str(ans.AnswerBonus))
                    answer.set("BonusType", str(ans.BonusType))
                    answer.set("PlayerIndex", str(ans.Player.game_index))
                    answer.text = ans.Text
        tree = ET.ElementTree(sheep_score_game)
        ET.indent(tree, '  ')
        tree.write(filename, encoding='utf-8', xml_declaration=True)


def qset(event):
    global curQ
    var = StringVar
    var = myTextbox1.get()
    if int(var) > 0:
        curQ = int(var) - 1
        qup()
    else:
        curQ = 2
        qdown()


def qdown():
    global curQ
    global myLabel2
    if curQ > len(sg.Questions): curQ = len(sg.Questions)
    if curQ > 1:
        curQ = curQ - 1
    myTextbox1.delete(0, END)
    myTextbox1.insert(INSERT, curQ)
    myTextbox1.grid_forget()
    myTextbox1.grid(row=0, column=2)
    if curQ == 0: return
    if len(sg.Questions) >= curQ:
        myLabel2.grid_forget()
        myLabel2 = Label(window, text=sg.Questions[curQ - 1].Text)
        myLabel2.grid(row=0, column=5)
    updateTreeview()


def qup():
    global curQ
    global myLabel2
    if curQ > len(sg.Questions): curQ = len(sg.Questions)
    if curQ < len(sg.Questions):
        curQ = curQ + 1
    myTextbox1.delete(0, END)
    myTextbox1.insert(INSERT, curQ)
    myTextbox1.grid_forget()
    myTextbox1.grid(row=0, column=2)
    if curQ == 0: return
    if len(sg.Questions) >= curQ:
        myLabel2.grid_forget()
        myLabel2 = Label(window, text=sg.Questions[curQ - 1].Text)
        myLabel2.grid(row=0, column=5)
    updateTreeview()


def resetProgram():
    global myTextbox1, myLabel2, players, curQ, current_var, curP
    sg.Questions = []
    sg.Players = []
    sg.Groups = []
    players = []
    curQ = 1
    curP = 0
    current_var.set("")
    myTextbox1.delete(0, END)
    myTextbox1.insert(INSERT, curQ)
    myTextbox1.grid_forget()
    myTextbox1.grid(row=0, column=2)
    myLabel2.grid_forget()
    myCheckbox1.grid(row=0, column=4)
    myLabel2 = Label(window, text="Click Sheep > Edit Questions... to begin.")
    myLabel2.grid(row=0, column=5)
    updateTreeview()
    return


def edAL(edAText, combo):
    global players, curP
    players = []
    existing_players = []
    answers = []
    for x in players: existing_players.append(x.Name)
    file1 = open(
        filedialog.askopenfilename(title="Load Players and Answers from File", filetypes=[("txt files", "*.txt")]), 'r',
        encoding="utf8")
    found = 0
    next_player = 0
    name = ""
    for line in file1:
        line = line.strip()
        if found == 0 and line[0:6] == "From: ":
            found = 1
            name = line[6:]
        if found == 2 and line == "------------------------------------------------------------------------":
            found = 0
            next_player = 1
        if found == 2:
            answers.append(line)
        if found == 1 and line == "------------------------------------------------------------------------":
            found = 2
        if next_player == 1:
            if name not in existing_players:
                player = EdPlayer(name)
                existing_players.append(name)
                index = 0  # question 0
                for ans in answers:
                    player.Answers.append(ans)
                answers = []
                players.append(player)
                next_player = 0
            else:
                print(name + "exists in " + str(existing_players))
                print("Duplicate Player " + name)
                answers = []
                print("dumped duplicate")
                next_player = 0
    players = sorted(players, key=lambda w: w.Name.lower())
    combo['values'] = [item.Name for item in players]
    combo.current(curP)
    PAnswers = []
    answers = ""
    for x in players[curP].Answers: PAnswers.append(x)
    for item in PAnswers: answers = answers + item + "\n"
    edAText.delete(1.0, END)
    edAText.insert(INSERT, answers)
    edAText.grid(column=0, columnspan=3, rowspan=10, padx=5, pady=5)
    return (edAText)


def edQL(edQText):
    # file1 = open("C:/Users/keith/Desktop/sheep/questions.txt", 'r')
    file1=""
    file1 = open(filedialog.askopenfilename(title="Load Questions from File", filetypes=[("txt files", "*.txt")]), 'r')
    if file1 == "": return
    strvar = file1.read()
    edQText.delete(1.0, END)
    edQText.insert(INSERT, strvar)
    return (edQText)


def edSave(edQW, edQText):
    global myLabel2, curQ
    questions = edQText.get("1.0", END).splitlines()
    for index, item in enumerate(questions):
        while index == len(sg.Questions):
            sg.Questions.append(ShGame.ShQuestion(sg, item))
        sg.Questions[index].Text = item
    while sg.Questions[len(sg.Questions) - 1].Text.strip() == "":
        sg.Questions.pop(len(sg.Questions) - 1)
        print("question popped")
    window.deiconify()
    if curQ == 0: curQ = 1
    if curQ > len(sg.Questions): curQ = len(sg.Questions)
    myTextbox1.delete(0, END)
    myTextbox1.insert(INSERT, curQ)
    myTextbox1.grid_forget()
    myTextbox1.grid(row=0, column=2)
    if len(sg.Questions) >= curQ:
        myLabel2.grid_forget()
        myLabel2 = Label(window, text=sg.Questions[curQ - 1].Text)
        myLabel2.grid(row=0, column=5)
    edQW.destroy()


def edPSave(edAW, edAText, combo):
    global players, score, myPlayers, curP
    if len(players) == 0:
        sg.Players = []
        for x in range(len(sg.Questions)):
            sg.Questions[x].Groups = []
    if len(players) > 0:
        combo.event_generate('<<ComboboxSelected>>')  # store values of currently selected player
        who = players[curP].Name
        players = sorted(players, key=lambda w: w.Name.lower())
        sg.Players = sorted(sg.Players, key=lambda w: w.Name.lower())
        index = 0
        for x in players:
            if x.Name == who:
                break
            index += 1
        curP = index
        dbplayernames = []  # sg name
        if len(sg.Players) > 0:
            for player in sg.Players:
                dbplayernames.append(player.Name)
        playernames = []  # ed names
        for player in players: playernames.append(player.Name)
        todeleteplayers = list(set(dbplayernames) - set(playernames))
        newplayers = []
        for player in players:  # add the name missing from playernames
            if player.Name not in dbplayernames:
                sg.Players.append(ShGame.ShPlayer(sg, player.Name, player.StartScore))
                newplayers.append(player.Name)
        for z in todeleteplayers:  # Lets delete deleted players.
            for x, player in enumerate(sg.Players):
                if player.Name in todeleteplayers:
                    sg.Players.pop(x)
            for x, player in enumerate(players):
                if player.Name in todeleteplayers:
                    players.pop(x)
        for ply in todeleteplayers:
            for q, Qs in enumerate(sg.Questions):
                for g, Gs in enumerate(Qs.Groups):
                    for a, As in enumerate(Gs.Answers):
                        if As.Player.Name == ply:
                            sg.Questions[q].Groups[g].Answers.pop(a)
                        if len(sg.Questions[q].Groups[g].Answers) == 0:
                            sg.Questions[q].Groups.pop(g)
        # lists should be the same
        players = sorted(players, key=lambda w: w.Name.lower())
        sg.Players = sorted(sg.Players, key=lambda w: w.Name.lower())
        dbplayernames = []
        playernames = []

        for player in sg.Players: dbplayernames.append(player.Name)
        for player in players: playernames.append(player.Name)
        for pnum, player in enumerate(players):
            sg.Players[pnum].StartScore = players[pnum].StartScore
            for qnum, anstxt in enumerate(player.Answers):
                while qnum == len(sg.Questions):
                    sg.Questions.append(ShGame.ShQuestion(sg, ""))
                if player.Name in newplayers:
                    newgroup = ShGame.ShGroup(sg.Questions[qnum], anstxt)
                    sg.Players[pnum].Answers.append(ShGame.ShAnswer(newgroup, sg.Players[pnum], anstxt))
                for g, grp in enumerate(sg.Questions[qnum].Groups):
                    if anstxt.lower == grp.Text.lower():
                        for a, ans in enumerate(grp.Answers):
                            if ans.Player.Name == player.Name:
                                if ans.Text.lower != anstxt.lower:
                                    sg.Questions[qnum].Group[g].Answers.pop(ans)  # del ans
                                    if len(grp.Answers) == 0:
                                        sg.Questions[qnum].Group.pop(g)  # del grp
                                    newgroup = ShGame.ShGroup(sg.Questions[qnum], anstxt)
                                    sg.Players[pnum].Answers.append(ShGame.ShAnswer(newgroup, sg.Players[pnum], anstxt))
        # Moving Answers from Players into groups.
        for x, player in enumerate(sg.Players):
            for i, ans in enumerate(player.Answers):
                present_groups = []
                for m in ans.Group.Question.Groups:
                    present_groups.append(m.Text.lower())
                if ans.Text.lower() not in present_groups:
                    ans.Group.Question.Groups.append(ShGame.ShGroup(ans.Group.Question, ans.Text))
                    present_groups.append(ans.Text.lower())
                ans.Group.Question.Groups[present_groups.index(ans.Text.lower())].Answers.append(ans)
        for x, player in enumerate(sg.Players):
            for i, ans in enumerate(player.Answers):
                sg.Players[x].Answers.pop(i)
    updateTreeview()
    window.deiconify()
    edAW.destroy()


def edPCancel(parent, child):
    parent.deiconify()
    child.destroy()


def edCancel(child):
    window.deiconify()
    child.destroy()


def edPOK(edAText, combo, edAW, newPW, newplayer, x=''):
    global players, score, curP
    if newplayer != "":
        names = []
        for x in players: names.append(x.Name)
        if newplayer not in names and newplayer != '':
            players.append(EdPlayer(newplayer.strip(), [], 0, -1))
        players = sorted(players, key=lambda w: w.Name.lower())
        index = 0
        for x in players:
            if x.Name == newplayer:
                break
            index += 1
        curP = index
        combo['values'] = [item.Name for item in players]
        if curP > len(players) - 1: curP = len(players)
        combo.current(curP)
        PAnswers = []
        answers = ""
        for x in players[curP].Answers: PAnswers.append(x)
        for item in PAnswers: answers = answers + item + "\n"
        edAText.delete(1.0, END)
        edAText.insert(INSERT, answers)
        edAText.grid(column=0, columnspan=3, rowspan=10, padx=5, pady=5)
    edAW.deiconify()
    newPW.destroy()


def edROK(edAText, combo, edAW, newPW, newplayer, x=''):
    global players, score, curP
    names = []
    for x in players: names.append(x.Name)
    if newplayer not in names and newplayer != '':
        players[curP].Name = newplayer.strip()
    combo['values'] = [item.Name for item in players]
    combo.current(curP)
    edAW.deiconify()
    newPW.destroy()


def newPlayer(edAText, combo, edAW):
    TextBoxUpdate(edAText, combo)
    edAW.withdraw()
    newPW = Toplevel(edAW)
    newPW.bind('<Return>', lambda x: edPOK(edAText, combo, edAW, newPW, newPEntry.get()))
    newPW.title("New Player")
    Label(newPW, text="Enter new player name:", padx=10, font=20).grid(row=0, column=0)
    newPEntry = Entry(newPW, font=20)
    newPEntry.grid(row=1, column=0)
    Button(newPW, text='OK', command=lambda: edPOK(edAText, combo, edAW, newPW, newPEntry.get())).grid(row=2,
                                                                                                       column=3)
    Button(newPW, text='Cancel', command=lambda: edPCancel(edAW, newPW)).grid(row=2, column=4)
    newPEntry.focus_force()


def renamePlayer(edAText, combo, edAW):
    global players
    if len(players) > 0:
        TextBoxUpdate(edAText, combo)
        edAW.withdraw()
        newPW = Toplevel(edAW)
        newPW.bind('<Return>', lambda x: edROK(edAText, combo, edAW, newPW, newPEntry.get()))
        newPW.title("Rename Player")
        newPLabel = Label(newPW, text="Rename the player:", padx=10, font=20).grid(row=0, column=0)
        entry_text = StringVar()
        newPEntry = Entry(newPW, font=20, textvariable=entry_text)
        entry_text.set(combo.get())
        newPEntry.grid(row=1, column=0)
        newPOK = Button(newPW, text='OK', command=lambda: edROK(edAText, combo, edAW, newPW, newPEntry.get())).grid(
            row=2, column=3)
        newPCancel = Button(newPW, text='Cancel', command=lambda: edPCancel(edAW, newPW)).grid(row=2, column=4)
        newPEntry.focus_force()


def delPlayer(edAText, combo):
    global players, curP
    if len(players) > 0:
        names = []
        for x in players: names.append(x.Name)
        index = names.index(combo.get())
        players.pop(index)
        if curP == len(players):
            curP -= 1
        combo['values'] = [item.Name for item in players]
        if len(players) == 0:
            combo.set('')
            PAnswers = []
            answers = ""
            edAText.delete(1.0, END)
            edAText.grid(column=0, columnspan=3, rowspan=10, padx=5, pady=5)
        else:
            combo.current(curP)
            PAnswers = []
            answers = ""
            for x in players[curP].Answers: PAnswers.append(x)
            for item in PAnswers: answers = answers + item + "\n"
            edAText.delete(1.0, END)
            edAText.insert(INSERT, answers)
            edAText.grid(column=0, columnspan=3, rowspan=10, padx=5, pady=5)
    combo.event_generate('<<ComboboxSelected>>')


def TextBoxUpdate(edATB, edAText, combo):
    global curP, current_var, players
    # Get current answers
    if len(players) > 0:
        players[curP].StartScore = edATB.get()
        answers = edAText.get(1.0, END).splitlines()
        if answers[-1].lstrip() == '':
            del answers[-1]
        index = 0
        if len(answers) >= len(players[curP].Answers):
            while index < len(players[curP].Answers):
                if answers[index] != players[curP].Answers[index]:
                    players[curP].Answers[index] = answers[index]
                index += 1
            while index < len(answers):
                players[curP].Answers.append(answers[index])
                index += 1
        if len(answers) < len(players[curP].Answers):
            while index < len(answers):
                if answers[index] != players[curP].Answers[index]:
                    players[curP].Answers[index] = answers[index]
                index += 1
            while index < len(players[curP].Answers):
                del players[curP].Answers[index]

        # Lets display new player.
        current_value = current_var.get()
        index = 0
        for item in players:
            if item.Name == current_value:
                curP = index
            else:
                index += 1
        if len(players) != 0:
            combo.current(curP)
            edATB.delete(0, END)
            edATB.insert(0, players[curP].StartScore)
            PAnswers = []
            answers = ""
            for x in players[curP].Answers: PAnswers.append(x)
            for item in PAnswers: answers = answers + str(item) + "\n"
            edAText.delete(1.0, END)
            edAText.insert(INSERT, answers)
            edAText.grid(column=0, columnspan=3, rowspan=10, padx=5, pady=5)


def validate_entry2(inp):
    if inp == "": return True
    try:
        float(inp)
    except:
        return False
    return True


def edAnswers(window):
    global players, curP, current_var

    def select_next(event):
        selection = combo.current()  # get the current selection
        last = len(combo['values']) - 1  # index of last item
        key = event.keysym  # get the key that was pressed
        if key == 'Up':
            try:
                combo.current(selection - 1)  # set the combobox to the previous item
                combo.event_generate('<<ComboboxSelected>>')
            except TclError:  # end of list reached
                pass  # combo.current(last)  # wrap around to last item
        elif key == 'Down':
            try:
                combo.current(selection + 1)  # set the combobox to the next item
                combo.event_generate('<<ComboboxSelected>>')
            except TclError:  # end of list reached
                pass  # combo.current(0)  # wrap around to first item
        return 'break'  # tell tk to dispose of this event and don't show the menu!

    window.withdraw()
    edAW = Toplevel(window)
    edAW.bind("<<ComboboxSelected>>", lambda x: TextBoxUpdate(edATB, edAText, combo))
    if len(players) == 0:
        players = []
    if len(sg.Players) != 0:
        playerlist = []
        for x in players: playerlist.append(x.Name)
        for qnum, question in enumerate(sg.Questions):
            for gnum, grp in enumerate(sg.Questions[qnum].Groups):
                for a, ans in enumerate(grp.Answers):
                    if ans.Player.Name not in playerlist:
                        players.append(EdPlayer(ans.Player.Name))
                        playerlist.append(ans.Player.Name)
                    if (len(players[playerlist.index(ans.Player.Name)].Answers)) == qnum:
                        players[playerlist.index(ans.Player.Name)].Answers.append(ans.Text)
    for x, y in enumerate(players):
        y.StartScore = sg.Players[x].StartScore

    if curP >= len(players):
        curP = len(players) - 1
    answers = ""
    if len(players) == 0:
        answers = 'Click Load... to load players and answers\nfrom a PM text file, or click New Player\nto add players manually.'
        curP = 0
    else:
        PAnswers = []
        for x in players[curP].Answers: PAnswers.append(x)
        for item in PAnswers: answers = answers + item + "\n"
    combo = ttk.Combobox(edAW, textvariable=current_var, state="readonly", values=[item.Name for item in players])
    if len(players) != 0: combo.current(curP)
    combo.bind('<Up>', select_next)  # up arrow
    combo.bind('<Down>', select_next)  # down arrow
    combo.grid(row=0, column=1)
    edAW.title("Edit Entries")
    edALabel = Label(edAW, text="Player:")
    edALabel.grid(row=0, column=0)
    Label(edAW).grid(row=0, column=2)
    edALabel = Label(edAW, text="Starting Score:", padx=10)
    edALabel.grid(row=1, column=0)
    edATB = Entry(edAW, width=10, validate="key", validatecommand=(window.register(validate_entry2), "%P"))
    if len(players) != 0:
        ss = players[curP].StartScore
        edATB.insert(INSERT, ss)
    edATB.grid(row=1, column=1)
    edAText = Text(edAW)
    if len(players) == 0:
        edAText.insert(INSERT,
                       'Click Load... to load players and answers\nfrom a PM text file, or click New Player\nto add players manually.')
    else:
        edAText.insert(INSERT, answers)
    edAText.grid(column=0, columnspan=3, rowspan=10, padx=5, pady=5)
    Button(edAW, text="Load", padx=20, command=lambda: edAL(edAText, combo)).grid(row=0, column=3, padx=10, pady=5)
    Button(edAW, text="New Player", padx=4, command=lambda: newPlayer(edAText, combo, edAW)).grid(row=1, column=3,
                                                                                                  padx=10, pady=5)
    Button(edAW, text="Change Name", padx=0, command=lambda: renamePlayer(edAText, combo, edAW)).grid(row=2, column=3,
                                                                                                      padx=10, pady=5)
    Button(edAW, text="Delete Player", padx=0, command=lambda: delPlayer(edAText, combo)).grid(row=3, column=3, padx=10,
                                                                                               pady=5)
    Button(edAW, text="Save Changes", command=lambda: edPSave(edAW, edAText, combo)).grid(row=9, column=3, padx=10,
                                                                                          pady=5)
    Button(edAW, text="Cancel", padx=20, command=lambda: edCancel(edAW)).grid(row=10, column=3, padx=10, pady=5)
    edAW.rowconfigure(4, weight=1)
    edAW.columnconfigure(2, weight=1)
    return


def edQuestions(window):
    window.withdraw()
    myfile = "\n".join(item.Text.lstrip() for item in sg.Questions)
    edQW = Toplevel(window)
    edQW.title("Edit Questions")
    edQLabel = Label(edQW,
                     text="Click Load... to load the questions from a text file, or just type them in here one per line")
    edQLabel.grid(row=0, columnspan=2)
    edQText = Text(edQW)
    edQText.insert(INSERT, myfile)
    edQText.grid(column=0, rowspan=10, padx=5, pady=5)
    edQLoad = Button(edQW, text="Load", padx=20, command=lambda: edQL(edQText)).grid(row=1, column=1)
    edQSave = Button(edQW, text="Save Changes", command=lambda: edSave(edQW, edQText)).grid(row=9, column=1)
    edQCancel = Button(edQW, text="Cancel", padx=20, command=lambda: edCancel(edQW)).grid(row=10, column=1)
    return


def validate_entry(text):
    return text.isdecimal()



def bDown(event):
    tv = event.widget
    if tv.identify_row(event.y) not in tv.selection():
        tv.selection_set(tv.identify_row(event.y))


def bUp(event):
    tv = event.widget
    if tv.identify_row(event.y) == "": return
    Tmoveto = tv.index(tv.identify_row(event.y))
    if tv.identify_row(event.y) not in tv.selection():
        moveto = myTreeview.item(tv.identify_row(event.y))
        fromANS = myTreeview.item(tv.selection())['values']
        fromGRP = myTreeview.item(tv.selection())['values']
        toGRP = moveto['values']
        if toGRP != "" and fromGRP != "":
            if fromGRP[0] == toGRP[0] and len(fromGRP) > 1:
                for i, q in enumerate(sg.Questions):
                    if int(i) == int(fromANS[0]):
                        myq = q
                for g in myq.Groups:
                    if g.Text == fromGRP[1]:
                        fog = g
                    if g.Text == toGRP[1]:
                        tog = g
                found = 0
                if len(fromGRP) ==3:
                    for g in myq.Groups:
                        for asx in g.Answers:
                            myans = asx
                            if asx._Player.Name == fromANS[2] and found != 1:
                                found = 1
                                tog.Answers.append(asx)
                                fog.Answers.remove(asx)
                                if len(fog.Answers) == 0:
                                    myq.Groups.remove(fog)
                                updateTreeview()
                elif len(fromGRP)==2:
                    fog.MergeToGroup(tog)
                    updateTreeview()





def displayTreeview():
    global myTreeview
    myTreeview.grid(row=1, column=0, columnspan=6, sticky='NSEW', padx=10, pady=5)


def updateTreeview():
    global myTreeview, curQ, vsb
    sg.Method = sg.ShMethod(Gametype.get())
    sg.Rounding = sg.ShRoundingType(Roundtype.get())
    if len(sg.Questions) != 0:
        myTreeview.grid_forget()
        myTreeview.delete(*myTreeview.get_children())
        if (curQ > len(sg.Questions)):
            curQ == len(sg.Questions)
        if (curQ < 1):
            curQ = 1
        curQuestion = sg.Questions[curQ - 1]
        # give instructions if no players loaded
        if (len(sg.Players) == 0):
            myTreeview.insert('', 'end', text="Click sheep >  Edit Entries... to add entries.", iid=0)
            displayTreeview()
        curgroup = 0
        curItem = 0
        # loop through each group
        for group in curQuestion.Groups:
            group_node = myTreeview.insert("", "end", open=cbvar1.get(), tags="group",
                                           value=[sg.Questions.index(curQuestion), group.Text],
                                           text=TextForGroupNode(group))
            for answer in group.Answers:
                myTreeview.insert(group_node, "end", tags="answer",
                                  value=[sg.Questions.index(curQuestion), group.Text, answer.Player.Name],
                                  text=TextForAnswerNode(answer))
        displayTreeview()
    else:
        myTreeview.grid_forget()
        vsb.grid_forget()
        myTreeview.delete(*myTreeview.get_children())
        displayTreeview()
        # text will be added later so don't bother with it in this function
        # for grp in curQuestion:
        #    curGroup=myTreeview.insert('','end',text=".",iid=0)

        # myTreeview.insert('','end',text="this is text",iid=0)


def do_popup(event):
    tv = event.widget
    item = tv.identify_row(event.y)
    if tv.identify_row(event.y) not in tv.selection():
        tv.selection_set(tv.identify_row(event.y))
    if item == "":
        return
    elif myTreeview.item(item)["tags"][0] == "group":
        try:
            tv.popup.tk_popup(event.x_root, event.y_root, 0)
        finally:
            tv.popup.grab_release()
    elif myTreeview.item(item)["tags"][0] == "answer":
        try:
            tv.popup2.tk_popup(event.x_root, event.y_root, 0)
        finally:
            tv.popup2.grab_release()


def SetGroupName():
    top = Toplevel()
    top.grab_set()
    top.bind('<Return>', lambda x: set_newgroupname(top, entry.get()))
    label = Label(top, text="What is the new name for the group?")
    entry = Entry(top, textvariable=input)
    buttonok = Button(top, text="OK", command=lambda: set_newgroupname(top, entry.get()))
    buttoncancel = Button(top, text="Cancel", command=lambda: edCancel(top))
    label.pack()
    entry.pack()
    buttonok.pack()
    buttoncancel.pack()
    entry.focus_force()


def set_newgroupname(top, input):
    top.destroy()
    values = myTreeview.item(myTreeview.selection())['values']
    q = values[0]
    question = sg.Questions[q]
    groupnames = [grp.Text for grp in question.Groups]
    if input not in groupnames and input != "":
        sg.Questions[q].Groups[groupnames.index(str(values[1]))].Text = input
    updateTreeview()


def UseAsGroupName():
    values = myTreeview.item(myTreeview.selection())['values']
    q = values[0]
    question = sg.Questions[q]
    groupnames = [grp.Text for grp in question.Groups]
    answers = [x for x in sg.Questions[q].Groups[groupnames.index(values[1])].Answers]
    for x in answers:
        if x.Player.Name == str(values[2]):
            newgrpname = x.Text
    if newgrpname not in groupnames and input != "":
        sg.Questions[q].Groups[groupnames.index(str(values[1]))].Text = newgrpname
    updateTreeview()


def MoveToNewGroup():
    values = myTreeview.item(myTreeview.selection())['values']
    q = values[0]
    pname = values[2]
    question = sg.Questions[q]
    group_names = [grp.Text for grp in question.Groups]
    answers = [x for x in sg.Questions[q].Groups[group_names.index(values[1])].Answers]
    answer = ""
    for x in answers:
        if x.Player.Name == str(pname):
            answer = x
    if answer != "" and answer.Text not in group_names and input != "":
        new_group = ShGame.ShGroup(sg.Questions[q], answer.Text)
        new_group.Answers.append(answer)
        sg.Questions[q].Groups.append(new_group)
        sg.Questions[q].Groups[group_names.index(str(values[1]))].Answers.remove(answer)
        if len(sg.Questions[q].Groups[group_names.index(str(values[1]))].Answers) == 0:
            sg.Questions[q].Groups.pop(group_names.index(str(values[1])))
    updateTreeview()


def copyPlayerListMenuItem_Click():
    if sg is None or len(sg.Players) == 0 or len(sg.Questions) == 0:
        copy_to_clipboard("Either no questions or no players loaded.")
        return
    if Output_type.get() == 1:
        TableText = True
        UnformattedText = False
        FormattedText = False
    elif Output_type.get() == 2:
        FormattedText = True
        UnformattedText = False
        TableText = False
    else:
        UnformattedText = True
        FormattedText = False
        TableText = False

    any_starting_scores = any(int(p.StartScore) != 0 for p in sg.Players)
    ss_pre = "[b][color=green]" if FormattedText or TableText else ""
    ss_post = "[/color][/b]" if FormattedText or TableText else ""
    start_score_string = ss_pre + " (starting score)" + ss_post if any_starting_scores else ""

    txt = ("" if UnformattedText else "[b]") + str(len(sg.Players)) + " players" + start_score_string + ":" + (
        "" if UnformattedText else "[/b]") + "\n\n" + \
          "\n".join(sorted( p.Name   + ((" " + ss_pre + "(" + ("%.4g" % p.StartScore) + ")" + ss_post) if int(p.StartScore) != 0 else "") for p in sg.Players))


    copy_to_clipboard(txt)


def copy_to_clipboard(stuff):
    r = Tk()
    r.withdraw()
    r.clipboard_clear()
    r.clipboard_append(stuff)
    r.update()  # now it stays on the clipboard after the window is closed
    r.destroy()


# returns text that should be displayed on this treenode
def TextForGroupNode(grp):
    curScoreMethod = sg.Method
    if len(grp.Answers) == 0:
        return grp.Text

    scoreString = ""

    try:
        if curScoreMethod == sg.ShMethod.Manual:
            scoreString = "[" + str(grp.GroupBonus) + "]"
        else:
            bonus_text = ""
            if grp.BonusType == ShGame.ShBonusType.Override:
                bonus_text = " (=" + str(grp.GroupBonus) + ")"
            elif grp.BonusType == ShGame.ShBonusType.Add:
                if grp.GroupBonus > 0:
                    bonus_text = " + " + str(grp.GroupBonus)
                if grp.GroupBonus < 0:
                    bonus_text = " - " + str(-grp.GroupBonus)
            scoreString = "[" + str(grp.Question.scores(False)[grp.Answers[0].Player]) + bonus_text + "]"
    except:
        scoreString = "ERROR"

    return grp.Text + " - " + (
        "" if grp.Correct else ShGame.get_correct_text(curScoreMethod, grp.Correct).upper() + " - ") + scoreString


def TextForAnswerNode(ans):
    bonus_text = ""
    if ans.BonusType == ShGame.ShBonusType.Override:
        bonus_text = " (=" + ans.AnswerBonus + ")"
    elif ans.BonusType == ShGame.ShBonusType.Add:
        if ans.AnswerBonus != 0:
            bonus_text = " (" + ("+" if ans.AnswerBonus > 0 else "") + ans.AnswerBonus + ")"

    return ans.Text + " - " + ans.Player.Name + bonus_text


# generate post for answers
def copyAnswersMenuItem_Click():
    global curQ
    cur_q_index = curQ -1
    curScoreMethod = sg.Method
    if sg is None or len(sg.Players) == 0 or len(sg.Questions) == 0:
        copy_to_clipboard("Either no questions or no players loaded.")
        return

    if Output_type.get() == 1:
        TableText = True
        UnformattedText = False
        FormattedText = False
    elif Output_type.get() == 2:
        FormattedText = True
        UnformattedText = False
        TableText = False
    else:
        UnformattedText = True
        FormattedText = False
        TableText = False

    OpenBold = "" if UnformattedText else "[B]"
    CloseBold = "" if UnformattedText else "[/B]"

    txt = OpenBold + "Question " + str(cur_q_index + 1) + ": " + sg.Questions[cur_q_index].Text + CloseBold + "\n\n"

    # sheepscoreoutput
    validGroups = []  # valid/correct groups
    validAces = []  # valid/correct aces
    invalidGroups = []  # invalid/incorrect groups

    if curScoreMethod == sg.ShMethod.Sheep or curScoreMethod == sg.ShMethod.Heep or curScoreMethod == sg.ShMethod.Heep15 or curScoreMethod == sg.ShMethod.Heep2 or curScoreMethod == sg.ShMethod.PeehsDM or curScoreMethod == sg.ShMethod.PeehsFB or curScoreMethod == sg.ShMethod.PeehsHybrid:
        validGroups = [g for g in sg.Questions[cur_q_index].Groups if len(g.Answers) > 1 and g.Correct]
        validGroups.sort(key=lambda g: -len(g.Answers))

        validAces = [g for g in sg.Questions[cur_q_index].Groups if len(g.Answers) == 1 and g.Correct]

        invalidGroups = [g for g in sg.Questions[cur_q_index].Groups if not g.Correct]
    elif curScoreMethod == sg.ShMethod.Kangaroo:
        validGroups = [g for g in sg.Questions[cur_q_index].Groups if len(g.Answers) > 1 and not g.Correct]
        validGroups.sort(key=lambda g: -len(g.Answers))

        validAces = [g for g in sg.Questions[cur_q_index].Groups if len(g.Answers) == 1 and not g.Correct]

        invalidGroups = [g for g in sg.Questions[cur_q_index].Groups if g.Correct]
    elif curScoreMethod == sg.ShMethod.Manual:
        validGroups = [g for g in sg.Questions[cur_q_index].Groups if g.Correct]
        validGroups.sort(key=lambda g: -len(g.Answers))

        invalidGroups = [g for g in sg.Questions[cur_q_index].Groups if not g.Correct]

    for grp in validGroups:

        g_bonus_text = get_score_output_text(grp.GetScore(False), grp.BonusType, grp.GroupBonus, curScoreMethod).strip()
        txt += OpenBold + grp.Text + " - " + g_bonus_text + CloseBold + "\n"
        for ans in sorted(grp.Answers, key=lambda a: a.Player.Name):
            p_bonus_text = get_bonus_output_text(ans.BonusType, ans.AnswerBonus, curScoreMethod).strip()
            txt += ans.Player.Name + (
                " " + OpenBold + p_bonus_text + CloseBold if p_bonus_text else "") + "\n"

        txt += "\n"

    if len(validAces) > 0:
        txt += OpenBold + "ACES - " + str(
            validAces[0].GetScore(False)) + ":" + CloseBold + "\n" + "\n"

    for grp in validAces:
        ans = grp.Answers[0]
        if ans.BonusType == ShGame.ShBonusType.Override:
            bonus_text = get_bonus_output_text(ans.BonusType, ans.AnswerBonus, curScoreMethod)
        else:
            bonus_text = get_bonus_output_text(grp.BonusType, grp.GroupBonus,
                                               curScoreMethod) + " " + get_bonus_output_text(
                ans.BonusType, ans.AnswerBonus, curScoreMethod)
        bonus_text = bonus_text.strip()
        if bonus_text:
            bonus_text = OpenBold + bonus_text + CloseBold
        txt += OpenBold + grp.Text + CloseBold + " - " + grp.Answers[
            0].Player.Name + " " + bonus_text + "\n"

    if len(invalidGroups) > 0:
        txt += "\n" + OpenBold + ShGame.get_correct_text(curScoreMethod, (
                curScoreMethod == sg.ShMethod.Kangaroo)) + "S" + " - " + str(
            invalidGroups[0].GetScore(False)) + ":" + CloseBold + "\n" + "\n"

    for grp in sorted(invalidGroups, key=lambda g: g.Text):
        for ans in sorted(grp.Answers, key=lambda a: a.Player.Name):
            if ans.BonusType == ShGame.ShBonusType.Override:
                bonus_text = get_bonus_output_text(ans.BonusType, ans.AnswerBonus, curScoreMethod)
            else:
                bonus_text = get_bonus_output_text(grp.BonusType, grp.GroupBonus,
                                                   curScoreMethod) + " " + get_bonus_output_text(ans.BonusType,
                                                                                                 ans.AnswerBonus,
                                                                                                 curScoreMethod)
            bonus_text = bonus_text.strip()
            if bonus_text:
                bonus_text = OpenBold + bonus_text + CloseBold

            txt += OpenBold + ans.Text + CloseBold + " - " + ans.Player.Name + " " + bonus_text + "\n"
    copy_to_clipboard(txt)

# methods for getting score
def get_score_output_text(score, bonus_type, bonus, method):
    if method == "Manual":
        if bonus_type == "None":
            return "0"
        else:
            return format(bonus, "0.#####")
    else:
        return str(score) + (" " + get_bonus_output_text(bonus_type, bonus, method) if bonus != 0 else "")


def get_bonus_output_text(bonus_type, bonus, method):
    if bonus_type == ShGame.ShBonusType.NONE:
        return ""

    if Output_type.get() == 1:
        TableText = True
        UnformattedText = False
        FormattedText = False
    elif Output_type.get() == 2:
        FormattedText = True
        UnformattedText = False
        TableText = False
    else:
        UnformattedText = True
        FormattedText = False
        TableText = False

    bonus_color = "Blue"

    if bonus_type == ShGame.ShBonusType.Override:
        bonus_color = "Purple"

    if bonus_type == ShGame.ShBonusType.Add and (
            (bonus < 0) ^ (method == sg.ShMethod.PeehsFB or method == sg.ShMethod.PeehsDM or method == sg.ShMethod.PeehsHybrid)):
        bonus_color = "Red"

    bonus_open = "" if UnformattedText else "[COLOR=\"" + bonus_color + "\"]"
    bonus_close = "" if UnformattedText else "[/COLOR]"

    bonus_pfx = ""
    if bonus_type == ShGame.ShBonusType.Override:
        bonus_pfx = "="
    elif float(bonus) > 0:
        bonus_pfx = "+"

    return bonus_open + "(" + bonus_pfx + str(bonus) + ")" + bonus_close


# Generate post for score totals up to and including this question
def copy_scores_up_to_this_question():
    global curQ
    cur_q_index = curQ -1
    curScoreMethod = sg.Method
    if sg is None or len(sg.Players) == 0 or len(sg.Questions) == 0:
        copy_to_clipboard("Either no questions or no players loaded.")
        return

    cur_scores = sg.Questions[cur_q_index].score_up_to(True)

    for plr in sg.Players:
        if plr not in cur_scores:
            copy_to_clipboard("ERROR")
            return
        cur_scores[plr] += float(plr.StartScore)

    order_mult = 1 if ShGame.is_score_descending(curScoreMethod) else -1
    txt = ""

    if Output_type.get() == 1:
        TableText = True
        UnformattedText = False
        FormattedText = False
    elif Output_type.get() == 2:
        FormattedText = True
        UnformattedText = False
        TableText = False
    else:
        UnformattedText = True
        FormattedText = False
        TableText = False

    if FormattedText or TableText:
        txt += "[b]"

    txt += "Scores after question " + str(cur_q_index + 1) + ":"

    if FormattedText or TableText:
        txt += "[/b]"

    txt += "\n\n"

    s_list = sorted(sg.Players, key=lambda p: cur_scores[p] * order_mult, reverse=True)

    if TableText:
        txt += "[table=30][tr][th]Player[/th][th]Score[/th][/tr]" + \
            "\n".join([("[tr][td]"+ p.Name + "[/td][td]" + ("%.4g" % cur_scores[p]) + "[/td][/tr]")  for p in s_list]) + \
            "[/table]\n"
    else:
        txt += "\n".join([("%.4g" % cur_scores[p]) + " - " + p.Name for p in s_list]) + "\n"

    copy_to_clipboard(txt)


def copyAllScoresUpToThisQuestionMenuItem_Click():
    global curQ
    cur_q_index = curQ -1
    curScoreMethod = sg.Method
    if sg is None or len(sg.Players) == 0 or len(sg.Questions) == 0:
        copy_to_clipboard("Either no questions or no players loaded.")
        return

    # only for tables
    if Output_type.get() != 1:
        copy_to_clipboard("List all scores only available for Table Formatting")
        return

    order_mult = -1 if ShGame.is_score_descending(curScoreMethod) else 1

    curScores = {}
    for plr in sg.Players:
        curScores[plr] = []

    for iQues in range(cur_q_index + 1):
        q_scores = sg.Questions[iQues].scores(True)
        for plr_scores in curScores.items():
            if plr_scores[0] not in q_scores:
                copy_to_clipboard("ERROR: players list out of sync q=" + str(iQues) + " p=" + str(plr_scores[0].game_index))
                return
            plr_scores[1].append(q_scores[plr_scores[0]])

    if any(len(ps[1]) != (1 + cur_q_index) for ps in curScores.items()):
        copy_to_clipboard("ERROR: answers list out of sync")
        return

    txt = "[b]Scores after question " + str(
        cur_q_index + 1) + ":[/b]" + "\n" + "\n" + "[table=30][tr][th]Player[/th][th]Total[/th]"

    any_starting_scores = any(p.StartScore != 0 for p in sg.Players)

    if any_starting_scores:
        txt += "[th]Start[/th]"

    for iQues in range(cur_q_index + 1):
        txt += "[th]Q" + str(iQues + 1) + "[/th]"
    txt += "[/tr]"

    for plr_scores in sorted(curScores.items(), key=lambda ps: (str(float(ps[0].StartScore) + sum(ps[1]))) * order_mult):
        plr = plr_scores[0]
        scrs = plr_scores[1]
        start_score_string = "\t" + str(plr.StartScore) if any_starting_scores else ""
        txt += "\n" + "[tr][td]" + plr.Name + "[/td][td][b]" + str(int(plr.StartScore) + sum(scrs)) + "[/b][/td][td]" + start_score_string + "[/td]"+"".join(("[td]"+str(s)+"[/td]") for s in scrs) + "[/tr]"

    txt += "[/table]" + "\n"

    copy_to_clipboard(txt)


def debug():
    print("sg " + str(sg))
    print("Game type: " + str(sg.Method) + " Rounding: " + str(sg.Rounding))
    print("GetAllAnswers for Q[0]:", sg.Questions[0].GetAllAnswers())
    print("Question[0].Scores:", sg.Questions[0].Scores(False))
    scores = []
    for x, group in enumerate(sg.Questions[0].Groups):
        scores.append(f"Group {x} scores {group.GetScore(False)} ")
    print("q0g0.GetScore", scores)


gt = {'Sheep': 1, 'PeehsDM': 2, 'PeehsFB': 3, 'PeehsHybrid': 4, 'Heep': 5, 'Heep15': 6, 'Heep2': 7, 'Kangaroo': 8,
      'Manual': 9}
gtl = ['filler', 'Sheep', 'PeehsDM', 'PeehsFB', 'PeehsHybrid', 'Heep', 'Heep15', 'Heep2', 'Kangaroo', 'Manual']

rt = {'None': 0, 'Up': 1, 'Down': 2, 'Nearest': 3}
rtl = ['None', 'Up', 'Down', 'Nearest']

bt = {'None': 1, 'Add': 2, 'Override': 3}
btl = ['filler', 'None', 'Add', 'Override']

sg = ShGame()
players = []
score = []
curQ = 1
curP = 1

window = Tk()

window.geometry("680x450")
window.title("Sheep Score Foggies Edition")
Output_type = IntVar()
Output_type.set(1)
Gametype = IntVar()
Gametype.set(1)
Roundtype = IntVar()
Roundtype.set(0)
current_var = StringVar()
menubar = Menu(window)
cbvar1 = IntVar()
ss = IntVar()
window.config(menu=menubar)

fileMenu = Menu(menubar, tearoff=0)
menubar.add_cascade(label="File", menu=fileMenu)

fileMenu.add_command(label="New Reveal", command=resetProgram)
fileMenu.add_command(label="Load Reveal...", command=sg.loadReveal)
fileMenu.add_command(label="Save Reveal...", command=sg.saveReveal)
#fileMenu.add_command(label="Debug", command=debug)
fileMenu.add_separator()
fileMenu.add_command(label="Exit", command=quit)

sheepMenu = Menu(menubar, tearoff=0)
menubar.add_cascade(label="Sheep", menu=sheepMenu)
sheepMenu.add_command(label="Edit Questions...", command=lambda: edQuestions(window))
sheepMenu.add_command(label="Edit Entries...", command=lambda: edAnswers(window))

scoringMenu = Menu(menubar, tearoff=0)
sheepMenu.add_cascade(label="Scoring", menu=scoringMenu)
scoringMenu.add_radiobutton(label="Sheep", value=1, variable=Gametype, command=updateTreeview)
peehsMenu = Menu(menubar, tearoff=0)
scoringMenu.add_cascade(label="Peehs", menu=peehsMenu)
peehsMenu.add_radiobutton(label="DM Scoring", value=2, variable=Gametype, command=updateTreeview)
peehsMenu.add_radiobutton(label="FB Scoring", value=3, variable=Gametype, command=updateTreeview)
peehsMenu.add_radiobutton(label="Hybrid", value=4, variable=Gametype, command=updateTreeview)
heepsMenu = Menu(menubar, tearoff=0)
scoringMenu.add_cascade(label="Heeps", menu=heepsMenu)
heepsMenu.add_radiobutton(label="2x Heep Bonus", value=7, variable=Gametype, command=updateTreeview)
heepsMenu.add_radiobutton(label="1.5x Heep Bonus", value=6, variable=Gametype, command=updateTreeview)
heepsMenu.add_radiobutton(label="No Heep Bonus", value=5, variable=Gametype, command=updateTreeview)
scoringMenu.add_radiobutton(label="Kangaroo", value=8, variable=Gametype, command=updateTreeview)
scoringMenu.add_radiobutton(label="Manual", value=9, variable=Gametype, command=updateTreeview)
scoringMenu.add_separator()

roundingMenu = Menu(menubar, tearoff=0)
scoringMenu.add_cascade(label="Rounding", menu=roundingMenu)
roundingMenu.add_radiobutton(label="No Rounding", value=0, variable=Roundtype, command=updateTreeview)
roundingMenu.add_radiobutton(label="Round Up", value=1, variable=Roundtype, command=updateTreeview)
roundingMenu.add_radiobutton(label="Round Down", value=2, variable=Roundtype, command=updateTreeview)
roundingMenu.add_radiobutton(label="Round Nearest", value=3, variable=Roundtype, command=updateTreeview)

outputMenu = Menu(menubar, tearoff=0)
menubar.add_cascade(label="Output", menu=outputMenu)
outputMenu.add_command(label="Copy answers for this question", command=copyAnswersMenuItem_Click)
outputMenu.add_command(label="Copy total scores up to this question",command=copyAllScoresUpToThisQuestionMenuItem_Click)
outputMenu.add_command(label="Copy score table up to this question",command=copy_scores_up_to_this_question)
outputMenu.add_command(label="Copy Player list", command=copyPlayerListMenuItem_Click)
outputMenu.add_separator()
styleMenu = Menu(menubar, tearoff=0)
outputMenu.add_cascade(label="Output Style", menu=styleMenu)
styleMenu.add_radiobutton(label="Forum Table", value=1, variable=Output_type)
styleMenu.add_radiobutton(label="Forum Formatted Text", value=2, variable=Output_type)
styleMenu.add_radiobutton(label="Unformatted Text", value=3, variable=Output_type)

Button(window, text="<", command=qdown).grid(row=0, column=1)
Button(window, text=">", command=qup).grid(row=0, column=3)
Label(window, text="Q #", padx=5).grid(row=0, column=0)

myCheckbox1 = Checkbutton(window, text='show collapsed', variable=cbvar1, onvalue=0, offvalue=1, command=updateTreeview)
myCheckbox1.grid(row=0, column=4)
myLabel2 = Label(window, text="Click Sheep > Edit Questions... to begin.")
myLabel2.grid(row=0, column=5)

myTextbox1 = Entry(window, width=4, validate="key", validatecommand=(window.register(validate_entry), "%S"))

myTextbox1.insert(INSERT, curQ)
myTextbox1.grid(row=0, column=2)
myTextbox1.bind("<Return>", qset)
myTreeview = ttk.Treeview(window, show="tree")
vsb = ttk.Scrollbar(window, orient="vertical", command=myTreeview.yview)
myTreeview.configure(yscrollcommand=vsb.set)
vsb.grid(column=6, sticky='ns')
myTreeview.popup = Menu(window, tearoff=0)
myTreeview.popup.add_command(label="Set Group Name...", command=SetGroupName)  # , command=next) etc...
myTreeview.popup.add_command(label="Mark invalid")
myTreeview.popup.add_command(label="Group Score")  # , command=lambda: self.closeWindow())
myTreeview.popup2 = Menu(window, tearoff=0)
myTreeview.popup2.add_command(label="Use as Group Name", command=UseAsGroupName)  # , command=next) etc...
myTreeview.popup2.add_command(label="Move to new group", command=MoveToNewGroup)
myTreeview.popup2.add_command(label="Player Score...")  # , command=lambda: self.closeWindow()
myTreeview.bind("<Button-3>", do_popup)
myTreeview.bind("<ButtonPress-1>", bDown)
myTreeview.bind("<ButtonRelease-1>", bUp, add='+')

displayTreeview()
vsb = ttk.Scrollbar(window, orient="vertical", command=myTreeview.yview)
window.rowconfigure(1, weight=1)
window.columnconfigure(5, weight=1)

#sg.loadReveal()

window.mainloop()
