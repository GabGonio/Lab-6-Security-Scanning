CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(64) NOT NULL
);

CREATE TABLE IF NOT EXISTS crew (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    handle VARCHAR(50) NOT NULL,
    region VARCHAR(50),
    active_since INTEGER
);

CREATE TABLE IF NOT EXISTS releases (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    platform VARCHAR(50),
    format VARCHAR(50),
    cracked_by VARCHAR(100),
    release_year INTEGER,
    notes TEXT,
    image_width INTEGER,
    image_height INTEGER
);

INSERT INTO users (username, password_hash) VALUES
    ('admin',  '140a4bbefca4bc788a61d7c32c343e2e'),
    ('sysop',  'a634786f773b8a549b8e2ba056307e7b'),
    ('razor',  '24a8ddfa69956912c4cc35a436e68f4a'),
    ('thg',    '8c97e63bc390c3a6eb9ebcce6eea09ba');

INSERT INTO crew (name, handle, region, active_since) VALUES
    ('The Humble Guys',  'THG', 'USA',    1987),
    ('Razor 1911',       'RZR', 'Norway', 1985),
    ('Fairlight',        'FLT', 'Sweden', 1987),
    ('The Dream Team',   'TDT', 'USA',    1986),
    ('Public Enemy',     'PE',  'USA',    1989),
    ('Quartex',          'QTX', 'UK',     1989);

INSERT INTO releases (title, platform, format, cracked_by, release_year, notes) VALUES
    ('Prince of Persia',        'DOS',   'floppy', 'THG', 1990, 'Protection removed. 5 disks.'),
    ('Monkey Island',           'DOS',   'floppy', 'RZR', 1990, 'LucasArts SCUMM protection cracked.'),
    ('Ultima VI',               'DOS',   'floppy', 'TDT', 1990, 'Copy check patched at offset 0x3A2F.'),
    ('Wing Commander',          'DOS',   'floppy', 'FLT', 1990, 'Stardog protection bypassed.'),
    ('Eye of the Beholder',     'DOS',   'floppy', 'THG', 1991, 'SSI protection removed.'),
    ('Civilization',            'DOS',   'floppy', 'RZR', 1991, 'Micropose serial check patched.'),
    ('Lemmings',                'DOS',   'floppy', 'QTX', 1991, 'Psygnosis protection stripped.'),
    ('Railroad Tycoon',         'DOS',   'floppy', 'TDT', 1990, 'Micropose protection neutralized.'),
    ('Secret of Monkey Island', 'Amiga', 'floppy', 'FLT', 1990, 'Disk check removed from loader.'),
    ('Castle Wolfenstein 3D',   'DOS',   'floppy', 'PE',  1992, 'Id Software exe patched.'),
    ('Indiana Jones Fate',      'DOS',   'floppy', 'THG', 1992, 'LucasArts protection cracked.'),
    ('Dune',                    'DOS',   'floppy', 'RZR', 1992, 'Cryo protection removed.');
