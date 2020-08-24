# Fill In the Blanks 
Spaced revision of Questions in the form of fill in the blanks for kids

Works in windows and Mac.


#  How to use

```bash

fillin -h

Study Revision with Spaced Repetetion for Kids on Mac and windows.

positional arguments:
  {add,review, import}

optional arguments:
  -h, --help    show this help message and exit

```

# To add Questions in bulk

Create a text file like the following


``ques.txt``
```text
___ barks?,dog
___ mewes?,cat
Are you a _____? ,human

```

And then use this command import the questions.

```bash

fillin import science.csv quest.txt

```
All questions will be stored in ``science.csv`` with the above command.

**Tip**: Try to keep one or two word answer. Not more than that. Use ``___``  (triple underscore ) for the blanks?


# To add single Question for your child

```bash

fillin add  barun.csv -q "____ is the highest mountain in the world" -a "mt. everest"

```
All questions will be stored in ``barun.csv`` for the above command.

**Tip**: Try to keep one or two word answer. Not more than that.



# To Review.

```bash

fillin review barun.csv

```

``barun.csv`` is the file tat all questions have been added.

**Tip**: Create a batch file, so the kid can just click on the batch file and practice the questions if any.


