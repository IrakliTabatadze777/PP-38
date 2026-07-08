create table students (
	id serial primary key,
	name varchar(30) not null,
	email varchar(150) unique not null,
	birth_date date,
	enrolled boolean default true,
	created_at timestamp default now()
)

insert into students(name, email, enrolled) values('John', 'John1@gmail.com', false)


INSERT INTO students (id, name, email, birth_date, enrolled, created_at)
VALUES (DEFAULT, 'Tako Chikovani', 'tako@example.com', '2002-03-30', TRUE, DEFAULT);


INSERT INTO students (name, email, birth_date)
VALUES  ('Mariam Kapanadze','mariam1@example.com', '2000-May-19'),
  		('Davit Lomidze','davit1@example.com',  '1998-Dec-05')


select * from students

select * from students order by created_at desc

select name, email from students where birth_date > '2000-01-01' and name = 'Tako Chikovani'

select name, email from students where birth_date > '2000-01-01' or name = 'Tako Chikovani'

select name, email from students where name like 'Tako%'

select name, email from students where name ilike 'tako%'


update students set birth_date = '2026-07-10', email ='left@example.com' where id = 1

delete from students where id = 1

drop table students

