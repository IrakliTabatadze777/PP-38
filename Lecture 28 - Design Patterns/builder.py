class Report:
    def __init__(self):
        self.title = "Untitled"
        self.author = "Unknown"
        self.page_numbers = False
        self.font_size = 12
        self.orientation = "portrait"
        self.sections = []

    def __repr__(self):
        return (
            f"Report(title={self.title!r}, author={self.author!r}, "
            f"pages={self.page_numbers}, font={self.font_size}pt, "
            f"orientation={self.orientation}, sections={self.sections})"
        )



class ReportBuilder:
    def __init__(self):
        self._report = Report()

    def title(self, title):
        self._report.title = title
        return self

    def author(self, author):
        self._report.author = author
        return self

    def page_numbers(self, page_numbers):
        self._report.page_numbers = page_numbers
        return self

    def font_size(self, font_size):
        self._report.font_size = font_size
        return self

    def sections(self, sections):
        self._report.sections = sections
        return self


    def build(self):
        return self._report


# report_builder = ReportBuilder()
#
# report_builder.title('Some Title').author('Some Author').font_size(16)
# report = report_builder.build()
# print(report)




class Student:
    def __init__(self, fname, lname):
        self.fname = fname
        self.lname = lname
        self.subjects = []


    def return_name(self):
        return self.fname

    def return_lname(self):
        return self.lname

    def enroll(self, subject):
        self.subjects.append(subject)
        return self

    def show(self):
        return f'{self.fname} {self.lname}, {self.subjects} subject(s)'



student = Student("John", "Doe")

student.enroll('Python').enroll('Java').enroll('C++')

print(student.show())
