from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import argparse
import os
import time
import six
from colorama import init, Fore, Back
import sys
from multiprocessing import Process


init(autoreset=True)


if os.name == "nt":
    import win32com.client as wincl

    def _say(sentence, sleepseconds=0.5):
        try:
            speaker = wincl.Dispatch("SAPI.SpVoice")
            speaker.Speak(sentence)
            time.sleep(sleepseconds)
        except Exception as ex:
            print("Error in speaking: ".format(ex.msg))
else:
    def _say(sentence, sleepseconds=0.5):
        os.system("say {0}".format(sentence))
        time.sleep(sleepseconds)


CORRECT_RES = ["Thats Fantastic Effort", "Wow thats good",
               "Thats right. Way to go.", "Good Job.", "Excellent", "Thats correct. Good Effort"]
INCORRECT_RES = ["Thats Incorrect",
                 "Try Harder", "Focus", "Are you kidding me", "Focus on this"]

# TODO Streaks
# Streaks encoragement


def is_time_to_add_words(fname):
    next_due_date = _get_next_review_day(fname)
    seconds_to_next_review = next_due_date-datetime.now()
    # check if the time has past 5 hours
    return seconds_to_next_review.seconds >= 60*60*5


def check_next_active(fname, num=5):
    if not is_time_to_add_words(fname):
        return
    wordslist = get_words(fname)
    selected_word = [word for word in wordslist if word.active is False]
    if len(selected_word) > num:
        selected_word = selected_word[:num]

    for word in selected_word:
        word.active = True
        word.due_data = datetime.now()+timedelta(seconds=600)
    save_words(wordslist, fname)


def notify(num, filename):
    msg = 'display notification "{}" with title "Fill_IN APP" sound name "Submarine"'
    text = "{} in {}".format(num, os.path.basename(filename))
    rest_command = """'display notification "{}" with title "FILL IN APP" sound name "Submarine"'""".format(
        text)
    os.system("osascript -e " + rest_command)


def get_no_of_words(args):
    wordslist = get_words(args.word_file)
    sw = get_selected_word(wordslist)
    n_words = len(sw)
    if n_words:
        notify(n_words, args.word_file)


def get_selected_word(wordlist):
    now = datetime.now()
    selected_word = [
        word for word in wordlist if word.due_date < now and word.active]
    return selected_word

def get_words_to_reveiw(wordlist):
    selected_word = get_selected_word(wordlist)
    no_words = len(selected_word)
    # if more than 15 words, show only 10-15 words
    if no_words > 20:
        selected_word = selected_word[:np.random.randint(15, 20)]
    if not selected_word:
        print("Nothing to review.")
        _say("Nothing to review.")
    else:
        print("{} words selected out of {}".format(
            len(selected_word), no_words))
    return selected_word


THESHOLDS = [timedelta(seconds=120), timedelta(hours=3), timedelta(hours=7), timedelta(hours=24), timedelta(days=2), timedelta(
    days=4), timedelta(days=8), timedelta(days=16), timedelta(days=28), timedelta(days=90), timedelta(days=180)]


class Card:
    def __init__(self, question, answer,  num=0, due_date=datetime.now(), active=False):
        self.question = question
        self.answer = answer
        self.num = num
        self.due_date = due_date
        self.active = active
        # self.no_incorrect = 0
        # self.no_of_tries = 0

    def increment(self):
        # self.no_of_tries += 1
        if self.num < len(THESHOLDS):
            self.num = self.num + 1
        else:
            self.num = len(THESHOLDS)

    def decrement(self):
        # self.no_of_tries += 1
        # punish if wrong after 28 days
        if self.num >= 8:
            self.num -= 6
        elif self.num >= 0:
            self.num = self.num - 1
            # self.no_incorrect += 1
        else:
            self.num = 0
            # self.no_incorrect += 1

    def update_due_date(self):
        try:
            self.due_date = datetime.now() + THESHOLDS[self.num]
        except Exception as ex:
            self.due_date = datetime.now() + THESHOLDS[self.num-1]

    def toggle_acive(self):
        self.active = not self.active

    def __repr__(self):
        return "{0} {1} {2} {3}".format(self.question, self.num, self.active, self.due_date)


class Deck():
    """
    Deck will be a file , with all the cards.
    """
    def __init__(self, fname = "words.csv"):
        self.fname = fname
        self.cards = None

    def _get_words(self):
        if os.path.exists(self.fname):
            df = pd.read_csv(self.fname, infer_datetime_format=True,
                            parse_dates=["due_date"])
            df = df.sort_values(by="due_date", ascending=False)
            wordlists = [Card(row.question, row.answer,  num=row.num,
                            due_date=row.due_date, active=row.active) for _, row in df.iterrows()]
        else:
            wordlists = []
        return wordlists

    def get_all_cards(self):
        if self.cards is None:
            self.cards = self._get_words()
        return self.cards
    
    def save_words(self, wordslist):
        pd.DataFrame(data=[(word.question, word.answer, word.due_date, word.num, word.active)
                       for word in wordslist], columns=["question", "answer", "due_date", "num", "active"]).to_csv(self.fname)

    def get_due_cards(self):
        pass
    


def ask(text):
    return six.moves.input(text)


def confirm(text):
    while True:
        choice = input(text.strip(' ') + ' ').lower()
        if choice in ('yes', 'y', 'ye', 'yep', 'yeah'):
            return True
        elif choice in ('no', 'n', 'nah', 'nay'):
            return False
        else:
            print("Please respond with 'yes' or 'no'")


def format_timedelta(delta):
    seconds = abs(int(delta.total_seconds()))
    periods = [
        (60 * 60 * 24 * 365, 'year'),
        (60 * 60 * 24 * 30, 'month'),
        (60 * 60 * 24, 'day'),
        (60 * 60, 'hour'),
        (60, 'minute'),
        (1, 'second')
    ]

    parts = []
    for period_seconds, period_name in periods:
        if seconds > period_seconds:
            period_value, seconds = divmod(seconds, period_seconds)
            part = '%s %s' % (period_value, period_name)
            if period_value > 1:
                part += 's'
            parts.append(part)
    ret = ', '.join(parts)
    if delta.total_seconds() < 0:
        ret = '-' + ret
    return ret


def do_review_one(word):
    while True:
        _say_question(word.question)
        answer_text = ask("")
        if answer_text.strip().lower() == word.answer.lower():
            is_correct = True
        else:
            is_correct = False

        if is_correct:
            word.increment()
        else:
            word.decrement()
        word.update_due_date()
        return word, is_correct, answer_text


def _change_question(question):
    return question.replace("___", "dash")


def _say_question(word, sleepseconds=0.0):
    process = Process(target=_say_question_inner,
                      args=(word, sleepseconds,), daemon=True)
    process.start()


def _say_question_inner(word, sleepseconds=0.0):
    print("\n{} : ".format(word), end="")
    question = _change_question(word)
    # _say(question, sleepseconds)
    _say("The Question is {}".format(question), sleepseconds=sleepseconds)


def do_review(wordslist):
    np.random.shuffle(wordslist)
    words_done = []
    total_correct = 0
    total_incorrect = 0
    while True:
        if not wordslist:
            break
        print(Fore.CYAN+"\n{0} Questions to go. ".format(len(wordslist)))
        word = np.random.choice(wordslist)
        word_, is_correct, ans = do_review_one(word)
        if is_correct:
            wordslist.remove(word)
            total_correct += 1
            print(Fore.YELLOW+'Correct')
            _say(np.random.choice(CORRECT_RES))
        else:
            total_incorrect += 1
            correct_word = word.answer
            print(Fore.RED+'Incorrect. The Answer is : %s' %
                  correct_word.upper())
            _say("{}. You wrote {}".format(np.random.choice(INCORRECT_RES), ans))
            _say("The Correct Answer is : ")
            _say(correct_word)
        words_done.append(word_)

    _say("You answered {} words correctly and {} words incorrectly".format(
        total_correct, total_incorrect))
    return words_done


def get_words(fname="words.csv"):
    if os.path.exists(fname):
        df = pd.read_csv(fname, infer_datetime_format=True,
                         parse_dates=["due_date"])
        df = df.sort_values(by="due_date", ascending=False)
        wordlists = [Card(row.question, row.answer,  num=row.num,
                          due_date=row.due_date, active=row.active) for _, row in df.iterrows()]
    else:
        wordlists = []
    return wordlists


def save_words(wordslist, fname="words.csv"):
    pd.DataFrame(data=[(word.question, word.answer, word.due_date, word.num, word.active)
                       for word in wordslist], columns=["question", "answer", "due_date", "num", "active"]).to_csv(fname)


def add_com(args):
   wordslist = get_words(args.word_file)
   word = Card(args.q, args.ans)
   wordslist.append(word)
   save_words(wordslist, args.word_file)
   print("Question {0} added to {1}".format(args.q, args.word_file))


def _get_next_review_day(fname):
    df = pd.read_csv(fname, infer_datetime_format=True,
                     parse_dates=["due_date"])
    next_due_date = df[df.num != 0].sort_values(by="due_date").iloc[0, 3]
    return next_due_date


def print_next_review_day(fname):
    next_due_date = _get_next_review_day(fname)
    text_msg = "Next review in {}".format(
        format_timedelta(next_due_date-datetime.now()))
    print(text_msg)
    if "-" not in text_msg:
        _say(text_msg)
    else:
        _say("Next Review is Now.")
        review_words(fname)


def study_com(args):
    wordslist = get_words(args.word_file)
    selected_word = [word for word in wordslist if word.active is False]
    if selected_word:
        for word in selected_word[:args.nwords]:
            word.active = True
            word.due_data = datetime.now()+timedelta(seconds=600)
            question = _change_question(word.question)
            print("\n", word.question)
            _say(question, 3)
            print("\t\t", word.answer.upper())
            _say(word.answer, 2)
        save_words(wordslist, args.word_file)


def review_words(word_file):
    
    wordslist = get_words(word_file)
    sel_words = get_words_to_reveiw(wordslist)
    if sel_words:
        try:
            words_done = do_review(sel_words)
            save_words(wordslist, word_file)
            check_next_active(word_file)
        except Exception as ex:
            print(ex)
            save_words(wordslist, word_file)
            raise

        print_next_review_day(word_file)
    else:
        check_next_active(word_file)
        print_next_review_day(word_file)


def review_com(args):
    review_words(args.word_file)

def import_com(args):
    data = pd.read_csv(args.text_file, header=None)
    wordslist = get_words(args.word_file)
    for row in data.iterrows():
        word = Card(row[1][0].strip(), row[1][1].strip())
        wordslist.append(word)
    save_words(wordslist, args.word_file)
    print("Question in {} imported into {} ".format(
        args.text_file, args.word_file))


def do_test_one(word):
    while True:
        # _say_question(word.question)
        print("\n{} : ".format(word.question), end="")
        answer_text = ask("")
        if answer_text.strip().lower() == word.answer.lower():
            is_correct = True
        else:
            is_correct = False

        if is_correct:
            word.active = False
        else:
            word.active = True
        return word, is_correct, answer_text

def get_unique_words(wordslist, test_words):
     wl = [word.question for word in wordslist]
     tw = [word for word in test_words if word.question not in wl]
     if len(tw) > 12:
         tw = np.random.choice(tw, size=10, replace=False)
     wordslist.extend(tw)
     return wordslist

def get_test_words(test_file, files, n_words):
    test_words = get_words(test_file)

    # remove last correct words
    for word in test_words:
        if not word.active:
            test_words.remove(word)

    wl = []
    for afile in files:
        wordslist = get_words(afile)
        sl = np.random.choice(wordslist, size=n_words, replace=False)
        wl.extend(sl)
    test_words = get_unique_words(wl, test_words)
    print("{} words selected for test".format(len(test_words)))
    return test_words


def _print_words(ic_words):
    print(Fore.MAGENTA+"Results:\n")
    for ic in ic_words:
        print(Fore.CYAN+ic[0].question, Fore.RED +
                ic[1], Fore.GREEN+ic[0].answer)

def print_correction(ic_words):
    _print_words(ic_words)
    date_time = datetime.now().strftime("%m_%d_%Y_%H_%M_%S")
    data = [(ic[0].question, ic[0].answer, ic[1]) for ic in ic_words]
    fname = os.path.join(os.path.expanduser(
        "~"), "FILL_IN_RESULTS_{}.csv".format(date_time))
    df = pd.DataFrame(data=data, columns=[
                      "Question", "Answer", "UserAnswer"]).to_csv(fname, index=False)


def do_test(test_words):
    correct = 0
    incorrect = 0
    total = len(test_words)
    incorrect_words = []
    save_selected_words = []
    while True:
        if not test_words:
            break
        print(Fore.CYAN+"\n{0} Questions to go. ".format(len(test_words)))
        word = np.random.choice(test_words)
        word_, is_correct, ans = do_test_one(word)
        save_selected_words.append(word_)
        if is_correct:
            correct += 1
            incorrect_words.append([word, ""])
        else:
            incorrect += 1
            if ans == "":
                ans = "____"
            incorrect_words.append([word, ans])
        test_words.remove(word)

    msg1 = "Your score is {} out of {} ".format(correct, total)
    msg2 = "You scored {:.1f} %".format(correct*100/total)
    print(msg1)
    print(msg2)
    _say(msg1)
    _say(msg2)
    print_correction(incorrect_words)
    return save_selected_words


def test_com(args):
    files = args.files
    n_words = args.nwords
    test_words = get_test_words(args.word_file, files, n_words)
    save_selected_words = do_test(test_words)
    save_words(save_selected_words, args.word_file)


def main():
    parser = argparse.ArgumentParser(
        description="Study Revision with Spaced Repetetion for Kids on Mac and windows.")
    subparser = parser.add_subparsers()

    add_p = subparser.add_parser("add")
    add_p.add_argument("word_file", type=str, default="words.csv")
    add_p.add_argument("-q", type=str, help="Question ")
    add_p.add_argument("-ans", type=str, help="Answer here")
    add_p.set_defaults(func=add_com)

    import_p = subparser.add_parser("import")
    import_p.add_argument("word_file", type=str, default="words.csv",
                          help="Where you want to add questions")
    import_p.add_argument(
        "text_file", type=str, help="File with question and answers per line seperated by , use ___ as blank  ")
    import_p.set_defaults(func=import_com)

    review_p = subparser.add_parser("review")
    review_p.add_argument("word_file", type=str, default="words.csv")
    review_p.set_defaults(func=review_com)

    study_p = subparser.add_parser("study")
    study_p.add_argument("word_file", type=str, default="words.csv")
    study_p.add_argument("-n", "--nwords", type=int, default=10)
    study_p.set_defaults(func=study_com)

    getno_p = subparser.add_parser("notify")
    getno_p.add_argument("word_file", type=str, default="words.csv")
    getno_p.set_defaults(func=get_no_of_words)

    test_p = subparser.add_parser("test")
    test_p.add_argument("word_file", type=str, default="test.csv")
    test_p.add_argument("files", type=str, nargs="*")
    test_p.add_argument("-n", "--nwords", type=int,
                        default=5, help="Words from each file")
    test_p.set_defaults(func=test_com)


    args = parser.parse_args()
    # print(args)
    args.func(args)


if __name__ == "__main__":
    sys.exit(main())
