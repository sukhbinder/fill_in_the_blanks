
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

from fill_in.util import _say, format_timedelta, ask, notify

from fill_in.deck_cards import Deck


init(autoreset=True)

CORRECT_RES = ["Thats Fantastic Effort", "Wow thats good",
               "Thats right. Way to go.", "Good Job.", "Excellent", "Thats correct. Good Effort",
               "You are acing this life level!",
               "Brain power: engaged and awesome!",
               "Smarty pants in action!",
               "Keep calm and study on.",
               "You are one smart cookie.",
               "You are the real MVP!",
               "Nailed it, Einstein!",
               "Learning ninja mode: activated!",
               "Future genius in training!",
               "School: you are crushing it!",
               "Einstein would be proud!",
               "Knowledge is your superpower!",
               "You are a study rockstar!",
               "Straight As and laughter!",
               "You are writing success stories!"
               ]

INCORRECT_RES = ["Thats Incorrect",
                 "Try Harder", "Focus", "Are you kidding me", "Focus on this",
                 "Oops, textbook tango again?", "Detour from brilliance lane!",
                 "Oopsie-doodle, redo time!", "Brain break? Try later.",
                 "Mission: find lost homework!",
                 "Oops, forgot mind at home?",
                 "Uh-oh, mini meltdown detected!",
                 "Attention: Brain recharge needed!",
                 "Alien abduction excuses? Denied!",
                 "Can not compute, retry please!",
                 "Lost in Daoydreamsville, huh?",
                 "Reality check needed ASAP!",
                 "Note to self: study!",
                 "Lifes pop quiz, failed?",
                 "Unplanned vacation from learning?"]
                 

# TODO Streaks
# Streaks encoragement


def is_time_to_add_words(fname):
    next_due_date = Deck(fname).get_next_review_day()
    seconds_to_next_review = next_due_date-datetime.now()
    # check if the time has past 5 hours
    return seconds_to_next_review.seconds >= 60*60*5


def check_next_active(fname, num=2, chapter=-1):
    if not is_time_to_add_words(fname):
        return
    deck = Deck(fname)
    selected_word = deck.get_inactive_cards(chapter=chapter)
    if len(selected_word) > num:
        selected_word = selected_word[:num]

    for word in selected_word:
        word.toggle_active()
        word.reset_date()
    deck.save_words(selected_word)


def get_no_of_words(args):
    # wordslist = get_words(args.word_file)
    sw = Deck(args.word_file).get_due_cards()
    n_words = len(sw)
    if n_words:
        notify(n_words, args.word_file)


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


def add_com(args):
    """
    Add a single question and answer
    """
    deck = Deck(args.word_file)
    deck.add_card(args.q, args.ans, chapter=args.chapter)
    print("Question {0} added to {1}".format(args.q, args.word_file))


def _get_next_review_day(fname):
    df = pd.read_csv(fname, infer_datetime_format=True,
                     parse_dates=["due_date"])
    next_due_date = df[df.num != 0].sort_values(by="due_date").iloc[0, 3]
    return next_due_date


def print_next_review_day(fname, chapter):
    next_due_date = Deck(fname).get_next_review_day()
    text_msg = "Next review in {}".format(
        format_timedelta(next_due_date-datetime.now()))
    print(text_msg)
    if "-" not in text_msg:
        _say(text_msg)
    else:
        _say("Next Review is Now.")
        review_words(fname, nmax=10, chapter=chapter)


def study_com(args):
    """
    Study command to study n number of words
    """
    deck = Deck(args.word_file)
    # selected_word = [word for word in wordslist if word.active is False]
    selected_word = deck.get_inactive_cards(args.chapter)
    if selected_word:
        for word in selected_word[:args.nwords]:
            word.toggle_active()
            word.reset_date()
            question = _change_question(word.question)
            print("\n", word.question)
            _say(question, 3)
            print("\t\t", word.answer.upper())
            _say(word.answer, 2)
        deck.save_words(selected_word)


def review_words(word_file, nmax=30, chapter=-1):
    deck = Deck(word_file)
    sel_words = deck.get_due_cards(chapter=chapter)
    no_words = len(sel_words)
    # if more than 15 words, show only 10-15 words
    if no_words > nmax:
        sel_words = sel_words[:np.random.randint(int(nmax/2), nmax-1)]
    if sel_words:
        try:
            words_done = do_review(sel_words)
            deck.save_words(words_done)
            check_next_active(word_file, chapter=chapter)
        except Exception as ex:
            print(ex)
            deck.save_words(sel_words)
            raise

        print_next_review_day(word_file, chapter)
    else:
        check_next_active(word_file, chapter=chapter)
        print_next_review_day(word_file, chapter)


def review_com(args):
    review_words(args.word_file, chapter=args.chapter)


def import_com(args):
    deck = Deck(args.word_file)
    deck.import_cards(args.text_file, chapter=args.chapter)


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
    test_words = Deck(test_file).get_active_cards()
    wl = []
    for afile in files:
        wordslist = Deck(afile).cards
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
    deck = Deck(args.word_file)
    deck.save_words(save_selected_words)

def rand_com(args):
    files = args.files
    n_words = args.nwords
    nfiles = len(files) 
    if nfiles>3:
        nfiles = 3 
    randfiles = np.random.choice(files, size=nfiles, replace=False)
    for afile in randfiles:
        review_words(afile, n_words)
        

def main():
    parser = argparse.ArgumentParser(
        description="Study Revision with Spaced Repetetion for Kids on Mac and windows.")
    subparser = parser.add_subparsers()

    add_p = subparser.add_parser("add")
    add_p.add_argument("word_file", type=str, default="words.csv")
    add_p.add_argument("-q", type=str, help="Question ")
    add_p.add_argument("-ans", type=str, help="Answer here")
    add_p.add_argument("-c", "--chapter", type=int, required=True)
    add_p.set_defaults(func=add_com)

    import_p = subparser.add_parser("import")
    import_p.add_argument("word_file", type=str, default="words.csv",
                          help="Where you want to add questions")
    import_p.add_argument(
        "text_file", type=str, help="File with question and answers per line seperated by , use ___ as blank  ")
    import_p.add_argument("-c", "--chapter", type=int,  required=True)
    import_p.set_defaults(func=import_com)

    review_p = subparser.add_parser("review")
    review_p.add_argument("word_file", type=str, default="words.csv")
    review_p.add_argument("-c", "--chapter", type=int, default=-1)
    review_p.set_defaults(func=review_com)

    study_p = subparser.add_parser("study")
    study_p.add_argument("word_file", type=str, default="words.csv")
    study_p.add_argument("-n", "--nwords", type=int, default=10)
    study_p.add_argument("-c", "--chapter", type=int, default=-1)
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

    rand_p = subparser.add_parser("random")
    rand_p.add_argument("files", type=str, nargs="*")
    rand_p.add_argument("-n", "--nwords", type=int,
                        default=10, help="Words from each file")
    rand_p.set_defaults(func=rand_com)

    args = parser.parse_args()
    # print(args)
    args.func(args)


if __name__ == "__main__":
    sys.exit(main())
