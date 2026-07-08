
-- ცხრილის შექმნა
create table students (
	id serial primary key,
	name varchar(30) not null,
	email varchar(150) unique not null,
	birth_date date,
	enrolled boolean default true,
	created_at timestamp default now()
)

-- ცხრილში ინფორმაციის ჩაწერა, მხოლოდ name, email და enrolled სვეტები
insert into students(name, email, enrolled) values('John', 'John1@gmail.com', false)

-- ცხრილში ინფორმაციის ჩაწერა DEFAULT მნიშვნელობებით ისეთ სვეტებში, სადაც მითითებული გვაქვს default მნიშვნელობები შექმნის დროს
INSERT INTO students (id, name, email, birth_date, enrolled, created_at)
VALUES (DEFAULT, 'Tako Chikovani', 'tako@example.com', '2002-03-30', TRUE, DEFAULT);

-- რამდენიმე ჩანაწერის გაკეთება ერთი ქუერის გამოყენებით
INSERT INTO students (name, email, birth_date)
VALUES  ('Mariam Kapanadze','mariam1@example.com', '2000-May-19'),
  		('Davit Lomidze','davit1@example.com',  '1998-Dec-05')


-- ყველა ჩანაწერის წაკითხვა (ყველა სვეტი)
select * from students

-- ყველა ჩანაწერის წაკითხვა (ყველა სვეტი), დალაგებული created_at სვეტის მიხედვით კლებადობით
select * from students order by created_at desc

-- მხოლოდ name და email სვეტები,
-- სადაც birth_date მეტი უნდა იყოს 2000-01-01_ზე და name მნიშვნელობა უნდა იყოს Tako Chikovani
-- ორივე პირობა უნდა დააკმაყოფილოს ჩანაწერმა
select name, email from students where birth_date > '2000-01-01' and name = 'Tako Chikovani'

-- მხოლოდ name და email სვეტები,
-- სადაც birth_date მეტი უნდა იყოს 2000-01-01_ზე ან name მნიშვნელობა უნდა იყოს Tako Chikovani
-- ერთ-ერთი პირობა მაინც უნდა დააკმაყოფილოს ჩანაწერმა
select name, email from students where birth_date > '2000-01-01' or name = 'Tako Chikovani'

-- name და email სვეტების წაკითხვა სადაც name სვეტი იწყება Tako სიმბოლოების თანმიმდევრობით, მის მარჯვნივ კი უნდა იყოს ნებისმიერი რაოდენობის ნებისმიერი სიმბოლოთა თანმიმდევრობა
-- ყურადღება ექცევა რეგისტრებს
select name, email from students where name like 'Tako%'

-- name და email სვეტების წაკითხვა სადაც name სვეტი იწყება tako სიმბოლოების თანმიმდევრობით, მის მარჯვნივ კი უნდა იყოს ნებისმიერი რაოდენობის ნებისმიერი სიმბოლოთა თანმიმდევრობა
-- ყურადღება არ ექცევა რეგისტრებს
select name, email from students where name ilike 'tako%'

-- ჩანაწერის განახლება
-- დააყენოს birth_date მნიშვნელობაზე '2026-07-10'
-- დააყენოს email მნიშვნელობა 'left@example.com'-ზე
-- მხოლოდ იმ ჩანაწერისთვის, რომელსაც id მნიშვნელობა აქვს 1
-- თუ არ მივუთითებთ ფილტრაციას(where) ყველა ჩანაწერი შეიცვლება
update students set birth_date = '2026-07-10', email = 'left@example.com' where id = 1

-- ჩანაწერის წაშლა, რომელსაც id მნიშვნელობა აქვს 1
delete from students where id = 1

-- ცხრილის წაშლა
drop table students

