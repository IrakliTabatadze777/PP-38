import json
from datetime import datetime
from dataclasses import dataclass, asdict


########################################################################
# 1. datetime მოდული
########################################################################

# datetime ობიექტის შექმნა ხელით
date_1 = datetime(2026, 6, 8, 20, 6, 30)

# მიმდინარე დრო
date_2 = datetime.now()

print(date_1)
print(date_2)


########################################################################
# 2. JSON და datetime — პრობლემა და გამოსავალი
########################################################################

# პრობლემა: json.dumps() ვერ ამუშავებს datetime ობიექტს პირდაპირ
# გამოსავალი 1: isoformat() — datetime-ს სტრინგად გარდაქმნა

data = {
    'name': 'ირაკლი',
    'age': 22,
    'scores': (95, 92, 93),
    'datetime': datetime.now()
}

# ხელით გადაყვანა სტრინგად
serializable_data = {
    'name': data['name'],
    'age': data['age'],
    'scores': data['scores'],
    'datetime': data['datetime'].isoformat()
}

print(serializable_data)


########################################################################
# 3. CustomEncoder — ავტომატური გადაყვანა
########################################################################

# გამოსავალი 2: JSONEncoder-ის გაფართოება
# cls=CustomEncoder-ს გადაეცემა json.dumps()-ს, და ავტომატურად
# გაუმკლავდება datetime ობიექტებს

class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


json_str = json.dumps(data, indent=4, sort_keys=True, ensure_ascii=False, cls=CustomEncoder)
print(json_str)


########################################################################
# 4. object_hook — JSON-დან Python-ის ობიექტების აღდგენა
########################################################################

# json.loads()-ს object_hook პარამეტრი გამოიძახება ყოველ dictionary-ზე
# და შეუძლია სტრინგი "2026-06-08T..." უკან datetime-ად გადაიყვანოს

def decode_types(obj: dict):
    for key, value in obj.items():
        if isinstance(value, str):
            try:
                obj[key] = datetime.fromisoformat(value)
            except ValueError:
                pass  # თუ სტრინგი datetime არ არის, ისე დარჩება
    return obj


json_str_example = '{"age": 22, "datetime": "2026-06-08T20:36:14.884562", "name": "ირაკლი", "scores": [95, 92, 93]}'

try:
    python_data = json.loads(json_str_example, object_hook=decode_types)
    print(python_data)
except json.JSONDecodeError as e:
    print(f"JSON შეცდომა: {e}")


########################################################################
# 5. JSON ფაილში ჩაწერა და წაკითხვა
########################################################################


with open('data.json', 'w', encoding='utf-8') as file:
    json.dump(serializable_data, file, ensure_ascii=False, indent=4)


with open('data.json', 'r', encoding='utf-8') as file:
    loaded_data = json.load(file)
    print(loaded_data)


########################################################################
# 6. კლასი + JSON — to_dict / from_dict
########################################################################

# ჩვეულებრივი კლასი JSON-თან სამუშაოდ:
# - to_dict()    -> Python ობიექტი -> dictionary -> JSON
# - from_dict()  -> JSON -> dictionary -> Python ობიექტი

class Student:
    def __init__(self, name, grade, score):
        self.name = name
        self.grade = grade
        self.score = score

    def to_dict(self):
        return {'name': self.name, 'grade': self.grade, 'score': self.score}

    @classmethod
    def from_dict(cls, d):
        return cls(name=d['name'], grade=d['grade'], score=d['score'])

    def __repr__(self):
        return f"Student(name={self.name!r}, grade={self.grade!r}, score={self.score})"


stud = Student('John', 'A', 100)

# სერიალიზაცია (Python -> JSON)
json_data = json.dumps(stud.to_dict())
print(json_data)

# დესერიალიზაცია (JSON -> Python)
# ორი გზა — შედეგი იგივეა:
restored_1 = Student.from_dict(json.loads(json_data))
restored_2 = json.loads(json_data, object_hook=Student.from_dict)

print(restored_1)
print(restored_2)


########################################################################
# 7. @dataclass + asdict() — თანამედროვე მიდგომა
########################################################################

# @dataclass ავტომატურად წერს __init__ და __repr__
# asdict() -> dataclass ობიექტი -> dictionary (ჩადგმულებიანაც!)

@dataclass
class Address:
    street: str
    city: str
    country: str = "GE"


@dataclass
class Student:
    name: str
    grade: str
    score: int
    address: Address  # ჩადგმული dataclass


addr = Address('Rustaveli Ave', 'Tbilisi')
stud = Student('John', 'A', 95, addr)

print(stud)

# asdict() ავტომატურად ამუშავებს ჩადგმულ ობიექტებსაც
stud_dict = asdict(stud)
print(stud_dict)

json_data = json.dumps(stud_dict, ensure_ascii=False)
print(json_data)


########################################################################
# 8. @dataclass — დესერიალიზაცია (JSON -> ობიექტი)
########################################################################

# პრობლემა: Student(**python_data) ვერ მუშაობს,
# რადგან address dictionary-ა, Address ობიექტი კი — არა.
# გამოსავალი: address ცალკე გადავიყვანოთ Address-ად.

python_data = json.loads(json_data)

restored = Student(
    **{k: v for k, v in python_data.items() if k != 'address'},
    address=Address(**python_data['address'])
)

print(restored)
