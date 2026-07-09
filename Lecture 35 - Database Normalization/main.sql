create table students(
	id serial primary key,
	name varchar(20) not null,
	email varchar(70) unique
);


create table courses(
	id serial primary key,
	name varchar(20) not null,
	lecturer_name varchar(20),
	lecture_room varchar(20)
);


create table enrollment(
	id serial primary key,
	student_id integer not null,
	course_id integer not null,
	enroll_date timestamp default now()
);


insert into students(name, email) values('Irakli', 'irakli@gmail.com'),
('Ana', 'ana@gmail.com'),
('Nutsa', 'nutsa@gmail.com');


insert into courses(name, lecturer_name, lecture_room) values('Python1', 'Dr. Lomidze', 'Room 204'),
('Java1', 'Dr. Beridze', 'Room 210');


-- ამატებს სტუდენტების კურსებზე ჩარიცხვის ინფორმაციას
-- სტუდენტი id=1 ჩაირიცხა ორ კურსზე
-- სტუდენტი id=2 ჩაირიცხა ერთ კურსზე
insert into enrollment(student_id, course_id) values(1, 1), (1, 2), (2, 1);



-- INNER JOIN აბრუნებს მხოლოდ იმ სტუდენტებს,
-- რომლებსაც აქვთ შესაბამისი ჩანაწერი enrollment ცხრილში
-- ანუ სტუდენტები კურსზე ჩარიცხვის გარეშე არ გამოჩნდებიან
select students.id, students.name, students.email, enrollment.course_id, enrollment.enroll_date
from students
	inner join enrollment on students.id = enrollment.student_id;



-- LEFT JOIN აბრუნებს ყველა სტუდენტს students ცხრილიდან
-- თუ სტუდენტს არ აქვს ჩარიცხვა, enrollment ცხრილის ველები იქნება NULL
select students.id, students.name, students.email, enrollment.course_id, enrollment.enroll_date
from students
	left join enrollment on students.id = enrollment.student_id;



-- RIGHT JOIN აბრუნებს ყველა ჩანაწერს enrollment ცხრილიდან
-- თუ enrollment-ში არის სტუდენტი, რომელიც students ცხრილში არ არსებობს,
-- მისი ინფორმაცია მაინც გამოჩნდება NULL მნიშვნელობებით
select students.id, students.name, students.email, enrollment.course_id, enrollment.enroll_date
from students
	right join enrollment on students.id = enrollment.student_id;



-- FULL OUTER JOIN აბრუნებს ორივე ცხრილის ყველა ჩანაწერს
-- გამოჩნდება როგორც სტუდენტები ჩარიცხვის გარეშე,
-- ასევე enrollment ჩანაწერები შესაბამისი სტუდენტის გარეშე
select students.id, students.name, students.email, enrollment.course_id, enrollment.enroll_date
from students
	full outer join enrollment on students.id = enrollment.student_id;



-- აკეთებს რამდენიმე ცხრილის გაერთიანებას
-- აერთიანებს:
-- students -> enrollment -> courses
-- შედეგად ვიღებთ სტუდენტის სრულ ინფორმაციას და მის კურსებს
select
	students.id,
	students.name,
	students.email,
	enrollment.course_id,
	enrollment.enroll_date,
	courses.name,
	courses.lecturer_name
from students
	inner join enrollment on students.id = enrollment.student_id
	inner join courses on courses.id = enrollment.course_id;



-- აერთიანებს სამ ცხრილს LEFT JOIN-ის გამოყენებით
-- აბრუნებს ყველა სტუდენტს და მათ კურსებს
-- WHERE პირობა ფილტრავს შედეგებს და ტოვებს მხოლოდ იმ ჩანაწერებს,
-- სადაც კურსის id არის 1
select
	students.id,
	students.name,
	students.email,
	enrollment.course_id,
	enrollment.enroll_date,
	courses.name,
	courses.lecturer_name
from students
	left join enrollment on students.id = enrollment.student_id
	left join courses on courses.id = enrollment.course_id
where courses.id = 1;



-- ამატებს foreign key შეზღუდვას enrollment ცხრილში
-- student_id ველი უკავშირდება students ცხრილის id ველს
-- ამის შემდეგ შეუძლებელი იქნება ისეთი student_id-ის ჩაწერა,
-- რომელიც students ცხრილში არ არსებობს
alter table enrollment
add constraint enrollment_student_id_students_id_fk
foreign key (student_id) references students(id);



-- ამატებს foreign key შეზღუდვას enrollment ცხრილში
-- course_id ველი უკავშირდება courses ცხრილის id ველს
-- ამის შემდეგ შეუძლებელი იქნება ისეთი course_id-ის ჩაწერა,
-- რომელიც courses ცხრილში არ არსებობს
alter table enrollment
add constraint course_id_fk
foreign key (course_id) references courses(id);