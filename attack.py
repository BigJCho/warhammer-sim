import argparse
import csv
import os
import sqlite3

DB_FILE = 'warhammer.db'
FIELDS = ['parent_name', 'weapon_name', 'A', 'skill', 'S', 'AP', 'D', 'keywords']

def get_db():
    return sqlite3.connect(DB_FILE)

def get_weapons_for_unit(parent_name):
    with get_db() as conn:
        return conn.execute("""
            SELECT w.*
            FROM weapons w
            JOIN units ON w.unit_id = u.id
            WHERE u.name = ?
        """, (parent_name,)).fetchall()

def add_weapon(parent_name):
    weapon_name = input("Weapon Name?\n> ")
    attacks = input("A?\n> ")
    skill = input("Skill?\n> ")
    strength = input('S?:\n> ')
    ap = input('AP?:\n> ')
    damage = input('D?:\n> ')
    keys = input('Keywords separated by space:\n> ')

    keywords = keys.split()

    with get_db() as conn:
        unit_id = conn.execute('SELECT id FROM units WHERE name = ?',
                               (parent_name,
                                )).fetchone()
        if not unit_id:
            raise ValueError("Unit does not exist")
        cur = conn.execute(
            """
            INSERT INTO weapons
            (unit_id, weapon_name, A, skill, S, AP, D)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            unit_id,
            weapon_name,
            attacks,
            skill,
            strength,
            ap,
            damage
        ))
        weapon_id = cur.lastrowid
        for word in keywords:
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