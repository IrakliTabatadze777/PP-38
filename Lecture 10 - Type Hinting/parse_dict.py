school = {
    "კლასი 10A": {
        "გიორგი": {
            "ასაკი": 16,
            "საშუალო_ქულა": 8.7,
            "საგნები": {
                "მათემატიკა": {"ქულა": 9, "გამოცდა": True},
                "ფიზიკა": {"ქულა": 8, "გამოცდა": False},
                "ისტორია": {"ქულა": 9, "გამოცდა": True},
                "ინგლისური": {"ქულა": 10, "გამოცდა": True}
            },
            "დასწრება": 92,
            "დამატებითი": ["ფეხბურთი", "პროგრამირება"]
        },
        "ანა": {
            "ასაკი": 15,
            "საშუალო_ქულა": 9.4,
            "საგნები": {
                "მათემატიკა": {"ქულა": 10, "გამოცდა": True},
                "ფიზიკა": {"ქულა": 9, "გამოცდა": True},
                "ისტორია": {"ქულა": 8, "გამოცდა": False},
                "ინგლისური": {"ქულა": 10, "გამოცდა": True}
            },
            "დასწრება": 98,
            "დამატებითი": ["ცეკვა"]
        },
        "დავით": {
            "ასაკი": 16,
            "საშუალო_ქულა": 7.2,
            "საგნები": {
                "მათემატიკა": {"ქულა": 6, "გამოცდა": False},
                "ფიზიკა": {"ქულა": 7, "გამოცდა": True},
                "ისტორია": {"ქულა": 8, "გამოცდა": True},
                "ინგლისური": {"ქულა": 9, "გამოცდა": False}
            },
            "დასწრება": 75,
            "დამატებითი": ["კალათბურთი", "პროგრამირება"]
        }
    },

    "კლასი 10B": {
        "მარიამ": {
            "ასაკი": 15,
            "საშუალო_ქულა": 9.1,
            "საგნები": {
                "მათემატიკა": {"ქულა": 9, "გამოცდა": True},
                "ბიოლოგია": {"ქულა": 10, "გამოცდა": True}
            },
            "დასწრება": 95,
            "დამატებითი": ["მუსიკა", "ხატვა"]
        },
        "ლევან": {
            "ასაკი": 16,
            "საშუალო_ქულა": 6.8,
            "საგნები": {
                "მათემატიკა": {"ქულა": 5, "გამოცდა": False},
                "ფიზიკა": {"ქულა": 7, "გამოცდა": False}
            },
            "დასწრება": 60,
            "დამატებითი": []
        }
    }
}


# 1. დაბეჭდე ყველა სტუდენტის სახელი და მისი საშუალო ქულა.
for class_name, students in school.items():
    # print(class_name, end='\t')
    # print(students)
    for student_name, student_rec in students.items():
        # print(student_name, end='\t')
        # print(student_rec)
        print(student_name, student_rec['საშუალო_ქულა'])



# 2. იპოვე საუკეთესო სტუდენტი სკოლაში (ყველაზე მაღალი საშუალო ქულით).

best_student = None
best_score = None

for class_name, students in school.items():
    # print(class_name, students)

    for student_name, student_rec in students.items():
        print(student_name, student_rec)
        current_score = student_rec['საშუალო_ქულა']

        if best_score is None or best_score < current_score:
            best_student = student_name
            best_score = current_score


if best_student is None or best_score is None:
    print('There is no records')
else:
    print(best_student, best_score)




# 3. დაბეჭდე ყველა სტუდენტი, რომლებსაც აქვთ დასწრება 90%-ზე მეტი.
for class_name, students in school.items():
    for student_name, student_rec in students.items():
        # print(student_name, student_rec)
        attendance = student_rec['დასწრება']

        if attendance < 90:
            continue

        print(student_name, attendance)


