import psycopg2


conn = psycopg2.connect(
    host='localhost', # 127.0.0.1
    port=5432,
    dbname='PP-38',
    user='postgres',
    password='123123'
)

print('Connection established')


cursor = conn.cursor()



# cursor.execute('SELECT * FROM students limit 10')
cursor.execute('SELECT * FROM students where id = 1')
rows = cursor.fetchone()


# maximum_id = 10
# cursor.execute("SELECT * FROM students where id < %s", (maximum_id,))
#
# rows = cursor.fetchall()


# for row in rows:
#     print(f'ID = {row[0]}, name = {row[1]}, email = {row[2]}')

print(rows)


# cursor.execute('insert into students(name, email) values (%s, %s)', ('irakli', 'irakli@istep.ge'))


conn.commit()

cursor.close()
conn.close()
