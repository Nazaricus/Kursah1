from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
import psycopg2
from psycopg2 import sql

# Создаем экземпляр Flask
sting = Flask(__name__)

# Параметры подключения к PostgreSQL
db_name = "kursochBUB123"
db_user = "postgres"
db_password = "sotaze40"
db_host = "localhost"
db_port = 5432

# Строка подключения для SQLAlchemy
sting.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
sting.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Инициализация SQLAlchemy
db = SQLAlchemy(sting)

class Order(db.Model):  # заказ
    id_order = db.Column(db.Integer, primary_key=True)  # айди заказа
    Seller_id = db.Column(db.Integer, nullable=False)  # айди продавца
    Menager_id = db.Column(db.Integer, nullable=False)  # айди менеджера склада
    fio_buyer = db.Column(db.String(50), nullable=False)  # фио покупателя
    buyer_phone = db.Column(db.Integer, nullable=False)  # телефон покупателя
    id_equipment = db.Column(db.Integer, nullable=False)  # айди запчасти
    id_spare = db.Column(db.Integer, nullable=False)  # айди техники
    availability = db.Column(db.String(50), nullable=False)  # статус заказа


class Manager(db.Model):  # менеджер склада
    Menager_id = db.Column(db.Integer, primary_key=True)  # менеджер айди
    fio_Manager = db.Column(db.String(50), nullable=False)  # фио менеджера


class Equipment(db.Model):  # запчасти
    id_equipment = db.Column(db.Integer, primary_key=True)  # айди
    numder_of_units = db.Column(db.Integer, nullable=False)  # кол-во единиц
    availability = db.Column(db.String(50), nullable=False)  # состояние
    price_per_unit = db.Column(db.Integer, nullable=False)  # цена
    name = db.Column(db.String(100), nullable=False)  # название


class Spare_parts(db.Model):  # техника
    id_spare = db.Column(db.Integer, primary_key=True)  # айди техники
    numder_units = db.Column(db.Integer, nullable=False)  # кол-во единиц
    availability = db.Column(db.String(50), nullable=False)  # состояние
    price_per_unit = db.Column(db.Integer, nullable=False)  # цена
    name = db.Column(db.String(100), nullable=False)  # название


class warehouse_cell(db.Model):  # склад
    cell_id = db.Column(db.Integer, primary_key=True)  # айди ячейки склада
    status = db.Column(db.String(50), nullable=False)  # статус ячейки
    id_equipment = db.Column(db.Integer, nullable=False)  # айди запчасти в ячейке


class parking_space(db.Model):  # парковка
    parking_id = db.Column(db.Integer, primary_key=True)  # айди парковочного места
    id_spare = db.Column(db.Integer, nullable=False)  # айди техники припаркованной на месте
    status = db.Column(db.String(50), nullable=False)  # статус места


class order_tex(db.Model):  # доп. таблица по технике в заказе
    id_order_tex = db.Column(db.Integer, primary_key=True)  # айди
    id_order = db.Column(db.Integer, nullable=False)  # айди заказа
    id_spare = db.Column(db.Integer, nullable=False)  # айди техники
    col_vo = db.Column(db.Integer, nullable=False)  # кол-во единиц


class order_eq(db.Model):  # доп. таблица по запчастям в заказе
    id_order_eq = db.Column(db.Integer, primary_key=True)  # айди
    id_order = db.Column(db.Integer, nullable=False)  # айди заказа
    id_equipment = db.Column(db.Integer, nullable=False)  # айди запчасти
    col_vo = db.Column(db.Integer, nullable=False)  # кол-во единиц в заказе

# Функция для создания базы данных
def create_database():
    try:
        # Подключение к PostgreSQL через базу данных 'postgres'
        conn = psycopg2.connect(
            dbname="postgres",
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port
        )
        conn.autocommit = True
        cursor = conn.cursor()

        # Проверка существования базы данных
        cursor.execute(sql.SQL("SELECT 1 FROM pg_database WHERE datname = %s"), [db_name])
        exists = cursor.fetchone()
        if not exists:
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))
            print(f"База данных '{db_name}' успешно создана!")
        else:
            print(f"База данных '{db_name}' уже существует.")

        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Ошибка при создании базы данных: {e}")

if __name__ == '__main__':
    create_database()
    with sting.app_context():
        db.create_all()
    sting.run(debug=True)