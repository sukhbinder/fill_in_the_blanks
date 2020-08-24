import pandas as pd
import numpy as np
import argparse
import os
import time
import six

from datetime import datetime, timedelta

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


CORRECT_RES = ["Thats Correct", "Correct", "Thats right. Way to go.", "Good Job.", "Excellent", "Thats correct. Good Effort"]

def get_words_to_reveiw(wordlist):
    now = datetime.now()
    selected_word = [word for word in wordlist if word.due_date < now]
    if not selected_word:
        print("Nothing to review.")
        _say("Nothing to review.")
    return selected_word

THESHOLDS = [timedelta(seconds=0), timedelta(hours=1), timedelta(hours=3), timedelta(hours=7), timedelta(hours=24) , timedelta(days=2), timedelta(days=3), timedelta(days=7), timedelta(days=14), timedelta(days=30), timedelta(days=90)]



class Card:
    def __init__(self, question, answer,  num=0, due_date=datetime.now(), active=True):
        self.question = question
        self.answer = answer
        self.num = num
        self.due_date = due_date
        self.active = active

    
    def increment(self):
        if self.num < len(THESHOLDS):
            self.num = self.num + 1
        else:
            self.num = len(THESHOLDS)

    def decrement(self):
        if self.num >= 0:
            self.num = self.num - 1
        else:
            self.num = 0
    
    def update_due_date(self):
        try:
            self.due_date = datetime.now() + THESHOLDS[self.num]
        except Exception as ex:
            self.due_date = datetime.now() + THESHOLDS[self.num-1]
    
    def __repr__(self):
        return "{0} {1} {2} {3}".format(self.question, self.num, self.active, self.due_date)
    


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
        print("Answer: ")
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



def _say_question(word,sleepseconds=0.0):
    _say(word, sleepseconds)
    _say("The Question is {}".format(word), sleepseconds=sleepseconds)
            
def do_review(wordslist):
    np.random.shuffle(wordslist)
    words_done = []
    while True:
        if not wordslist:
            break
        print("\n{0} Questions to go. ".format(len(wordslist)))
        word = np.random.choice(wordslist)
        word_, is_correct, ans = do_review_one(word)
        if is_correct:
            wordslist.remove(word)
            print('Correct')
            _say(np.random.choice(CORRECT_RES))
        else:
            correct_word = word.answer
            print('Incorrect. The Answer is : %s' % correct_word.upper())
            _say("Incorrect. You wrote {}".format(ans))
            _say("The Correct Answer is : ")
            _say(correct_word)
        words_done.append(word_)
    
    return words_done

def get_words(fname="words.csv"):
    if os.path.exists(fname):
        df = pd.read_csv(fname, infer_datetime_format=True, parse_dates=["due_date"])
        wordlists = [Card(row.question, row.answer,  num=row.num, due_date=row.due_date, active=row.active) for _, row in df.iterrows()]
    else:
        wordlists=[]
    return wordlists


def save_words(wordslist, fname="words.csv"):
    pd.DataFrame(data=[(word.question, word.answer, word.due_date, word.num, word.active) for word in wordslist], columns=["question", "answer", "due_date","num","active"]).to_csv(fname)

def add_com(args):
   wordslist = get_words(args.word_file)
   word = Card(args.q, args.ans)
   wordslist.append(word)
   save_words(wordslist, args.word_file)
   print("Question {0} added to {1}".format(args.q,args.word_file))

def print_next_review_day(fname):
    df = pd.read_csv(fname, infer_datetime_format=True, parse_dates=["due_date"])
    next_due_date = df.sort_values(by="due_date").iloc[0,3]  
    text_msg = "Next review in {}".format(format_timedelta(next_due_date-datetime.now()))
    print(text_msg)
    _say(text_msg)

def review_com(args):
    wordslist = get_words(args.word_file)
    sel_words = get_words_to_reveiw(wordslist)
    if sel_words:
        try:
            words_done = do_review(sel_words)
            save_words(wordslist, args.word_file)
        except Exception as ex:
            print(ex)
            save_words(wordslist, args.word_file)
            raise
        print_next_review_day(args.word_file)
    else:
        print_next_review_day(args.word_file)

def import_com(args):
    data = pd.read_csv(args.text_file, header=None)
    wordslist = get_words(args.word_file)

    for row in data.iterrows():
        word = Card(row[1][0].strip(), row[1][1].strip())
        wordslist.append(word)
    save_words(wordslist, args.word_file)
    print("Question in {} imported into {} ".format(args.text_file, args.word_file))


def main():
    parser = argparse.ArgumentParser(description="Study Revision with Spaced Repetetion for Kids on Mac and windows.")
    subparser = parser.add_subparsers()
    
    add_p = subparser.add_parser("add")
    add_p.add_argument("word_file", type=str, default="words.csv")
    add_p.add_argument("-q", type=str, help="Question ")
    add_p.add_argument("-ans", type=str, help ="Answer here")
    add_p.set_defaults(func=add_com)

    import_p = subparser.add_parser("import")
    import_p.add_argument("word_file", type=str, default="words.csv", help="Where you want to add questions")
    import_p.add_argument("text_file", type=str, help="File with question and answers per line seperated by , use ___ as blank  ")
    import_p.set_defaults(func=import_com)
    
    review_p = subparser.add_parser("review")
    review_p.add_argument("word_file", type=str, default="words.csv")
    review_p.set_defaults(func=review_com)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
  


