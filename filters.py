from aiogram.dispatcher.filters import BoundFilter
from aiogram import types
import sqlite3

class IsTeacher(BoundFilter):
    async def check(self, message:types.Message):
        member = str(message.from_user.id)
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        users = cursor.execute(f"SELECT id FROM teachers WHERE id = {member}").fetchall()
        c = 0
        for i in users:
            if member in str(i):
                c += 1
        if c >= 1:
            return True
        else:
            return False

class IsNotTeacher(BoundFilter):
    async def check(self, message:types.Message):
        member = str(message.from_user.id)
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        users = cursor.execute(f"SELECT id FROM teachers WHERE id = {member}").fetchall()
        c = 0
        for i in users:
            if member in str(i):
                c += 1
        if c == 0:
            return True
        else:
            return False

class IsParent(BoundFilter):
    async def check(self, message:types.Message):
        member = str(message.from_user.id)
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        users = cursor.execute(f"SELECT id FROM parents WHERE id = {member}").fetchall()
        c = 0
        for i in users:
            if member in str(i):
                c += 1
        if c >= 1:
            return True
        else:
            return False

class IsStudent(BoundFilter):
    async def check(self, message:types.Message):
        member = str(message.from_user.id)
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        users = cursor.execute(f"SELECT id FROM students WHERE id = {member}").fetchall()
        c = 0
        for i in users:
            if member in str(i):
                c += 1
        if c >= 1:
            return True
        else:
            return False

