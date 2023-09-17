import asyncio
import logging
import sqlite3

from aiogram import Bot, types, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove
from datetime import date
from asyncio import sleep

from config import tokenobr
from filters import IsTeacher, IsNotTeacher, IsStudent, IsParent
from obrsystem.keyboards import main_btns, kb_choice, cl_buttons, high_choice, inline_kb1, inf, links_kb

storage = MemoryStorage()
logging.basicConfig(level=logging.INFO)
bot = Bot(token=tokenobr, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot, storage=storage)


class Decide(StatesGroup):
    Me = State()
    class Teacher(StatesGroup):
        Name = State()
        Form = State()
    class Student(StatesGroup):
        Name = State()
        Form = State()
        Code = State()
    class Parent(StatesGroup):
        Name = State()
        Form = State()
        Child = State()
        Code = State()

class Assign(StatesGroup):
    Form = State()
    Todo = State()
    Deadline = State()

class Event(StatesGroup):
    Name = State()
    Form = State()
    Date = State()

class Send(StatesGroup):
    Text = State()

class NewList(StatesGroup):
    ListName = State()

class NewGoal(StatesGroup):
    GoalName = State()

@dp.message_handler(commands='start', state=None)
async def start(message:types.Message):
    id1 = str(message.from_user.id)
    conn1 = sqlite3.connect('users.db')
    cursor = conn1.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS teachers(id, name, form, code_stud, code_par)")
    cursor.execute("CREATE TABLE IF NOT EXISTS students(id, name, form, code)")
    cursor.execute("CREATE TABLE IF NOT EXISTS parents(id, name, form, child, code)")
    conn1.commit()
    teacher = cursor.execute(f"SELECT name FROM teachers WHERE id = '{id1}'").fetchall()
    student = cursor.execute(f"SELECT name FROM students WHERE id = '{id1}'").fetchall()
    parent = cursor.execute(f"SELECT name FROM parents WHERE id = '{id1}'").fetchall()
    if teacher:
        await message.answer(f"Здравствуйте, {str(teacher[0][0])[str(teacher[0][0]).find(' '):]}", reply_markup=main_btns)
    if student:
        await message.answer(f"Здравствуйте, {str(student[0][0])[str(student[0][0]).find(' '):]}", reply_markup=main_btns)
    if parent:
        await message.answer(f"Здравствуйте, {str(parent[0][0])[str(parent[0][0]).find(' '):]}", reply_markup=main_btns)
    elif not parent and not student and not teacher:
        await message.answer("Добро пожаловать в нашего бота, выберите ", reply_markup=kb_choice)
        await Decide.Me.set()

@dp.message_handler(text='Я учитель', state=Decide.Me)
async def teach(message:types.Message):
    await message.answer("Введите своё ФИО", reply_markup=ReplyKeyboardRemove())
    await Decide.Teacher.Name.set()

@dp.message_handler(lambda message: message.text, state=Decide.Teacher.Name)
async def tname(message:types.Message):
    data = [str(message.from_user.id), message.text, 0, 0, 0]
    conn1 = sqlite3.connect('users.db')
    cursor = conn1.cursor()
    cursor.execute("INSERT OR IGNORE INTO teachers VALUES(?, ?, ?, ?, ?)", data)
    conn1.commit()
    await message.answer("Теперь укажите свой класс")
    await Decide.Teacher.Form.set()

@dp.message_handler(lambda message: message.text, state=Decide.Teacher.Form)
async def tform(message:types.Message, state=Decide.Teacher.Form):
    id1 = str(message.from_user.id)
    form1 = message.text.upper()
    conn1 = sqlite3.connect('users.db')
    cursor = conn1.cursor()
    cursor.execute(f"UPDATE teachers SET form = REPLACE(form, 0, '{form1}')")
    name = str(cursor.execute(f"SELECT name FROM teachers WHERE id = '{id1}'").fetchone()[0]).split()
    code_s = name[0][0] + name[1][0] + name[2][0] + form1 + 'У'
    code_p = name[0][0] + name[1][0] + name[2][0] + form1 + 'Р'
    cursor.execute(f"UPDATE teachers SET code_stud = REPLACE(code_stud, 0, '{code_s}')")
    cursor.execute(f"UPDATE teachers SET code_par = REPLACE(code_par, 0, '{code_p}')")
    conn1.commit()
    await message.answer(f"<b>Код для учеников:</b> {code_s}\n\n<b>Код для родителей:</b> {code_p}", reply_markup=main_btns)
    await FSMContext.finish(state)


@dp.message_handler(text='Я ученик', state=Decide.Me)
async def stud(message:types.Message):
    await message.answer("Введите своё ФИО", reply_markup=ReplyKeyboardRemove())
    await Decide.Student.Name.set()


@dp.message_handler(lambda message: message.text, state=Decide.Student.Name)
async def tform(message:types.Message):
    data = [message.from_user.id, message.text, 0, 0]
    conn1 = sqlite3.connect('users.db')
    cursor = conn1.cursor()
    cursor.execute("INSERT OR IGNORE INTO students VALUES(?, ?, ?, ?)", data)
    conn1.commit()
    await message.answer("Теперь укажите свой класс")
    await Decide.Student.Form.set()

@dp.message_handler(lambda message: message.text, state=Decide.Student.Form)
async def sform(message:types.Message):
    id1 = message.from_user.id
    form1 = message.text.upper()
    conn1 = sqlite3.connect('users.db')
    cursor = conn1.cursor()
    cursor.execute(f"UPDATE students SET form = REPLACE(form, 0, '{form1}') WHERE id = '{id1}'")
    conn1.commit()
    await message.answer("Теперь введите код ученика, его нужно получить у вашего учителя")
    await Decide.Student.Code.set()

@dp.message_handler(lambda message: message.text, state=Decide.Student.Code)
async def scode(message:types.Message, state=Decide.Student.Code):
    code_to_check = message.text.upper()
    id1 = message.from_user.id
    conn1 = sqlite3.connect('users.db')
    cursor = conn1.cursor()
    form1 = str(cursor.execute(f"SELECT form FROM students WHERE id = {id1}").fetchone()[0])
    code_check = str(cursor.execute(f"SELECT code_stud FROM teachers WHERE form = '{form1}'").fetchone()[0])
    if code_to_check == code_check:
        cursor.execute(f"UPDATE students SET code = REPLACE(code, 0, '{code_to_check}') WHERE id = '{id1}'")
        conn1.commit()
        await message.answer("Вы успешно вступили в класс", reply_markup=main_btns)
        await FSMContext.finish(state)
    else:
        await message.answer("Вы ввели неправильный код, попробуйте снова")
        await Decide.Student.Code.set()


@dp.message_handler(text='Я родитель', state=Decide.Me)
async def stud(message:types.Message):
    await message.answer("Введите своё ФИО", reply_markup=ReplyKeyboardRemove())
    await Decide.Parent.Name.set()

@dp.message_handler(lambda message: message.text, state=Decide.Parent.Name)
async def tform(message:types.Message):
    data = [message.from_user.id, message.text, 0, 0, 0]
    conn1 = sqlite3.connect('users.db')
    cursor = conn1.cursor()
    cursor.execute("INSERT OR IGNORE INTO parents VALUES(?, ?, ?, ?, ?)", data)
    conn1.commit()
    await message.answer("Укажите класс обучения своего ребёнка")
    await Decide.Parent.Form.set()

@dp.message_handler(lambda message: message.text, state=Decide.Parent.Form)
async def sform(message:types.Message):
    id1 = message.from_user.id
    form1 = message.text.upper()
    conn1 = sqlite3.connect('users.db')
    cursor = conn1.cursor()
    cursor.execute(f"UPDATE parents SET form = REPLACE(form, 0, '{form1}') WHERE id = '{id1}'")
    conn1.commit()
    await message.answer("Теперь укажите ФИО вашего ребёнка")
    await Decide.Parent.Child.set()


@dp.message_handler(lambda message: message.text, state=Decide.Parent.Child)
async def sform(message: types.Message):
    id1 = message.from_user.id
    child1 = message.text.title()
    conn1 = sqlite3.connect('users.db')
    cursor = conn1.cursor()
    cursor.execute(f"UPDATE parents SET child = REPLACE(child, 0, '{child1}') WHERE id = '{id1}'")
    conn1.commit()
    await message.answer("Теперь введите код ученика, его нужно получить у учителя вашего ребёнка")
    await Decide.Parent.Code.set()


@dp.message_handler(lambda message: message.text, state=Decide.Parent.Code)
async def scode(message:types.Message, state=Decide.Student.Code):
    code_to_check = message.text.upper()
    id1 = message.from_user.id
    conn1 = sqlite3.connect('users.db')
    cursor = conn1.cursor()
    child1 = str(cursor.execute(f"SELECT child FROM parents WHERE id = '{id1}'").fetchone()[0])
    form1 = str(cursor.execute(f"SELECT form FROM parents WHERE id = '{id1}'").fetchone()[0])
    code_check = str(cursor.execute(f"SELECT code_par FROM teachers WHERE form = '{form1}'").fetchone()[0])
    if code_to_check == code_check:
        cursor.execute(f"UPDATE parents SET code = REPLACE(code, 0, '{code_to_check}') WHERE id = '{id1}'")
        conn1.commit()
        await message.answer("Вы успешно вошли в профиль родителя", reply_markup=main_btns)
        await FSMContext.finish(state)
    else:
        await message.answer("Вы ввели неправильный код, попробуйте снова")
        await Decide.Parent.Code.set()

@dp.message_handler(text=['/timetable', 'Расписание 🗓️'])
async def schedulle(message:types.Message):
    conn2 = sqlite3.connect('timetable.db')
    cursor = conn2.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS monday(class, lessons)")
    cursor.execute("CREATE TABLE IF NOT EXISTS tuesday(class, lessons)")
    cursor.execute("CREATE TABLE IF NOT EXISTS wednesday(class, lessons)")
    cursor.execute("CREATE TABLE IF NOT EXISTS thursday(class, lessons)")
    cursor.execute("CREATE TABLE IF NOT EXISTS friday(class, lessons)")
    cursor.execute("CREATE TABLE IF NOT EXISTS saturday(class, lessons)")
    conn2.commit()
    await message.answer("Выберите день недели", reply_markup=cl_buttons)

@dp.message_handler(text='Понедельник')
async def monday(message:types.Message):
    id1 = message.from_user.id
    conn1 = sqlite3.connect('users.db')
    cursor1 = conn1.cursor()
    form = str(cursor1.execute(f"SELECT form FROM students WHERE id = '{id1}'").fetchone()[0])
    conn2 = sqlite3.connect('timetable.db')
    cursor2 = conn2.cursor()
    to_print = str(cursor2.execute(f"SELECT lessons FROM monday WHERE class = '{form}'").fetchall()[0][0]).split(', ')
    ans = f'<b>{form} - Понедельник</b>\n\n'
    for i in range(len(to_print)):
        ans += f"{i+1}. {to_print[i]}\n"
    await message.answer(ans)

@dp.message_handler(text='Вторник')
async def monday(message:types.Message):
    id1 = message.from_user.id
    conn1 = sqlite3.connect('users.db')
    cursor1 = conn1.cursor()
    form = str(cursor1.execute(f"SELECT form FROM students WHERE id = '{id1}'").fetchone()[0])
    conn2 = sqlite3.connect('timetable.db')
    cursor2 = conn2.cursor()
    to_print = str(cursor2.execute(f"SELECT lessons FROM tuesday WHERE class = '{form}'").fetchall()[0][0]).split(', ')
    ans = f'<b>{form} - Вторник</b>\n\n'
    for i in range(len(to_print)):
        ans += f"{i+1}. {to_print[i]}\n"
    await message.answer(ans)

@dp.message_handler(text='Среда')
async def monday(message:types.Message):
    id1 = message.from_user.id
    conn1 = sqlite3.connect('users.db')
    cursor1 = conn1.cursor()
    form = str(cursor1.execute(f"SELECT form FROM students WHERE id = '{id1}'").fetchone()[0])
    conn2 = sqlite3.connect('timetable.db')
    cursor2 = conn2.cursor()
    to_print = str(cursor2.execute(f"SELECT lessons FROM wednesday WHERE class = '{form}'").fetchall()[0][0]).split(', ')
    ans = f'<b>{form} - Среда</b>\n\n'
    for i in range(len(to_print)):
        ans += f"{i+1}. {to_print[i]}\n"
    await message.answer(ans)

@dp.message_handler(text='Четверг')
async def monday(message:types.Message):
    id1 = message.from_user.id
    conn1 = sqlite3.connect('users.db')
    cursor1 = conn1.cursor()
    form = str(cursor1.execute(f"SELECT form FROM students WHERE id = '{id1}'").fetchone()[0])
    conn2 = sqlite3.connect('timetable.db')
    cursor2 = conn2.cursor()
    to_print = str(cursor2.execute(f"SELECT lessons FROM thursday WHERE class = '{form}'").fetchall()[0][0]).split(', ')
    ans = f'<b>{form} - Четверг</b>\n\n'
    for i in range(len(to_print)):
        ans += f"{i+1}. {to_print[i]}\n"
    await message.answer(ans)

@dp.message_handler(text='Пятница')
async def monday(message:types.Message):
    id1 = message.from_user.id
    conn1 = sqlite3.connect('users.db')
    cursor1 = conn1.cursor()
    form = str(cursor1.execute(f"SELECT form FROM students WHERE id = '{id1}'").fetchone()[0])
    conn2 = sqlite3.connect('timetable.db')
    cursor2 = conn2.cursor()
    to_print = str(cursor2.execute(f"SELECT lessons FROM friday WHERE class = '{form}'").fetchall()[0][0]).split(', ')
    ans = f'<b>{form} - Пятница</b>\n\n'
    for i in range(len(to_print)):
        ans += f"{i+1}. {to_print[i]}\n"
    await message.answer(ans)

@dp.message_handler(text='Суббота')
async def monday(message:types.Message):
    id1 = message.from_user.id
    conn1 = sqlite3.connect('users.db')
    cursor1 = conn1.cursor()
    form = str(cursor1.execute(f"SELECT form FROM students WHERE id = '{id1}'").fetchone()[0])
    conn2 = sqlite3.connect('timetable.db')
    cursor2 = conn2.cursor()
    to_print = str(cursor2.execute(f"SELECT lessons FROM saturday WHERE class = '{form}'").fetchall()[0][0]).split(', ')
    ans = f'<b>{form} - Суббота</b>\n\n'
    for i in range(len(to_print)):
        ans += f"{i+1}. {to_print[i]}\n"
    await message.answer(ans)

@dp.message_handler(IsTeacher(), text=['/assignment', 'Задания 📚'])
async def assign(message:types.Message):
    conn = sqlite3.connect('assign.db')
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS homework(id, teacher, form, todo, deadline)")
    conn.commit()
    await message.answer("Укажите класс, которому вы хотите дать задание")
    await Assign.Form.set()

@dp.message_handler(IsTeacher(), lambda message:message.text, state=Assign.Form)
async def asf(message:types.Message):
    id1 = message.from_user.id
    form = message.text.upper()
    conn1 = sqlite3.connect('users.db')
    cursor1 = conn1.cursor()
    name = cursor1.execute(f"SELECT name FROM teachers WHERE id = '{id1}'").fetchone()[0]
    data = [id1, name, form, 'None', 'None']
    conn2 = sqlite3.connect('assign.db')
    cursor2 = conn2.cursor()
    cursor2.execute(f"INSERT OR IGNORE INTO homework VALUES(?, ?, ?, ?, ?)", data)
    conn2.commit()
    await message.answer("Теперь нужно указать задание")
    await Assign.Todo.set()

@dp.message_handler(IsTeacher(), lambda message:message.text, state=Assign.Todo)
async def ast(message:types.Message):
    id1 = message.from_user.id
    todo = str(message.text)
    conn = sqlite3.connect('assign.db')
    cursor = conn.cursor()
    cursor.execute(f"UPDATE homework SET todo = REPLACE(todo, 'None', '{todo}')")
    conn.commit()
    await message.answer("Когда срок сдачи задания (укажите в формате dd.mm)")
    await Assign.Deadline.set()

@dp.message_handler(IsTeacher(), lambda message: message.text, state=Assign.Deadline)
async def asd(message:types.Message):
    id1 = message.from_user.id
    deadline = str(message.text)
    conn = sqlite3.connect('assign.db')
    cursor = conn.cursor()
    cursor.execute(f"UPDATE homework SET deadline = REPLACE(deadline, 'None', '{deadline}')")
    conn.commit()
    await message.answer("Задание добавлено")
    await Assign.next()

@dp.message_handler(IsNotTeacher(), text=['/assignment', 'Задания'])
async def assign_stud(message:types.Message):
    id1 = message.from_user.id
    conn1 = sqlite3.connect('users.db')
    cursor1 = conn1.cursor()
    form = cursor1.execute(f"SELECT form FROM students WHERE id = '{id1}'").fetchone()
    conn2 = sqlite3.connect('assign.db')
    cursor2 = conn2.cursor()
    if form:
        to_print = cursor2.execute(f"SELECT todo FROM homework WHERE form = '{form[0]}'").fetchall()
        deadline = cursor2.execute(f"SELECT deadline FROM homework WHERE form = '{form[0]}'").fetchall()
        ans = ''
        for i in range(len(to_print)):
            ans += f"{i + 1}. {to_print[i][0]} до {deadline[i][0]}\n"
        await message.answer(ans)
    else:
        form1 = cursor1.execute(f"SELECT form FROM parents WHERE id = '{id1}'").fetchone()
        if form1:
            to_print = cursor2.execute(f"SELECT todo FROM homework WHERE form = '{form1[0]}'").fetchall()
            deadline = cursor2.execute(f"SELECT deadline FROM homework WHERE form = '{form1[0]}'").fetchall()
            ans = ''
            for i in range(len(to_print)):
                ans += f"{i + 1}. {to_print[i][0]} до {deadline[i][0]}\n"
            await message.answer(ans)
        else:
            await message.answer('У вас нет заданий')

@dp.message_handler(IsTeacher(), commands='addevents')
async def tevent(message:types.Message):
    conn = sqlite3.connect('events.db')
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS teachers(id, event, name, form, date)")
    cursor.execute("CREATE TABLE IF NOT EXISTS students(id, event, name, form, date)")
    conn.commit()
    await message.answer("Введите название мероприятия")
    await Event.Name.set()

@dp.message_handler(IsTeacher(), lambda message:message.text, state=Event.Name)
async def evnam(message:types.Message):
    id1 = message.from_user.id
    event = message.text
    conn1 = sqlite3.connect('users.db')
    cursor1 = conn1.cursor()
    name = cursor1.execute(f"SELECT name FROM teachers WHERE id = '{id1}'").fetchone()[0]
    data = [id1, event, name, 'None', 'None']
    conn2 = sqlite3.connect('events.db')
    cursor2 = conn2.cursor()
    cursor2.execute("INSERT OR IGNORE INTO teachers VALUES(?, ?, ?, ?, ?)", data)
    conn2.commit()
    await message.answer("Теперь укажите класс участия, если мероприятие для всех - напишите 'все'")
    await Event.next()

@dp.message_handler(IsTeacher(), lambda message:message.text, state=Event.Form)
async def evform(message:types.Message):
    id1 = message.from_user.id
    form1 = message.text.upper()
    conn = sqlite3.connect('events.db')
    cursor = conn.cursor()
    cursor.execute(f"UPDATE teachers SET form = REPLACE(form, 'None', {form1}) WHERE id = '{id1}'")
    conn.commit()
    await message.answer("Осталось ввести дату проведения мероприятия (в формате dd.mm)")
    await Event.next()

@dp.message_handler(IsTeacher(), lambda message:message.text, state=Event.Date)
async def evdate(message:types.Message):
    id1 = message.from_user.id
    date1 = message.text
    conn = sqlite3.connect("events.db")
    cursor = conn.cursor()
    cursor.execute(f"UPDATE teachers SET date = REPLACE(date, 'None', {date1}) WHERE id = '{id1}'")
    conn.commit()
    await message.answer("Мероприятие добавлено")
    await Event.next()

@dp.message_handler(text=['/events', 'События ✨'])
async def sevent(message:types.Message):
    id1 = str(message.from_user.id)
    conn1 = sqlite3.connect("users.db")
    cursor1 = conn1.cursor()
    conn2 = sqlite3.connect('events.db')
    cursor2 = conn2.cursor()
    form = cursor1.execute(f"SELECT form FROM students WHERE id = '{id1}'").fetchone()
    print(form[0])
    if not form:
        form1 = cursor1.execute(f"SELECT form FROM teachers WHERE id = '{id1}'").fetchone()
        event = cursor2.execute(f"SELECT * FROM teachers").fetchall()
        if not event:
            await message.answer("На данный момент нет доступных мероприятий")
        else:
            ans = ''
            for i in event:
                if str(i[3]) in str(form1[0]):
                    ans += i[1] + " - " + i[4] + '\n\n'
            await message.answer(ans)
        if not form1:
            form2 = cursor1.execute(f"SELECT form FROM parents WHERE id = '{id1}'").fetchone()
            event = cursor2.execute(f"SELECT * FROM teachers").fetchall()
            if not event:
                await message.answer("На данный момент нет доступных мероприятий")
            else:
                ans = ''
                for i in event:
                    if str(i[3]) in str(form2[0]):
                        ans += i[1] + " - " + i[4] + '\n\n'
                await message.answer(ans)
    else:
        event = cursor2.execute(f"SELECT * FROM teachers").fetchall()
        if not event:
            await message.answer("На данный момент нет доступных мероприятий")
        else:
            ans = ''
            for i in event:
                if str(i[3]) in str(form[0]):
                     ans += i[1] + " - " + i[4] + '\n\n'
            await message.answer(ans)


@dp.message_handler(IsTeacher(), text=['/events', 'События'])
async def sevent(message:types.Message):
    id1 = str(message.from_user.id)
    conn1 = sqlite3.connect("users.db")
    cursor1 = conn1.cursor()
    conn2 = sqlite3.connect('events.db')
    cursor2 = conn2.cursor()
    # form = cursor1.execute(f"SELECT form FROM students WHERE id = {id1}").fetchone()[0]
    event = cursor2.execute(f"SELECT * FROM teachers WHERE id = {id1}").fetchall()
    ans = ''
    for i in event:
        ans += f"{i[1]} - {i[-1]}\n\n"
    await message.answer(ans)


@dp.message_handler(IsNotTeacher(), commands='send')
async def send(message:types.Message):
    await message.answer("Напишите свой вопрос, проблему и т.д.")
    await Send.Text.set()

@dp.message_handler(IsTeacher(), commands='send')
async def send(message:types.Message):
    await message.answer("Эта функция недоступна для учителей")

@dp.message_handler(IsNotTeacher(), lambda message:message.text, state=Send.Text)
async def stext(message:types.Message):
    id1 = message.from_user.id
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    form = cursor.execute(f"SELECT form FROM students WHERE id = {id1}").fetchone()[0]
    name = cursor.execute(f"SELECT name FROM students WHERE id = {id1}").fetchone()[0]
    idt = cursor.execute(f"SELECT id FROM teachers WHERE form = '{form}'").fetchone()[0]
    to_send = message.text
    await bot.send_message(chat_id=idt, text=f"Вам пришло сообщение от {name}")
    await bot.send_message(chat_id=idt, text=f"<b>{to_send}</b>")
    await message.answer('Ваше сообщение отправлено')
    await Send.next()


@dp.message_handler(text=['/bells', 'Расписание звонков'])
async def bell(message:types.Message):
    await message.answer("Расписание звонков\n\n1. 08:20 > 09:00\n2. 09:10 > 09:50\n3. 10:00 > 10:40\n4. 10:50 > 11:30\n5. 11:40 > 12:20\n"
"6. 12:50 > 13:30\n7. 13:40 > 14:20\n8. 14:40 > 15:20\n9. 15:30 > 16:10\n10. 17:00 > 17:30")


@dp.message_handler(commands='newlist', state=None)
async def new_list(message:types.Message, state: FSMContext):
    id1 = message.from_user.id
    conn = sqlite3.connect('to_do_list.db')
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS list(id INTEGER, goal)")
    conn.commit()
    user = cursor.execute(f"SELECT * FROM list WHERE id = {id1}").fetchall()
    if user:
        await message.answer(
            "У вас уже есть список,чтобы создать новый необходимо удалить старый с помощью команды /clearlist")
        await state.finish()
    else:
        cursor.execute(f"CREATE TABLE IF NOT EXISTS list(id INTEGER, goal)")
        conn.commit()
        await message.answer("Введите название для вашего списка")
        await NewList.next()


@dp.message_handler(lambda message: message.text, state=NewList.ListName)
async def name_list(message:types.Message):
    id1 = message.from_user.id
    list_name = message.text.title()
    conn = sqlite3.connect('to_do_list.db')
    cursor = conn.cursor()
    cursor.execute(f"CREATE TABLE IF NOT EXISTS list(id INTEGER, goal)")
    cursor.execute("INSERT OR IGNORE INTO list VALUES (?, ?)", (id1, list_name),)
    conn.commit()
    user = cursor.execute(f"SELECT * FROM list WHERE id = {id1}").fetchall()
    if user:
        await message.answer("Вы создали новый список, для добавления задач используйте команду /newgoal")
        await NewList.next()
    else:
        await message.answer("Не удалось создать новый список, попробуйте снова")
        await NewList.last()

@dp.message_handler(commands='newgoal', state=None)
async def add_goal(message:types.Message):
    await message.answer("Напишите название своей цели")
    await NewGoal.next()

@dp.message_handler(lambda message: message.text, state=NewGoal.GoalName)
async def goal_name(message:types.Message):
    id1 = message.from_user.id
    goal = message.text
    data = [id1, goal]
    conn = sqlite3.connect('to_do_list.db')
    cursor = conn.cursor()
    cursor.execute(f"CREATE TABLE IF NOT EXISTS list(id INTEGER, goal)")
    cursor.execute(f"INSERT OR IGNORE INTO list VALUES(?, ?)", data)
    conn.commit()
    await message.answer("Цель добавлена")
    await NewGoal.next()

@dp.message_handler(commands='mylist')
async def show_list(message:types.Message):
    id1 = message.from_user.id
    conn = sqlite3.connect('to_do_list.db')
    cursor = conn.cursor()
    users_list = cursor.execute(f"SELECT * FROM list WHERE id = {id1}").fetchall()[1::]
    if users_list:
        list_to_send = ''
        list_to_send += cursor.execute(f"SELECT * FROM list WHERE id = {id1}").fetchone()[-1] + "\n"
        for i, x in enumerate(users_list):
            for j in x[1::]:
                list_to_send += f"{i+1}. {j.title()}\n"
        await message.answer(list_to_send)
    else:
        await message.answer("Ваш список пуст")

@dp.message_handler(commands='clearlist')
async def delete(message:types.Message):
    id1 = message.from_user.id
    conn = sqlite3.connect('to_do_list4.db')
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM list WHERE id = {id1}")
    conn.commit()
    await message.answer("Вам список был удалён, чтобы добавить новый используйте команду /newlist")


@dp.message_handler(text=['/menu', 'Назад', 'Главное меню'])
async def menu(message:types.Message):
    await message.answer("Вы вернулись в главное меню", reply_markup=main_btns)



async def remind():
    while True:
        td = str(date.today()).split('-')
        conn1 = sqlite3.connect('users.db')
        cursor1 = conn1.cursor()
        users = cursor1.execute("SELECT id FROM students").fetchall()
        for i in users:
            conn2 = sqlite3.connect('assign.db')
            cursor2 = conn2.cursor()
            user = int(i[0])
            form1 = str(cursor1.execute(f"SELECT form FROM students WHERE id = {user}").fetchone()[0])
            deadline = cursor2.execute(f"SELECT deadline FROM homework WHERE form = '{form1}'").fetchall()
            for x in deadline:
                dl = str(x[0])
                task = cursor2.execute(f"SELECT todo FROM homework WHERE form = '{form1}' AND deadline = {dl}").fetchone()[0]
                if dl[dl.find('.')+1:] == td[1] and int(td[-1]) == (int(dl[:dl.find('.')])-1):
                    await bot.send_message(chat_id=user, text=f"Завтра день сдачи задания: {task}")

        await sleep(86400)

@dp.message_handler(text=['Полезная информация ℹ️', '/info'])
async def info(message:types.Message):
    await message.answer("Выберите интересующую категорию", reply_markup=inf)

@dp.message_handler(text=['/high_edu', 'Подборка вузов'])
async def send_welcome(message: types.Message):
    await message.answer("Выберите своё направление", reply_markup=high_choice)

@dp.message_handler(text=['/olymp', 'Подготовка к олимпиадам'])
async def olymp(message:types.Message):
    await message.answer("Ильдар Сайфулаевич(физика) - 8-960-XXXXXXX\n\nАртур Павлович(математика) - 8-963-XXXXXXX\n\n""Лариса Владимировна(история) - 8-965-XXXXXXX\n\nИльдус Ильясович (англ.яз) - 8-939-XXXXXXX\n\n"
"Искандер Сунгатов (информатика)  - 8-937-XXXXXXX\n\nАйрат Альфисович (общ-ие) - 8-953-XXXXXXX\n\n""(По всем вопросам обращайтесь к вашему классному руководителю)")


@dp.message_handler(text=['/courses', 'Обучающие курсы'])
async def courses(message: types.Message):
    await message.answer("Курсы по программированию от государства или ведущих компаний", reply_markup=inline_kb1)

@dp.message_handler(text=['/links', 'Полезные ссылки'])
async def links(message:types.Message):
    await message.answer("Вот несколько полезных ссылок", reply_markup=links_kb)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(remind())
    executor.start_polling(dp, skip_updates=True)
