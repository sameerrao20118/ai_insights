"""
Multi-Table Test Schema for Talk-to-Data

This schema creates a realistic multi-table database for testing
natural language to SQL translation with JOIN queries.

Scenario: E-commerce system with customers, orders, products, and reviews.
"""

-- Drop tables if they exist (for clean setup)
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS reviews;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS categories;

-- Create categories table
CREATE TABLE categories (
    category_id INT PRIMARY KEY AUTO_INCREMENT,
    category_name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Create products table
CREATE TABLE products (
    product_id INT PRIMARY KEY AUTO_INCREMENT,
    product_name VARCHAR(255) NOT NULL,
    category_id INT,
    price DECIMAL(10,2) NOT NULL,
    stock_quantity INT DEFAULT 0,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(category_id)
) ENGINE=InnoDB;

-- Create customers table
CREATE TABLE customers (
    customer_id INT PRIMARY KEY AUTO_INCREMENT,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    loyalty_points INT DEFAULT 0
) ENGINE=InnoDB;

-- Create orders table
CREATE TABLE orders (
    order_id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT NOT NULL,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    shipping_address TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
) ENGINE=InnoDB;

-- Create order_items table (junction table)
CREATE TABLE order_items (
    order_item_id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    subtotal DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
) ENGINE=InnoDB;

-- Create reviews table
CREATE TABLE reviews (
    review_id INT PRIMARY KEY AUTO_INCREMENT,
    product_id INT NOT NULL,
    customer_id INT NOT NULL,
    rating INT CHECK (rating BETWEEN 1 AND 5),
    review_text TEXT,
    review_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
) ENGINE=InnoDB;

-- Insert sample data

-- Categories
INSERT INTO categories (category_name, description) VALUES
('Electronics', 'Electronic devices and gadgets'),
('Books', 'Physical and digital books'),
('Clothing', 'Apparel and accessories'),
('Home & Garden', 'Home improvement and garden supplies');

-- Products
INSERT INTO products (product_name, category_id, price, stock_quantity, description) VALUES
('Laptop Pro 15', 1, 1299.99, 50, 'High-performance laptop'),
('Wireless Mouse', 1, 29.99, 200, 'Ergonomic wireless mouse'),
('Python Programming Guide', 2, 49.99, 100, 'Comprehensive Python book'),
('Data Science Handbook', 2, 59.99, 75, 'Data science reference'),
('Cotton T-Shirt', 3, 19.99, 300, 'Comfortable cotton t-shirt'),
('Jeans', 3, 79.99, 150, 'Classic denim jeans'),
('Garden Tools Set', 4, 89.99, 40, 'Complete garden tools'),
('LED Smart Bulb', 4, 24.99, 120, 'WiFi-enabled smart bulb');

-- Customers
INSERT INTO customers (first_name, last_name, email, phone, loyalty_points) VALUES
('John', 'Doe', 'john.doe@email.com', '555-0101', 150),
('Jane', 'Smith', 'jane.smith@email.com', '555-0102', 280),
('Bob', 'Johnson', 'bob.johnson@email.com', '555-0103', 75),
('Alice', 'Williams', 'alice.williams@email.com', '555-0104', 420),
('Charlie', 'Brown', 'charlie.brown@email.com', '555-0105', 90);

-- Orders
INSERT INTO orders (customer_id, total_amount, status, shipping_address) VALUES
(1, 1329.98, 'delivered', '123 Main St, City, State 12345'),
(2, 169.97, 'shipped', '456 Oak Ave, Town, State 67890'),
(1, 49.99, 'delivered', '123 Main St, City, State 12345'),
(3, 109.98, 'pending', '789 Pine Rd, Village, State 11111'),
(4, 1379.97, 'delivered', '321 Elm St, Hamlet, State 22222'),
(2, 79.99, 'cancelled', '456 Oak Ave, Town, State 67890'),
(5, 24.99, 'delivered', '654 Maple Dr, Borough, State 33333');

-- Order Items
INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal) VALUES
-- Order 1: John's laptop and mouse
(1, 1, 1, 1299.99, 1299.99),
(1, 2, 1, 29.99, 29.99),
-- Order 2: Jane's books and t-shirt
(2, 3, 1, 49.99, 49.99),
(2, 4, 1, 59.99, 59.99),
(2, 5, 3, 19.99, 59.97),
-- Order 3: John's Python book
(3, 3, 1, 49.99, 49.99),
-- Order 4: Bob's clothing
(4, 5, 2, 19.99, 39.98),
(4, 6, 1, 79.99, 79.99),
-- Order 5: Alice's laptop and garden tools
(5, 1, 1, 1299.99, 1299.99),
(5, 7, 1, 89.99, 89.99),
-- Order 6: Jane's cancelled jeans
(6, 6, 1, 79.99, 79.99),
-- Order 7: Charlie's smart bulb
(7, 8, 1, 24.99, 24.99);

-- Reviews
INSERT INTO reviews (product_id, customer_id, rating, review_text) VALUES
(1, 1, 5, 'Excellent laptop, very fast!'),
(1, 4, 5, 'Best purchase this year'),
(2, 1, 4, 'Good mouse, comfortable to use'),
(3, 1, 5, 'Great Python resource'),
(3, 2, 4, 'Comprehensive and well-written'),
(5, 2, 3, 'Decent quality, fits well'),
(7, 4, 5, 'Perfect for my garden'),
(8, 5, 4, 'Easy to setup and use');

-- Create indexes for performance
CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_order_items_order ON order_items(order_id);
CREATE INDEX idx_order_items_product ON order_items(product_id);
CREATE INDEX idx_reviews_product ON reviews(product_id);
CREATE INDEX idx_reviews_customer ON reviews(customer_id);
CREATE INDEX idx_products_category ON products(category_id);

-- Verify the schema
SELECT 
    'Tables Created' as Status,
    COUNT(*) as Count
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = DATABASE()
AND TABLE_TYPE = 'BASE TABLE';

-- Show relationship summary
SELECT 
    TABLE_NAME,
    COLUMN_NAME,
    REFERENCED_TABLE_NAME,
    REFERENCED_COLUMN_NAME
FROM information_schema.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = DATABASE()
AND REFERENCED_TABLE_NAME IS NOT NULL
ORDER BY TABLE_NAME;
