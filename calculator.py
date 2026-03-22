import argparse
import random
import re
import sqlite3
import statistics

import attack
import target

DB_FILE = 'warhammer.db'

### Beyond just raw rules, need to simulate actual weapon choies per unit and composition (ie 3 cognis heavy)
### Maybe we consider this evolving into a dynamic list builder
### Need to add modifiers for +/- hit, rapid fire, rerolls, lethals, sustained, feel no pain

### I think we just need to start adding in units and iterating upon them
### in the sense that when we reach a rule we just need to write a conditional for it within the calculator

### Going to have to add preprocessing in the loop for melee weapon selection?
### Perhaps start with model count per unit

### I think modifiers should be a list of keywords

# Regex for expressions like 2d6 or d6+1
DICE_RE = re.compile(
    r"^\s*(\d*)\s*[dD]\s*(\d+)\s*([+-]\s*\d+)?\s*$"
)

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def get_keywords(weapon, attacker, target_name):
    keywords = []
    with get_db() as conn:
        query = conn.execute("""
            select w.name as weapon_name, k.name as keyword from weapons w
            join units u on w.unit_id = u.id
            join weapon_keywords wk on w.id = wk.weapon_id
            join keywords k on wk.keyword_id = k.id
            where u.name = ? and w.name = ?
        """, (attacker, weapon['name'])).fetchall()
        for row in query:
            # 'anti' check
            if 'anti' in row['keyword']:
                value = anti_check(row['keyword'], target_name)
                if value:
                    term = f'anti {value}'
                    keywords.append(term)
            else:
                keywords.append(row['keyword'])
    return parse_keywords(keywords)

# Helper function to simplify anti-x rules
def anti_check(keyword, target_name):
    match = re.match(r"anti[-\s]?(\w+)\s+(\d+)", keyword)

    if match:
        type = match.group(1)
        value = int(match.group(2))

        # Run check on unit
        with get_db() as conn:
            query = conn.execute("""
                select k.name from units u
                join unit_keywords uk on u.id = uk.unit_id
                join keywords k on k.id = uk.keyword_id
                where u.name = ? and k.name = ?
                """, (target_name, type)).fetchall()
            if query:    
                return value
    return 0

# Helper function to parse raw keyword strings into useful dicts
def parse_keywords(keyword_list):
    parsed = {}
    for kw in keyword_list:
        kw = kw.strip().lower()
        match = re.match(r"(.+?)\s+(\d+)$", kw)
        if match:
            name = match.group(1)
            value = int(match.group(2))
            parsed[name] = value
        else:
            parsed[kw] = True
    return parsed


def monte_carlo(n, weapon, target, modifiers, keywords):
    results = []
    for _ in range(n):
        results.append(calculate(weapon, target, modifiers, keywords))
    return results

def parse_dice(expr):
    match = DICE_RE.match(expr)
    if not match:
        raise ValueError(f"Invalid dice expression: {expr}")

    num_dice = int(match.group(1)) if match.group(1) else 1
    die_size = int(match.group(2))
    modifier = int(match.group(3).replace(" ", "")) if match.group(3) else 0

    return num_dice, die_size, modifier

def roll_dice(expr):
    if expr.isdigit():
        return int(expr), [], 0
    num_dice, die_size, modifier = parse_dice(expr)

    rolls = [random.randint(1, die_size) for _ in range(num_dice)]
    total = sum(rolls) + modifier

    return total, rolls, modifier

# modifiers[0] is skill (- is good here), [1] is hit, [2] is damage, [3] is feel no pain
def calculate(weapon, target, modifiers, keywords):
    # Populate all statuses
    anti = keywords.get('anti', 0)
    #blast = get
    devastating_wounds = keywords.get('devastating wounds')
    #heavy = get See melta
    lethal_hits = keywords.get('lethal hits')
    #melta = get I want to make this and rapid create 2 profiles for if applicable or not
    #rapid_fire = get
    sustained_hits = keywords.get('sustained hits', 0)
    torrent = keywords.get('torrent')
    twin_linked = keywords.get('twin-linked')

    # Comparing weapon strength to target toughness for later roll
    if int(weapon['strength']) <= (int(target['toughness'])/2):
        wound_thresh = 6
    elif int(weapon['strength']) >= (int(target['toughness'])*2):
        wound_thresh = 2
    elif int(weapon['strength']) < (int(target['toughness'])/2):
        wound_thresh = 5
    elif int(weapon['strength']) > (int(target['toughness'])/2):
        wound_thresh = 3
    else:
        wound_thresh = 4

    # Calculate save
    # AP + Sv compare to Invuln Save, keeping the lower of the two
    if int(weapon['AP']) + int(target['save']) >= int(target['invuln']):
        save = int(target['invuln'])
    else:
        save = int(weapon['AP']) + int(target['save'])

    x = 1

    tot_wounds = 0
    tot_hits = 0
    tot_succ_wounds = 0
    tot_dam = 0
    tot_mortals = 0

    # Sim x amount of times
    for i in range(x):
        hits = 0
        wounds = 0
        succ_wounds = 0
        dam = 0
        mortals = 0
        
        attacks, _, _ = roll_dice(weapon['attacks'])

        # Roll to hit
        for a in range(attacks):
            roll = random.randint(1,6)
            # Lethal hits status effect
            if lethal_hits and roll == 6:
                wounds += 1
            elif roll + modifiers[1] >= int(weapon['skill']) - modifiers[0]:
                hits += 1
            # Sustained hits status effect
            if roll == 6:
                hits += sustained_hits
        # Torrent status effect
        if torrent:
            hits = attacks

        # Roll to wound
        for h in range(hits):
            roll = random.randint(1,6)
            # Anti and devastating wounds status effect
            if devastating_wounds:
                if (anti and roll >= anti) or roll == 6:
                    mortals += 1
            elif anti and roll >= anti:
                wounds += 1
            elif roll >= wound_thresh:
                wounds += 1
            # Twin-linked status effect
            elif twin_linked:
                roll = random.randint(1,6)
                if devastating_wounds:
                    if (anti and roll >= anti) or roll == 6:
                        mortals += 1
                elif anti and roll >= anti:
                    wounds += 1
                elif roll >= wound_thresh:
                    wounds += 1

        # Roll to save
        for w in range(wounds):
            roll = random.randint(1,6)
            if roll <= save:
                succ_wounds += 1

        # Calculate damage
        for sw in range(succ_wounds):
            damage, _, _ = roll_dice(weapon['damage'])
            damage = damage + modifiers[2] if damage > 1 else 1
            dam += damage
        
        # Calculate mortal damage (for use later)
        for m in range(mortals):
            damage, _, _ = roll_dice(weapon['damage'])
            damage = damage + modifiers[2] if damage > 1 else 1
            dam += damage

        succ_dam = dam

        for d in range(dam):
            roll = random.randint(1,6)
            if roll >= modifiers[3]:
                succ_dam -= 1
        
        tot_hits += hits
        tot_wounds += wounds
        tot_succ_wounds += succ_wounds
        tot_dam += succ_dam
        tot_mortals += mortals
        

    avg_hits = tot_hits / x
    avg_wounds = tot_wounds / x
    avg_succ_wounds = tot_succ_wounds / x
    avg_dam = tot_dam / x
    avg_mortals = tot_mortals / x
    
    return tot_dam
    

    #print(f'Weapon : {weapon['weapon_name']} Target: {target['name']}')
    #print(f'Average Hits: {avg_hits}')
    #print(f'Average Wounds: {avg_wounds}')
    #print(f'Average Succesful Wounds: {avg_succ_wounds}')
    #print(f'Average Damage: {avg_dam}\n')

def main():
    parser = argparse.ArgumentParser(description='Warhammmer damage calculator')
    parser.add_argument('--attacker', required=True, help='Unit attacking')
    parser.add_argument('--target', required=True, help='Unit being attacked')
    # I don't think in the long run this is the optimal way to enter modifiers
    parser.add_argument('--skill', help='Skill modifier +/-')
    parser.add_argument('--hit', help='Hit modifier +/-')
    parser.add_argument('--damage', help='Damage modifier +/-')
    parser.add_argument('--feel', help='Feel no pain')
    args = parser.parse_args()

    weapons = attack.get_weapons_for_unit(args.attacker)
    unit = target.get_unit(args.target)

    modifiers = []
    if args.skill:
        modifiers.append(int(args.skill))
    else:
        modifiers.append(0)
    if args.hit:
        modifiers.append(int(args.hit))
    else:
        modifiers.append(0)
    if args.damage:
        modifiers.append(int(args.damage))
    else:
        modifiers.append(0)
    if args.feel:
        modifiers.append(int(args.feel))
    else:
        modifiers.append(99)


    for w in weapons:
        # Process keywords
        keywords = get_keywords(w, args.attacker, unit['name'])
        print(keywords)
        results = monte_carlo(100000 ,w, unit, modifiers, keywords)
        print(w['name'])
        print("Mean:", statistics.mean(results))
        print("Median:", statistics.median(results))
        print("Std Dev:", statistics.stdev(results))
        print("95th percentile:", sorted(results)[int(0.95 * len(results))])
        print('')

if __name__ == '__main__':
    main()