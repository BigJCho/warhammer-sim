import argparse
import sqlite3

DB_FILE = 'warhammer.db'
FIELDS = ['name', 'T', 'Sv', 'ISv', 'W', 'points', 'keywords']

def get_db():
    return sqlite3.connect(DB_FILE)

def add_unit():
    name = input('Name?\n> ')
    toughness = input('T?\n> ')
    save = input('Sv?\n> ')
    invul_save = input('ISv?\n> ')
    wounds = input('W?\n> ')
    points = input('Point cost?\n> ')
    keys = input('Keywords separated with a space\n> ')

    keywords = keys.split()

    print('Is this correct?')
    print(f'Name: {name}, T: {toughness}, S: {save}, ISv: {invul_save}, W: {wounds}, Points: {points}, Keywords: {keywords}')
    confirmation = input('Y or N:\n >')
    if confirmation.lower() != 'y':
        print('Please re-run and enter again.')
        return
    else:
        with get_db() as conn:
            cur = conn.execute("""
                INSERT INTO units (name, T, Sv, ISv, W, points)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (name, toughness, save, invul_save, wounds, points))
            unit_id = cur.lastrowid
            for word in keywords:
                conn.execute("""
                    INSERT INTO unit_keywords (unit_id, keyword_id)
                    VALUES (
                        ?,
                        (SELECT id FROM keywords WHERE name = ?)
                    )
                """, (unit_id, word))

def delete_unit(name):
    with get_db() as conn:
        conn.execute('DELETE FROM units WHERE name = ?', (name,))

def main():
    parser = argparse.ArgumentParser(description='Warhammmer unit manager')
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    subparsers.add_parser('add', help='Add a new unit')

    delete_parser = subparsers.add_parser('delete', help= 'Delete a unit')
    delete_parser.add_argument('--name', required=True, help='Unit name')

    args = parser.parse_args()

    if args.command == 'add':
        add_unit()
    elif args.command == 'delete':
        delete_unit(args.name)

if __name__ == '__main__':
    main()