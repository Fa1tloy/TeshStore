CREATE DATABASE TechStore;
USE TechStore;

-- Роли
CREATE TABLE roles (
    id INT PRIMARY KEY AUTO_INCREMENT,
    role_name VARCHAR(50) NOT NULL
);

INSERT INTO roles (role_name) VALUES
('admin'),
('client');

-- Пользователи
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    login VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role_id INT,
    FOREIGN KEY (role_id) REFERENCES roles(id)
);

INSERT INTO users (login, password, role_id) VALUES
('admin', 'admin123', 1),
('ivan', '123', 2),
('anna', '123', 2),
('sergey', '123', 2),
('olga', '123', 2);

-- Группы товаров
CREATE TABLE categories (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL
);

INSERT INTO categories (name) VALUES
('Холодильники'),
('Стиральные машины'),
('Телевизоры'),
('Микроволновые печи'),
('Пылесосы');

-- Товары
CREATE TABLE products (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(150) NOT NULL,
    brand VARCHAR(100),
    price DECIMAL(10,2),
    power VARCHAR(50),
    photo VARCHAR(255),
    category_id INT,
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

INSERT INTO products (name, brand, price, power, photo, category_id) VALUES
('LG InstaView', 'LG', 79990.00, 'A++', '', 1),
('Samsung EcoBubble', 'Samsung', 56990.00, '2200W', '', 2),
('Sony Bravia 55', 'Sony', 99990.00, '150W', '', 3),
('Bosch Serie 4', 'Bosch', 18990.00, '900W', '', 4),
('Dyson V11', 'Dyson', 45990.00, '545W', '', 5);

-- Заказы
CREATE TABLE orders (
    id INT PRIMARY KEY AUTO_INCREMENT,
    product_id INT,
    client_name VARCHAR(100),
    order_date DATE,
    quantity INT,
    FOREIGN KEY (product_id) REFERENCES products(id)
);

INSERT INTO orders (product_id, client_name, order_date, quantity) VALUES
(1, 'Иван', '2025-01-15', 1),
(1, 'Анна', '2025-02-11', 2),
(3, 'Сергей', '2025-02-24', 1),
(5, 'Ольга', '2025-03-02', 1);
