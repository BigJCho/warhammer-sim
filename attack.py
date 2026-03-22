import argparse
import sqlite3

DB_FILE = 'warhammer.db'
FIELDS = ['parent_name', 'weapon_name', 'A', 'skill', 'S', 'AP', 'D', 'keywords']

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def get_weapons_for_unit(parent_name):
    with get_db() as conn:
        return conn.execute("""
            SELECT w.*
            FROM weapons w
            JOIN units u ON w.unit_id = u.id
            WHERE u.name = ?
        """, (parent_name,)).fetchall()

def add_weapon(parent_name):
    weapon_name = input("Weapon Name?\n> ")
    attacks = input("A?\n> ")
    skill = input("Skill?\n> ")
    strength = input('S?:\n> ')
    ap = input('AP?:\n> ')
    damage = input('D?:\n> ')
    type = input('Melee or Ranged?\n')
    keys = input('Keywords separated by comma:\n> ')
    
    keywords = [k.strip().lower() for k in keys.split(',')]

    with get_db() as conn:
        row = conn.execute('SELECT id FROM units WHERE name = ?',
                               (parent_name,
                                )).fetchone()
        if not row:
            raise ValueError("Unit does not exist")
        unit_id = row[0]
        cur = conn.execute(
            """
            INSERT INTO weapons
            (unit_id, name, attacks, skill, strength, ap, damage, type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            unit_id,
            weapon_name,
            attacks,
            skill,
            strength,
            ap,
            damage,
            type
        ))
        weapon_id = cur.lastrowid
        if keys:
            for word in keywords:
                conn.execute(
                        """
                        INSERT OR IGNORE INTO keywords
                        (name)
                        VALUES (?)
                    """, (
                        word,
                    ))
                conn.execute("""
                    INSERT INTO weapon_keywords (weapon_id, keyword_id)
                    VALUES (
                        ?,
                        (SELECT id FROM keywords WHERE name = ?)
                    )
                """, (weapon_id, word))

def main():
    parser = argparse.ArgumentParser(description='Unit weapon manager')
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    add_parser = subparsers.add_parser('add', help='Add a new unit')
    add_parser.add_argument('--parent_name', required=True, help='Unit name')

    delete_parser = subparsers.add_parser('delete', help= 'Delete a unit')
    delete_parser.add_argument('--parent_name', required=True, help='Unit name')
    delete_parser.add_argument('--weapon_name', help='Weapon name')
    delete_parser.add_argument('--all', action='store_true', help='Flag to delete a unit')

    args = parser.parse_args()

    if args.command == 'add':
        add_weapon(args.parent_name)

if __name__ == '__main__':
    main()