import io

from flask import Flask, render_template, request, redirect, url_for, send_file
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, time
import pandas as pd

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:sotaze40@localhost:5432/kursah'
db: SQLAlchemy = SQLAlchemy(app)

class Seller(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fio_seller = db.Column(db.Text, nullable=False)
    phone_seller = db.Column(db.Text, nullable=False)
    specialization = db.Column(db.Text, nullable=False)

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fio_client = db.Column(db.Text, nullable=False)
    phone_client = db.Column(db.Text, nullable=False)
    address_client = db.Column(db.Text, nullable=False)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True) # айди заказа
    time = db.Column(db.Time, nullable=False) # время заказа
    date = db.Column(db.Date, nullable=False) # дата заказа
    id_seller = db.Column(db.Integer, nullable=False) # айди продавца
    id_client = db.Column(db.Integer, nullable=False) # айди клиента


class Delivery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    deadlines = db.Column(db.Date, nullable=False)
    prise_delivery = db.Column(db.Integer, nullable=False)
    address_delivery = db.Column(db.String(200), nullable=False)
    id_order = db.Column(db.Integer, nullable=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    manufacturer = db.Column(db.String, nullable=False)
    expiration_date = db.Column(db.Date, nullable=False)
    description = db.Column(db.String, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String, nullable=False)
    price = db.Column(db.Integer, nullable=False)

class OrderProduct(db.Model): # доп таблиа по товару в заказе
    id = db.Column(db.Integer, primary_key=True) # айди линии товара
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False) # айди заказа
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False) # айди товара
    quantity = db.Column(db.Integer, nullable=False) # количество

@app.route('/index')
def index():
    return render_template('all_data.html')

@app.route('/')
@app.route('/all_data')
def all_data():
    sellers = Seller.query.all()
    clients = Client.query.all()

    # Получаем все заказы вместе с товарами и их количеством
    orders = db.session.query(
        Order.id,
        Order.time,
        Order.date,
        Order.id_seller,
        Order.id_client,
        db.func.string_agg(Product.name + ' (' + db.cast(OrderProduct.quantity, db.Text) + ')', ', ').label('products')
    ).join(
        OrderProduct, Order.id == OrderProduct.order_id, isouter=True
    ).join(
        Product, OrderProduct.product_id == Product.id, isouter=True
    ).group_by(
        Order.id, Order.time, Order.date, Order.id_seller, Order.id_client
    ).all()

    deliveries = Delivery.query.all()
    products = Product.query.all()

    return render_template(
        'all_data.html',
        sellers=sellers,
        clients=clients,
        orders=orders,
        deliveries=deliveries,
        products=products
    )

@app.route('/products', methods=['GET', 'POST'])
def products():
    if request.method == 'POST':
        # Получение данных из формы для нового продукта
        manufacturer = request.form['manufacturer']
        expiration_date_str = request.form['expiration_date']
        description = request.form['description']
        quantity = int(request.form['quantity'])
        name = request.form['name']
        price = float(request.form['price'])

        # Преобразование строки даты в объект даты
        expiration_date = datetime.strptime(expiration_date_str, '%Y-%m-%d').date()

        # Создание нового продукта
        new_product = Product(manufacturer=manufacturer, expiration_date=expiration_date, description=description,
                              quantity=quantity, name=name, price=price)
        db.session.add(new_product)
        db.session.commit()
        return redirect('/products')
    else:
        return render_template('products.html')

@app.route('/seller', methods=['GET', 'POST'])
def seller():
    if request.method == 'POST':
        fio_seller = request.form['fio_seller']
        phone_seller = request.form['phone_seller']
        specialization = request.form['specialization']

        seller = Seller(fio_seller=fio_seller, phone_seller=phone_seller, specialization=specialization)
        try:
            db.session.add(seller)
            db.session.commit()
            return redirect('/seller')
        except:
            return 'При добавлении сотрудника произошла ошибка!'
    else:
        return render_template('seller.html')


from datetime import datetime

from datetime import datetime, date


@app.route('/order', methods=['GET', 'POST'])
def order():
    if request.method == 'POST':
        id_seller = int(request.form['id_seller'])
        id_client = int(request.form['id_client'])
        date_str = request.form['date']
        time_str = request.form['time']

        # Преобразование времени и даты
        time_obj = datetime.strptime(time_str, '%H:%M').time()
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()

        # Создание нового заказа
        new_order = Order(id_seller=id_seller, id_client=id_client, date=date_obj, time=time_obj)
        db.session.add(new_order)
        db.session.commit()

        # Добавление товаров в заказ
        products = request.form.getlist('product_id')  # Список ID товаров
        quantities = request.form.getlist('quantity')  # Список количеств

        for product_id, quantity in zip(products, quantities):
            if int(quantity) > 0:
                product = Product.query.get(int(product_id))
                if product and product.quantity >= int(quantity):
                    # Уменьшаем количество товара
                    product.quantity -= int(quantity)

                    # Добавляем запись в OrderProduct
                    order_product = OrderProduct(order_id=new_order.id, product_id=int(product_id), quantity=int(quantity))
                    db.session.add(order_product)
                else:
                    return f"Ошибка: недостаточно товара с ID {product_id}!"

        db.session.commit()
        return redirect('/all_data')

    else:
        sellers = Seller.query.all()
        clients = Client.query.all()
        products = Product.query.all()
        return render_template('order.html', sellers=sellers, clients=clients, products=products)

@app.route('/delivery', methods=['GET', 'POST'])
def delivery():
    if request.method == 'POST':
        address_delivery = request.form['address_delivery']
        prise_delivery = float(request.form['prise_delivery'])
        deadlines = datetime.strptime(request.form['deadlines'], '%Y-%m-%d').date()
        id_order = int(request.form['id_order'])

        # Проверка существования заказа
        if not Order.query.get(id_order):
            return f"Ошибка: заказ с ID {id_order} не существует."

        # Создание новой доставки
        delivery = Delivery(
            address_delivery=address_delivery,
            prise_delivery=prise_delivery,
            deadlines=deadlines,
            id_order=id_order
        )
        try:
            db.session.add(delivery)
            db.session.commit()
            return redirect('/delivery')
        except Exception as e:
            return f'Ошибка при добавлении доставки: {str(e)}'
    else:
        # Передача списка заказов в шаблон
        orders = Order.query.all()
        return render_template('delivery.html', orders=orders)


@app.route('/client', methods=['GET', 'POST'])
def client():
    if request.method == 'POST':
        fio_client = request.form['fio_client']
        phone_client = request.form['phone_client']
        address_client = request.form['address_client']

        client = Client(fio_client=fio_client, phone_client=phone_client, address_client=address_client)
        try:
            db.session.add(client)
            db.session.commit()
            return redirect('/all_data')
        except:
            return 'При добавлении покупателя произошла ошибка!'
    else:
        return render_template('client.html')

@app.route('/products/<int:id>/upd', methods=['GET', 'POST'])
def update_product(id):
    product = Product.query.get(id)
    if request.method == 'POST':
        product.name = request.form.get('name')
        product.manufacturer = request.form.get('manufacturer')

        expiration_date_str = request.form.get('expiration_date')
        try:
            product.expiration_date = datetime.strptime(expiration_date_str, '%Y-%m-%d').date()
        except ValueError:
            return 'Ошибка: неверный формат даты!'

        product.description = request.form.get('description')
        product.quantity = request.form.get('quantity')
        product.price = request.form.get('price')

        try:
            db.session.commit()
            return redirect('/all_data')
        except Exception as e:
            return f'При обновлении товара произошла ошибка! {e}'
    else:
        return render_template('upd_products.html', product=product)

@app.route('/client/<int:id>/upd', methods=['GET', 'POST'])
def update_client(id):
    client = Client.query.get(id)
    if request.method == 'POST':
        client.phone_client = request.form.get('phone_client')
        client.fio_client = request.form.get('fio_client')
        client.address_client = request.form.get('address_client')
        try:
            db.session.commit()
            return redirect('/all_data')
        except:
            return 'При обновлении покупателя произошла ошибка!'
    else:
        return render_template('udp_client.html', client=client)

@app.route('/order/<int:id>/upd', methods=['GET', 'POST'])
def update_order(id):
    order = Order.query.get(id)
    if not order:
        return "Заказ не найден!"

    if request.method == 'POST':
        order.id_seller = int(request.form['id_seller'])
        order.id_client = int(request.form['id_client'])
        date_str = request.form['date']
        time_str = request.form['time']

        # Обновление времени и даты
        order.time = datetime.strptime(time_str, '%H:%M').time()
        order.date = datetime.strptime(date_str, '%Y-%m-%d').date()

        # Получение старых товаров из OrderProduct
        old_order_products = OrderProduct.query.filter_by(order_id=order.id).all()

        # Возвращаем старое количество товаров
        for op in old_order_products:
            product = Product.query.get(op.product_id)
            if product:
                product.quantity += op.quantity

        # Очистка текущих товаров в заказе
        OrderProduct.query.filter_by(order_id=order.id).delete()

        # Добавление новых товаров
        products = request.form.getlist('product_id')
        quantities = request.form.getlist('quantity')

        for product_id, quantity in zip(products, quantities):
            if int(quantity) > 0:
                product = Product.query.get(int(product_id))
                if product and product.quantity >= int(quantity):
                    # Уменьшаем количество товара
                    product.quantity -= int(quantity)

                    # Добавляем запись в OrderProduct
                    order_product = OrderProduct(order_id=order.id, product_id=int(product_id), quantity=int(quantity))
                    db.session.add(order_product)
                else:
                    return f"Ошибка: недостаточно товара с ID {product_id}!"

        db.session.commit()
        return redirect('/all_data')

    else:
        sellers = Seller.query.all()
        clients = Client.query.all()
        products = Product.query.all()
        order_products = OrderProduct.query.filter_by(order_id=order.id).all()

        # Формируем список выбранных товаров и их количеств
        selected_products = {op.product_id: op.quantity for op in order_products}

        return render_template('upd_order.html', order=order, sellers=sellers, clients=clients, products=products,
                               selected_products=selected_products)

@app.route('/seller/<int:id>/upd', methods=['GET', 'POST'])
def update_seller(id):
    seller = Seller.query.get(id)
    if request.method == 'POST':
        seller.fio_seller = request.form['fio_seller']
        seller.phone_seller = request.form['phone_seller']
        seller.specialization = request.form['specialization']
        try:
            db.session.commit()
            return redirect('/all_data')
        except:
            return 'При обновлении сотрудника произошла ошибка!'
    else:
        return render_template('upd_seller.html', seller=seller)

@app.route('/delivery/<int:id>/upd', methods=['GET', 'POST'])
def update_delivery(id):
    delivery = Delivery.query.get(id)
    if request.method == 'POST':
        delivery.address_delivery = request.form['address_delivery']
        delivery.prise_delivery = request.form['prise_delivery']
        delivery.deadlines = request.form['deadlines']
        delivery.id_order = request.form['id_order']
        try:
            db.session.commit()
            return redirect('/all_data')
        except:
            return 'При обновлении доставки произошла ошибка!'
    else:
        return render_template('upd_delivery.html', delivery=delivery)

@app.route('/delete_product/<int:id>', methods=['GET'])
def delete_product(id):
    product = Product.query.get(id)
    if product:
        db.session.delete(product)
        db.session.commit()
    return redirect('/all_data')

@app.route('/delete_order/<int:id>', methods=['GET'])
def delete_order(id):
    order = Order.query.get(id)
    if order:
        db.session.delete(order)
        db.session.commit()
    return redirect('/all_data')

@app.route('/delete_client/<int:id>', methods=['GET'])
def delete_client(id):
    client = Client.query.get(id)
    if client:
        db.session.delete(client)
        db.session.commit()
    return redirect('/all_data')

@app.route('/delete_seller/<int:id>', methods=['GET'])
def delete_seller(id):
    seller = Seller.query.get(id)
    if seller:
        db.session.delete(seller)
        db.session.commit()
    return redirect('/all_data')

@app.route('/delete_delivery/<int:id>', methods=['GET'])
def delete_delivery(id):
    delivery = Delivery.query.get(id)
    if delivery:
        db.session.delete(delivery)
        db.session.commit()
    return redirect('/all_data')

@app.route('/clients_report')
def clients_report():
    # Получение данных о клиентах
    clients_data = db.session.query(
        Client.id,
        Client.fio_client,
        Client.phone_client,
        Client.address_client,
        db.func.count(Order.id).label('order_count')
    ).outerjoin(Order, Order.id_client == Client.id).group_by(Client.id).all()

    # Формируем таблицу HTML
    return render_template('clients_report.html', clients=clients_data)

@app.route('/sales_report')
def sales_report():
    # Получение данных о продажах
    sales_data = db.session.query(
        Order.id.label('order_id'),
        Order.date.label('order_date'),
        Order.time.label('order_time'),
        Seller.fio_seller.label('seller'),
        Client.fio_client.label('client'),
        db.func.sum(Product.price).label('total_price')
    ).join(Seller, Order.id_seller == Seller.id)\
    .join(Client, Order.id_client == Client.id)\
    .join(OrderProduct, OrderProduct.order_id == Order.id)\
    .join(Product, OrderProduct.product_id == Product.id)\
    .group_by(Order.id, Seller.fio_seller, Client.fio_client).all()

    # Формируем таблицу HTML
    return render_template('sales_report.html', sales=sales_data)

@app.route('/download_clients_report')
def download_clients_report():
    # Генерация отчёта в формате Excel
    clients_data = db.session.query(
        Client.id,
        Client.fio_client,
        Client.phone_client,
        Client.address_client,
        db.func.count(Order.id).label('order_count')
    ).outerjoin(Order, Order.id_client == Client.id).group_by(Client.id).all()

    # Формируем DataFrame
    df = pd.DataFrame([{
        'ID клиента': c.id,
        'ФИО клиента': c.fio_client,
        'Телефон': c.phone_client,
        'Адрес': c.address_client,
        'Количество заказов': c.order_count
    } for c in clients_data])

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Clients Report')

    output.seek(0)
    return send_file(output, as_attachment=True, download_name='clients_report.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@app.route('/download_sales_report')
def download_sales_report():
    # Генерация отчёта в формате Excel
    sales_data = db.session.query(
        Order.id.label('order_id'),
        Order.date.label('order_date'),
        Order.time.label('order_time'),
        Seller.fio_seller.label('seller'),
        Client.fio_client.label('client'),
        db.func.sum(Product.price).label('total_price')
    ).join(Seller, Order.id_seller == Seller.id)\
    .join(Client, Order.id_client == Client.id)\
    .join(OrderProduct, OrderProduct.id_order == Order.id)\
    .join(Product, OrderProduct.id_product == Product.id)\
    .group_by(Order.id, Seller.fio_seller, Client.fio_client).all()

    # Формируем DataFrame
    df = pd.DataFrame([{
        'ID заказа': s.order_id,
        'Дата заказа': s.order_date,
        'Время заказа': s.order_time,
        'Продавец': s.seller,
        'Клиент': s.client,
        'Общая стоимость': s.total_price
    } for s in sales_data])

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sales Report')

    output.seek(0)
    return send_file(output, as_attachment=True, download_name='sales_report.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

