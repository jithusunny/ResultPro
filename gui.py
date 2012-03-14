#!/usr/bin/env python

import re
from urllib import urlopen
import sys, serial
from PyQt4.QtGui import *
from PyQt4.QtCore import *


def parse(string):
    '''Parses the HTML code and returns plain text'''
    string = re.sub(r'<.*?>|\n|[A-Z]+[0-9]+', '', string)
    string = re.sub(r'\t{1,6}', ' ', string)
    string = re.sub(r'.*Status|P : Passed.*', '', string)
    string = re.sub(r' {2,}', ' ', string)
    string = string.strip()
    return string

def failed(string):
    '''Returns true if student has failed in atleast one subject. False is returned otherwise.'''
    return re.search(r' F |F$', string)
 
def subject_string_match(string):
    '''Returns the first subject string in the input string.'''
    substr = re.search(r'([a-zA-Z-&] *)+([0-9-] *)+ [PF]', string)
    return substr

def stripA(string):
    '''Returns the string after deletion of 'A' from the end if presnt'''
    string = string.rstrip(' A ')
    string = string.rstrip(' A')
    string = string.strip()
    return string

def filter_subjects(string):
    '''Returns the dictionary - key: subject; value: 0.'''
    sub_dict = {}
    while string:
        string = string.strip()
        substring = subject_string_match(string).group()
        sub = re.search(r'([a-zA-Z-&] *)+', substring).group().strip()
        sub = stripA(sub)
        sub_dict[sub] = 0
        string = string[len(substring):]
    return sub_dict

def no_result(string):
    '''Returns true if the particular string contains label 'withheld'/'Withheld'''
    return re.search(r'withheld|Withheld|invalid|not registered', string)


def num_of_digits_roll(string):
    '''Return the number of digits in roll number.'''
    roll = re.search(r'(?<=regno=)[A-Za-z0-9]+', string).group()
    num = re.search(r'[0-9]+', roll).group()
    return len(num)

def subtotal(string):
    '''Returns the subject-total, ie the last number(before the symbol 'P') in input subject line.'''
    subtot = re.search(r'[0-9]+ P', string).group().split()[0]
    return int(subtot)

def process_result(param_list, progress_bar):

    #Declarations of variables and data structures used.
    failed_students = 0
    flag = False
    topper = [0] * 3
    #url = raw_input('Enter the url of result page of first(any) student from university website: ')
    #total = int(raw_input('Enter the total marks: '))
    #students = int(raw_input('Enter the total number of students: '))
    
    url = str(param_list[0])
    students = int(param_list[1])
    total = int(param_list[2])

    individual_total = [0] * (students + 1)
    effective_students = students
    perc_above_80 = 0
    perc_above_75 = 0
    perc_60_to_75 = 0
    perc_below_60 = 0

    roll_prefix = re.search(r'(?<=regno=)[a-zA-Z]+', url).group()
    url_prefix = re.search(r'.*?regno=', url).group()

    res_file = open(roll_prefix, 'w')

    #Populates the subject-dictionary.
    page = urlopen(url).read()
    result_string = parse(page)
    subject_dict = filter_subjects(result_string)
    zero_num = num_of_digits_roll(url) - 1

    test = open('chumma', 'w')
    test.write(param_list[0])
    test.close()

    res_file.write('Roll number\tTotal\tPercentage')
    res_file.write( '\n----------- \t----- \t----------\n')
    #Does the calculation of pass-status, per-subject-pass-status & total of each student.
    for i in range(1, students + 1):
    
        progress_bar.setValue(progress_bar.value() + 1)
        print "student", i
        if i < 10:
            roll = roll_prefix + zero_num * '0' + str(i)
        elif i < 100:
            roll = roll_prefix + (zero_num - 1) * '0' + str(i)
        else:
            roll = roll_prefix + (zero_num - 2) * '0' + str(i)
        fail = False
        page = urlopen(url_prefix + roll + '&Submit=Submit').read()
        result_string = parse(page)

        if no_result(result_string):
            effective_students -= 1
        if failed(result_string):
            fail = True
            failed_students += 1

        sub = subject_string_match(result_string)
        while(sub):
            subject_line=sub.group()
            subject = re.search(r'([a-zA-Z-&] *)+', subject_line).group().strip()
            subject = stripA(subject)

            if failed(subject_line):
                subject_dict[subject] += 1
            if not fail:
                individual_total[i] += subtotal(subject_line)

            result_string = result_string[len(subject_line):].strip()
            sub = subject_string_match(result_string)
 
        if individual_total[i] > topper[1]:
            topper[0] = roll
            topper[1] = individual_total[i]

        if individual_total[i]:
            res_file.write(str(roll) + '\t ' + str(individual_total[i]) + '\t  ' + '%.2f\n' %(float(individual_total[i])/total*100))

            temp = float(individual_total[i])/total * 100
            if temp >= 80:
                perc_above_80 += 1
            if temp >= 75:
                perc_above_75 += 1
            if temp >= 60 and temp < 75:
                perc_60_to_75 += 1
            if temp < 60:
                perc_below_60 += 1
        

    res_file.write( '\nTopper of the class is:' + topper[0] + '- Marks: ' + str(topper[1]) + ' Percentage: %.2f' %(float(topper[1])/total * 100))

    res_file.write( '\n\nNo.of students with percentage above 80%: ' + str(perc_above_80))
    res_file.write( '\nNo.of students with percentage above 75%: ' + str(perc_above_75))
    res_file.write( '\nNo.of students with percentage in between 60% and 75%: ' + str(perc_60_to_75))
    res_file.write( '\nNo.of students with percentage below 60%: ' + str(perc_below_60))

    res_file.write( '\nClass Pass Percentage: %.4f(%d out of %d Students)\n' %(float(effective_students-failed_students)/effective_students*100, effective_students-failed_students, effective_students))

    for subject in subject_dict:
        res_file.write( '\nPass Percentage in' + subject + "is: %.4f" %(float(effective_students-subject_dict[subject])/effective_students*100))
    res_file.write('\n')

class Window(QWidget):

    def __init__(self, args):
        """ In the constructor we're doing everything to get our application
            started, which is basically constructing a basic QApplication by 
            its __init__ method, then adding our widgets and finally starting 
            the exec_loop."""
        QApplication.__init__(self, args)
        self.addWidgets()
    
    def start(self):
        self.p_bar.setVisible(True)
       
        self.process_result()
        print 'over'

    def __init__(self):
        QWidget.__init__(self, parent = None)

        #Component creation
        self.start_Button = QPushButton("Start")
       
        self.URL_Label = QLabel("URL of a result page:")
        self.Strength_Label = QLabel("Strength of batch:")
        self.Total_Label = QLabel("Total Marks:")

        self.URL_Input = QLineEdit()
        self.Strength_Input = QLineEdit()
        self.Total_Input = QLineEdit()
        
        self.p_bar = QProgressBar()
        self.p_bar.setVisible(False)

        #Action
        self.connect(self.start_Button, SIGNAL("clicked()"), self.start)

        #Layout Setting
        grid = QGridLayout()
        grid.setSpacing(10)

        grid.addWidget(self.URL_Label, 1, 1)
        grid.addWidget(self.URL_Input, 1, 2)
        grid.addWidget(self.Strength_Label, 2, 1)
        grid.addWidget(self.Strength_Input, 2, 2)
        grid.addWidget(self.Total_Label, 3, 1)
        grid.addWidget(self.Total_Input, 3, 2)

        vbox = QVBoxLayout()
        vbox.addLayout(grid)
        vbox.addWidget(self.start_Button)
        vbox.addWidget(self.p_bar)

        self.setLayout(vbox)

        #Centering the window
        screen = QDesktopWidget().screenGeometry()
        mysize = self.geometry()
        hpos = ( screen.width() - mysize.width() ) / 2
        vpos = ( screen.height() - mysize.height() ) / 2
        self.move(hpos, vpos)  
        self.resize(300, 350)
        
        
    def process_result(self):
        #Declarations of variables and data structures used.
        failed_students = 0
        flag = False
        topper = [0] * 3
        #url = raw_input('Enter the url of result page of first(any) student from university website: ')
        #total = int(raw_input('Enter the total marks: '))
        #students = int(raw_input('Enter the total number of students: '))
    
        url = str(self.URL_Input.text())
        students = int(self.Strength_Input.text())
        total = int(self.Total_Input.text())

        individual_total = [0] * (students + 1)
        effective_students = students
        perc_above_80 = 0
        perc_above_75 = 0
        perc_60_to_75 = 0
        perc_below_60 = 0

        roll_prefix = re.search(r'(?<=regno=)[a-zA-Z]+', url).group()
        url_prefix = re.search(r'.*?regno=', url).group()
    
        res_file = open(roll_prefix, 'w')

        #Populates the subject-dictionary.
        page = urlopen(url).read()
        result_string = parse(page)
        subject_dict = filter_subjects(result_string)
        zero_num = num_of_digits_roll(url) - 1

        res_file.write('Roll number\tTotal\tPercentage')
        res_file.write( '\n----------- \t----- \t----------\n')
        #Does the calculation of pass-status, per-subject-pass-status & total of each student.
        for i in range(1, students + 1):
    
            self.p_bar.setValue(self.p_bar.value() + 1)
            print "student", i
            if i < 10:
                roll = roll_prefix + zero_num * '0' + str(i)
            elif i < 100:
                roll = roll_prefix + (zero_num - 1) * '0' + str(i)
            else:
                roll = roll_prefix + (zero_num - 2) * '0' + str(i)
            fail = False
            page = urlopen(url_prefix + roll + '&Submit=Submit').read()
            result_string = parse(page)

            if no_result(result_string):
               effective_students -= 1
            if failed(result_string):
                fail = True
                failed_students += 1

            sub = subject_string_match(result_string)
            while(sub):
                subject_line=sub.group()
                subject = re.search(r'([a-zA-Z-&] *)+', subject_line).group().strip()
                subject = stripA(subject)

                if failed(subject_line):
                    subject_dict[subject] += 1
                if not fail:
                    individual_total[i] += subtotal(subject_line)

                result_string = result_string[len(subject_line):].strip()
                sub = subject_string_match(result_string)
 
            if individual_total[i] > topper[1]:
                topper[0] = roll
                topper[1] = individual_total[i]

            if individual_total[i]:
                res_file.write(str(roll) + '\t ' + str(individual_total[i]) + '\t  ' + '%.2f\n' %(float(individual_total[i])/total*100))

                temp = float(individual_total[i])/total * 100
                if temp >= 80:
                    perc_above_80 += 1
                if temp >= 75:
                    perc_above_75 += 1
                if temp >= 60 and temp < 75:
                    perc_60_to_75 += 1
                if temp < 60:
                    perc_below_60 += 1
        

        res_file.write( '\nTopper of the class is:' + topper[0] + '- Marks: ' + str(topper[1]) + ' Percentage: %.2f' %(float(topper[1])/total * 100))

        res_file.write( '\n\nNo.of students with percentage above 80%: ' + str(perc_above_80))
        res_file.write( '\nNo.of students with percentage above 75%: ' + str(perc_above_75))
        res_file.write( '\nNo.of students with percentage in between 60% and 75%: ' + str(perc_60_to_75))
        res_file.write( '\nNo.of students with percentage below 60%: ' + str(perc_below_60))
    
        res_file.write( '\nClass Pass Percentage: %.4f(%d out of %d Students)\n' %(float(effective_students-failed_students)/effective_students*100, effective_students-failed_students, effective_students))

        for subject in subject_dict:
            res_file.write( '\nPass Percentage in' + subject + "is: %.4f" %(float(effective_students-subject_dict[subject])/effective_students*100))
        res_file.write('\n')

if __name__=="__main__" :
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec_())
   
