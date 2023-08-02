import os
import pandas as pd
import argparse 

from fill_in import app


STUDY_FOLDER=r"/Users/sukhbindersingh/study"

def parse_number_string(number_string):
    result = []
    
    for part in number_string.split(","):
        if "-" in part:
            start, end = part.split("-")
            if len(start) == 0:
                result.append(int(part))
            else:   
                result.extend(range(int(start), int(end) + 1))
        else:
            result.append(int(part))
    
    return result



def get_subjects(sfolder):
    subjects = [file for file in os.listdir(sfolder) if file.lower().endswith(".csv")]
    return subjects

def print_subject(subjects):
    choices=[]
    print("\n\nAvaialve Subjects:")
    for i,val in enumerate(subjects):
        choices.append(i)
        print(i, val)
    return choices


def get_chapters(fname):
    df = pd.read_csv(fname)
    return df.chapter.unique().tolist()

def get_selected_subject(subjects):

    while True:
        choices = print_subject(subjects)
        userin = input("\n\nWhich subject to review (q to exit) :")
        if userin == "q":
            break
        try:
            userin = int(userin)
        except Exception:
            pass
        if userin in choices:
            break
    return userin

# clean_doms = list(set(mlist).intersection(clean_doms))

def get_selected_chaps(chaps):

    while True:
        print("\n\nAvailable Chapters: ", chaps)
        userin = input("\n\nWhich chapters to review (1,2 or 3-5, q to exit) : ")
        if userin == "q":
            break
        try:
            userin = parse_number_string(userin)
        except Exception:
            pass
        userin = list(set(userin).intersection(chaps))
        if userin:
            break
    return userin


def main():
    parser = argparse.ArgumentParser(description="Review app")
    parser.add_argument("-f", "--study_folder", type=str, default=STUDY_FOLDER)

    args = parser.parse_args()

    subs = get_subjects(args.study_folder)
    us = get_selected_subject(subs)
    if us != "q":
        fname = os.path.join(args.study_folder,subs[us])
        chaps = get_chapters(fname)
        userchaps = get_selected_chaps(chaps)
        if userchaps != "q":
            for chapter in userchaps:
                app.review_words(fname, chapter=chapter)
    

if __name__ == "__main__":
    main()