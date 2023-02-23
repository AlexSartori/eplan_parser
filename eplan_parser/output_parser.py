#!/usr/bin/env python3

import re, sys, json


def __print_err(msg):
    print(' \u001b[31m✖\u001b[0m - ' + msg)

def __print_wrn(msg):
    print(' \u001b[33m!\u001b[0m - ' + msg)

def __print_suc(msg):
    print(' \u001b[32m✓\u001b[0m - ' + msg)

def __print_inf(msg):
    print(' \u001b[34mi\u001b[0m - ' + msg)


def check_index(lines, index, key, match_start=''):
    return key in index and lines[index[key]].startswith(match_start)


def parse_co2_data(lines, index):
    if not check_index(lines, index, 'CO2 Emissions', 'ANNUAL CO2 EMISSIONS'):
        __print_err("Error parsing CO2 data: section not present in index or bad index value")
        return None
    
    data = {}
    idx = index['CO2 Emissions']
    label_1, val_1, _ = lines[idx+1].split('\t', 2)
    label_2, val_2, _ = lines[idx+2].split('\t', 2)

    if label_1.strip() != 'CO2-emission (total)' or label_2.strip() != 'CO2-emission (corrected)':
        __print_err("CO2 section has an unexpected format")
        return None

    data['total'] = int(val_1.replace(',', '.'))
    data['corrected'] = int(val_2.replace(',', '.'))
    return data


def parse_res_share(lines, index):
    if not check_index(lines, index, 'RES Share', 'SHARE OF RES'):
        __print_err("Error parsing RES Share data: section not present in index or bad index value")
        return None
    
    data = {}
    idx = index['RES Share']
    for i in range(3):
        l, v, _ = lines[idx+i+1].split('\t', 2)
        data[l.strip()] = float(v.replace(',', '.'))

    return data


def parse_fuel_annual(lines, index):
    if not check_index(lines, index, 'Annual Fuel Consumption'):
        __print_err("Error parsing fuel data: section not present in index or bad index value")
        return None
    
    data = {}
    idx = index['Annual Fuel Consumption']
    l1, l2, l3, _ = lines[idx].split('\t', 3)

    if not (
            l1.startswith('ANNUAL FUEL CONSUMPTIONS') and
            l2.startswith('TOTAL') and
            l3.startswith('HOUSEHOLDS')
        ):
        __print_err("Annual Fuel data has unexpected format")
        return None
    
    while True:
        idx += 1
        label, total, household, _ = lines[idx].split('\t', 3)
        label = label.strip()

        if label == '':
            break
        else:
            data[label] = {}
            data[label]['total'] = float(total.replace(',', '.'))
            data[label]['household'] = float(household.replace(',', '.')) if household.strip() else ''

    return data


def parse_annual_costs(lines, index):
    if not check_index(lines, index, 'Annual Costs'):
        __print_err("Error parsing annual costs data: section not present in index or bad index value")
        return None
    
    idx = index['Annual Costs']
    data = {}
    l1, l2, l3, l4, _ = lines[idx].split('\t', 4)
    
    if not (
            l1.startswith('ANNUAL COSTS') and
            l2.startswith('TOTAL') and 
            l3.startswith('VARIABLE') and
            l4.startswith('BREAKDOWN')
        ):
        __print_err("Annual Costs data has unexpected format")
        return None

    while True:
        idx += 1

        if not lines[idx].strip():
            continue
        
        label, tot, var, bd, _ = lines[idx].split('\t', 4)
        label = label.strip()

        if label:
            data[label] = {}
            data[label]['total'] = float(tot.replace(',', '.')) if tot.strip() else ''
            data[label]['variable'] = float(var.replace(',', '.')) if var.strip() else ''
            data[label]['breakdown'] = float(bd.replace(',', '.')) if bd.strip() else ''
        
        if label == 'TOTAL ANNUAL COSTS':
            break

    return data


def parse_yearly_totals(lines, index):
    data = {}
    header = get_yearly_totals_header(lines, index)

    # Parse annual totals
    if not check_index(lines, index, 'Yearly Totals'):
        __print_err('Error parsing yearly data: Yearly Totals not in index on bad index value')
        return None
    
    idx = index['Yearly Totals']
    data = {label: {} for label in header}
    annual_totals = lines[idx+1].strip().split('\t')[1:]
    for i, v in enumerate(annual_totals):
        col = header[i]
        data[col]['Annual Total'] = float(v.replace(',', '.')) if v.strip() != 'Percent' else v.strip()
    
    # Parse monthly totals
    if not check_index(lines, index, 'Monthly Totals'):
        __print_err('Error parsing yearly data: Monthly Totals not in index or bad index value')
        return None

    idx = index['Monthly Totals']
    for i in range(12):
        l = lines[idx+i+1].strip().split('\t')
        vals = map(float, l[1:])
        month = l[0].strip()

        for i, v in enumerate(vals):
            col = header[i]
            data[col][month] = v
    
    # Parse annual averages
    idx += 14 # 1 (header) + 12 (months) + 1 (blank)
    if not lines[idx].startswith('Annual Average'):
        __print_err('Yearly averages has unexpected format')
        return None
    
    for i in range(3):
        l = lines[idx+i].strip().split('\t')
        label = l[0].strip()
        vals = list(float(v.replace(',', '.')) if v.strip() != '-' else '-' for v in l[1:])
        
        for i, v in enumerate(vals):
            col = header[i]
            data[col][label] = v

    return data


def parse_hourly_totals(lines, index):
    data = {}
    header = get_yearly_totals_header(lines, index)

    if not check_index(lines, index, 'Hourly Totals'):
        __print_err('Error parsing hourly data: Hourly Totals not in index or bad index value')
        return None
    
    idx = index['Hourly Totals']
    data = {label: [] for label in header}
    for i in range(8784): # No. of lines = hours in one year
        l = lines[idx+i+1].strip().split('\t')
        vals = map(float, l[1:])

        for i, v in enumerate(vals):
            col = header[i]
            data[col].append(v)
    
    return data

    
def get_yearly_totals_header(lines, index):
    if not check_index(lines, index, 'Yearly Totals'):
        __print_err('Cannot find header for Yearly Totals in index')
        return None
    
    idx = index['Yearly Totals']
    line_1, line_2 = lines[idx-3], lines[idx-2]
    labels = zip(line_1.split('\t'), line_2.split('\t'))
    labels = [(l1.strip() + ' ' + l2.strip()).strip() for l1, l2 in labels]

    remaps = {'Indi- vidual': 'Individual'}
    return list(remaps[l] if l in remaps else l for l in labels if l)


def parse_costs_overview_totals(lines, index):
    __print_wrn("Costs overview parsing not yet implemented")
    return None


def parse_fuel_balance(lines, index):
    __print_wrn("Fuel balance parsing not yet implemented")
    return None
    
    data = {}

    if not check_index(lines, index, 'Fuel Balance'):
        __print_err('Error parsing fuel data: Fuel balance not in index or bad index value')
        return None
    
    idx = index['Fuel Balance']
    col_0 = [f.strip() for f in lines[idx].split('\t')].index('FUEL BALANCE')
    idx += 3
    
    header = list(f.strip() for f in lines[idx].split('\t')[col_0+1:])
    data = {label: {} for label in header}
    
    for i in range(9):
        l = [f.strip() for f in lines[idx+i+1].split('\t')[col_0:]]
        label, vals = l[0], [float(v.replace(',', '.')) for v in l[1:]]
        print(label)

        for i, v in enumerate(vals):
            col = header[i]
            data[col][label] = v

    return data


def export_to_json(fname, dataset):
    written_bytes = -1
    
    with open(fname, 'w', encoding='utf-8') as f:
        written_bytes = f.write(json.dumps(dataset))
    
    __print_suc(
        'Exported JSON dataset to "%s" - %.1f Mb (%d bytes) written' %
        (fname, written_bytes/(1024*1024), written_bytes)
    )


def read_energyplan_file(fname):
    lines = []
    
    with open(fname, encoding='iso-8859-15') as f:
        lines = f.readlines()
        __print_suc('Read %d lines from "%s"' % (len(lines), fname))

    return lines


def load_dataset(fname):
    lines = read_energyplan_file(fname)
    dataset = {}
    index = {}

    for i, l in enumerate(lines):
        if l.startswith('EnergyPLAN model'):
            index['Header'] = i
        if l.startswith('ANNUAL CO2 EMISSIONS'):
            index['CO2 Emissions'] = i
        if l.startswith('SHARE OF RES'):
            index['RES Share'] = i
        if l.startswith('ANNUAL FUEL CONSUMPTIONS'):
            index['Annual Fuel Consumption'] = i
        if l.startswith('ANNUAL COSTS'):
            index['Annual Costs'] = i
        if l.startswith('TOTAL FOR ONE YEAR'):
            index['Yearly Totals'] = i
        if l.startswith('MONTHLY AVERAGE VALUES'):
            index['Monthly Totals'] = i
        if l.startswith('HOURLY VALUES'):
            index['Hourly Totals'] = i
        if 'OVERVIEW OF INVESTMENT COSTS' in l:
            index['Costs Overview'] = i
        if 'FUEL BALANCE' in l:
            index['Fuel Balance'] = i

    # Check EnergyPLAN version
    tested_versions = ['16.22']
    v = re.match(r'EnergyPLAN model ([0-9\.]+)', lines[index['Header']]).groups()[0]
    
    if v not in tested_versions:
        __print_wrn('Warning: Dataset is from an untested version of EnergyPLAN (%s)' % v)
        __print_wrn('         This parser has been tested with versions: %s' % ', '.join(tested_versions))
        __print_wrn('         If you find any bugs or good compatibility please add a comment on:')
        __print_wrn('         <https://gist.github.com/AlexSartori/51694c43e967c436f78c9abf39056eb1>')

    # Read CO2 data
    dataset['CO2 Emissions'] = parse_co2_data(lines, index)
    __print_suc('Parsed CO2 section') if dataset['CO2 Emissions'] else None

    # Read RES Share
    dataset['RES Share'] = parse_res_share(lines, index)
    __print_suc('Parsed RES Share section') if dataset['RES Share'] else None

    # Read annnual fuel consumption
    dataset['Annual Fuel Consumption'] = parse_fuel_annual(lines, index)
    __print_suc('Parsed Fuel Consumption section') if dataset['Annual Fuel Consumption'] else None

    # Read annual costs
    dataset['Annual Costs'] = parse_annual_costs(lines, index)
    __print_suc('Parsed Annual Costs section') if dataset['Annual Costs'] else None

    # Read yearly totals
    dataset['Yearly Totals'] = parse_yearly_totals(lines, index)
    __print_suc('Parsed Yearly Totals section') if dataset['Yearly Totals'] else None

    # Read hourly totals
    dataset['Hourly Totals'] = parse_hourly_totals(lines, index)
    __print_suc('Parsed Hourly Totals section') if dataset['Hourly Totals'] else None

    # Read costs overview
    dataset['Costs Overview'] = parse_costs_overview_totals(lines, index)
    __print_suc('Parsed Costs Overview section') if dataset['Costs Overview'] else None

    # Read fuel balance
    dataset['Fuel Balance'] = parse_fuel_balance(lines, index)
    __print_suc('Parsed Fuel Balance section') if dataset['Fuel Balance'] else None

    return dataset


def run_from_terminal():
    if len(sys.argv) != 3:
        print("Usage: eplan_parser <input.txt> <output.json>")
        return

    # Load the dataset
    dataset = load_dataset(sys.argv[1])

    # Export the dataset
    export_to_json(sys.argv[2], dataset)

