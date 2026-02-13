CREATE TABLE IF NOT EXISTS quotes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    genre VARCHAR(50) NOT NULL,
    text TEXT NOT NULL,
    author VARCHAR(100) DEFAULT 'Unknown',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_genre (genre)
);

-- Seed some initial data
INSERT INTO quotes (genre, text, author) VALUES 
('motivation', 'The only way to do great work is to love what you do.', 'Steve Jobs'),
('motivation', 'Believe you can and you''re halfway there.', 'Theodore Roosevelt'),
('life', 'Life is what happens when you''re busy making other plans.', 'John Lennon'),
('tech', 'Software is eating the world.', 'Marc Andreessen');
