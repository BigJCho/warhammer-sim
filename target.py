import argparse
import sqlite3

DB_FILE = 'warhammer.db'

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# Needs to return the row for a unit
def get_unit(unit_name):
    with get_db() as conn:
        row = conn.execute('SELECT * FROM units WHERE name = ?',
                                   (unit_name,
                                    )).fetchone()
        if not row:
            raise ValueError("Unit does not exist")
        unit = row
        return unit

def add_unit():
    name = input('Name?\n> ')
    toughness = input('T?\n> ')
    save = input('Sv?\n> ')
    invul_save = input('ISv?\n> ')
    wounds = input('W?\n> ')
    points = input('Point cost? Please use max unit size\n> ')
    models = input('Model count? Please use max unit size\n')
    keys = input('Keywords separated with a comma\n> ')

    keywords = [k.strip().lower() for k in keys.split(',')]

    print('Is this correct?')
    print(f'Name: {name}, T: {toughness}, S: {save}, ISv: {invul_save}, W: {wounds}, Points: {points}, Models: {models}, Keywords: {keywords}')
    confirmation = input('Y or N:\n >')
    if confirmation.lower() != 'y':
        print('Please re-run and enter again.')
        return
    else:
        with get_db() as conn:
            cur = conn.execute("""
                INSERT INTO units (name, toughness, wounds, save, invuln, points, models)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (name, toughness, wounds, save, invul_save, points, models))
            unit_id = cur.lastrowid
            if keys:
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