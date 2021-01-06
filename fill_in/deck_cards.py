from datetime import datetime, timedelta
import os
import pandas as pd


# THESHOLDS = [timedelta(seconds=120), timedelta(hours=3), timedelta(hours=7), timedelta(hours=24), timedelta(days=2), timedelta(
#     days=4), timedelta(days=8), timedelta(days=16), timedelta(days=28), timedelta(days=90), timedelta(days=180)]

THESHOLDS = [timedelta(seconds=120), timedelta(hours=8), timedelta(hours=24), timedelta(days=2), timedelta(days=4), timedelta(
    days=8), timedelta(days=16), timedelta(days=28), timedelta(days=90), timedelta(days=180), timedelta(days=300)]

class Card:
    def __init__(self, id, question, answer,  num=0, due_date=datetime.now(), active=False, chapter=1):
        self.id = id
        self.question = question
        self.answer = answer
        self.num = num
        self.due_date = due_date
        self.active = active
        self.chapter = chapter
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

    def toggle_active(self):
        self.active = not self.active

    def reset_date(self, seconds=600):
        self.due_data = datetime.now()+timedelta(seconds=seconds)

    def __repr__(self):
        return "{0} {1} {2} {3} {4} {5}".format(self.id, self.question, self.num, self.chapter, self.active, self.due_date)


class Deck():
    """
    Deck will be a file , with all the cards.
    """
    def __init__(self, fname = "words.csv"):
        self.fname = fname
        self.cards = None
        self.nextid = 0
        self.nextchapter = 1
        self._get_all_cards()

    def _get_words(self):
        nextid = 0
        if os.path.exists(self.fname):
            df = pd.read_csv(self.fname, infer_datetime_format=True,
                            parse_dates=["due_date"], index_col=0)
            df = df.sort_values(by="due_date", ascending=False)
            if "chapter" in df.columns:
                wordlists = [Card(index, row.question, row.answer,  num=row.num,
                                due_date=row.due_date, active=row.active, chapter=row.chapter) for index, row in df.iterrows()]
            else:
                wordlists = [Card(index, row.question, row.answer,  num=row.num,
                                due_date=row.due_date, active=row.active) for index, row in df.iterrows()]

            self._get_nextid(df)
            self._get_nextchapter(df)
        else:
            wordlists = []
        return wordlists

    def _get_nextid(self, df):
        df.sort_values(by="id", inplace=True)
        self.nextid = df.index[-1]+1

    def _get_nextchapter(self, df):

        try:
            df.sort_values(by="chapter", inplace=True)
            self.nextchapter = df.chapter.max()+1
        except KeyError:
            self.nextchapter=1
            self.save()

    def _get_all_cards(self):
        if self.cards is None:
            self.cards = self._get_words()

    def is_time_to_add_words(self):
        next_due_date = self.get_next_review_day()
        seconds_to_next_review = next_due_date-datetime.now()
        # check if the time has past 5 hours
        return seconds_to_next_review.seconds >= 60*60*5

    def check_next_active(self):
        num=2 # add 5 words at a time
        if not self.is_time_to_add_words():
            return
        selected_word = self.get_inactive_cards()
        if len(selected_word) > num:
            selected_word = selected_word[:num]

        for word in selected_word:
            word.toggle_active()
            word.due_data = datetime.now()+timedelta(seconds=600)
        self.save_words(selected_word)
    
    def save(self):
        if self.cards:
            df = pd.DataFrame(data=[(word.id, word.question, word.answer, word.due_date, word.num, word.active, word.chapter)
                       for word in self.cards], columns=["id","question", "answer", "due_date", "num", "active", "chapter"])
            df.sort_values(by="id", inplace=True)
            df.to_csv(self.fname, index=False)
            self._get_nextid(df)
            self._get_nextchapter(df)

    def save_words(self, wordslist):
        for word in wordslist:
            for aword in self.cards:
                if aword.id == word.id:
                    aword.num = word.num
                    aword.update_due_date()
        self.save()

    def get_due_cards(self, chapters=None):
        self._get_all_cards()
        now = datetime.now()
        if chapters is None:
            selected_word = [
                word for word in self.cards if word.due_date < now and word.active]
        else:
            selected_word = [
                word for word in self.cards if word.due_date < now and word.active and word.chapter in chapters]
        if len(selected_word) < 5: # if less than five,check next update
            self.check_next_active()
        return selected_word

    def get_inactive_cards(self):
        self._get_all_cards()
        selected_word = [word for word in self.cards if not word.active]
        return selected_word

    def get_active_cards(self):
        self._get_all_cards()
        selected_word = [word for word in self.cards if word.active]
        return selected_word

    def reload_cards(self):
        self.cards = self._get_words()

    def __repr__(self):
        return "{} deck has {} cards".format(self.fname, len(self.cards))
    
    def _add_card(self, question, answer, active=False, chapter=1):
        card = Card(id = self.nextid, question=question, answer=answer, active=active, chapter=chapter)
        self.nextid = self.nextid + 1
        self.cards.append(card)

    def add_card(self, question, answer, active=False, chapter=1, save=True):
        self._get_all_cards()
        self._add_card(question, answer, active, chapter)
        if save:
            self.save()

    def get_next_review_day(self):
        df = pd.read_csv(self.fname, infer_datetime_format=True, parse_dates=["due_date"], index_col=0)

        if len(df[df.active]) != 0:
            next_due_date = df[df.active].sort_values(by="due_date").iloc[0, 2]
        else:
            print("Please study, no card is active")
            next_due_date = datetime.now()+timedelta(seconds=-120)
        return next_due_date
    
    def import_cards(self, afile, print_msg=True, save=True, chapter=None):
        self._get_all_cards()
        try:
            data = pd.read_csv(afile, header=None)
        except Exception as ex:
            raise

        if chapter is None:
            chapter = self.nextchapter
        
        for row in data.iterrows():
            self._add_card(row[1][0].strip(), row[1][1].strip(), active=False, chapter=chapter)
        if save:
            self.save()
        if print_msg:
            print("{} Question in {} imported into {} ".format( len(data),
                    afile, self.fname))

if __name__ == "__main__":
    deck = Deck("a.csv")
    sl = deck.get_due_cards()
    print(sl)