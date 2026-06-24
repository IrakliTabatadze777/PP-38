


class CSVParser:
    def __init__(self, filename):
        self.filename = filename

    def parse(self):
        print(f'Parsing CSV: {self.filename}')


class JSONParser:
    def __init__(self, filename):
        self.filename = filename

    def parse(self):
        print(f'Parsing JSON: {self.filename}')



class TXTParser:
    def __init__(self, filename):
        self.filename = filename

    def parse(self):
        print(f'Parsing TXT: {self.filename}')



def parse_data(filename, file_ext):
    file_extensions = {
        'csv': CSVParser,
        'json': JSONParser,
        'txt': TXTParser
    }

    parser_obj = file_extensions.get(file_ext)(filename)
    parser_obj.parse()




if __name__ == '__main__':
    file_name = 'test.txt'
    file_extension = file_name.split('.')[-1]

    parse_data(file_name, file_extension)



